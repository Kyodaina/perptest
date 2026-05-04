const fileInput = document.getElementById('audioFile');
const startBtn = document.getElementById('startBtn');
const statusEl = document.getElementById('status');
const transcriptEl = document.getElementById('transcript');
const bar = document.getElementById('bar');
const txtBtn = document.getElementById('txtBtn');
const pdfBtn = document.getElementById('pdfBtn');

let lastJobId = null;

const setStatus = (text) => (statusEl.textContent = `Státusz: ${text}`);

startBtn.addEventListener('click', async () => {
  const file = fileInput.files[0];
  if (!file) {
    setStatus('válassz fájlt');
    return;
  }

  txtBtn.disabled = true;
  pdfBtn.disabled = true;
  transcriptEl.textContent = '';
  bar.style.width = '0%';

  const form = new FormData();
  form.append('file', file);

  setStatus('feltöltés...');
  const uploadRes = await fetch('/api/upload', { method: 'POST', body: form });
  const uploadData = await uploadRes.json();

  if (!uploadRes.ok) {
    setStatus(uploadData.detail || 'hiba');
    return;
  }

  lastJobId = uploadData.job_id;
  setStatus('feldolgozás folyamatban');
  pollJob(lastJobId);
});

async function pollJob(jobId) {
  const res = await fetch(`/api/jobs/${jobId}`);
  const job = await res.json();

  if (!res.ok) {
    setStatus(job.detail || 'ismeretlen hiba');
    return;
  }

  bar.style.width = `${job.progress}%`;

  if (job.status === 'completed') {
    setStatus('kész');
    transcriptEl.textContent = job.result.formatted_transcript;
    txtBtn.disabled = false;
    pdfBtn.disabled = false;
    return;
  }

  if (job.status === 'failed') {
    setStatus(`hiba: ${job.error}`);
    return;
  }

  setTimeout(() => pollJob(jobId), 1200);
}

txtBtn.addEventListener('click', () => {
  if (lastJobId) window.open(`/api/export/${lastJobId}/txt`, '_blank');
});

pdfBtn.addEventListener('click', () => {
  if (lastJobId) window.open(`/api/export/${lastJobId}/pdf`, '_blank');
});
