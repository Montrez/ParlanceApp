#!/usr/bin/env python3
"""Wire guide-es.html / guide-fr.html to guide-ui.js (binary EN ↔ native chrome).

Translates instructional chrome (sidebar labels, nicknames, rule titles, when-rules,
buttons, intro). Leaves conjugation tables, Spanish/French tense names, and example
sentences untouched — those are subject-matter content, not interface chrome.

Usage:
  python3 scripts/retrofit_guide_chrome.py
"""
from __future__ import annotations

import html as html_lib
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "Parlance" / "web"
DOCS = ROOT / "docs"

# Shared chrome that appears in both guides (EN → ES, EN → FR)
SHARED: dict[str, tuple[str, str]] = {
    "A1 Foundations": ("A1 Fundamentos", "A1 Fondamentaux"),
    "A2 Building Blocks": ("A2 Bloques básicos", "A2 Éléments de base"),
    "B1 Tenses": ("B1 Tiempos", "B1 Temps"),
    "B2 Tenses": ("B2 Tiempos", "B2 Temps"),
    "C1 Tenses": ("C1 Tiempos", "C1 Temps"),
    "C2 Mastery": ("C2 Dominio", "C2 Maîtrise"),
    "Reference": ("Referencia", "Référence"),
    "Key Contrasts": ("Contrastes clave", "Contrastes clés"),
    "A1 → C2 Deep Reference": ("Referencia profunda A1 → C2", "Référence approfondie A1 → C2"),
    "The Core Rule": ("La regla básica", "La règle de base"),
    "Mnemonic": ("Regla mnemotécnica", "Moyen mnémotechnique"),
    "Back to Journal": ("Volver al diario", "Retour au journal"),
    "☰ Contents": ("☰ Contenido", "☰ Sommaire"),
    "Good News": ("Buena noticia", "Bonne nouvelle"),
    "Interpreter Note": ("Nota para intérpretes", "Note pour interprètes"),
    "Side-by-Side Contrasts": ("Contrastes lado a lado", "Contrastes côte à côte"),
    "Daily routines": ("Rutinas diarias", "Routines quotidiennes"),
    "General truths": ("Verdades generales", "Vérités générales"),
    "Current actions": ("Acciones actuales", "Actions en cours"),
    "Emotions": ("Emociones", "Émotions"),
    "Plans": ("Planes", "Projets"),
    "Intentions": ("Intenciones", "Intentions"),
    "Predictions": ("Predicciones", "Prédictions"),
    "How to Form It": ("Cómo se forma", "Comment le former"),
    "The Golden Rule": ("La regla de oro", "La règle d'or"),
    "Recognition Only": ("Solo reconocimiento", "Reconnaissance seulement"),
}

