#!/usr/bin/env python3
"""Export Parlance merged HF weights to MLX 4-bit for on-device iOS (mlx-swift-lm)."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

TRAINING_DIR = Path(__file__).resolve().parent
BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
MIN_WEIGHT_BYTES = 800_000_000

LANG_CONFIG = {
    "es": {
        "hf": TRAINING_DIR / "models" / "parlance-es",
        "mlx": TRAINING_DIR / "models" / "parlance-es-mlx",
        "staging": TRAINING_DIR / "models" / ".parlance-es-staging",
    },
    "fr": {
        "hf": TRAINING_DIR / "models" / "parlance-fr",
        "mlx": TRAINING_DIR / "models" / "parlance-fr-mlx",
        "staging": TRAINING_DIR / "models" / ".parlance-fr-staging",
    },
}


def prepare_hf_dir(src: Path, staging: Path) -> None:
    """Stage merged weights with a tokenizer mlx_lm can load."""
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    weights = src / "model.safetensors"
    if not weights.exists() or weights.stat().st_size < MIN_WEIGHT_BYTES:
        raise SystemExit(
            f"Missing or incomplete merged weights at {weights}. "
            f"Re-export merged parlance ({src.name}); see TRAINING_STATUS.md."
        )

    for name in ("model.safetensors", "config.json", "generation_config.json"):
        shutil.copy2(src / name, staging / name)

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    tokenizer.save_pretrained(staging)


def convert(staging: Path, mlx_out: Path, q_bits: int) -> None:
    if mlx_out.exists():
        shutil.rmtree(mlx_out)
    cmd = [
        sys.executable,
        "-m",
        "mlx_lm",
        "convert",
        "--hf-path",
        str(staging),
        "--mlx-path",
        str(mlx_out),
        "-q",
        "--q-bits",
        str(q_bits),
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export parlance-es/fr to MLX 4-bit")
    parser.add_argument(
        "--lang",
        choices=sorted(LANG_CONFIG),
        default="es",
        help="Language export (default: es)",
    )
    parser.add_argument("--hf-path", type=Path, default=None)
    parser.add_argument("--mlx-path", type=Path, default=None)
    parser.add_argument("--q-bits", type=int, default=4)
    parser.add_argument("--skip-convert", action="store_true", help="Only stage HF dir")
    args = parser.parse_args()

    cfg = LANG_CONFIG[args.lang]
    hf_path = args.hf_path or cfg["hf"]
    mlx_path = args.mlx_path or cfg["mlx"]
    staging = cfg["staging"]

    print(f"Export {args.lang}: {hf_path} -> {mlx_path}")
    prepare_hf_dir(hf_path, staging)
    if args.skip_convert:
        print(f"Staged at {staging}")
        return

    convert(staging, mlx_path, args.q_bits)
    shutil.rmtree(staging, ignore_errors=True)

    total = sum(f.stat().st_size for f in mlx_path.rglob("*") if f.is_file())
    print(f"MLX export done: {mlx_path} ({total / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
