from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ModelFamily = Literal["qwen2.5-vl", "llava"]
ModelSize = Literal["small", "medium", "large"]
PrecisionMode = Literal["fast", "balanced", "precise"]
MarketingIntent = Literal["discount", "urgency", "branding", "awareness"]


class AnalyzeRequest(BaseModel):
    model_family: ModelFamily = "qwen2.5-vl"
    model_size: ModelSize = "small"
    precision: PrecisionMode = "balanced"
    frame_interval_seconds: float = Field(default=1.5, ge=0.5, le=5.0)


class FrameResult(BaseModel):
    frame_path: str
    timestamp_seconds: float
    visible_text: str
    prices: list[str]
    key_messages: list[str]
    cta: str
    marketing_intent: MarketingIntent
    importance_score: int = Field(ge=1, le=5)


class AudioSegment(BaseModel):
    start: float
    end: float
    text: str


class FileResult(BaseModel):
    filename: str
    file_type: Literal["image", "video"]
    frames: list[FrameResult] = []
    audio_transcript: list[AudioSegment] = []


class JobState(BaseModel):
    job_id: str
    status: Literal["queued", "running", "done", "error"]
    progress: float = Field(ge=0, le=100)
    logs: list[str] = []
    results: list[FileResult] = []
    error: str | None = None