# guide-es specific (EN → ES). FR column unused for native wiring.
ES_ONLY: dict[str, str] = {
    "Conjugaciones": "Conjugaciones",
    "A1 → C2 Spanish Conjugation Guide": "Guía de conjugación española A1 → C2",
    "Rules, irregular verbs, trigger words, and real examples for every key tense. Click any tense in the sidebar to jump there.":
        "Reglas, verbos irregulares, palabras clave y ejemplos reales para cada tiempo importante. Haz clic en cualquier tiempo del menú para ir allí.",
    "Present Tense · A1": "Presente · A1",
    "Essential Distinction · A1": "Distinción esencial · A1",
    "Verb Patterns · A1": "Patrones verbales · A1",
    "Verb Types · A2": "Tipos de verbos · A2",
    "Near Future · A2": "Futuro próximo · A2",
    "Verb Patterns · A2": "Patrones verbales · A2",
    "Past Tense · B1": "Pasado · B1",
    "Future Tense · B1": "Futuro · B1",
    "Conditional · B1/B2": "Condicional · B1/B2",
    "Subjunctive · B1/B2": "Subjuntivo · B1/B2",
    "Past Perfect · B2": "Pluscuamperfecto · B2",
    "Subjunctive · B2": "Subjuntivo · B2",
    "Future Perfect · B2": "Futuro perfecto · B2",
    "Conditional Perfect · B2": "Condicional perfecto · B2",
    "Past Perfect Subjunctive · C1": "Subjuntivo pluscuamperfecto · C1",
    "Advanced Structures · C1": "Estructuras avanzadas · C1",
    "Professional Register · C1": "Registro profesional · C1",
    "Archaic / Legal · C2": "Arcaico / legal · C2",
    "Archaic Subjunctive · C2": "Subjuntivo arcaico · C2",
    "Native Mastery · C2": "Dominio nativo · C2",
    "Key Structure · Reference": "Estructura clave · Referencia",
    "Critical Contrast · Reference": "Contraste crítico · Referencia",
    '"The present tense" — what you do, what\'s happening now, general truths':
        "«El presente» — lo que haces, lo que ocurre ahora, verdades generales",
    "\"Both mean 'to be' but are used differently\" — ser for identity/essence, estar for states/location":
        "«Ambos significan “ser/estar”, pero se usan distinto» — ser para identidad/esencia, estar para estados/ubicación",
    '"Boot verbs" — the stem vowel changes for all forms EXCEPT nosotros and vosotros':
        "«Verbos de bota» — la vocal del radical cambia en todas las formas EXCEPTO nosotros y vosotros",
    '"Reflexive verbs" — the action is done to oneself':
        "«Verbos reflexivos» — la acción se hace a uno mismo",
    '"Going to do" — the near future, plans, and intentions':
        "«Ir a hacer» — el futuro próximo, planes e intenciones",
    '"To like" — but backwards! The thing liked is the subject':
        "«Gustar» — ¡al revés! La cosa que gusta es el sujeto",
    '"The simple past" — something happened and it\'s done':
        "«El pretérito» — algo ocurrió y ya terminó",
    '"The background past" — what was ongoing, habitual, or how things were':
        "«El imperfecto» — lo que estaba en curso, era habitual o cómo eran las cosas",
    '"Have done" — recent past still connected to now':
        "«Haber hecho» — pasado reciente aún conectado con el ahora",
    '"Will do" — predictions, promises, and future facts':
        "«Haré» — predicciones, promesas y hechos futuros",
    '"Would do" — hypotheticals, politeness, reported speech':
        "«Haría» — hipótesis, cortesía, discurso referido",
    '"The mood of subjectivity" — wishes, doubt, emotion, necessity':
        "«El modo de la subjetividad» — deseos, duda, emoción, necesidad",
    '"Had done" — the past before the past':
        "«Había hecho» — el pasado anterior a otro pasado",
    '"If only... / I wished... / If I were..." — the gateway tense':
        "«Ojalá… / Desearía… / Si yo fuera…» — el tiempo puente",
    '"Will have done" — completed before a future moment':
        "«Habré hecho» — completado antes de un momento futuro",
    '"Would have done" — the result of an impossible past condition':
        "«Habría hecho» — resultado de una condición pasada imposible",
    '"Had done (in a subjunctive context)" — regret, impossible past wishes, and Type 3 si clauses':
        "«Hubiera hecho» — arrepentimiento, deseos pasados imposibles y si de tipo 3",
    "Verb periphrases — the structures that make your Spanish sound native":
        "Perífrasis verbales — las estructuras que hacen que tu español suene nativo",
    "Formal vs informal — the register shifts that interpreters must master":
        "Formal vs informal — los cambios de registro que el intérprete debe dominar",
    '"If it should be" — archaic tense alive in law, proverbs, and formal documents':
        "«Si fuere» — tiempo arcaico vivo en la ley, proverbios y documentos formales",
    "Style and nuance — the final frontier of interpreter-level Spanish":
        "Estilo y matiz — la frontera final del español a nivel de intérprete",
    "The most important distinction in Spanish":
        "La distinción más importante del español",
    "Near future with present": "Futuro próximo con presente",
    "SER — Identity": "SER — Identidad",
    "SER — Origin": "SER — Origen",
    "SER — Characteristics": "SER — Características",
    "ESTAR — Location": "ESTAR — Ubicación",
    "ESTAR — Emotions/states": "ESTAR — Emociones/estados",
    "ESTAR — Temporary conditions": "ESTAR — Condiciones temporales",
    "o→ue in action": "o→ue en acción",
    "e→ie in action": "e→ie en acción",
    "e→i in action": "e→i en acción",
    "Reciprocal actions": "Acciones recíprocas",
    "Singular — one thing": "Singular — una cosa",
    "Plural — multiple things": "Plural — varias cosas",
    "Infinitive — an activity": "Infinitivo — una actividad",
    "Encantar — to love (stronger)": "Encantar — amar (más fuerte)",
    "A specific completed event": "Un evento concreto y terminado",
    "A series of sequential past events": "Una serie de eventos pasados en secuencia",
    "An event that interrupted an ongoing action": "Un evento que interrumpió una acción en curso",
    "Actions within a time frame still in progress": "Acciones dentro de un marco temporal aún en curso",
    "Habitual / repeated past actions (\"used to\")": "Acciones pasadas habituales/repetidas («solía»)",
    "Describing background conditions / states": "Describir condiciones o estados de fondo",
    "Life experiences (ever/never)": "Experiencias de vida (alguna vez/nunca)",
    "Past action with present consequence": "Acción pasada con consecuencia presente",
    "Recent past with still-relevant result": "Pasado reciente con resultado aún relevante",
    "Future plans or predictions": "Planes o predicciones futuras",
    "Promises and orders (formal)": "Promesas y órdenes (formal)",
    "Probability / speculation about the present (B2!)": "Probabilidad / especulación sobre el presente (¡B2!)",
    "Hypothetical consequences (the \"then\" in if/then)": "Consecuencias hipotéticas (el «entonces» del si/entonces)",
    "Polite requests (quisiera = softer version of quiero)": "Peticiones corteses (quisiera = versión más suave de quiero)",
    "Reported speech (what someone said they \"would\" do)": "Discurso referido (lo que alguien dijo que «haría»)",
    "Wishes and desires (querer que, desear que, esperar que)": "Deseos (querer que, desear que, esperar que)",
    "Emotions about others' actions (alegrarse de que, temer que)": "Emociones sobre acciones ajenas (alegrarse de que, temer que)",
    "Doubt or denial (no creer que, dudar que)": "Duda o negación (no creer que, dudar que)",
    "Future time clauses (cuando, en cuanto, hasta que, antes de que)": "Cláusulas de tiempo futuro (cuando, en cuanto, hasta que, antes de que)",
    "Action completed before another past action": "Acción completada antes de otra acción pasada",
    "Reported past events (backstory in narratives)": "Eventos pasados referidos (trasfondo narrativo)",
    "como si (as if) — always triggers Imp. Subj.": "como si — siempre dispara el imperfecto de subjuntivo",
    "Wishes about the present (Ojalá + Imp. Subj.)": "Deseos sobre el presente (Ojalá + imperfecto de subjuntivo)",
    "If-clauses with unreal/hypothetical present situations (Si + Imp. Subj. → Conditional)":
        "Oraciones condicionales irreales/hipotéticas (Si + imperfecto de subjuntivo → Condicional)",
    "Probability in the past (B2)": "Probabilidad en el pasado (B2)",
    "Type 3 si clauses — the impossible past condition": "Si de tipo 3 — la condición pasada imposible",
    "Impossible past wishes (Ojalá + Pluscuam. Subj.)": "Deseos pasados imposibles (Ojalá + pluscuamperfecto de subjuntivo)",
    "Trigger Words → use Presente": "Palabras clave → usa Presente",
    "Trigger Words → use Ir + a + Infinitivo": "Palabras clave → usa Ir + a + Infinitivo",
    "Trigger Words → use Indefinido": "Palabras clave → usa Indefinido",
    "Trigger Words → use Imperfecto": "Palabras clave → usa Imperfecto",
    "Trigger Words → use Perfecto": "Palabras clave → usa Perfecto",
    "Common Reflexive Verbs": "Verbos reflexivos comunes",
    "Similar Verbs (same pattern as gustar)": "Verbos similares (mismo patrón que gustar)",
    "Verb Meaning Changes": "Cambios de significado del verbo",
    "Spain vs Latin America": "España vs Latinoamérica",
    "Key Irregulars in Subjuntivo Presente": "Irregulares clave del subjuntivo presente",
    "Never use Subjuntivo after si in if-clauses": "Nunca uses subjuntivo tras si en oraciones condicionales",
    "-ra vs -se forms": "Formas -ra vs -se",
    "Interpreter Tip: deber vs deber de": "Consejo: deber vs deber de",
    "The C2 Interpreter Standard": "El estándar C2 del intérprete",
    "What Are Perífrasis?": "¿Qué son las perífrasis?",
    "Key Perífrasis for Interpreters": "Perífrasis clave para intérpretes",
    "Why Register Matters": "Por qué importa el registro",
    "Common Anglicisms to Avoid": "Anglicismos comunes a evitar",
    "Register Elevation: Informal → Professional": "Elevación de registro: informal → profesional",
    "Nuanced Word Choice": "Elección de palabras con matiz",
    "Advanced Discourse Connectors": "Conectores discursivos avanzados",
    "The Three Si Clause Patterns": "Los tres patrones de las cláusulas con si",
    "Legal conditions — \"whoever / if someone should\"": "Condiciones legales — «quienquiera / si alguien…»",
    "Famous proverbs and set phrases": "Proverbios famosos y frases hechas",
    "→ French Conjugation Guide": "→ Guía de conjugación francesa",
    "Si Clauses (If/Then)": "Cláusulas con si (Si/Entonces)",
}

