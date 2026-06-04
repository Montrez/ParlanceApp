#!/usr/bin/env python3
"""Upsert golden seed rows into assessed_level_{es,fr}.jsonl (by sentence text)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from coach_training_format import legacy_seed_to_training

TRAINING_DIR = Path(__file__).resolve().parent
DATA = TRAINING_DIR / "data"


def sentence_key(example: dict) -> str:
    for msg in example.get("messages", []):
        if msg.get("role") == "user" and '"' in msg.get("content", ""):
            c = msg["content"]
            return c[c.index('"') + 1 : c.rindex('"')].strip().lower()
    return ""


def merge_lang(lang: str, seed: Path, target: Path) -> None:
    if not seed.exists():
        raise SystemExit(f"Missing seed file: {seed}")

    seeds: list[dict] = []
    for line in seed.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            seeds.append(legacy_seed_to_training(json.loads(line), lang))

    existing: list[dict] = []
    keys: set[str] = set()
    if target.exists():
        for line in target.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            ex = json.loads(line)
            k = sentence_key(ex)
            if k in keys:
                continue
            keys.add(k)
            existing.append(ex)

    upserted = 0
    for ex in seeds:
        k = sentence_key(ex)
        if k in keys:
            existing = [e for e in existing if sentence_key(e) != k]
            upserted += 1
        keys.add(k)
        existing.append(ex)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in existing) + "\n",
        encoding="utf-8",
    )
    print(f"Upserted {upserted} golden seed(s) → {target} ({len(existing)} total)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lang",
        choices=["es", "fr", "both"],
        default="both",
        help="Language seed set to merge (default: both)",
    )
    args = parser.parse_args()

    langs = ["es", "fr"] if args.lang == "both" else [args.lang]
    for lang in langs:
        folder = "spanish" if lang == "es" else "french"
        merge_lang(
            lang,
            DATA / folder / f"seed_assessed_level_{lang}.jsonl",
            DATA / folder / f"assessed_level_{lang}.jsonl",
        )


if __name__ == "__main__":
    main()
