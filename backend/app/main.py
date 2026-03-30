from pathlib import Path
from typing import Annotated

import aiofiles
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.schemas import JobCreateResponse, JobDetails, PrecisionMode
from backend.app.services.job_manager import job_manager

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory="frontend"), name="assets")
app.mount("/uploads", StaticFiles(directory=str(settings.upload_dir)), name="uploads")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse("frontend/index.html")


@app.post("/api/upload", response_model=JobCreateResponse)
async def upload_files(
    files: Annotated[list[UploadFile], File(...)],
    precision_mode: Annotated[PrecisionMode, Form()] = PrecisionMode.balanced,
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    saved_paths: list[Path] = []
    for upload in files:
        destination = settings.upload_dir / upload.filename
        async with aiofiles.open(destination, "wb") as out:
            while content := await upload.read(1024 * 1024):
                await out.write(content)
        saved_paths.append(destination)

    job = job_manager.create_job(saved_paths, precision_mode)
    return JobCreateResponse(job_id=job.job_id, status=job.status, created_at=job.created_at)


@app.get("/api/jobs/{job_id}", response_model=JobDetails)
async def get_job(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
