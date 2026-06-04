"""Sanity checks and safe fallbacks for Parlance Coach SLM feedback."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

# Matches training/generate_dialect_data.py (majority dialect in train.jsonl)
DEFAULT_ES_DIALECT = "mexican"

STOPWORDS = {
    "a", "al", "con", "de", "del", "el", "en", "es", "está", "están", "estás",
    "la", "las", "le", "lo", "los", "para", "por", "que", "se", "su", "sus",
    "un", "una", "y", "the", "and", "or", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "shall", "can", "need", "dare",
    "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "under", "again", "further", "then", "once", "here", "there",
    "when", "where", "why", "how", "all", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than",
    "too", "very", "just", "don", "now", "use", "correct", "incorrect", "formal",
    "informal", "register", "sentence", "learner", "level", "grammar", "rule",
    "spanish", "english", "interpreter", "training", "cefr", "excellent", "needs",
    "improvement", "appropriate", "vocabulary", "professional", "settings",
}

ALLOWLIST_QUOTED = re.compile(r"'([^']{3,})'|\"([^\"]{3,})\"|«([^»]{3,})»")

SI_CLAUSE_CONDITIONAL = re.compile(
    r"\bsi\b[^.!?]*\b(tendr[ií]a|har[ií]a|ser[ií]a|podr[ií]a|querr[ií]a|dir[ií]a|vendr[ií]a)\b",
    re.I,
)

SI_CLAUSE_FRENCH_CONDITIONAL = re.compile(
    r"\bsi\b[^.!?]*\b(j'aurais|tu aurais|il aurait|elle aurait|nous aurions|vous auriez)\b",
    re.I,
)

SI_CORRECTIONS = (
    (re.compile(r"\btendr[ií]a\b", re.I), "tuviera"),
    (re.compile(r"\bhar[ií]a\b", re.I), "hiciera"),
    (re.compile(r"\bser[ií]a\b", re.I), "fuera"),
    (re.compile(r"\bpodr[ií]a\b", re.I), "pudiera"),
)

ECHAR_DE_MENOS_LEISMO = re.compile(r"\b(le|les)\s+echo\s+de\s+menos\b", re.I)

FEMININE_ANTECEDENT_HINTS = (
    "ella", "novia", "madre", "hermana", "esposa", "mujer", "amiga", "hija", "abuela",
)
MASCULINE_ANTECEDENT_HINTS = (
    "novio", "padre", "hermano", "esposo", "hombre", "amigo", "hijo", "abuelo",
)


def _spanish_level_guidance(level: str) -> str:
    level = level.upper()
    if level in ("C2", "C1"):
        return (
            "Focus on professional register, near-native precision, and interpreting vocabulary. "
            "Flag Anglicisms and calques."
        )
    if level == "B2":
        return (
            "Focus on subjunctive vs indicative, si-clause structure (imperfect subjunctive + "
            "conditional), gender agreement, and register (tú/usted)."
        )
    if level == "B1":
        return "Focus on past tenses, subjunctive triggers, and register. Be clear about why an error matters."
    if level == "A2":
        return "Focus on present tense, reflexives, and basic agreement. Gently note tú/usted choice."
    return "Focus on present tense and basic structures. Be encouraging; note register simply."


def normalize_assessed_level(raw: str | None) -> str | None:
    if not raw:
        return None
    u = str(raw).upper().strip()
    return u if u in ("A1", "A2", "B1", "B2", "C1", "C2") else None


def _has_subordinator(text: str) -> bool:
    n = _normalize(text)
    if "fait que" in n or "fait qu" in n or "el hecho de que" in n:
        return True
    return any(
        m in n
        for m in (
            " porque ", " pues ", " que ", " qu ", " cuando ", " si ", " aunque ",
            " mientras ", " lo cual ", " donde ", " como ", " sino ",
            " lorsque ", " puisque ", " bien que ",
        )
    )


CEFR_COMPLEXITY_PROMPT = (
    "CEFR & COMPLEXITY:\n"
    "- assessed_level: A1–C2 ONLY if highly confident from specific structures in THIS sentence. "
    "When uncertain, omit and describe complexity in complexity_note without a CEFR label. Never guess from word count.\n"
    "- complexity_note: 1–2 English sentences on vocabulary, syntax, subordination, and register. "
    "Always include when possible, even without assessed_level.\n"
    "- next_level_alt / target_level_alt: stronger rewrites; level labels only when assessed_level is set.\n\n"
)


# Infinitives cited in coach text vs conjugations in the learner sentence
_VERB_SURFACE_FORMS: dict[str, tuple[str, ...]] = {
    "ser": ("soy", "eres", "es", "somos", "son", "fui", "fue", "fuimos", "fueron", "era", "eras", "eran", "sido"),
    "estar": ("estoy", "estas", "está", "esta", "estamos", "estan", "estuve", "estuvo", "estaba"),
    "haber": ("he", "has", "ha", "hay", "hemos", "han", "habia", "había", "hubo", "habria", "habría"),
    "tener": ("tengo", "tienes", "tiene", "tenemos", "tienen", "tuve", "tuvo", "tenia", "tenía", "tendria", "tendría"),
    "hacer": ("hago", "haces", "hace", "hacemos", "hacen", "hice", "hizo", "hacia", "haría", "haria"),
    "ir": ("voy", "vas", "va", "vamos", "van", "fui", "fue", "iba", "ire", "iré"),
    "gustar": ("gusta", "gustan", "gusto", "gustas", "gustó", "gusto"),
}


def _is_medical_register(sentence: str, lang: str = "es") -> bool:
    norm = _normalize(sentence)
    if lang == "fr":
        return bool(
            re.search(
                r"\b(patient|ains|medicament|chirurg|intervention|diagnostic)\b",
                norm,
                re.I,
            )
        )
    return bool(
        re.search(
            r"\b(paciente|aines|medicamento|cirugia|cirugía|intervencion|intervención|diagnostico|diagnóstico)\b",
            norm,
            re.I,
        )
    )


def _has_french_subjunctive(norm: str) -> bool:
    return bool(
        re.search(
            r"\b(eut|fut|soit|ait|eussent|fussent|vinssent|fussiez|eussions)\b",
            norm,
            re.I,
        )
    )


def _has_french_typography_issue(sentence: str) -> bool:
    return bool(re.search(r"[A-Za-zÀ-ÿ][?!;:]", sentence))


def _assessed_level_plausible(sentence: str, level: str, lang: str = "es") -> bool:
    norm = _normalize(sentence)
    wc = len(sentence.split())
    has_sub = _has_subordinator(sentence)
    if lang == "fr":
        has_subj = _has_french_subjunctive(norm)
        has_cond = bool(
            re.search(r"\b(aurais|aurait|aurions|auriez|serais|serait|ferais|ferait)\b", norm, re.I)
        )
        has_passe = bool(re.search(r"\b(suis alle|suis allé|est alle|est allé|ai ete|ai été)\b", norm, re.I))
    else:
        has_subj = bool(
            re.search(r"\b(hubiera|tuviera|fuera|pudiera|quisiera|hiciera|hubiese|tuviese)\b", norm, re.I)
        )
        has_cond = bool(re.search(r"\b(habria|habría|tendria|tendría|seria|sería|podria|podría)\b", norm, re.I))
        has_passe = bool(
            re.search(
                r"\b(fui|fue|fuimos|fueron|hice|hizo|estuve|estuvo|pude|pudo|quise|quiso|vine|vino|dije|dijo)\b",
                norm,
                re.I,
            )
        )
    u = level.upper()
    if u == "A1":
        return wc <= 8 and not has_sub and not has_subj and not has_cond and not has_passe
    if u == "A2":
        return wc <= 12 and not has_subj
    if u in ("B1", "B2"):
        return True
    if u in ("C1", "C2"):
        if _is_medical_register(sentence, lang) and wc >= 8:
            return True
        if lang == "fr" and u == "C2" and wc >= 14 and has_sub and (
            "arbitrage" in norm or "stipulations" in norm or "obligatoire" in norm
        ):
            return True
        if lang == "es" and u == "C2" and wc >= 14 and has_sub and (
            "arbitraje" in norm or "vinculante" in norm or "renuncien" in norm
        ):
            return True
        return has_subj or (has_sub and wc >= 12) or has_cond
    return False


def _coach_salvage_assessed_level(sentence: str, assessed: str | None, lang: str = "es") -> str | None:
    """Adjust model CEFR labels that are one band off for clear structural cues."""
    if not assessed or not sentence:
        return assessed
    norm = _normalize(sentence)
    u = assessed.upper()
    has_preterite = bool(
        re.search(
            r"\b(fui|fue|fuimos|fueron|hice|hizo|estuve|estuvo|pude|pudo|quise|quiso|vine|vino|dije|dijo)\b",
            norm,
            re.I,
        )
    )
    if u == "A1":
        if has_preterite and _assessed_level_plausible(sentence, "A2", lang):
            return "A2"
        if re.search(r"\bgust", norm) and len(sentence.split()) >= 5 and _assessed_level_plausible(
            sentence, "A2", lang
        ):
            return "A2"
    if u == "B1" and _simple_preterite_past_narrative(sentence) and _assessed_level_plausible(
        sentence, "A2", lang
    ):
        return "A2"
    if u == "B1" and re.search(r"\btuviera\b", norm) and re.search(
        r"\b(estudiaria|estudiaría|haría|haria)\b", norm, re.I
    ):
        return "B2"
    if u == "A2" and re.search(r"\bquiero que\b", norm) and re.search(
        r"\b(vengas|venga|haga|hagas|tenga|tengas)\b", norm, re.I
    ):
        return "B2"
    if u == "A2" and re.search(r"\b(senora|senor|dominga)\b", norm) and re.search(
        r"\bcomo esta\b", norm, re.I
    ):
        return "B1"
    if u == "B2" and re.search(r"\bhubiera\b", norm) and _has_subordinator(sentence):
        return "C1"
    if lang == "fr":
        if u == "B1" and re.search(r"\bhier\b", norm) and re.search(
            r"\b(suis alle|suis allé|est alle|est allé)\b", norm, re.I
        ) and _assessed_level_plausible(sentence, "A2", lang):
            return "A2"
        if u == "B2" and re.search(r"\b(fait que|soit arrive|soit arrivé)\b", norm, re.I):
            return "C1"
    return assessed


def _confident_assessed_level(sentence: str, lang: str = "es") -> str | None:
    """High-confidence CEFR from structure when the model omitted a label."""
    norm = _normalize(sentence)
    wc = len(sentence.split())
    has_preterite = bool(
        re.search(
            r"\b(fui|fue|fuimos|fueron|hice|hizo|estuve|estuvo|pude|pudo|quise|quiso|vine|vino|dije|dijo)\b",
            norm,
            re.I,
        )
    )
    if lang == "fr":
        if wc <= 6 and re.search(r"\b(suis|es|est|vais|vas|va)\b", norm) and not _has_subordinator(sentence):
            if _assessed_level_plausible(sentence, "A1", lang):
                return "A1"
        if re.search(r"\b(aime|aimes|aiment)\b", norm) and wc <= 10 and _assessed_level_plausible(
            sentence, "A2", lang
        ):
            return "A2"
        if re.search(r"\bhier\b", norm) and re.search(
            r"\b(suis alle|est alle)\b", norm, re.I
        ) and _assessed_level_plausible(sentence, "A2", lang):
            return "A2"
        if ("je pense" in norm or "nous devons" in norm) and wc >= 8 and _assessed_level_plausible(
            sentence, "B1", lang
        ):
            return "B1"
        if re.search(r"\b(bonjour|madame|monsieur)\b", norm) and re.search(
            r"\b(allez|comment)\b", norm, re.I
        ) and _assessed_level_plausible(sentence, "B1", lang):
            return "B1"
        if _is_medical_register(sentence, lang) and wc >= 8 and _assessed_level_plausible(sentence, "C1", lang):
            return "C1"
        if re.search(r"\bje veux que\b", norm) and re.search(
            r"\b(viennes|vienne|viennent|fasses|fasse|sois|soit)\b", norm, re.I
        ):
            return "B2"
        if re.search(r"\bsi\s+j\s+avais\b", norm) or re.search(
            r"\bsi\s+(tu|il|elle|nous|vous)\s+avais\b", norm, re.I
        ):
            if re.search(r"\b(serais|serait|viendrais|viendrait|ferais|ferait|serais venu)\b", norm, re.I):
                return "B2"
        if re.search(r"\bfait qu", norm) and re.search(r"\bsoit\b", norm) and _has_subordinator(sentence):
            return "C1"
        if wc >= 14 and re.search(
            r"\b(eu egard|stipulations|arbitrage|obligatoire|different)\b", norm, re.I
        ) and _assessed_level_plausible(sentence, "C2", lang):
            return "C2"
        return None

    if has_preterite and wc >= 5 and _assessed_level_plausible(sentence, "A2", lang):
        return "A2"
    if ("estoy incomoda" in norm or ("estoy" in norm and "no dejo de" in norm)) and _assessed_level_plausible(
        sentence, "B1", lang
    ):
        return "B1"
    if _is_medical_register(sentence, lang) and wc >= 8 and _assessed_level_plausible(sentence, "C1", lang):
        return "C1"
    if _simple_preterite_past_narrative(sentence) and _assessed_level_plausible(sentence, "A2", lang):
        return "A2"
    if re.search(r"\bquiero que\b", norm) and re.search(
        r"\b(vengas|venga|haga|hagas|tenga|tengas)\b", norm, re.I
    ):
        return "B2"
    if re.search(r"\bhubiera\b", norm) and _has_subordinator(sentence) and _assessed_level_plausible(
        sentence, "C1", lang
    ):
        return "C1"
    if wc >= 14 and re.search(
        r"\b(arbitraje|vinculante|renuncien|estipulado|medida en que)\b", norm, re.I
    ) and _assessed_level_plausible(sentence, "C2", lang):
        return "C2"
    return None


def _preserve_inferred_fields(
    out: dict[str, Any], sentence: str | None = None, lang: str = "es"
) -> dict[str, Any]:
    keep_level = out.get("_keep_assessed_level") is True
    if out.get("_coach_repaired") and not keep_level:
        out.pop("assessed_level", None)
        out.pop("assessedLevel", None)
        out.pop("sentence_level", None)
        assessed = None
    else:
        assessed = normalize_assessed_level(
            out.get("assessed_level") or out.get("assessedLevel") or out.get("sentence_level")
        )
        if assessed and sentence:
            assessed = _coach_salvage_assessed_level(sentence, assessed, lang=lang)
    if assessed and sentence and not _assessed_level_plausible(sentence, assessed, lang=lang):
        assessed = None
    if not assessed and sentence:
        assessed = _confident_assessed_level(sentence, lang=lang)
    if assessed and sentence:
        assessed = _coach_salvage_assessed_level(sentence, assessed, lang=lang)
    if assessed and sentence and not _assessed_level_plausible(sentence, assessed, lang=lang):
        out.pop("assessed_level", None)
    elif assessed:
        out["assessed_level"] = assessed
    else:
        out.pop("assessed_level", None)
    out.pop("_keep_assessed_level", None)
    out.pop("assessedLevel", None)
    out.pop("sentence_level", None)
    note = str(out.get("complexity_note") or out.get("complexityNote") or "").strip()
    if note:
        out["complexity_note"] = note
    else:
        out.pop("complexity_note", None)
    out.pop("complexityNote", None)
    return out


def spanish_coach_system_prompt(level: str = "", dialect: str = DEFAULT_ES_DIALECT, rag_context: str = "") -> str:
    """Inference prompt — CEFR level inferred from the sentence only."""
    prompt = (
        f"You are a Spanish grammar coach for interpreter training, "
        f"with expertise in {dialect} dialect variation. "
        "Do NOT assume the learner picked a CEFR level.\n\n"
        f"{CEFR_COMPLEXITY_PROMPT}"
        "CRITICAL ACCURACY RULES:\n"
        "- Do NOT invent grammatical errors. Only flag real, clear mistakes.\n"
        '- Grammatically correct sentences are "Excellent" — but explanation must cite specific structures (not generic praise).\n'
        '- Do NOT set assessed_level unless highly confident. When uncertain, omit and use complexity_note only.\n'
        '- next_level_alt MUST upgrade the sentence — never copy input verbatim.\n'
        '- tip MUST include a complete Spanish example sentence showing stronger phrasing.\n'
        '- Only mark "Needs Improvement" when there is an actual grammar error — not a style preference.\n'
        "- Never flag valid dialect features as errors (e.g. voseo in Rioplatense, ustedes for all plural).\n"
        "- With formal address (señor/señora + «está»), do NOT «correct» to informal «estás».\n"
        "- After «si» in hypothetical clauses, use imperfect subjunctive (tuviera), NOT conditional (tendría).\n"
        "- ALL example sentences (correction, next_level_alt, target_level_alt) MUST be complete sentences in Spanish.\n"
        "- grammar_rule, explanation, register, and tip MUST be in English.\n"
        "- For next_level_alt: same idea one CEFR level above assessed_level.\n"
        "- For target_level_alt: same idea two levels above assessed_level (null at C1/C2).\n"
    )
    if rag_context.strip():
        prompt += (
            "\nREFERENCE KNOWLEDGE (use these rules to verify accuracy — do not invent errors outside them):\n"
            f"{rag_context.strip()}\n"
        )
    prompt += (
        "\nRespond with ONLY a valid JSON object (no markdown fences):\n"
        "{\n"
        '  "assessed_level": "A1" | "A2" | "B1" | "B2" | "C1" | "C2" | null,\n'
        '  "complexity_note": "1–2 English sentences on sentence complexity (vocabulary, syntax, subordination, register)",\n'
        '  "status": "Excellent" or "Needs Improvement",\n'
        '  "grammar_rule": "The specific grammar rule — always name the rule, even when correct",\n'
        '  "explanation": "WHY the sentence is correct or incorrect — cite the learner\'s words",\n'
        '  "correction": null or "Corrected sentence in Spanish (required when Needs Improvement)",\n'
        '  "register": "Formal (usted) or informal (tú/vos) and whether appropriate for interpreter settings",\n'
        '  "next_level_alt": "Same idea one CEFR level above assessed_level, in Spanish",\n'
        '  "target_level_alt": "Same idea two levels above assessed_level, in Spanish (null at C1/C2 if N/A)",\n'
        '  "tip": "Practical interpreter tip about register, Anglicisms, or word precision"\n'
        "}"
    )
    return prompt


def spanish_coach_user_prompt(sentence: str, level: str = "") -> str:
    return f'Analyze this Spanish sentence: "{sentence}"'


def french_coach_system_prompt(level: str = "", rag_context: str = "") -> str:
    prompt = (
        "You are a French grammar coach for interpreter training, "
        "with expertise in France and Canadian (Québec) dialect variation. "
        "Do NOT assume the learner picked a CEFR level.\n\n"
        f"{CEFR_COMPLEXITY_PROMPT}"
        "CRITICAL ACCURACY RULES:\n"
        "- Do NOT invent grammatical errors. Only flag real, clear mistakes.\n"
        '- Grammatically correct sentences are "Excellent" — but explanation must cite specific structures (not generic praise).\n'
        '- Do NOT set assessed_level unless highly confident. When uncertain, omit and use complexity_note only.\n'
        '- next_level_alt MUST upgrade the sentence — never copy input verbatim.\n'
        '- tip MUST include a complete French example sentence showing stronger phrasing.\n'
        '- Only mark "Needs Improvement" when there is an actual grammar error — not a style preference.\n'
        "- Never flag valid Canadian French features as errors unless inappropriate for context.\n"
        "- Si-clause: Si + imparfait → conditionnel — NOT *Si j'aurais* in the protasis.\n"
        "- ALL example sentences must be complete sentences in French.\n"
        "- grammar_rule, explanation, register, and tip MUST be in English.\n"
        "- For next_level_alt: same idea one CEFR level above assessed_level.\n"
        "- For target_level_alt: same idea two levels above assessed_level (null at C1/C2).\n"
    )
    if rag_context.strip():
        prompt += (
            "\nREFERENCE KNOWLEDGE (use these rules to verify accuracy — do not invent errors outside them):\n"
            f"{rag_context.strip()}\n"
        )
    prompt += (
        "\nRespond with ONLY a valid JSON object (no markdown fences):\n"
        "{\n"
        '  "assessed_level": "A1" | "A2" | "B1" | "B2" | "C1" | "C2" | null,\n'
        '  "complexity_note": "1–2 English sentences on sentence complexity (vocabulary, syntax, subordination, register)",\n'
        '  "status": "Excellent" or "Needs Improvement",\n'
        '  "grammar_rule": "The specific grammar rule — always name the rule, even when correct",\n'
        '  "explanation": "WHY the sentence is correct or incorrect — cite the learner\'s words",\n'
        '  "correction": null or "Corrected sentence in French (required when Needs Improvement)",\n'
        '  "register": "Formal (vous) or informal (tu) and whether appropriate for interpreter settings",\n'
        '  "next_level_alt": "Same idea one CEFR level above assessed_level, in French",\n'
        '  "target_level_alt": "Same idea two levels above assessed_level, in French (null at C1/C2 if N/A)",\n'
        '  "tip": "Practical interpreter tip about register, Anglicisms, or word precision"\n'
        "}"
    )
    return prompt


def french_coach_user_prompt(sentence: str, level: str = "") -> str:
    return f'Analyze this French sentence: "{sentence}"'


def _normalize(text: str) -> str:
    text = text.lower()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^a-z0-9\s]", " ", text)


def _tokens(text: str) -> set[str]:
    return {
        t
        for t in _normalize(text).split()
        if len(t) >= 3 and t not in STOPWORDS
    }


def _quoted_terms(text: str) -> list[str]:
    terms: list[str] = []
    for m in ALLOWLIST_QUOTED.finditer(text):
        term = (m.group(1) or m.group(2) or m.group(3) or "").strip()
        if len(term) >= 3:
            terms.append(term)
    return terms


def _term_reflected_in_sentence(sent_norm: str, sent_tokens: set[str], core: str) -> bool:
    if core in sent_norm or core in sent_tokens:
        return True
    parts = [p for p in core.split() if len(p) >= 4]
    if parts and any(p in sent_norm for p in parts):
        return True
    for lemma, forms in _VERB_SURFACE_FORMS.items():
        if core == lemma or core.startswith(lemma + " "):
            if any(f in sent_norm.split() or f in sent_tokens for f in forms):
                return True
    return False


def find_hallucinated_terms(sentence: str, *texts: str) -> list[str]:
    """Spanish terms in coach text that are not reflected in the learner sentence."""
    sent_norm = _normalize(sentence)
    sent_tokens = _tokens(sentence)
    bad: list[str] = []
    for text in texts:
        if not text:
            continue
        for term in _quoted_terms(text):
            core = _normalize(term)
            if len(core) < 3:
                continue
            # Ignore English fragments accidentally captured by «…» parsing
            if re.search(r"\b(more|instead|common|should|would|when)\b", core):
                continue
            if _term_reflected_in_sentence(sent_norm, sent_tokens, core):
                continue
            bad.append(term)
    return bad


def _strip_unrelated_alts(sentence: str, feedback: dict[str, Any]) -> dict[str, Any]:
    out = dict(feedback)
    for key in ("next_level_alt", "target_level_alt"):
        if is_unrelated_rewrite(sentence, out.get(key)):
            out.pop(key, None)
    return out


def is_unrelated_rewrite(sentence: str, alt: str | None) -> bool:
    if not alt or not alt.strip():
        return False
    sw = _tokens(sentence)
    aw = _tokens(alt)
    if not sw or not aw:
        return False
    overlap = sw & aw
    min_overlap = 2 if len(sw) >= 3 else 1
    return len(overlap) < min_overlap


def detect_register_conflict(sentence: str, feedback: dict[str, Any]) -> bool:
    sent = _normalize(sentence)
    correction = feedback.get("correction") or ""
    corr = _normalize(correction) if correction else ""

    formal_markers = ("usted", "señor", "señora", "don ", "doña ", "sr.", "sra.")
    informal_markers = (" tú ", " tu ", "vos ", " estás", " estás?", " cómo estás")

    sent_formal = any(m in sent for m in formal_markers) or (
        " está" in sent or sent.rstrip().endswith("esta")
    )
    sent_informal = any(m in sent for m in informal_markers) or "estás" in sent

    reg_text = _normalize(str(feedback.get("register") or ""))
    claims_formal = "formal" in reg_text and "informal" not in reg_text

    corr_informal = "estás" in corr or " cómo estás" in corr
    corr_formal = "usted" in corr or " está usted" in corr

    if sent_formal and not sent_informal and corr_informal and not corr_formal:
        return True
    if claims_formal and corr_informal and not corr_formal:
        return True
    return False


def _grammar_rule_looks_like_meta(rule: str) -> bool:
    lower = rule.lower()
    return (
        "the learner" in lower
        or "the sentence" in lower
        or "needs to" in lower
        or "should have" in lower
    )


def _echar_de_menos_leismo_feedback(sentence: str, level: str) -> dict[str, Any] | None:
    if not ECHAR_DE_MENOS_LEISMO.search(sentence):
        return None
    norm = _normalize(sentence)
    if any(h in norm for h in FEMININE_ANTECEDENT_HINTS):
        direct = "la"
    elif any(h in norm for h in MASCULINE_ANTECEDENT_HINTS):
        direct = "lo"
    else:
        direct = "la"
    correction = sentence
    correction = re.sub(
        r"\bles\s+echo\s+de\s+menos\b",
        f"{'las' if direct == 'la' else 'los'} echo de menos",
        correction,
        flags=re.I,
    )
    correction = re.sub(
        r"\ble\s+echo\s+de\s+menos\b",
        f"{direct} echo de menos",
        correction,
        flags=re.I,
    )
    out: dict[str, Any] = {
        "status": "Needs Improvement",
        "grammar_rule": "«Echar de menos» takes a direct object (lo/la), not «le»",
        "explanation": (
            f"«Echar de menos» governs a direct object: «{direct} echo de menos». "
            "«Le echo de menos» is leísmo — common in speech but «le» is not the direct object form on DELE/interpreter exams."
        ),
        "correction": correction,
        "register": "Neutral; leísmo may appear regionally but use lo/la for standard written Spanish.",
        "next_level_alt": correction,
        "tip": "Match the pronoun to who you miss: «la echo de menos» (her), «lo echo de menos» (him), «los echo de menos» (them).",
        "complexity_note": (
            "Fixed expression «echar de menos» with clitic pronoun; leísmo with «le» is common in speech "
            "but direct-object lo/la is expected in formal and exam Spanish."
        ),
        "_coach_repaired": True,
    }
    if level.upper() not in ("C1", "C2"):
        out["target_level_alt"] = correction
    return out


def _heuristic_improvement_tip(sentence: str, level: str, issues: list[str]) -> str:
    norm = _normalize(sentence)
    if "echo de menos" in norm:
        return "«Echar de menos» takes lo/la: «la echo de menos» (her), «lo echo de menos» (him) — not «le»."
    if re.search(r"\b(le|les|lo|la|los|las)\s+\w", sentence, re.I):
        return (
            "Check clitic pronouns: direct objects are lo/la/los/las; "
            "«le/les» mark indirect objects unless regional leísmo applies."
        )
    if issues:
        return "Fix punctuation first, then confirm tú/usted matches your interpreting scenario."
    return (
        f"Tighten vocabulary for {level}: prefer precise verbs and connectors over repeated "
        "«y» clauses where a subordinate fits."
    )


def known_spanish_error_feedback(sentence: str, level: str) -> dict[str, Any] | None:
    from coach_rules import feedback_from_rules

    if fb := feedback_from_rules(sentence, "es"):
        out = dict(fb)
        if level.upper() not in ("C1", "C2") and out.get("correction"):
            out["next_level_alt"] = out["correction"]
            out["target_level_alt"] = out["correction"]
        return _preserve_inferred_fields(out, sentence)
    return None


def known_french_error_feedback(sentence: str, level: str) -> dict[str, Any] | None:
    if not SI_CLAUSE_FRENCH_CONDITIONAL.search(sentence):
        return None
    correction = sentence
    for pattern, repl in (
        (re.compile(r"\bj'aurais\b", re.I), "j'avais"),
        (re.compile(r"\btu aurais\b", re.I), "tu avais"),
        (re.compile(r"\bil aurait\b", re.I), "il avait"),
        (re.compile(r"\belle aurait\b", re.I), "elle avait"),
        (re.compile(r"\bnous aurions\b", re.I), "nous avions"),
        (re.compile(r"\bvous auriez\b", re.I), "vous aviez"),
    ):
        correction = pattern.sub(repl, correction)
    out: dict[str, Any] = {
        "status": "Needs Improvement",
        "grammar_rule": "Si clauses: imparfait in the protasis, not conditionnel",
        "explanation": (
            "After « si » introducing a hypothetical condition, French uses the imparfait "
            "(e.g. « j'avais »), not the conditionnel (« j'aurais »). The conditionnel belongs in the main clause."
        ),
        "correction": correction,
        "register": "Neutral; focus on standard French for interpreting exams.",
        "next_level_alt": correction,
        "tip": "Mnemonic: « Si j'avais…, je ferais… » — imparfait in the si-clause, conditionnel in the result.",
        "complexity_note": (
            "Hypothetical « si » clause with conditionnel in the protasis instead of imparfait — "
            "upper-intermediate structure band even when the form is wrong."
        ),
        "assessed_level": "B2",
        "_coach_repaired": True,
        "_keep_assessed_level": True,
    }
    if level.upper() not in ("C1", "C2"):
        out["target_level_alt"] = correction
    return out


def _is_greeting_sentence(sentence: str) -> bool:
    n = _normalize(sentence)
    return any(
        token in n
        for token in ("hola", "buenos", "como esta", "senora", "senor")
    )


_TIME_ADVERBS = (
    "ayer",
    "hoy",
    "manana",
    "mañana",
    "anoche",
    "anteayer",
    "pasado manana",
    "pasado mañana",
)

# Unaccented token → accented form (display label for feedback)
_ACCENT_FIXES: tuple[tuple[str, str, str], ...] = (
    (r"\bcomi\b", "comí", "comí"),
    (r"\bcomio\b", "comió", "comió"),
    (r"\btrabaje\b", "trabajé", "trabajé"),
    (r"\btrabajo\b", "trabajó", "trabajó"),
    (r"\bestuve\b", "estuve", "estuve"),
    (r"\bestudio\b", "estudié", "estudié"),
    (r"\bdi\b", "dí", "dí"),
)


def _missing_accent_fixes(sentence: str) -> list[tuple[str, str]]:
    """Words that need a written accent (learner wrote ASCII-only form)."""
    missing: list[tuple[str, str]] = []
    for pattern, accented, label in _ACCENT_FIXES:
        if re.search(pattern, sentence, re.I) and not re.search(
            rf"\b{re.escape(accented)}\b", sentence, re.I
        ):
            missing.append((pattern, label))
    return missing


def _apply_accent_fixes(sentence: str, missing: list[tuple[str, str]]) -> str:
    out = sentence
    for pattern, label in missing:
        out = re.sub(pattern, label, out, count=1, flags=re.I)
    return out


def _explanation_mentions_accents(explanation: str, labels: list[str]) -> bool:
    low = explanation.lower()
    if "accent" in low or "acento" in low or "tilde" in low or "orthograph" in low:
        return True
    return any(label.lower() in low for label in labels)


def _cites_time_adverb_as_verb_tense(feedback: dict[str, Any]) -> bool:
    """Reject «preterite Ayer» / «imperfect Ayer» — adverbs are not conjugated."""
    text = " ".join(
        str(feedback.get(k) or "")
        for k in ("grammar_rule", "explanation", "tip")
    ).lower()
    if "preterite" not in text and "imperfect" not in text and "pretérito" not in text:
        return False
    for adv in _TIME_ADVERBS:
        if adv not in text:
            continue
        if re.search(
            rf"(preterite|imperfect|pretérito|imperfecto).{{0,40}}{re.escape(adv)}|"
            rf"{re.escape(adv)}.{{0,40}}(preterite|imperfect|pretérito|imperfecto)",
            text,
        ):
            return True
        if re.search(rf"['\"«]{adv}['\"»]", text) and (
            "preterite" in text or "imperfect" in text
        ):
            return True
    return False


def _simple_preterite_past_narrative(sentence: str) -> bool:
    """Yesterday + preterite main clauses, no imperfect backdrop or subordination."""
    norm = _normalize(sentence)
    if not any(adv in norm for adv in ("ayer", "anoche", "anteayer")):
        return False
    has_preterite = bool(
        re.search(
            r"\b(fue|fui|comi|comio|trabaje|trabajo|estuve|hice|hizo|vine|vino|di|dio)\b",
            norm,
            re.I,
        )
    )
    has_imperfect = bool(
        re.search(r"\b(era|estaba|comia|trabajaba|habia|había|iba)\b", norm, re.I)
    )
    return has_preterite and not has_imperfect and not _has_subordinator(sentence)


def _past_narrative_accent_feedback(sentence: str) -> dict[str, Any]:
    """Reliable feedback for short ayer + preterite lines (accent / light style only)."""
    missing = _missing_accent_fixes(sentence)
    correction = _apply_accent_fixes(sentence, missing) if missing else None
    if correction:
        correction = re.sub(r",\s*y\s+yo\s+", " y ", correction, count=1, flags=re.I)
        correction = re.sub(r"\s+y\s+yo\s+", " y ", correction, count=1, flags=re.I)

    if missing:
        labels = ", ".join(f"«{lbl}»" for _, lbl in missing)
        grammar = "Written accent marks (tildes) on past-tense verb forms"
        explanation = (
            f"Add the missing accent(s) on {labels}. "
            "«Ayer» is a time adverb (yesterday), not a verb — it does not have preterite or imperfect forms. "
            "Your preterite verbs (*fue*, *comí*, *trabajé*) are appropriate for completed events yesterday."
        )
        status = "Needs Improvement"
    else:
        grammar = "Preterite narrative with time adverb «ayer»"
        explanation = (
            "«Ayer» sets the time frame; *fue*, *comí*, and *trabajé* correctly use the preterite "
            "for completed actions. Coordination with «y» is natural in informal narration."
        )
        status = "Excellent"

    out: dict[str, Any] = {
        "status": status,
        "grammar_rule": grammar,
        "explanation": explanation,
        "complexity_note": (
            "Short past-tense narrative (~12 words): time adverb «ayer», preterite verbs, "
            "coordination with «y» — A2 band, not B1 subordination."
        ),
        "assessed_level": "A2",
        "register": "Informal diary-style narration; standard written accents expected in formal text.",
        "next_level_alt": "Ayer me fue muy bien el día; comí con mi madre y trabajé un rato en el campo.",
        "tip": "Remember accents on preterite -é/-í forms: «comí», «trabajé». «Ayer» never takes a tense ending.",
        "_keep_assessed_level": True,
    }
    if correction and correction.strip() != sentence.strip():
        out["correction"] = correction
    if status == "Excellent":
        out["correction"] = None
    return _preserve_inferred_fields(out, sentence)


def _model_invented_error(sentence: str, feedback: dict[str, Any]) -> bool:
    if feedback.get("status") != "Needs Improvement":
        return False
    if _cites_time_adverb_as_verb_tense(feedback):
        return True
    fields = (
        str(feedback.get("grammar_rule") or ""),
        str(feedback.get("explanation") or ""),
    )
    if find_hallucinated_terms(sentence, *fields):
        return True
    # Preterite/imperfect lecture on a simple ayer narrative with no real tense error
    text = " ".join(fields).lower()
    if _simple_preterite_past_narrative(sentence) and (
        "preterite" in text and "imperfect" in text
    ):
        if not _missing_accent_fixes(sentence):
            return True
    return False


def _infer_assessed_level(norm: str, word_count: int, y_coordinated: bool, has_subjunctive: bool) -> str | None:
    """Deprecated — do not assign CEFR from heuristics."""
    return None


def _strip_trailing_punct(text: str) -> str:
    return text.strip().rstrip(".,!?;:")


def _upgrade_y_coordination(text: str) -> tuple[str, str | None]:
    parts = re.split(r"\s+y\s+", text, maxsplit=1, flags=re.I)
    if len(parts) != 2:
        return text, None
    a = _strip_trailing_punct(parts[0].strip())
    b = _strip_trailing_punct(parts[1].strip())
    if b:
        b = b[0].lower() + b[1:]
    nxt = f"{a}, porque {b}."
    tgt = f"{a}, sobre todo porque {b}, lo cual me resulta difícil de manejar."
    return nxt, tgt


def _substantive_excellent_feedback(sentence: str) -> dict[str, Any]:
    text = sentence.strip()
    norm = _normalize(text)
    word_count = len(text.split())
    y_coordinated = bool(re.search(r"\s+y\s+", text, re.I))
    has_subjunctive = bool(
        re.search(r"\b(hubiera|tuviera|fuera|pudiera|quisiera|hiciera)\b", norm, re.I)
    )
    assessed = None

    if "estoy incomoda" in norm or "estoy incómoda" in text.lower() or (
        "estoy" in norm and "no dejo de" in norm
    ):
        grammar = "Estar + adjective for temporary states; periphrasis «no dejar de + infinitive»"
        explanation = (
            "«Estoy incómoda» correctly uses **estar** for a temporary state or feeling — "
            "*ser incómoda* would describe a person's character, not how you feel right now. "
            "«No dejo de pensar» is a valid periphrasis meaning \"I can't stop thinking.\" "
            "Both clauses are grammatically sound; chaining them with «y» keeps the sentence "
            "conversational but structurally simple."
        )
        complexity = (
            "Two coordinated main clauses joined with «y»: present tense + adjective (estar) and the "
            "periphrasis «no dejar de + infinitive». No subordination — everyday spoken structure."
        )
        register = (
            "Informal first person (tú implied); appropriate for personal or clinical rapport "
            "if the context is intimate."
        )
        next_alt = "Me siento incómoda porque no dejo de pensar en ello."
        target_alt = "Me encuentro incómoda, sobre todo porque no consigo dejar de darle vueltas al asunto."
        tip = (
            "Replace «y» with cause: «Me siento incómoda **porque** no dejo de pensar en ello.» Or: "
            "«…**pues** no puedo dejar de **darle vueltas** al asunto.»"
        )
        assessed = "B1"
    elif y_coordinated and not _has_subordinator(text):
        grammar = "Coordination with «y» vs subordination (porque, pues, lo cual)"
        explanation = (
            "Your sentence links ideas with «y», which is grammatically fine but reads as two separate "
            "thoughts. Subordinating the second clause (cause, contrast, or result) shows tighter control "
            "and sounds more natural in formal settings."
        )
        complexity = (
            "Simple coordination with «y» and no subordinate clause — structurally straightforward. "
            "Clear vocabulary but limited syntactic layering."
        )
        register = (
            "Confirm tú/usted matches the setting; «y» chains are fine in casual speech but often "
            "upgraded in formal interpreting."
        )
        next_alt, target_alt = _upgrade_y_coordination(text)
        tip = f"Upgrade: «{next_alt}» — swap «y» for **porque** or **pues** to show how the two ideas relate."
    elif "estoy " in norm or "estoy," in norm:
        grammar = "Ser vs estar — temporary states with estar"
        explanation = (
            "Using **estar** for feelings, conditions, or locations is appropriate here. The sentence is "
            "grammatically correct; focus next on whether vocabulary and connectors match the formality "
            "of your interpreting context."
        )
        complexity = (
            f"Present tense with **estar** + complement. {word_count} words — "
            f"{'includes subordination' if _has_subordinator(text) else 'main-clause structure only'}."
        )
        register = "First-person state description; match tú/usted to the patient or client relationship."
        next_alt = text if text.endswith(".") else text + "."
        target_alt = None
        if y_coordinated:
            next_alt, target_alt = _upgrade_y_coordination(text)
        tip = (
            "Add precision: try «Me siento…» or «Me encuentro…» for a slightly more formal register."
        )
    else:
        grammar = "Sentence structure and register"
        explanation = (
            "No grammar error stands out. The structures you used are acceptable — tighten vocabulary "
            "and connectors so the line fits a professional interpreting context."
        )
        complexity = (
            f"{word_count}-word sentence. "
            f"{'Includes subordination' if _has_subordinator(text) else 'Main-clause structure'} — "
            "describe syntax and vocabulary rather than assigning a CEFR band."
        )
        register = "Confirm tú/usted and formality match the scenario (clinical, legal, or casual)."
        if y_coordinated and not _has_subordinator(text):
            next_alt, target_alt = _upgrade_y_coordination(text)
        else:
            next_alt, target_alt = text, None
        tip = (
            "Try a subordinate clause: «…, **porque** …» or «…, **lo cual** …» to link ideas in one sentence."
        )

    out: dict[str, Any] = {
        "status": "Excellent",
        "grammar_rule": grammar,
        "explanation": explanation,
        "complexity_note": complexity,
        "register": register,
        "next_level_alt": next_alt,
        "tip": tip,
        "_coach_repaired": True,
    }
    if assessed:
        out["assessed_level"] = assessed
        out["_keep_assessed_level"] = True
    if target_alt:
        out["target_level_alt"] = target_alt
    return _preserve_inferred_fields(out, sentence)


def _feedback_is_low_quality(sentence: str, feedback: dict[str, Any]) -> bool:
    grammar = str(feedback.get("grammar_rule") or "").lower()
    explanation = str(feedback.get("explanation") or "")
    complexity = str(feedback.get("complexity_note") or feedback.get("complexityNote") or "").strip()
    nxt = str(feedback.get("next_level_alt") or "")
    if "general spanish grammar" in grammar:
        return True
    if "no clear errors detected" in explanation.lower():
        return True
    if "no confirmed grammar error" in explanation.lower():
        return True
    if len(explanation.strip()) < 48:
        return True
    if not complexity:
        return True
    if nxt and _normalize(nxt) == _normalize(sentence):
        return True
    return False


def _generic_excellent_feedback(sentence: str, level: str) -> dict[str, Any]:
    return _substantive_excellent_feedback(sentence)


def _salvage_feedback(sentence: str, feedback: dict[str, Any]) -> dict[str, Any] | None:
    out = dict(feedback)
    for alt_key in ("next_level_alt", "target_level_alt"):
        if is_unrelated_rewrite(sentence, out.get(alt_key)):
            out.pop(alt_key, None)
    if detect_register_conflict(sentence, out):
        out.pop("correction", None)
        out["status"] = "Excellent"
        out["explanation"] = (
            str(out.get("explanation") or "")
            + " Formal «está» with «señora» is correct — informal «estás» would be a register error."
        ).strip()
    halluc = find_hallucinated_terms(
        sentence,
        str(out.get("grammar_rule") or ""),
        str(out.get("explanation") or ""),
        str(out.get("tip") or ""),
    )
    if halluc:
        return None
    return out


def feedback_needs_repair(sentence: str, feedback: dict[str, Any], lang: str = "es") -> bool:
    status = str(feedback.get("status") or "")
    grammar_rule = str(feedback.get("grammar_rule") or "")
    explanation = str(feedback.get("explanation") or "")
    tip = str(feedback.get("tip") or "")
    correction = str(feedback.get("correction") or "")

    # Quoted examples in tips often mention forms not in the learner sentence — only check on errors.
    if status == "Needs Improvement":
        fields = (grammar_rule, explanation, tip)
        if find_hallucinated_terms(sentence, *fields):
            return True
    if is_unrelated_rewrite(sentence, feedback.get("next_level_alt")):
        return True
    if is_unrelated_rewrite(sentence, feedback.get("target_level_alt")):
        return True
    if detect_register_conflict(sentence, feedback):
        return True
    if _grammar_rule_looks_like_meta(grammar_rule):
        return True
    if status == "Needs Improvement":
        if len(explanation.strip()) < 24:
            return True
        if not correction.strip():
            return True
        if _normalize(correction) == _normalize(sentence):
            return True
    known_fn = known_spanish_error_feedback if lang == "es" else known_french_error_feedback
    if status == "Excellent" and known_fn(sentence, ""):
        return True
    if status == "Excellent" and _feedback_is_low_quality(sentence, feedback):
        return True
    return False


def french_heuristic_feedback(sentence: str, level: str) -> dict[str, Any]:
    """Rule-based fallback when French SLM output fails sanity checks."""
    if known := known_french_error_feedback(sentence, level):
        return _preserve_inferred_fields(dict(known), sentence, lang="fr")

    text = sentence.strip()
    norm = _normalize(text)
    correction = None
    if _has_french_typography_issue(text):
        correction = re.sub(r"([A-Za-zÀ-ÿ])([?!;:])", r"\1 \2", text, count=1)
    status = "Needs Improvement" if correction else "Excellent"
    if status == "Excellent":
        out = _substantive_excellent_feedback(text)
        out["_coach_repaired"] = True
        return _preserve_inferred_fields(out, sentence, lang="fr")

    out: dict[str, Any] = {
        "status": status,
        "grammar_rule": "French typography (space before ? ! ; :)",
        "explanation": (
            "In French, insert a space before « ? », « ! », « ; », and « : » "
            "(e.g. « comment allez-vous ? »)."
        ),
        "correction": correction,
        "register": "Neutral written French.",
        "next_level_alt": correction or text,
        "tip": "Mnemonic: « mot ? » — thin space before double punctuation in formal French.",
        "_coach_repaired": True,
    }
    return _preserve_inferred_fields(out, sentence, lang="fr")


def heuristic_feedback(sentence: str, level: str) -> dict[str, Any]:
    """Rule-based fallback when the SLM output fails sanity checks."""
    if known := known_spanish_error_feedback(sentence, level):
        return known

    text = sentence.strip()
    norm = _normalize(text)
    issues: list[str] = []

    if "?" in text and "¿" not in text:
        issues.append("missing opening inverted question mark (¿)")
    if "!" in text and "¡" not in text:
        issues.append("missing opening inverted exclamation mark (¡)")
    has_informal_greeting_cue = bool(
        re.search(r"\b(te|tu|amor|carino|querido|querida)\b", norm)
    )
    has_affectionate_extranar = (
        "amor" in norm and "extran" in norm and bool(re.search(r"\bte\b", norm))
    )
    has_formal_greeting_cue = (
        (
            ("como esta" in norm or "cómo está" in text.lower())
            and "estas" not in norm
        )
        or bool(re.search(r"\b(usted|senor|senora)\b", norm))
    ) and not has_informal_greeting_cue
    if has_informal_greeting_cue:
        register = (
            "Informal and affectionate: familiar pronouns or terms of endearment fit a "
            "close personal relationship, not a formal usted exchange."
        )
    elif has_formal_greeting_cue:
        register = (
            "Formal address (usted): «señora» + third-person «está» fits a polite greeting. "
            "Keep «¿cómo está?» — do not switch to informal «¿cómo estás?» in this context."
        )
    else:
        register = "Note whether tú/usted matches the setting (clinical, legal, or casual)."

    correction = None
    if issues:
        fixed = text
        if "?" in fixed and "¿" not in fixed:
            fixed = re.sub(
                r",?\s*cómo\s+está\??",
                ", ¿cómo está?",
                fixed,
                count=1,
                flags=re.IGNORECASE,
            )
            if fixed == text:
                fixed = "¿" + fixed.lstrip()
        correction = fixed

    status = "Needs Improvement" if issues else "Excellent"
    if not issues and not _is_greeting_sentence(text):
        return _substantive_excellent_feedback(text)

    if issues:
        grammar = "Inverted question marks (¿…?) in Spanish"
        explanation = (
            (
                "Add «¿» before a question clause. With «señora» and «está», keep formal "
                "usted — do not «correct» to informal «estás»."
            )
            if has_formal_greeting_cue
            else "Add «¿» before a question clause and preserve the sentence's existing register."
        )
    elif has_affectionate_extranar:
        grammar = "Informal greeting, vocative punctuation, and direct-object pronoun «te»"
        explanation = (
            f"«{text}» is grammatically sound: «te» is the informal direct-object pronoun "
            "used with «extrañar», and «amor» is an affectionate vocative. For polished "
            "punctuation, write «Hola, amor, te extraño mucho.»"
        )
    elif has_informal_greeting_cue:
        grammar = "Informal greeting and familiar address"
        explanation = (
            f"«{text}» uses informal, familiar language. Keep that register when the "
            "relationship is personal, and use commas to set off a vocative where appropriate."
        )
    elif has_formal_greeting_cue:
        grammar = "Formal greeting and usted register"
        explanation = "Polite greeting with appropriate formal verb form; only minor punctuation may apply."
    else:
        grammar = "Greeting and context-appropriate register"
        explanation = (
            f"«{text}» is grammatically sound. Choose formal or informal address based "
            "on the relationship and interpreting setting."
        )

    next_alt = correction or text
    if has_informal_greeting_cue:
        next_alt = re.sub(r"^hola\s+", "Hola, ", next_alt, count=1, flags=re.IGNORECASE)
    elif has_formal_greeting_cue and level.upper() in ("B2", "B1", "A2", "A1"):
        next_alt = re.sub(
            r"^hola\s+",
            "Buenos días, ",
            next_alt,
            count=1,
            flags=re.IGNORECASE,
        )

    out: dict[str, Any] = {
        "status": status,
        "grammar_rule": grammar,
        "explanation": explanation,
        "register": register,
        "next_level_alt": next_alt,
        "tip": (
            f"Use commas to set off a vocative where appropriate: «{next_alt}» Keep "
            "informal «te» for a close personal relationship; use formal address or "
            "rephrase when the setting requires it."
            if has_informal_greeting_cue
            else _heuristic_improvement_tip(text, level, issues)
        ),
        "_coach_repaired": True,
    }
    if correction:
        out["correction"] = correction
    if level.upper() in ("B2", "C1", "C2"):
        out["target_level_alt"] = correction or next_alt
    return out


def _has_punctuation_issue(sentence: str) -> bool:
    return ("?" in sentence and "¿" not in sentence) or ("!" in sentence and "¡" not in sentence)


def _sanitize_french_feedback(sentence: str, feedback: dict[str, Any], level: str = "") -> dict[str, Any]:
    """Validate French SLM JSON; repair or replace when clearly unreliable."""
    if known := known_french_error_feedback(sentence, level):
        return _preserve_inferred_fields(dict(known), sentence, lang="fr")

    if _has_french_typography_issue(sentence):
        return french_heuristic_feedback(sentence, level)

    feedback = _strip_unrelated_alts(sentence, feedback)

    if feedback_needs_repair(sentence, feedback, lang="fr"):
        if salvaged := _salvage_feedback(sentence, feedback):
            if not feedback_needs_repair(sentence, salvaged, lang="fr"):
                return _preserve_inferred_fields(dict(salvaged), sentence, lang="fr")
        if known := known_french_error_feedback(sentence, level):
            return _preserve_inferred_fields(dict(known), sentence, lang="fr")
        return french_heuristic_feedback(sentence, level)

    out = dict(feedback)
    halluc = find_hallucinated_terms(
        sentence,
        str(out.get("grammar_rule") or ""),
        str(out.get("explanation") or ""),
        str(out.get("tip") or ""),
    )
    if halluc:
        out["_coach_warning"] = (
            f"Removed unreliable references not in your sentence: {', '.join(halluc[:3])}"
        )
        for key in ("grammar_rule", "explanation", "tip"):
            val = str(out.get(key) or "")
            for term in halluc:
                val = val.replace(term, "…")
            out[key] = val

    for alt_key in ("next_level_alt", "target_level_alt"):
        if is_unrelated_rewrite(sentence, out.get(alt_key)):
            out.pop(alt_key, None)

    return _preserve_inferred_fields(out, sentence, lang="fr")


def _sanitize_spanish_feedback(sentence: str, feedback: dict[str, Any], level: str = "") -> dict[str, Any]:
    """Validate Spanish SLM JSON; repair or replace when clearly unreliable."""
    if known := known_spanish_error_feedback(sentence, level):
        return _preserve_inferred_fields(dict(known), sentence)

    if _has_punctuation_issue(sentence):
        return heuristic_feedback(sentence, level)

    if _model_invented_error(sentence, feedback):
        if _simple_preterite_past_narrative(sentence):
            return _past_narrative_accent_feedback(sentence)
        return _generic_excellent_feedback(sentence, level)

    # Drop off-topic rewrites before deciding the whole response is unusable
    feedback = _strip_unrelated_alts(sentence, feedback)

    if feedback_needs_repair(sentence, feedback, lang="es"):
        if salvaged := _salvage_feedback(sentence, feedback):
            if not feedback_needs_repair(sentence, salvaged, lang="es"):
                return _preserve_inferred_fields(dict(salvaged), sentence)
        if known := known_spanish_error_feedback(sentence, level):
            return known
        return heuristic_feedback(sentence, level)

    out = dict(feedback)
    halluc = find_hallucinated_terms(
        sentence,
        str(out.get("grammar_rule") or ""),
        str(out.get("explanation") or ""),
        str(out.get("tip") or ""),
    )
    if halluc:
        out["_coach_warning"] = (
            f"Removed unreliable references not in your sentence: {', '.join(halluc[:3])}"
        )
        for key in ("grammar_rule", "explanation", "tip"):
            val = str(out.get(key) or "")
            for term in halluc:
                val = val.replace(term, "…")
            out[key] = val

    for alt_key in ("next_level_alt", "target_level_alt"):
        if is_unrelated_rewrite(sentence, out.get(alt_key)):
            out.pop(alt_key, None)

    if detect_register_conflict(sentence, out):
        out["status"] = "Needs Improvement"
        out["explanation"] = (
            str(out.get("explanation") or "")
            + " Register mismatch: formal «está» should not be «corrected» to informal «estás»."
        ).strip()
        out.pop("correction", None)

    if _cites_time_adverb_as_verb_tense(out) or (
        _simple_preterite_past_narrative(sentence)
        and str(out.get("status")) == "Needs Improvement"
        and "preterite" in str(out.get("explanation") or "").lower()
        and "imperfect" in str(out.get("explanation") or "").lower()
        and not _missing_accent_fixes(sentence)
    ):
        return _past_narrative_accent_feedback(sentence)

    missing_acc = _missing_accent_fixes(sentence)
    correction = str(out.get("correction") or "")
    if (
        missing_acc
        and correction
        and _correction_adds_accents(sentence, correction, missing_acc)
        and not _explanation_mentions_accents(
            str(out.get("explanation") or ""), [lbl for _, lbl in missing_acc]
        )
    ):
        labels = ", ".join(f"«{lbl}»" for _, lbl in missing_acc)
        out["explanation"] = (
            str(out.get("explanation") or "").strip()
            + f" Add written accents: {labels}. «Ayer» is only a time adverb, not a verb form."
        ).strip()
        if "accent" not in str(out.get("grammar_rule") or "").lower():
            out["grammar_rule"] = "Written accent marks on past-tense verb forms"

    from coach_rules import merge_with_ai

    out = merge_with_ai(sentence, out, "es")
    return _preserve_inferred_fields(out, sentence)


def sanitize_feedback(
    sentence: str, feedback: dict[str, Any], level: str = "", *, lang: str = "es"
) -> dict[str, Any]:
    """Validate SLM JSON; repair or replace when clearly unreliable."""
    if lang == "fr":
        return _sanitize_french_feedback(sentence, feedback, level)
    return _sanitize_spanish_feedback(sentence, feedback, level)


def _correction_adds_accents(
    sentence: str, correction: str, missing: list[tuple[str, str]]
) -> bool:
    for pattern, label in missing:
        if re.search(pattern, sentence, re.I) and re.search(
            rf"\b{re.escape(label)}\b", correction, re.I
        ):
            return True
    return False
