#!/usr/bin/env python3
"""Move the iOS and Android version numbers together.

Four files carry a version, and editing them by hand is how they drift:

  Parlance/Info.plist              CFBundleShortVersionString / CFBundleVersion
  Parlance.xcodeproj/project.pbxproj  MARKETING_VERSION / CURRENT_PROJECT_VERSION
  android/app/build.gradle         versionName / versionCode

This reads all of them, refuses to act if they already disagree, and writes the
same values back to every one. scripts/check_platform_sync.py enforces the same
invariant in CI, so anything this script produces passes by construction.

Usage:
  scripts/bump_version.py --show          what the numbers are right now
  scripts/bump_version.py --build         build number + 1, marketing untouched
  scripts/bump_version.py --marketing 2.5 set the marketing version
  scripts/bump_version.py --build-to 22   force the build number (rarely needed)

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


@dataclass
class Versions:
    marketing: str
    build: int


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


def read_versions() -> Versions:
    marketing = _read_all(MARKETING_PATTERNS)
    build = _read_all(BUILD_PATTERNS)

    for label, values in (("marketing version", marketing), ("build number", build)):
        distinct = {value for _, value in values}
        if len(distinct) > 1:
            detail = ", ".join(
                f"{path.relative_to(ROOT)}={value}" for path, value in values)
            sys.exit(
                f"error: {label} already disagrees across files ({detail}).\n"
                f"       Set them all with --marketing / --build-to before bumping.")

    build_value = build[0][1]
    if not build_value.isdigit():
        sys.exit(f"error: build number {build_value!r} is not a whole number")

    return Versions(marketing=marketing[0][1], build=int(build_value))


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
                        help="set the build number outright")
    parser.add_argument("--marketing", metavar="X.Y",
                        help="set the marketing version")
    args = parser.parse_args()

    current = read_versions()

    if args.show or not (args.build or args.build_to or args.marketing):
        print(f"marketing version {current.marketing}, build {current.build}")
        return 0

    if args.build and args.build_to:
        sys.exit("error: --build and --build-to do the same job, pick one")

    marketing = current.marketing
    build = current.build

    if args.marketing:
        if not re.fullmatch(r"\d+(\.\d+){0,2}", args.marketing):
            sys.exit(f"error: {args.marketing!r} is not a version like 2.5 or 2.5.1")
        marketing = args.marketing

    if args.build:
        build = current.build + 1
    elif args.build_to is not None:
        # Going backwards is the one mistake the stores will not let you undo,
        # so it takes more than a typo to do it here.
        if args.build_to <= current.build:
            sys.exit(
                f"error: build {args.build_to} is not above the current {current.build}. "
                f"Store build numbers only go up.")
        build = args.build_to

    write(MARKETING_PATTERNS, marketing)
    write(BUILD_PATTERNS, str(build))

    print(f"marketing version {current.marketing} -> {marketing}")
    print(f"build {current.build} -> {build}")
    print("iOS and Android both updated. Run scripts/check_platform_sync.py to confirm.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