# guide-fr specific (EN → FR)
FR_ONLY: dict[str, str] = {
    "Conjugaisons": "Conjugaisons",
    "A1 → C2 French Conjugation Guide": "Guide de conjugaison française A1 → C2",
    "Full rules, irregular verbs, trigger words, and real examples. Use the sidebar to navigate between tenses.":
        "Règles complètes, verbes irréguliers, mots déclencheurs et exemples réels. Utilisez le menu pour naviguer entre les temps.",
    "Present Tense · A1": "Présent · A1",
    "Essential Verbs · A1": "Verbes essentiels · A1",
    "Spelling Changes · A1": "Changements d'orthographe · A1",
    "Reflexive Verbs · A2": "Verbes pronominaux · A2",
    "Near Future · A2": "Futur proche · A2",
    "Grammar · A2": "Grammaire · A2",
    "Past Tense · B1": "Passé · B1",
    "Future Tense · B1": "Futur · B1",
    "Conditional · B1/B2": "Conditionnel · B1/B2",
    "Subjunctive · B1/B2": "Subjonctif · B1/B2",
    "Past Perfect · B2": "Plus-que-parfait · B2",
    "Future Perfect · B2": "Futur antérieur · B2",
    "Conditional Perfect · B2": "Conditionnel passé · B2",
    "Past Subjunctive · B2": "Subjonctif passé · B2",
    "Literary Past · C1": "Passé littéraire · C1",
    "Literary Subjunctive · C1": "Subjonctif littéraire · C1",
    "Professional Register · C1": "Registre professionnel · C1",
    "Literary Past Perfect · C2": "Passé antérieur · C2",
    "Advanced Structures · C2": "Structures avancées · C2",
    "Native Mastery · C2": "Maîtrise native · C2",
    "Critical Contrast · Reference": "Contraste critique · Référence",
    "Key Structure · Reference": "Structure clé · Référence",
    '"The present tense" — what you do, what\'s happening now, general truths':
        "« Le présent » — ce que vous faites, ce qui se passe maintenant, les vérités générales",
    '"The two most essential verbs" — être (to be) and avoir (to have) are irregular and used everywhere':
        "« Les deux verbes les plus essentiels » — être et avoir sont irréguliers et partout",
    '"Stem-changing verbs" — some -ER verbs change spelling in certain forms to preserve pronunciation':
        "« Verbes à radical variable » — certains verbes en -ER changent d'orthographe pour la prononciation",
    '"Reflexive verbs" — the action reflects back on the subject using me, te, se, nous, vous, se':
        "« Verbes pronominaux » — l'action revient sur le sujet avec me, te, se, nous, vous, se",
    '"The near future" — what you\'re going to do. Use aller (conjugated) + infinitive':
        "« Le futur proche » — ce que vous allez faire. Aller (conjugué) + infinitif",
    '"Partitive articles" — du, de la, de l\', des express an unspecified quantity: "some" or "any"':
        "« Articles partitifs » — du, de la, de l', des expriment une quantité indéterminée",
    '"The completed past" — what happened, what you did':
        "« Le passé composé » — ce qui s'est passé, ce que vous avez fait",
    '"The background past" — what was ongoing, habitual, or descriptive':
        "« L'imparfait » — ce qui était en cours, habituel ou descriptif",
    '"Will do" — also expresses probability/supposition':
        "« Ferai » — exprime aussi la probabilité / la supposition",
    '"Would do" — hypotheticals, politeness, and reported speech':
        "« Ferais » — hypothèses, politesse et discours rapporté",
    '"The mood of uncertainty" — wishes, doubts, emotions, and future time clauses':
        "« Le mode de l'incertitude » — souhaits, doutes, émotions et propositions temporelles futures",
    '"Had done" — the past before the past':
        "« Avais/étais fait » — le passé avant un autre passé",
    '"Will have done" — also used to speculate about the recent past':
        "« Aurai/serai fait » — aussi pour spéculer sur le passé récent",
    '"Would have done" — the result of an impossible past condition':
        "« Aurais/serais fait » — résultat d'une condition passée impossible",
    '"That he may have done" — past action in a subjunctive context':
        "« Qu'il ait/soit fait » — action passée dans un contexte subjonctif",
    '"The literary past" — used in formal writing, literature, and historical texts':
        "« Le passé simple » — écriture formelle, littérature et textes historiques",
    '"That he might do" — the literary form of the past subjunctive':
        "« Qu'il fît » — forme littéraire du subjonctif passé",
    "Formal vs informal — the register shifts that interpreters must master":
        "Formel vs informel — les changements de registre que l'interprète doit maîtriser",
    '"As soon as he had done" — a rare literary tense you\'ll encounter in formal texts':
        "« Dès qu'il eut fait » — temps littéraire rare dans les textes formels",
    '"Had done (literary)" — the literary equivalent of the plus-que-parfait':
        "« Eut fait » — équivalent littéraire du plus-que-parfait",
    "Style and nuance — the final frontier of interpreter-level French":
        "Style et nuance — la frontière finale du français au niveau interprète",
    "The most important distinction in French — master this and your past tense becomes natural":
        "La distinction la plus importante en français — maîtrisez-la et votre passé devient naturel",
    "Trigger Expressions → Présent": "Expressions déclencheurs → Présent",
    "Trigger Expressions → Futur Proche": "Expressions déclencheurs → Futur proche",
    "Trigger Expressions → Passé Composé": "Expressions déclencheurs → Passé composé",
    "Trigger Expressions → Imparfait": "Expressions déclencheurs → Imparfait",
    "Trigger Expressions → Futur Simple": "Expressions déclencheurs → Futur simple",
    "Être — Identity": "Être — Identité",
    "Être — Origin": "Être — Origine",
    "Être — Description": "Être — Description",
    "Avoir — Possession": "Avoir — Possession",
    "Avoir — Age (French uses avoir!)": "Avoir — Âge (le français utilise avoir !)",
    "Avoir — Expressions": "Avoir — Expressions",
    "e→è pattern": "Schéma e→è",
    "é→è pattern": "Schéma é→è",
    "Double consonant pattern": "Schéma de double consonne",
    "The être verbs — DR MRS VANDERTRAMPP": "Les verbes être — DR MRS VANDERTRAMPP",
    "Avoir Expressions — Watch Out!": "Expressions avec avoir — Attention !",
    "The Spelling Quirk": "La particularité orthographique",
    "The Double Role": "Le double rôle",
    "The Film Analogy": "L'analogie du film",
    "The Movie Metaphor": "La métaphore du film",
    "The Two-Subject Rule": "La règle des deux sujets",
    "Futur Simple vs. Futur Proche": "Futur simple vs futur proche",
    "Passé Simple vs Passé Composé": "Passé simple vs passé composé",
    "The Interpreter Standard": "Le standard de l'interprète",
    "Beyond Grammar": "Au-delà de la grammaire",
    "→ Spanish Conjugation Guide": "→ Guide de conjugaison espagnole",
    "Si Clauses (If/Then)": "Propositions en si (Si/Alors)",
    "A single completed past event": "Un événement passé unique et achevé",
    "A sequence of events (one after another)": "Une séquence d'événements (l'un après l'autre)",
    "An event that interrupted an ongoing situation": "Un événement qui a interrompu une situation en cours",
    "An action repeated a specific number of times": "Une action répétée un nombre précis de fois",
    "Habitual/repeated actions (used to)": "Actions habituelles/répétées (« j'avais l'habitude de »)",
    "Descriptions and background scenes": "Descriptions et scènes de fond",
    "Ongoing action when something else happened": "Action en cours quand autre chose est arrivée",
    "States of mind / emotions / conditions in the past": "États d'esprit / émotions / conditions au passé",
    "Telling the time or age in the past": "Dire l'heure ou l'âge au passé",
    "In narratives — setting up backstory": "Dans les récits — poser le contexte",
    "Future plans and predictions": "Projets et prédictions futurs",
    "Probability Use (B2)": "Usage de probabilité (B2)",
    "Hypothetical consequences (\"would\") — the \"then\" in si clauses":
        "Conséquences hypothétiques (« ferais ») — le « alors » des si",
    "Polite requests (softer than present tense)": "Demandes polies (plus douces que le présent)",
    "Reported speech (\"said that he would\")": "Discours rapporté (« a dit qu'il ferait »)",
    "Unverified information / journalistic conditional (B2)": "Information non vérifiée / conditionnel journalistique (B2)",
    "Wishes and desires (vouloir que, désirer que, souhaiter que)": "Souhaits et désirs (vouloir que, désirer que, souhaiter que)",
    "Emotions (être content/triste/surpris que, craindre que, regretter que)":
        "Émotions (être content/triste/surpris que, craindre que, regretter que)",
    "Doubt and denial (douter que, ne pas croire que, ne pas penser que)":
        "Doute et négation (douter que, ne pas croire que, ne pas penser que)",
    "Necessity and importance (il faut que, il est important que, il est nécessaire que)":
        "Nécessité et importance (il faut que, il est important que, il est nécessaire que)",
    "Conjunctions that always trigger subjonctif": "Conjonctions qui déclenchent toujours le subjonctif",
    "After quand/lorsque/dès que in future contexts (KEY rule!)":
        "Après quand/lorsque/dès que dans un contexte futur (règle clé !)",
    "Superlatives and unique expressions (le seul, le premier, le plus…)":
        "Superlatifs et expressions uniques (le seul, le premier, le plus…)",
    "Action completed before another past event": "Action achevée avant un autre événement passé",
    "Reporting something someone hadn't done yet": "Rapporter quelque chose que quelqu'un n'avait pas encore fait",
    "In si clauses — impossible past conditions (Type 3)": "Dans les si — conditions passées impossibles (type 3)",
    "Emotions about past events (me alegró que, lamenté que)": "Émotions sur des événements passés",
    "Action in progress when something else happened": "Action en cours quand autre chose est arrivée",
    "Narrative events in literature": "Événements narratifs en littérature",
    "Historical accounts and formal journalism": "Récits historiques et journalisme formel",
    "Formal/elevated register — speeches and ceremonies": "Registre formel/élevé — discours et cérémonies",
    "Literary sequence of tenses (past main verb + subjunctive)":
        "Concordance littéraire des temps (verbe principal passé + subjonctif)",
    "Concordance des temps (Sequence of Tenses)": "Concordance des temps",
    "Polite softening (imparfait de politesse)": "Adoucissement poli (imparfait de politesse)",
    "After quantity expressions": "Après les expressions de quantité",
    "Negative": "Négation",
    "Abstract": "Abstrait",
    "Food": "Nourriture",
    "Reciprocal": "Réciproque",
    "Note: ir a + infinitive is more common in speech": "Note : aller + infinitif est plus courant à l'oral",
    "Critical for Legal Interpreters": "Critique pour les interprètes juridiques",
    "The Three Si Clause Patterns": "Les trois schémas des propositions en si",
    "Key Perífrasis for Interpreters": "Périphrases clés pour interprètes",
    "Common Anglicisms to Avoid": "Anglicismes courants à éviter",
    "Register Elevation: Informal → Professional": "Élévation de registre : informel → professionnel",
    "Nuanced Word Choice": "Choix de mots nuancé",
    "Advanced Discourse Connectors": "Connecteurs discursifs avancés",
    "Three types — each expressing a different level of likelihood":
        "Trois types — chacun exprime un niveau de vraisemblance différent",
    "Three patterns — each expressing a different level of likelihood":
        "Trois schémas — chacun exprime un niveau de vraisemblance différent",
    "Polite requests — much softer than present tense": "Demandes polies — bien plus douces que le présent",
    "como si + past unreal (as if something had happened)": "comme si + irréel passé",
    "Repeated action a specific number of times": "Action répétée un nombre précis de fois",
    '"That he might have done" — the most elevated literary form':
        "« Qu'il eût fait » — la forme littéraire la plus élevée",
    "Wishes/emotions/doubt expressed in the past (Sequence of Tenses)":
        "Souhaits/émotions/doutes exprimés au passé (concordance des temps)",
}


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def attr_escape(s: str) -> str:
    return html_lib.escape(s, quote=True)


