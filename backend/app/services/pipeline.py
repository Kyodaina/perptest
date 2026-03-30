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
  "marketing_intent": "discount | urgency | branding | awareness",
  "importance_score": 1-5
}
Rules:
- No markdown.
- visible_text must contain ALL readable text from the image, unfiltered,
  without summarization or interpretation.
- If data is missing, return empty strings/arrays.
""".strip()


def analyze_image(image_path: Path, mode: PrecisionMode) -> AnalysisOutput:
    qwen_model, qwen_processor = model_manager.load_qwen_vl()
    cfg = PRECISION_CONFIGS[mode.value]

    image = Image.open(image_path).convert("RGB")
    conversation = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": PROMPT_TEMPLATE},
            ],
        },
    ]
    prompt = qwen_processor.apply_chat_template(conversation, tokenize=False, add_generation_prompt=True)

    inputs = qwen_processor(images=image, text=prompt, return_tensors="pt")
    inputs = {k: v.to(qwen_model.device) if torch.is_tensor(v) else v for k, v in inputs.items()}

    output = qwen_model.generate(
        **inputs,
        max_new_tokens=cfg.max_new_tokens,
        temperature=cfg.temperature,
        top_p=cfg.top_p,
        do_sample=True,
    )

    # Decode only generated continuation to avoid prompt echo in output,
    # which can corrupt JSON extraction.
    input_token_count = inputs["input_ids"].shape[1]
    generated = output[0][input_token_count:]
    decoded = qwen_processor.decode(generated, skip_special_tokens=True).strip()
    return parse_analysis_json(decoded)


def transcribe_audio(audio_path: Path) -> str:
    whisper_model = model_manager.load_whisper()
    result = whisper_model.transcribe(str(audio_path), fp16=False)
    return result.get("text", "").strip()
