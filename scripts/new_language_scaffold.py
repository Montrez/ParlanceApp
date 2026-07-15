#!/usr/bin/env python3
"""Scaffold a new Parlance practice language.

Turns "add a new practice language" from a manual, error-prone multi-file
checklist (see issue #12/#14) into one command that generates valid stub
files, then prints exactly what's left to do by hand (real content, Xcode
wiring, training data).

This does NOT touch the *interface* language files (Parlance/web/locales/*.json,
i18n.js's _embedded fallbacks) — those are the UI chrome language (en/es/fr for
buttons/menus), a separate concern from which language you're learning. See
languages.js's header comment for that distinction.

Usage:
    python3 scripts/new_language_scaffold.py <code> "<Display Name>" \\
        [--coach-role "English name for AI prompts"] \\
        [--exam-key dele] [--on-device] [--with-rules] [--force] [--dry-run]

Example:
    python3 scripts/new_language_scaffold.py de "Deutsch" --coach-role German --exam-key goethe

What it does:
    1. Adds a row to Parlance/web/languages.js's PARLANCE_LANGUAGES registry.
    2. Generates Parlance/web/guide-XX.html and dialect-XX.html (structural
       skeleton reused from the guide-es.html/dialect-es.html shells — head,
       CSS, sidebar chrome, mobile-nav script — with placeholder content
       sections marked TODO instead of real grammar content).
    3. Adds stub entries to rag-knowledge.js: RAG_KNOWLEDGE.grammar[XX],
       RAG_KNOWLEDGE.exam[examKey], RAG_KNOWLEDGE.medical/legal.terminology[XX],
       GRAMMAR_TRIGGERS[XX], MEDICAL_KEYWORDS[XX], LEGAL_KEYWORDS[XX].
    4. Generates a stub Parlance/web/coach-standard-XX.js (and, with
       --with-rules, an empty coach-rules-XX.js — optional; French ships
       without one and the engine just skips rule-based detection for it).
    5. Wires index.html: <option> entries in both #langSelect selects, plus
       the new <script> tag(s).
    6. Mirrors every created/edited file into docs/ (kept byte-identical to
       Parlance/web/ per repo convention).
    7. Runs `node --check` on generated/edited JS and validates generated HTML
       is well-formed, then prints a checklist of remaining manual work.

Do not hand-edit the outputs of steps 1-5 with sed/regex elsewhere — rerun
this script (with --force) if you need to change generated stubs before
you've started filling in real content.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = REPO_ROOT / "Parlance" / "web"
DOCS_DIR = REPO_ROOT / "docs"


class _StrictHTMLValidator(HTMLParser):
    """Minimal well-formedness check: every opened tag gets closed, in order."""

    VOID_ELEMENTS = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }

    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag not in self.VOID_ELEMENTS:
            self.stack.append(tag)

    def handle_startendtag(self, tag: str, attrs) -> None:
        pass

    def handle_endtag(self, tag: str) -> None:
        if tag in self.VOID_ELEMENTS:
            return
        if not self.stack:
            self.errors.append(f"unexpected closing tag </{tag}> with nothing open")
            return
        if self.stack[-1] == tag:
            self.stack.pop()
            return
        if tag in self.stack:
            # Close everything up to and including the matching tag (mirrors
            # how browsers recover from unbalanced markup); this is a
            # sanity check, not a strict validator.
            while self.stack and self.stack[-1] != tag:
                self.stack.pop()
            if self.stack:
                self.stack.pop()
        else:
            self.errors.append(f"closing tag </{tag}> has no matching open tag")


def validate_html(text: str, label: str) -> list[str]:
    parser = _StrictHTMLValidator()
    parser.feed(text)
    errs = list(parser.errors)
    if parser.stack:
        errs.append(f"unclosed tag(s): {', '.join(parser.stack)}")
    return [f"{label}: {e}" for e in errs]


# ── generic bracket-aware text surgery ─────────────────────────────────────

def find_balanced_close(text: str, open_idx: int) -> int:
    """Given the index of an opening '{' or '[', return the index of its
    matching close, skipping over string literals AND /regex/ literals so
    quoted or regex-embedded braces/brackets (or apostrophes inside a regex,
    e.g. /\\b(j'ai|...)/  — very much a thing in this codebase's French
    GRAMMAR_TRIGGERS) don't throw off the count."""
    opener = text[open_idx]
    closer = {"{": "}", "[": "]"}[opener]
    depth = 0
    i = open_idx
    in_string: str | None = None
    # last non-whitespace char seen, to disambiguate a leading '/' as regex-start
    # vs. division (division essentially never precedes these tokens in this file).
    prev_significant = ""
    while i < len(text):
        ch = text[i]
        if in_string:
            if ch == "\\":
                i += 2
                continue
            if ch == in_string:
                in_string = None
            i += 1
            continue
        if ch in ("'", '"', "`"):
            in_string = ch
            i += 1
            continue
        if ch == "/" and prev_significant in "([{,:=>&|!?+-~*%^;\n":
            end = _skip_regex_literal(text, i)
            if end is not None:
                i = end
                prev_significant = "/"
                continue
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return i
        if not ch.isspace():
            prev_significant = ch
        i += 1
    raise ValueError(f"unbalanced '{opener}' starting at index {open_idx}")


def _skip_regex_literal(text: str, slash_idx: int) -> int | None:
    """If text[slash_idx] starts a /regex/flags literal, return the index just
    past its flags. Returns None if it doesn't look like a terminated regex
    literal on the same line (in which case the caller should treat '/' as an
    ordinary character, e.g. division)."""
    j = slash_idx + 1
    in_class = False
    while j < len(text):
        c = text[j]
        if c == "\n":
            return None
        if c == "\\":
            j += 2
            continue
        if c == "[":
            in_class = True
        elif c == "]":
            in_class = False
        elif c == "/" and not in_class:
            j += 1
            while j < len(text) and text[j].isalpha():
                j += 1
            return j
        j += 1
    return None


def insert_after_key_block(text: str, container_span: tuple[int, int], key: str, new_entry: str) -> str:
    """Within text[container_span[0]:container_span[1]], find `key: {` or
    `key: [`, locate its matching close, and insert `new_entry` right after
    (adding a leading comma). Returns the full modified text."""
    start, end = container_span
    m = re.search(rf"\b{re.escape(key)}\s*:\s*[\{{\[]", text[start:end])
    if not m:
        raise ValueError(f"could not find key '{key}' in container span {container_span}")
    open_idx = start + m.end() - 1
    close_idx = find_balanced_close(text, open_idx)
    insert_at = close_idx + 1
    return text[:insert_at] + "," + new_entry + text[insert_at:]


def container_span(text: str, key: str) -> tuple[int, int]:
    """Locate `key: {` (top-level-ish) and return (open_idx, close_idx) span
    of its value, inclusive of braces."""
    m = re.search(rf"\b{re.escape(key)}\s*:\s*\{{", text)
    if not m:
        raise ValueError(f"could not find container '{key}'")
    open_idx = m.end() - 1
    close_idx = find_balanced_close(text, open_idx)
    return (open_idx, close_idx + 1)


def const_span(text: str, name: str) -> tuple[int, int]:
    m = re.search(rf"\bconst\s+{re.escape(name)}\s*=\s*\{{", text)
    if not m:
        raise ValueError(f"could not find const '{name}'")
    open_idx = m.end() - 1
    close_idx = find_balanced_close(text, open_idx)
    return (open_idx, close_idx + 1)


def nested_container_span(text: str, parent_key: str, child_key: str) -> tuple[int, int]:
    """Find `child_key: {` inside `parent_key: {...}`, in full-text coordinates."""
    parent_start, parent_end = container_span(text, parent_key)
    m = re.search(rf"\b{re.escape(child_key)}\s*:\s*\{{", text[parent_start:parent_end])
    if not m:
        raise ValueError(f"could not find '{child_key}' inside '{parent_key}'")
    open_idx = parent_start + m.end() - 1
    close_idx = find_balanced_close(text, open_idx)
    return (open_idx, close_idx + 1)


# ── stub content builders ───────────────────────────────────────────────────

CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]


