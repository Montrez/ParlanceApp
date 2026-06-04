#!/usr/bin/env python3
"""Re-merge and save Parlance SLMs from a saved LoRA adapter (no retraining)."""

import argparse
import sys
from pathlib import Path

TRAINING_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TRAINING_DIR))

from transformers import AutoTokenizer  # noqa: E402

from finetune_slm import BASE_MODEL, LANG_DIRS, save_merged_fp16_model  # noqa: E402


def find_adapter_dir(lang: str) -> Path | None:
    ckpt_root = TRAINING_DIR / "checkpoints" / f"parlance-{lang}"
    final = ckpt_root / "final_adapter"
    if final.exists():
        return final
    if not ckpt_root.exists():
        return None
    candidates = sorted(
        (p for p in ckpt_root.iterdir() if p.is_dir() and p.name.startswith("checkpoint-")),
        key=lambda p: int(p.name.split("-")[-1]) if p.name.split("-")[-1].isdigit() else 0,
    )
    for path in reversed(candidates):
        if (path / "adapter_model.safetensors").exists():
            return path
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", choices=["es", "fr", "both"], default="both")
    args = parser.parse_args()

    langs = ["es", "fr"] if args.lang == "both" else [args.lang]
    for lang in langs:
        adapter_dir = find_adapter_dir(lang)
        output_dir = TRAINING_DIR / "models" / f"parlance-{lang}"
        if adapter_dir is None:
            print(f"SKIP {lang}: no LoRA adapter under checkpoints/parlance-{lang}")
            continue
        print(f"  Adapter: {adapter_dir}")
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
        print(f"Re-exporting {lang} → {output_dir}")
        save_merged_fp16_model(adapter_dir, output_dir, tokenizer)
        print(f"  Done: {output_dir / 'model.safetensors'}")


if __name__ == "__main__":
    main()
