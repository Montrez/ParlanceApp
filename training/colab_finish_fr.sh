#!/usr/bin/env bash
# French SLM on Colab — run AFTER you connect a GPU in the browser notebook.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
CLI="node /tmp/colab-cli-node/dist/index.js"

EP=$($CLI runtime list --json 2>/dev/null | python3 -c "
import json,sys
d=json.load(sys.stdin)
for r in d.get('runtimes',[]):
    acc=r.get('accelerator','')
    if acc and acc != 'CPU':
        print(r['endpoint']); break
")

if [[ -z "${EP:-}" ]]; then
  echo "No GPU runtime visible. In Colab: Runtime → Change runtime type → T4 GPU → Connect."
  echo "Then run this script again."
  exit 1
fi

echo "Using Colab GPU: $EP"
node "$ROOT/register_colab_runtime.mjs" "$EP" >/dev/null

$CLI fs upload "$ROOT/finetune_slm.py" -r finetune_slm.py -e "$EP"
$CLI fs upload "$ROOT/colab_train.py" -r colab_train.py -e "$EP"
$CLI fs upload "$ROOT/colab_train_fr.py" -r colab_train_fr.py -e "$EP"
$CLI fs upload "$ROOT/reexport_merged.py" -r reexport_merged.py -e "$EP"

if [[ ! -f "$ROOT/parlance_training_data.zip" ]]; then
  (cd "$ROOT" && zip -rq parlance_training_data.zip data/french/train.jsonl data/french/valid.jsonl)
fi
$CLI fs upload "$ROOT/parlance_training_data.zip" -r parlance_training_data.zip -e "$EP"

echo "Starting French training on Colab (background)..."
$CLI exec --background -e "$EP" -f "$ROOT/colab_train_fr.py"
echo "Monitor: $CLI exec attach 1"
echo "When done, run: training/colab_download_fr.sh"
