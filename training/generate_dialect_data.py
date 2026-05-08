#!/usr/bin/env python3
"""
Generate dialect-aware training data for per-language Parlance SLMs.

Creates examples that teach the model to:
1. Recognize valid dialect variations (not penalize correct regional forms)
2. Identify register differences across dialects
3. Handle interpreter-specific vocabulary by region

Spanish dialects: Mexican, Rioplatense (Argentina/Uruguay), Caribbean,
                  Castilian (Spain), Andean, Colombian
French dialects:  Metropolitan, Québécois, Belgian, Swiss, West African

Usage:
    export GROQ_API_KEY="your-key"
    python generate_dialect_data.py --lang es --count 500
    python generate_dialect_data.py --lang fr --count 500
    python generate_dialect_data.py --lang es --dialect mexican --count 200
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

# ── SPANISH DIALECT CONFIG ───────────────────────────────────────

ES_DIALECTS = {
    "mexican": {
        "name": "Mexican Spanish",
        "region": "Mexico",
        "key_features": [
            "Uses 'ustedes' for both formal and informal plural (no 'vosotros')",
            "Diminutives used heavily (-ito/-ita): 'ahorita', 'tantito', 'cerquita'",
            "Common expressions: 'órale', 'ándale', 'mande' (polite 'what?')",
            "'Güey/wey' in informal speech",
            "Leísmo is NOT standard (use 'lo/la' for direct objects)",
            "Preference for 'platicar' over 'hablar' in casual speech",
            "Nahuatl-origin vocabulary: chocolate, tomate, aguacate, guajolote",
            "'¿Qué onda?' as informal greeting",
        ],
        "register_notes": "Mexican formal register uses 'usted' extensively even with acquaintances. 'Mande' shows respect. Professional interpreters should avoid 'güey' and slang.",
        "topics": [
            "ordering at a taquería", "visiting a mercado", "family celebrations (quinceañera)",
            "medical visit (IMSS/clinic)", "school registration", "legal proceedings",
            "business meeting in Mexico City", "immigration paperwork",
        ],
    },
    "rioplatense": {
        "name": "Rioplatense Spanish",
        "region": "Argentina and Uruguay",
        "key_features": [
            "Uses 'vos' instead of 'tú' with unique conjugations: 'vos tenés', 'vos querés', 'vos sabés'",
            "Imperative with vos: 'vení', 'decí', 'sentate' (not 'ven', 'di', 'siéntate')",
            "'Vosotros' is NOT used — 'ustedes' for all plural",
            "Yeísmo rehilado: 'll' and 'y' pronounced as 'sh' [ʃ]",
            "'Che' as vocative/attention-getter",
            "Italian-influenced vocabulary: 'laburo' (work), 'pibe/piba' (kid), 'birra' (beer)",
            "'Re-' as intensifier: 're lindo', 're copado'",
            "Lunfardo slang in informal speech: 'afanar' (steal), 'mango' (peso)",
        ],
        "register_notes": "Voseo is standard across ALL registers in Argentina — even formal documents. 'Usted' marks high formality. Interpreters must know voseo conjugation patterns.",
        "topics": [
            "ordering in a parrilla", "discussing fútbol", "visiting the campo",
            "medical appointment", "university enrollment", "tango culture",
            "business meeting in Buenos Aires", "legal consultation",
        ],
    },
    "caribbean": {
        "name": "Caribbean Spanish",
        "region": "Dominican Republic, Cuba, Puerto Rico, coastal Venezuela/Colombia",
        "key_features": [
            "Aspiration or deletion of syllable-final /s/: 'esto' → 'ehto', 'los dos' → 'loh doh'",
            "Lambdacism: /r/ → /l/ in syllable-final position: 'comer' → 'comel'",
            "Subject pronoun usage more frequent than Castilian: 'Yo quiero que tú vayas'",
            "Inverted questions with subject before verb: '¿Qué tú quieres?' instead of '¿Qué quieres tú?'",
            "'Ustedes' for all plural (no 'vosotros')",
            "PR: English borrowings — 'parquear' (park), 'guagua' (bus in DR/Cuba)",
            "'Wepa' (PR), '¿Qué lo que?' (DR) as informal greetings",
        ],
        "register_notes": "Written Caribbean Spanish follows standard orthography despite pronunciation differences. Interpreters should understand spoken features but write standard forms. Subject pronoun placement varies by register.",
        "topics": [
            "visiting the playa", "ordering mofongo/tostones", "medical visit",
            "hurricane preparation", "family reunion", "legal proceedings",
            "government office visit", "school enrollment for newcomers",
        ],
    },
    "castilian": {
        "name": "Castilian Spanish",
        "region": "Spain (especially central/northern)",
        "key_features": [
            "'Vosotros' for informal plural with unique conjugations: 'vosotros tenéis', 'vosotros queréis'",
            "Distinction ('distinción'): 'z' and 'ce/ci' pronounced /θ/ (like English 'th')",
            "Leísmo accepted for masculine singular persons: 'Le vi' (I saw him)",
            "'Vale' as ubiquitous confirmation word",
            "'Coger' means 'to take/grab' (neutral — unlike Latin American usage)",
            "Use of 'pretérito perfecto' for recent past: 'He comido hoy' (I ate today)",
            "'Mola' (cool), 'tío/tía' (dude), 'currar' (work) in informal speech",
            "Vocabulary: 'ordenador' (computer), 'móvil' (phone), 'coche' (car)",
        ],
        "register_notes": "Spain uses 'vosotros' in informal contexts and 'ustedes' only for formal. The Real Academia Española (RAE) sets the standard. Interpreters working with Spanish nationals must know vosotros forms.",
        "topics": [
            "ordering tapas", "visiting a museo", "discussing Spanish politics",
            "medical appointment (sanidad pública)", "university life",
            "business meeting in Madrid/Barcelona", "legal proceedings in Spain",
            "bureaucratic procedures (Hacienda, Seguridad Social)",
        ],
    },
    "andean": {
        "name": "Andean Spanish",
        "region": "Peru, Bolivia, Ecuador, highland Colombia",
        "key_features": [
            "Strong distinction between /ll/ and /y/ (lleísmo)",
            "Quechua/Aymara substrate: 'pues' shortened to 'ps' or 'pe'",
            "Double possessives: 'su casa de Juan' (Juan's house)",
            "Diminutives: '-ito/-ita' used even more than Mexican Spanish",
            "Voseo limited to certain regions (Andean Ecuador)",
            "Vocabulary: 'choclo' (corn), 'papa' (potato), 'ají' (chili pepper)",
            "'Nomás' as discourse marker: 'Pase nomás' (come right in)",
            "Loísmo in some rural areas: using 'lo' for feminine direct objects",
        ],
        "register_notes": "Andean formal register is relatively conservative. Indigenous language influence is stronger in rural/informal contexts. Interpreters working with Andean communities should recognize Quechua-influenced syntax.",
        "topics": [
            "market shopping", "agricultural discussions", "medical visit in rural clinic",
            "community meeting", "traditional celebrations (Inti Raymi)",
            "school enrollment", "legal proceedings", "immigration consultation",
        ],
    },
    "colombian": {
        "name": "Colombian Spanish",
        "region": "Colombia (varies by region: Bogotá, Medellín, coast)",
        "key_features": [
            "Usted used broadly — even between close friends in Bogotá",
            "Voseo in Antioquia/Medellín: 'vos sabés', but 'tú' in Bogotá",
            "Clear, 'neutral' pronunciation often used in media/dubbing industry",
            "'Sumercé' (from 'su merced') in Boyacá as respectful address",
            "Vocabulary: 'chévere' (cool), 'bacano' (great), 'parcero/parce' (buddy)",
            "'A la orden' as polite response (at your service)",
            "'Pues' used extensively as filler/connector",
            "Costeño dialect (Caribbean coast) shares features with Caribbean Spanish",
        ],
        "register_notes": "Colombian Spanish from Bogotá is considered among the 'clearest' for learners. The widespread use of 'usted' even informally can confuse learners used to tú/usted distinction. Interpreters should note regional variation within Colombia.",
        "topics": [
            "coffee culture", "visiting a finca", "medical appointment",
            "university discussions", "business meeting in Bogotá",
            "legal proceedings", "cultural events (feria, carnaval)",
            "discussing violence/peace process (sensitive interpreting)",
        ],
    },
}

# ── FRENCH DIALECT CONFIG ────────────────────────────────────────

FR_DIALECTS = {
    "metropolitan": {
        "name": "Metropolitan French",
        "region": "France (standard/Parisian)",
        "key_features": [
            "Standard reference for grammar and vocabulary",
            "Liaison rules strictly followed in formal speech",
            "'On' frequently replaces 'nous' in spoken language",
            "Verlan (reversed syllables) in slang: 'meuf' (femme), 'relou' (lourd), 'ouf' (fou)",
            "Ne-dropping in spoken French: 'Je sais pas' instead of 'Je ne sais pas'",
            "'Bof', 'quoi', 'genre' as discourse markers",
            "Past tense: passé composé dominates speech; passé simple is literary only",
            "Vocabulary: 'portable' (phone), 'ordinateur' (computer), 'voiture' (car)",
        ],
        "register_notes": "Metropolitan French has the sharpest formal/informal divide. 'Tu' vs 'vous' is critical. Ne-dropping signals informality. Professional interpreters must maintain 'ne' in formal contexts.",
        "topics": [
            "ordering at a brasserie", "Parisian daily life", "discussing politics",
            "medical appointment", "university enrollment", "business meeting",
            "legal proceedings", "bureaucratic procedures (préfecture, CAF)",
        ],
    },
    "quebecois": {
        "name": "Québécois French",
        "region": "Quebec, Canada",
        "key_features": [
            "Affrication of /t/ and /d/ before /i/ and /y/: 'tu' → [tsy], 'dire' → [dzir]",
            "'Tu' used as question particle: 'Tu veux-tu?' (Do you want?)",
            "Sacres (religious swear words used as intensifiers): 'tabernacle', 'câlice', 'crisse'",
            "English borrowings: 'char' (car), 'job', 'fun', 'checker' (to check)",
            "'Icitte' for 'ici', 'pantoute' for 'pas du tout', 'pogner' for 'attraper'",
            "'Pis' for 'puis/et', 'ben' for 'bien', 'faque' for 'ça fait que' (so/therefore)",
            "Vocabulary: 'dépanneur' (corner store), 'blonde' (girlfriend), 'chum' (boyfriend/buddy)",
            "Office québécois de la langue française (OQLF) promotes French alternatives to anglicisms",
        ],
        "register_notes": "Formal Québécois is closer to Metropolitan standard. Informal speech diverges significantly. Interpreters must understand both but use standard forms in professional settings. Some terms (dépanneur, autoroute) are standard in Quebec contexts.",
        "topics": [
            "winter activities", "ordering poutine", "discussing Quebec politics",
            "medical visit (RAMQ system)", "school registration (CEGEP)",
            "business meeting in Montréal", "legal proceedings (Code civil du Québec)",
            "immigration to Quebec (CSQ, PEQ)",
        ],
    },
    "belgian": {
        "name": "Belgian French",
        "region": "Wallonia and Brussels, Belgium",
        "key_features": [
            "Numbers: 'septante' (70), 'nonante' (90) instead of 'soixante-dix', 'quatre-vingt-dix'",
            "'Huitante' NOT used (that's Swiss) — Belgium uses 'quatre-vingts' for 80",
            "Vocabulary: 'kot' (student room), 'drache' (heavy rain), 'brol' (mess/stuff)",
            "Germanic substrate influence in syntax and vocabulary near Flemish border",
            "'Savoir' used where Metropolitan French uses 'pouvoir': 'Tu sais me passer le sel?'",
            "'Une fois' as discourse marker (sometimes)",
            "Pronunciation: distinction between /ɛ̃/ (brin) and /œ̃/ (brun) maintained",
            "Less tendency to drop 'ne' in spoken language compared to Paris",
        ],
        "register_notes": "Belgian formal French follows Metropolitan standard closely. Septante/nonante are standard in ALL registers in Belgium. Interpreters should use these forms when working with Belgian speakers.",
        "topics": [
            "EU institutions (Brussels)", "Belgian chocolate/cuisine",
            "medical appointment (mutuelle)", "university life (UCLouvain, ULB)",
            "business meeting in Brussels", "legal proceedings (Belgian law)",
            "discussing linguistic tensions (French/Flemish)", "cultural events",
        ],
    },
    "swiss": {
        "name": "Swiss French",
        "region": "Romandie (western Switzerland)",
        "key_features": [
            "Numbers: 'septante' (70), 'huitante' (80), 'nonante' (90)",
            "'Natel' for mobile phone (brand name become generic)",
            "Vocabulary: 'souper' (dinner, not 'dîner'), 'déjeuner' (lunch), 'action' (sale/discount)",
            "'Cornet' for plastic bag (not 'sac plastique')",
            "'Panosse' for mop, 'linge' for towel",
            "More conservative pronunciation — final consonants sometimes pronounced",
            "German influence in some syntax and vocabulary near language border",
            "Federal terminology: 'canton', 'commune', 'Conseil fédéral'",
        ],
        "register_notes": "Swiss French formal register follows Metropolitan standard with regional number words. Huitante/septante/nonante are standard in ALL contexts. Swiss precision in language reflects cultural values.",
        "topics": [
            "banking and finance", "chocolate/watch industry", "skiing/mountain activities",
            "medical visit (assurance maladie)", "university (EPFL, UNIL)",
            "business meeting in Geneva/Lausanne", "UN/Red Cross (Geneva)",
            "cantonal government procedures",
        ],
    },
    "west_african": {
        "name": "West African French",
        "region": "Senegal, Côte d'Ivoire, Mali, Cameroon, DRC, etc.",
        "key_features": [
            "Largest growing French-speaking population globally",
            "Vocabulary: 'essencerie' (gas station), 'goudron' (paved road), 'cadeau' (gift/tip — broader use)",
            "'On dit quoi?' as informal greeting (What's up?)",
            "Nouchi (Ivorian slang): 'go' (girl), 'gaou' (fool), 'dja' (already)",
            "Wolof-influenced expressions in Senegal: 'inchallah' commonly used",
            "Verb tenses may differ: progressive aspect more commonly marked",
            "French often used as lingua franca between different ethnic groups",
            "'Tu' may be used more broadly across social contexts than in France",
            "Code-switching between French and local languages is natural",
        ],
        "register_notes": "West African formal French follows Metropolitan grammar closely but with regional vocabulary. Interpreters working with African communities must understand cultural context — 'tu' usage doesn't signal disrespect. Growing importance for international organizations.",
        "topics": [
            "market shopping", "family celebrations", "medical visit",
            "school enrollment", "community meeting", "legal proceedings",
            "immigration/asylum contexts", "NGO/humanitarian work",
            "business meeting (ECOWAS, UEMOA)", "cultural exchange",
        ],
    },
}

# ── GENERATION PROMPT ────────────────────────────────────────────

DIALECT_PROMPT = """You are generating training data for a language learning AI that understands dialect variation in {lang_name}.

