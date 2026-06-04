#!/usr/bin/env python3
"""
Rewrite training JSONL to the assessed_level inference schema.

Usage:
    python migrate_training_schema.py --lang es
    python migrate_training_schema.py --lang both --include-train-valid
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from coach_training_format import legacy_seed_to_training, migrate_training_example

TRAINING_DIR = Path(__file__).resolve().parent
DATA = TRAINING_DIR / "data"


def migrate_file(src: Path, dst: Path, lang: str, *, append: bool = False) -> tuple[int, int]:
    ok = skip = 0
    dst.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with open(src, encoding="utf-8") as fin, open(dst, mode, encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                skip += 1
                continue

            if "messages" in row:
                out = migrate_training_example(row, lang)
            elif "sentence" in row or "input_sentence" in row:
                try:
                    out = legacy_seed_to_training(row, lang)
                except ValueError:
                    skip += 1
                    continue
            else:
                skip += 1
                continue

            if not out:
                skip += 1
                continue
            fout.write(json.dumps(out, ensure_ascii=False) + "\n")
            ok += 1
    return ok, skip


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate SLM training data to assessed_level schema")
    parser.add_argument("--lang", choices=["es", "fr", "both"], default="es")
    parser.add_argument(
        "--include-train-valid",
        action="store_true",
        help="Also migrate existing train.jsonl / valid.jsonl (not only source shards)",
    )
    args = parser.parse_args()

    langs = ["es", "fr"] if args.lang == "both" else [args.lang]

    for lang in langs:
        lang_dir = DATA / ("spanish" if lang == "es" else "french")
        out_name = f"assessed_level_{lang}.jsonl"
        out_path = lang_dir / out_name
        total_ok = total_skip = 0

        sources = sorted(lang_dir.glob("*.jsonl"))
        if not args.include_train_valid:
            sources = [p for p in sources if p.name not in ("train.jsonl", "valid.jsonl", out_name)]

        if not sources:
            print(f"  [{lang}] No source JSONL in {lang_dir}")
            continue

        # Fresh output shard (prepare_slm_data merges all jsonl except train/valid)
        if out_path.exists():
            out_path.unlink()

        migrated_sources: list[Path] = []
        for src in sources:
            if src == out_path:
                continue
            append = out_path.exists()
            ok, skip = migrate_file(src, out_path, lang, append=append)
            total_ok += ok
            total_skip += skip
            if ok:
                migrated_sources.append(src)
            print(f"  [{lang}] {src.name}: {ok} migrated, {skip} skipped")

        archive = lang_dir / "archive_legacy_schema"
        archive.mkdir(exist_ok=True)
        for src in migrated_sources:
            dest = archive / src.name
            if dest.exists():
                dest.unlink()
            shutil.move(str(src), str(dest))
            print(f"  [{lang}] archived → {dest.relative_to(TRAINING_DIR)}")

        print(f"  [{lang}] Wrote {total_ok} examples → {out_path} ({total_skip} skipped total)")


if __name__ == "__main__":
    main()
