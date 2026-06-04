#!/usr/bin/env bash
# Validate, regression-test, and sync shared/coach-rules/es.json → embedded JS
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 training/validate_coach_rules.py
python3 training/run_coach_rules_regression.py --lang es
node -e "
const fs = require('fs');
const path = require('path');
const j = JSON.parse(fs.readFileSync(path.join('$ROOT', 'shared/coach-rules/es.json'), 'utf8'));
const out = '/** Auto-synced from shared/coach-rules/es.json — run scripts/sync_coach_rules.sh */\n'
  + '(function (root) {\n  root.ParlanceCoachRulesES = '
  + JSON.stringify(j, null, 2)
  + ';\n})(typeof globalThis !== \"undefined\" ? globalThis : this);\n';
for (const rel of [
  'Parlance/web/coach-rules-es.js',
  'docs/coach-rules-es.js',
  'firebase/functions/lib/coach-rules-es.js',
]) {
  const p = path.join('$ROOT', rel);
  fs.writeFileSync(p, out);
  console.log('wrote', p);
}
"