Generate {batch_size} training examples focused on {dialect_name} ({dialect_region}).

KEY DIALECT FEATURES to incorporate:
{dialect_features}

REGISTER NOTES: {register_notes}

Topic context: {topic}
CEFR Level: {level}

For each example, create a sentence a {level} learner might write. The sentences should:
- Use dialect-specific vocabulary or structures when natural for the topic
- Mix correct (~40%) and incorrect (~60%) sentences
- For incorrect sentences: include errors typical of {level} learners, but NEVER flag valid dialect features as errors
- {error_instruction}

{level_guidance}

CRITICAL DIALECT RULES:
- NEVER mark a valid dialect feature as an error (e.g., "vos tenés" is CORRECT in Rioplatense)
- When a form differs from standard but is correct in this dialect, the explanation should acknowledge this
- Register tips should be dialect-aware (e.g., voseo in Argentina is used across all registers)
- The "register" field should note the dialect context when relevant

Return a JSON array of objects. Each object must have:
- "input_sentence": the sentence the learner wrote (in {lang_name})
- "cefr_level": "{level}"
- "language": "{lang_code}"
- "dialect": "{dialect_key}"
- "expected_output": object with:
  - "status": "Excellent" or "Needs Improvement"
  - "grammar_rule": specific rule in English
  - "explanation": why correct/incorrect, dialect-aware, in English
  - "correction": corrected sentence in {lang_name} (null if Excellent)
  - "register": register analysis noting dialect context
  - "next_level_alt": same idea at {next_level} level in {lang_name}
  - "target_level_alt": same idea at {target_level} level in {lang_name} (null if C1/C2)
  - "tip": dialect-aware register tip for interpreter training, in English

