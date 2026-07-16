#!/usr/bin/env python3
"""Colab one-shot: re-export Parlance SLM adapter to full-precision merged weights.

Usage:
    python colab_reexport.py --lang es
    python colab_reexport.py --lang fr
    python colab_reexport.py --lang both
"""
from __future__ import annotations

import argparse
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Colab re-export merged Parlance SLM")
    parser.add_argument("--lang", choices=["es", "fr", "both"], required=True)
    args = parser.parse_args()

    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "-U", *PKGS],
        check=True,
    )

    import torch

    if not torch.cuda.is_available():
        sys.exit("ERROR: Need Colab GPU for merge step.")

    from reexport_merged import find_adapter_dir, main as reexport_main

    langs = ("es", "fr") if args.lang == "both" else (args.lang,)
    for lang in langs:
        adapter = find_adapter_dir(lang)
        if adapter is None:
            sys.exit(f"No adapter under checkpoints/parlance-{lang}")
        print(f"Using adapter: {adapter}")
        sys.argv = ["reexport_merged.py", "--lang", lang]
        reexport_main()


if __name__ == "__main__":
    main()
