"""Exam resources, tips, and role-based center lookup for Parlance Discord."""
from __future__ import annotations

from discord_channel_catalog import EXAM_CATEGORY, channel_mention

# channel name → exam role keys served by that channel
EXAM_CHANNELS: dict[str, list[str]] = {
    "dele": ["DELE"],
    "siele": ["SIELE"],
    "delf": ["DELF"],
    "dalf": ["DALF"],
    "tcf": ["TCF"],
}

EXAM_ROLE_NAMES = frozenset({"DELE", "SIELE", "DELF", "DALF", "TCF"})

# exam role → channel name
ROLE_TO_CHANNEL: dict[str, str] = {
    "DELE": "dele",
    "SIELE": "siele",
    "DELF": "delf",
    "DALF": "dalf",
    "TCF": "tcf",
}

# Spanish vs French center directories
EXAM_FAMILY: dict[str, str] = {
    "DELE": "spanish",
    "SIELE": "spanish",
    "DELF": "french",
    "DALF": "french",
    "TCF": "french",
}

EXAM_OVERVIEWS: dict[str, str] = {
    "dele": """**DELE** — Official Spanish diploma from Instituto Cervantes. Levels A1–C2 (CEFR). No expiry.

**How to register:**
1. Find a center near you → https://examenes.cervantes.es/es/dele/donde
2. Select your country, exam session, and level
3. Contact the center listed — they handle registration directly
   *(If you're in Spain, you can also register online through that same portal)*""",
    "siele": """**SIELE** — Digital Spanish certificate, modular format, results in days. Valid 5 years.

**How to register:**
1. Go to → https://www.siele.org/en/reservas
2. Select your country and exam modality (SIELE Global = all 4 skills, €155)
3. Pick a date and center — or choose **remote** if no center is near you
   *(Find centers only: https://www.siele.org/en/encuentre-su-centro)*""",
    "delf": """**DELF** — Official French diploma for non-native speakers. Levels A1–B2. Lifetime validity.

**How to register:**
1. Find a center near you → https://www.france-education-international.fr/en/centres-d-examen/liste
2. Select your country from the dropdown
3. Contact the center listed — they set their own dates and fees""",
    "dalf": """**DALF** — Advanced French diploma. Levels C1–C2. Often required for French universities. Lifetime validity.

**How to register:**
1. Find a center near you → https://www.france-education-international.fr/en/centres-d-examen/liste
2. Select your country from the dropdown
3. Contact the center — they handle registration and payment directly""",
    "tcf": """**TCF** — French proficiency test used for immigration, university admission, and placement (includes TCF Canada).

**How to register:**
1. Find a center near you → https://www.france-education-international.fr/en/centres-d-examen/liste
2. Select your country and filter by TCF
3. Contact the center for dates and registration""",
}

EXAM_TIPS: dict[str, str] = {
    "dele": """**Prep tips**
• Timed writing practice — match your target level (B2 vs C1 feel different)
• Register (tú/usted) and subjunctive triggers are common weak spots
• Use Parlance Coach for sentence-level feedback; post longer paragraphs here for peer review
• Book your seat early — popular centers fill up""",
    "siele": """**Prep tips**
• SIELE is computer-based — practice typing accented characters
• You can take modules separately; plan which sections you need
• Shorter prep cycle than DELE — good if you need a score soon""",
    "delf": """**Prep tips**
• DELF is section-based — you must pass each skill; don't neglect oral prep
• Structured paragraphs: intro, development, conclusion
• Connectors (cependant, en effet, néanmoins) matter at B2+
• B2 is the usual step before DALF""",
    "dalf": """**Prep tips**
• C1/C2 expect nuance, register control, and argumentation
• Read opinion pieces and summarize arguments in your own words
• DALF writing is long-form — build stamina with timed sessions""",
    "tcf": """**Prep tips**
• TCF is often used for immigration or placement — confirm which TCF variant you need
• Shorter than DELF/DALF in some formats — check your center's offering""",
}

DELE_COUNTRIES: list[dict[str, str]] = [
    {"label": "United States", "value": "us", "url": "https://examenes.cervantes.es/es/dele/donde", "note": "Search by country then state — NYC, Chicago, LA, Miami, Houston."},
    {"label": "Mexico", "value": "mx", "url": "https://examenes.cervantes.es/es/dele/donde", "note": "CDMX, Guadalajara, Monterrey."},
    {"label": "Spain", "value": "es", "url": "https://examenes.cervantes.es/es/dele/donde", "note": "Widest network — search by city."},
    {"label": "Colombia", "value": "co", "url": "https://examenes.cervantes.es/es/dele/donde", "note": "Bogotá, Medellín, Cali."},
    {"label": "Argentina", "value": "ar", "url": "https://examenes.cervantes.es/es/dele/donde", "note": "Buenos Aires and regional centers."},
    {"label": "Brazil", "value": "br", "url": "https://examenes.cervantes.es/es/dele/donde", "note": "São Paulo, Rio."},
    {"label": "Canada", "value": "ca", "url": "https://examenes.cervantes.es/es/dele/donde", "note": "Toronto, Vancouver, Montreal."},
    {"label": "United Kingdom", "value": "uk", "url": "https://examenes.cervantes.es/es/dele/donde", "note": "London, Manchester, Edinburgh."},
    {"label": "France", "value": "fr", "url": "https://examenes.cervantes.es/es/dele/donde", "note": "Instituto Cervantes cities."},
    {"label": "Germany", "value": "de", "url": "https://examenes.cervantes.es/es/dele/donde", "note": "Berlin, Munich, Hamburg."},
    {"label": "China", "value": "cn", "url": "https://examenes.cervantes.es/es/dele/donde", "note": "Beijing, Shanghai."},
    {"label": "Another country", "value": "other", "url": "https://examenes.cervantes.es/es/dele/donde", "note": "Filter by country on the Cervantes portal."},
]

