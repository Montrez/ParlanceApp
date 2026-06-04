#!/usr/bin/env python3
"""Quick smoke tests for Parlance fine-tuned SLMs."""

import sys
import time
from pathlib import Path

TRAINING_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TRAINING_DIR))

from parlance_slm_infer import get_engine, MODEL_DIRS  # noqa: E402

TESTS = {
    "es": [
        ("B2", "Yo voy al médico mañana por la mañana."),
        ("B2", "Si yo tendría más tiempo, estudiaría más."),
        ("C1", "La paciente debe suspender los AINEs antes de la cirugía."),
        ("B2", "Hola señora Dominga, cómo está?"),
    ],
    "fr": [
        ("B2", "Je pense que nous devons faire une décision."),
        ("B2", "Si j'aurais su, je serais venu plus tôt."),
        ("C1", "Le patient doit arrêter les AINS avant l'intervention."),
    ],
}


def run_lang(lang: str) -> bool:
    model_dir = MODEL_DIRS[lang]
    if not (model_dir / "model.safetensors").exists():
        print(f"  SKIP {lang}: missing {model_dir}")
        return False

    print(f"\n{'='*50}\n  {lang.upper()} model\n{'='*50}")
    engine = get_engine(lang)
    ok = 0
    for level, sentence in TESTS[lang]:
        t0 = time.time()
        try:
            result = engine.analyze(sentence, level=level)
            elapsed = time.time() - t0
            status = result.get("status", "?")
            assessed = result.get("assessed_level") or "—"
            rule = (result.get("grammar_rule") or "")[:60]
            print(f"\n  [{level}] {sentence[:50]}...")
            print(f"    status={status}  assessed={assessed}  ({elapsed:.1f}s)")
            print(f"    rule: {rule}")
            if result.get("correction"):
                print(f"    fix:  {result['correction'][:70]}")
            ok += 1
        except Exception as e:
            print(f"\n  FAIL [{level}] {sentence[:40]}... — {e}")
    print(f"\n  {ok}/{len(TESTS[lang])} passed for {lang}")
    return ok == len(TESTS[lang])


def main():
    langs = sys.argv[1:] if len(sys.argv) > 1 else ["es", "fr"]
    all_ok = all(run_lang(lang) for lang in langs)
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
