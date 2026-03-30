import json
import re
from pathlib import Path

from PIL import Image

from app.config import MAX_IMAGE_EDGE
from app.schemas import AnalysisResult
from app.services.model_loader import QwenModelLoader

SYSTEM_INSTRUCTION = (
    "You analyze advertisement images. Return strict JSON only with keys: "
    "visible_text (string), prices (array of strings), "
    "marketing_intent (one of: discount, urgency, branding, awareness), "
    "importance_score (integer 1-5)."
)


class AdAnalyzer:
    def __init__(self):
        self.model, self.processor = QwenModelLoader.load()

    def _extract_json(self, raw_text: str) -> AnalysisResult:
        match = re.search(r"\{.*\}", raw_text, re.S)
        if not match:
            raise ValueError(f"No JSON object found in model output: {raw_text[:250]}")

        payload = json.loads(match.group(0))
        payload.setdefault("visible_text", "")
        payload.setdefault("prices", [])
        payload.setdefault("marketing_intent", "awareness")
        payload.setdefault("importance_score", 3)

        if payload["marketing_intent"] not in {"discount", "urgency", "branding", "awareness"}:
            payload["marketing_intent"] = "awareness"

        payload["importance_score"] = max(1, min(5, int(payload["importance_score"])))
        payload["prices"] = [str(v) for v in payload.get("prices", [])]
        payload["visible_text"] = str(payload.get("visible_text", ""))

        return AnalysisResult(**payload)

    def analyze(self, image_path: Path) -> AnalysisResult:
        image = Image.open(image_path).convert("RGB")
        # Avoid extreme visual token counts on very large images.
        image.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE))
        user_prompt = (
            "Extract all visible ad text and infer marketing strategy. "
            "Detect price strings exactly as seen (e.g. 2990 Ft, $49.99). "
            "Respond JSON only."
        )

        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": SYSTEM_INSTRUCTION}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": user_prompt},
                ],
            },
        ]

        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=[text], images=[image], return_tensors="pt")
        if getattr(self.model, "device", None):
            inputs = inputs.to(self.model.device)

        generated_ids = self.model.generate(**inputs, max_new_tokens=256)
        decoded = self.processor.batch_decode(
            generated_ids[:, inputs.input_ids.shape[1] :],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        )[0]
        return self._extract_json(decoded)
