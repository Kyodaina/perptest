import json
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from app.config import RESULTS_DIR
from app.schemas import JobState
from app.services.pipeline import ProcessingPipeline


@dataclass
class UploadedFile:
    file_id: str
    filename: str
    path: Path
    media_type: str


@dataclass
class JobData:
    job_id: str
    file_ids: list[str]
    precision: str
    status: str = "queued"
    progress: float = 0.0
    logs: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    results: list[dict] = field(default_factory=list)
    error: str | None = None


class JobManager:
    def __init__(self) -> None:
        self.pipeline = ProcessingPipeline()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.jobs: dict[str, JobData] = {}
        self.files: dict[str, UploadedFile] = {}
        self._lock = threading.Lock()

    def register_file(self, filename: str, path: Path, media_type: str) -> UploadedFile:
        file_id = str(uuid.uuid4())
        uploaded = UploadedFile(file_id=file_id, filename=filename, path=path, media_type=media_type)
        self.files[file_id] = uploaded
        return uploaded

    def create_job(self, file_ids: list[str], precision: str) -> str:
        job_id = str(uuid.uuid4())
        job = JobData(job_id=job_id, file_ids=file_ids, precision=precision)
        with self._lock:
            self.jobs[job_id] = job
        self.executor.submit(self._run_job, job_id)
        return job_id

    def get_job(self, job_id: str) -> JobState:
        job = self.jobs.get(job_id)
        if not job:
            raise KeyError("Job not found")
        return JobState(
            job_id=job.job_id,
            status=job.status,
            progress=job.progress,
            logs=job.logs,
            created_at=job.created_at,
            finished_at=job.finished_at,
            results=job.results,
            error=job.error,
        )

    def get_file(self, file_id: str) -> UploadedFile | None:
        return self.files.get(file_id)

    def _log(self, job: JobData, message: str) -> None:
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        job.logs.append(f"[{timestamp}] {message}")

    def _run_job(self, job_id: str) -> None:
        job = self.jobs[job_id]
        try:
            job.status = "running"
            total = len(job.file_ids)
            self._log(job, f"Job started ({total} file(s), precision={job.precision}).")

            for idx, file_id in enumerate(job.file_ids, start=1):
                upload = self.files.get(file_id)
                if not upload:
                    self._log(job, f"Skipping unknown file_id={file_id}")
                    continue

                self._log(job, f"Processing {upload.filename}")
                result = self.pipeline.process_file(
                    file_id=upload.file_id,
                    filename=upload.filename,
                    path=upload.path,
                    precision=job.precision,
                )
                job.results.append(result.model_dump())
                job.progress = round((idx / total) * 100.0, 2)
                self._log(job, f"Completed {upload.filename}")

            job.status = "completed"
            job.finished_at = datetime.utcnow()
            self._persist_results(job)
            self._log(job, "Job completed successfully.")
        except Exception as exc:  # noqa: BLE001
            job.status = "failed"
            job.error = str(exc)
            job.finished_at = datetime.utcnow()
            self._log(job, f"Job failed: {exc}")

    def _persist_results(self, job: JobData) -> None:
        target = RESULTS_DIR / f"{job.job_id}.json"
        with target.open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "job_id": job.job_id,
                    "created_at": job.created_at.isoformat(),
                    "finished_at": job.finished_at.isoformat() if job.finished_at else None,
                    "results": job.results,
                },
                handle,
                ensure_ascii=False,
                indent=2,
            )


job_manager = JobManager()
