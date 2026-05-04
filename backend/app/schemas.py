from pydantic import BaseModel


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class TranscriptResult(BaseModel):
    language: str
    duration_seconds: float
    formatted_transcript: str
    segments: list[TranscriptSegment]
