#!/usr/bin/env python3
"""Merge imported GEC corpora + Parlance seeds into train/valid splits.

No per-level cap. Judgment-gold sentences are held out of training.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

TRAINING_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TRAINING_DIR))

from gec_format import extract_user_sentence, seed_row_to_gec  # noqa: E402

SEED_FILES = {
    "es": TRAINING_DIR.parent / "Parlance" / "training" / "seed_es.jsonl",
    "fr": TRAINING_DIR.parent / "Parlance" / "training" / "seed_fr.jsonl",
}
GOLD_PATHS = (
    TRAINING_DIR / "golden" / "gec_judgment.jsonl",
    TRAINING_DIR / "golden" / "gec_understanding_fr.jsonl",
    TRAINING_DIR / "golden" / "gec_understanding_es.jsonl",
)


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def gold_holdout() -> dict[str, set[str]]:
    held: dict[str, set[str]] = {"es": set(), "fr": set(), "en": set()}
    for path in GOLD_PATHS:
        for row in load_jsonl(path):
            lang = row.get("lang") or "fr"
            sentence = (row.get("sentence") or "").strip().lower()
            if lang in held and sentence:
                held[lang].add(sentence)
    return held


def status_of(example: dict) -> str:
    for msg in example.get("messages", []):
        if msg.get("role") != "assistant":
            continue
        try:
            return json.loads(msg["content"]).get("status") or ""
        except (json.JSONDecodeError, TypeError):
            return ""
    return ""


QUALITY_KEEP = {"cancre", "cowsl2h", "parlance_seed", "gec_targets"}


def merge_lang(
    lang: str,
    split: float,
    seed: int,
    *,
    quality: bool = False,
    upsample_targets: int = 1,
) -> None:
    random.seed(seed)
    held = gold_holdout().get(lang, set())
    imported = TRAINING_DIR / "data" / "gec" / lang / "imported.jsonl"
    examples = load_jsonl(imported)
    if quality:
        examples = [
            ex
            for ex in examples
            if (ex.get("source") or "") in QUALITY_KEEP
            and "fix grammar:" not in extract_user_sentence(ex).lower()
        ]
    target_path = TRAINING_DIR / "data" / "gec" / lang / "targets.jsonl"
    if target_path.exists():
        extras = load_jsonl(target_path)
        examples.extend(extras * max(1, upsample_targets))
    seed_path = SEED_FILES.get(lang)
    if seed_path and seed_path.exists():
        for raw in load_jsonl(seed_path):
            converted = seed_row_to_gec(raw, lang, source="parlance_seed")
            if converted:
                examples.append(converted)

    unique: list[dict] = []
    seen: set[str] = set()
    held_out = 0
    for example in examples:
        sentence = extract_user_sentence(example).lower()
        if not sentence:
            continue
        if sentence in held:
            held_out += 1
            continue
        if sentence in seen:
            continue
        seen.add(sentence)
        unique.append(example)

    random.shuffle(unique)
    split_at = int(len(unique) * split)
    train, valid = unique[:split_at], unique[split_at:]
    if upsample_targets > 1:
        extras = [ex for ex in train if ex.get("source") == "gec_targets"]
        train.extend(extras * (upsample_targets - 1))
        random.shuffle(train)
    out_dir = TRAINING_DIR / "data" / "gec" / lang
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in (("train", train), ("valid", valid)):
        path = out_dir / f"{name}.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    counts = {"Excellent": 0, "Needs Improvement": 0}
    for row in unique:
        st = status_of(row)
        if st in counts:
            counts[st] += 1
    print(
        f"  {lang}: {len(train):,} train / {len(valid):,} valid "
        f"(held out {held_out} gold sentences) "
        f"Excellent={counts['Excellent']:,} NI={counts['Needs Improvement']:,}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare GEC train/valid splits")
    parser.add_argument("--lang", choices=["es", "fr", "en", "all"], default="all")
    parser.add_argument("--split", type=float, default=0.9)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--quality",
        action="store_true",
        help="Keep cancre, Parlance seeds, and GEC targets. Drop multilingual-gec.",
    )
    parser.add_argument("--upsample-targets", type=int, default=1)
    args = parser.parse_args()
    langs = ["es", "fr", "en"] if args.lang == "all" else [args.lang]
    for lang in langs:
        merge_lang(
            lang,
            args.split,
            args.seed,
            quality=args.quality,
            upsample_targets=args.upsample_targets,
        )


if __name__ == "__main__":
    main()
