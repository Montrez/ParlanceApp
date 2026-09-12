#!/usr/bin/env python3
"""Move the iOS and Android version numbers together.

Four files carry a version, and editing them by hand is how they drift:

  Parlance/Info.plist              CFBundleShortVersionString / CFBundleVersion
  Parlance.xcodeproj/project.pbxproj  MARKETING_VERSION / CURRENT_PROJECT_VERSION
  android/app/build.gradle         versionName / versionCode

This reads all of them, refuses to bump if they already disagree, and writes the
same values back to every one. scripts/check_platform_sync.py enforces the same
invariant in CI, so anything this script produces passes by construction.

If they have already drifted, force them back together with --marketing and/or
--build-to (those flags rewrite every file even when values disagree).

Usage:
  scripts/bump_version.py --show          what the numbers are right now
  scripts/bump_version.py --build         build number + 1, marketing untouched
  scripts/bump_version.py --marketing 2.5 set the marketing version
  scripts/bump_version.py --build-to 22   set/sync the build number

The build number is what App Store Connect and Play actually order releases by,
and it only ever goes up. The marketing version is the string humans see.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

INFO_PLIST = ROOT / "Parlance/Info.plist"
PBXPROJ = ROOT / "Parlance.xcodeproj/project.pbxproj"
GRADLE = ROOT / "android/app/build.gradle"

# (file, regex with three groups: prefix, value, suffix)
MARKETING_PATTERNS = [
    (INFO_PLIST, re.compile(
        r"(<key>CFBundleShortVersionString</key>\s*<string>)([^<]+)(</string>)")),
    (PBXPROJ, re.compile(r"(MARKETING_VERSION = )([^;]+)(;)")),
    (GRADLE, re.compile(r'(versionName ")([^"]+)(")')),
]

BUILD_PATTERNS = [
    (INFO_PLIST, re.compile(
        r"(<key>CFBundleVersion</key>\s*<string>)([^<]+)(</string>)")),
    (PBXPROJ, re.compile(r"(CURRENT_PROJECT_VERSION = )([^;]+)(;)")),
    (GRADLE, re.compile(r"(versionCode )(\d+)()")),
]

XCODE_MARKETING_VAR = "$(MARKETING_VERSION)"
XCODE_BUILD_VAR = "$(CURRENT_PROJECT_VERSION)"


@dataclass
class Versions:
    marketing: str
    build: int
    marketing_drift: bool = False
    build_drift: bool = False
    detail: str = ""


def _read_all(patterns) -> list[tuple[Path, str]]:
    """Every value the patterns match, so disagreement is visible."""
    found = []
    for path, pattern in patterns:
        text = path.read_text(encoding="utf-8")
        matches = pattern.findall(text)
        if not matches:
            sys.exit(f"error: no version found in {path.relative_to(ROOT)}")
        for match in matches:
            found.append((path, match[1].strip()))
    return found


def _detail(values: list[tuple[Path, str]]) -> str:
    return ", ".join(
        f"{path.relative_to(ROOT)}={value}" for path, value in values)


def _concrete_marketing(values: list[tuple[Path, str]]) -> list[str]:
    return [v for _, v in values if v and v != XCODE_MARKETING_VAR]


def _concrete_builds(values: list[tuple[Path, str]]) -> list[int]:
    out = []
    for _, v in values:
        if v == XCODE_BUILD_VAR:
            continue
        if v.isdigit():
            out.append(int(v))
    return out


def read_versions(*, require_agree: bool) -> Versions:
    marketing = _read_all(MARKETING_PATTERNS)
    build = _read_all(BUILD_PATTERNS)
    marketing_vals = {v for _, v in marketing}
    build_vals = {v for _, v in build}
    marketing_drift = len(marketing_vals) > 1
    build_drift = len(build_vals) > 1
    detail_parts = []
    if marketing_drift:
        detail_parts.append(f"marketing: {_detail(marketing)}")
    if build_drift:
        detail_parts.append(f"build: {_detail(build)}")
    detail = "; ".join(detail_parts)

    if require_agree and (marketing_drift or build_drift):
        sys.exit(
            f"error: version already disagrees across files ({detail}).\n"
            f"       Sync with --marketing and/or --build-to, then bump.")

    concrete_m = _concrete_marketing(marketing)
    concrete_b = _concrete_builds(build)
    if not concrete_m:
        sys.exit("error: no concrete marketing version found (only Xcode vars?)")
    if not concrete_b:
        sys.exit("error: no concrete build number found (only Xcode vars?)")

    # When drifted, report the highest store-relevant build and a concrete marketing.
    return Versions(
        marketing=sorted(concrete_m)[-1],
        build=max(concrete_b),
        marketing_drift=marketing_drift,
        build_drift=build_drift,
        detail=detail,
    )


def write(patterns, value: str) -> None:
    for path, pattern in patterns:
        text = path.read_text(encoding="utf-8")
        updated = pattern.sub(lambda m: f"{m.group(1)}{value}{m.group(3)}", text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--show", action="store_true",
                        help="print the current versions and exit")
    parser.add_argument("--build", action="store_true",
                        help="increment the build number by one")
    parser.add_argument("--build-to", type=int, metavar="N",
                        help="set the build number outright (also repairs drift)")
    parser.add_argument("--marketing", metavar="X.Y",
                        help="set the marketing version (also repairs drift)")
    args = parser.parse_args()

    forcing = bool(args.marketing or args.build_to is not None)
    current = read_versions(require_agree=not forcing and not args.show)

    if args.show or not (args.build or args.build_to is not None or args.marketing):
        line = f"marketing version {current.marketing}, build {current.build}"
        if current.marketing_drift or current.build_drift:
            line += f" (DRIFT: {current.detail})"
        print(line)
        return 0

    if args.build and args.build_to is not None:
        sys.exit("error: --build and --build-to do the same job, pick one")

    if args.build and (current.marketing_drift or current.build_drift):
        sys.exit(
            f"error: cannot --build while versions disagree ({current.detail}).\n"
            f"       Sync with --marketing / --build-to first.")

    marketing = current.marketing
    build = current.build

    if args.marketing:
        if not re.fullmatch(r"\d+(\.\d+){0,2}", args.marketing):
            sys.exit(f"error: {args.marketing!r} is not a version like 2.5 or 2.5.1")
        marketing = args.marketing

    if args.build:
        build = current.build + 1
    elif args.build_to is not None:
        # Store build numbers only go up. When repairing drift, allowing equal
        # to the highest existing number is how the lagging platforms catch up.
        if args.build_to < current.build:
            sys.exit(
                f"error: build {args.build_to} is below the current high-water "
                f"mark {current.build}. Store build numbers only go up.")
        if args.build_to == current.build and not (current.build_drift or current.marketing_drift):
            sys.exit(
                f"error: build {args.build_to} is already set everywhere. "
                f"Use --build to go to {current.build + 1}.")
        build = args.build_to

    write(MARKETING_PATTERNS, marketing)
    write(BUILD_PATTERNS, str(build))

    print(f"marketing version {current.marketing} -> {marketing}")
    print(f"build {current.build} -> {build}")
    if current.marketing_drift or current.build_drift:
        print(f"repaired drift ({current.detail})")
    print("iOS and Android both updated. Run scripts/check_platform_sync.py to confirm.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