def build_languages_js_entry(code: str, name: str, coach_role: str, exam_key: str, on_device: bool) -> str:
    return f"""
  {code}: {{
    code: '{code}',
    name: '{name}',
    placeholder: 'TODO: placeholder text in {name} (e.g. \\'Write a sentence in {name}…\\')',
    titlePlaceholder: 'Entry title… (e.g. TODO)',
    coachRole: '{coach_role}',
    guideFile: 'guide-{code}.html',
    dialectFile: 'dialect-{code}.html',
    examKey: '{exam_key}',
    hasOnDeviceModel: {str(on_device).lower()},
    coachStandardGlobal: 'ParlanceCoachStandard{code.upper()}',
  }},""".rstrip("\n")


def build_languages_js(existing: str, code: str, name: str, coach_role: str, exam_key: str, on_device: bool) -> str:
    if re.search(rf"\b{code}\s*:\s*\{{", existing):
        raise SystemExit(f"languages.js already has an entry for '{code}' — use --force-aware manual edit, this script won't touch an existing entry")
    m = re.search(r"const PARLANCE_LANGUAGES\s*=\s*\{", existing)
    if not m:
        raise SystemExit("could not find PARLANCE_LANGUAGES in languages.js")
    open_idx = m.end() - 1
    close_idx = find_balanced_close(existing, open_idx)
    entry = build_languages_js_entry(code, name, coach_role, exam_key, on_device)
    return existing[:close_idx] + entry + "\n" + existing[close_idx:]


