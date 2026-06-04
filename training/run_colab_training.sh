#!/usr/bin/env bash
# Run Parlance SLM training on Google Colab T4 via colab-cli (browser GPU, not local).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
CLI="node /tmp/colab-cli-node/dist/index.js"
COLAB_CLI_REPO="${COLAB_CLI_REPO:-/tmp/colab-cli-node}"

if [[ ! -f "$COLAB_CLI_REPO/dist/index.js" ]]; then
  echo "Install colab-cli: git clone https://github.com/MurphyLo/colab-cli.git $COLAB_CLI_REPO && cd $COLAB_CLI_REPO && npm install && npm run build"
  exit 1
fi

CLI="node $COLAB_CLI_REPO/dist/index.js"

# One-time auth (opens browser)
if ! $CLI auth status 2>&1 | grep -q "Logged in"; then
  echo "Opening Google OAuth — approve in the browser..."
  open "$($CLI auth login --json 2>&1 | python3 -c "import sys,json; print(json.load(sys.stdin)['url'])")" 2>/dev/null || true
  for _ in $(seq 1 40); do
    $CLI auth status 2>&1 | grep -q "Logged in" && break
    sleep 3
  done
fi

# Zip data if missing
if [[ ! -f "$ROOT/parlance_training_data.zip" ]]; then
  (cd "$ROOT" && zip -rq parlance_training_data.zip \
    data/spanish/train.jsonl data/spanish/valid.jsonl \
    data/french/train.jsonl data/french/valid.jsonl)
fi

# Use existing T4 or create one
EP=$($CLI runtime list --json 2>/dev/null | python3 -c "
import json,sys
d=json.load(sys.stdin)
for r in d.get('runtimes',[]):
    if r.get('accelerator')=='T4':
        print(r['endpoint']); break
" 2>/dev/null || true)

if [[ -z "${EP:-}" ]]; then
  echo "Creating T4 runtime..."
  EP=$($CLI runtime create --accelerator T4 --json | python3 -c "import json,sys; print(json.load(sys.stdin)['endpoint'])")
else
  echo "Using existing T4: $EP"
  node "$ROOT/register_colab_runtime.mjs" "$EP" >/dev/null
fi

$CLI fs upload "$ROOT/finetune_slm.py" -r finetune_slm.py -e "$EP"
$CLI fs upload "$ROOT/colab_train_all.py" -r colab_train_all.py -e "$EP"
$CLI fs upload "$ROOT/parlance_training_data.zip" -r parlance_training_data.zip -e "$EP"

echo "Starting training (background exec id 1)..."
$CLI exec --background -e "$EP" -f "$ROOT/colab_train_all.py"
echo "Monitor: $CLI exec attach 1"
echo "When done, download models from /content/models/ on the runtime."
