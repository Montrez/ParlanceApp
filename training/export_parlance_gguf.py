#!/usr/bin/env python3
"""
Export Parlance merged HF weights to GGUF for Android / llama.cpp inference.

Produces a quantized .gguf file from the same merged safetensors weights used
for the iOS MLX export.  Requires llama.cpp to be installed (pip install
llama-cpp-python, or clone llama.cpp and build locally).

Usage:
    python3 training/export_parlance_gguf.py --lang es
    python3 training/export_parlance_gguf.py --lang fr
    python3 training/export_parlance_gguf.py --lang both
    python3 training/export_parlance_gguf.py --lang es --quant Q4_K_M
    python3 training/export_parlance_gguf.py --lang es --quant Q8_0

Outputs:
    training/models/parlance-es-gguf/parlance-es-Q4_K_M.gguf   (~290 MB)
    training/models/parlance-fr-gguf/parlance-fr-Q4_K_M.gguf   (~290 MB)

Quant guide:
    Q4_K_M  — best balance of size/quality for Qwen 0.5B  (default)
    Q8_0    — higher quality, ~530 MB, good for testing
    Q5_K_M  — middle ground (~360 MB)
    F16     — full precision float16, ~1 GB, for benchmarking only
"""

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
        "gguf_dir": TRAINING_DIR / "models" / "parlance-es-gguf",
        "name": "parlance-es",
    },
    "fr": {
        "hf": TRAINING_DIR / "models" / "parlance-fr",
        "gguf_dir": TRAINING_DIR / "models" / "parlance-fr-gguf",
        "name": "parlance-fr",
    },
}

QUANT_CHOICES = ["Q4_K_M", "Q5_K_M", "Q8_0", "F16"]


# ── helpers ──────────────────────────────────────────────────────────────────

def _check_weights(hf_dir: Path) -> None:
    weights = hf_dir / "model.safetensors"
    if not weights.exists():
        raise SystemExit(
            f"Merged weights not found at {weights}.\n"
            f"Run: python3 training/finetune_slm.py --lang <lang> --mac   (or from Colab)\n"
            f"then: python3 training/export_parlance_mlx.py --lang <lang>  (merges LoRA)"
        )
    size = weights.stat().st_size
    if size < MIN_WEIGHT_BYTES:
        raise SystemExit(
            f"Weights look incomplete ({size / 1e6:.0f} MB < expected ~942 MB).\n"
            f"Re-run the merge step.  See TRAINING_STATUS.md."
        )


def _find_convert_script() -> Path:
    """Locate llama.cpp's convert_hf_to_gguf.py in common install locations."""
    candidates = [
        # pip install llama-cpp-python
        Path(sys.prefix) / "lib" / "python3" / "site-packages" / "llama_cpp" / "convert_hf_to_gguf.py",
        # homebrew / manual clone
        Path.home() / "llama.cpp" / "convert_hf_to_gguf.py",
        Path("/opt/homebrew/opt/llama.cpp/convert_hf_to_gguf.py"),
        Path("/usr/local/lib/llama.cpp/convert_hf_to_gguf.py"),
    ]
    # Also try importlib to find installed llama_cpp package path
    try:
        import llama_cpp  # noqa: F401
        import importlib.util
        spec = importlib.util.find_spec("llama_cpp")
        if spec and spec.origin:
            pkg_dir = Path(spec.origin).parent
            candidates.insert(0, pkg_dir / "convert_hf_to_gguf.py")
    except ImportError:
        pass

    for c in candidates:
        if c.exists():
            return c

    raise SystemExit(
        "Could not find llama.cpp's convert_hf_to_gguf.py.\n\n"
        "Option A — pip install (recommended for most users):\n"
        "    pip install llama-cpp-python\n\n"
        "Option B — clone llama.cpp:\n"
        "    git clone https://github.com/ggml-org/llama.cpp ~/llama.cpp\n"
        "    pip install -r ~/llama.cpp/requirements.txt\n\n"
        "Then re-run this script."
    )


def _find_quantize_bin() -> Path | None:
    """Return the llama.cpp quantize binary if available (optional step)."""
    for name in ("llama-quantize", "quantize"):
        found = shutil.which(name)
        if found:
            return Path(found)
    # common build output path
    for p in (
        Path.home() / "llama.cpp" / "build" / "bin" / "llama-quantize",
        Path.home() / "llama.cpp" / "quantize",
    ):
        if p.exists():
            return p
    return None


def _stage_hf_dir(hf_dir: Path, staging: Path) -> None:
    """Copy weights + fetch tokenizer into a clean staging dir."""
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    for name in ("model.safetensors", "config.json", "generation_config.json"):
        src = hf_dir / name
        if src.exists():
            shutil.copy2(src, staging / name)

    # Fetch the canonical tokenizer from HF (same as MLX export)
    print(f"  Fetching tokenizer from {BASE_MODEL}…")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    tokenizer.save_pretrained(staging)
    print(f"  Staged HF dir: {staging}")


