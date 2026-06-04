#!/usr/bin/env python3
"""Load and run Parlance fine-tuned Qwen SLMs (Spanish / French)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import torch
from parlance_slm_validate import (
    french_coach_system_prompt,
    french_coach_user_prompt,
    sanitize_feedback,
    spanish_coach_system_prompt,
    spanish_coach_user_prompt,
)
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

TRAINING_DIR = Path(__file__).resolve().parent
BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
MODEL_DIRS = {
    "es": TRAINING_DIR / "models" / "parlance-es",
    "fr": TRAINING_DIR / "models" / "parlance-fr",
}
# Merged FP16 export is ~940 MB; old 4-bit broken exports are ~437 MB
MIN_MERGED_BYTES = 800_000_000


def is_model_ready(lang: str) -> bool:
    path = MODEL_DIRS[lang] / "model.safetensors"
    return path.exists() and path.stat().st_size >= MIN_MERGED_BYTES

_LANG_META = {
    "es": ("Spanish", "SPANISH", "tú/usted"),
    "fr": ("French", "FRENCH", "tu/vous"),
}


class ParlanceSLM:
    def __init__(self, lang: str, device: str | None = None):
        if lang not in MODEL_DIRS:
            raise ValueError(f"Unknown language: {lang}")
        model_dir = MODEL_DIRS[lang]
        weights = model_dir / "model.safetensors"
        if not weights.exists():
            raise FileNotFoundError(f"Model not found: {model_dir}")
        if weights.stat().st_size < MIN_MERGED_BYTES:
            raise FileNotFoundError(
                f"Model at {model_dir} is incomplete or an old 4-bit export. "
                f"Re-export merged weights (see training/TRAINING_STATUS.md)."
            )

        self.lang = lang
        self.device = device or ("mps" if torch.backends.mps.is_available() else "cpu")
        # Tokenizer from base hub (merged export may omit vocab files)
        self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
        dtype = torch.float16 if self.device == "mps" else torch.float32
        config = AutoConfig.from_pretrained(model_dir, trust_remote_code=True)
        if getattr(config, "quantization_config", None) is not None:
            del config.quantization_config
        self.model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            config=config,
            torch_dtype=dtype,
            trust_remote_code=True,
        ).to(self.device)
        self.model.eval()

    def analyze(self, sentence: str, level: str = "", max_new_tokens: int = 512, rag_context: str = "") -> dict[str, Any]:
        lang_name, _, _ = _LANG_META[self.lang]

        if self.lang == "es":
            system = spanish_coach_system_prompt(level, rag_context=rag_context)
            user = spanish_coach_user_prompt(sentence, level)
        else:
            system = french_coach_system_prompt(level, rag_context=rag_context)
            user = french_coach_user_prompt(sentence, level)

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        text = self.tokenizer.decode(
            out[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True
        )
        try:
            parsed = parse_feedback_json(text)
        except (ValueError, json.JSONDecodeError):
            from parlance_slm_validate import french_heuristic_feedback, heuristic_feedback

            if self.lang == "fr":
                return french_heuristic_feedback(sentence, level)
            return heuristic_feedback(sentence, level)
        return sanitize_feedback(sentence, parsed, level=level, lang=self.lang)


def parse_feedback_json(raw: str) -> dict[str, Any]:
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    start = cleaned.find("{")
    if start == -1:
        raise ValueError(f"No JSON in model output: {raw[:300]}")
    depth = 0
    end = -1
    for i, ch in enumerate(cleaned[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end == -1:
        raise ValueError(f"No JSON in model output: {raw[:300]}")
    snippet = cleaned[start : end + 1]
    try:
        data = json.loads(snippet)
    except json.JSONDecodeError:
        repaired = re.sub(r",\s*}", "}", snippet)
        data = json.loads(repaired)
    return normalize_feedback(data)


def normalize_feedback(raw: dict[str, Any]) -> dict[str, Any]:
    status = raw.get("status", "Excellent")
    if status not in ("Excellent", "Needs Improvement"):
        status = "Excellent"
    out: dict[str, Any] = {
        "status": status,
        "grammar_rule": raw.get("grammar_rule") or raw.get("grammarRule") or "",
        "explanation": raw.get("explanation") or "",
    }
    for key in ("correction", "register", "next_level_alt", "target_level_alt", "tip"):
        val = raw.get(key)
        if val is not None and val != "":
            out[key] = val
    assessed = raw.get("assessed_level") or raw.get("assessedLevel")
    if assessed is not None and str(assessed).strip():
        out["assessed_level"] = assessed
    complexity = raw.get("complexity_note") or raw.get("complexityNote")
    if complexity is not None and str(complexity).strip():
        out["complexity_note"] = complexity
    return out


# Lazy singletons per language
_engines: dict[str, ParlanceSLM] = {}


def get_engine(lang: str) -> ParlanceSLM:
    if lang not in _engines:
        _engines[lang] = ParlanceSLM(lang)
    return _engines[lang]
