from dataclasses import dataclass

import whisper
from transformers import AutoProcessor, LlavaForConditionalGeneration

from backend.app.config import settings


@dataclass
class PrecisionConfig:
    max_new_tokens: int
    temperature: float
    top_p: float


PRECISION_CONFIGS = {
    "fast": PrecisionConfig(max_new_tokens=180, temperature=0.1, top_p=0.8),
    "balanced": PrecisionConfig(max_new_tokens=260, temperature=0.2, top_p=0.9),
    "precise": PrecisionConfig(max_new_tokens=350, temperature=0.3, top_p=0.95),
}


class ModelManager:
    def __init__(self) -> None:
        self._llava_model = None
        self._llava_processor = None
        self._whisper_model = None

    def load_llava(self) -> tuple[LlavaForConditionalGeneration, AutoProcessor]:
        if self._llava_model is None or self._llava_processor is None:
            self._llava_processor = AutoProcessor.from_pretrained(
                settings.llava_model_name,
                cache_dir=str(settings.model_dir / "llava"),
            )
            self._llava_model = LlavaForConditionalGeneration.from_pretrained(
                settings.llava_model_name,
                cache_dir=str(settings.model_dir / "llava"),
                device_map="auto",
                torch_dtype="auto",
            )
        return self._llava_model, self._llava_processor

    def load_whisper(self):
        if self._whisper_model is None:
            self._whisper_model = whisper.load_model(
                settings.whisper_model_name,
                download_root=str(settings.model_dir / "whisper"),
            )
        return self._whisper_model


model_manager = ModelManager()
