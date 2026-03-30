from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.job_manager import JobManager
from app.services.schemas import AnalyzeRequest

router = APIRouter(prefix="/api")

job_manager: JobManager | None = None
staging_dir: Path | None = None


class AnalyzePayload(AnalyzeRequest):
    paths: list[str]


def configure(manager: JobManager, staging: Path):
    global job_manager, staging_dir
    job_manager = manager
    staging_dir = staging


@router.post("/upload")
async def upload(files: list[UploadFile] = File(...)):
    if not staging_dir:
        raise HTTPException(status_code=500, detail="Server not initialized")

    saved_paths = []
    for file in files:
        out = staging_dir / file.filename
        content = await file.read()
        out.write_bytes(content)
        saved_paths.append(str(out))

    return {"files": saved_paths}


@router.post("/analyze")
async def analyze(payload: AnalyzePayload):
    if not job_manager:
        raise HTTPException(status_code=500, detail="Server not initialized")

    config = AnalyzeRequest(
        model_family=payload.model_family,
        model_size=payload.model_size,
        precision=payload.precision,
        frame_interval_seconds=payload.frame_interval_seconds,
    )
    job_id = job_manager.create_job([Path(p) for p in payload.paths], config)
    return {"job_id": job_id}


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    if not job_manager:
        raise HTTPException(status_code=500, detail="Server not initialized")
    if job_id not in job_manager.jobs:
        raise HTTPException(status_code=404, detail="Unknown job")
    return job_manager.get_job(job_id)
