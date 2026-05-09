#!/usr/bin/env python3
"""
Prepare final training/validation splits for per-language SLM fine-tuning.

Merges all JSONL files in training/data/spanish/ or training/data/french/,
shuffles, deduplicates, and splits into train (90%) and valid (10%).

Usage:
    python prepare_slm_data.py --lang es
    python prepare_slm_data.py --lang fr
    python prepare_slm_data.py --lang both

Output:
    training/data/spanish/train.jsonl, training/data/spanish/valid.jsonl
    training/data/french/train.jsonl, training/data/french/valid.jsonl
"""

import argparse
import json
import random
from pathlib import Path


def extract_input_sentence(example: dict) -> str:
    """Extract the user's input sentence for deduplication."""
    for msg in example.get("messages", []):
        if msg.get("role") == "user":
            content = msg["content"]
            if '"' in content:
                start = content.index('"') + 1
                end = content.rindex('"')
                return content[start:end].strip().lower()
    return ""


def get_level(example: dict) -> str:
    for msg in example.get("messages", []):
        if msg.get("role") == "user":
            for lvl in ["A1", "A2", "B1", "B2", "C1", "C2"]:
                if f"at {lvl} level" in msg["content"]:
                    return lvl
    return ""


def merge_and_split(lang_dir: Path, split_ratio: float = 0.9, level_cap: int = 350):
    source_files = sorted(lang_dir.glob("*.jsonl"))
    source_files = [f for f in source_files if f.name not in ("train.jsonl", "valid.jsonl")]

    if not source_files:
        print(f"  No JSONL files found in {lang_dir}")
        return

    all_examples = []
    seen_sentences = set()
    duplicates = 0

    for filepath in source_files:
        count = 0
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    example = json.loads(line)
                    sentence = extract_input_sentence(example)
                    if sentence and sentence in seen_sentences:
                        duplicates += 1
                        continue
                    if sentence:
                        seen_sentences.add(sentence)
                    all_examples.append(example)
                    count += 1
                except json.JSONDecodeError:
                    continue
        print(f"    {filepath.name}: {count} examples")

    print(f"    Duplicates removed: {duplicates}")
    print(f"    Total unique (before cap): {len(all_examples)}")

    by_level = {}
    for ex in all_examples:
        lvl = get_level(ex)
        by_level.setdefault(lvl, []).append(ex)

    capped = []
    capped_count = 0
    for lvl, examples in by_level.items():
        if len(examples) > level_cap:
            random.shuffle(examples)
            capped_count += len(examples) - level_cap
            capped.extend(examples[:level_cap])
        else:
            capped.extend(examples)

    all_examples = capped
    if capped_count:
        print(f"    Level cap ({level_cap}): removed {capped_count} excess examples")
    print(f"    Total balanced: {len(all_examples)}")

    random.shuffle(all_examples)

    split_idx = int(len(all_examples) * split_ratio)
    train = all_examples[:split_idx]
    valid = all_examples[split_idx:]

    train_file = lang_dir / "train.jsonl"
    valid_file = lang_dir / "valid.jsonl"

    with open(train_file, "w", encoding="utf-8") as f:
        for ex in train:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    with open(valid_file, "w", encoding="utf-8") as f:
        for ex in valid:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"    Train: {len(train)} → {train_file}")
    print(f"    Valid: {len(valid)} → {valid_file}")

    # Print level distribution
    level_counts = {}
    for ex in all_examples:
        for msg in ex.get("messages", []):
            if msg.get("role") == "user":
                for lvl in ["A1", "A2", "B1", "B2", "C1", "C2"]:
                    if f"at {lvl} level" in msg["content"]:
                        level_counts[lvl] = level_counts.get(lvl, 0) + 1
                        break
    if level_counts:
        print(f"    Level distribution: {dict(sorted(level_counts.items()))}")


def main():
    parser = argparse.ArgumentParser(description="Prepare SLM training data splits")
    parser.add_argument("--lang", choices=["es", "fr", "both"], default="both")
    parser.add_argument("--split", type=float, default=0.9, help="Train/valid split ratio (default: 0.9)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible splits")
    args = parser.parse_args()

    random.seed(args.seed)
    data_dir = Path("training/data")

    if args.lang in ("es", "both"):
        print("═══ Spanish SLM Data ═══")
        merge_and_split(data_dir / "spanish", args.split)
        print()

    if args.lang in ("fr", "both"):
        print("═══ French SLM Data ═══")
        merge_and_split(data_dir / "french", args.split)


if __name__ == "__main__":
    main()
