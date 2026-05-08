#!/usr/bin/env python3
"""
Split existing mixed training data into per-language datasets.
Reads all JSONL files in training/data/ and routes examples
to training/data/spanish/ or training/data/french/ based on content.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
ES_DIR = DATA_DIR / "spanish"
FR_DIR = DATA_DIR / "french"

ES_DIR.mkdir(exist_ok=True)
FR_DIR.mkdir(exist_ok=True)


def detect_language(example: dict) -> str:
    """Detect language from the training example's system/user message."""
    messages = example.get("messages", [])
    text = " ".join(m.get("content", "") for m in messages).lower()
    if "spanish" in text or "español" in text:
        return "es"
    if "french" in text or "français" in text:
        return "fr"
    return "unknown"


def split_file(filepath: Path, es_out, fr_out) -> tuple[int, int]:
    es_count = 0
    fr_count = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                example = json.loads(line)
                lang = detect_language(example)
                if lang == "es":
                    es_out.write(line + "\n")
                    es_count += 1
                elif lang == "fr":
                    fr_out.write(line + "\n")
                    fr_count += 1
            except json.JSONDecodeError:
                continue
    return es_count, fr_count


def main():
    source_files = sorted(DATA_DIR.glob("*.jsonl"))
    if not source_files:
        print("No JSONL files found in training/data/")
        return

    total_es = 0
    total_fr = 0

    with open(ES_DIR / "base.jsonl", "w", encoding="utf-8") as es_out, \
         open(FR_DIR / "base.jsonl", "w", encoding="utf-8") as fr_out:

        for filepath in source_files:
            es, fr = split_file(filepath, es_out, fr_out)
            total_es += es
            total_fr += fr
            print(f"  {filepath.name}: {es} Spanish, {fr} French")

    print(f"\nTotal: {total_es} Spanish → data/spanish/base.jsonl")
    print(f"Total: {total_fr} French → data/french/base.jsonl")


if __name__ == "__main__":
    main()