def _convert_to_f16(convert_script: Path, staging: Path, f16_path: Path) -> None:
    """Run llama.cpp's HF → GGUF F16 conversion."""
    f16_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(convert_script),
        str(staging),
        "--outfile", str(f16_path),
        "--outtype", "f16",
    ]
    print(f"  Converting to F16 GGUF…\n  {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    size_mb = f16_path.stat().st_size / 1e6
    print(f"  F16 GGUF: {f16_path} ({size_mb:.0f} MB)")


def _quantize(quantize_bin: Path, f16_path: Path, out_path: Path, quant: str) -> None:
    """Quantize an F16 GGUF with llama-quantize."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(quantize_bin), str(f16_path), str(out_path), quant]
    print(f"  Quantizing to {quant}…\n  {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    size_mb = out_path.stat().st_size / 1e6
    print(f"  {quant} GGUF: {out_path} ({size_mb:.0f} MB)")


def _convert_direct(convert_script: Path, staging: Path, out_path: Path, quant: str) -> None:
    """Newer llama.cpp can quantize in one step via --outtype."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Map our quant names to llama.cpp outtype tokens
    outtype_map = {"Q4_K_M": "q4_k_m", "Q5_K_M": "q5_k_m", "Q8_0": "q8_0", "F16": "f16"}
    outtype = outtype_map.get(quant, "q4_k_m")
    cmd = [
        sys.executable,
        str(convert_script),
        str(staging),
        "--outfile", str(out_path),
        "--outtype", outtype,
    ]
    print(f"  Converting + quantizing ({quant}) in one pass…\n  {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Older llama.cpp doesn't support --outtype for quantized formats
        return False
    size_mb = out_path.stat().st_size / 1e6
    print(f"  {quant} GGUF: {out_path} ({size_mb:.0f} MB)")
    return True


# ── main export ──────────────────────────────────────────────────────────────

def export_lang(lang: str, quant: str, keep_f16: bool) -> None:
    cfg = LANG_CONFIG[lang]
    hf_dir: Path = cfg["hf"]
    gguf_dir: Path = cfg["gguf_dir"]
    name: str = cfg["name"]
    staging = TRAINING_DIR / "models" / f".{name}-gguf-staging"

    print(f"\n{'='*60}")
    print(f"  Exporting {lang.upper()} → GGUF {quant}")
    print(f"{'='*60}")

    _check_weights(hf_dir)

    final_path = gguf_dir / f"{name}-{quant}.gguf"
    if final_path.exists():
        size_mb = final_path.stat().st_size / 1e6
        print(f"  Already exists: {final_path} ({size_mb:.0f} MB)")
        print(f"  Use --force to re-export.")
        return

    convert_script = _find_convert_script()
    print(f"  llama.cpp convert: {convert_script}")

    _stage_hf_dir(hf_dir, staging)

    try:
        if quant == "F16":
            _convert_to_f16(convert_script, staging, final_path)
        else:
            # Try one-pass quantized conversion first (newer llama.cpp)
            success = _convert_direct(convert_script, staging, final_path, quant)
            if not success:
                # Fall back: convert to F16 first, then quantize
                f16_path = gguf_dir / f"{name}-F16.gguf"
                _convert_to_f16(convert_script, staging, f16_path)
                quantize_bin = _find_quantize_bin()
                if quantize_bin is None:
                    raise SystemExit(
                        f"F16 GGUF created at {f16_path}.\n"
                        f"To quantize to {quant}, install llama-quantize:\n"
                        f"  brew install llama.cpp     (macOS)\n"
                        f"  or build from: https://github.com/ggml-org/llama.cpp\n"
                        f"Then run:\n"
                        f"  llama-quantize {f16_path} {final_path} {quant}"
                    )
                _quantize(quantize_bin, f16_path, final_path, quant)
                if not keep_f16:
                    f16_path.unlink(missing_ok=True)
                    print(f"  Removed intermediate F16 GGUF.")
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    print(f"\n  Done: {final_path}")
    print(f"  Copy to Android assets/ or serve via local HTTP for llama.cpp inference.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export Parlance fine-tuned models to GGUF for Android / llama.cpp"
    )
    parser.add_argument(
        "--lang",
        choices=sorted(LANG_CONFIG) + ["both"],
        default="es",
        help="Language to export (default: es)",
    )
    parser.add_argument(
        "--quant",
        choices=QUANT_CHOICES,
        default="Q4_K_M",
        help="Quantization type (default: Q4_K_M — best size/quality for Qwen 0.5B)",
    )
    parser.add_argument(
        "--keep-f16",
        action="store_true",
        help="Keep intermediate F16 GGUF when doing two-pass quantization",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-export even if output GGUF already exists",
    )
    args = parser.parse_args()

    if args.force:
        for lang in (["es", "fr"] if args.lang == "both" else [args.lang]):
            cfg = LANG_CONFIG[lang]
            target = cfg["gguf_dir"] / f"{cfg['name']}-{args.quant}.gguf"
            if target.exists():
                target.unlink()
                print(f"Removed existing {target}")

    langs = ["es", "fr"] if args.lang == "both" else [args.lang]
    for lang in langs:
        export_lang(lang, args.quant, args.keep_f16)

    print("\n" + "="*60)
    print("  GGUF export complete.")
    print("="*60)
    for lang in langs:
        cfg = LANG_CONFIG[lang]
        out = cfg["gguf_dir"] / f"{cfg['name']}-{args.quant}.gguf"
        if out.exists():
            print(f"  {lang.upper()}: {out}  ({out.stat().st_size / 1e6:.0f} MB)")
    print()
    print("  Android integration options:")
    print("  1. Capacitor plugin (llama.cpp JNI):")
    print("     - Bundle .gguf in Android app assets/models/")
    print("     - Call inference via capacitor-community/llama or custom JNI plugin")
    print("  2. MediaPipe LLM Inference API:")
    print("     - Convert to LiteRT format: mediapipe/tasks/python/genai/converter")
    print("     - Works with Qwen 0.5B on mid-range Android (Snapdragon 7/8-series)")
    print("  3. Local llama.cpp server (dev/testing):")
    print("     - adb push <model>.gguf /data/local/tmp/")
    print("     - Run llama-server and point journal.js at localhost:8080")


if __name__ == "__main__":
    main()
