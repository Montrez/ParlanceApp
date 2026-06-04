#!/usr/bin/env bash
# One extra epoch on golden seed data (resume from last Spanish checkpoint).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/training"
LOG="${1:-golden_refresh_es.log}"

MAC_FLAG=""
if [[ "$(uname -s)" == "Darwin" ]]; then
  MAC_FLAG="--mac"
fi

echo "═══ Golden refresh retrain (es) — log: $LOG ═══" | tee "$LOG"
date | tee -a "$LOG"

python3 merge_golden_seeds.py 2>&1 | tee -a "$LOG"
python3 prepare_slm_data.py --lang es 2>&1 | tee -a "$LOG"

CKPT="checkpoints/parlance-es/checkpoint-318"
if [[ ! -d "$CKPT" ]]; then
  CKPT="$(ls -d checkpoints/parlance-es/checkpoint-* 2>/dev/null | sort -V | tail -1)"
fi
echo "Resuming from $CKPT, training to epoch 3 (one extra epoch)" | tee -a "$LOG"

# epoch eval + caffeinate: fewer long MPS validation passes; Mac stays awake
TRAIN_CMD=(python3 finetune_slm.py --lang es --epochs 3 --resume --resume-from "$CKPT"
  --batch-size 2 --eval-strategy epoch --save-steps 50)
if [[ -n "$MAC_FLAG" ]]; then
  TRAIN_CMD+=($MAC_FLAG)
  caffeinate -dimsu "${TRAIN_CMD[@]}" 2>&1 | tee -a "$LOG"
else
  "${TRAIN_CMD[@]}" 2>&1 | tee -a "$LOG"
fi

echo "═══ Smoke + regression ═══" | tee -a "$LOG"
python3 smoke_test_slm.py es 2>&1 | tee -a "$LOG"
python3 run_coach_regression.py --lang es 2>&1 | tee -a "$LOG" || true

echo "═══ MLX export + iOS bundle ═══" | tee -a "$LOG"
python3 export_parlance_mlx.py --lang es 2>&1 | tee -a "$LOG"
./prepare_ios_coach_model.sh 2>&1 | tee -a "$LOG"

date | tee -a "$LOG"
echo "Done — see $LOG" | tee -a "$LOG"
