#!/usr/bin/env python3
"""
Generate specialty training data for Parlance interpreter training SLM.
Covers: DELE/DELF exam prep, CCHI/NBCMI medical interpreting, legal interpreting.

Uses same output format as generate_data.py for unified fine-tuning.

Usage:
    export GROQ_API_KEY="your-key"
    python generate_specialty_data.py --category dele --lang es --count 200
    python generate_specialty_data.py --category delf --lang fr --count 200
    python generate_specialty_data.py --category medical --lang es --count 200
    python generate_specialty_data.py --category legal --lang es --count 200
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

# ── DELE EXAM PREP (Spanish) ────────────────────────────────────

DELE_CONFIG = {
    "A1": {
        "exam_tasks": [
            "DELE A1 Prueba 3 — write a short note to a friend about your weekend plans",
            "DELE A1 Prueba 1 — answer questions about a short text describing someone's daily routine",
            "DELE A1 Prueba 3 — fill out a registration form with personal information",
            "DELE A1 — write a postcard from vacation describing the weather and activities",
            "DELE A1 — respond to a short email invitation accepting or declining",
        ],
        "vocab_focus": "greetings, numbers, family, food, colors, daily routine, weather",
        "grammar_focus": "present tense regular verbs, ser/estar basics, articles, gender agreement",
    },
    "A2": {
        "exam_tasks": [
            "DELE A2 Prueba 3 — write a short letter describing your neighborhood",
            "DELE A2 — describe a recent shopping experience in a short paragraph",
            "DELE A2 Prueba 1 — answer comprehension questions about a short news story",
            "DELE A2 — write directions from your house to the nearest supermarket",
            "DELE A2 — describe your best friend's appearance and personality",
        ],
        "vocab_focus": "shopping, directions, descriptions, feelings, past events, comparisons",
        "grammar_focus": "preterite basic forms, reflexive verbs, ir+a+infinitive, gustar, comparatives",
    },
    "B1": {
        "exam_tasks": [
            "DELE B1 Prueba 3 Tarea 1 — write a formal email to a hotel requesting information",
            "DELE B1 Prueba 3 Tarea 2 — write a blog post about a cultural event you attended",
            "DELE B1 — narrate a memorable travel experience using past tenses",
            "DELE B1 — write a letter of complaint about a product or service",
            "DELE B1 — express your opinion about social media's impact on youth",
        ],
        "vocab_focus": "travel, culture, opinions, complaints, formal correspondence",
        "grammar_focus": "preterite vs imperfect, present subjunctive basics, por vs para, formal register",
    },
    "B2": {
        "exam_tasks": [
            "DELE B2 Prueba 3 Tarea 1 — write a formal letter to a newspaper editor about an environmental issue",
            "DELE B2 Prueba 3 Tarea 2 — write an argumentative essay on work-life balance",
            "DELE B2 — analyze a graph about employment trends and write a report",
            "DELE B2 — write a review of a cultural event distinguishing fact from opinion",
            "DELE B2 — compose a cover letter for a professional internship in a Spanish-speaking country",
        ],
        "vocab_focus": "professional vocabulary, academic language, idiomatic expressions, media terminology",
        "grammar_focus": "subjunctive in all contexts, conditional structures, passive voice, formal register consistency",
    },
    "C1": {
        "exam_tasks": [
            "DELE C1 Prueba 3 Tarea 1 — summarize and critically analyze two contrasting texts about immigration policy",
            "DELE C1 Prueba 3 Tarea 2 — write a formal report based on audio data about healthcare reform",
            "DELE C1 — write an academic essay discussing the role of technology in education",
            "DELE C1 — compose a professional proposal for a cultural exchange program",
            "DELE C1 — analyze rhetorical strategies in a political speech excerpt",
        ],
        "vocab_focus": "academic discourse, political language, healthcare terminology, rhetorical devices",
        "grammar_focus": "advanced subjunctive (pluperfect), verbal periphrasis, discourse connectors, register shifts",
    },
    "C2": {
        "exam_tasks": [
            "DELE C2 Prueba 3 — write a critical essay integrating information from a lecture and a written text about linguistic diversity",
            "DELE C2 — compose a scholarly analysis of a literary excerpt discussing narrative techniques",
            "DELE C2 — write a diplomatic brief summarizing positions on international trade policy",
            "DELE C2 — produce a professional translation of a legal document excerpt maintaining register",
            "DELE C2 — write a nuanced opinion piece on the ethics of AI in interpreting",
        ],
        "vocab_focus": "literary criticism, diplomatic language, legal terminology, academic register, dialectal awareness",
        "grammar_focus": "near-native precision, stylistic variation, archaic forms where appropriate, discourse-level cohesion",
    },
}

# ── DELF/DALF EXAM PREP (French) ────────────────────────────────

DELF_CONFIG = {
    "A1": {
        "exam_tasks": [
            "DELF A1 Production écrite — write a short message to a friend about your weekend",
            "DELF A1 — fill out a registration form for a French language course",
            "DELF A1 — write a postcard describing your vacation",
            "DELF A1 — respond to an email invitation to a birthday party",
            "DELF A1 — describe your daily routine in 5-6 sentences",
        ],
        "vocab_focus": "greetings, family, food, daily routine, weather, hobbies",
        "grammar_focus": "present tense, être/avoir, articles, gender agreement, negation",
    },
    "A2": {
        "exam_tasks": [
            "DELF A2 Production écrite — write a short letter describing an event you attended",
            "DELF A2 — write about your neighborhood and what you can do there",
            "DELF A2 — describe a memorable meal at a restaurant",
            "DELF A2 — write a message explaining why you can't attend a meeting",
            "DELF A2 — compare life in the city vs countryside in a short paragraph",
        ],
        "vocab_focus": "events, neighborhood, food, excuses, comparisons, past experiences",
        "grammar_focus": "passé composé basics, reflexive verbs, futur proche, partitive articles",
    },
    "B1": {
        "exam_tasks": [
            "DELF B1 Production écrite — write a formal email to your employer requesting a schedule change",
            "DELF B1 — write a blog post expressing your opinion on a social issue",
            "DELF B1 — narrate an unexpected event that happened during a trip",
            "DELF B1 — write a letter of complaint to a company about poor service",
            "DELF B1 — express your point of view on the importance of learning languages",
        ],
        "vocab_focus": "workplace, opinions, travel, complaints, education, social issues",
        "grammar_focus": "passé composé vs imparfait, subjunctive basics, conditional, formal vs informal",
    },
    "B2": {
        "exam_tasks": [
            "DELF B2 Production écrite — write an argumentative essay on the role of social media in democracy",
            "DELF B2 — write a formal letter to a local official proposing an environmental initiative",
            "DELF B2 — analyze a news article and present your critical perspective",
            "DELF B2 — write a cover letter for a position at an international organization",
            "DELF B2 — compose a report summarizing the results of a survey on work-life balance",
        ],
        "vocab_focus": "media, politics, environment, professional correspondence, academic argumentation",
        "grammar_focus": "subjunctive in complex clauses, passive voice, conditional past, formal register",
    },
    "C1": {
        "exam_tasks": [
            "DALF C1 Production écrite — synthesize two texts on cultural identity and globalization into a structured essay",
            "DALF C1 — write a critical analysis of a policy proposal on healthcare reform",
            "DALF C1 — compose an academic summary of a conference presentation on linguistics",
            "DALF C1 — write a professional report evaluating the effectiveness of a public program",
            "DALF C1 — analyze the rhetorical strategies in a French political debate excerpt",
        ],
        "vocab_focus": "academic synthesis, political analysis, healthcare, rhetoric, professional reporting",
        "grammar_focus": "advanced subjunctive, nominalization, discourse connectors, register consistency",
    },
    "C2": {
        "exam_tasks": [
            "DALF C2 Production écrite — write a structured argumentative essay based on a dossier of documents about digital ethics",
            "DALF C2 — compose a scholarly review of a literary work analyzing narrative voice and style",
            "DALF C2 — write a diplomatic summary reconciling conflicting positions on international law",
            "DALF C2 — produce a professional translation maintaining register and cultural nuance",
            "DALF C2 — write a critical essay on the evolution of the French language in a globalized world",
        ],
        "vocab_focus": "literary analysis, legal/diplomatic language, academic prose, cultural criticism",
        "grammar_focus": "near-native mastery, stylistic elegance, literary tenses, discourse-level precision",
    },
}

# ── CCHI/NBCMI MEDICAL INTERPRETING ─────────────────────────────

MEDICAL_CONFIG = {
    "scenarios": {
        "es": [
            "interpret a doctor explaining a diabetes diagnosis to a patient",
            "sight-translate a hospital discharge summary",
            "interpret a nurse explaining medication dosage and side effects",
            "convey informed consent for a surgical procedure",
            "interpret a mental health intake interview",
            "explain an insurance authorization process to a patient",
            "interpret between a pediatrician and a parent about vaccinations",
            "convey lab results and their implications to a patient",
            "interpret an emergency room triage assessment",
            "translate a patient's description of symptoms to medical terminology",
            "interpret a physical therapy session with exercise instructions",
            "convey a prenatal care appointment discussion",
            "interpret an oncology consultation about treatment options",
            "explain a radiology report to a patient in accessible language",
            "interpret a cardiology follow-up discussing medication changes",
        ],
        "fr": [
            "interpret a doctor explaining a diabetes diagnosis to a patient",
            "sight-translate a hospital discharge summary",
            "interpret a nurse explaining medication dosage and side effects",
            "convey informed consent for a surgical procedure",
            "interpret a mental health intake interview",
            "explain an insurance authorization process to a patient",
            "interpret between a pediatrician and a parent about vaccinations",
            "convey lab results and their implications to a patient",
            "interpret an emergency room triage assessment",
            "translate a patient's description of symptoms to medical terminology",
            "interpret a physical therapy session with exercise instructions",
            "convey a prenatal care appointment discussion",
            "interpret an oncology consultation about treatment options",
            "explain a radiology report to a patient in accessible language",
            "interpret a cardiology follow-up discussing medication changes",
        ],
    },
    "terminology_areas": [
        "anatomy and body systems", "common diseases and conditions",
        "medications and pharmacology", "surgical procedures",
        "mental health terminology", "obstetrics and gynecology",
        "pediatric care", "emergency medicine", "oncology",
        "cardiology", "endocrinology", "radiology and imaging",
    ],
    "ethics_scenarios": [
        "patient requests interpreter to not translate something to the doctor",
        "interpreter notices signs of domestic abuse during appointment",
        "doctor uses medical jargon the patient clearly doesn't understand",
        "patient asks interpreter for personal medical advice",
        "interpreter has a conflict of interest (knows the patient personally)",
        "patient's family member tries to interpret instead",
        "culturally sensitive information that may affect treatment",
        "interpreter must maintain neutrality during emotional disclosure",
    ],
}

# ── LEGAL INTERPRETING ──────────────────────────────────────────

LEGAL_CONFIG = {
    "scenarios": {
        "es": [
            "interpret during an arraignment hearing",
            "sight-translate a police report for a defendant",
            "interpret a lawyer-client privileged conversation about plea options",
            "convey Miranda rights accurately during an arrest",
            "interpret witness testimony in a civil lawsuit",
            "translate a restraining order for a petitioner",
            "interpret during a family court custody hearing",
            "convey a judge's sentencing statement to the defendant",
            "interpret a deposition about a workplace injury",
            "sight-translate an immigration form (I-589 asylum application)",
            "interpret during a bail hearing",
            "convey a jury instruction to a non-English-speaking juror alternate",
            "interpret a probation officer's meeting with a parolee",
            "translate a lease agreement dispute in small claims court",
            "interpret an immigration interview at USCIS",
        ],
        "fr": [
            "interpret during an arraignment hearing",
            "sight-translate a police report for a defendant",
            "interpret a lawyer-client privileged conversation about plea options",
            "convey Miranda-equivalent rights during an arrest",
            "interpret witness testimony in a civil lawsuit",
            "translate a restraining order for a petitioner",
            "interpret during a family court custody hearing",
            "convey a judge's sentencing statement to the defendant",
            "interpret a deposition about a workplace injury",
            "sight-translate an immigration asylum application",
            "interpret during a bail hearing",
            "convey a jury instruction",
            "interpret a probation officer's meeting with a parolee",
            "translate a lease agreement dispute in small claims court",
            "interpret an immigration interview",
        ],
    },
    "terminology_areas": [
        "criminal law procedures", "civil litigation terms",
        "family law and custody", "immigration law",
        "constitutional rights", "court roles and procedures",
        "evidence and objections", "sentencing and penalties",
        "contracts and agreements", "real estate and property law",
    ],
}

LANG_NAMES = {"es": "Spanish", "fr": "French"}

# ── PROMPTS ─────────────────────────────────────────────────────

EXAM_PROMPT = """You are generating training data for an interpreter training AI. Generate {batch_size} DIVERSE examples for {lang_name} at CEFR level {level}.

