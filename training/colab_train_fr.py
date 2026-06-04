#!/usr/bin/env python3
"""Train French Parlance SLM only on Colab (install deps, data, train + merged save)."""
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


def run(cmd):
    print(f"\n>>> {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True)


def main():
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

    run([sys.executable, "finetune_slm.py", "--lang", "fr", "--epochs", "3"])
    print("\nDone. French model at models/parlance-fr", flush=True)


if __name__ == "__main__":
    main()
