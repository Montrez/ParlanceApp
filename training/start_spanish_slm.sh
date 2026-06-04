#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
WEIGHTS="$ROOT/models/parlance-es/model.safetensors"

if [[ ! -f "$WEIGHTS" ]]; then
  echo "Missing Spanish model: $WEIGHTS"
  echo "See training/TRAINING_STATUS.md"
  exit 1
fi
SIZE=$(stat -f%z "$WEIGHTS" 2>/dev/null || stat -c%s "$WEIGHTS")
if [[ "$SIZE" -lt 800000000 ]]; then
  echo "Spanish weights look too small ($SIZE bytes). Need merged ~942MB export."
  exit 1
fi

echo "Starting Parlance Coach (Spanish) at http://127.0.0.1:8765"
exec python3 "$ROOT/parlance_slm_server.py"
