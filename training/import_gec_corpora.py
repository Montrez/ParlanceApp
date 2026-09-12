#!/usr/bin/env python3
"""Download public learner-correction corpora and write GEC JSONL.

Sources we can actually use without a research form:
  cows     — COWS-L2H Spanish essays + instructor corrections (Apache 2.0)
  cancre   — graelo/cancre French error/correction pairs
  multigec — juancavallotti/multilingual-gec ES/FR/EN (Tatoeba + synthetic noise)

Skipped on purpose:
  FRIDA    — not publicly downloadable
  cLang-8  — needs a Lang-8 form and is CC BY-NC-SA (not for a sellable app)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

TRAINING_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TRAINING_DIR))

from gec_format import (  # noqa: E402
    pair_to_example,
    same_sentence,
    split_sentences,
    token_overlap,
)

RAW_DIR = TRAINING_DIR / "data" / "raw"
GEC_DIR = TRAINING_DIR / "data" / "gec"
COWS_DIR = RAW_DIR / "cowsl2h"
COWS_REPO = "https://github.com/ucdaviscl/cowsl2h.git"
COWS_TOPICS = (
    "famous",
    "vacation",
    "special",
    "terrible",
    "yourself",
    "beautiful",
    "place_you_dislike",
    "chaplin",
)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"  wrote {len(rows):,} → {path}")


def clone_cows() -> Path:
    if (COWS_DIR / "LICENSE").exists() or (COWS_DIR / "famous").exists():
        print(f"  COWS-L2H already present at {COWS_DIR}")
        return COWS_DIR
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  cloning {COWS_REPO} (sparse, essays + corrections only)")
    subprocess.run(
        [
            "git",
            "clone",
            "--filter=blob:none",
            "--sparse",
            "--depth",
            "1",
            COWS_REPO,
            str(COWS_DIR),
        ],
        check=True,
    )
    subprocess.run(
        ["git", "sparse-checkout", "set", *COWS_TOPICS],
        cwd=COWS_DIR,
        check=True,
    )
    return COWS_DIR


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _corrected_path(corrected_dir: Path, essay_path: Path) -> Path | None:
    candidates = [
        corrected_dir / f"{essay_path.stem}.corrected.txt",
        corrected_dir / essay_path.name.replace(".txt", ".corrected.txt"),
        corrected_dir / essay_path.name,
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def import_cows() -> list[dict]:
    root = clone_cows()
    rows: list[dict] = []
    skipped = 0
    for essays_dir in root.rglob("essays"):
        corrected_dir = essays_dir.parent / "corrected"
        if not corrected_dir.is_dir():
            continue
        for essay_path in essays_dir.iterdir():
            if not essay_path.is_file() or essay_path.name.startswith("."):
                continue
            if " (1)" in essay_path.name:
                continue
            corr_path = _corrected_path(corrected_dir, essay_path)
            if corr_path is None:
                skipped += 1
                continue
            src_text = _read_text(essay_path)
            tgt_text = _read_text(corr_path)
            src_sents = split_sentences(src_text)
            tgt_sents = split_sentences(tgt_text)
            pairs: list[tuple[str, str]] = []
            if len(src_sents) == len(tgt_sents) and src_sents:
                pairs = list(zip(src_sents, tgt_sents))
            elif token_overlap(src_text, tgt_text) >= 0.55:
                pairs = [(src_text, tgt_text)]
            else:
                skipped += 1
                continue
            for src, tgt in pairs:
                example = pair_to_example(
                    "es",
                    src,
                    tgt,
                    source="cowsl2h",
                    max_words=120,
                )
                if example:
                    rows.append(example)
                else:
                    skipped += 1
    print(f"  COWS-L2H: {len(rows):,} sentence pairs ({skipped} skipped)")
    return rows


def import_cancre() -> list[dict]:
    from datasets import load_dataset

    ds = load_dataset("graelo/cancre", split="train")
    rows: list[dict] = []
    skipped = 0
    for item in ds:
        example = pair_to_example(
            "fr",
            item.get("phrase1") or "",
            item.get("phrase2") or "",
            explanation=item.get("explication") or "",
            source="cancre",
        )
        if example:
            rows.append(example)
        else:
            skipped += 1
    print(f"  cancre: {len(rows):,} pairs ({skipped} skipped)")
    return rows


def import_multigec(langs: set[str]) -> dict[str, list[dict]]:
    from datasets import load_dataset

    ds = load_dataset("juancavallotti/multilingual-gec", split="train")
    by_lang = {lang: [] for lang in langs}
    excellent_seen: dict[str, set[str]] = {lang: set() for lang in langs}
    skipped = 0
    for item in ds:
        lang = (item.get("lang") or "").lower()
        if lang not in by_lang:
            continue
        dirty = item.get("modified") or ""
        clean = item.get("sentence") or ""
        example = pair_to_example(
            lang,
            dirty,
            clean,
            source="multigec",
        )
        if example:
            by_lang[lang].append(example)
        else:
            skipped += 1
            continue
        key = clean.strip().lower()
        if key and key not in excellent_seen[lang] and not same_sentence(dirty, clean):
            excellent_seen[lang].add(key)
            leave = pair_to_example(lang, clean, clean, source="multigec_clean")
            if leave:
                by_lang[lang].append(leave)
    for lang, rows in by_lang.items():
        print(f"  multilingual-gec {lang}: {len(rows):,} pairs")
    print(f"  multilingual-gec skipped: {skipped}")
    return by_lang


def main() -> None:
    parser = argparse.ArgumentParser(description="Import public GEC corpora")
    parser.add_argument(
        "--source",
        choices=["cows", "cancre", "multigec", "all"],
        default="all",
    )
    parser.add_argument("--lang", choices=["es", "fr", "en", "all"], default="all")
    args = parser.parse_args()

    langs = {"es", "fr", "en"} if args.lang == "all" else {args.lang}
    buckets: dict[str, list[dict]] = {lang: [] for lang in langs}

    if args.source in ("cows", "all") and "es" in langs:
        buckets["es"].extend(import_cows())
    if args.source in ("cancre", "all") and "fr" in langs:
        buckets["fr"].extend(import_cancre())
    if args.source in ("multigec", "all"):
        for lang, rows in import_multigec(langs).items():
            buckets[lang].extend(rows)

    GEC_DIR.mkdir(parents=True, exist_ok=True)
    for lang, rows in buckets.items():
        write_jsonl(GEC_DIR / lang / "imported.jsonl", rows)


if __name__ == "__main__":
    main()