def build_coach_standard_stub(code: str, name: str) -> str:
    global_name = f"ParlanceCoachStandard{code.upper()}"
    return f"""(function (root) {{
  root.{global_name} = {{
    "version": 1,
    "lang": "{code}",
    "name": "TODO: standard name, e.g. 'Standard {name}'",
    "normative_authority": "TODO: e.g. an academy or standards body for {name}",
    "cefr_framework": "CEFR",
    "role": "TODO: 1-2 sentences describing the register/voice the Coach should teach toward.",
    "principles": [
      "TODO: principle the Coach must apply when grading a sentence"
    ],
    "non_negotiable_errors": [
      "TODO: an error type that should always be 'Needs Improvement', never excused"
    ],
    "excellent_means": "TODO: what 'Excellent' status means for this language",
    "needs_improvement_means": "TODO: what 'Needs Improvement' status means for this language",
    "interpreter_register": "TODO: formal/informal register notes relevant to interpreter training"
  }};
}})(typeof globalThis !== "undefined" ? globalThis : this);
"""


def build_coach_rules_stub(code: str, name: str) -> str:
    global_name = f"ParlanceCoachRules{code.upper()}"
    return f"""(function (root) {{
  root.{global_name} = {{
    "version": 1,
    "lang": "{code}",
    "standard_version": 1,
    "standard_path": "coach-standard-{code}.js",
    "grammar_rule_default": "TODO",
    "rules": []
  }};
}})(typeof globalThis !== "undefined" ? globalThis : this);
"""


