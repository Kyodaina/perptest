import os
from threading import Lock

import torch
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

from app.config import MODEL_CACHE_DIR, QWEN_MODEL_ID


class QwenModelLoader:
    """Lazy singleton loader for Qwen2.5-VL resources."""

    _lock = Lock()
    _model = None
    _processor = None

    @classmethod
    def load(cls):
        with cls._lock:
            if cls._model is None or cls._processor is None:
                os.environ["HF_HOME"] = str(MODEL_CACHE_DIR)
                cls._processor = AutoProcessor.from_pretrained(
                    QWEN_MODEL_ID,
                    cache_dir=str(MODEL_CACHE_DIR),
                    trust_remote_code=True,
                )
                dtype = torch.float16 if torch.cuda.is_available() else torch.float32
                cls._model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                    QWEN_MODEL_ID,
                    torch_dtype=dtype,
                    device_map="auto",
                    cache_dir=str(MODEL_CACHE_DIR),
                    trust_remote_code=True,
                )
            return cls._model, cls._processor