CONTEXT: {exam_task}

The learner is preparing for the {exam_name} exam and training to become a professional interpreter.

Create realistic sentences a {level} learner might write for this exam task.
Vocabulary focus: {vocab_focus}
Grammar focus: {grammar_focus}

Mix of correct (~40%) and incorrect (~60%) sentences with realistic {level}-level errors.

Return a JSON array of objects with exactly these fields:
- "input_sentence": the sentence (in {lang_name})
- "cefr_level": "{level}"
- "language": "{lang_code}"
- "expected_output": object with:
  - "status": "Excellent" or "Needs Improvement"
  - "grammar_rule": specific rule in English
  - "explanation": specific, actionable feedback in English — reference {exam_name} exam expectations
  - "correction": corrected sentence in {lang_name} (null if Excellent)
  - "next_level_alt": same idea at a higher level in {lang_name}
  - "target_level_alt": null
  - "tip": {exam_name}-specific tip about register, exam strategy, or common pitfalls — in English

CRITICAL: All sentences must be in {lang_name}. Tips should reference {exam_name} exam format and scoring. Return ONLY the JSON array."""

MEDICAL_PROMPT = """You are generating training data for a medical interpreter training AI. Generate {batch_size} DIVERSE examples for {lang_name}.

CONTEXT: {scenario}
TERMINOLOGY AREA: {term_area}

