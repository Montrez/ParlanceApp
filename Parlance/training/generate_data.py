#!/usr/bin/env python3
"""
Generate synthetic training data for Parlance language feedback SLM.

Uses the Anthropic API to generate high-quality training examples matching
the SentenceReview JSON schema. Output is in JSONL format ready for
MLX LoRA fine-tuning.

Usage:
    pip install anthropic
    export ANTHROPIC_API_KEY="sk-ant-..."
    python generate_data.py --language es --count 500
    python generate_data.py --language fr --count 500
    python generate_data.py --language es --count 500 --level C1
    python generate_data.py --format mlx  # Convert to MLX chat format
"""

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("Install the Anthropic SDK: pip install anthropic")
    sys.exit(1)

# Grammar topics per level and language
TOPICS = {
    "es": {
        "B1": [
            "ser vs estar with adjectives",
            "preterito indefinido regular conjugation",
            "preterito imperfecto for habitual past",
            "indefinido vs imperfecto contrast",
            "present tense irregular yo forms",
            "gender agreement (el/la with nouns ending in -a/-o exceptions)",
            "gustar-type verbs (encantar, molestar, interesar)",
            "preterito perfecto with haber + participio",
            "por vs para",
            "direct and indirect object pronouns",
            "reflexive verbs in daily routine",
            "ir a + infinitive for future plans",
            "telling time and age in the past (imperfecto)",
            "hacer + time expressions (hace dos anos que...)",
        ],
        "B2": [
            "present subjunctive after querer que, esperar que",
            "present subjunctive after es importante que, es necesario que",
            "present subjunctive after no creer que, dudar que",
            "present subjunctive in future time clauses (cuando, en cuanto)",
            "imperfect subjunctive in si clauses Type 2",
            "imperfect subjunctive after past tense main verbs (sequence of tenses)",
            "preterito pluscuamperfecto for past-before-past",
            "Anglicism: aplicar para (should be solicitar)",
            "Anglicism: realizar meaning 'to realize' (should be darse cuenta)",
            "Anglicism: soportar meaning 'to support' (should be apoyar)",
            "Anglicism: atender meaning 'to attend' (should be asistir a)",
            "Anglicism: English word order with adjectives before nouns",
            "condicional simple for hypotheticals and polite requests",
            "reported speech with tense shifting",
            "subjunctive vs indicative after creer/no creer",
            "como si + imperfect subjunctive",
        ],
        "C1": [
            "Type 3 si clauses (pluperfect subjunctive + conditional perfect)",
            "mixed si clauses (past condition, present result)",
            "professional register for interpreting contexts",
            "advanced Anglicisms in formal writing",
            "subjunctive in relative clauses with indefinite antecedent",
            "concessive clauses with aunque + subjunctive vs indicative",
            "passive voice and se constructions in formal register",
            "nuanced word precision (efectivo vs eficaz vs eficiente)",
            "perifrasis verbales (deber de + inf vs deber + inf)",
            "formal hedging (cabria senalar, conviene destacar)",
            "nominalizations for academic/professional register",
            "subjunctive in adverbial clauses of purpose and concession",
        ],
    },
    "fr": {
        "B1": [
            "passe compose with avoir (regular participles)",
            "passe compose with etre (DR MRS VANDERTRAMPP verbs)",
            "imparfait for habitual past and descriptions",
            "passe compose vs imparfait contrast",
            "futur simple regular and irregular stems",
            "futur simple after quand/lorsque/des que with future meaning",
            "conditionnel present for polite requests",
            "gender agreement with adjectives",
            "partitive articles (du, de la, des, de)",
            "reflexive verbs in passe compose (etre + agreement)",
            "negation patterns (ne...pas, ne...jamais, ne...plus)",
            "pronouns y and en",
            "relative pronouns qui, que, ou, dont",
        ],
        "B2": [
            "present subjunctive after vouloir que, il faut que",
            "present subjunctive after emotions (etre content que, regretter que)",
            "present subjunctive after doubt (douter que, ne pas croire que)",
            "present subjunctive after conjunctions (bien que, pour que, avant que)",
            "past participle agreement with preceding direct object (avoir)",
            "plus-que-parfait for past-before-past",
            "conditionnel passe for past hypotheticals and regret",
            "Type 2 si clauses (imparfait + conditionnel present)",
            "Type 3 si clauses (plus-que-parfait + conditionnel passe)",
            "subjonctif passe for completed actions in subjunctive contexts",
            "subjunctive after superlatives (le meilleur que + subj)",
            "Anglicism: realiser for 'to realize' (should be se rendre compte)",
            "Anglicism: faire une decision (should be prendre une decision)",
            "Anglicism: supporter for 'to support' (should be soutenir)",
            "False cognate: excite (sexual connotation in French)",
            "reported speech with tense concordance",
        ],
        "C1": [
            "journalistic conditionnel (unverified information)",
            "futur anterieur for probability about past",
            "professional register for interpreting contexts",
            "advanced concessive constructions (quoique, quelque...que)",
            "formal hedging (il semblerait que, on pourrait avancer que)",
            "nominalizations and abstract noun usage",
            "passive voice with se faire + infinitive",
            "nuanced Anglicisms in formal/professional French",
            "advanced relative clauses (auquel, duquel, lequel)",
            "ne expletif after avant que, a moins que, de peur que",
            "formal register distinctions (tu vs vous in professional settings)",
            "gérondif vs present participle for simultaneous actions",
        ],
    },
}

