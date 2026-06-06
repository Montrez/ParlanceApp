#!/bin/sh
# Xcode Cloud: GoogleService-Info.plist is gitignored (real keys stay local).
# Copy the committed example so Archive can compile; Firebase sign-in won't work
# in CI builds unless you inject a real plist via a custom environment secret.
set -e

ROOT="${CI_PRIMARY_REPOSITORY_PATH:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$ROOT"

PLIST="Parlance/GoogleService-Info.plist"
EXAMPLE="Parlance/GoogleService-Info.plist.example"

if [ -f "$PLIST" ]; then
  echo "ci_pre_xcodebuild: $PLIST already present"
  exit 0
fi

if [ ! -f "$EXAMPLE" ]; then
  echo "error: missing $EXAMPLE — cannot satisfy Xcode Copy Bundle Resources"
  exit 1
fi

python3 - <<'PY'
import re
from pathlib import Path

root = Path(".")
example = root / "Parlance/GoogleService-Info.plist.example"
out = root / "Parlance/GoogleService-Info.plist"
text = example.read_text(encoding="utf-8")
text = re.sub(r"<!--.*?-->\s*", "", text, flags=re.DOTALL)
out.write_text(text, encoding="utf-8")
print(f"ci_pre_xcodebuild: wrote {out} from example (placeholder Firebase config)")
PY