def wrap_text_element(el, en: str, native: str) -> None:
    """Replace element's text children with a single bilingual-tagged string.
    Preserves nested badge spans by wrapping only direct text or wrapping the whole
    element when it has no nested structure we need to keep.
    """
    # If element has only text (and maybe whitespace), set attributes on el itself
    badges = el.find_all(class_=re.compile(r"nav-badge|level-pill"))
    if badges:
        # Wrap the non-badge text in a span
        # Collect text nodes that aren't inside badges
        text_bits = []
        for child in list(el.children):
            if isinstance(child, NavigableString):
                t = str(child).strip()
                if t:
                    text_bits.append(t)
                    child.replace_with("")
            elif getattr(child, "name", None) == "span" and child.get("class") and any(
                "badge" in c or "pill" in c for c in child.get("class", [])
            ):
                continue
            elif getattr(child, "name", None) == "span" and not (child.get("class") and any(
                "badge" in c or "pill" in c for c in child.get("class", [])
            )):
                # existing inner span (e.g. tense name) — leave Spanish/French names alone
                return
        if not text_bits:
            return
        en_text = normalize(" ".join(text_bits))
        # Prefer full en from map if we only got partial
        span = soup_new_tag(el, "span")
        span["data-t-en"] = en
        span["data-t-native"] = native
        span.string = en
        # insert before first badge
        badges[0].insert_before(span)
        badges[0].insert_before(" ")
        return

    el["data-t-en"] = en
    el["data-t-native"] = native
    el.clear()
    el.append(en)