The learner is preparing for CCHI/NBCMI medical interpreter certification.

Create realistic sentences that would appear in this medical interpreting context. Include:
- Medical terminology that must be interpreted precisely
- Patient-facing language that needs to be clear and accessible
- Formal medical register alongside patient-friendly explanations

Mix of correct (~35%) and incorrect (~65%) sentences with errors like: wrong medical term, register mismatch, false cognate, imprecise translation of medical concept, missing formality.

Return a JSON array of objects with exactly these fields:
- "input_sentence": the sentence (in {lang_name})
- "cefr_level": "C1"
- "language": "{lang_code}"
- "expected_output": object with:
  - "status": "Excellent" or "Needs Improvement"
  - "grammar_rule": specific medical terminology or interpreting rule in English
  - "explanation": feedback referencing CCHI/NBCMI standards, medical accuracy, and interpreter ethics — in English
  - "correction": corrected sentence in {lang_name} (null if Excellent)
  - "next_level_alt": a more precise/professional version in {lang_name}
  - "target_level_alt": null
  - "tip": medical interpreting tip about terminology precision, ethics, or CCHI/NBCMI exam expectations — in English

CRITICAL: All sentences must be in {lang_name}. Tips should reference medical interpreter certification standards. Return ONLY the JSON array."""

LEGAL_PROMPT = """You are generating training data for a legal interpreter training AI. Generate {batch_size} DIVERSE examples for {lang_name}.

