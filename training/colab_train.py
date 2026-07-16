#!/usr/bin/env python3
"""Colab one-shot: install deps, unzip data, fine-tune Parlance SLM for one or more langs.

Usage (from the Colab working directory that has training scripts + data zip):
    python colab_train.py --lang fr
    python colab_train.py --lang es
    python colab_train.py --lang both
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path

PKGS = [
    "torch",
    "transformers",
    "peft>=0.14",
    "datasets",
    "accelerate",
    "bitsandbytes",
    "trl",
    "torchao>=0.16",
]


def run(cmd: list[str]) -> None:
    print(f"\n>>> {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Colab train Parlance SLM")
    parser.add_argument(
        "--lang",
        choices=["es", "fr", "both"],
        required=True,
        help="Language to train (or both)",
    )
    parser.add_argument("--epochs", type=int, default=3)
    args = parser.parse_args()

    run([sys.executable, "-m", "pip", "install", "-q", "-U", *PKGS])

    zpath = Path("parlance_training_data.zip")
    if zpath.exists():
        print("Extracting training data...", flush=True)
        with zipfile.ZipFile(zpath) as zf:
            zf.extractall(".")

    import torch

    if not torch.cuda.is_available():
        sys.exit("ERROR: No CUDA GPU. Use a T4 runtime.")
    print(f"GPU: {torch.cuda.get_device_name(0)}", flush=True)

    langs = ("es", "fr") if args.lang == "both" else (args.lang,)
    for lang in langs:
        run([
            sys.executable,
            "finetune_slm.py",
            "--lang",
            lang,
            "--epochs",
            str(args.epochs),
        ])

    outs = " and ".join(f"models/parlance-{lang}" for lang in langs)
    print(f"\nDone. Model(s) at {outs}", flush=True)


if __name__ == "__main__":
    main()