BATCH_PROMPT = """You are generating training data for a language learning AI model. Generate {batch_size} DIVERSE training examples for {lang_name} at the {level} level.

The topic focus for this batch: {topic}

Each example must be a JSON object with these EXACT fields:
- "sentence": A {lang_name} sentence that a {level}-level English-speaking learner would write (include realistic errors for "Needs Improvement", or genuinely good sentences for "Excellent")
- "language": "{lang_code}"
- "level": "{level}"
- "status": "Excellent" or "Needs Improvement"
- "grammar_rule": The specific grammar rule tested (ALWAYS provided, even for Excellent)
- "explanation": WHY the sentence is correct or incorrect (detailed, in English)
- "correction": Corrected sentence in {lang_name} (null if Excellent)
- "b1_alternative": A simpler B1-level way to say the same thing (null if not applicable)
- "c1_alternative": A professional C1 interpreter-level version (null if not applicable or already C1)
- "tip": Extra tip about Anglicisms, register, or word precision (null if none)

Requirements:
- Mix of "Excellent" (~40%) and "Needs Improvement" (~60%) statuses
- Sentences should be realistic things an interpreter-in-training would write
- Include varied vocabulary: daily life, work, politics, culture, travel, interpreting scenarios
- For "Needs Improvement": the error must be SPECIFIC and the correction must fix ONLY that error
- For "Excellent": explain specifically WHAT makes it good at the {level} level
- Explanations must be in English; all {lang_name} text in {lang_name}
- Grammar rules should be precise and pedagogical (name the actual rule)
- B1 alternatives should be genuinely simpler; C1 alternatives should sound like a native professional
- Tips should focus on Anglicisms, false cognates, and register awareness

Output ONLY a JSON array of {batch_size} objects. No markdown, no commentary."""