CONTEXT: {scenario}
TERMINOLOGY AREA: {term_area}

The learner is training for legal/court interpreting certification.

Create realistic sentences from this legal interpreting context. Include:
- Court and legal terminology that must be interpreted with absolute precision
- Formal legal register (legalese) alongside accessible explanations
- Sentences where register shifts or imprecise terminology could have serious consequences

Mix of correct (~35%) and incorrect (~65%) sentences with errors like: wrong legal term, register mismatch, imprecise translation of legal concept, calque from English, informal register in formal legal context.

Return a JSON array of objects with exactly these fields:
- "input_sentence": the sentence (in {lang_name})
- "cefr_level": "C1"
- "language": "{lang_code}"
- "expected_output": object with:
  - "status": "Excellent" or "Needs Improvement"
  - "grammar_rule": specific legal terminology or interpreting rule in English
  - "explanation": feedback about legal precision, register, and interpreting standards — in English
  - "correction": corrected sentence in {lang_name} (null if Excellent)
  - "next_level_alt": a more precise/formal legal version in {lang_name}
  - "target_level_alt": null
  - "tip": legal interpreting tip about terminology, court protocol, or professional standards — in English

CRITICAL: All sentences must be in {lang_name}. Legal terminology must be accurate for the target legal system. Return ONLY the JSON array."""

ETHICS_PROMPT = """You are generating training data for an interpreter ethics training AI. Generate {batch_size} DIVERSE examples for {lang_name}.

