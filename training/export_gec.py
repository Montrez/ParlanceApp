#!/usr/bin/env python3
"""Stage a fused Gemma 4 GEC model into the iOS MLX folder name.

Fuse first:
  .venv/bin/python -m mlx_lm fuse \\
    --model <local gemma-4-e2b-it-4bit snapshot> \\
    --adapter-path adapters/parlance-gec-{es,fr} \\
    --save-path models/parlance-gec-{es,fr}

Then:
  python3 export_gec.py --lang fr
  python3 export_gec.py --lang es
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

TRAINING_DIR = Path(__file__).resolve().parent
ROOT = TRAINING_DIR.parent


def stage(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["rsync", "-a", "--delete", f"{src}/", f"{dest}/"], check=True)
    total = sum(f.stat().st_size for f in dest.rglob("*") if f.is_file())
    print(f"{dest} ({total / 1e9:.2f} GB)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage fused GEC MLX for iOS")
    parser.add_argument("--lang", choices=("es", "fr"), required=True)
    parser.add_argument("--src", type=Path, default=None)
    args = parser.parse_args()
    src = args.src or (TRAINING_DIR / "models" / f"parlance-gec-{args.lang}")
    if not (src / "config.json").exists() or not (src / "model.safetensors").exists():
        raise SystemExit(f"Missing fused model at {src}. Fuse the LoRA first.")
    stage(src, TRAINING_DIR / "models" / f"parlance-{args.lang}-mlx")
    stage(src, ROOT / "Parlance" / "Models" / f"parlance-{args.lang}-mlx")


if __name__ == "__main__":
    main()
