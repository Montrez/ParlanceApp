#!/usr/bin/env python3
"""Colab one-shot: re-export Spanish Parlance SLM to full-precision merged weights."""
import subprocess
import sys

PKGS = [
    "torch",
    "transformers",
    "peft>=0.14",
    "accelerate",
    "bitsandbytes",
    "torchao>=0.16",
]

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-U", *PKGS], check=True)

import torch

if not torch.cuda.is_available():
    sys.exit("ERROR: Need Colab GPU for merge step.")

from reexport_merged import find_adapter_dir, main as reexport_main

adapter = find_adapter_dir("es")
if adapter is None:
    sys.exit("No Spanish adapter under checkpoints/parlance-es")

print(f"Using adapter: {adapter}")
sys.argv = ["reexport_merged.py", "--lang", "es"]
reexport_main()
