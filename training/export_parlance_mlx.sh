#!/usr/bin/env bash
# Export parlance-es or parlance-fr merged HF weights to MLX 4-bit.
# Examples: ./training/export_parlance_mlx.sh --lang fr
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/training/export_parlance_mlx.py" "$@"