def build_guide_html(template_text: str, code: str, name: str, coach_role: str) -> str:
    body_open_start = template_text.index("<body")
    body_start = template_text.index(">", body_open_start) + 1
    nav_start = template_text.index("<nav class=\"sidebar\">", body_start)
    content_start = template_text.index('<div class="content">', nav_start)
    content_end = template_text.index("</div><!-- /content -->", content_start) + len("</div><!-- /content -->")

    head = template_text[:body_open_start]
    head = re.sub(r"<title>.*?</title>", f"<title>{name} A1\u2192C2 Deep Guide (TODO)</title>", head, count=1)
    # guide-es.html/guide-fr.html both used to have `lang="en"` on <html> (a
    # known bug, fixed for #21) — set it correctly here instead of copying
    # that forward. head/content colors and structure both come from the
    # shared content-theme.css/content-guide.css links already in this head;
    # do not add a per-language <style> block here.
    head = re.sub(r'<html lang="[a-z]{2}">', f'<html lang="{code}">', head, count=1)

    tail = template_text[content_end:]

    nav_items = "\n".join(
        f'  <a class="nav-item" href="#todo-{lvl.lower()}">TODO: {lvl} topic <span class="nav-badge">{lvl}</span></a>'
        for lvl in CEFR_LEVELS
    )
    nav = f"""<body class="guide lang-{code}">
<div class="layout">

<!-- SIDEBAR -->
<nav class="sidebar">
  <div class="sidebar-logo">
    <h1>{name}</h1>
    <p>A1 \u2192 C2 Deep Reference (TODO)</p>
  </div>

  <div class="nav-section-label">TODO: sections</div>
{nav_items}
</nav>

<!-- CONTENT -->
<div class="content">

<div class="intro-box">
  <div class="intro-flag">\U0001F4DA</div>
  <div>
    <div class="intro-title">A1 \u2192 C2 {name} Guide (TODO)</div>
    <div class="intro-desc">TODO: intro description. Rules, irregular forms, trigger words, and real examples for every key topic.</div>
  </div>
</div>
"""
    sections = []
    for lvl in CEFR_LEVELS:
        sections.append(f"""
<!-- TODO: replace with real {coach_role} content for {lvl} -->
<section class="tense-section" id="todo-{lvl.lower()}">
  <div class="section-chapter">TODO chapter name \u00b7 {lvl}</div>
  <div class="tense-header-row">
    <h2 class="tense-title">TODO: {lvl} topic title</h2>
    <span class="level-pill">{lvl}</span>
  </div>
  <p class="tense-nickname">TODO: one-line description of this rule/topic</p>

  <div class="rule-box">
    <div class="rule-box-title">The Core Rule</div>
    <p>TODO: explain the rule here.</p>
  </div>
</section>
""")

    return head + nav + "\n".join(sections) + "\n\n" + tail


def build_dialect_html(template_text: str, code: str, name: str) -> str:
    head_end = template_text.index("<body")
    body_tag_end = template_text.index(">", head_end) + 1
    nav_start = template_text.index('<nav class="sidebar">', body_tag_end)
    main_start = template_text.index('<main class="content">', nav_start)
    body_end = template_text.rindex("</body>")

    head = template_text[:head_end]
    head = re.sub(r"<title>.*?</title>", f"<title>Dialect Guide (TODO) \u2014 {name}</title>", head, count=1)
    head = re.sub(r'<html lang="[a-z]{2}">', f'<html lang="{code}">', head, count=1)

    tail = template_text[body_end:]

    body_open = f'<body class="dialect lang-{code}">\n<div class="layout">\n<nav class="sidebar">\n'
    nav_body = """  <div class="sidebar-logo">
    <h1>\U0001F30E TODO: Dialects</h1>
    <p>TODO: tagline for native speakers & interpreters</p>
  </div>
  <div class="nav-section-label">TODO: tool</div>
  <a class="nav-item active" href="#picker">TODO: your region &rarr; theirs</a>
  <div class="nav-section-label">TODO: quick reference</div>
  <a class="nav-item" href="#pronouns">TODO: pronouns</a>
  <a class="nav-item" href="#vocab">TODO: vocabulary</a>
  <a class="nav-item" href="#traps">TODO: trap words</a>
  <a class="nav-item" href="#regions">TODO: regional profiles</a>
  <a class="nav-item" href="#dont-correct">TODO: don't correct this</a>
  <!-- TODO: add <div class="lang-switch"> cross-links to/from the other dialect guides -->
</nav>

<main class="content">
  <div class="rule-box">
    <strong>TODO: "How to use this guide" intro</strong> — explain, in one or
    two sentences, that this page has one interactive TOOL (the region-pair
    picker below) plus several REFERENCE sections in the sidebar menu (see
    docs/adding-a-language.md for why this box exists — it's here to prevent
    the exact "I don't know what's used for what" confusion issue #21 fixed).
  </div>

  <section class="section" id="picker">
    <h2>TODO: your region &rarr; theirs</h2>
    <p class="subtitle">TODO: picker description.</p>

    <div class="picker-card">
      <div class="picker-row">
        <div>
          <label for="fromRegion">TODO: I speak like...</label>
          <select id="fromRegion">
            <option value="">TODO: select your region</option>
            <option value="region1">TODO region 1</option>
            <option value="region2">TODO region 2</option>
          </select>
        </div>
        <div>
          <label for="toRegion">TODO: the other person is from...</label>
          <select id="toRegion">
            <option value="">TODO: select their region</option>
            <option value="region1">TODO region 1</option>
            <option value="region2">TODO region 2</option>
          </select>
        </div>
      </div>
      <p class="picker-note">TODO: interpreter tip about adapting register.</p>
    </div>

    <div id="pairResult" class="pair-result">
      <h3 id="pairTitle"></h3>
      <ul id="pairList"></ul>
    </div>
  </section>

  <section class="section" id="pronouns">
    <h2>TODO: pronouns and address</h2>
    <p class="subtitle">TODO</p>
  </section>

  <section class="section" id="vocab">
    <h2>TODO: vocabulary</h2>
    <p class="subtitle">TODO</p>
  </section>

  <section class="section" id="traps">
    <h2>TODO: trap words</h2>
    <p class="subtitle">TODO</p>
  </section>

  <section class="section" id="regions">
    <h2>TODO: regional profiles</h2>
    <p class="subtitle">TODO: all regions at a glance, to browse. If you only care about two, use the tool above.</p>
  </section>

  <section class="section" id="dont-correct">
    <h2>TODO: don't correct this</h2>
    <p class="subtitle">TODO</p>
  </section>
"""
    return head + body_open + nav_body + tail