def soup_new_tag(el, name: str):
    return el.page.new_tag(name) if hasattr(el, "page") else BeautifulSoup("", "html.parser").new_tag(name)


def apply_bilingual(soup: BeautifulSoup, native_lang: str, translations: dict[str, str]) -> int:
    """Apply data-t-en / data-t-native to chrome elements. Returns count wrapped."""
    count = 0
    chrome_classes = [
        "nav-section-label", "intro-title", "intro-desc", "section-chapter",
        "tense-nickname", "rule-box-title", "trigger-box-title", "tip-label",
        "when-rule", "contrast-title",
    ]

    def lookup(text: str) -> tuple[str, str] | None:
        key = normalize(text)
        if key in translations:
            return key, translations[key]
        # try without trailing CEFR markers already stripped
        return None

    for cls in chrome_classes:
        for el in soup.select(f".{cls}"):
            if el.has_attr("data-t-en"):
                continue
            raw = normalize(el.get_text(" ", strip=True))
            # strip CEFR badges from matching key
            key = re.sub(r"\s+(A1|A2|B1|B2|C1|C2|B1/B2)\s*$", "", raw).strip()
            # Also try full raw
            pair = lookup(raw) or lookup(key)
            if not pair:
                # section-chapter often is "Present Tense · A1" — try as-is with · level
                continue
            en, native = pair
            wrap_simple(el, en, native)
            count += 1

    # sidebar logo
    logo = soup.select_one(".sidebar-logo")
    if logo:
        for child in logo.find_all(["h1", "p"], recursive=False):
            if child.has_attr("data-t-en"):
                continue
            raw = normalize(child.get_text(" ", strip=True))
            pair = lookup(raw)
            if pair:
                wrap_simple(child, pair[0], pair[1])
                count += 1

    for sel in [".back-btn", ".mobile-nav-btn"]:
        for el in soup.select(sel):
            if el.has_attr("data-t-en") or el.find(attrs={"data-t-en": True}):
                continue
            raw = normalize(el.get_text(" ", strip=True))
            pair = lookup(raw)
            if pair:
                wrap_simple(el, pair[0], pair[1])
                count += 1

    return count


