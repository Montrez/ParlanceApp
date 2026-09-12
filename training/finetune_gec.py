#!/usr/bin/env python3
"""Fine-tune Gemma 4 E2B on the narrow GEC task with MLX LoRA.

Usage:
    python3 finetune_gec.py --lang fr
    python3 finetune_gec.py --lang es --iters 800
    python3 finetune_gec.py --lang en --dry-run
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

TRAINING_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL = "mlx-community/gemma-4-e2b-it-4bit"
PYTHON_CANDIDATES = (
    str(TRAINING_DIR / ".venv" / "bin" / "python"),
    "/opt/homebrew/bin/python3.13",
    "/opt/homebrew/bin/python3.11",
    "python3.13",
    "python3.11",
)


def mlx_python() -> str:
    """Prefer a Python whose mlx-lm can load Gemma 4. System python3 is 3.9."""
    ordered = [sys.executable, *PYTHON_CANDIDATES]
    seen: set[str] = set()
    for py in ordered:
        if py in seen:
            continue
        seen.add(py)
        try:
            check = subprocess.run(
                [py, "-c", "import mlx_lm.models.gemma4"],
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            continue
        if check.returncode == 0:
            return py
    raise SystemExit(
        "mlx-lm is too old for Gemma 4 (needs 0.31+). Install with:\n"
        "  cd training && python3.13 -m venv .venv && .venv/bin/pip install -U 'mlx-lm>=0.31'\n"
        "then rerun this script."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune the GEC coach with MLX LoRA")
    parser.add_argument("--lang", choices=["es", "fr", "en"], required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--iters", type=int, default=800)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--lr", type=float, default=1e-5)
    parser.add_argument("--max-seq-length", type=int, default=768)
    parser.add_argument("--num-layers", type=int, default=16)
    parser.add_argument(
        "--adapter-path",
        type=Path,
        default=None,
        help="Defaults to training/adapters/parlance-gec-{lang}",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Continue from adapters/parlance-gec-{lang}/adapters.safetensors",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    data_dir = TRAINING_DIR / "data" / "gec" / args.lang
    train_file = data_dir / "train.jsonl"
    if not train_file.exists():
        raise SystemExit(
            f"Missing {train_file}. Run import_gec_corpora.py then prepare_gec_data.py first."
        )
    adapter = args.adapter_path or (TRAINING_DIR / "adapters" / f"parlance-gec-{args.lang}")
    adapter.parent.mkdir(parents=True, exist_ok=True)

    python = mlx_python()
    cmd = [
        python,
        "-m",
        "mlx_lm",
        "lora",
        "--model",
        args.model,
        "--train",
        "--data",
        str(data_dir),
        "--adapter-path",
        str(adapter),
        "--fine-tune-type",
        "lora",
        "--mask-prompt",
        "--iters",
        str(args.iters),
        "--batch-size",
        str(args.batch_size),
        "--learning-rate",
        str(args.lr),
        "--max-seq-length",
        str(args.max_seq_length),
        "--num-layers",
        str(args.num_layers),
        "--grad-checkpoint",
        "--save-every",
        "1000",
    ]
    resume_file = adapter / "adapters.safetensors"
    if args.resume:
        if not resume_file.exists():
            raise SystemExit(f"--resume set but missing {resume_file}")
        cmd.extend(["--resume-adapter-file", str(resume_file)])
    print(" ".join(cmd))
    if args.dry_run:
        return
    subprocess.run(cmd, check=True)
    print(f"Adapter saved to {adapter}")


if __name__ == "__main__":
    main()