def generate_batch(client, language, level, topic, batch_size=10):
    lang_name = "Spanish" if language == "es" else "French"

    prompt = BATCH_PROMPT.format(
        batch_size=batch_size,
        lang_name=lang_name,
        lang_code=language,
        level=level,
        topic=topic,
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        examples = json.loads(text)
        if isinstance(examples, list):
            return examples
    except json.JSONDecodeError:
        print(f"  [WARN] Failed to parse batch for {level}/{topic}", file=sys.stderr)

    return []


def generate_dataset(language, total_count, levels=None):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Set ANTHROPIC_API_KEY environment variable")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    if levels is None:
        levels = ["B1", "B2", "C1"]
    elif isinstance(levels, str):
        levels = [levels]

    topics = TOPICS.get(language, {})
    all_examples = []

    per_level = total_count // len(levels)
    batch_size = 10

    for level in levels:
        level_topics = topics.get(level, [])
        if not level_topics:
            print(f"  [SKIP] No topics for {language}/{level}")
            continue

        generated = 0
        topic_idx = 0

        print(f"\n  Generating {per_level} examples for {language.upper()} {level}...")

        while generated < per_level:
            topic = level_topics[topic_idx % len(level_topics)]
            remaining = min(batch_size, per_level - generated)

            print(f"    [{generated}/{per_level}] Topic: {topic[:50]}...")

            try:
                batch = generate_batch(client, language, level, topic, remaining)
                all_examples.extend(batch)
                generated += len(batch)
            except Exception as e:
                print(f"    [ERROR] {e}", file=sys.stderr)
                time.sleep(5)

            topic_idx += 1
            time.sleep(1)

    return all_examples


def convert_to_mlx_format(input_path, output_path, language):
    """Convert raw JSONL to MLX chat format for fine-tuning."""
    lang_name = "Spanish" if language == "es" else "French"

    system_msg = (
        f"You are a {lang_name} professor training interpreters. "
        f"Analyze the learner's sentence and provide structured feedback. "
        f"Always identify the grammar rule, explain why it is correct or incorrect, "
        f"and provide level-appropriate alternatives. "
        f"Keep explanations in English; {lang_name} examples in {lang_name}."
    )

    with open(input_path, "r") as f:
        examples = [json.loads(line) for line in f if line.strip()]

    random.shuffle(examples)

    split = int(len(examples) * 0.9)
    train = examples[:split]
    valid = examples[split:]

    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, data in [("train.jsonl", train), ("valid.jsonl", valid)]:
        with open(output_dir / name, "w") as f:
            for ex in data:
                level = ex.get("level", "B2")
                sentence = ex.get("sentence", "")

                response = {
                    "status": ex.get("status", "Excellent"),
                    "grammar_rule": ex.get("grammar_rule", ""),
                    "explanation": ex.get("explanation", ""),
                    "correction": ex.get("correction"),
                    "b1_alternative": ex.get("b1_alternative"),
                    "c1_alternative": ex.get("c1_alternative"),
                    "tip": ex.get("tip"),
                }

                chat = {
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {
                            "role": "user",
                            "content": f"The learner is at level {level}. Analyze this {lang_name} sentence: \"{sentence}\"",
                        },
                        {
                            "role": "assistant",
                            "content": json.dumps(response, ensure_ascii=False),
                        },
                    ]
                }
                f.write(json.dumps(chat, ensure_ascii=False) + "\n")

    print(f"  MLX dataset written to {output_dir}/")
    print(f"    train.jsonl: {len(train)} examples")
    print(f"    valid.jsonl: {len(valid)} examples")


def main():
    parser = argparse.ArgumentParser(description="Generate Parlance training data")
    parser.add_argument("--language", "-l", choices=["es", "fr"], default="es")
    parser.add_argument("--count", "-n", type=int, default=500)
    parser.add_argument("--level", choices=["B1", "B2", "C1"], default=None,
                        help="Generate for a specific level only (default: all)")
    parser.add_argument("--output", "-o", default=None,
                        help="Output file path (default: data_{language}.jsonl)")
    parser.add_argument("--format", choices=["raw", "mlx"], default="raw",
                        help="'raw' generates JSONL, 'mlx' converts existing raw JSONL to MLX chat format")
    parser.add_argument("--input", "-i", default=None,
                        help="Input file for --format mlx conversion")

    args = parser.parse_args()

    if args.format == "mlx":
        input_path = args.input
        if not input_path:
            input_path = f"data_{args.language}.jsonl"
            seed_path = f"seed_{args.language}.jsonl"
            if not Path(input_path).exists() and Path(seed_path).exists():
                input_path = seed_path

        if not Path(input_path).exists():
            print(f"Error: Input file {input_path} not found")
            sys.exit(1)

        output_dir = args.output or f"mlx_data_{args.language}"
        print(f"Converting {input_path} to MLX format...")
        convert_to_mlx_format(input_path, output_dir, args.language)
        return

    output_path = args.output or f"data_{args.language}.jsonl"
    lang_name = "Spanish" if args.language == "es" else "French"

    print(f"Generating {args.count} {lang_name} training examples...")
    print(f"  Language: {args.language}")
    print(f"  Level(s): {args.level or 'B1, B2, C1'}")
    print(f"  Output: {output_path}")

    examples = generate_dataset(args.language, args.count, args.level)

    with open(output_path, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"\nDone! Generated {len(examples)} examples -> {output_path}")
    print(f"\nNext steps:")
    print(f"  1. Review a sample: head -20 {output_path} | python -m json.tool")
    print(f"  2. Convert to MLX format: python generate_data.py --format mlx -l {args.language} -i {output_path}")
    print(f"  3. Fine-tune: mlx_lm.lora --model google/gemma-4-e2b --train --data mlx_data_{args.language}/")


if __name__ == "__main__":
    main()
