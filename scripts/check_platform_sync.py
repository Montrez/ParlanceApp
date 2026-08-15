#!/usr/bin/env python3
"""Guard against the iOS and Android apps drifting apart.

Both platforms run the same web layer out of Parlance/web/ (mirrored to docs/,
which Capacitor bundles). The web layer talks to whichever host it is embedded
in through one message protocol: it posts {action: ...} objects and the host
calls back into window.__parlance* functions. When only one host learns a new
action, that feature silently disappears on the other platform instead of
failing loudly -- which is exactly how Android ended up with no native sign-in
while iOS had it for months.

Checks:
  1. Every action journal.js posts to the native bridge is handled by both the
     iOS host files (see IOS_BRIDGE_FILES) and the Android ParlanceBridge.java,
     or is listed in IOS_ONLY_ACTIONS with a reason.
  2. Every window.__parlance* callback journal.js installs is invoked by both
     hosts, or is listed in IOS_ONLY_CALLBACKS with a reason.
  3. Android versionCode/versionName match iOS CFBundleVersion /
     CFBundleShortVersionString, so a release never ships as "1.0 (20)" on one
     store and "2.4 (1)" on the other.

Usage:
  python3 scripts/check_platform_sync.py
"""
from __future__ import annotations

import plistlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOURNAL_JS = ROOT / "Parlance" / "web" / "journal.js"
# The iOS half of the bridge is split: ContentView owns message handling and
# config pushes, AuthManager owns session injection. Both talk to the same web
# layer, so both count as the host when checking parity with Android.
IOS_BRIDGE_FILES = (
    ROOT / "Parlance" / "ContentView.swift",
    ROOT / "Parlance" / "AuthManager.swift",
)
IOS_BRIDGE_LABEL = " / ".join(p.name for p in IOS_BRIDGE_FILES)
ANDROID_BRIDGE = (
    ROOT
    / "android"
    / "app"
    / "src"
    / "main"
    / "java"
    / "com"
    / "parlance"
    / "interpreterguide"
    / "ParlanceBridge.java"
)
INFO_PLIST = ROOT / "Parlance" / "Info.plist"
ANDROID_GRADLE = ROOT / "android" / "app" / "build.gradle"

# Actions the Android host deliberately does not implement. Each entry needs a
# reason; removing the reason means the gap was never a decision.
IOS_ONLY_ACTIONS: dict[str, str] = {
    "showAISettings": "Android uses the web AI settings modal (capability nativeSettings=false).",
}

IOS_ONLY_CALLBACKS: dict[str, str] = {}


def read(path: Path) -> str:
    if not path.exists():
        sys.exit(f"FAIL: expected file is missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def posted_actions(js: str) -> set[str]:
    """Actions journal.js sends to a native host.

    Three shapes: an inline `action: 'foo'` property, a bare string message, and
    the auth helper that forwards its argument as the action.
    """
    return (
        set(re.findall(r"action:\s*'([A-Za-z]+)'", js))
        | set(re.findall(r"postToNative\('([A-Za-z]+)'\)", js))
        | set(re.findall(r"callNativeAuth\('([A-Za-z]+)'\)", js))
    )


def installed_callbacks(js: str) -> set[str]:
    """Callbacks journal.js installs for a host to invoke."""
    return set(re.findall(r"window\.(__parlance[A-Za-z]+)\s*=", js))


def check_protocol(failures: list[str]) -> None:
    js = read(JOURNAL_JS)
    ios = "\n".join(read(path) for path in IOS_BRIDGE_FILES)
    android = read(ANDROID_BRIDGE)

    # `action` is also a free-form key in non-bridge payloads; only the ones a
    # host actually knows about are protocol members.
    actions = {a for a in posted_actions(js) if f'"{a}"' in ios or f'"{a}"' in android}
    for action in sorted(actions):
        if f'"{action}"' not in ios:
            failures.append(
                f"Bridge action '{action}' is handled on Android but not in "
                f"{IOS_BRIDGE_LABEL}."
            )
        if f'"{action}"' not in android and action not in IOS_ONLY_ACTIONS:
            failures.append(
                f"Bridge action '{action}' is handled on iOS but not in "
                f"{ANDROID_BRIDGE.relative_to(ROOT)}. Implement it, or add it to "
                f"IOS_ONLY_ACTIONS in {Path(__file__).name} with a reason."
            )

    for callback in sorted(installed_callbacks(js)):
        if callback in ("__parlanceUpdateConfig",):
            continue
        in_ios = callback in ios
        in_android = callback in android
        if in_ios and not in_android and callback not in IOS_ONLY_CALLBACKS:
            failures.append(
                f"Callback window.{callback} is invoked by iOS but never by "
                f"{ANDROID_BRIDGE.relative_to(ROOT)}. A promise that no host "
                f"resolves hangs until the analysis timeout."
            )
        if in_android and not in_ios:
            failures.append(
                f"Callback window.{callback} is invoked by Android but never by "
                f"{IOS_BRIDGE_LABEL}."
            )


def check_versions(failures: list[str]) -> None:
    plist = plistlib.loads(INFO_PLIST.read_bytes())
    ios_build = str(plist.get("CFBundleVersion", "")).strip()
    ios_marketing = str(plist.get("CFBundleShortVersionString", "")).strip()

    gradle = read(ANDROID_GRADLE)
    code_match = re.search(r"versionCode\s+(\d+)", gradle)
    name_match = re.search(r'versionName\s+"([^"]+)"', gradle)
    if not code_match or not name_match:
        failures.append(f"Could not read versionCode/versionName from {ANDROID_GRADLE.relative_to(ROOT)}.")
        return

    if code_match.group(1) != ios_build:
        failures.append(
            f"Version drift: iOS CFBundleVersion is {ios_build} but Android "
            f"versionCode is {code_match.group(1)}."
        )
    if name_match.group(1) != ios_marketing:
        failures.append(
            f"Version drift: iOS CFBundleShortVersionString is {ios_marketing} but "
            f"Android versionName is {name_match.group(1)}."
        )


def main() -> int:
    failures: list[str] = []
    check_protocol(failures)
    check_versions(failures)

    if failures:
        print("Platform sync check FAILED:\n")
        for failure in failures:
            print(f"  - {failure}")
        print("\nSee scripts/check_platform_sync.py for what each check covers.")
        return 1

    print("Platform sync check passed: bridge protocol and versions match on iOS and Android.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
