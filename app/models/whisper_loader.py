import os

import torch
from faster_whisper import WhisperModel

from app.config import WHISPER_LOCAL_DIR, WHISPER_MODEL_SIZE


class WhisperTranscriber:
    def __init__(self) -> None:
        os.environ.setdefault("HF_HOME", str(WHISPER_LOCAL_DIR.parent))
        compute_type = "float16" if torch.cuda.is_available() else "int8"
        self.model = WhisperModel(
            WHISPER_MODEL_SIZE,
            download_root=str(WHISPER_LOCAL_DIR),
            compute_type=compute_type,
        )

    def transcribe(self, audio_path: str) -> str:
        segments, _ = self.model.transcribe(audio_path, vad_filter=True)
        return " ".join(segment.text.strip() for segment in segments if segment.text).strip()
