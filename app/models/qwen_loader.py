import json
import os
import re
from dataclasses import dataclass
from typing import Any

import torch
from PIL import Image
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

from app.config import QWEN_LOCAL_DIR, QWEN_MODEL_ID


@dataclass
class QwenPrecisionConfig:
    max_new_tokens: int
    temperature: float
    top_p: float


PRECISION_CONFIGS = {
    "fast": QwenPrecisionConfig(max_new_tokens=180, temperature=0.1, top_p=0.8),
    "balanced": QwenPrecisionConfig(max_new_tokens=280, temperature=0.15, top_p=0.9),
    "precise": QwenPrecisionConfig(max_new_tokens=420, temperature=0.2, top_p=0.92),
}


class QwenVLAnalyzer:
    def __init__(self) -> None:
        os.environ.setdefault("HF_HOME", str(QWEN_LOCAL_DIR.parent))
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            QWEN_MODEL_ID,
            cache_dir=str(QWEN_LOCAL_DIR.parent),
            torch_dtype=dtype,
            device_map="auto" if torch.cuda.is_available() else None,
        )
        if self.device == "cpu":
            self.model.to("cpu")

        self.processor = AutoProcessor.from_pretrained(
            QWEN_MODEL_ID,
            cache_dir=str(QWEN_LOCAL_DIR.parent),
        )

    def analyze_image(self, image_path: str, precision: str = "balanced") -> dict[str, Any]:
        config = PRECISION_CONFIGS[precision]

        prompt = (
            "Analyze this advertisement image and return only strict JSON with keys: "
            'visible_text (string), prices (array of strings), key_messages (array of strings), '
            'cta (string), marketing_intent (discount|urgency|branding|awareness), '
            "importance_score (integer 1-5). No markdown, no explanation."
        )

        image = Image.open(image_path).convert("RGB")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        inputs = self.processor(
            text=[text],
            images=[image],
            return_tensors="pt",
            padding=True,
        )
        if self.device == "cpu":
            inputs = {k: v.to("cpu") for k, v in inputs.items()}
        else:
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        generated = self.model.generate(
            **inputs,
            max_new_tokens=config.max_new_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            do_sample=True,
        )
        output_text = self.processor.batch_decode(generated, skip_special_tokens=True)[0]
        return self._normalize_response(output_text)

    def _normalize_response(self, raw_text: str) -> dict[str, Any]:
        match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
        if not match:
            raise ValueError(f"Qwen response did not include JSON: {raw_text}")

        parsed = json.loads(match.group(0))

        normalized = {
            "visible_text": str(parsed.get("visible_text", "")).strip(),
            "prices": [str(item).strip() for item in parsed.get("prices", []) if str(item).strip()],
            "key_messages": [
                str(item).strip() for item in parsed.get("key_messages", []) if str(item).strip()
            ],
            "cta": str(parsed.get("cta", "")).strip(),
            "marketing_intent": str(parsed.get("marketing_intent", "awareness")).strip().lower(),
            "importance_score": int(parsed.get("importance_score", 3)),
        }

        if normalized["marketing_intent"] not in {"discount", "urgency", "branding", "awareness"}:
            normalized["marketing_intent"] = "awareness"

        normalized["importance_score"] = max(1, min(5, normalized["importance_score"]))
        return normalized
