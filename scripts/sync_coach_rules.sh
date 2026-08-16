#!/usr/bin/env bash
# Validate rules, sync standards + rules to embedded JS for web/Firebase
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 training/validate_coach_rules.py
python3 training/run_coach_rules_regression.py --lang es
python3 training/run_coach_rules_regression.py --lang fr
python3 training/run_coach_rules_regression.py --lang en
node -e "
const fs = require('fs');
const path = require('path');

function syncStandard(lang, globalName) {
  const std = JSON.parse(fs.readFileSync(path.join('$ROOT', \`shared/standards/\${lang}-coach-standard.json\`), 'utf8'));
  const out = \`/** Auto-synced from shared/standards/\${lang}-coach-standard.json */\n\`
    + \`(function (root) {\n  root.\${globalName} = \`
    + JSON.stringify(std, null, 2)
    + ';\n})(typeof globalThis !== \"undefined\" ? globalThis : this);\n';
  for (const rel of [\`Parlance/web/coach-standard-\${lang}.js\`, \`docs/coach-standard-\${lang}.js\`]) {
    fs.writeFileSync(path.join('$ROOT', rel), out);
    console.log('wrote', rel);
  }
}

function syncRules(lang, globalName) {
  const j = JSON.parse(fs.readFileSync(path.join('$ROOT', \`shared/coach-rules/\${lang}.json\`), 'utf8'));
  const out = \`/** Auto-synced from shared/coach-rules/\${lang}.json — run scripts/sync_coach_rules.sh */\n\`
    + \`(function (root) {\n  root.\${globalName} = \`
    + JSON.stringify(j, null, 2)
    + ';\n})(typeof globalThis !== \"undefined\" ? globalThis : this);\n';
  for (const rel of [
    \`Parlance/web/coach-rules-\${lang}.js\`,
    \`docs/coach-rules-\${lang}.js\`,
    \`firebase/functions/lib/coach-rules-\${lang}.js\`,
  ]) {
    const p = path.join('$ROOT', rel);
    fs.writeFileSync(p, out);
    console.log('wrote', p);
  }
}

syncStandard('es', 'ParlanceCoachStandardES');
syncStandard('en', 'ParlanceCoachStandardEN');
syncRules('es', 'ParlanceCoachRulesES');
syncRules('fr', 'ParlanceCoachRulesFR');
syncRules('en', 'ParlanceCoachRulesEN');
"
