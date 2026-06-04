#!/usr/bin/env python3
"""
Generate training data for Parlance grammar feedback SLM.
Creates diverse (sentence, CEFR level) -> JSON feedback pairs for fine-tuning Qwen 2.5.

Supports two free backends:
  - Groq: Free Llama 3.3 70B (get key at console.groq.com)
  - Gemini: Free tier 1,500 req/day (get key at aistudio.google.com/apikey)

Usage:
    # Groq (recommended — free, fast, no daily limit)
    export GROQ_API_KEY="your-key"
    python generate_data.py --backend groq --lang es --count 500
    python generate_data.py --backend groq --lang fr --count 500

    # Gemini
    export GEMINI_API_KEY="your-key"
    python generate_data.py --backend gemini --lang es --count 500

Output: training/data/{lang}_{timestamp}.jsonl
"""

import argparse
import json
import os
import random
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

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
- Register tips should note formal vs informal and professional appropriateness
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


# ── BACKENDS ──────────────────────────────────────────────────────

def groq_generate(api_key: str, model: str, prompt: str) -> str:
    """Call Groq API using only stdlib (no extra dependencies)."""
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }).encode()

    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Parlance/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def gemini_generate(api_key: str, model: str, prompt: str) -> str:
    """Call Gemini API using only stdlib."""
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 8000,
            "responseMimeType": "application/json",
        },
    }).encode()

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data["candidates"][0]["content"]["parts"][0]["text"]


# ── GENERATION ────────────────────────────────────────────────────

def build_prompt(lang: str, level: str, batch_size: int) -> str:
    config = LANG_CONFIG[lang]
    topic = random.choice(config["topics"][level])
    errors = ", ".join(random.sample(config["error_types"][level], min(3, len(config["error_types"][level]))))

    return GENERATION_PROMPT.format(
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


def generate_batch(backend_fn, api_key: str, model: str, lang: str, level: str, batch_size: int = 10) -> list:
    prompt = build_prompt(lang, level, batch_size)

    # Groq needs a wrapper hint since response_format: json_object returns an object, not array
    if "groq" in str(backend_fn.__name__):
        prompt += '\n\nWrap the array in a JSON object: {"examples": [...]}'

    raw = backend_fn(api_key, model, prompt)

    try:
        data = json.loads(raw.strip())
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "examples" in data:
            return data["examples"]
        return []
    except (json.JSONDecodeError, KeyError):
        print(f"  [warn] Failed to parse batch for {lang}/{level}")
        return []


def to_training_format(example: dict) -> dict:
    """Convert to instruction-tuning format for Qwen 2.5 fine-tuning."""
    from coach_training_format import build_training_messages, migrate_feedback_payload

    lang = example.get("language", "es")
    sentence = example["input_sentence"]
    level = example.get("cefr_level", "B1")
    expected = dict(example["expected_output"])
    feedback = migrate_feedback_payload(expected, sentence, level, lang)
    return build_training_messages(lang, sentence, feedback)


def main():
    parser = argparse.ArgumentParser(description="Generate Parlance SLM training data")
    parser.add_argument("--backend", choices=["groq", "gemini"], default="groq", help="API backend (default: groq)")
    parser.add_argument("--lang", choices=["es", "fr"], required=True)
    parser.add_argument("--level", choices=LEVELS, default=None, help="Single level (default: all)")
    parser.add_argument("--count", type=int, default=500, help="Total examples to generate")
    parser.add_argument("--batch-size", type=int, default=10, help="Examples per API call")
    parser.add_argument("--output-dir", default="training/data", help="Output directory")
    parser.add_argument("--delay", type=float, default=None, help="Seconds between batches")
    args = parser.parse_args()

    if args.backend == "groq":
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("Set GROQ_API_KEY environment variable.")
            print("Get one free at: https://console.groq.com/keys")
            sys.exit(1)
        backend_fn = groq_generate
        model = "meta-llama/llama-4-scout-17b-16e-instruct"
        delay = args.delay if args.delay is not None else 2.0
    else:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Set GEMINI_API_KEY environment variable.")
            print("Get one free at: https://aistudio.google.com/apikey")
            sys.exit(1)
        backend_fn = gemini_generate
        model = "gemini-1.5-flash"
        delay = args.delay if args.delay is not None else 4.0

    levels = [args.level] if args.level else LEVELS
    per_level = args.count // len(levels)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    existing = list(out_dir.glob(f"{args.lang}_*.jsonl"))
    if existing:
        out_file = max(existing, key=lambda p: p.stat().st_mtime)
        print(f"Appending to existing file: {out_file}")
    else:
        out_file = out_dir / f"{args.lang}_{timestamp}.jsonl"

    total = 0
    lang_name = LANG_CONFIG[args.lang]["name"]
    print(f"Backend: {args.backend} ({model})", flush=True)
    print(f"Generating {args.count} examples for {lang_name}...", flush=True)
    print(f"Levels: {', '.join(levels)} ({per_level} each)", flush=True)
    print(f"Output: {out_file}\n", flush=True)

    with open(out_file, "a", encoding="utf-8") as f:
        for level in levels:
            generated = 0
            batches_needed = (per_level + args.batch_size - 1) // args.batch_size
            print(f"  [{level}] generating {per_level} examples ({batches_needed} batches)...", flush=True)

            for i in range(batches_needed):
                remaining = per_level - generated
                batch_sz = min(args.batch_size, remaining)
                if batch_sz <= 0:
                    break

                for attempt in range(5):
                    try:
                        examples = generate_batch(backend_fn, api_key, model, args.lang, level, batch_sz)
                        for ex in examples:
                            training_ex = to_training_format(ex)
                            f.write(json.dumps(training_ex, ensure_ascii=False) + "\n")
                            generated += 1
                            total += 1
                        f.flush()
                        break
                    except Exception as e:
                        wait = min(15 * (2 ** attempt) + random.uniform(0, 5), 120)
                        print(f"  [error] Batch {i+1} attempt {attempt+1} failed: {e}", flush=True)
                        if attempt < 4:
                            print(f"  [retry] Waiting {wait:.0f}s...", flush=True)
                            time.sleep(wait)

                if i < batches_needed - 1:
                    time.sleep(delay)

                if (i + 1) % 5 == 0:
                    print(f"    ... {generated}/{per_level} examples so far", flush=True)

            print(f"  [{level}] done: {generated} examples", flush=True)

    print(f"\nTotal: {total} examples written to {out_file}")
    if out_file.stat().st_size > 0:
        print(f"File size: {out_file.stat().st_size / 1024:.1f} KB")
    else:
        print("Warning: No examples generated. Check your API key and quota.")


if __name__ == "__main__":
    main()
