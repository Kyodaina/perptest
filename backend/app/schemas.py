from typing import Literal

from pydantic import BaseModel, Field


MarketingIntent = Literal["discount", "urgency", "branding", "awareness"]


class AnalysisResult(BaseModel):
    visible_text: str = Field(default="")
    prices: list[str] = Field(default_factory=list)
    marketing_intent: MarketingIntent = Field(default="awareness")
    importance_score: int = Field(default=3, ge=1, le=5)


class ImageResult(BaseModel):
    file_name: str
    status: Literal["queued", "running", "completed", "failed"]
    progress: float = Field(default=0.0, ge=0, le=100)
    logs: list[str] = Field(default_factory=list)
    output: AnalysisResult | None = None
    error: str | None = None
