#!/usr/bin/env bash
# Phase B: rebalance CEFR prompt + short Spanish retrain (native assessed_level labels).
# Re-invoke under caffeinate so the Mac stays awake until train + export finish.
if [[ -z "${PARLANCE_CAFFEINATE:-}" ]]; then
  export PARLANCE_CAFFEINATE=1
  exec caffeinate -dims "$0" "$@"
fi
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/training"
LOG="$ROOT/training/phase_b_retrain_es.log"
EPOCHS="${1:-1}"
ARCHIVE="data/spanish/archive_legacy_schema"

exec > >(tee -a "$LOG") 2>&1
echo "═══ Phase B ES retrain (CEFR prompt rebalance) — $(date) ═══"
echo "Log: $LOG  epochs=$EPOCHS"

echo ""
echo "═══ 1. Rebuild training data (base + dialect + seed, updated CEFR prompt) ═══"
mkdir -p data/spanish "$ARCHIVE"
for f in base.jsonl dialect_20260508_105447.jsonl seed_assessed_level_es.jsonl; do
  if [[ ! -f "$ARCHIVE/$f" ]]; then
    echo "ERROR: missing $ARCHIVE/$f"
    exit 1
  fi
  cp "$ARCHIVE/$f" "data/spanish/$f"
done
rm -f data/spanish/assessed_level_es.jsonl data/spanish/train.jsonl data/spanish/valid.jsonl
python3 migrate_training_schema.py --lang es
cp "$ARCHIVE/seed_assessed_level_es.jsonl" data/spanish/

echo ""
echo "═══ 2. Merge golden seeds ═══"
python3 merge_golden_seeds.py --lang es

echo ""
echo "═══ 3. Prepare train/valid splits ═══"
python3 prepare_slm_data.py --lang es
TRAIN_N=$(wc -l < data/spanish/train.jsonl | tr -d ' ')
if [[ "$TRAIN_N" -lt 500 ]]; then
  echo "ERROR: train.jsonl has only $TRAIN_N rows — aborting (need 500+)."
  exit 1
fi
echo "  train=$TRAIN_N rows OK"

echo ""
echo "═══ 4. Fine-tune — epochs=${EPOCHS}, resume from checkpoint-160 ═══"
python3 finetune_slm.py --lang es --epochs "$EPOCHS" --mac --resume

echo ""
echo "═══ 5. Smoke test ═══"
python3 smoke_test_slm.py es

echo ""
echo "═══ 6. Golden regression ═══"
python3 run_coach_regression.py --lang es

echo ""
echo "═══ 7. Coach rules regression ═══"
python3 run_coach_rules_regression.py --lang es

echo ""
echo "═══ 8. Export MLX 4-bit for iOS ═══"
python3 export_parlance_mlx.py --lang es

echo ""
echo "═══ 9. Sync MLX into Parlance/Models ═══"
"$ROOT/training/prepare_ios_coach_model.sh"

echo ""
echo "═══ Phase B complete — $(date) ═══"
