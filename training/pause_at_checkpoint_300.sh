#!/usr/bin/env bash
# Stop Spanish fine-tune after checkpoint-300 is written (resume later with --resume).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
CKPT="$ROOT/checkpoints/parlance-es/checkpoint-300"
LOG="$ROOT/level_retrain_es_resume.log"

echo "[pause] Watching for checkpoint-300…"
while [ ! -d "$CKPT" ]; do
  sleep 10
done

# Allow trainer to finish writing optimizer state
sleep 15

echo "[pause] checkpoint-300 found — stopping training" | tee -a "$LOG"
pkill -f "finetune_slm.py --lang es" 2>/dev/null || true
pkill -f "caffeinate -dims python3 finetune_slm.py" 2>/dev/null || true

cat >> "$LOG" <<'EOF'

══════════════════════════════════════════════════════════════
  PAUSED at checkpoint-300 (Jun 2). Resume tonight:

  cd training
  caffeinate -dims python3 finetune_slm.py --lang es --epochs 2 --mac --batch-size 2 --resume

  (~18 steps left of 318, then merge + export MLX)
══════════════════════════════════════════════════════════════
EOF

echo "[pause] Done. Training stopped."
