#!/usr/bin/env python3
"""Score the GEC adapter on held-out judgment gold. Exit 1 if any case fails."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TRAINING_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TRAINING_DIR))

from gec_format import fold, gec_system_prompt, gec_user_prompt  # noqa: E402

DEFAULT_MODEL = "mlx-community/gemma-4-e2b-it-4bit"
GOLD_PATH = TRAINING_DIR / "golden" / "gec_judgment.jsonl"


def parse_feedback(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate GEC judgment gold")
    parser.add_argument("--lang", default="fr")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--adapter-path",
        type=Path,
        default=TRAINING_DIR / "adapters" / "parlance-gec-fr",
    )
    args = parser.parse_args()

    from mlx_lm import generate, load

    model, tokenizer = load(args.model, adapter_path=str(args.adapter_path))
    failed = 0
    total = 0
    for line in GOLD_PATH.read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        if item.get("lang") != args.lang:
            continue
        total += 1
        messages = [
            {"role": "system", "content": gec_system_prompt(args.lang)},
            {"role": "user", "content": gec_user_prompt(args.lang, item["sentence"])},
        ]
        prompt = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=False
        )
        raw = generate(model, tokenizer, prompt=prompt, max_tokens=180, verbose=False)
        fb = parse_feedback(raw)
        status_ok = fb.get("status") == item["status"]
        corr_ok = True
        if item["status"] == "Needs Improvement":
            corr_ok = fold(fb.get("correction") or "") == fold(item.get("correction") or "")
        else:
            corr_ok = not fb.get("correction")
        ok = status_ok and corr_ok
        if not ok:
            failed += 1
        print("=" * 60)
        print("IN:", item["sentence"])
        print("EXPECT:", item["status"], item.get("correction"))
        print("GOT:   ", fb.get("status"), fb.get("correction"))
        print("PASS" if ok else "FAIL")
    print(f"\n{total - failed}/{total} passed")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
