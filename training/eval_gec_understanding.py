#!/usr/bin/env python3
"""Extensive French coach eval: leave-alone, real errors, and invention traps.

This is a writing-coach test, not a one-tester checklist.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

TRAINING_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TRAINING_DIR))

from gec_format import (  # noqa: E402
    extract_user_sentence,
    fold,
    gec_system_prompt,
    gec_user_prompt,
    normalize_text,
    token_overlap,
)

DEFAULT_MODEL = "mlx-community/gemma-4-e2b-it-4bit"
CURATED = {
    "fr": TRAINING_DIR / "golden" / "gec_understanding_fr.jsonl",
    "es": TRAINING_DIR / "golden" / "gec_understanding_es.jsonl",
}


def parse_feedback(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


def score_item(item: dict, fb: dict) -> dict:
    expect = item["status"]
    got_status = fb.get("status")
    got_corr = fb.get("correction")
    src = item["sentence"]
    expect_corr = item.get("correction")
    status_ok = got_status == expect
    false_excellent = expect == "Needs Improvement" and got_status == "Excellent"
    false_ni = expect == "Excellent" and got_status == "Needs Improvement"
    rewrite = False
    corr_ok = True

    if expect == "Excellent":
        if got_corr and fold(got_corr) != fold(src):
            corr_ok = False
            rewrite = True
    else:
        if not got_corr:
            corr_ok = False
        else:
            if normalize_text(got_corr) == normalize_text(src):
                corr_ok = False
            for needle in item.get("must_include") or []:
                if fold(needle) not in fold(got_corr):
                    corr_ok = False
            for banned in item.get("must_not") or []:
                if fold(banned) in fold(got_corr) or fold(banned) in fold(fb.get("explanation") or ""):
                    corr_ok = False
            if expect_corr and fold(got_corr) == fold(expect_corr):
                rewrite = False
            else:
                if expect_corr and token_overlap(got_corr, expect_corr) < 0.55:
                    corr_ok = False
                if token_overlap(got_corr, src) < 0.45:
                    rewrite = True
                    corr_ok = False

    ok = status_ok and corr_ok
    return {
        "ok": ok,
        "status_ok": status_ok,
        "corr_ok": corr_ok,
        "false_excellent": false_excellent,
        "false_ni": false_ni,
        "rewrite": rewrite,
        "got_status": got_status,
        "got_corr": got_corr,
    }


def infer(model, tokenizer, lang: str, sentence: str) -> dict:
    messages = [
        {"role": "system", "content": gec_system_prompt(lang)},
        {"role": "user", "content": gec_user_prompt(lang, sentence)},
    ]
    prompt = tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=False
    )
    from mlx_lm import generate

    raw = generate(model, tokenizer, prompt=prompt, max_tokens=200, verbose=False)
    return parse_feedback(raw)


def load_valid_sample(lang: str, n: int, seed: int) -> list[dict]:
    path = TRAINING_DIR / "data" / "gec" / lang / "valid.jsonl"
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            sentence = extract_user_sentence(row)
            assistant = next(
                (m["content"] for m in row.get("messages", []) if m.get("role") == "assistant"),
                "",
            )
            try:
                fb = json.loads(assistant)
            except json.JSONDecodeError:
                continue
            if not sentence or fb.get("status") not in ("Excellent", "Needs Improvement"):
                continue
            rows.append(
                {
                    "id": f"heldout-{len(rows)+1}",
                    "category": "heldout_valid",
                    "sentence": sentence,
                    "status": fb["status"],
                    "correction": fb.get("correction"),
                    "must_include": [],
                    "must_not": [],
                }
            )
    random.Random(seed).shuffle(rows)
    return rows[:n]


def main() -> None:
    parser = argparse.ArgumentParser(description="GEC understanding eval")
    parser.add_argument("--lang", choices=("fr", "es"), default="fr")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--adapter-path", type=Path, default=None)
    parser.add_argument("--heldout", type=int, default=25)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.adapter_path is None:
        args.adapter_path = TRAINING_DIR / "adapters" / f"parlance-gec-{args.lang}"

    from mlx_lm import load

    print(f"Loading {args.model} + {args.adapter_path}")
    model, tokenizer = load(args.model, adapter_path=str(args.adapter_path))

    gold = CURATED[args.lang]
    curated = [json.loads(l) for l in gold.read_text(encoding="utf-8").splitlines() if l.strip()]
    items = curated + load_valid_sample(args.lang, args.heldout, args.seed)

    by_cat = defaultdict(lambda: {"n": 0, "ok": 0, "fe": 0, "fni": 0, "rw": 0})
    fails = []
    for item in items:
        fb = infer(model, tokenizer, args.lang, item["sentence"])
        result = score_item(item, fb)
        cat = item.get("category", "other")
        by_cat[cat]["n"] += 1
        if result["ok"]:
            by_cat[cat]["ok"] += 1
        if result["false_excellent"]:
            by_cat[cat]["fe"] += 1
        if result["false_ni"]:
            by_cat[cat]["fni"] += 1
        if result["rewrite"]:
            by_cat[cat]["rw"] += 1
        mark = "PASS" if result["ok"] else "FAIL"
        print(f"{mark} [{cat}] {item['sentence']}")
        if not result["ok"]:
            print(f"     expect {item['status']} | {item.get('correction')}")
            print(f"     got    {result['got_status']} | {result['got_corr']}")
            fails.append(item["id"])

    print("\n=== UNDERSTANDING REPORT ===")
    total_n = total_ok = fe = fni = rw = 0
    for cat in sorted(by_cat):
        s = by_cat[cat]
        total_n += s["n"]
        total_ok += s["ok"]
        fe += s["fe"]
        fni += s["fni"]
        rw += s["rw"]
        pct = 100 * s["ok"] / s["n"] if s["n"] else 0
        print(
            f"{cat:20} {s['ok']:3}/{s['n']:<3} {pct:5.0f}%  "
            f"missed-error={s['fe']} invented-error={s['fni']} rewrite={s['rw']}"
        )
    print(
        f"{'TOTAL':20} {total_ok:3}/{total_n:<3} {100 * total_ok / total_n:5.0f}%  "
        f"missed-error={fe} invented-error={fni} rewrite={rw}"
    )
    print(
        "\nmissed-error = called Excellent when the learner was wrong. "
        "invented-error = flagged a correct sentence. "
        "rewrite = changed meaning or style instead of the smallest fix."
    )


if __name__ == "__main__":
    main()
