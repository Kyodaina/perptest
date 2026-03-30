from __future__ import annotations

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from app.config import MAX_WORKERS
from app.schemas import AnalysisResult
from app.services.analyzer import AdAnalyzer


@dataclass
class ImageTaskState:
    file_name: str
    status: str = "queued"
    progress: float = 0.0
    logs: list[str] = field(default_factory=list)
    output: AnalysisResult | None = None
    error: str | None = None


@dataclass
class JobState:
    job_id: str
    status: str = "queued"
    progress: float = 0.0
    logs: list[str] = field(default_factory=list)
    items: dict[str, ImageTaskState] = field(default_factory=dict)


class JobManager:
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self._jobs: dict[str, JobState] = {}
        self._lock = threading.Lock()
        self._analyzer = AdAnalyzer()

    def create_job(self, files: list[Path]) -> str:
        job_id = str(uuid.uuid4())
        items = {str(path): ImageTaskState(file_name=path.name) for path in files}
        job = JobState(job_id=job_id, status="queued", items=items)

        with self._lock:
            self._jobs[job_id] = job

        self._executor.submit(self._run_job, job_id, files)
        return job_id

    def _append_log(self, job: JobState, message: str):
        job.logs.append(message)

    def _run_job(self, job_id: str, files: list[Path]):
        with self._lock:
            job = self._jobs[job_id]
            job.status = "running"
            self._append_log(job, "Job started")

        total = len(files)
        for index, file_path in enumerate(files, start=1):
            with self._lock:
                item = job.items[str(file_path)]
                item.status = "running"
                item.progress = 5
                self._append_log(job, f"Analyzing {file_path.name}")
                item.logs.append("Loading image and prompting model")

            try:
                result = self._analyzer.analyze(file_path)
                with self._lock:
                    item.output = result
                    item.status = "completed"
                    item.progress = 100
                    item.logs.append("Inference complete")
                    self._append_log(job, f"Finished {file_path.name}")
            except Exception as exc:  # noqa: BLE001
                with self._lock:
                    item.status = "failed"
                    item.error = str(exc)
                    item.progress = 100
                    item.logs.append(f"Failed: {exc}")
                    self._append_log(job, f"Failed {file_path.name}: {exc}")

            with self._lock:
                job.progress = round((index / total) * 100, 2)

        with self._lock:
            failures = any(state.status == "failed" for state in job.items.values())
            job.status = "failed" if failures else "completed"
            self._append_log(job, f"Job completed with status={job.status}")

    def get_job(self, job_id: str) -> JobState | None:
        with self._lock:
            return self._jobs.get(job_id)


job_manager = JobManager()
