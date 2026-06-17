"""Contextual coach tips — cite the learner's words, not generic connector advice."""

from __future__ import annotations

import re
from typing import Any

from coach_rules import _normalize


def _has_subordinator(text: str) -> bool:
    n = _normalize(text)
    if "el hecho de que" in n:
        return True
    return any(
        m in n
        for m in (
            " porque ", " pues ", " que ", " qu ", " cuando ", " si ", " aunque ",
            " mientras ", " lo cual ", " donde ", " como ", " sino ",
        )
    )


def _snippet(sentence: str, pattern: str, *, pad: int = 18) -> str:
    m = re.search(pattern, sentence, re.I)
    if not m:
        return ""
    start = max(0, m.start() - pad)
    end = min(len(sentence), m.end() + pad)
    chunk = sentence[start:end].strip(" .,;")
    if start > 0:
        chunk = "…" + chunk
    if end < len(sentence):
        chunk = chunk + "…"
    return chunk


def _correction_delta(sentence: str, correction: str) -> str | None:
    if not correction or _normalize(correction) == _normalize(sentence):
        return None
    # Short contrast: show correction if not too long
    if len(correction) <= 120:
        return correction
    return correction[:117] + "…"


_GENERIC_TIP_PHRASES = (
    "add «porque»",
    "add porque",
    "subordinate clause",
    "lo cual",
    "link ideas in one flowing",
    "fix each bullet in order",
    "tighten vocabulary and connectors",
    "prefer precise verbs and connectors",
)


def tip_is_generic(tip: str | None) -> bool:
    if not tip or len(tip.strip()) < 12:
        return True
    lower = tip.lower()
    return any(p in lower for p in _GENERIC_TIP_PHRASES)


def tip_for_improvement(
    sentence: str,
    issues: list[dict[str, Any]],
    correction: str | None,
    *,
    lang: str = "es",
) -> str:
    """Needs Improvement — quote what they wrote and how to fix it."""
    if lang != "es":
        return _correction_delta(sentence, correction or "") or "Apply the fixes above in order."

    ids = {i.get("id", "") for i in issues}
    parts: list[str] = []

    if "para_purpose_infinitive" in ids:
        snip = _snippet(sentence, r"\b\w+\s+a\s+(ver|hacer|comprar|ir)\b") or _snippet(
            sentence, r"\ba\s+(ver|hacer|comprar|ir)\b"
        )
        corr_snip = ""
        if correction:
            corr_snip = _snippet(correction, r"\bpara\s+(ver|hacer|comprar|ir)\b")
        if snip and corr_snip:
            parts.append(f"In «{snip}», use **para** before the infinitive — e.g. «{corr_snip}».")
        elif snip:
            parts.append(f"In «{snip}», purpose before an infinitive needs **para**, not **a**.")
        else:
            parts.append("Before an infinitive of purpose, use **para**, not bare **a**.")

    if "greeting_vocative_order" in ids or "como_es_wellbeing" in ids:
        snip = _snippet(sentence, r"[Cc][óo]mo\s+es[^.!?]{0,40}") or _snippet(
            sentence, r"usted\s+d[ií]a\s+se[nñ]or"
        )
        if snip:
            parts.append(
                f"Your opening «{snip}» should be **¿Cómo está usted hoy, señor?** — "
                "**estar** for wellbeing, natural vocative order."
            )
        else:
            parts.append("Use **¿Cómo está usted hoy, señor?** — not **Cómo es** + scrambled word order.")

    if "que_clause_infinitive_subjunctive" in ids:
        snip = _snippet(sentence, r"\b(espero|quiero|deseo|necesito|ojal[aá])\s+que[^.!?]{0,45}")
        if snip:
            parts.append(
                f"In «{snip}», the verb after **que** needs subjunctive (**vayan**, not bare **ir**)."
            )
        else:
            parts.append("After «espero que» / «quiero que», use subjunctive in the subordinate clause — not an infinitive.")

    if "si_clause_conditional_protasis" in ids:
        snip = _snippet(sentence, r"\bsi\b[^.!?]{0,45}")
        if snip:
            parts.append(
                f"In «{snip}», the **si**-clause needs imperfect subjunctive (**tuviera**), not conditional (**tendría**)."
            )

    if "leismo_echar_de_menos_feminine" in ids or any(i.startswith("leismo") for i in ids):
        snip = _snippet(sentence, r"\b(le|les)\s+echo\s+de\s+menos\b")
        if snip:
            parts.append(f"Change «{snip}» to **la/lo echo de menos** — direct object, not **le**.")

    if "accent_comi" in ids or any("accent" in i for i in ids):
        snip = _snippet(sentence, r"\bcomi\b")
        if snip:
            parts.append(f"Add the tilde in «{snip}» → **comí** (preterite -í form).")

    if "punctuation_question" in ids:
        snip = _snippet(sentence, r"[^.!?]*\?")
        if snip:
            parts.append(f"Add **¿** at the start of the question in «{snip}».")

    if "gender_muchas_cosas" in ids:
        parts.append("Match gender: **muchas cosas**, not **muchos cosas**.")

    if "por_para_trabajo" in ids:
        snip = _snippet(sentence, r"\bpor\s+\w*\s*trabajo\b")
        if snip:
            parts.append(f"Purpose: change «{snip}» to use **para (el) trabajo**.")

    if parts:
        return " ".join(parts[:2])

    if delta := _correction_delta(sentence, correction or ""):
        return f"Revise to keep your meaning: «{delta}»"

    first = issues[0].get("issue") if issues else ""
    return f"Fix: {first}" if first else "Apply each grammar fix while keeping your original meaning."


