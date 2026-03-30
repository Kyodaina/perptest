from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PrecisionMode(str, Enum):
    fast = "fast"
    balanced = "balanced"
    precise = "precise"


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class AnalysisOutput(BaseModel):
    visible_text: str
    prices: list[str]
    marketing_intent: str
    importance_score: int = Field(ge=1, le=5)


class MediaResult(BaseModel):
    file_name: str
    media_type: str
    analysis: AnalysisOutput | None = None
    transcription: str | None = None
    error: str | None = None


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime


class JobDetails(BaseModel):
    job_id: str
    status: JobStatus
    progress: float
    precision_mode: PrecisionMode
    logs: list[str]
    files: list[str]
    created_at: datetime
    updated_at: datetime
    result: list[MediaResult] = Field(default_factory=list)
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
