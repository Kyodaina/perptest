from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForVision2Seq, pipeline

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

    @staticmethod
    def _dtype():
        return torch.float16 if torch.cuda.is_available() else torch.float32

    def _build_pipeline(self, model_id: str, model_dir: Path):
        last_err: Exception | None = None
        for task_name in ("image-text-to-text", "image-to-text"):
            try:
                return pipeline(
                    task=task_name,
                    model=model_id,
                    torch_dtype=self._dtype(),
                    device_map="auto",
                    model_kwargs={"cache_dir": str(model_dir)},
                )
            except Exception as exc:
                last_err = exc
        raise RuntimeError(f"Unable to initialize multimodal pipeline for {model_id}: {last_err}")

    @lru_cache(maxsize=12)
    def get_backend(self, family: str, size: str):
        model_id = MODEL_MAP[family][size]
        model_dir = self.model_root / family / size
        model_dir.mkdir(parents=True, exist_ok=True)

        if family == "qwen2.5-vl":
            processor = AutoProcessor.from_pretrained(
                model_id,
                cache_dir=str(model_dir),
                trust_remote_code=True,
            )
            model = AutoModelForVision2Seq.from_pretrained(
                model_id,
                cache_dir=str(model_dir),
                torch_dtype=self._dtype(),
                device_map="auto",
                trust_remote_code=True,
            )
            return {"kind": "qwen_native", "processor": processor, "model": model}

        llava_pipe = self._build_pipeline(model_id, model_dir)
        return {"kind": "pipeline", "pipe": llava_pipe}

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
                chunks = item["generated_text"]
                for chunk in reversed(chunks):
                    if isinstance(chunk, dict) and "content" in chunk and isinstance(chunk["content"], str):
                        return chunk["content"]
                return str(chunks)
        return str(item)

    def _analyze_qwen_native(self, image: Image.Image, backend: dict[str, Any], precision: PrecisionMode) -> str:
        processor = backend["processor"]
        model = backend["model"]

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": PROMPT},
                ],
            }
        ]
        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = processor(text=[text], images=[image], return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        generated_ids = model.generate(
            **inputs,
            max_new_tokens=self._max_tokens(precision),
            temperature=self._temperature(precision),
            do_sample=self._temperature(precision) > 0,
        )

        prompt_len = inputs["input_ids"].shape[1]
        new_tokens = generated_ids[:, prompt_len:]
        return processor.batch_decode(new_tokens, skip_special_tokens=True)[0]

    def _analyze_pipeline(self, image: Image.Image, backend: dict[str, Any], precision: PrecisionMode) -> str:
        pipe = backend["pipe"]
        generate_kwargs = {
            "max_new_tokens": self._max_tokens(precision),
            "temperature": self._temperature(precision),
            "do_sample": self._temperature(precision) > 0,
        }

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
            out = pipe(text=f"<image>\n{PROMPT}", images=[image], generate_kwargs=generate_kwargs)
        return self._extract_generated_text(out)

    def analyze_image(self, image_path: Path, family: str, size: str, precision: PrecisionMode) -> dict[str, Any]:
        backend = self.get_backend(family, size)
        image = Image.open(image_path).convert("RGB")

        if backend["kind"] == "qwen_native":
            generated = self._analyze_qwen_native(image, backend, precision)
        else:
            generated = self._analyze_pipeline(image, backend, precision)

        return self._extract_json(generated)
