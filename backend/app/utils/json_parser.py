import json
import re
from typing import Any

from backend.app.schemas import AnalysisOutput


INTENTS = {"discount", "urgency", "branding", "awareness"}


def _extract_json_blob(raw_text: str) -> str:
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model output")
    return match.group(0)


def parse_analysis_json(raw_text: str) -> AnalysisOutput:
    blob = _extract_json_blob(raw_text)
    payload: dict[str, Any] = json.loads(blob)

    if payload.get("marketing_intent") not in INTENTS:
        payload["marketing_intent"] = "awareness"

    score = int(payload.get("importance_score", 3))
    payload["importance_score"] = min(5, max(1, score))

    payload.setdefault("visible_text", "")
    payload.setdefault("prices", [])
    payload.setdefault("key_messages", [])
    payload.setdefault("cta", "")

    return AnalysisOutput.model_validate(payload)