# ── rag-knowledge.js stub insertion ─────────────────────────────────────────

def build_rag_knowledge_patch(text: str, code: str, name: str, exam_key: str) -> str:
    grammar_span = container_span(text, "grammar")
    grammar_stub = f"""
    {code}: {{
      A1: {{ rules: ["TODO: A1 grammar rule for {name}"], tips: ["TODO: A1 register tip"] }},
      A2: {{ rules: ["TODO: A2 grammar rule for {name}"], tips: ["TODO: A2 register tip"] }},
      B1: {{ rules: ["TODO: B1 grammar rule for {name}"], tips: ["TODO: B1 register tip"] }},
      B2: {{ rules: ["TODO: B2 grammar rule for {name}"], tips: ["TODO: B2 register tip"] }},
      C1: {{ rules: ["TODO: C1 grammar rule for {name}"], tips: ["TODO: C1 register tip"] }},
      C2: {{ rules: ["TODO: C2 grammar rule for {name}"], tips: ["TODO: C2 register tip"] }}
    }}""".rstrip("\n")
    text = insert_after_key_block(text, grammar_span, "fr", grammar_stub)

    exam_span = container_span(text, "exam")
    exam_stub = f"""
    {exam_key}: {{
      general: "TODO: what {exam_key.upper()} is and who administers it, for {name}.",
      levels: {{
        A1: "TODO", A2: "TODO", B1: "TODO", B2: "TODO", C1: "TODO", C2: "TODO"
      }}
    }}""".rstrip("\n")
    text = insert_after_key_block(text, exam_span, "delf", exam_stub)

    med_term_span = nested_container_span(text, "medical", "terminology")
    med_stub = f"""
      {code}: {{
        body: "TODO: {name} body-part terms",
        conditions: "TODO: {name} common conditions",
        procedures: "TODO: {name} common procedures"
      }}""".rstrip("\n")
    text = insert_after_key_block(text, med_term_span, "fr", med_stub)

    legal_term_span = nested_container_span(text, "legal", "terminology")
    legal_stub = f"""
      {code}: {{
        court: "TODO: {name} court-role terms",
        proceedings: "TODO: {name} proceedings terms",
        rights: "TODO: {name} rights terms"
      }}""".rstrip("\n")
    text = insert_after_key_block(text, legal_term_span, "fr", legal_stub)

    triggers_span = const_span(text, "GRAMMAR_TRIGGERS")
    text = insert_after_key_block(text, triggers_span, "fr", f"\n  {code}: []")

    med_kw_span = const_span(text, "MEDICAL_KEYWORDS")
    text = insert_after_key_block(text, med_kw_span, "fr", f"\n  {code}: [/* TODO: {name} medical keywords */]")

    legal_kw_span = const_span(text, "LEGAL_KEYWORDS")
    text = insert_after_key_block(text, legal_kw_span, "fr", f"\n  {code}: [/* TODO: {name} legal keywords */]")

    return text


