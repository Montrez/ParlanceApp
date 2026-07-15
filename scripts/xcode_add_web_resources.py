#!/usr/bin/env python3
"""Register new Parlance/web/* files as bundled resources in Parlance.xcodeproj.

This project uses classic, explicit PBXFileReference/PBXBuildFile entries (not
Xcode 16's folder-synchronized groups — objectVersion 56 predates that, and
converting the whole project is out of scope for one language's worth of
files). Adding a new bundled web resource has historically meant hand-editing
four different list-like sections of project.pbxproj and hand-rolling UUIDs —
fiddly and easy to get subtly wrong (see: the two dead, misnamed "locales 2"
placeholder groups this script's design replaces, and theme.css shipping in
Parlance/web/ for a while without ever being wired into the app bundle).

This script does that mechanically and idempotently instead. See issue #14.

Usage:
    python3 scripts/xcode_add_web_resources.py <relative-path-under-Parlance/web> [more...]
    python3 scripts/xcode_add_web_resources.py guide-de.html dialect-de.html coach-standard-de.js

Folders (e.g. a locale dir or a bundled MLX model dir) are supported too —
pass the folder's relative path and it's registered with lastKnownFileType =
folder, matching how parlance-es-mlx/parlance-fr-mlx are already wired.

Safe to re-run: any relative path that's already registered (matched by its
`path = "...";` literal) is skipped, not duplicated.
"""
from __future__ import annotations

import re
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PBXPROJ = ROOT / "Parlance.xcodeproj" / "project.pbxproj"
WEB_DIR = ROOT / "Parlance" / "web"

# Every bundled web resource lives directly under this one PBXGroup.
WEB_GROUP_COMMENT = "web"

EXT_TO_FILETYPE = {
    ".html": "text.html",
    ".css": "text.css",
    ".js": "sourcecode.javascript",
    ".json": "text.json",
    ".plist": "text.plist.xml",
}


def fresh_uuid() -> str:
    """24 uppercase hex chars, matching this project's existing ID style."""
    return uuid.uuid4().hex.upper()[:24]


def quoted_path(rel_path: str) -> str:
    """pbxproj quotes any path containing chars that aren't valid in a bare
    identifier (this project quotes any path with a dash, in practice)."""
    return f'"{rel_path}"' if re.search(r"[^A-Za-z0-9_.]", rel_path) else rel_path


def already_registered(text: str, rel_path: str) -> bool:
    # Tolerate either quoting style — existing hand-written entries in this file
    # aren't fully consistent about quoting paths that don't strictly need it
    # (e.g. `path = theme.css;` vs `path = "theme.css";` are both valid and
    # both appear in this project), so match either form rather than only the
    # one quoted_path() would itself produce.
    pattern = rf'path = "?{re.escape(rel_path)}"?;'
    return re.search(pattern, text) is not None


def insert_before_marker(text: str, marker: str, new_line: str) -> str:
    idx = text.index(marker)
    return text[:idx] + new_line + "\n" + text[idx:]


def insert_into_list_near(text: str, unique_prefix: str, new_entry: str) -> str:
    """Find the `children = (` or `files = (` list immediately following
    `unique_prefix` (a substring that uniquely anchors to the right group/
    build phase), and insert `new_entry` as a new element just before that
    list's closing `);`."""
    start = text.index(unique_prefix)
    list_open = text.index("(", start) + 1
    close_idx = text.index("\n\t\t\t);", list_open)
    return text[:close_idx] + f"\n\t\t\t\t{new_entry}," + text[close_idx:]


def add_resource(text: str, rel_path: str) -> tuple[str, str | None]:
    """Returns (possibly-updated text, message). message is None if a no-op
    (already registered)."""
    if already_registered(text, rel_path):
        return text, f"{rel_path}: already registered, skipped"

    name = Path(rel_path).name
    is_dir = (WEB_DIR / rel_path).is_dir()
    if is_dir:
        filetype = "folder"
    else:
        ext = Path(rel_path).suffix.lower()
        filetype = EXT_TO_FILETYPE.get(ext)
        if filetype is None:
            return text, f"{rel_path}: unrecognized extension '{ext}' — add it to EXT_TO_FILETYPE and rerun"

    file_ref_uuid = fresh_uuid()
    build_file_uuid = fresh_uuid()
    qpath = quoted_path(rel_path)

    file_ref_line = (
        f'\t\t{file_ref_uuid} /* {name} */ = {{isa = PBXFileReference; '
        f'lastKnownFileType = {filetype}; path = {qpath}; sourceTree = "<group>"; }};'
    )
    build_file_line = (
        f'\t\t{build_file_uuid} /* {name} in Resources */ = {{isa = PBXBuildFile; '
        f'fileRef = {file_ref_uuid} /* {name} */; }};'
    )

    text = insert_before_marker(text, "/* End PBXFileReference section */", file_ref_line)
    text = insert_before_marker(text, "/* End PBXBuildFile section */", build_file_line)
    text = insert_into_list_near(
        text, f"/* {WEB_GROUP_COMMENT} */ = {{\n\t\t\tisa = PBXGroup;\n\t\t\tchildren = (",
        f"{file_ref_uuid} /* {name} */",
    )
    text = insert_into_list_near(
        text, "isa = PBXResourcesBuildPhase;",
        f"{build_file_uuid} /* {name} in Resources */",
    )
    return text, f"{rel_path}: added ({filetype})"


def validate(pbxproj_path: Path) -> None:
    result = subprocess.run(["plutil", "-lint", str(pbxproj_path)], capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(
            f"plutil -lint failed after edit — NOT leaving a broken project.pbxproj on disk.\n{result.stdout}{result.stderr}"
        )


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1

    original = PBXPROJ.read_text()
    text = original
    messages = []
    for rel_path in argv:
        rel_path = rel_path.strip("/")
        if not (WEB_DIR / rel_path).exists():
            print(f"error: {WEB_DIR / rel_path} does not exist on disk — create the file/folder first")
            return 1
        text, msg = add_resource(text, rel_path)
        messages.append(msg)

    if text == original:
        for m in messages:
            print(m)
        print("No changes needed.")
        return 0

    tmp_path = PBXPROJ.with_suffix(".pbxproj.tmp")
    tmp_path.write_text(text)
    try:
        validate(tmp_path)
    except SystemExit:
        tmp_path.unlink(missing_ok=True)
        raise
    tmp_path.replace(PBXPROJ)

    for m in messages:
        print(m)
    print(f"\nUpdated {PBXPROJ.relative_to(ROOT)} — verify with `xcodebuild -list -project Parlance.xcodeproj` "
          "and a real build before committing.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
