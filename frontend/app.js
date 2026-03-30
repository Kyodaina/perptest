const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const startBtn = document.getElementById('startBtn');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const logBox = document.getElementById('logBox');
const resultsGrid = document.getElementById('resultsGrid');
const precisionMode = document.getElementById('precisionMode');

let selectedFiles = [];
let pollTimer = null;

function renderFiles() {
  fileList.innerHTML = selectedFiles.map((f) => `<li>${f.name}</li>`).join('');
}

function appendLogs(logs) {
  logBox.textContent = logs.join('\n');
  logBox.scrollTop = logBox.scrollHeight;
}

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  selectedFiles = [...selectedFiles, ...Array.from(e.dataTransfer.files)];
  renderFiles();
});

fileInput.addEventListener('change', (e) => {
  selectedFiles = [...selectedFiles, ...Array.from(e.target.files)];
  renderFiles();
});

function renderResults(job) {
  resultsGrid.innerHTML = '';
  job.result.forEach((item) => {
    const card = document.createElement('article');
    card.className = 'result-card';

    if (item.media_type === 'image') {
      const imageTag = `<img src="/uploads/${item.file_name}" alt="${item.file_name}" />`;
      card.innerHTML = `
        ${imageTag}
        <h3>${item.file_name}</h3>
        <p><strong>Visible text:</strong> ${item.analysis?.visible_text || ''}</p>
        <p><strong>Prices:</strong> ${(item.analysis?.prices || []).join(', ')}</p>
        <p><strong>Intent:</strong> ${item.analysis?.marketing_intent || ''}</p>
        <p><span class="badge">Importance ${item.analysis?.importance_score || '-'}/5</span></p>
      `;
    } else if (item.media_type === 'audio') {
      card.innerHTML = `
        <h3>${item.file_name}</h3>
        <p><strong>Transcription:</strong> ${item.transcription || ''}</p>
      `;
    } else {
      card.innerHTML = `<h3>${item.file_name}</h3><p class="muted">Error: ${item.error}</p>`;
    }
    resultsGrid.appendChild(card);
  });
}

async function pollJob(jobId) {
  const res = await fetch(`/api/jobs/${jobId}`);
  const job = await res.json();

  progressBar.style.width = `${Math.round(job.progress * 100)}%`;
  progressText.textContent = `${Math.round(job.progress * 100)}% - ${job.status}`;
  appendLogs(job.logs);

  if (job.status === 'completed' || job.status === 'failed') {
    clearInterval(pollTimer);
    pollTimer = null;
    renderResults(job);
  }
}

startBtn.addEventListener('click', async () => {
  if (!selectedFiles.length) {
    alert('Please select files first.');
    return;
  }

  const formData = new FormData();
  selectedFiles.forEach((f) => formData.append('files', f));
  formData.append('precision_mode', precisionMode.value);

  const xhr = new XMLHttpRequest();
  xhr.open('POST', '/api/upload');

  xhr.upload.onprogress = (event) => {
    if (event.lengthComputable) {
      const pct = Math.round((event.loaded / event.total) * 100);
      progressBar.style.width = `${pct}%`;
      progressText.textContent = `Upload ${pct}%`;
    }
  };

  xhr.onload = () => {
    if (xhr.status >= 200 && xhr.status < 300) {
      try {
        const payload = JSON.parse(xhr.responseText);
        appendLogs([`Job ${payload.job_id} created.`]);
        pollTimer = setInterval(() => pollJob(payload.job_id), 1500);
      } catch (err) {
        appendLogs([`Upload succeeded but response parse failed: ${err}`, xhr.responseText]);
        alert('Server returned an unexpected payload; check logs panel for details.');
      }
    } else {
      alert(`Upload failed: ${xhr.responseText}`);
    }
  };

  xhr.onerror = () => alert('Network error during upload');
  xhr.send(formData);
});
