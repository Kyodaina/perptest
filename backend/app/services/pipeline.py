from pathlib import Path

import torch
from PIL import Image

from backend.app.schemas import AnalysisOutput, PrecisionMode
from backend.app.services.model_manager import PRECISION_CONFIGS, model_manager
from backend.app.utils.json_parser import parse_analysis_json

PROMPT_TEMPLATE = """
You are a strict ad intelligence extractor.
Analyze this advertisement image and return ONLY JSON with this exact schema:
{
  "visible_text": "string",
  "prices": ["string"],
  "key_messages": ["string"],
  "cta": "string",
  "marketing_intent": "discount | urgency | branding | awareness",
  "importance_score": 1-5
}
Rules:
- No markdown.
- Keep only facts visible in image.
- If data is missing, return empty strings/arrays.
""".strip()


def analyze_image(image_path: Path, mode: PrecisionMode) -> AnalysisOutput:
    llava_model, llava_processor = model_manager.load_llava()
    cfg = PRECISION_CONFIGS[mode.value]

    image = Image.open(image_path).convert("RGB")
    conversation = [
        {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": PROMPT_TEMPLATE},
            ],
        },
    ]
    prompt = llava_processor.apply_chat_template(conversation, add_generation_prompt=True)

    inputs = llava_processor(images=image, text=prompt, return_tensors="pt")
    inputs = {k: v.to(llava_model.device) if torch.is_tensor(v) else v for k, v in inputs.items()}

    output = llava_model.generate(
        **inputs,
        max_new_tokens=cfg.max_new_tokens,
        temperature=cfg.temperature,
        top_p=cfg.top_p,
        do_sample=True,
    )
    decoded = llava_processor.decode(output[0], skip_special_tokens=True)
    return parse_analysis_json(decoded)


def transcribe_audio(audio_path: Path) -> str:
    whisper_model = model_manager.load_whisper()
    result = whisper_model.transcribe(str(audio_path), fp16=False)
    return result.get("text", "").strip()
