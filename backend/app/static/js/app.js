const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const uploadProgress = document.querySelector('#uploadProgress > div');
const processProgress = document.querySelector('#processProgress > div');
const logsEl = document.getElementById('logs');
const resultsEl = document.getElementById('results');

let files = [];
let stagedPaths = [];

function renderFiles() {
  fileList.innerHTML = files.map(f => `<li>${f.name}</li>`).join('');
}

function appendLog(msg) {
  logsEl.textContent += `${new Date().toISOString()} | ${msg}\n`;
  logsEl.scrollTop = logsEl.scrollHeight;
}

['dragenter', 'dragover'].forEach(ev => dropzone.addEventListener(ev, e => {
  e.preventDefault();
  dropzone.style.opacity = '0.8';
}));

['dragleave', 'drop'].forEach(ev => dropzone.addEventListener(ev, e => {
  e.preventDefault();
  dropzone.style.opacity = '1';
}));

dropzone.addEventListener('drop', (e) => {
  files = [...files, ...e.dataTransfer.files];
  renderFiles();
});

fileInput.addEventListener('change', () => {
  files = [...files, ...fileInput.files];
  renderFiles();
});

async function uploadFiles() {
  const form = new FormData();
  files.forEach(file => form.append('files', file));

  const xhr = new XMLHttpRequest();
  const done = new Promise((resolve, reject) => {
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        uploadProgress.style.width = `${(e.loaded / e.total) * 100}%`;
      }
    });
    xhr.onload = () => resolve(JSON.parse(xhr.responseText));
    xhr.onerror = () => reject(new Error('Upload failed'));
  });

  xhr.open('POST', '/api/upload');
  xhr.send(form);
  return done;
}

function badgeIntent(intent) {
  return `<span class="badge">${intent}</span>`;
}

function renderResults(results) {
  resultsEl.innerHTML = '';
  results.forEach(file => {
    const card = document.createElement('div');
    card.className = 'result-card';

    const frames = file.frames.map(fr => `
      <div class="frame">
        <img src="${fr.frame_path}" alt="frame" />
        <p><b>Timestamp:</b> ${fr.timestamp_seconds.toFixed(2)}s</p>
        <p><b>Text:</b> ${fr.visible_text}</p>
        <p><b>Prices:</b> ${fr.prices.join(', ') || '-'}</p>
        <p><b>CTA:</b> ${fr.cta || '-'}</p>
        <p><b>Intent:</b> ${badgeIntent(fr.marketing_intent)} <b>Importance:</b> ${fr.importance_score}/5</p>
        <p><b>Messages:</b> ${fr.key_messages.join(' | ')}</p>
      </div>
    `).join('');

    const audio = file.audio_transcript.map(seg => `[${seg.start.toFixed(1)}-${seg.end.toFixed(1)}] ${seg.text}`).join('\n');

    card.innerHTML = `
      <h3>${file.filename} (${file.file_type})</h3>
      <div class="frames">${frames}</div>
      ${audio ? `<h4>Audio Transcript</h4><div class="audio">${audio}</div>` : ''}
    `;
    resultsEl.appendChild(card);
  });
}

async function pollJob(jobId) {
  let done = false;
  while (!done) {
    const res = await fetch(`/api/jobs/${jobId}`);
    const state = await res.json();
    processProgress.style.width = `${state.progress}%`;
    logsEl.textContent = state.logs.join('\n');

    if (state.status === 'done') {
      appendLog('Processing complete');
      renderResults(state.results);
      done = true;
    } else if (state.status === 'error') {
      appendLog(`ERROR: ${state.error}`);
      done = true;
    } else {
      await new Promise(r => setTimeout(r, 1800));
    }
  }
}

document.getElementById('startBtn').addEventListener('click', async () => {
  if (!files.length) {
    alert('Please add files first.');
    return;
  }

  appendLog('Uploading files...');
  const uploadResult = await uploadFiles();
  stagedPaths = uploadResult.files;
  appendLog(`Uploaded ${stagedPaths.length} files`);

  const payload = {
    paths: stagedPaths,
    model_family: document.getElementById('modelFamily').value,
    model_size: document.getElementById('modelSize').value,
    precision: document.getElementById('precision').value,
    frame_interval_seconds: 1.5,
  };

  const analyzeRes = await fetch('/api/analyze', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  });
  const analyzeData = await analyzeRes.json();

  appendLog(`Job created: ${analyzeData.job_id}`);
  pollJob(analyzeData.job_id);
});
