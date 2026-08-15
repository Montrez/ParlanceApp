#!/usr/bin/env python3
"""Generate web CSS variables and native Xcode color assets from design/theme.json.

Single source of truth: design/theme.json. This script is the only thing that
should ever write Parlance/web/theme.css, docs/theme.css, or the color assets
under Parlance/Assets.xcassets/. Do not hand-edit those outputs.

Usage:
    python3 scripts/generate_theme.py [--check]

    --check   Don't write anything; exit 1 if regenerating would change any
              output file (useful in CI to catch theme.json edits that
              weren't followed by re-running this script).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
THEME_JSON = REPO_ROOT / "design" / "theme.json"
WEB_OUTPUTS = [REPO_ROOT / "Parlance" / "web" / "theme.css", REPO_ROOT / "docs" / "theme.css"]
CONTENT_WEB_OUTPUTS = [
    REPO_ROOT / "Parlance" / "web" / "content-theme.css",
    REPO_ROOT / "docs" / "content-theme.css",
]
ASSETS_DIR = REPO_ROOT / "Parlance" / "Assets.xcassets"

CONTENT_VAR_NAMES = {
    "bg": "--bg",
    "surface": "--surface",
    "border": "--border",
    "text": "--text",
    "muted": "--muted",
    "tagBg": "--tag-bg",
    "highlight": "--highlight",
}

CSS_VAR_NAMES = {
    "ink": "--ink",
    "paper": "--paper",
    "paper2": "--paper2",
    "rule": "--rule",
    "muted": "--muted",
    "accent": "--accent",
    "green": "--green",
    "amber": "--amber",
    "blue": "--blue",
    "red": "--red",
    "teal": "--teal",
    "lavender": "--lavender",
    "warningSurface": "--warning-surface",
    "accentText": "--accent-text",
}

TINT_VAR_NAMES = {
    "accent": "--accent-light",
    "green": "--green-bg",
    "amber": "--amber-bg",
    "blue": "--blue-bg",
    "red": "--red-bg",
    "accentText": "--accent-text-bg",
}

HEADER_VAR_NAMES = {
    "bg": "--header-bg",
    "text": "--header-text",
    "muted": "--header-muted",
    "border": "--header-border",
    "selectBg": "--header-select-bg",
    "sep": "--header-sep",
    "accent": "--header-accent",
    "writeBorder": "--header-write-border",
    "writeLabel": "--header-write-label",
}


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def rgba_css(hex_color: str, alpha: float) -> str:
    r, g, b = hex_to_rgb(hex_color)
    return f"rgba({r},{g},{b},{alpha})"


def build_css(theme: dict) -> str:
    tokens = theme["tokens"]
    header_tokens = theme.get("header_tokens", {})
    raw_css = theme.get("raw_css", {})

    def block(mode: str) -> list[str]:
        lines = []
        for key, var_name in CSS_VAR_NAMES.items():
            lines.append(f"  {var_name}: {tokens[key][mode]};")
            tint_var = TINT_VAR_NAMES.get(key)
            if tint_var:
                alpha = tokens[key]["tint_alpha"][mode]
                lines.append(f"  {tint_var}: {rgba_css(tokens[key][mode], alpha)};")
        for key, var_name in HEADER_VAR_NAMES.items():
            if key in header_tokens:
                lines.append(f"  {var_name}: {header_tokens[key][mode]};")
        for key, values in raw_css.items():
            lines.append(f"  --{key}: {values[mode]};")
        return lines

    out = []
    out.append("/* GENERATED FILE — do not edit by hand.")
    out.append("   Source of truth: design/theme.json")
    out.append("   Regenerate with: python3 scripts/generate_theme.py */")
    out.append(":root {")
    out.extend(block("light"))
    out.append("}")
    out.append("")
    out.append('[data-theme="dark"] {')
    out.extend(block("dark"))
    out.append("}")
    out.append("")
    return "\n".join(out)


def build_content_css(theme: dict) -> str:
    tokens = theme["content_tokens"]
    hues = tokens["hues"]

    def block(mode: str) -> list[str]:
        lines = []
        for key, var_name in CONTENT_VAR_NAMES.items():
            lines.append(f"  {var_name}: {tokens[key][mode]};")
        for hue_name, hue in hues.items():
            if hue_name.startswith("$"):
                continue
            lines.append(f"  --{hue_name}: {hue['text'][mode]};")
            lines.append(f"  --{hue_name}-bg: {hue['bg'][mode]};")
        return lines

    out = []
    out.append("/* GENERATED FILE — do not edit by hand.")
    out.append("   Source of truth: design/theme.json (content_tokens)")
    out.append("   Regenerate with: python3 scripts/generate_theme.py")
    out.append("   Used by the standalone reference pages: guide-*.html, dialect-*.html.")
    out.append("   Load this BEFORE content-guide.css. */")
    out.append(":root {")
    out.extend(block("light"))
    out.append("}")
    out.append("")
    out.append('[data-theme="dark"] body, body.dark {')
    out.extend(block("dark"))
    out.append("}")
    out.append("")
    return "\n".join(out)


def component(value: int) -> str:
    return f"{value / 255:.3f}"


def colorset_json(hex_light: str, hex_dark: str) -> dict:
    r, g, b = hex_to_rgb(hex_light)
    dr, dg, db = hex_to_rgb(hex_dark)
    return {
        "colors": [
            {
                "color": {
                    "color-space": "srgb",
                    "components": {
                        "alpha": "1.000",
                        "red": component(r),
                        "green": component(g),
                        "blue": component(b),
                    },
                },
                "idiom": "universal",
            },
            {
                "appearances": [{"appearance": "luminosity", "value": "dark"}],
                "color": {
                    "color-space": "srgb",
                    "components": {
                        "alpha": "1.000",
                        "red": component(dr),
                        "green": component(dg),
                        "blue": component(db),
                    },
                },
                "idiom": "universal",
            },
        ],
        "info": {"author": "xcode", "version": 1},
    }


def build_native_assets(theme: dict) -> dict[Path, str]:
    tokens = theme["tokens"]
    outputs = {}
    for asset_name, token_key in theme["native_assets"].items():
        token = tokens[token_key]
        path = ASSETS_DIR / f"{asset_name}.colorset" / "Contents.json"
        content = json.dumps(colorset_json(token["light"], token["dark"]), indent=2) + "\n"
        outputs[path] = content
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    theme = json.loads(THEME_JSON.read_text())
    css = build_css(theme)
    content_css = build_content_css(theme)
    native_outputs = build_native_assets(theme)

    all_outputs: dict[Path, str] = {path: css for path in WEB_OUTPUTS}
    all_outputs.update({path: content_css for path in CONTENT_WEB_OUTPUTS})
    all_outputs.update(native_outputs)

    changed = []
    for path, content in all_outputs.items():
        existing = path.read_text() if path.exists() else None
        if existing != content:
            changed.append(path)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)

    if args.check:
        if changed:
            print("Theme outputs are stale. Run scripts/generate_theme.py to regenerate:")
            for path in changed:
                print(f"  {path.relative_to(REPO_ROOT)}")
            return 1
        print("Theme outputs are up to date.")
        return 0

    if changed:
        print(f"Generated {len(changed)} file(s):")
        for path in changed:
            print(f"  {path.relative_to(REPO_ROOT)}")
    else:
        print("No changes — theme outputs already up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
