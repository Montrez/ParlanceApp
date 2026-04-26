#!/usr/bin/env python3
"""
Generate training data for Parlance grammar feedback SLM.
Uses Gemini Flash (free tier: 1,500 req/day) to create diverse
(sentence, CEFR level) -> JSON feedback pairs for fine-tuning Qwen 2.5.

Usage:
    export GEMINI_API_KEY="your-key-here"
    python generate_data.py --lang es --count 500
    python generate_data.py --lang fr --count 500
    python generate_data.py --lang es --level A1 --count 100

Output: training/data/{lang}_{level}_{timestamp}.jsonl
"""

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import google.generativeai as genai
except ImportError:
    print("Install the Gemini SDK:  pip install google-generativeai")
    sys.exit(1)

LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

LANG_CONFIG = {
    "es": {
        "name": "Spanish",
        "topics": {
            "A1": [
                "introduce yourself", "describe your family", "order food at a restaurant",
                "ask for directions", "talk about your daily routine", "describe your house",
                "say what you like and dislike", "talk about the weather", "describe your job",
                "talk about hobbies", "numbers and time", "days of the week and months",
            ],
            "A2": [
                "describe a past vacation", "talk about weekend plans", "describe how you feel",
                "compare two cities", "talk about shopping", "describe a friend",
                "explain your morning routine with reflexive verbs", "make plans for tonight",
                "describe a recent experience", "talk about food preferences",
            ],
            "B1": [
                "narrate a childhood memory", "describe a trip using past tenses",
                "express opinions about education", "talk about a movie you saw",
                "describe a problem and solution", "discuss cultural differences",
                "talk about future career goals", "describe a celebration or holiday",
                "give advice to a friend", "express hypothetical wishes",
            ],
            "B2": [
                "argue for or against remote work", "discuss environmental issues",
                "analyze a news article", "describe a complex process",
                "discuss immigration policy", "compare education systems",
                "express regret about past decisions", "discuss technology's impact on society",
                "debate healthcare approaches", "discuss economic inequality",
            ],
            "C1": [
                "interpret a political speech", "summarize a legal document",
                "discuss nuances of dialect variation", "analyze literary themes",
                "explain medical procedures to patients", "discuss diplomatic protocols",
                "interpret in a business negotiation", "analyze economic policy",
                "discuss ethical dilemmas in medicine", "present academic research findings",
            ],
            "C2": [
                "translate legal testimony with precision", "interpret simultaneous conference speech",
                "discuss linguistic register in court settings", "analyze rhetorical devices in speeches",
                "navigate dialectal variation in real-time interpreting",
                "discuss idiomatic vs literal translation trade-offs",
                "interpret emotional testimony maintaining register",
                "analyze bureaucratic language and simplify it",
                "discuss stylistic choices in literary translation",
                "navigate code-switching in bilingual contexts",
            ],
        },
        "error_types": {
            "A1": ["ser/estar confusion", "wrong gender agreement", "wrong present tense conjugation",
                    "missing article", "wrong word order"],
            "A2": ["wrong reflexive pronoun", "ir+a+infinitive errors", "gustar structure errors",
                    "wrong preposition", "stem-change verb errors"],
            "B1": ["preterite vs imperfect confusion", "wrong subjunctive trigger",
                    "ser/estar with adjectives", "por vs para", "wrong perfect tense form"],
            "B2": ["subjunctive in noun clauses", "conditional perfect errors",
                    "si clause sequence of tenses", "anglicisms", "wrong register (formal/informal)"],
            "C1": ["pluperfect subjunctive errors", "wrong verbal periphrasis", "false cognates",
                    "register mismatch in professional context", "calques from English"],
            "C2": ["subtle register shifts", "archaic form misuse", "dialectal inconsistency",
                    "discourse connector misuse", "unnatural collocations"],
        },
    },
    "fr": {
        "name": "French",
        "topics": {
            "A1": [
                "introduce yourself", "describe your family", "order food at a cafe",
                "ask for directions", "talk about your daily routine", "describe your apartment",
                "say what you like and dislike", "talk about the weather", "describe your job",
                "talk about hobbies", "numbers and time", "days of the week and months",
            ],
            "A2": [
                "describe a past vacation", "talk about weekend plans", "describe how you feel",
                "compare two cities", "talk about shopping", "describe a friend",
                "explain your morning routine with reflexive verbs", "make plans for tonight",
                "describe a recent experience", "talk about food preferences using partitives",
            ],
            "B1": [
                "narrate a childhood memory", "describe a trip using past tenses",
                "express opinions about education", "talk about a film you watched",
                "describe a problem and solution", "discuss cultural differences",
                "talk about future career goals", "describe a celebration or holiday",
                "give advice to a friend", "express hypothetical wishes",
            ],
            "B2": [
                "argue for or against remote work", "discuss environmental issues",
                "analyze a news article", "describe a complex process",
                "discuss immigration policy", "compare education systems",
                "express regret about past decisions", "discuss technology's impact on society",
                "debate healthcare approaches", "discuss economic inequality",
            ],
            "C1": [
                "interpret a political speech", "summarize a legal document",
                "discuss nuances of regional French", "analyze literary themes",
                "explain medical procedures to patients", "discuss diplomatic language",
                "interpret in a business negotiation", "analyze economic policy",
                "discuss ethical dilemmas", "present academic research findings",
            ],
            "C2": [
                "translate legal testimony with precision", "interpret simultaneous conference speech",
                "discuss linguistic register in court settings", "analyze rhetorical devices",
                "navigate regional variation in real-time interpreting",
                "discuss idiomatic vs literal translation trade-offs",
                "interpret emotional testimony maintaining register",
                "analyze bureaucratic language and simplify it",
                "discuss stylistic choices in literary translation",
                "navigate code-switching in bilingual contexts",
            ],
        },
        "error_types": {
            "A1": ["être/avoir confusion", "wrong gender agreement", "wrong present tense conjugation",
                    "missing article", "wrong word order"],
            "A2": ["wrong reflexive pronoun", "partitive article errors", "futur proche errors",
                    "wrong preposition", "stem-change verb errors"],
            "B1": ["passé composé vs imparfait confusion", "wrong subjunctive trigger",
                    "auxiliary choice (être/avoir) in passé composé", "wrong past participle agreement",
                    "wrong perfect tense form"],
            "B2": ["subjunctive in noun clauses", "conditionnel passé errors",
                    "si clause sequence of tenses", "anglicisms", "wrong register (tu/vous)"],
            "C1": ["subjonctif imparfait errors", "passé simple misuse", "false cognates",
                    "register mismatch in professional context", "calques from English"],
            "C2": ["subtle register shifts", "literary tense misuse", "dialectal inconsistency",
                    "discourse connector misuse", "unnatural collocations"],
        },
    },
}

