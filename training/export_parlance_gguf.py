#!/usr/bin/env python3
"""Export Parlance merged HF weights to Q4 GGUF for on-device Android (llama.cpp).

Same HuggingFace merges iOS already ships as MLX. One-time, local, $0.
Do not upload the GGUF files to Firebase Storage. They are gitignored.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

TRAINING_DIR = Path(__file__).resolve().parent
ROOT = TRAINING_DIR.parent
BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
MIN_WEIGHT_BYTES = 800_000_000
LLAMA_DIR = TRAINING_DIR / ".llama.cpp"
QUANT = "Q4_K_M"

LANG_CONFIG = {
    "es": {
        "hf": TRAINING_DIR / "models" / "parlance-es",
        "staging": TRAINING_DIR / "models" / ".parlance-es-gguf-staging",
        "gguf": TRAINING_DIR / "models" / "parlance-es.gguf",
    },
    "fr": {
        "hf": TRAINING_DIR / "models" / "parlance-fr",
        "staging": TRAINING_DIR / "models" / ".parlance-fr-gguf-staging",
        "gguf": TRAINING_DIR / "models" / "parlance-fr.gguf",
    },
}

ANDROID_DESTS = (
    ROOT / "android" / "app" / "src" / "main" / "assets" / "models",
    ROOT / "android" / "parlance_models" / "src" / "main" / "assets",
)


def python_bin() -> str:
    """Use an interpreter that can import torch. convert_hf_to_gguf imports it at startup."""
    for candidate in ("python3", "python3.11", "python3.12", "python3.13"):
        path = shutil.which(candidate)
        if not path:
            continue
        probe = subprocess.run([path, "-c", "import torch"], check=False)
        if probe.returncode == 0:
            return path
    raise SystemExit(
        "No Python with torch found. Install torch in python3 and re-run."
    )


def prepare_hf_dir(src: Path, staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    weights = src / "model.safetensors"
    if not weights.exists() or weights.stat().st_size < MIN_WEIGHT_BYTES:
        raise SystemExit(
            f"Missing or incomplete merged weights at {weights}. "
            "Re-export merged parlance; see TRAINING_STATUS.md."
        )

    for name in (
        "model.safetensors",
        "config.json",
        "generation_config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "vocab.json",
        "merges.txt",
        "added_tokens.json",
        "chat_template.jinja",
    ):
        src_file = src / name
        if src_file.exists():
            shutil.copy2(src_file, staging / name)

    if not (staging / "tokenizer.json").exists():
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
        tokenizer.save_pretrained(staging)


def ensure_llama_src() -> Path:
    convert = LLAMA_DIR / "convert_hf_to_gguf.py"
    if convert.exists():
        return LLAMA_DIR
    print(f"Cloning llama.cpp into {LLAMA_DIR} (convert script only)")
    LLAMA_DIR.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "https://github.com/ggml-org/llama.cpp.git",
            str(LLAMA_DIR),
        ],
        check=True,
    )
    if not convert.exists():
        raise SystemExit(f"llama.cpp clone is missing {convert}")
    return LLAMA_DIR


def ensure_llama_quantize() -> str:
    found = shutil.which("llama-quantize")
    if found:
        return found
    local = LLAMA_DIR / "build" / "bin" / "llama-quantize"
    if local.exists():
        return str(local)

    dest_dir = TRAINING_DIR / ".llama-bin"
    for candidate in dest_dir.rglob("llama-quantize"):
        if candidate.is_file() and candidate.parent.name != ".llama-bin":
            return str(candidate)

    machine = platform.machine().lower()
    system = platform.system().lower()
    if system != "darwin":
        raise SystemExit(
            "llama-quantize is not on PATH. Install llama.cpp "
            "(brew install llama.cpp) or build it, then re-run."
        )
    arch = "arm64" if machine in ("arm64", "aarch64") else "x64"
    suffix = f"bin-macos-{arch}.tar.gz"
    url = macos_release_url(suffix)
    dest_dir.mkdir(parents=True, exist_ok=True)
    archive = dest_dir / "llama-macos.tar.gz"
    print(f"Downloading llama-quantize ({url})")
    urllib.request.urlretrieve(url, archive)
    with tarfile.open(archive, "r:gz") as tf:
        tf.extractall(dest_dir)
    for candidate in dest_dir.rglob("llama-quantize"):
        candidate.chmod(candidate.stat().st_mode | stat.S_IXUSR)
        if candidate.resolve() != cached.resolve():
            shutil.copy2(candidate, cached)
            cached.chmod(cached.stat().st_mode | stat.S_IXUSR)
        return str(cached)
    raise SystemExit("Downloaded llama.cpp archive but llama-quantize was not inside it")


def macos_release_url(suffix: str) -> str:
    req = urllib.request.Request(
        "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "parlance-gguf-export"},
    )
    with urllib.request.urlopen(req) as resp:
        release = json.load(resp)
    for asset in release.get("assets", []):
        name = asset.get("name") or ""
        if name.endswith(suffix):
            return asset["browser_download_url"]
    tag = release.get("tag_name", "latest")
    raise SystemExit(f"No llama.cpp asset ending in {suffix} on {tag}")


def convert_f16(staging: Path, f16_out: Path) -> None:
    llama = ensure_llama_src()
    convert = llama / "convert_hf_to_gguf.py"
    env = os.environ.copy()
    gguf_py = llama / "gguf-py"
    if gguf_py.is_dir():
        env["PYTHONPATH"] = (
            str(gguf_py) + os.pathsep + env.get("PYTHONPATH", "")
        )
    cmd = [
        python_bin(),
        str(convert),
        str(staging),
        "--outfile",
        str(f16_out),
        "--outtype",
        "f16",
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True, env=env)


def quantize(f16_path: Path, q4_path: Path) -> None:
    quant = ensure_llama_quantize()
    cmd = [quant, str(f16_path), str(q4_path), QUANT]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)


def copy_to_android(gguf: Path, lang: str) -> None:
    name = f"parlance-{lang}.gguf"
    for dest_dir in ANDROID_DESTS:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / name
        print(f"Copy {gguf} -> {dest}")
        shutil.copy2(gguf, dest)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export parlance-es/fr to Q4_K_M GGUF for Android"
    )
    parser.add_argument(
        "--lang",
        choices=sorted(LANG_CONFIG),
        default="es",
        help="Language export (default: es)",
    )
    parser.add_argument("--hf-path", type=Path, default=None)
    parser.add_argument("--gguf-path", type=Path, default=None)
    parser.add_argument(
        "--skip-android-copy",
        action="store_true",
        help="Write training/models only",
    )
    args = parser.parse_args()

    cfg = LANG_CONFIG[args.lang]
    hf_path = args.hf_path or cfg["hf"]
    gguf_path = args.gguf_path or cfg["gguf"]
    staging = cfg["staging"]

    print(f"Export {args.lang}: {hf_path} -> {gguf_path}")
    prepare_hf_dir(hf_path, staging)

    with tempfile.TemporaryDirectory(prefix="parlance-gguf-") as tmp:
        f16_path = Path(tmp) / f"parlance-{args.lang}-f16.gguf"
        convert_f16(staging, f16_path)
        gguf_path.parent.mkdir(parents=True, exist_ok=True)
        quantize(f16_path, gguf_path)

    shutil.rmtree(staging, ignore_errors=True)

    if not args.skip_android_copy:
        copy_to_android(gguf_path, args.lang)

    print(f"GGUF export done: {gguf_path} ({gguf_path.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
