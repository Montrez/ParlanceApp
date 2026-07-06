#!/usr/bin/env bash
# Overnight Spanish retrain with Parlance Spanish Standard in every system prompt.
# Re-invoke under caffeinate so the Mac stays awake until train + regression finish.
if [[ -z "${PARLANCE_CAFFEINATE:-}" ]]; then
  export PARLANCE_CAFFEINATE=1
  exec caffeinate -dims "$0" "$@"
fi
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/training"
LOG="$ROOT/training/standard_retrain_es.log"
EPOCHS="${1:-2}"

exec > >(tee -a "$LOG") 2>&1
echo "═══ Parlance ES standard retrain — $(date) ═══"
echo "Log: $LOG"

echo ""
echo "═══ 1. Rebuild assessed_level data (standard in system prompts) ═══"
if [[ ! -f data/spanish/assessed_level_es.jsonl ]] || [[ $(wc -l < data/spanish/assessed_level_es.jsonl) -lt 100 ]]; then
  python3 migrate_training_schema.py --lang es --include-train-valid
else
  echo "  assessed_level_es.jsonl present — skipping migrate (already refreshed)"
fi
if [[ ! -f data/spanish/seed_assessed_level_es.jsonl ]]; then
  cp data/spanish/archive_legacy_schema/seed_assessed_level_es.jsonl data/spanish/ 2>/dev/null || true
fi

echo ""
echo "═══ 2. Merge golden seeds ═══"
if [[ ! -f data/spanish/seed_assessed_level_es.jsonl ]]; then
  cp data/spanish/archive_legacy_schema/seed_assessed_level_es.jsonl data/spanish/ 2>/dev/null || true
fi
python3 merge_golden_seeds.py --lang es

echo ""
echo "═══ 3. Prepare train/valid splits ═══"
python3 prepare_slm_data.py --lang es

echo ""
echo "═══ 4. Fine-tune — epochs=${EPOCHS}, fresh LoRA, no resume ═══"
python3 finetune_slm.py --lang es --epochs "$EPOCHS" --mac

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
echo "═══ 9. Sync MLX into Parlance/Models (Xcode bundle) ═══"
"$ROOT/training/prepare_ios_coach_model.sh"

echo ""
echo "═══ Done — $(date) ═══"
