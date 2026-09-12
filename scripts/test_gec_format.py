#!/usr/bin/env python3
"""Smoke tests for the narrow GEC training format."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "training"))

from gec_format import pair_to_example, seed_row_to_gec, same_sentence  # noqa: E402


def assistant(example: dict) -> dict:
    return json.loads(example["messages"][-1]["content"])


def main() -> None:
    leave = pair_to_example("fr", "Merci à vous.", "Merci à vous.")
    assert leave is not None
    assert assistant(leave)["status"] == "Excellent"
    assert assistant(leave)["correction"] is None

    fix = pair_to_example(
        "fr",
        "Le point négatif que je me suis mal préparé.",
        "Le point négatif est que je me suis mal préparé.",
    )
    assert fix is not None
    assert assistant(fix)["status"] == "Needs Improvement"
    assert "est que" in assistant(fix)["correction"]

    rewrite = pair_to_example(
        "fr",
        "Nous irons à la plage l'année prochaine",
        "Nous sommes allés à la plage l'année dernière",
    )
    assert rewrite is None

    seed = seed_row_to_gec(
        {
            "sentence": "Merci à vous. Cordialement",
            "status": "Excellent",
            "explanation": "Keep merci à vous.",
            "correction": None,
        },
        "fr",
    )
    assert seed is not None
    assert assistant(seed)["status"] == "Excellent"
    assert same_sentence("Merci à vous.", "merci a vous.")
    print("gec_format ok")


if __name__ == "__main__":
    main()