GENERATION_PROMPT = """You are generating training data for a language learning AI. Generate {batch_size} DIVERSE training examples for {lang_name} at CEFR level {level}.

The learner is training to become a professional interpreter, so register awareness (formal vs informal) is critical at every level.

For each example, create a realistic sentence a {level} learner might write about: {topic}

Mix of correct (~40%) and incorrect (~60%) sentences. For incorrect sentences, include errors typical of {level} learners: {error_types}

{level_specific_guidance}

Return a JSON array of objects. Each object must have exactly these fields:
- "input_sentence": the sentence the learner wrote (in {lang_name})
- "cefr_level": "{level}"
- "language": "{lang_code}"
- "expected_output": an object with:
  - "status": "Excellent" or "Needs Improvement"
  - "grammar_rule": specific rule in English
  - "explanation": why correct/incorrect, in English, specific and actionable
  - "correction": corrected sentence in {lang_name} (null if Excellent)
  - "next_level_alt": same idea at {next_level} level in {lang_name}
  - "target_level_alt": same idea at {target_level} level in {lang_name} (null if {level} is C1 or C2)
  - "tip": register/formality tip for interpreter training, in English (ALWAYS include)

CRITICAL RULES:
- All example sentences (correction, next_level_alt, target_level_alt) MUST be in {lang_name}
- Vary sentence length, complexity, and vocabulary within the level
- Make errors realistic, not random — these should look like real learner mistakes
- Register tips should note formal vs informal (tú/usted, tu/vous) and professional appropriateness
- Return ONLY the JSON array, no markdown or explanation"""

LEVEL_GUIDANCE = {
    "A1": "Focus on: present tense conjugation, basic ser/estar or être/avoir, simple vocabulary, subject-verb agreement. Be very encouraging in explanations.",
    "A2": "Focus on: reflexive verbs, near future, basic past references, stem-changing verbs, gustar/partitive articles. Gently introduce register.",
    "B1": "Focus on: past tense usage (preterite vs imperfect / passé composé vs imparfait), basic subjunctive triggers, por/para. Note register choices.",
    "B2": "Focus on: subjunctive mood, conditional structures, si clauses, anglicisms, formal vs informal register. Flag register mismatches.",
    "C1": "Focus on: professional register, advanced subjunctive, verbal periphrasis, false cognates, interpreting-specific vocabulary. Register is critical.",
    "C2": "Focus on: near-native precision, stylistic elegance, dialectal awareness, discourse-level cohesion, archaic/literary forms. Master-level register.",
}

