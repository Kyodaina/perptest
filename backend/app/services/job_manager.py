from __future__ import annotations

import queue
import shutil
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path

from .media_processor import IMAGE_EXTS, VIDEO_EXTS, MediaProcessor
from .schemas import AnalyzeRequest, JobState


@dataclass
class JobPayload:
    job_id: str
    files: list[Path]
    config: AnalyzeRequest


class JobManager:
    def __init__(self, upload_dir: Path, output_dir: Path, model_root: Path) -> None:
        self.upload_dir = upload_dir
        self.output_dir = output_dir
        self.media_processor = MediaProcessor(upload_dir, output_dir, model_root)
        self.jobs: dict[str, JobState] = {}
        self._queue: queue.Queue[JobPayload] = queue.Queue()
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def create_job(self, source_files: list[Path], config: AnalyzeRequest) -> str:
        job_id = str(uuid.uuid4())
        job_dir = self.upload_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        staged_files = []
        for src in source_files:
            dst = job_dir / src.name
            shutil.move(str(src), str(dst))
            staged_files.append(dst)

        self.jobs[job_id] = JobState(job_id=job_id, status="queued", progress=0, logs=["Job queued"])
        self._queue.put(JobPayload(job_id=job_id, files=staged_files, config=config))
        return job_id

    def get_job(self, job_id: str) -> JobState:
        return self.jobs[job_id]

    def _log(self, job_id: str, message: str):
        state = self.jobs[job_id]
        state.logs.append(message)

    def _run(self):
        while True:
            payload = self._queue.get()
            state = self.jobs[payload.job_id]
            try:
                state.status = "running"
                total = len(payload.files)

                for i, file_path in enumerate(payload.files, start=1):
                    ext = file_path.suffix.lower()
                    self._log(payload.job_id, f"Processing {file_path.name}")
                    if ext in IMAGE_EXTS:
                        result = self.media_processor.process_image(
                            file_path,
                            payload.config.model_family,
                            payload.config.model_size,
                            payload.config.precision,
                        )
                    elif ext in VIDEO_EXTS:
                        result = self.media_processor.process_video(
                            file_path,
                            payload.config.model_family,
                            payload.config.model_size,
                            payload.config.precision,
                            payload.config.frame_interval_seconds,
                        )
                    else:
                        self._log(payload.job_id, f"Skipping unsupported file: {file_path.name}")
                        continue

                    state.results.append(result)
                    state.progress = round((i / total) * 100, 2)
                    self._log(payload.job_id, f"Completed {file_path.name}")

                state.status = "done"
                state.progress = 100
                self._log(payload.job_id, "Job completed")
            except Exception as exc:
                state.status = "error"
                state.error = str(exc)
                self._log(payload.job_id, f"Job failed: {exc}")
            finally:
                self._queue.task_done()
