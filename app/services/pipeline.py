from pathlib import Path

from app.config import SUPPORTED_AUDIO_EXTENSIONS, SUPPORTED_IMAGE_EXTENSIONS
from app.models.qwen_loader import QwenVLAnalyzer
from app.models.whisper_loader import WhisperTranscriber
from app.schemas import ProcessedFileResult


class ProcessingPipeline:
    def __init__(self) -> None:
        self._qwen: QwenVLAnalyzer | None = None
        self._whisper: WhisperTranscriber | None = None

    @property
    def qwen(self) -> QwenVLAnalyzer:
        if self._qwen is None:
            self._qwen = QwenVLAnalyzer()
        return self._qwen

    @property
    def whisper(self) -> WhisperTranscriber:
        if self._whisper is None:
            self._whisper = WhisperTranscriber()
        return self._whisper

    def process_file(self, file_id: str, filename: str, path: Path, precision: str) -> ProcessedFileResult:
        ext = path.suffix.lower()
        if ext in SUPPORTED_IMAGE_EXTENSIONS:
            result = self.qwen.analyze_image(str(path), precision=precision)
            return ProcessedFileResult(
                file_id=file_id,
                filename=filename,
                file_type="image",
                image_analysis=result,
            )

        if ext in SUPPORTED_AUDIO_EXTENSIONS:
            transcript = self.whisper.transcribe(str(path))
            return ProcessedFileResult(
                file_id=file_id,
                filename=filename,
                file_type="audio",
                transcription=transcript,
            )

        raise ValueError(f"Unsupported file extension: {ext}")
