#!/usr/bin/env bash
# Download merged French model from Colab (splits large safetensors).
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
[[ -n "${EP:-}" ]] || { echo "No Colab GPU runtime."; exit 1; }

echo "Splitting model on Colab for download..."
$CLI exec -e "$EP" -f /dev/stdin <<'PY'
from pathlib import Path
src = Path("/content/models/parlance-fr/model.safetensors")
chunk = 350 * 1024 * 1024
with open(src, "rb") as f:
    i = 0
    while True:
        data = f.read(chunk)
        if not data:
            break
        (src.parent / f"model.safetensors.part{i:02d}").write_bytes(data)
        print(f"part{i:02d}", len(data))
        i += 1
PY

OUT="$ROOT/models/parlance-fr"
mkdir -p "$OUT"
for i in 00 01 02; do
  if $CLI fs download "/content/models/parlance-fr/model.safetensors.part$i" -o "$OUT/model.safetensors.part$i" -e "$EP" 2>/dev/null; then
    echo "got part $i"
  fi
done
$CLI fs download /content/models/parlance-fr/config.json -o "$OUT/config.json" -e "$EP"

parts=("$OUT"/model.safetensors.part*)
if [[ -f "${parts[0]}" ]]; then
  cat "$OUT"/model.safetensors.part* > "$OUT/model.safetensors"
  rm -f "$OUT"/model.safetensors.part*
  ls -lh "$OUT/model.safetensors"
fi

python3 "$ROOT/smoke_test_slm.py" fr