def wrap_simple(el, en: str, native: str) -> None:
    """Set bilingual attrs on element; keep nested badges if present."""
    badges = [
        c for c in el.find_all(True, recursive=True)
        if c.get("class") and any("badge" in x or "pill" in x for x in c.get("class", []))
    ]
    if badges:
        # Don't clear badges — put attrs on a wrapper span for text only if structure is simple
        # Most section-chapter / when-rule / tip-label have no badges
        pass
    # For elements that contain only text (or text + badges as siblings of nav-item handled separately)
    children = [c for c in el.children if not (isinstance(c, NavigableString) and not str(c).strip())]
    only_text = all(isinstance(c, NavigableString) for c in children)
    if only_text or not badges:
        el["data-t-en"] = en
        el["data-t-native"] = native
        # Preserve structure: if has nested non-badge tags with Spanish content, don't wipe
        nested_tags = [c for c in el.find_all(True, recursive=False) if c.name]
        if nested_tags and not badges:
            # has nested structure (e.g. contrast cells) — only set if leaf-like
            if el.name in ("div", "p", "h1", "h2", "button") and not nested_tags:
                el.clear()
                el.append(en)
            else:
                # leaf text element with possible <em>/<strong>
                has_only_inline = all(t.name in ("em", "strong", "i", "b", "br") for t in nested_tags)
                if has_only_inline or not nested_tags:
                    el.clear()
                    el.append(en)
        else:
            # keep badges
            for b in badges:
                b.extract()
            el.clear()
            el.append(en)
            for b in badges:
                el.append(" ")
                el.append(b)


