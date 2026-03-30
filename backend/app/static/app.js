const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const fileList = document.getElementById("file-list");
const startBtn = document.getElementById("start-btn");
const progressBar = document.getElementById("progress-bar");
const progressText = document.getElementById("progress-text");
const debugLogs = document.getElementById("debug-logs");
const resultsEl = document.getElementById("results");

let selectedFiles = [];
let jobId = null;

function renderFiles() {
  fileList.innerHTML = "";
  selectedFiles.forEach((f) => {
    const li = document.createElement("li");
    li.textContent = `${f.name} (${Math.round(f.size / 1024)} KB)`;
    fileList.appendChild(li);
  });
  startBtn.disabled = selectedFiles.length === 0;
}

function setFiles(files) {
  selectedFiles = [...files].filter((f) => /\.(jpg|jpeg|png|webp)$/i.test(f.name));
  renderFiles();
}

dropZone.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", (e) => setFiles(e.target.files));

["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (e) => {
    e.preventDefault();
    dropZone.classList.add("drag");
  });
});
["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag");
  });
});
dropZone.addEventListener("drop", (e) => setFiles(e.dataTransfer.files));

startBtn.addEventListener("click", async () => {
  const formData = new FormData();
  selectedFiles.forEach((file) => formData.append("files", file));

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/api/upload");
  xhr.upload.onprogress = (event) => {
    if (event.lengthComputable) {
      const uploadProgress = Math.round((event.loaded / event.total) * 100);
      progressBar.style.width = `${uploadProgress}%`;
      progressText.textContent = `Uploading: ${uploadProgress}%`;
    }
  };

  xhr.onload = () => {
    if (xhr.status >= 200 && xhr.status < 300) {
      const payload = JSON.parse(xhr.responseText);
      jobId = payload.job_id;
      pollJob();
    } else {
      debugLogs.textContent = `Upload failed: ${xhr.responseText}`;
    }
  };

  xhr.send(formData);
});

function renderResultCard(item) {
  const o = item.output;
  const intentClass = `intent-${o.marketing_intent}`;
  return `
    <article class="result-card">
      <h3>${item.file_name}</h3>
      <a href="/uploads/${encodeURIComponent(item.file_name)}" target="_blank" rel="noreferrer">
        <img src="/uploads/${encodeURIComponent(item.file_name)}" alt="${item.file_name}" />
      </a>
      <p><strong>Visible text:</strong> ${o.visible_text || "(none)"}</p>
      <p><strong>Prices:</strong> ${o.prices.length ? o.prices.join(", ") : "(none)"}</p>
      <p><strong>Marketing intent:</strong> <span class="badge ${intentClass}">${o.marketing_intent}</span></p>
      <p><strong>Importance:</strong> ${"⭐".repeat(o.importance_score)} (${o.importance_score}/5)</p>
    </article>
  `;
}

async function pollJob() {
  if (!jobId) return;

  const res = await fetch(`/api/jobs/${jobId}`);
  const data = await res.json();

  progressBar.style.width = `${data.progress}%`;
  progressText.textContent = `Status: ${data.status} (${data.progress}%)`;
  debugLogs.textContent = [...data.logs, "", ...data.items.flatMap((i) => [`[${i.file_name}]`, ...i.logs])].join("\n");

  resultsEl.innerHTML = data.items
    .filter((i) => i.output)
    .map((i) => renderResultCard(i))
    .join("");

  if (data.status === "running" || data.status === "queued") {
    setTimeout(pollJob, 1200);
  }
}
