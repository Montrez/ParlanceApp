#!/usr/bin/env python3
"""Upload a signed AAB to the Play internal track using gcloud user credentials."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import urllib.error
import urllib.request

PACKAGE = "com.parlance.interpreterguide"
TRACK = "internal"
API = "https://androidpublisher.googleapis.com/androidpublisher/v3"


def token() -> str:
    out = subprocess.check_output(
        ["gcloud", "auth", "application-default", "print-access-token"],
        text=True,
    ).strip()
    if not out:
        raise SystemExit("gcloud auth print-access-token returned empty")
    return out


def request(method: str, url: str, data: bytes | None = None, content_type: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token()}"}
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Play API {err.code} {method} {url}\n{detail}") from err


def main() -> None:
    aab = Path(sys.argv[1] if len(sys.argv) > 1 else
               "android/app/build/outputs/bundle/release/app-release.aab")
    if not aab.is_file():
        raise SystemExit(f"Missing AAB: {aab}")

    edit = request("POST", f"{API}/applications/{PACKAGE}/edits", b"{}", "application/json")
    edit_id = edit["id"]
    print(f"Opened Play edit {edit_id}")

    upload_url = (
        f"https://androidpublisher.googleapis.com/upload/androidpublisher/v3/"
        f"applications/{PACKAGE}/edits/{edit_id}/bundles?uploadType=media"
    )
    bundle = request(
        "POST",
        upload_url,
        aab.read_bytes(),
        "application/octet-stream",
    )
    version_code = bundle.get("versionCode")
    print(f"Uploaded bundle versionCode={version_code}")

    request(
        "PUT",
        f"{API}/applications/{PACKAGE}/edits/{edit_id}/tracks/{TRACK}",
        json.dumps({
            "track": TRACK,
            "releases": [{
                "name": f"2.4 ({version_code})",
                "status": "completed",
                "versionCodes": [str(version_code)],
            }],
        }).encode(),
        "application/json",
    )
    print(f"Assigned {version_code} to {TRACK}")

    request("POST", f"{API}/applications/{PACKAGE}/edits/{edit_id}:commit", b"{}", "application/json")
    print(f"Committed. Internal track has {PACKAGE} {version_code}.")
    # Keep the process from looking hung on a huge upload.
    time.sleep(0)


if __name__ == "__main__":
    main()
