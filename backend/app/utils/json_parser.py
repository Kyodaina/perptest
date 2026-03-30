import json
import re
from typing import Any

from backend.app.schemas import AnalysisOutput


INTENTS = {"discount", "urgency", "branding", "awareness"}


def _extract_json_blob(raw_text: str) -> str:
    # Collect all potential JSON objects and prefer the last one because
    # VLM outputs often include previous turns or prompt echoes.
    matches = re.findall(r"\{[\s\S]*?\}", raw_text)
    if not matches:
        raise ValueError("No JSON object found in model output")
    return matches[-1]


def _normalize_json_string(blob: str) -> str:
    normalized = blob.strip()
    normalized = normalized.replace("“", '"').replace("”", '"')
    normalized = normalized.replace("’", "'")
    # Repair model-produced invalid escape sequences (e.g. \_ or \|)
    # by doubling only backslashes that are not valid JSON escapes.
    normalized = re.sub(r'\\(?!["\\/bfnrtu])', r"\\\\", normalized)
    # Remove trailing commas before object/array close tokens.
    normalized = re.sub(r",\s*([}\]])", r"\1", normalized)
    return normalized


def _load_json_with_fallback(blob: str) -> dict[str, Any]:
    first_error: Exception | None = None
    attempts = [blob, _normalize_json_string(blob)]
    for candidate in attempts:
        try:
            parsed: dict[str, Any] = json.loads(candidate)
            return parsed
        except json.JSONDecodeError as exc:
            if first_error is None:
                first_error = exc

    raise ValueError(f"Invalid JSON returned by model: {first_error}")


def parse_analysis_json(raw_text: str) -> AnalysisOutput:
    blob = _extract_json_blob(raw_text)
    payload = _load_json_with_fallback(blob)

    if payload.get("marketing_intent") not in INTENTS:
        payload["marketing_intent"] = "awareness"

    score = int(payload.get("importance_score", 3))
    payload["importance_score"] = min(5, max(1, score))

    payload.setdefault("visible_text", "")
    payload.setdefault("prices", [])

    return AnalysisOutput.model_validate(payload)
