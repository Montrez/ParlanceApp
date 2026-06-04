#!/usr/bin/env bash
# Prepare Spanish + French Parlance Coach for iOS archive (MLX 4-bit, ~294 MB each).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

prepare_lang() {
  local lang="$1"
  local mlx_dir="training/models/parlance-${lang}-mlx"
  local bundle_dir="Parlance/Models/parlance-${lang}-mlx"

  echo ""
  echo "==> [$lang] Export merged HF weights to MLX (if needed)"
  if [[ ! -f "${mlx_dir}/config.json" ]]; then
    python3 training/export_parlance_mlx.py --lang "$lang"
  fi

  echo "==> [$lang] Smoke test (Python reference)"
  python3 training/smoke_test_slm.py "$lang"

  echo "==> [$lang] Sync MLX weights into Parlance/Models for Xcode bundle"
  mkdir -p Parlance/Models
  rsync -a --delete "${mlx_dir}/" "${bundle_dir}/"
  du -sh "${bundle_dir}"
}

prepare_lang es
prepare_lang fr

echo ""
echo "OK. Xcode Copy Bundle Resources bundles:"
echo "  Parlance/Models/parlance-es-mlx/"
echo "  Parlance/Models/parlance-fr-mlx/"
echo "Archive: open Parlance.xcodeproj → Product → Archive (device build)."
