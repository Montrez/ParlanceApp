#!/usr/bin/env bash
# Poll Colab T4 training and update TRAINING_STATUS.md
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
EP="${COLAB_ENDPOINT:-gpu-t4-s-kkb-usw4a2-102if7uwpmmwz}"
CLI="node /tmp/colab-cli-node/dist/index.js"
START_UTC="2026-05-22T03:11:34"
START_EPOCH=$(date -j -f "%Y-%m-%d %H:%M:%S" "2026-05-21 23:11:34" "+%s" 2>/dev/null || date -d "2026-05-22 03:11:34 UTC" "+%s")
ETA_TYPICAL=$((START_EPOCH + 45 * 60))
ETA_MAX=$((START_EPOCH + 60 * 60))

now=$(date "+%s")
elapsed=$((now - START_EPOCH))
elapsed_min=$((elapsed / 60))

gpu_line=$($CLI runtime resources -e "$EP" 2>&1 | grep -E "Tesla|util" || echo "GPU: unavailable")
exec_line=$($CLI exec list 2>&1 | head -3)

# Probe models when daemon free
models="unknown"
if $CLI exec -e "$EP" "import os; print('es',os.path.isdir('models/parlance-es'),'fr',os.path.isdir('models/parlance-fr'))" 2>/dev/null; then
  models=$($CLI exec -e "$EP" "import os; print('es',os.path.isdir('models/parlance-es'),'fr',os.path.isdir('models/parlance-fr'))" 2>&1 | tail -1)
else
  models="busy (training likely still running)"
fi

status="running"
if echo "$gpu_line" | grep -q "util 0%"; then
  status="idle (check if models exist)"
fi
if echo "$models" | grep -q "es True.*fr True"; then
  status="complete on VM — ready to download"
fi

cat > "$ROOT/TRAINING_STATUS.md" <<EOF
# Colab SLM training tracker

**Last checked:** $(date "+%Y-%m-%d %H:%M:%S %Z") ($(date -u "+%H:%M:%S UTC"))

## Timeline

| | |
|--|--|
| **Started** | 2026-05-21 23:11:34 EDT (exec #5, fixed script) |
| **Elapsed** | **${elapsed_min} min** (~$((elapsed % 60))s) |
| **Typical ETA** | $(date -r "$ETA_TYPICAL" "+%Y-%m-%d %H:%M:%S %Z" 2>/dev/null || date -d "@$ETA_TYPICAL" "+%Y-%m-%d %H:%M:%S %Z") |
| **Latest ETA** | $(date -r "$ETA_MAX" "+%Y-%m-%d %H:%M:%S %Z" 2>/dev/null || date -d "@$ETA_MAX" "+%Y-%m-%d %H:%M:%S %Z") |

## Status: **${status}**

\`\`\`
${gpu_line}
Models: ${models}
\`\`\`

## Exec list

\`\`\`
${exec_line}
\`\`\`

## Job plan

1. Spanish — 3 epochs (~15–25 min)
2. French — 3 epochs (~15–25 min)
3. Merge + save both models (~5–10 min)
4. Download to \`training/models/\` on Mac

EOF

echo "Updated $ROOT/TRAINING_STATUS.md (${elapsed_min} min elapsed, status: ${status})"
