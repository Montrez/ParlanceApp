#!/usr/bin/env bash
# Re-export Spanish Parlance SLM on Colab T4 (merged FP16), then download to Mac.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
CLI="node /tmp/colab-cli-node/dist/index.js"
EP="${COLAB_EP:-gpu-t4-s-kkb-usw4a2-102if7uwpmmwz}"

echo "== Step 1: Register runtime =="
node "$ROOT/register_colab_runtime.mjs" "$EP" >/dev/null || true

echo "== Step 2: Upload scripts =="
$CLI fs upload "$ROOT/finetune_slm.py" -r finetune_slm.py -e "$EP"
$CLI fs upload "$ROOT/reexport_merged.py" -r reexport_merged.py -e "$EP"

echo "== Step 3: Re-export Spanish on Colab GPU =="
$CLI exec -e "$EP" -- "python3 -m pip install -q torch transformers peft accelerate bitsandbytes && python3 reexport_merged.py --lang es"

echo "== Step 4: Check output size on Colab =="
$CLI exec -e "$EP" -- "ls -lh /content/models/parlance-es/model.safetensors; python3 -c \"import json; c=json.load(open('/content/models/parlance-es/config.json')); print('quantization_config' in c)\""

echo "== Step 5: Download to Mac =="
mkdir -p "$ROOT/models/parlance-es"
$CLI fs download /content/models/parlance-es/model.safetensors -o "$ROOT/models/parlance-es/model.safetensors" -e "$EP"
$CLI fs download /content/models/parlance-es/config.json -o "$ROOT/models/parlance-es/config.json" -e "$EP"
$CLI fs download /content/models/parlance-es/generation_config.json -o "$ROOT/models/parlance-es/generation_config.json" -e "$EP"

echo "== Step 6: Smoke test on Mac =="
python3 "$ROOT/smoke_test_slm.py" es

echo "Done: $ROOT/models/parlance-es/"