SCENARIO: {scenario}

The learner is preparing for CCHI/NBCMI certification and needs to understand interpreter ethics (NCIHC Standards of Practice, IMIA Code of Ethics).

For each example, create a realistic statement or question an interpreter might encounter in this ethical scenario, and provide guidance on the correct ethical response.

Return a JSON array of objects with exactly these fields:
- "input_sentence": what the interpreter says/does in {lang_name} (may include an ethical misstep or correct response)
- "cefr_level": "C1"
- "language": "{lang_code}"
- "expected_output": object with:
  - "status": "Excellent" or "Needs Improvement"
  - "grammar_rule": the relevant ethical principle (e.g., "Impartiality", "Confidentiality", "Role boundaries", "Accuracy")
  - "explanation": detailed explanation of the ethical principle and why this response is correct/incorrect — reference NCIHC or IMIA standards — in English
  - "correction": what the interpreter should say/do instead in {lang_name} (null if Excellent)
  - "next_level_alt": null
  - "target_level_alt": null
  - "tip": practical ethics tip for interpreter certification exams — in English

CRITICAL: All interpreter speech must be in {lang_name}. Ethics explanations in English. Return ONLY the JSON array."""


def groq_generate(api_key: str, model: str, prompt: str) -> str:
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


def parse_response(raw: str) -> list:
    try:
        data = json.loads(raw.strip())
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ["examples", "data", "items", "results"]:
                if key in data and isinstance(data[key], list):
                    return data[key]
        return []
    except (json.JSONDecodeError, KeyError):
        return []


def to_training_format(example: dict, category: str) -> dict:
    lang_code = example.get("language", "es")
    lang_name = LANG_NAMES.get(lang_code, "Spanish")
    level = example.get("cefr_level", "C1")

    category_desc = {
        "dele": f"DELE {level} exam preparation coach",
        "delf": f"DELF/DALF {level} exam preparation coach",
        "medical": "medical interpreter training coach (CCHI/NBCMI)",
        "legal": "legal/court interpreter training coach",
        "ethics": "interpreter ethics coach (NCIHC/IMIA standards)",
    }

    system_msg = (
        f"You are a {lang_name} {category_desc.get(category, 'interpreter training coach')}. "
        f"Analyze the learner's sentence at CEFR level {level}. "
        f"Respond with a JSON object containing: status, grammar_rule, explanation, "
        f"correction, next_level_alt, target_level_alt, and tip. "
        f"All example sentences must be in {lang_name}. Always include a professional tip."
    )

    user_msg = f'Analyze this {lang_name} sentence at {level} level: "{example["input_sentence"]}"'

    return {
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": json.dumps(example["expected_output"], ensure_ascii=False)},
        ]
    }


def generate_batch(api_key, model, prompt, batch_size):
    prompt += f'\n\nWrap the array in a JSON object: {{"examples": [...]}}'
    raw = groq_generate(api_key, model, prompt)
    return parse_response(raw)


def run_exam_generation(api_key, model, lang, exam_name, config, count, batch_size, delay, out_file):
    levels = LEVELS
    per_level = count // len(levels)
    total = 0

    print(f"\n{'='*50}", flush=True)
    print(f"{exam_name} Exam Prep — {LANG_NAMES[lang]}", flush=True)
    print(f"Generating {count} examples ({per_level} per level)", flush=True)
    print(f"{'='*50}\n", flush=True)

    with open(out_file, "a", encoding="utf-8") as f:
        for level in levels:
            cfg = config[level]
            generated = 0
            batches_needed = (per_level + batch_size - 1) // batch_size
            print(f"  [{level}] {batches_needed} batches...", flush=True)

            for i in range(batches_needed):
                remaining = per_level - generated
                bs = min(batch_size, remaining)
                if bs <= 0:
                    break

                task = random.choice(cfg["exam_tasks"])
                prompt = EXAM_PROMPT.format(
                    batch_size=bs, lang_name=LANG_NAMES[lang], lang_code=lang,
                    level=level, exam_name=exam_name, exam_task=task,
                    vocab_focus=cfg["vocab_focus"], grammar_focus=cfg["grammar_focus"],
                )

                for attempt in range(5):
                    try:
                        examples = generate_batch(api_key, model, prompt, bs)
                        for ex in examples:
                            ex.setdefault("language", lang)
                            ex.setdefault("cefr_level", level)
                            f.write(json.dumps(to_training_format(ex, exam_name.lower().split("/")[0].split(" ")[0]), ensure_ascii=False) + "\n")
                            generated += 1
                            total += 1
                        f.flush()
                        break
                    except Exception as e:
                        wait = min(15 * (2 ** attempt) + random.uniform(0, 5), 120)
                        print(f"  [error] {e}", flush=True)
                        if attempt < 4:
                            time.sleep(wait)

                if i < batches_needed - 1:
                    time.sleep(delay)

            print(f"  [{level}] done: {generated}", flush=True)

    print(f"\n{exam_name}: {total} examples written", flush=True)
    return total


def run_specialty_generation(api_key, model, lang, category, prompt_template, scenarios, term_areas, count, batch_size, delay, out_file):
    total = 0
    batches_needed = (count + batch_size - 1) // batch_size
    generated = 0

    print(f"\n{'='*50}", flush=True)
    print(f"{category.upper()} Interpreting — {LANG_NAMES[lang]}", flush=True)
    print(f"Generating {count} examples", flush=True)
    print(f"{'='*50}\n", flush=True)

    with open(out_file, "a", encoding="utf-8") as f:
        for i in range(batches_needed):
            remaining = count - generated
            bs = min(batch_size, remaining)
            if bs <= 0:
                break

            scenario = random.choice(scenarios)
            term_area = random.choice(term_areas)
            prompt = prompt_template.format(
                batch_size=bs, lang_name=LANG_NAMES[lang], lang_code=lang,
                scenario=scenario, term_area=term_area,
            )

            for attempt in range(5):
                try:
                    examples = generate_batch(api_key, model, prompt, bs)
                    for ex in examples:
                        ex.setdefault("language", lang)
                        ex.setdefault("cefr_level", "C1")
                        f.write(json.dumps(to_training_format(ex, category), ensure_ascii=False) + "\n")
                        generated += 1
                        total += 1
                    f.flush()
                    break
                except Exception as e:
                    wait = min(15 * (2 ** attempt) + random.uniform(0, 5), 120)
                    print(f"  [error] {e}", flush=True)
                    if attempt < 4:
                        time.sleep(wait)

            if i < batches_needed - 1:
                time.sleep(delay)

            if (i + 1) % 5 == 0:
                print(f"    ... {generated}/{count}", flush=True)

    print(f"\n{category}: {total} examples written", flush=True)
    return total


def run_ethics_generation(api_key, model, lang, count, batch_size, delay, out_file):
    total = 0
    batches_needed = (count + batch_size - 1) // batch_size
    generated = 0

    print(f"\n{'='*50}", flush=True)
    print(f"ETHICS (CCHI/NBCMI) — {LANG_NAMES[lang]}", flush=True)
    print(f"Generating {count} examples", flush=True)
    print(f"{'='*50}\n", flush=True)

    with open(out_file, "a", encoding="utf-8") as f:
        for i in range(batches_needed):
            remaining = count - generated
            bs = min(batch_size, remaining)
            if bs <= 0:
                break

            scenario = random.choice(MEDICAL_CONFIG["ethics_scenarios"])
            prompt = ETHICS_PROMPT.format(
                batch_size=bs, lang_name=LANG_NAMES[lang], lang_code=lang,
                scenario=scenario,
            )

            for attempt in range(5):
                try:
                    examples = generate_batch(api_key, model, prompt, bs)
                    for ex in examples:
                        ex.setdefault("language", lang)
                        ex.setdefault("cefr_level", "C1")
                        f.write(json.dumps(to_training_format(ex, "ethics"), ensure_ascii=False) + "\n")
                        generated += 1
                        total += 1
                    f.flush()
                    break
                except Exception as e:
                    wait = min(15 * (2 ** attempt) + random.uniform(0, 5), 120)
                    print(f"  [error] {e}", flush=True)
                    if attempt < 4:
                        time.sleep(wait)

            if i < batches_needed - 1:
                time.sleep(delay)

            if (i + 1) % 5 == 0:
                print(f"    ... {generated}/{count}", flush=True)

    print(f"\nethics: {total} examples written", flush=True)
    return total


def main():
    parser = argparse.ArgumentParser(description="Generate specialty interpreter training data")
    parser.add_argument("--category", choices=["dele", "delf", "medical", "legal", "ethics", "all"], required=True)
    parser.add_argument("--lang", choices=["es", "fr"], required=True)
    parser.add_argument("--count", type=int, default=200, help="Examples per category")
    parser.add_argument("--batch-size", type=int, default=8, help="Examples per API call")
    parser.add_argument("--delay", type=float, default=4.0, help="Seconds between batches")
    parser.add_argument("--output-dir", default="training/data", help="Output directory")
    args = parser.parse_args()

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Set GROQ_API_KEY environment variable.")
        sys.exit(1)

    model = "meta-llama/llama-4-scout-17b-16e-instruct"

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"specialty_{args.lang}_{timestamp}.jsonl"

    grand_total = 0
    categories = ["dele", "delf", "medical", "legal", "ethics"] if args.category == "all" else [args.category]

    for cat in categories:
        if cat == "dele" and args.lang == "es":
            grand_total += run_exam_generation(api_key, model, "es", "DELE", DELE_CONFIG, args.count, args.batch_size, args.delay, out_file)
        elif cat == "delf" and args.lang == "fr":
            grand_total += run_exam_generation(api_key, model, "fr", "DELF/DALF", DELF_CONFIG, args.count, args.batch_size, args.delay, out_file)
        elif cat == "dele" and args.lang == "fr":
            print("DELE is Spanish-only. Use --category delf for French.", flush=True)
        elif cat == "delf" and args.lang == "es":
            print("DELF/DALF is French-only. Use --category dele for Spanish.", flush=True)
        elif cat == "medical":
            grand_total += run_specialty_generation(
                api_key, model, args.lang, "medical", MEDICAL_PROMPT,
                MEDICAL_CONFIG["scenarios"][args.lang], MEDICAL_CONFIG["terminology_areas"],
                args.count, args.batch_size, args.delay, out_file,
            )
        elif cat == "legal":
            grand_total += run_specialty_generation(
                api_key, model, args.lang, "legal", LEGAL_PROMPT,
                LEGAL_CONFIG["scenarios"][args.lang], LEGAL_CONFIG["terminology_areas"],
                args.count, args.batch_size, args.delay, out_file,
            )
        elif cat == "ethics":
            grand_total += run_ethics_generation(api_key, model, args.lang, args.count, args.batch_size, args.delay, out_file)

    print(f"\n{'='*50}", flush=True)
    print(f"GRAND TOTAL: {grand_total} examples → {out_file}", flush=True)
    if out_file.exists():
        print(f"File size: {out_file.stat().st_size / 1024:.1f} KB", flush=True)


if __name__ == "__main__":
    main()
