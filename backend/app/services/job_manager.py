from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from app.schemas import TranscriptResult
from app.services.analyzer import transcribe_audio


@dataclass
class Job:
    job_id: str
    file_name: str
    status: str = "queued"
    progress: int = 0
    logs: list[str] = field(default_factory=list)
    result: TranscriptResult | None = None
    error: str | None = None


class JobManager:
    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}
        self.lock = threading.Lock()

    def create_job(self, path: Path) -> str:
        job_id = str(uuid.uuid4())
        job = Job(job_id=job_id, file_name=path.name)
        with self.lock:
            self.jobs[job_id] = job

        thread = threading.Thread(target=self._run_job, args=(job_id, path), daemon=True)
        thread.start()
        return job_id

    def _run_job(self, job_id: str, path: Path) -> None:
        job = self.jobs[job_id]
        job.status = "processing"
        job.logs.append("Hang előfeldolgozás és transzkripció elindult.")

        def set_progress(value: int) -> None:
            job.progress = value

        try:
            job.result = transcribe_audio(path, progress_cb=set_progress)
            job.status = "completed"
            job.logs.append("Transzkripció kész.")
        except Exception as exc:
            job.status = "failed"
            job.error = str(exc)
            job.logs.append(f"Hiba történt: {exc}")

    def get(self, job_id: str) -> Job | None:
        return self.jobs.get(job_id)


job_manager = JobManager()