# ── index.html wiring ───────────────────────────────────────────────────────

def patch_index_html(text: str, code: str, name: str, with_rules: bool) -> str:
    # 1. abbreviated interface-adjacent select (id="langSelect" abbreviated ES/FR)
    def add_option(html: str, marker: str, option_line: str) -> str:
        idx = html.index(marker)
        insert_at = html.rindex("\n", 0, idx) + 1
        return html[:insert_at] + option_line + "\n" + html[insert_at:]

    html = text
    html = add_option(html, '<option value="fr">Français</option>', f'      <option value="{code}">{name}</option>')

    script_marker = '<script src="coach-standard.js?v=14"></script>'
    idx = html.index(script_marker)
    insert_at = html.rindex("\n", 0, idx) + 1
    new_scripts = f'<script src="coach-standard-{code}.js?v=1"></script>\n'
    if with_rules:
        new_scripts += f'<script src="coach-rules-{code}.js?v=1"></script>\n'
    html = html[:insert_at] + new_scripts + html[insert_at:]
    return html


# ── main ─────────────────────────────────────────────────────────────────────

def node_check(path: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["node", "--check", str(path)], capture_output=True, text=True, timeout=30
        )
    except FileNotFoundError:
        return ["node not found on PATH — skipped syntax check"]
    if result.returncode != 0:
        return [f"{path.name}: {result.stderr.strip()}"]
    return []


def write_both(rel_path: str, content: str, force: bool, dry_run: bool) -> None:
    web_path = WEB_DIR / rel_path
    docs_path = DOCS_DIR / rel_path
    if web_path.exists() and not force:
        raise SystemExit(f"{web_path} already exists — pass --force to overwrite")
    if dry_run:
        print(f"[dry-run] would write {web_path} and {docs_path}")
        return
    web_path.parent.mkdir(parents=True, exist_ok=True)
    docs_path.parent.mkdir(parents=True, exist_ok=True)
    web_path.write_text(content)
    docs_path.write_text(content)


