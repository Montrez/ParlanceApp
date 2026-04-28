#!/usr/bin/env python3
"""Merge all training JSONL files into a single shuffled dataset for fine-tuning."""

import json
import random
import sys
from pathlib import Path

def main():
    data_dir = Path("training/data")
    if not data_dir.exists():
        print("No training/data directory found.")
        sys.exit(1)

    all_examples = []
    for f in sorted(data_dir.glob("*.jsonl")):
        with open(f) as fh:
            lines = [line.strip() for line in fh if line.strip()]
            all_examples.extend(lines)
            print(f"  {f.name}: {len(lines)} examples")

    random.seed(42)
    random.shuffle(all_examples)

    split = int(len(all_examples) * 0.9)
    train = all_examples[:split]
    val = all_examples[split:]

    out_train = data_dir / "train.jsonl"
    out_val = data_dir / "val.jsonl"

    with open(out_train, "w") as f:
        f.write("\n".join(train) + "\n")
    with open(out_val, "w") as f:
        f.write("\n".join(val) + "\n")

    print(f"\nTotal: {len(all_examples)} examples")
    print(f"Train: {len(train)} → {out_train}")
    print(f"Val:   {len(val)} → {out_val}")


if __name__ == "__main__":
    main()