All example sentences MUST be in {lang_name}. Return ONLY the JSON array."""

LEVEL_GUIDANCE = {
    "A1": "Focus on: present tense, basic vocabulary, simple structures. Be encouraging. Errors: subject-verb agreement, gender, articles.",
    "A2": "Focus on: reflexive verbs, near future, basic descriptions. Gently introduce dialect awareness. Errors: reflexive pronouns, prepositions.",
    "B1": "Focus on: past tenses, subjunctive triggers, opinions. Note when dialect forms differ from textbook. Errors: tense selection, subjunctive.",
    "B2": "Focus on: subjunctive, conditionals, register. Explicitly discuss dialect variation. Errors: register mismatch, anglicisms, si clauses.",
    "C1": "Focus on: professional register, advanced grammar, interpreting vocabulary. Dialect mastery expected. Errors: false cognates, register shifts.",
    "C2": "Focus on: near-native precision, dialectal code-switching, stylistic nuance. Errors: unnatural collocations, subtle register mismatches.",
}

NEXT_LEVELS = {"A1": "A2", "A2": "B1", "B1": "B2", "B2": "C1", "C1": "C2", "C2": "native-polish"}
TARGET_LEVELS = {"A1": "B1", "A2": "B2", "B1": "C1", "B2": "C2", "C1": None, "C2": None}


# ── API BACKENDS ─────────────────────────────────────────────────

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


def deepseek_generate(api_key: str, model: str, prompt: str) -> str:
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }).encode()

    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
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


# ── GENERATION ───────────────────────────────────────────────────

def get_dialect_config(lang: str, dialect: str) -> dict:
    if lang == "es":
        return ES_DIALECTS.get(dialect, {})
    return FR_DIALECTS.get(dialect, {})


def get_all_dialects(lang: str) -> dict:
    return ES_DIALECTS if lang == "es" else FR_DIALECTS


def build_prompt(lang: str, dialect_key: str, dialect_cfg: dict, level: str, batch_size: int) -> str:
    lang_name = "Spanish" if lang == "es" else "French"
    topic = random.choice(dialect_cfg["topics"])
    features = "\n".join(f"  - {f}" for f in dialect_cfg["key_features"])

    error_types = {
        "es": {
            "A1": "ser/estar confusion, gender agreement, present tense conjugation",
            "A2": "reflexive pronouns, ir+a+infinitive, gustar structure",
            "B1": "preterite vs imperfect, subjunctive triggers, por vs para",
            "B2": "subjunctive in noun clauses, si clauses, anglicisms, register",
            "C1": "pluperfect subjunctive, verbal periphrasis, false cognates",
            "C2": "subtle register shifts, dialectal inconsistency, unnatural collocations",
        },
        "fr": {
            "A1": "être/avoir confusion, gender agreement, present tense conjugation",
            "A2": "reflexive pronouns, partitive articles, futur proche",
            "B1": "passé composé vs imparfait, auxiliary choice, subjunctive triggers",
            "B2": "subjunctive in noun clauses, si clauses, anglicisms, tu/vous register",
            "C1": "subjonctif imparfait, passé simple, false cognates, register mismatch",
            "C2": "subtle register shifts, literary tense misuse, unnatural collocations",
        },
    }

    error_instruction = f"Typical {level} errors: {error_types[lang][level]}"

    prompt = DIALECT_PROMPT.format(
        lang_name=lang_name,
        lang_code=lang,
        batch_size=batch_size,
        dialect_name=dialect_cfg["name"],
        dialect_region=dialect_cfg["region"],
        dialect_key=dialect_key,
        dialect_features=features,
        register_notes=dialect_cfg["register_notes"],
        topic=topic,
        level=level,
        error_instruction=error_instruction,
        level_guidance=LEVEL_GUIDANCE[level],
        next_level=NEXT_LEVELS[level],
        target_level=TARGET_LEVELS[level] or "N/A",
    )

    prompt += '\n\nWrap the array in a JSON object: {"examples": [...]}'
    return prompt


def to_training_format(example: dict) -> dict:
    lang_name = "Spanish" if example.get("language") == "es" else "French"
    level = example.get("cefr_level", "B1")
    dialect = example.get("dialect", "standard")

    system_msg = (
        f"You are a {lang_name} grammar coach for interpreter training, "
        f"with expertise in {dialect} dialect variation. "
        f"Analyze the learner's sentence at CEFR level {level}. "
        f"Respond with a JSON object containing: status, grammar_rule, explanation, "
        f"correction, register, next_level_alt, target_level_alt, and tip. "
        f"All example sentences must be in {lang_name}. "
        f"Never flag valid dialect features as errors. Always include a register tip."
    )

    user_msg = f'Analyze this {lang_name} sentence at {level} level: "{example["input_sentence"]}"'

    return {
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": json.dumps(example["expected_output"], ensure_ascii=False)},
        ]
    }


def generate_batch(backend_fn, api_key: str, model: str,
                   lang: str, dialect_key: str, dialect_cfg: dict,
                   level: str, batch_size: int = 8) -> list:
    prompt = build_prompt(lang, dialect_key, dialect_cfg, level, batch_size)
    raw = backend_fn(api_key, model, prompt)

    try:
        data = json.loads(raw.strip())
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "examples" in data:
            return data["examples"]
        return []
    except (json.JSONDecodeError, KeyError):
        print(f"  [warn] Failed to parse batch for {lang}/{dialect_key}/{level}")
        return []


def main():
    parser = argparse.ArgumentParser(description="Generate dialect-aware Parlance SLM training data")
    parser.add_argument("--backend", choices=["groq", "deepseek"], default="groq")
    parser.add_argument("--lang", choices=["es", "fr"], required=True)
    parser.add_argument("--dialect", default=None, help="Specific dialect (default: all)")
    parser.add_argument("--level", choices=LEVELS, default=None, help="Single level (default: all)")
    parser.add_argument("--count", type=int, default=500, help="Total examples to generate")
    parser.add_argument("--batch-size", type=int, default=8, help="Examples per API call")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between batches")
    args = parser.parse_args()

    if args.backend == "groq":
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("Set GROQ_API_KEY. Get one free at: https://console.groq.com/keys")
            sys.exit(1)
        backend_fn = groq_generate
        model = "qwen/qwen3-32b"
    else:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            print("Set DEEPSEEK_API_KEY. Get one free at: https://platform.deepseek.com/api_keys")
            sys.exit(1)
        backend_fn = deepseek_generate
        model = "deepseek-v4-flash"

    all_dialects = get_all_dialects(args.lang)
    if args.dialect:
        if args.dialect not in all_dialects:
            print(f"Unknown dialect '{args.dialect}'. Available: {', '.join(all_dialects.keys())}")
            sys.exit(1)
        dialects = {args.dialect: all_dialects[args.dialect]}
    else:
        dialects = all_dialects

    levels = [args.level] if args.level else LEVELS
    per_dialect_level = max(1, args.count // (len(dialects) * len(levels)))

    lang_name = "Spanish" if args.lang == "es" else "French"
    out_dir = Path("training/data/spanish" if args.lang == "es" else "training/data/french")
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"dialect_{timestamp}.jsonl"

    total = 0
    print(f"Backend: {args.backend} ({model})")
    print(f"Generating {args.count} dialect-aware examples for {lang_name}")
    print(f"Dialects: {', '.join(dialects.keys())}")
    print(f"Levels: {', '.join(levels)} ({per_dialect_level} per dialect×level)")
    print(f"Output: {out_file}\n")

    with open(out_file, "w", encoding="utf-8") as f:
        for dialect_key, dialect_cfg in dialects.items():
            print(f"\n─── {dialect_cfg['name']} ({dialect_cfg['region']}) ───")

            for level in levels:
                generated = 0
                batches_needed = (per_dialect_level + args.batch_size - 1) // args.batch_size
                print(f"  [{level}] {per_dialect_level} examples ({batches_needed} batches)...", end="", flush=True)

                for i in range(batches_needed):
                    remaining = per_dialect_level - generated
                    batch_sz = min(args.batch_size, remaining)
                    if batch_sz <= 0:
                        break

                    for attempt in range(4):
                        try:
                            examples = generate_batch(
                                backend_fn, api_key, model,
                                args.lang, dialect_key, dialect_cfg,
                                level, batch_sz
                            )
                            for ex in examples:
                                training_ex = to_training_format(ex)
                                f.write(json.dumps(training_ex, ensure_ascii=False) + "\n")
                                generated += 1
                                total += 1
                            f.flush()
                            break
                        except Exception as e:
                            wait = min(10 * (2 ** attempt) + random.uniform(0, 3), 60)
                            if attempt < 3:
                                time.sleep(wait)
                            else:
                                print(f" [error: {e}]", end="")

                    if i < batches_needed - 1:
                        time.sleep(args.delay)

                print(f" ✓ {generated}")

    print(f"\n{'='*50}")
    print(f"Total: {total} examples → {out_file}")
    if out_file.stat().st_size > 0:
        print(f"File size: {out_file.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
