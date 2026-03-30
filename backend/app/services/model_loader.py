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
                if torch.cuda.is_available():
                    dtype = torch.float16
                    device_map = "auto"
                else:
                    # CPU-safe path: keep memory tighter and deterministic.
                    dtype = torch.float32
                    device_map = "cpu"
                cls._model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                    QWEN_MODEL_ID,
                    torch_dtype=dtype,
                    device_map=device_map,
                    low_cpu_mem_usage=True,
                    cache_dir=str(MODEL_CACHE_DIR),
                    trust_remote_code=True,
                )
            return cls._model, cls._processor