def overwrite_both(rel_path: str, content: str, dry_run: bool) -> None:
    web_path = WEB_DIR / rel_path
    docs_path = DOCS_DIR / rel_path
    if dry_run:
        print(f"[dry-run] would update {web_path} and {docs_path}")
        return
    web_path.write_text(content)
    docs_path.write_text(content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("code", help="two-letter language code, e.g. 'de'")
    parser.add_argument("name", help="display name in that language, e.g. 'Deutsch'")
    parser.add_argument("--coach-role", help="English display name used in AI prompts, e.g. 'German' (defaults to --name)")
    parser.add_argument("--exam-key", default=None, help="exam registry key, e.g. 'goethe' (defaults to '<code>-exam')")
    parser.add_argument("--on-device", action="store_true", help="mark hasOnDeviceModel: true (only do this once a bundled MLX model actually exists)")
    parser.add_argument("--with-rules", action="store_true", help="also generate an (empty) coach-rules-XX.js — optional, French ships without one")
    parser.add_argument("--force", action="store_true", help="overwrite existing generated files for this code")
    parser.add_argument("--dry-run", action="store_true", help="print what would happen without writing anything")
    args = parser.parse_args()

    code = args.code.strip().lower()
    if not re.fullmatch(r"[a-z]{2}", code):
        raise SystemExit("language code must be exactly 2 lowercase letters (e.g. 'de')")
    name = args.name.strip()
    coach_role = (args.coach_role or name).strip()
    exam_key = (args.exam_key or f"{code}-exam").strip().lower()

    print(f"Scaffolding practice language '{code}' ({name})...")

    languages_js = (WEB_DIR / "languages.js").read_text()
    languages_js = build_languages_js(languages_js, code, name, coach_role, exam_key, args.on_device)
    overwrite_both("languages.js", languages_js, args.dry_run)

    guide_template = (WEB_DIR / "guide-es.html").read_text()
    guide_html = build_guide_html(guide_template, code, name, coach_role)
    write_both(f"guide-{code}.html", guide_html, args.force, args.dry_run)

    dialect_template = (WEB_DIR / "dialect-es.html").read_text()
    dialect_html = build_dialect_html(dialect_template, code, name)
    write_both(f"dialect-{code}.html", dialect_html, args.force, args.dry_run)

    coach_standard_js = build_coach_standard_stub(code, name)
    write_both(f"coach-standard-{code}.js", coach_standard_js, args.force, args.dry_run)

    if args.with_rules:
        coach_rules_js = build_coach_rules_stub(code, name)
        write_both(f"coach-rules-{code}.js", coach_rules_js, args.force, args.dry_run)

    rag_knowledge = (WEB_DIR / "rag-knowledge.js").read_text()
    rag_knowledge = build_rag_knowledge_patch(rag_knowledge, code, name, exam_key)
    overwrite_both("rag-knowledge.js", rag_knowledge, args.dry_run)

    index_html = (WEB_DIR / "index.html").read_text()
    index_html = patch_index_html(index_html, code, name, args.with_rules)
    overwrite_both("index.html", index_html, args.dry_run)

    if args.dry_run:
        print("\nDry run complete — no files were written.")
        return 0

    # ── validation ──
    print("\nValidating generated output...")
    problems: list[str] = []
    for js_file in ["languages.js", "rag-knowledge.js", f"coach-standard-{code}.js"] + (
        [f"coach-rules-{code}.js"] if args.with_rules else []
    ):
        problems += node_check(WEB_DIR / js_file)

    for html_file in [f"guide-{code}.html", f"dialect-{code}.html"]:
        problems += validate_html((WEB_DIR / html_file).read_text(), html_file)

    if problems:
        print("VALIDATION PROBLEMS:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("  OK — generated JS passes `node --check`, generated HTML tags balance.")

    print(f"""
Done. Remaining manual steps for '{code}' ({name}):

  1. Write real content in Parlance/web/guide-{code}.html and dialect-{code}.html
     (and their docs/ mirrors — keep byte-identical, this script already synced them).
  2. Fill in Parlance/web/coach-standard-{code}.js with real standard/principles/register text.
  3. Fill in the RAG_KNOWLEDGE stubs this script added to rag-knowledge.js
     (grammar[{code}], exam[{exam_key}], medical/legal.terminology[{code}],
     GRAMMAR_TRIGGERS[{code}], MEDICAL_KEYWORDS[{code}], LEGAL_KEYWORDS[{code}]).
  4. Add a <div class="lang-switch"> cross-link to dialect-{code}.html in the
     OTHER existing dialect-*.html files (and vice versa) — this script only
     wires the new file, not the existing ones.
  5. If you want {name} on the app's *interface* (not just as something to
     practice), add a locales/{code}.json + _embedded fallback in i18n.js —
     separate from everything else this script did.
  6. If/when you want an on-device Parlance Coach model for {name}:
     bundle the MLX weights, add a row to Parlance/LanguageRegistry.swift,
     flip hasOnDeviceModel to true in languages.js, and follow #15's
     training pipeline plan.
  7. Wire the new content files into Xcode so the native app can load them
     from WKWebView (this project uses explicit PBXFileReference entries, not
     synchronized folders):

         python3 scripts/xcode_add_web_resources.py guide-{code}.html dialect-{code}.html \\
             coach-standard-{code}.js{' coach-rules-' + code + '.js' if args.with_rules else ''}

     Then sanity-check with `xcodebuild -list -project Parlance.xcodeproj`
     and a real build before committing.
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