NEXT_LEVELS = {"A1": "A2", "A2": "B1", "B1": "B2", "B2": "C1", "C1": "C2", "C2": "native-polish"}
TARGET_LEVELS = {"A1": "B1", "A2": "B2", "B1": "C1", "B2": "C2", "C1": None, "C2": None}


def setup_gemini(api_key: str):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash")


def generate_batch(model, lang: str, level: str, batch_size: int = 10) -> list:
    config = LANG_CONFIG[lang]
    topic = random.choice(config["topics"][level])
    errors = ", ".join(random.sample(config["error_types"][level], min(3, len(config["error_types"][level]))))

    prompt = GENERATION_PROMPT.format(
        batch_size=batch_size,
        lang_name=config["name"],
        lang_code=lang,
        level=level,
        topic=topic,
        error_types=errors,
        level_specific_guidance=LEVEL_GUIDANCE[level],
        next_level=NEXT_LEVELS[level],
        target_level=TARGET_LEVELS[level] or "N/A",
    )

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.9,
            max_output_tokens=8000,
            response_mime_type="application/json",
        ),
    )

    try:
        data = json.loads(response.text)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, AttributeError):
        print(f"  [warn] Failed to parse batch for {lang}/{level}/{topic}")
        return []


def to_training_format(example: dict) -> dict:
    """Convert to instruction-tuning format for Qwen 2.5 fine-tuning."""
    lang_name = "Spanish" if example.get("language") == "es" else "French"
    level = example.get("cefr_level", "B1")

    system_msg = (
        f"You are a {lang_name} grammar coach for interpreter training. "
        f"Analyze the learner's sentence at CEFR level {level}. "
        f"Respond with a JSON object containing: status, grammar_rule, explanation, "
        f"correction, next_level_alt, target_level_alt, and tip. "
        f"All example sentences must be in {lang_name}. Always include a register tip."
    )

    user_msg = f'Analyze this {lang_name} sentence at {level} level: "{example["input_sentence"]}"'

    return {
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": json.dumps(example["expected_output"], ensure_ascii=False)},
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="Generate Parlance SLM training data")
    parser.add_argument("--lang", choices=["es", "fr"], required=True)
    parser.add_argument("--level", choices=LEVELS, default=None, help="Single level (default: all)")
    parser.add_argument("--count", type=int, default=500, help="Total examples to generate")
    parser.add_argument("--batch-size", type=int, default=10, help="Examples per API call")
    parser.add_argument("--output-dir", default="training/data", help="Output directory")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Set GEMINI_API_KEY environment variable.")
        print("Get one free at: https://aistudio.google.com/apikey")
        sys.exit(1)

    model = setup_gemini(api_key)
    levels = [args.level] if args.level else LEVELS
    per_level = args.count // len(levels)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"{args.lang}_{timestamp}.jsonl"

    total = 0
    print(f"Generating {args.count} examples for {LANG_CONFIG[args.lang]['name']}...")
    print(f"Levels: {', '.join(levels)} ({per_level} each)")
    print(f"Output: {out_file}\n")

    with open(out_file, "w", encoding="utf-8") as f:
        for level in levels:
            generated = 0
            batches_needed = (per_level + args.batch_size - 1) // args.batch_size
            print(f"  [{level}] generating {per_level} examples ({batches_needed} batches)...")

            for i in range(batches_needed):
                remaining = per_level - generated
                batch_sz = min(args.batch_size, remaining)
                if batch_sz <= 0:
                    break

                try:
                    examples = generate_batch(model, args.lang, level, batch_sz)
                    for ex in examples:
                        training_ex = to_training_format(ex)
                        f.write(json.dumps(training_ex, ensure_ascii=False) + "\n")
                        generated += 1
                        total += 1
                except Exception as e:
                    print(f"  [error] Batch {i+1} failed: {e}")
                    time.sleep(2)
                    continue

                if i < batches_needed - 1:
                    time.sleep(0.5)

            print(f"  [{level}] done: {generated} examples")

    print(f"\nTotal: {total} examples written to {out_file}")
    print(f"File size: {out_file.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
