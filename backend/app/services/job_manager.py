from __future__ import annotations

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from backend.app.config import settings
from backend.app.schemas import JobDetails, JobStatus, MediaResult, PrecisionMode
from backend.app.services.pipeline import analyze_image, transcribe_audio

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg"}


class JobManager:
    def __init__(self) -> None:
        self.executor = ThreadPoolExecutor(max_workers=settings.max_workers)
        self.jobs: dict[str, JobDetails] = {}

    def create_job(self, files: list[Path], precision_mode: PrecisionMode) -> JobDetails:
        now = datetime.utcnow()
        job_id = str(uuid.uuid4())
        job = JobDetails(
            job_id=job_id,
            status=JobStatus.queued,
            progress=0.0,
            precision_mode=precision_mode,
            logs=["Job queued"],
            files=[str(f) for f in files],
            created_at=now,
            updated_at=now,
        )
        self.jobs[job_id] = job
        self.executor.submit(self._run_job, job_id)
        return job

    def get_job(self, job_id: str) -> JobDetails | None:
        return self.jobs.get(job_id)

    def _log(self, job: JobDetails, message: str) -> None:
        job.logs.append(f"[{datetime.utcnow().isoformat()}] {message}")
        job.updated_at = datetime.utcnow()

    def _run_job(self, job_id: str) -> None:
        job = self.jobs[job_id]
        try:
            job.status = JobStatus.running
            self._log(job, "Processing started")
            files = [Path(f) for f in job.files]
            total = len(files)
            results: list[MediaResult] = []

            for index, path in enumerate(files, start=1):
                suffix = path.suffix.lower()
                self._log(job, f"Processing file: {path.name}")
                try:
                    if suffix in IMAGE_EXTENSIONS:
                        analysis = analyze_image(path, job.precision_mode)
                        result = MediaResult(
                            file_name=path.name,
                            media_type="image",
                            analysis=analysis,
                        )
                    elif suffix in AUDIO_EXTENSIONS:
                        transcription = transcribe_audio(path)
                        result = MediaResult(
                            file_name=path.name,
                            media_type="audio",
                            transcription=transcription,
                        )
                    else:
                        result = MediaResult(
                            file_name=path.name,
                            media_type="unknown",
                            error=f"Unsupported extension: {suffix}",
                        )
                except Exception as exc:  # noqa: BLE001
                    result = MediaResult(
                        file_name=path.name,
                        media_type="unknown",
                        error=str(exc),
                    )
                results.append(result)
                job.progress = round(index / total, 4)
                self._log(job, f"Progress updated: {job.progress * 100:.1f}%")

            job.result = results
            self._save_result(job)
            job.status = JobStatus.completed
            job.progress = 1.0
            self._log(job, "Processing completed")
        except Exception as exc:  # noqa: BLE001
            job.status = JobStatus.failed
            job.error = str(exc)
            self._log(job, f"Processing failed: {exc}")

    def _save_result(self, job: JobDetails) -> None:
        output_path = settings.result_dir / f"{job.job_id}.json"
        output_path.write_text(json.dumps(job.model_dump(mode="json"), indent=2), encoding="utf-8")
        self._log(job, f"Saved result to {output_path}")


job_manager = JobManager()
