from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import torch
from PIL import Image
from transformers import pipeline

from .schemas import PrecisionMode

MODEL_MAP = {
    "qwen2.5-vl": {
        "small": "Qwen/Qwen2.5-VL-3B-Instruct",
        "medium": "Qwen/Qwen2.5-VL-7B-Instruct",
        "large": "Qwen/Qwen2.5-VL-72B-Instruct",
    },
    "llava": {
        "small": "llava-hf/llava-1.5-7b-hf",
        "medium": "llava-hf/llava-v1.6-mistral-7b-hf",
        "large": "llava-hf/llava-v1.6-34b-hf",
    },
}

PROMPT = """Analyze this advertisement frame and return STRICT JSON with this exact schema:
{
  \"visible_text\": \"string\",
  \"prices\": [\"2990 Ft\"],
  \"key_messages\": [\"string\"],
  \"cta\": \"string\",
  \"marketing_intent\": \"discount | urgency | branding | awareness\",
  \"importance_score\": 1-5
}
Rules:
- Output ONLY JSON.
- prices must be an array of strings.
- marketing_intent must be exactly one of the enum values.
- importance_score must be integer 1..5.
"""


class VisionLanguageService:
    def __init__(self, model_root: Path) -> None:
        self.model_root = model_root

    @staticmethod
    def _max_tokens(precision: PrecisionMode) -> int:
        return {"fast": 180, "balanced": 260, "precise": 360}[precision]

    @staticmethod
    def _temperature(precision: PrecisionMode) -> float:
        return {"fast": 0.0, "balanced": 0.1, "precise": 0.2}[precision]

    @lru_cache(maxsize=12)
    def get_pipeline(self, family: str, size: str):
        model_id = MODEL_MAP[family][size]
        model_dir = self.model_root / family / size
        model_dir.mkdir(parents=True, exist_ok=True)

        return pipeline(
            task="image-text-to-text",
            model=model_id,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            model_kwargs={"cache_dir": str(model_dir)},
        )

    @staticmethod
    def _default_payload() -> dict[str, Any]:
        return {
            "visible_text": "",
            "prices": [],
            "key_messages": [],
            "cta": "",
            "marketing_intent": "awareness",
            "importance_score": 3,
        }

    def _extract_json(self, raw_text: str) -> dict[str, Any]:
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        content = match.group(0) if match else raw_text.strip()

        try:
            parsed = json.loads(content)
        except Exception:
            return self._default_payload()

        if parsed.get("marketing_intent") not in {"discount", "urgency", "branding", "awareness"}:
            parsed["marketing_intent"] = "awareness"

        try:
            parsed["importance_score"] = max(1, min(5, int(parsed.get("importance_score", 3))))
        except Exception:
            parsed["importance_score"] = 3

        parsed["prices"] = [str(p) for p in parsed.get("prices", [])]
        parsed["key_messages"] = [str(m) for m in parsed.get("key_messages", [])]

        return {
            "visible_text": str(parsed.get("visible_text", "")),
            "prices": parsed["prices"],
            "key_messages": parsed["key_messages"],
            "cta": str(parsed.get("cta", "")),
            "marketing_intent": parsed["marketing_intent"],
            "importance_score": parsed["importance_score"],
        }

    @staticmethod
    def _extract_generated_text(output: Any) -> str:
        if not isinstance(output, list) or not output:
            return "{}"
        item = output[0]
        if isinstance(item, dict):
            if "generated_text" in item and isinstance(item["generated_text"], str):
                return item["generated_text"]
            if "generated_text" in item and isinstance(item["generated_text"], list):
                # chat-style output, take the last text chunk
                chunks = item["generated_text"]
                for chunk in reversed(chunks):
                    if isinstance(chunk, dict) and "content" in chunk:
                        content = chunk["content"]
                        if isinstance(content, str):
                            return content
                return str(chunks)
        return str(item)

    def analyze_image(self, image_path: Path, family: str, size: str, precision: PrecisionMode) -> dict[str, Any]:
        pipe = self.get_pipeline(family, size)
        image = Image.open(image_path).convert("RGB")

        generate_kwargs = {
            "max_new_tokens": self._max_tokens(precision),
            "temperature": self._temperature(precision),
            "do_sample": self._temperature(precision) > 0,
        }

        # Primary: chat-format multimodal payload (works for recent LLaVA/Qwen VLM pipelines).
        chat_messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": PROMPT},
                ],
            }
        ]

        try:
            out = pipe(text=chat_messages, images=[image], generate_kwargs=generate_kwargs)
        except Exception:
            # Fallback: explicit <image> token prefix.
            out = pipe(text=f"<image>\n{PROMPT}", images=[image], generate_kwargs=generate_kwargs)

        generated = self._extract_generated_text(out)
        return self._extract_json(generated)