DELF_COUNTRIES: list[dict[str, str]] = [
    {"label": "United States", "value": "us", "url": "https://www.france-education-international.fr/en/centres-d-examen/liste", "note": "Alliance Française in major cities — select USA from the dropdown."},
    {"label": "Canada", "value": "ca", "url": "https://www.france-education-international.fr/en/centres-d-examen/liste", "note": "Montreal, Quebec City, Ottawa, Toronto."},
    {"label": "France", "value": "fr", "url": "https://www.france-education-international.fr/en/centres-d-examen/liste", "note": "Search by département."},
    {"label": "Belgium", "value": "be", "url": "https://www.france-education-international.fr/en/centres-d-examen/liste", "note": "Brussels, Liège."},
    {"label": "Switzerland", "value": "ch", "url": "https://www.france-education-international.fr/en/centres-d-examen/liste", "note": "Geneva, Lausanne, Zurich."},
    {"label": "Morocco", "value": "ma", "url": "https://www.france-education-international.fr/en/centres-d-examen/liste", "note": "Casablanca, Rabat, Marrakech."},
    {"label": "Tunisia", "value": "tn", "url": "https://www.france-education-international.fr/en/centres-d-examen/liste", "note": "Tunis, Sfax."},
    {"label": "Vietnam", "value": "vn", "url": "https://www.france-education-international.fr/en/centres-d-examen/liste", "note": "Hanoi, Ho Chi Minh City."},
    {"label": "United Kingdom", "value": "uk", "url": "https://www.france-education-international.fr/en/centres-d-examen/liste", "note": "London AF + regional."},
    {"label": "Germany", "value": "de", "url": "https://www.france-education-international.fr/en/centres-d-examen/liste", "note": "Berlin, Munich, Hamburg."},
    {"label": "Mexico", "value": "mx", "url": "https://www.france-education-international.fr/en/centres-d-examen/liste", "note": "CDMX, Guadalajara."},
    {"label": "Another country", "value": "other", "url": "https://www.france-education-international.fr/en/centres-d-examen/liste", "note": "Select your country from the dropdown."},
]

SIELE_COUNTRIES: list[dict[str, str]] = [
    {"label": "United States", "value": "us", "url": "https://www.siele.org/en/encuentre-su-centro", "note": "Search by city on SIELE's center finder."},
    {"label": "Mexico", "value": "mx", "url": "https://www.siele.org/en/encuentre-su-centro", "note": "Multiple authorized centers."},
    {"label": "Spain", "value": "es", "url": "https://www.siele.org/en/encuentre-su-centro", "note": "Large center list."},
    {"label": "Colombia", "value": "co", "url": "https://www.siele.org/en/encuentre-su-centro", "note": "Bogotá and other cities."},
    {"label": "Another country", "value": "other", "url": "https://www.siele.org/en/encuentre-su-centro", "note": "Full center list on siele.org."},
]

# region role → country values to prioritize in dynamic finder
REGION_COUNTRY_VALUES: dict[str, list[str]] = {
    "North America": ["us", "ca", "mx"],
    "Latin America": ["mx", "co", "ar", "br"],
    "Europe": ["fr", "de", "uk", "be", "ch", "es"],
    "Asia-Pacific": ["cn", "vn"],
    "Africa": ["ma", "tn"],
    "Middle East": ["other"],
    "Oceania": ["other"],
}

REGION_EXAM_HINTS: dict[str, str] = {
    "North America": f"Set your exam roles, then head to {channel_mention('find-a-seat')} — we'll suggest US and Canada centers.",
    "Latin America": f"Check {channel_mention('find-a-seat')} for centers in Mexico, Colombia, or Argentina.",
    "Europe": f"{channel_mention('find-a-seat')} can point you to France, UK, Germany, or Spain.",
    "Asia-Pacific": f"Use {channel_mention('find-a-seat')} — China and Vietnam are in the directory.",
    "Africa": f"{channel_mention('find-a-seat')} lists Morocco and Tunisia for French exams.",
    "Middle East": f"Use {channel_mention('find-a-seat')} and pick your country on the official directory.",
    "Oceania": f"Use {channel_mention('find-a-seat')} — pick “Another country” for local partners.",
}

EMBED_ROLES_INTRO = "Introduce yourself"
EMBED_ROLES_MORE = "Optional focus"
EMBED_FIND_SEAT = "Find a test center"
EMBED_PASSED = "Share your pass"
EMBED_EXAM_CHANNEL = "About this exam"

FIND_SEAT_INTRO = (
    f"Uses your **exam** and **region** roles from {channel_mention('choose-roles')} to suggest a center near you.\n\n"
    "Set those roles first if you haven't — then press the button below. "
    "You'll pick a country, then your state or city to narrow it down."
)

PASSED_INTRO = (
    "Passed DELE, DELF, or another exam? Tell us — level, language, and what helped most. "
    "It encourages people still preparing."
)
