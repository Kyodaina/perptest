from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class UploadItem(BaseModel):
    file_id: str
    filename: str
    media_type: str


class UploadResponse(BaseModel):
    items: list[UploadItem]


class StartJobRequest(BaseModel):
    file_ids: list[str] = Field(min_length=1)
    precision: Literal["fast", "balanced", "precise"] = "balanced"


class ImageAnalysisResult(BaseModel):
    visible_text: str
    prices: list[str]
    key_messages: list[str]
    cta: str
    marketing_intent: Literal["discount", "urgency", "branding", "awareness"]
    importance_score: int = Field(ge=1, le=5)


class ProcessedFileResult(BaseModel):
    file_id: str
    filename: str
    file_type: Literal["image", "audio"]
    image_analysis: ImageAnalysisResult | None = None
    transcription: str | None = None


class JobResponse(BaseModel):
    job_id: str


class JobState(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    progress: float
    logs: list[str]
    created_at: datetime
    finished_at: datetime | None = None
    results: list[ProcessedFileResult] = Field(default_factory=list)
    error: str | None = None
