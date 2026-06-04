#!/usr/bin/env python3
"""Run full Parlance SLM training on a Colab VM (install deps, unzip data, train es+fr)."""
import subprocess
import sys
import zipfile
from pathlib import Path

PKGS = [
    "torch",
    "transformers",
    "peft",
    "datasets",
    "accelerate",
    "bitsandbytes",
    "trl",
]


def run(cmd):
    print(f"\n>>> {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True)


def main():
    print("Installing dependencies...", flush=True)
    run([sys.executable, "-m", "pip", "install", "-q", *PKGS])

    zpath = Path("parlance_training_data.zip")
    if zpath.exists():
        print("Extracting training data...", flush=True)
        with zipfile.ZipFile(zpath) as zf:
            zf.extractall(".")

    import torch

    if not torch.cuda.is_available():
        sys.exit("ERROR: No CUDA GPU on this runtime. Use a T4 GPU runtime.")
    print(f"GPU: {torch.cuda.get_device_name(0)}", flush=True)

    for lang in ("es", "fr"):
        run([sys.executable, "finetune_slm.py", "--lang", lang, "--epochs", "3"])

    print("\nDone. Models at models/parlance-es and models/parlance-fr", flush=True)


if __name__ == "__main__":
    main()
