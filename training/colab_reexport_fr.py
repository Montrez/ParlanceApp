#!/usr/bin/env python3
"""Colab one-shot: re-export French Parlance SLM to full-precision merged weights."""
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

from reexport_merged import find_adapter_dir

sys.argv = ["reexport_merged.py", "--lang", "fr"]
adapter = find_adapter_dir("fr")
if adapter is None:
    sys.exit("No French adapter under checkpoints/parlance-fr")

print(f"Using adapter: {adapter}")
from reexport_merged import main as reexport_main

reexport_main()
