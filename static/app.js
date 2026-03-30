const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const startBtn = document.getElementById('startBtn');
const precisionSelect = document.getElementById('precision');
const uploadProgressWrap = document.getElementById('uploadProgressWrap');
const uploadProgressBar = document.getElementById('uploadProgressBar');
const jobProgressBar = document.getElementById('jobProgressBar');
const jobProgressText = document.getElementById('jobProgressText');
const logsBox = document.getElementById('logs');
const resultsWrap = document.getElementById('results');

let selectedFiles = [];

const renderFiles = () => {
  fileList.innerHTML = selectedFiles.map(f => `<li>${f.name} (${Math.round(f.size/1024)} KB)</li>`).join('');
};

dropzone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => {
  selectedFiles = [...e.target.files];
  renderFiles();
});

dropzone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropzone.classList.add('active');
});
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('active'));
dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.classList.remove('active');
  selectedFiles = [...e.dataTransfer.files].filter(f => /image\/(jpeg|png|webp)/.test(f.type));
  renderFiles();
});

function setUploadProgress(percent) {
  uploadProgressWrap.classList.remove('hidden');
  uploadProgressBar.style.width = `${percent}%`;
}

function uploadFiles(files) {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/uploads');

    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        const percent = (event.loaded / event.total) * 100;
        setUploadProgress(percent.toFixed(2));
      }
    });

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        reject(new Error(xhr.responseText));
      }
    };
    xhr.onerror = () => reject(new Error('Upload failed due to network error.'));
    xhr.send(formData);
  });
}

async function startJob(fileIds, precision) {
  const res = await fetch('/api/jobs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_ids: fileIds, precision }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function pollJob(jobId) {
  let done = false;
  while (!done) {
    const res = await fetch(`/api/jobs/${jobId}`);
    const state = await res.json();

    jobProgressBar.style.width = `${state.progress}%`;
    jobProgressText.textContent = `Status: ${state.status} | ${state.progress}%`;
    logsBox.textContent = state.logs.join('\n');

    if (state.status === 'completed') {
      renderResults(state.results);
      done = true;
    } else if (state.status === 'failed') {
      throw new Error(state.error || 'Processing failed');
    } else {
      await new Promise(r => setTimeout(r, 1200));
    }
  }
}

function renderResults(results) {
  resultsWrap.innerHTML = results
    .filter(item => item.file_type === 'image')
    .map(item => {
      const r = item.image_analysis;
      return `
      <article class="result-card">
        <img src="/api/files/${item.file_id}" alt="${item.filename}" />
        <div class="result-body">
          <h3>${item.filename}</h3>
          <p><strong>Visible text:</strong> ${r.visible_text || '-'}</p>
          <p><strong>CTA:</strong> ${r.cta || '-'}</p>
          <p><strong>Prices:</strong> ${(r.prices || []).join(', ') || '-'}</p>
          <p><strong>Key messages:</strong> ${(r.key_messages || []).join(' | ') || '-'}</p>
          <p>
            <span class="badge">Intent: ${r.marketing_intent}</span>
            <span class="badge">Importance: ${r.importance_score}/5</span>
          </p>
        </div>
      </article>`;
    })
    .join('');
}

startBtn.addEventListener('click', async () => {
  try {
    if (!selectedFiles.length) {
      alert('Please select at least one image file.');
      return;
    }

    startBtn.disabled = true;
    logsBox.textContent = 'Uploading files...';

    const uploadResponse = await uploadFiles(selectedFiles);
    const fileIds = uploadResponse.items.map(item => item.file_id);

    logsBox.textContent += '\nUpload complete. Starting job...';
    const job = await startJob(fileIds, precisionSelect.value);
    await pollJob(job.job_id);
  } catch (error) {
    logsBox.textContent += `\nError: ${error.message}`;
  } finally {
    startBtn.disabled = false;
  }
});
