#!/usr/bin/env python3
"""Collapse dialect page dual .ui-en / .ui-native markup into data-t-* attributes.

Before (two DOM nodes, CSS hide/show):
  <h1 class="ui-en">Regional Guide</h1>
  <h1 class="ui-native">Dialectos</h1>

After (one node, filled by guide-ui.js):
  <h1 data-t-en="Regional Guide" data-t-native="Dialectos">Regional Guide</h1>

Run:
  python3 scripts/convert_dialect_bilingual.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "Parlance" / "web"


def class_list(el: Tag) -> list[str]:
    raw = el.get("class") or []
    if isinstance(raw, str):
        return raw.split()
    return list(raw)


def has_class(el: Tag, name: str) -> bool:
    return name in class_list(el)


def strip_ui_class(el: Tag, name: str) -> None:
    classes = [c for c in class_list(el) if c != name]
    if classes:
        el["class"] = classes
    elif "class" in el.attrs:
        del el.attrs["class"]


def inner_markup(el: Tag) -> str:
    return "".join(str(c) for c in el.contents).strip()


def is_plain_text(el: Tag) -> bool:
    return all(isinstance(c, NavigableString) for c in el.contents)


def next_tag_sibling(el: Tag) -> Tag | None:
    sib = el.next_sibling
    while sib is not None:
        if isinstance(sib, Tag):
            return sib
        if isinstance(sib, NavigableString) and sib.strip():
            return None
        sib = sib.next_sibling
    return None


def merge_pair(en_el: Tag, native_el: Tag) -> None:
    en_html = inner_markup(en_el)
    native_html = inner_markup(native_el)
    strip_ui_class(en_el, "ui-en")
    if is_plain_text(en_el) and is_plain_text(native_el):
        en_el["data-t-en"] = en_html
        en_el["data-t-native"] = native_html
        en_el.clear()
        en_el.append(en_html)
    else:
        en_el["data-t-en-html"] = en_html
        en_el["data-t-native-html"] = native_html
        en_el.clear()
        # Seed with English so the page is readable before JS runs
        fragment = BeautifulSoup(en_html, "html.parser")
        for child in list(fragment.contents):
            en_el.append(child)
    native_el.decompose()


def convert_document(html: str, *, native_lang: str, storage_key: str,
                     title_en: str, title_native: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Remove dual-visibility CSS block if present
    for style in soup.find_all("style"):
        text = style.string or ""
        if "ui-en" in text and "ui-native" in text:
            style.decompose()

    # Merge consecutive ui-en / ui-native siblings (same tag)
    changed = True
    while changed:
        changed = False
        for en_el in list(soup.find_all(class_=lambda c: c and "ui-en" in (c if isinstance(c, list) else c.split()))):
            if not isinstance(en_el, Tag) or not has_class(en_el, "ui-en"):
                continue
            native_el = next_tag_sibling(en_el)
            if (
                native_el is None
                or not has_class(native_el, "ui-native")
                or native_el.name != en_el.name
            ):
                continue
            merge_pair(en_el, native_el)
            changed = True

    leftover = soup.select(".ui-en, .ui-native")
    if leftover:
        preview = ", ".join(
            f"{el.name}.{'.'.join(class_list(el))}" for el in leftover[:8]
        )
        raise SystemExit(f"Unmerged ui-en/ui-native left: {preview}")

    # Ensure guide-ui.js is linked before other scripts
    body = soup.body
    if body is None:
        raise SystemExit("No <body>")

    if not soup.find("script", src=re.compile(r"guide-ui\.js")):
        tag = soup.new_tag("script", src="guide-ui.js")
        # Insert before first inline script in body, else append
        first_script = body.find("script")
        if first_script:
            first_script.insert_before(tag)
            first_script.insert_before("\n")
        else:
            body.append(tag)

    # Replace duplicated applyGuideEnv / setGuideReadLang block with GuideUI.init
    for script in list(body.find_all("script")):
        src = script.get("src")
        if src:
            continue
        text = script.string or ""
        if "applyGuideEnv" in text and "setGuideReadLang" in text:
            new = soup.new_string(
                f"""
window.GuideUI.init({{
  nativeLang: {native_lang!r},
  storageKey: {storage_key!r},
  titleEn: {title_en!r},
  titleNative: {title_native!r},
  onApplied: function () {{
    if (typeof updatePair === 'function') updatePair();
  }}
}});
"""
            )
            # Keep mobile-nav helpers that may share the script; strip only the guide-env part
            # If the whole script is env + nav, rebuild carefully.
            before, _, after = text.partition("window.applyGuideEnv")
            # Always preserve helpers above applyGuideEnv (mobile nav, etc.)
            keep = before.rstrip()
            script.clear()
            if keep:
                script.append(keep + "\n\n" + str(new).lstrip("\n"))
            else:
                script.append(new)

    return str(soup)


def main() -> None:
    jobs = [
        (
            WEB / "dialect-es.html",
            dict(
                native_lang="es",
                storage_key="parlance_guide_read_es",
                title_en="Regional Guide — Spanish",
                title_native="Guía de dialectos — Español",
            ),
        ),
        (
            WEB / "dialect-fr.html",
            dict(
                native_lang="fr",
                storage_key="parlance_guide_read_fr",
                title_en="Regional Guide — French",
                title_native="Guide des dialectes — Français",
            ),
        ),
    ]
    for path, kwargs in jobs:
        raw = path.read_text(encoding="utf-8")
        if 'data-t-en="' in raw and "ui-en" not in raw:
            print(f"skip (already converted): {path.name}")
            continue
        out = convert_document(raw, **kwargs)
        path.write_text(out, encoding="utf-8")
        print(f"converted {path.name}")


if __name__ == "__main__":
    main()