def wire_guide_ui(soup: BeautifulSoup, native_lang: str, storage_key: str, title_en: str, title_native: str) -> None:
    # Ensure guide-ui.js script
    if not soup.find("script", src=re.compile(r"guide-ui\.js")):
        tag = soup.new_tag("script", src="guide-ui.js")
        # insert before last script or before </body>
        scripts = soup.find_all("script")
        if scripts:
            scripts[0].insert_before(tag)
        else:
            soup.body.append(tag)

    init_js = f"""
GuideUI.init({{
  nativeLang: '{native_lang}',
  storageKey: '{storage_key}',
  titleEn: {title_en!r},
  titleNative: {title_native!r},
}});
"""
    # Prepend to first inline script that isn't guide-ui, or add new
    inline = None
    for s in soup.find_all("script"):
        if s.get("src"):
            continue
        inline = s
        break
    if inline:
        existing = inline.string or ""
        if "GuideUI.init" not in existing:
            inline.string = init_js + "\n" + existing
    else:
        s = soup.new_tag("script")
        s.string = init_js
        soup.body.append(s)


def build_translations(native_lang: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for en, (es, fr) in SHARED.items():
        out[en] = es if native_lang == "es" else fr
    if native_lang == "es":
        out.update(ES_ONLY)
    else:
        out.update(FR_ONLY)
    return out


def process(filename: str, native_lang: str, storage_key: str, title_en: str, title_native: str) -> None:
    path = WEB / filename
    raw = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(raw, "html.parser")
    # Fix BeautifulSoup's wrap_simple needing page ref — use soup.new_tag via monkey
    translations = build_translations(native_lang)
    n = apply_bilingual(soup, native_lang, translations)
    wire_guide_ui(soup, native_lang, storage_key, title_en, title_native)
    # BeautifulSoup can mangle formatting; write with formatter
    out = str(soup)
    # Prefer keep doctype
    if not out.lstrip().startswith("<!DOCTYPE"):
        out = "<!DOCTYPE html>\n" + out
    path.write_text(out, encoding="utf-8")
    docs = DOCS / filename
    if docs.exists() or True:
        docs.write_text(out, encoding="utf-8")
    print(f"{filename}: wrapped ~{n} chrome nodes, GuideUI wired, mirrored to docs/")


def main() -> None:
    process(
        "guide-es.html",
        "es",
        "parlance_guide_read_es_grammar",
        "Spanish A1→C2 Deep Guide",
        "Guía profunda de español A1→C2",
    )
    process(
        "guide-fr.html",
        "fr",
        "parlance_guide_read_fr_grammar",
        "French A1→C2 Conjugation Guide",
        "Guide de conjugaison française A1→C2",
    )


if __name__ == "__main__":
    main()