def tip_for_excellent(
    sentence: str,
    *,
    next_alt: str | None = None,
    y_coordinated: bool = False,
    lang: str = "es",
) -> str:
    """Excellent — one concrete upgrade using their words, not generic connector advice."""
    if lang != "es":
        return "Keep your meaning; adjust formality to match the interpreting setting."

    text = sentence.strip()
    norm = _normalize(text)

    if y_coordinated:
        _parts = re.split(r"\s+y\s+", text, maxsplit=1, flags=re.I)
        _left = _parts[0].strip(" .")
        _right = _parts[1].strip(" .") if len(_parts) > 1 else ""
        if next_alt and _normalize(next_alt) != _normalize(text):
            # Reject porque-fragments — they teach bad Spanish
            _is_porque_fragment = re.search(
                r"\bporque\s+(la|el|los|las|mi|tu|su|un|una)\s+\w+\.?\s*$",
                next_alt,
                re.I,
            )
            if not _is_porque_fragment and _left:
                return (
                    f"You link ideas with «{_left}… y …» — for formal interpreting, "
                    f"try your own words in: «{next_alt}»"
                )
        # Fallback: fragment detected or no usable next_alt — use sequencing connectors
        if _left and _right:
            return (
                f"With «y» chains, add sequencing: e.g. «{_left} y después {_right}.» "
                f"or subordination: «{_left} antes de ir a {_right}.»"
            )

    m = re.search(r"(?i)\b(quiero\s+[^.!?]{3,50})", text)
    if m:
        snip = m.group(1).strip()
        if re.search(r"\bpara\s+\w", snip, re.I):
            return (
                f"«{snip}» already states purpose — add a time frame («esta tarde», «mañana») "
                "if the interpreter note needs when."
            )
        return (
            f"«{snip}» is clear — if this is a goal, add **para** + infinitive "
            f"(«{snip} para …») or a time phrase for the session."
        )

    m = re.search(r"(?i)\b(me gusta|te gusta|le gusta|gusta)\s+[^.!?]{3,40}", text)
    if m:
        return f"Solid «{m.group(0).strip()}» — specify when or how often if the context is scheduling."

    m = re.search(
        r"(?i)\b((?:fui|fue|hice|hizo|comí|comi|trabajé|trabaje|estuve|estuvo)[^.!?]{0,35})",
        text,
    )
    if m:
        return (
            f"Good past-tense narrative with «{m.group(1).strip()}» — "
            "keep a time adverb («ayer», «esta mañana») in professional notes."
        )

    if re.search(r"\b(senor|senora)\b", norm) and re.search(r"\besta\b", norm):
        snip = _snippet(text, r"[Hh]ola[^.!?]{0,35}") or _snippet(text, r"[Cc][óo]mo\s+est[aá][^.!?]{0,20}")
        if snip:
            return f"Formal «{snip}» — set off the vocative with commas: «Buenos días, señora, ¿cómo está?»"
        return "Formal usted + «está» fits polite address — use commas around the vocative."

    if re.search(r"\b(hubiera|tuviera|vengas|haga|tenga)\b", norm):
        snip = _snippet(text, r"[^.!?]{0,30}\b(que|si)\b[^.!?]{0,40}")
        if snip:
            return f"Strong subjunctive in «{snip}» — keep trigger verb and mood aligned in your rewrite."

    if _has_subordinator(text):
        content = re.findall(r"\b[\wáéíóúñ]{5,}\b", text)
        skip = {"porque", "cuando", "aunque", "mientras", "donde", "desde", "hasta", "sobre"}
        vocab = [w for w in content if _normalize(w) not in skip][:2]
        if vocab:
            return (
                f"Subordination is already working — sharpen domain terms "
                f"(e.g. «{'», «'.join(vocab)}») for interpreter precision."
            )

    words = re.findall(r"\b[\wáéíóúñ]{4,}\b", text)
    if len(words) >= 2:
        return (
            f"Your line with «{words[0]}» and «{words[1]}» reads cleanly — "
            "adjust one verb or noun only if the register must be more formal."
        )

    return "Keep your meaning; change only the word or form flagged above, if any."
