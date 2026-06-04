#!/usr/bin/env bash
# Retrain Parlance Coach for reliable assessed_level (Mac / Colab).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/training"

LANG="${1:-es}"
EPOCHS="${2:-2}"
MAC_FLAG=""
if [[ "$(uname -s)" == "Darwin" ]]; then
  MAC_FLAG="--mac"
fi

echo "═══ 1. Migrate training data to assessed_level schema ═══"
python3 migrate_training_schema.py --lang "$LANG" --include-train-valid

echo ""
echo "═══ 2. Prepare train/valid splits ═══"
python3 prepare_slm_data.py --lang "$LANG"

echo ""
echo "═══ 3. Fine-tune (epochs=$EPOCHS) ═══"
RESUME_FLAG=""
if [[ -d "checkpoints/parlance-${LANG}/checkpoint-"* ]] 2>/dev/null || ls checkpoints/parlance-"${LANG}"/checkpoint-* &>/dev/null; then
  RESUME_FLAG="--resume"
fi
python3 finetune_slm.py --lang "$LANG" --epochs "$EPOCHS" $MAC_FLAG $RESUME_FLAG

echo ""
echo "═══ 4. Smoke test ═══"
python3 smoke_test_slm.py "$LANG"

echo ""
echo "═══ 5. Merge golden seeds + golden regression ═══"
python3 merge_golden_seeds.py
python3 run_coach_regression.py --lang "$LANG"

echo ""
echo "═══ 6. Export MLX for iOS (optional) ═══"
echo "Run: python3 export_parlance_mlx.py --lang $LANG"
echo "Then: ./prepare_ios_coach_model.sh"
