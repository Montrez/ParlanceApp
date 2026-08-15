#!/usr/bin/env python3
"""Authoring source for Parlance/web/dialect-en-pairs.js.

Each region pair is written by hand. Do not generate pairs from a shared
housing/food/phone template. Run:

  python3 scripts/build_dialect_en_pairs.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Parlance" / "web" / "dialect-en-pairs.js"


def t(en: str, es: str, fr: str) -> dict:
    return {"en": en, "es": es, "fr": fr}


def item(point, why, local, formal, note=None, lexicon=None):
    out = {
        "point": point,
        "why": why,
        "local": {"from": local[0], "to": local[1]},
        "formal": {"from": formal[0], "to": formal[1]},
    }
    if note:
        out["note"] = note
    if lexicon:
        out["lexicon"] = lexicon
    return out


def lex(idea, frm, to):
    return {"idea": idea, "from": frm, "to": to}


NAMES = {
    "us": t("United States", "Estados Unidos", "États-Unis"),
    "uk": t("United Kingdom", "Reino Unido", "Royaume-Uni"),
    "ie": t("Ireland", "Irlanda", "Irlande"),
    "au": t("Australia", "Australia", "Australie"),
    "nz": t("New Zealand", "Nueva Zelanda", "Nouvelle-Zélande"),
    "ca": t("Canada", "Canadá", "Canada"),
    "za": t("South Africa", "Sudáfrica", "Afrique du Sud"),
    "in": t("India", "India", "Inde"),
    "cb": t("Caribbean", "Caribe", "Caraïbes"),
}

ORDER = ["us", "uk", "ie", "au", "nz", "ca", "za", "in", "cb"]

LABELS = {
    "en": {
        "local": "Local / everyday",
        "formal": "Formal / official",
        "idea": "What it is",
        "selectYours": "Select your variety",
        "selectTheirs": "Select their variety",
        "sameNote": (
            "Same national variety. The country still has internal regions: "
            "US South vs New York, Scotland vs London, island vs island. "
            "Check Trap words and the profiles below for slang and grammar "
            "inside the country. Do not flatten those into one accent."
        ),
    },
    "es": {
        "local": "Local / cotidiano",
        "formal": "Formal / oficial",
        "idea": "Qué es",
        "selectYours": "Selecciona tu variedad",
        "selectTheirs": "Selecciona su variedad",
        "sameNote": (
            "Misma variedad nacional. El país sigue teniendo regiones internas. "
            "Revisa «Palabras trampa» y los perfiles. No aplanes esos rasgos "
            "en un solo acento."
        ),
    },
    "fr": {
        "local": "Local / quotidien",
        "formal": "Formel / officiel",
        "idea": "De quoi il s’agit",
        "selectYours": "Sélectionnez votre variété",
        "selectTheirs": "Sélectionnez sa variété",
        "sameNote": (
            "Même variété nationale. Le pays a encore des régions internes. "
            "Consultez « Mots pièges » et les profils. N’aplatissez pas ces "
            "traits en un seul accent."
        ),
    },
}

PAIRS: dict[str, list] = {}


def add(key: str, *items):
    PAIRS[key] = list(items)


# --- United States ↔ United Kingdom ---------------------------------------
add(
    "us|uk",
    item(
        t(
            "Floors will put someone on the wrong storey in a fire or a hospital.",
            "Los pisos pueden poner a alguien en la planta equivocada en un incendio o un hospital.",
            "Les étages peuvent envoyer quelqu’un au mauvais niveau dans un incendie ou un hôpital.",
        ),
        t(
            "In the US, the first floor is street level. In the UK, the first floor is one flight up. The UK street level is the ground floor. If a witness says “first floor flat” and you render it as US first floor, the crew goes to the wrong door.",
            "En EE. UU., the first floor es la planta de la calle. En el RU, the first floor es un tramo de escaleras arriba. La planta de la calle es the ground floor. Si un testigo dice «first floor flat» y lo interpretas como first floor estadounidense, el equipo va a la puerta equivocada.",
            "Aux É.-U., the first floor est le niveau de la rue. Au RU, the first floor est un étage plus haut. Le niveau de la rue est the ground floor. Si un témoin dit « first floor flat » et que vous rendez le first floor américain, l’équipe va à la mauvaise porte.",
        ),
        (
            "The smoke is on the first floor. That’s where we live.",
            "The smoke is on the first floor. That’s the floor above the shop.",
        ),
        (
            "The smoke is on the ground floor, street level.",
            "The smoke is on the first floor, one storey above the ground floor.",
        ),
        t(
            "On a record, say ground floor or second storey. Do not leave first floor bare.",
            "En un expediente, di ground floor o second storey. No dejes first floor suelto.",
            "Au dossier, dites ground floor ou second storey. Ne laissez pas first floor seul.",
        ),
    ),
    item(
        t(
            "pants, rubber, table, and public school do not travel.",
            "pants, rubber, table y public school no viajan.",
            "pants, rubber, table et public school ne voyagent pas.",
        ),
        t(
            "US pants are trousers. UK pants are often underwear. A US classroom rubber is an eraser; in the UK rubber is a condom. To table a motion in the US is to postpone it; in the UK it is to put it on the agenda. A US public school is state-funded; a UK public school is fee-paying. These four have wrecked meetings and school placements.",
            "En EE. UU. pants son pantalones. En el RU pants suele ser ropa interior. Un rubber de aula en EE. UU. es una goma; en el RU es un condón. Table a motion en EE. UU. es posponerla; en el RU es ponerla en el orden del día. Una public school estadounidense es pública; en el RU es privada de pago. Estas cuatro han hundido reuniones y escolarizaciones.",
            "Aux É.-U., pants veut dire pantalon. Au RU, pants sont souvent des sous-vêtements. Un rubber de classe US est une gomme ; au RU, c’est un préservatif. Table a motion aux É.-U. reporte ; au RU, cela met à l’ordre du jour. Une public school US est publique ; au RU, elle est payante. Ces quatre mots ont déjà fait échouer des réunions et des inscriptions.",
        ),
        (
            "He bought new pants. The teacher needs a rubber. They tabled the motion. She goes to public school.",
            "He bought new trousers. Don’t say rubber for an eraser. They tabled the motion, so it is being discussed. She goes to a public school, which is private and expensive.",
        ),
        (
            "He purchased new trousers. The teacher needs an eraser. They postponed the motion. She attends a state-funded school.",
            "He purchased new trousers. The teacher needs an eraser. They placed the motion on the agenda. She attends an independent, fee-paying school.",
        ),
        t(
            "If education or a meeting is on the record, name the institution type. Never leave public school or table unexplained.",
            "Si hay educación o una reunión en el expediente, nombra el tipo de institución. Nunca dejes public school o table sin explicar.",
            "Si l’éducation ou une réunion est au dossier, nommez le type d’établissement. Ne laissez jamais public school ou table sans explication.",
        ),
        [
            lex(t("trousers", "pantalones", "pantalon"), "pants", "trousers (pants = underwear)"),
            lex(t("eraser", "goma de borrar", "gomme"), "rubber / eraser", "eraser (rubber = condom)"),
            lex(t("postpone a motion", "posponer una moción", "reporter une motion"), "table the motion", "shelve the motion"),
            lex(t("put on the agenda", "poner en el orden del día", "mettre à l’ordre du jour"), "bring up / introduce", "table the motion"),
            lex(t("state school", "escuela pública", "école publique"), "public school", "state school"),
            lex(t("fee-paying school", "escuela de pago", "école payante"), "private school", "public school"),
        ],
    ),
    item(
        t(
            "Healthcare: ER is not A&E, and a specialist is not a consultant.",
            "Salud: ER no es A&E, y un specialist no es un consultant.",
            "Santé : ER n’est pas A&E, et un specialist n’est pas un consultant.",
        ),
        t(
            "US emergency room is UK accident and emergency (A&E). A US specialist is often a UK consultant. UK surgery can mean the GP’s office, not an operating theatre. NHS, insurance, copay, and referral do not map one-to-one. If you keep ER in a UK hospital, staff look for a door that is not labelled that way.",
            "La emergency room de EE. UU. es accident and emergency (A&E) en el RU. Un specialist estadounidense suele ser un consultant británico. En el RU, surgery puede ser el consultorio del médico de cabecera, no un quirófano. NHS, insurance, copay y referral no se equivalen uno a uno. Si dejas ER en un hospital británico, el personal busca una puerta que no se llama así.",
            "L’emergency room US est l’accident and emergency (A&E) britannique. Un specialist US est souvent un consultant UK. Au RU, surgery peut désigner le cabinet du généraliste, pas un bloc. NHS, insurance, copay et referral ne se recouvrent pas. Si vous laissez ER dans un hôpital britannique, le personnel cherche une porte qui n’existe pas sous ce nom.",
        ),
        (
            "We took him to the ER. The specialist said we need a referral for the surgery.",
            "We took him to A&E. The consultant said we need a referral. The GP surgery is around the corner.",
        ),
        (
            "He was taken to the emergency department. The attending physician requested a referral for the operation.",
            "He was taken to accident and emergency. The consultant requested a referral. The general practice is nearby.",
        ),
        None,
        [
            lex(t("emergency department", "urgencias", "urgences"), "ER / emergency room", "A&E / casualty"),
            lex(t("senior hospital doctor", "médico hospitalario senior", "médecin hospitalier senior"), "specialist / attending", "consultant"),
            lex(t("family doctor’s office", "consultorio", "cabinet"), "doctor’s office", "GP surgery"),
            lex(t("operating room", "quirófano", "bloc opératoire"), "OR / operating room", "theatre / operating theatre"),
            lex(t("pharmacist", "farmacéutico", "pharmacien"), "pharmacist / drugstore", "chemist"),
        ],
    ),
    item(
        t(
            "Law: attorney, solicitor, barrister, and defendant captions.",
            "Derecho: attorney, solicitor, barrister y el encabezado del acusado.",
            "Droit : attorney, solicitor, barrister et l’intitulé de la défense.",
        ),
        t(
            "US attorney covers a wide role. In England and Wales a solicitor prepares the case and a barrister usually speaks in the higher courts. US defense is UK defence in the caption. Discovery is disclosure. A US motion may be a UK application. Do not turn a solicitor into an attorney on a UK record unless you also name the role.",
            "Attorney en EE. UU. cubre un rol amplio. En Inglaterra y Gales, un solicitor prepara el caso y un barrister suele hablar en los tribunales superiores. Defense en EE. UU. es defence en el RU. Discovery es disclosure. Una motion estadounidense puede ser una application británica. No conviertas a un solicitor en attorney en un expediente británico sin nombrar el rol.",
            "Attorney aux É.-U. couvre un rôle large. En Angleterre et au pays de Galles, un solicitor prépare le dossier et un barrister plaide souvent devant les juridictions supérieures. Defense US = defence UK. Discovery = disclosure. Une motion US peut être une application UK. Ne transformez pas un solicitor en attorney sur un dossier britannique sans nommer le rôle.",
        ),
        (
            "My attorney filed a motion. The defense wants discovery.",
            "My solicitor instructed a barrister. The defence wants disclosure.",
        ),
        (
            "Counsel for the defendant filed a motion. The defense requested discovery.",
            "The solicitor instructed counsel. The defence requested disclosure.",
        ),
        None,
        [
            lex(t("lawyer (general)", "abogado (general)", "avocat (général)"), "attorney / lawyer", "solicitor / barrister (name the role)"),
            lex(t("pre-trial evidence", "pruebas previas", "preuves avant procès"), "discovery", "disclosure"),
            lex(t("request to the court", "petición al tribunal", "demande au tribunal"), "motion", "application / motion"),
            lex(t("spelling on the caption", "ortografía en el encabezado", "orthographe de l’intitulé"), "defense", "defence"),
        ],
    ),
    item(
        t(
            "Dates: 3/4 is 4 March in the US and 3 April in the UK.",
            "Fechas: 3/4 es el 4 de marzo en EE. UU. y el 3 de abril en el RU.",
            "Dates : 3/4 est le 4 mars aux É.-U. et le 3 avril au RU.",
        ),
        t(
            "US dates are month-day-year. UK dates are day-month-year. A charging document, a prescription, or a flight that says 3/4/26 is a different day. Spoken “the fourth of March” is safe. So is 4 March 2026.",
            "En EE. UU. las fechas son mes-día-año. En el RU son día-mes-año. Un escrito de cargos, una receta o un vuelo con 3/4/26 es otro día. «The fourth of March» es seguro. También 4 March 2026.",
            "Aux É.-U., les dates sont mois-jour-année. Au RU, jour-mois-année. Un acte, une ordonnance ou un vol qui indique 3/4/26 tombe un autre jour. « The fourth of March » est sûr. 4 March 2026 aussi.",
        ),
        (
            "The hearing is 3/4. That’s March fourth.",
            "The hearing is 3/4. That’s the third of April.",
        ),
        (
            "The hearing is 4 March 2026.",
            "The hearing is 3 April 2026.",
        ),
        t(
            "Write the month in letters on any record that will be read in the other country.",
            "Escribe el mes en letras en cualquier expediente que se lea en el otro país.",
            "Écrivez le mois en lettres sur tout dossier lu dans l’autre pays.",
        ),
    ),
    item(
        t(
            "Grammar that is standard on one side and marked on the other.",
            "Gramática estándar de un lado y marcada del otro.",
            "Grammaire standard d’un côté, marquée de l’autre.",
        ),
        t(
            "US I have gotten is standard. UK I have got is the normal past participle; gotten sounds American. UK collective nouns often take a plural verb: the team are. US the team is. UK at the weekend / in hospital / at university. US on the weekend / in the hospital / in college. None of these is an error. Do not “fix” them when you are interpreting the speaker’s voice.",
            "I have gotten es estándar en EE. UU. En el RU, I have got es el participio normal; gotten suena estadounidense. En el RU los colectivos suelen llevar verbo en plural: the team are. En EE. UU., the team is. RU: at the weekend / in hospital / at university. EE. UU.: on the weekend / in the hospital / in college. Ninguno es un error. No los «arregles» cuando interpretas la voz del hablante.",
            "I have gotten est standard aux É.-U. Au RU, I have got est le participe normal ; gotten sonne américain. Au RU, les collectifs prennent souvent le pluriel : the team are. Aux É.-U., the team is. RU : at the weekend / in hospital / at university. É.-U. : on the weekend / in the hospital / in college. Aucun n’est une faute. Ne les « corrigez » pas quand vous interprétez la voix du locuteur.",
        ),
        (
            "I’ve gotten worse. The team is winning. I’m in the hospital. See you on the weekend.",
            "I’ve got worse. The team are winning. I’m in hospital. See you at the weekend.",
        ),
        (
            "My condition has deteriorated. The team is winning. I am in hospital. I will see you at the weekend.",
            "My condition has deteriorated. The team are winning. I am in hospital. I will see you at the weekend.",
        ),
    ),
    item(
        t(
            "Everyday lexicon that still belongs in the booth.",
            "Léxico cotidiano que sigue importando en cabina.",
            "Lexique quotidien qui compte encore en cabine.",
        ),
        t(
            "These are not slang. They are the normal word. If the listener will not understand, keep the speaker’s word and add the other country’s word once. Do not silently replace every flat with apartment when the speaker is British.",
            "Esto no es argot. Es la palabra normal. Si el oyente no va a entender, conserva la palabra del hablante y añade la del otro país una vez. No sustituyas en silencio cada flat por apartment si el hablante es británico.",
            "Ce n’est pas de l’argot. C’est le mot normal. Si l’auditeur ne comprendra pas, gardez le mot du locuteur et ajoutez une fois le mot de l’autre pays. Ne remplacez pas en silence chaque flat par apartment si le locuteur est britannique.",
        ),
        (
            "The truck is on the freeway. Take the elevator to my apartment. I’m on vacation.",
            "The lorry is on the motorway. Take the lift to my flat. I’m on holiday.",
        ),
        (
            "The commercial vehicle is on the interstate. Take the lift to the apartment. I will be on annual leave.",
            "The goods vehicle is on the motorway. Take the lift to the flat. I will be on annual leave.",
        ),
        None,
        [
            lex(t("apartment", "apartamento", "appartement"), "apartment", "flat"),
            lex(t("elevator", "ascensor", "ascenseur"), "elevator", "lift"),
            lex(t("truck", "camión", "camion"), "truck", "lorry"),
            lex(t("highway", "autopista", "autoroute"), "freeway / highway", "motorway"),
            lex(t("time off", "vacaciones", "congés"), "vacation", "holiday"),
            lex(t("fries", "papas fritas", "frites"), "fries", "chips"),
            lex(t("potato chips", "patatas de bolsa", "chips"), "chips", "crisps"),
            lex(t("cookie", "galleta dulce", "biscuit sucré"), "cookie", "biscuit"),
            lex(t("bathroom", "baño", "toilettes"), "restroom / bathroom", "loo / toilet"),
            lex(t("flashlight", "linterna", "lampe torche"), "flashlight", "torch"),
            lex(t("trunk of a car", "maletero", "coffre"), "trunk", "boot"),
            lex(t("hood of a car", "capó", "capot"), "hood", "bonnet"),
        ],
    ),
    item(
        t(
            "Pronunciation that changes the word people think they heard.",
            "Pronunciación que cambia la palabra que la gente cree haber oído.",
            "Prononciation qui change le mot que l’on croit avoir entendu.",
        ),
        t(
            "route can rhyme with out in the US and root in the UK. A US vitamin has a first vowel like “eye”; UK often has “i” as in sit. privacy, oregano, schedule (sk vs sh), and lieutenant (loo-tenant vs lef-tenant) are the ones that make a listener ask you to repeat. Repeat the word, then spell it if the record needs it.",
            "route puede rimar con out en EE. UU. y con root en el RU. Vitamin en EE. UU. empieza como «eye»; en el RU suele ser la i de sit. privacy, oregano, schedule (sk vs sh) y lieutenant (loo-tenant vs lef-tenant) son las que hacen que el oyente te pida que repitas. Repite la palabra y, si el expediente lo necesita, delétraela.",
            "route peut rimer avec out aux É.-U. et avec root au RU. Vitamin US a une première voyelle « eye » ; au RU, souvent « i » de sit. privacy, oregano, schedule (sk vs sh) et lieutenant (loo-tenant vs lef-tenant) font répéter. Répétez le mot, puis épellez-le si le dossier l’exige.",
        ),
        (
            "Take Route 9. The lieutenant scheduled the vitamin.",
            "Take the route that rhymes with root. The left-tenant scheduled the vitamin.",
        ),
        (
            "Take Route 9, R-O-U-T-E 9. The lieutenant scheduled the vitamin supplement.",
            "Take the route, R-O-U-T-E. The lieutenant scheduled the vitamin supplement.",
        ),
    ),
)

add(
    "us|ie",
    item(
        t(
            "grand is fine in Ireland and a thousand dollars in the US.",
            "grand es «bien» en Irlanda y mil dólares en EE. UU.",
            "grand veut dire « ça va » en Irlande et mille dollars aux É.-U.",
        ),
        t(
            "Irish That’s grand means the situation is acceptable. US a grand is $1,000. If a client says “it’s grand” after a settlement offer, do not write “one thousand dollars.” If a US speaker says “it’ll be a grand,” do not write “the client agrees.”",
            "En irlandés, That’s grand significa que la situación es aceptable. En EE. UU., a grand son 1 000 $. Si un cliente dice «it’s grand» tras una oferta, no escribas «mil dólares». Si un estadounidense dice «it’ll be a grand», no escribas «el cliente acepta».",
            "En irlandais, That’s grand signifie que c’est acceptable. Aux É.-U., a grand = 1 000 $. Si un client dit « it’s grand » après une offre, n’écrivez pas « mille dollars ». Si un Américain dit « it’ll be a grand », n’écrivez pas « le client accepte ».",
        ),
        ("That’ll be a grand.", "That’s grand. We’re sound."),
        ("That will be one thousand dollars.", "That is acceptable. We are satisfied."),
    ),
    item(
        t(
            "ye is plural you. after + -ing is a recent-past in Irish English.",
            "ye es you en plural. after + -ing es pasado reciente en inglés irlandés.",
            "ye est le you pluriel. after + -ing est un passé récent en anglais irlandais.",
        ),
        t(
            "Are ye coming? is standard informal Irish English, not a failed you. I’m after booking it means I have just booked it, not that I want to book it later. US after booking would sound like a plan. Render the Irish after-perfect as a present perfect on a US record if the listener will misread it.",
            "Are ye coming? es inglés irlandés informal estándar, no un you fallido. I’m after booking it significa que acabo de reservarlo, no que quiero reservarlo después. En EE. UU., after booking suena a un plan. En un expediente estadounidense, interpreta el after-perfect irlandés como present perfect si el oyente lo va a malentender.",
            "Are ye coming ? est de l’anglais irlandais informel standard, pas un you raté. I’m after booking it = je viens de réserver, pas « je vais réserver ». Aux É.-U., after booking sonne comme un projet. Sur un dossier US, rendez le after-perfect irlandais par un present perfect si l’auditeur se trompera.",
        ),
        (
            "Are you all coming? I’m just booking it now.",
            "Are ye coming? I’m after booking it.",
        ),
        (
            "Are you all attending? I am booking it now.",
            "Are you all attending? I have just booked it.",
        ),
    ),
    item(
        t(
            "press, craic, and the HSE are Irish, not cute UK English.",
            "press, craic y el HSE son irlandeses, no inglés británico simpático.",
            "press, craic et le HSE sont irlandais, pas de l’anglais britannique amusant.",
        ),
        t(
            "A press is a cupboard. The craic is the atmosphere or a good time, not a crime. Health is the HSE, not the NHS and not US insurance. Courts and Gardaí have their own names. Ireland is not the UK.",
            "Un press es un armario. The craic es el ambiente o un buen rato, no un delito. La salud es el HSE, no el NHS ni un seguro estadounidense. Los tribunales y la Garda tienen sus propios nombres. Irlanda no es el RU.",
            "Un press est un placard. The craic est l’ambiance ou un bon moment, pas un crime. La santé, c’est le HSE, pas le NHS ni une assurance US. Tribunaux et Gardaí ont leurs noms. L’Irlande n’est pas le RU.",
        ),
        (
            "The glasses are in the cupboard. We had a good time. I went to the ER.",
            "The glasses are in the press. The craic was mighty. I went to A&E / the hospital under the HSE.",
        ),
        (
            "The glasses are in the cupboard. We had an enjoyable evening. I attended the emergency department.",
            "The glasses are in the cupboard. We had an enjoyable evening. I attended the emergency department under the HSE.",
        ),
        None,
        [
            lex(t("cupboard", "armario", "placard"), "cupboard / cabinet", "press"),
            lex(t("a good time", "un buen rato", "un bon moment"), "a good time / fun", "the craic"),
            lex(t("health service", "servicio de salud", "service de santé"), "ER / insurance", "HSE / A&E"),
            lex(t("police", "policía", "police"), "police / cop", "Garda / Gardaí"),
        ],
    ),
)

add(
    "us|au",
    item(
        t(
            "thongs are flip-flops. root can be vulgar. chips must be named.",
            "thongs son chanclas. root puede ser vulgar. chips hay que nombrarlas.",
            "thongs sont des tongs. root peut être vulgaire. chips doit être nommé.",
        ),
        t(
            "US thongs are underwear. Australian thongs are flip-flops. US root for a team is fine; Australian root as a verb is sexual. Australian chips are often fries; a packet of chips can still be crisps. Ask, then put the object on the record.",
            "En EE. UU. thongs es ropa interior. En Australia son chanclas. Root for a team es correcto en EE. UU.; en Australia root como verbo es sexual. Las chips australianas suelen ser fries; un packet of chips puede ser crisps. Pregunta y pon el objeto en el expediente.",
            "Aux É.-U., thongs = sous-vêtement. En Australie, ce sont des tongs. Root for a team est correct aux É.-U. ; en Australie, root verbe est sexuel. Les chips australiennes sont souvent des frites ; un packet of chips peut être des chips. Demandez, puis nommez l’objet au dossier.",
        ),
        (
            "She wore a thong. We’ll root for them. I want chips.",
            "She wore thongs to the beach. Don’t say root. I want hot chips.",
        ),
        (
            "She wore underwear. We will support the team. I would like potato chips.",
            "She wore flip-flops. We will support the team. I would like hot chips, meaning fried potatoes.",
        ),
    ),
    item(
        t(
            "Australian public school is state-funded, like the US, unlike the UK.",
            "La public school australiana es estatal, como en EE. UU., no como en el RU.",
            "La public school australienne est publique, comme aux É.-U., contrairement au RU.",
        ),
        t(
            "If you have just done a UK job, your muscle memory will hear public school as fee-paying. In Australia it is a government school. Private / independent is the fee-paying side. Get this wrong and you mis-state a child’s placement.",
            "Si acabas de hacer un encargo británico, el oído oirá public school como de pago. En Australia es una escuela estatal. Private / independent es la de pago. Si te equivocas, falseas la escolarización de un niño.",
            "Si vous sortez d’une mission UK, l’oreille entendra public school comme payante. En Australie, c’est une école d’État. Private / independent est le payant. Une erreur fausse le placement d’un enfant.",
        ),
        (
            "She goes to public school. That’s the free one.",
            "She goes to a public school. That’s the government one.",
        ),
        (
            "She attends a state-funded public school.",
            "She attends a government school.",
        ),
    ),
    item(
        t(
            "ute, arvo, and no worries are normal speech, not jokes.",
            "ute, arvo y no worries son habla normal, no chistes.",
            "ute, arvo et no worries sont de l’oral normal, pas des blagues.",
        ),
        t(
            "A ute is a pickup truck. Arvo is afternoon. No worries can mean you’re welcome, it’s fine, or I will handle it. On a US record, render the meaning. Do not keep no worries if the listener will hear it as indifference to a medical risk.",
            "Una ute es una pickup. Arvo es la tarde. No worries puede significar de nada, está bien o me encargo. En un expediente estadounidense, transmite el significado. No dejes no worries si el oyente lo oirá como indiferencia ante un riesgo médico.",
            "Une ute est un pick-up. Arvo = après-midi. No worries peut vouloir dire de rien, ça va ou je m’en occupe. Sur un dossier US, rendez le sens. Ne gardez pas no worries si l’auditeur l’entendra comme de l’indifférence face à un risque médical.",
        ),
        (
            "I’ll bring the pickup this afternoon. No problem.",
            "I’ll bring the ute this arvo. No worries.",
        ),
        (
            "I will bring the pickup truck this afternoon. I will take care of it.",
            "I will bring the utility vehicle this afternoon. I will take care of it.",
        ),
        None,
        [
            lex(t("pickup truck", "camioneta", "pick-up"), "pickup / truck", "ute"),
            lex(t("afternoon", "tarde", "après-midi"), "afternoon", "arvo"),
            lex(t("you’re welcome / it’s fine", "de nada / está bien", "de rien / ça va"), "you’re welcome / no problem", "no worries"),
        ],
    ),
)

add(
    "us|nz",
    item(
        t(
            "New Zealand is close to Australia and not a copy. jandals, dairy, bach.",
            "Nueva Zelanda se parece a Australia y no es una copia. jandals, dairy, bach.",
            "La Nouvelle-Zélande est proche de l’Australie et n’en est pas une copie. jandals, dairy, bach.",
        ),
        t(
            "Flip-flops are jandals, not Australian thongs and not US underwear. A dairy is a corner shop, not a farm. A bach is a holiday house. Vowels differ from Australian English enough that names get mis-heard. Keep Māori names as said. They belong on the record.",
            "Las chanclas son jandals, no thongs australianas ni ropa interior estadounidense. Un dairy es una tienda de barrio, no una granja. Un bach es una casa de vacaciones. Las vocales difieren del inglés australiano lo bastante como para oír mal los nombres. Conserva los nombres maoríes tal como se dijeron. Van al expediente.",
            "Les tongs sont des jandals, pas des thongs australiennes ni un sous-vêtement US. Un dairy est une épicerie, pas une ferme. Un bach est une maison de vacances. Les voyelles diffèrent assez de l’Australie pour faire entendre de travers les noms. Gardez les noms māori tels quels. Ils vont au dossier.",
        ),
        (
            "Wear flip-flops. Stop at the corner store. We have a cabin up north.",
            "Wear jandals. Stop at the dairy. We have a bach up north.",
        ),
        (
            "Wear flip-flops. Stop at the convenience store. We have a holiday house in the north.",
            "Wear flip-flops. Stop at the convenience store. We have a holiday house in the north.",
        ),
    ),
    item(
        t(
            "Health and courts are New Zealand systems, not US insurance and not the NHS.",
            "La salud y los tribunales son sistemas neozelandeses, no un seguro de EE. UU. ni el NHS.",
            "Santé et tribunaux sont des systèmes néo-zélandais, pas une assurance US ni le NHS.",
        ),
        t(
            "ACC (accident compensation), DHB-era and current health names, and the District Court / High Court do not map onto ER copays or Crown Court. Use the local official name, then a short gloss if the US listener needs it.",
            "ACC (compensación por accidente), los nombres de salud y el District Court / High Court no se equivalen a copagos de urgencias ni al Crown Court. Usa el nombre oficial local y, si el oyente estadounidense lo necesita, una glosa breve.",
            "L’ACC, les noms de santé et le District Court / High Court ne recouvrent pas les copays d’ER ni la Crown Court. Utilisez le nom officiel local, puis une courte glose si l’auditeur US en a besoin.",
        ),
        (
            "I went to the ER. Workers’ comp will pay.",
            "I went to A&E. ACC will cover it.",
        ),
        (
            "I attended the emergency department. Accident compensation will cover it.",
            "I attended the emergency department. ACC, the accident compensation scheme, will cover it.",
        ),
    ),
)

add(
    "us|ca",
    item(
        t(
            "Speech often sounds US. Formal writing often does not.",
            "El habla suele sonar estadounidense. La escritura formal a menudo no.",
            "L’oral ressemble souvent à l’américain. L’écrit formel souvent non.",
        ),
        t(
            "A Canadian may say apartment, truck, and elevator, then write colour, centre, and defence on a form. Do not “fix” the spelling to US -or on a Canadian record. Courts and health are provincial. OHIP, MSP, RAMQ are not “Medicaid.”",
            "Un canadiense puede decir apartment, truck y elevator, y luego escribir colour, centre y defence en un formulario. No «corrijas» la ortografía al -or estadounidense en un expediente canadiense. Tribunales y salud son provinciales. OHIP, MSP, RAMQ no son «Medicaid».",
            "Un Canadien peut dire apartment, truck et elevator, puis écrire colour, centre et defence sur un formulaire. Ne « corrigez » pas l’orthographe en -or US sur un dossier canadien. Tribunaux et santé sont provinciaux. OHIP, MSP, RAMQ ne sont pas « Medicaid ».",
        ),
        (
            "I live in an apartment. Write color on the form.",
            "I live in an apartment. Write colour on the form.",
        ),
        (
            "The patient resides in an apartment. The form uses the spelling color.",
            "The patient resides in an apartment. The form uses the spelling colour.",
        ),
        None,
        [
            lex(t("bathroom", "baño", "toilettes"), "restroom / bathroom", "washroom"),
            lex(t("winter hat", "gorro de invierno", "bonnet d’hiver"), "beanie", "toque"),
            lex(t("formal spelling", "ortografía formal", "orthographe formelle"), "color / center / defense", "colour / centre / defence"),
        ],
    ),
    item(
        t(
            "Quebec English sits next to French. Atlantic and Prairie speech are not Toronto.",
            "El inglés de Quebec convive con el francés. El Atlántico y las Praderas no son Toronto.",
            "L’anglais du Québec côtoie le français. L’Atlantique et les Prairies ne sont pas Toronto.",
        ),
        t(
            "A dépanneur is a convenience store in Quebec. Some English speakers in Quebec use French institutional names (CLSC, SAQ) as the normal word. Keep those names. Do not translate them into a US chain.",
            "Un dépanneur es una tienda de barrio en Quebec. Algunos anglófonos de Quebec usan nombres institucionales franceses (CLSC, SAQ) como palabra normal. Conserva esos nombres. No los traduzcas a una cadena estadounidense.",
            "Un dépanneur est une épicerie au Québec. Des anglophones québécois utilisent des noms institutionnels français (CLSC, SAQ) comme mot normal. Gardez-les. Ne les traduisez pas en enseigne US.",
        ),
        (
            "I stopped at the convenience store. I went to the clinic.",
            "I stopped at the dépanneur. I went to the CLSC.",
        ),
        (
            "I stopped at the convenience store. I attended the clinic.",
            "I stopped at the dépanneur, a convenience store. I attended the CLSC, a local community clinic.",
        ),
    ),
)

add(
    "us|za",
    item(
        t(
            "just now is later. now-now is sooner. A robot is a traffic light.",
            "just now es más tarde. now-now es antes. Un robot es un semáforo.",
            "just now veut dire plus tard. now-now, plus tôt. Un robot est un feu.",
        ),
        t(
            "This is the pairing that produces false urgency. A South African who says I will do it just now is not promising immediately. Now-now is sooner than just now, still not always “this second.” A robot is a traffic light. If you render just now as right now in a US ER, you invent a timeline.",
            "Este par produce falsa urgencia. Un sudafricano que dice I will do it just now no promete inmediatez. Now-now es antes que just now, y aún no siempre es «ahora mismo». Un robot es un semáforo. Si interpretas just now como right now en unas urgencias de EE. UU., inventas un plazo.",
            "Cette paire crée une fausse urgence. Un Sud-Africain qui dit I will do it just now ne promet pas l’immédiat. Now-now est plus tôt que just now, pas forcément « tout de suite ». Un robot est un feu. Si vous rendez just now par right now aux urgences US, vous inventez un délai.",
        ),
        (
            "I’ll do it right now. Stop at the traffic light. The pickup is in the driveway.",
            "I’ll do it just now. Stop at the robot. The bakkie is in the driveway.",
        ),
        (
            "I will do it immediately.",
            "I will do it later, not immediately. Stop at the traffic light. The pickup truck is in the driveway.",
        ),
        None,
        [
            lex(t("later, not immediately", "más tarde, no ahora", "plus tard, pas tout de suite"), "right now / in a minute", "just now"),
            lex(t("sooner than just now", "antes que just now", "plus tôt que just now"), "in a second", "now-now"),
            lex(t("traffic light", "semáforo", "feu"), "stoplight / traffic light", "robot"),
            lex(t("pickup", "camioneta", "pick-up"), "pickup", "bakkie"),
            lex(t("barbecue", "barbacoa", "barbecue"), "barbecue / cookout", "braai"),
            lex(t("sneakers", "zapatillas", "baskets"), "sneakers", "takkies"),
        ],
    ),
    item(
        t(
            "Official English sits beside Afrikaans, isiZulu, isiXhosa, and other languages.",
            "El inglés oficial convive con el afrikáans, el zulú, el xhosa y otras lenguas.",
            "L’anglais officiel côtoie l’afrikaans, l’isiZulu, l’isiXhosa et d’autres langues.",
        ),
        t(
            "A name, a place, or a legal term may be in another official language. Keep it. South African English is not “British with an accent.” Load-shedding, township, and specific court names need a gloss for a US listener, not a rewrite into American slang.",
            "Un nombre, un lugar o un término legal puede estar en otra lengua oficial. Consérvalo. El inglés sudafricano no es «británico con acento». Load-shedding, township y los nombres de los tribunales necesitan una glosa para un oyente de EE. UU., no una reescritura en argot estadounidense.",
            "Un nom, un lieu ou un terme juridique peut être dans une autre langue officielle. Gardez-le. L’anglais sud-africain n’est pas « du britannique avec un accent ». Load-shedding, township et les noms de tribunaux ont besoin d’une glose pour un auditeur US, pas d’une réécriture en argot américain.",
        ),
        (
            "The power went out. I went to the neighborhood.",
            "There was load-shedding. I went to the township.",
        ),
        (
            "There was a power outage. I went to the residential area.",
            "There was load-shedding, a scheduled power cut. I went to the township. Keep the name the speaker used.",
        ),
    ),
)

add(
    "us|in",
    item(
        t(
            "prepone, revert, do the needful, and good name are Indian English.",
            "prepone, revert, do the needful y good name son inglés indio.",
            "prepone, revert, do the needful et good name sont de l’anglais indien.",
        ),
        t(
            "Prepone means bring forward, the opposite of postpone. Revert means reply, not return to a previous software state. Do the needful means take the required action. Good name means full name. These are features of a recognized official variety. Do not mark them as errors in the journal. Do translate them for a US listener who will hear revert as “undo.”",
            "Prepone significa adelantar, lo contrario de postpone. Revert significa responder, no volver a un estado anterior de un programa. Do the needful significa tomar la medida necesaria. Good name significa nombre completo. Son rasgos de una variedad oficial reconocida. No los marques como errores en el diario. Tradúcelos para un oyente de EE. UU. que oirá revert como «deshacer».",
            "Prepone = avancer, le contraire de postpone. Revert = répondre, pas revenir à un état logiciel. Do the needful = prendre la mesure requise. Good name = nom complet. Ce sont des traits d’une variété officielle reconnue. Ne les marquez pas comme des fautes dans le journal. Traduisez-les pour un auditeur US qui entendra revert comme « annuler ».",
        ),
        (
            "Can we move the meeting earlier? I’ll get back to you. What’s her name? Please handle it.",
            "Can we prepone the meeting? I will revert. What is her good name? Please do the needful.",
        ),
        (
            "Can we bring the meeting forward? I will reply. What is her full name? Please take the required action.",
            "Can we bring the meeting forward? I will reply. What is her full name? Please take the required action.",
        ),
        t(
            "If both parties are using Indian English, keep prepone and revert. If the listener is US, render the meaning.",
            "Si ambas partes usan inglés indio, conserva prepone y revert. Si el oyente es de EE. UU., transmite el significado.",
            "Si les deux parties utilisent l’anglais indien, gardez prepone et revert. Si l’auditeur est US, rendez le sens.",
        ),
        [
            lex(t("bring forward", "adelantar", "avancer"), "move up / bring forward", "prepone"),
            lex(t("reply", "responder", "répondre"), "get back to you / reply", "revert"),
            lex(t("take the required action", "tomar la medida necesaria", "prendre la mesure requise"), "please take care of it", "do the needful"),
            lex(t("full name", "nombre completo", "nom complet"), "full name / legal name", "good name"),
            lex(t("100,000", "100 000", "100 000"), "100,000 / a hundred thousand", "a lakh"),
            lex(t("10,000,000", "10 000 000", "10 000 000"), "10 million", "a crore"),
        ],
    ),
    item(
        t(
            "only, itself, and the progressive with stative verbs are grammar, not padding.",
            "only, itself y el progresivo con verbos de estado son gramática, no relleno.",
            "only, itself et le progressif avec des verbes d’état sont de la grammaire, pas du remplissage.",
        ),
        t(
            "I am knowing and I am understanding are used in Indian English where US English wants I know / I understand. only and itself can mark emphasis or a discourse boundary: What is your name only? That is not a request for a single name and nothing else in the US sense. Sir and madam are more frequent and less ironic than in the US. Keep the respect if that is the speaker’s register.",
            "I am knowing e I am understanding se usan en inglés indio donde EE. UU. quiere I know / I understand. only e itself pueden marcar énfasis o un corte del discurso: What is your name only? No es una petición de «un solo nombre y nada más» en el sentido estadounidense. Sir y madam son más frecuentes y menos irónicos que en EE. UU. Conserva el respeto si ese es el registro del hablante.",
            "I am knowing et I am understanding s’emploient en anglais indien là où les É.-U. veulent I know / I understand. only et itself peuvent marquer l’emphase ou une frontière de discours : What is your name only ? Ce n’est pas « un seul nom et rien d’autre » au sens US. Sir et madam sont plus fréquents et moins ironiques qu’aux É.-U. Gardez le respect si c’est le registre du locuteur.",
        ),
        (
            "I understand. What’s her name?",
            "I am understanding. What is her good name only?",
        ),
        (
            "I understand. What is her full name?",
            "I understand. What is her full name?",
        ),
    ),
    item(
        t(
            "Indian legal and administrative English is a standard, often UK-aligned in spelling.",
            "El inglés jurídico y administrativo indio es un estándar, a menudo alineado con el RU en la ortografía.",
            "L’anglais juridique et administratif indien est un standard, souvent aligné sur le RU à l’écrit.",
        ),
        t(
            "Advocate, brief, honourable court, and filed before map onto Indian procedure, not automatically onto a US attorney and a motion. Spell defence / organise as the document does. A lakh of rupees is 100,000. Write the figure in numerals as well.",
            "Advocate, brief, honourable court y filed before corresponden al procedimiento indio, no automáticamente a un attorney y una motion de EE. UU. Escribe defence / organise como el documento. Un lakh de rupias son 100 000. Escribe también la cifra en números.",
            "Advocate, brief, honourable court et filed before relèvent de la procédure indienne, pas automatiquement d’un attorney et d’une motion US. Écrivez defence / organise comme le document. Un lakh de roupies = 100 000. Écrivez aussi le chiffre.",
        ),
        (
            "My attorney filed a motion for $150,000.",
            "My advocate filed it before the honourable court. The amount is 1.5 lakh.",
        ),
        (
            "Counsel filed a motion for 150,000 dollars.",
            "The advocate filed the matter before the court. The amount is 150,000 rupees (1.5 lakh).",
        ),
    ),
)

add(
    "us|cb",
    item(
        t(
            "Creole grammar is a system. Formal island English is often UK-aligned.",
            "La gramática criolla es un sistema. El inglés formal de las islas suele alinearse con el RU.",
            "La grammaire créole est un système. L’anglais formel des îles s’aligne souvent sur le RU.",
        ),
        t(
            "Jamaica, Trinidad, Barbados, the Bahamas and others each have an English–Creole continuum. Everyday speech may drop be, mark aspect with does or a-, and use different pronouns. That is not broken English. In the booth, render the meaning. On a US court record, you may need a standard English line plus a note that the speaker used Creole grammar. Do not “fix” the speaker in their own voice.",
            "Jamaica, Trinidad, Barbados, las Bahamas y otros tienen un continuo inglés-criollo. El habla cotidiana puede omitir be, marcar aspecto con does o a-, y usar otros pronombres. No es inglés roto. En cabina, transmite el significado. En un expediente judicial de EE. UU. puede hacer falta una línea en inglés estándar y una nota de que el hablante usó gramática criolla. No «arregles» al hablante en su propia voz.",
            "La Jamaïque, Trinité, la Barbade, les Bahamas et d’autres ont un continuum anglais-créole. L’oral peut omettre be, marquer l’aspect avec does ou a-, et changer les pronoms. Ce n’est pas de l’anglais cassé. En cabine, rendez le sens. Sur un dossier judiciaire US, une ligne en anglais standard plus une note peut être nécessaire. Ne « corrigez » pas le locuteur dans sa propre voix.",
        ),
        (
            "She is going to the store now. She has already left.",
            "She going to the shop. She done gone. Soon come.",
        ),
        (
            "She is going to the store now. She has already left.",
            "She is going to the shop. She has already left. She will arrive shortly.",
        ),
        t(
            "soon come means the person will arrive, not that they are already in the doorway.",
            "soon come significa que la persona llegará, no que ya está en la puerta.",
            "soon come signifie que la personne arrivera, pas qu’elle est déjà sur le pas de la porte.",
        ),
    ),
    item(
        t(
            "yard, pickney, and island legal English.",
            "yard, pickney y el inglés jurídico de las islas.",
            "yard, pickney et l’anglais juridique des îles.",
        ),
        t(
            "yard can mean home or the community around it. pickney is a child. Court and school English on many islands is UK-aligned (flat, lift, defence). Do not assume US vocabulary because the listener is in the US. Name the island if you know it. Jamaica is not Trinidad.",
            "yard puede significar casa o la comunidad alrededor. pickney es un niño. El inglés de tribunales y escuelas en muchas islas se alinea con el RU (flat, lift, defence). No asumas vocabulario estadounidense porque el oyente esté en EE. UU. Nombra la isla si la sabes. Jamaica no es Trinidad.",
            "yard peut vouloir dire la maison ou le voisinage. pickney = enfant. L’anglais des tribunaux et des écoles s’aligne souvent sur le RU (flat, lift, defence). N’supposez pas le vocabulaire US parce que l’auditeur est aux É.-U. Nommez l’île si vous la connaissez. La Jamaïque n’est pas Trinité.",
        ),
        (
            "The kids are at home. Take the elevator.",
            "The pickney dem in the yard. Take the lift.",
        ),
        (
            "The children are at home. Take the elevator.",
            "The children are at home. Take the lift.",
        ),
    ),
)

add(
    "uk|ie",
    item(
        t(
            "Ireland is not UK English with a lilt. ye, grand, and the after-perfect are Irish.",
            "Irlanda no es inglés del RU con cadencia. ye, grand y el after-perfect son irlandeses.",
            "L’Irlande n’est pas de l’anglais britannique avec un accent. ye, grand et le after-perfect sont irlandais.",
        ),
        t(
            "Spelling and many nouns align (flat, lift, chips). Address and recent-past do not. Are ye coming? and I’m after doing it are Irish. A UK listener may hear after as a plan. HSE is not the NHS. Gardaí are not the police in the British sense of a force name. Say Ireland, not “the UK,” on the record.",
            "La ortografía y muchos sustantivos coinciden (flat, lift, chips). El trato y el pasado reciente no. Are ye coming? e I’m after doing it son irlandeses. Un oyente británico puede oír after como un plan. El HSE no es el NHS. La Garda no es «the police» como nombre de cuerpo británico. En el expediente di Irlanda, no «the UK».",
            "L’orthographe et beaucoup de noms s’alignent (flat, lift, chips). Le tutoiement et le passé récent non. Are ye coming ? et I’m after doing it sont irlandais. Un auditeur britannique peut entendre after comme un projet. Le HSE n’est pas le NHS. Les Gardaí ne sont pas « the police » au sens d’un corps britannique. Dites Irlande, pas « the UK », au dossier.",
        ),
        (
            "Are you lot coming? I’ve just done it. I went to A&E under the NHS.",
            "Are ye coming? I’m after doing it. I went to A&E under the HSE.",
        ),
        (
            "Are you all attending? I have just done it. I attended A&E under the NHS.",
            "Are you all attending? I have just done it. I attended A&E under the HSE.",
        ),
    ),
    item(
        t(
            "press and craic will be misunderstood in Britain if you leave them bare.",
            "press y craic se malentenderán en Gran Bretaña si los dejas sueltos.",
            "press et craic seront mal compris en Grande-Bretagne si vous les laissez seuls.",
        ),
        t(
            "A UK press is a newspaper or a printing press. An Irish press is a cupboard. Craic is not a crack or a crime. Gloss once, then you can keep the word if the speaker repeats it.",
            "En el RU, press es un periódico o una imprenta. En Irlanda, press es un armario. Craic no es una grieta ni un delito. Glosa una vez y luego puedes conservar la palabra si el hablante la repite.",
            "Au RU, press est un journal ou une imprimerie. En Irlande, press est un placard. Craic n’est ni une fissure ni un crime. Glosez une fois, puis vous pouvez garder le mot si le locuteur le répète.",
        ),
        (
            "The mugs are in the cupboard. We had a good night.",
            "The mugs are in the press. The craic was mighty.",
        ),
        (
            "The mugs are in the cupboard. We had an enjoyable evening.",
            "The mugs are in the cupboard. We had an enjoyable evening.",
        ),
    ),
)

add(
    "uk|au",
    item(
        t(
            "Spelling largely aligns. Public school and thongs do not.",
            "La ortografía coincide en gran parte. Public school y thongs no.",
            "L’orthographe s’aligne en grande partie. Public school et thongs non.",
        ),
        t(
            "Both write colour and centre. A UK public school is fee-paying. An Australian public school is a government school. UK thongs are underwear. Australian thongs are flip-flops. This pairing is where UK interpreters get school placements and clothing wrong because the rest of the variety feels familiar.",
            "Ambos escriben colour y centre. Una public school británica es de pago. Una public school australiana es estatal. En el RU thongs es ropa interior. En Australia son chanclas. En este par los intérpretes británicos se equivocan con la escuela y la ropa porque el resto de la variedad les suena familiar.",
            "Les deux écrivent colour et centre. Une public school UK est payante. Une public school australienne est d’État. Au RU, thongs = sous-vêtements. En Australie, ce sont des tongs. C’est ici que les interprètes britanniques se trompent sur l’école et les vêtements, parce que le reste leur semble familier.",
        ),
        (
            "She goes to a public school. That’s Eton-type. She wore thongs under her dress.",
            "She goes to a public school. That’s the government one. She wore thongs to the beach.",
        ),
        (
            "She attends a fee-paying independent school. She wore underwear.",
            "She attends a government school. She wore flip-flops.",
        ),
    ),
    item(
        t(
            "ute, arvo, and chips still need a gloss for a British listener.",
            "ute, arvo y chips siguen necesitando glosa para un oyente británico.",
            "ute, arvo et chips ont encore besoin d’une glose pour un auditeur britannique.",
        ),
        t(
            "A British listener knows lift and flat. They may not know ute (pickup) or arvo (afternoon). Chips in both countries can be fries; a packet of crisps is the UK snack, and Australia will also say packet of chips. Ask which one is fried potatoes.",
            "Un oyente británico conoce lift y flat. Puede no conocer ute (pickup) ni arvo (tarde). Chips en ambos países pueden ser fries; un packet of crisps es el snack británico, y en Australia también se dice packet of chips. Pregunta cuáles son las papas fritas.",
            "Un auditeur britannique connaît lift et flat. Il peut ignorer ute (pick-up) ou arvo (après-midi). Chips peut vouloir dire frites des deux côtés ; un packet of crisps est le snack UK, et l’Australie dit aussi packet of chips. Demandez lesquelles sont des frites.",
        ),
        (
            "I’ll bring the van this afternoon. I want chips and a packet of crisps.",
            "I’ll bring the ute this arvo. I want hot chips.",
        ),
        (
            "I will bring the van this afternoon. I would like chips and crisps.",
            "I will bring the utility vehicle this afternoon. I would like hot chips, fried potatoes.",
        ),
    ),
)

add(
    "uk|nz",
    item(
        t(
            "UK-aligned spelling, New Zealand words, Māori on the record.",
            "Ortografía alineada con el RU, palabras neozelandesas, maorí en el expediente.",
            "Orthographe alignée sur le RU, mots néo-zélandais, māori au dossier.",
        ),
        t(
            "jandals, dairy, and bach will not be understood in Britain without a gloss. Māori names and terms are not optional decoration. Keep the speaker’s form. Health is not the NHS; use the New Zealand official name and a short gloss.",
            "jandals, dairy y bach no se entenderán en Gran Bretaña sin glosa. Los nombres y términos maoríes no son adorno opcional. Conserva la forma del hablante. La salud no es el NHS; usa el nombre oficial neozelandés y una glosa breve.",
            "jandals, dairy et bach ne passeront pas en Grande-Bretagne sans glose. Les noms et termes māori ne sont pas une décoration. Gardez la forme du locuteur. La santé n’est pas le NHS ; utilisez le nom officiel néo-zélandais et une courte glose.",
        ),
        (
            "Wear flip-flops. Stop at the corner shop. We have a cottage.",
            "Wear jandals. Stop at the dairy. We have a bach.",
        ),
        (
            "Wear flip-flops. Stop at the corner shop. We have a holiday cottage.",
            "Wear flip-flops. Stop at the convenience store. We have a holiday house.",
        ),
    ),
)

add(
    "uk|ca",
    item(
        t(
            "Canada sits between you and the US. Expect mixed spelling and US-leaning speech.",
            "Canadá está entre tú y EE. UU. Espera ortografía mixta y habla más cercana a la estadounidense.",
            "Le Canada se situe entre vous et les É.-U. Attendez-vous à une orthographe mixte et un oral proche de l’américain.",
        ),
        t(
            "A Canadian may say truck and apartment, then write colour on a federal form. Washroom is the normal public-toilet word. Provincial health names are not the NHS. Do not turn a Canadian court into a Crown Court by habit.",
            "Un canadiense puede decir truck y apartment, y luego escribir colour en un formulario federal. Washroom es la palabra normal para el baño público. Los nombres de salud provinciales no son el NHS. No conviertas un tribunal canadiense en Crown Court por costumbre.",
            "Un Canadien peut dire truck et apartment, puis écrire colour sur un formulaire fédéral. Washroom est le mot normal pour les toilettes publiques. Les noms de santé provinciaux ne sont pas le NHS. Ne transformez pas un tribunal canadien en Crown Court par habitude.",
        ),
        (
            "The lorry is outside. The loo is down the hall. I went to A&E under the NHS.",
            "The truck is outside. The washroom is down the hall. I went to emerg under OHIP.",
        ),
        (
            "The goods vehicle is outside. The toilet is down the hall. I attended A&E under the NHS.",
            "The truck is outside. The washroom is down the hall. I attended emergency under the provincial health plan.",
        ),
    ),
)

add(
    "uk|za",
    item(
        t(
            "Formal English is close. just now, robot, and bakkie are not British.",
            "El inglés formal es cercano. just now, robot y bakkie no son británicos.",
            "L’anglais formel est proche. just now, robot et bakkie ne sont pas britanniques.",
        ),
        t(
            "A British listener will hear just now as “a moment ago” or “immediately.” In South Africa it often means later. A robot is a traffic light, not a machine. A bakkie is a pickup. Load-shedding is a scheduled power cut. Gloss those four every time until the listener has them.",
            "Un oyente británico oirá just now como «hace un momento» o «ahora mismo». En Sudáfrica suele significar más tarde. Un robot es un semáforo, no una máquina. Una bakkie es una pickup. Load-shedding es un corte de luz programado. Glosa esas cuatro cada vez hasta que el oyente las tenga.",
            "Un auditeur britannique entendra just now comme « à l’instant » ou « tout de suite ». En Afrique du Sud, cela veut souvent dire plus tard. Un robot est un feu, pas une machine. Une bakkie est un pick-up. Load-shedding est une coupure programmée. Glosez ces quatre mots à chaque fois jusqu’à ce que l’auditeur les ait.",
        ),
        (
            "I’ll do it in a moment. Stop at the lights. The pickup is in the car park.",
            "I’ll do it just now. Stop at the robot. The bakkie is in the car park.",
        ),
        (
            "I will do it shortly.",
            "I will do it later, not immediately. Stop at the traffic light. The pickup truck is in the car park.",
        ),
    ),
)

add(
    "uk|in",
    item(
        t(
            "Spelling often aligns. Discourse markers and numbers do not.",
            "La ortografía suele alinearse. Los marcadores del discurso y los números no.",
            "L’orthographe s’aligne souvent. Les marqueurs de discours et les nombres non.",
        ),
        t(
            "Both may write colour and defence. Indian revert, prepone, do the needful, lakh, and crore will still stop a British listener. Indian legal English (advocate, honourable court) is its own procedure. Do not assume a solicitor/barrister split.",
            "Ambos pueden escribir colour y defence. Revert, prepone, do the needful, lakh y crore indios seguirán frenando a un oyente británico. El inglés jurídico indio (advocate, honourable court) es un procedimiento propio. No asumas la división solicitor/barrister.",
            "Les deux peuvent écrire colour et defence. Revert, prepone, do the needful, lakh et crore indiens arrêteront encore un auditeur britannique. L’anglais juridique indien (advocate, honourable court) a sa propre procédure. N’supposez pas le couple solicitor/barrister.",
        ),
        (
            "I’ll get back to you. Can we bring the meeting forward? It’s 150,000.",
            "I will revert. Can we prepone the meeting? It’s 1.5 lakh.",
        ),
        (
            "I will reply. Can we bring the meeting forward? The amount is 150,000.",
            "I will reply. Can we bring the meeting forward? The amount is 150,000 (1.5 lakh).",
        ),
    ),
)

add(
    "uk|cb",
    item(
        t(
            "Court English may look British. Everyday speech may be Creole.",
            "El inglés judicial puede parecer británico. El habla cotidiana puede ser criolla.",
            "L’anglais judiciaire peut sembler britannique. L’oral quotidien peut être créole.",
        ),
        t(
            "Many islands use UK-aligned school and court English (lift, flat, defence). The same speaker may use Creole grammar at home. Render the meaning. Do not treat aspect markers as missing verbs. Name the island.",
            "Muchas islas usan inglés escolar y judicial alineado con el RU (lift, flat, defence). El mismo hablante puede usar gramática criolla en casa. Transmite el significado. No trates los marcadores de aspecto como verbos que faltan. Nombra la isla.",
            "Beaucoup d’îles utilisent un anglais scolaire et judiciaire aligné sur le RU (lift, flat, defence). Le même locuteur peut utiliser une grammaire créole chez lui. Rendez le sens. Ne traitez pas les marqueurs d’aspect comme des verbes manquants. Nommez l’île.",
        ),
        (
            "She’s gone to the shop. She’ll be back soon. Take the lift.",
            "She done gone to the shop. Soon come. Take the lift.",
        ),
        (
            "She has gone to the shop. She will return shortly. Take the lift.",
            "She has gone to the shop. She will return shortly. Take the lift.",
        ),
    ),
)

add(
    "au|nz",
    item(
        t(
            "Close, not interchangeable. Flip-flops and the corner shop have different names.",
            "Cercanos, no intercambiables. Las chanclas y la tienda de barrio tienen nombres distintos.",
            "Proches, pas interchangeables. Les tongs et l’épicerie ont des noms différents.",
        ),
        t(
            "Australian thongs are New Zealand jandals. An Australian milk bar is not a New Zealand dairy. A bach is New Zealand; a shack or holiday house is the gloss. Vowels differ enough that names get repeated. Keep Māori as said. Do not call a New Zealander Australian on the record.",
            "Las thongs australianas son jandals en Nueva Zelanda. Un milk bar australiano no es un dairy neozelandés. Bach es de Nueva Zelanda; shack o holiday house es la glosa. Las vocales difieren lo bastante como para repetir nombres. Conserva el maorí tal cual. No llames australiano a un neozelandés en el expediente.",
            "Les thongs australiennes sont des jandals en Nouvelle-Zélande. Un milk bar australien n’est pas un dairy néo-zélandais. Bach est néo-zélandais ; shack ou holiday house est la glose. Les voyelles diffèrent assez pour faire répéter les noms. Gardez le māori tel quel. N’appelez pas un Néo-Zélandais Australien au dossier.",
        ),
        (
            "Wear thongs. Stop at the milk bar.",
            "Wear jandals. Stop at the dairy.",
        ),
        (
            "Wear flip-flops. Stop at the convenience store.",
            "Wear flip-flops. Stop at the convenience store.",
        ),
    ),
)

add("ie|au", item(
    t("Both feel informal to outsiders. grand vs no worries, press vs cupboard, HSE vs Medicare-style systems.",
      "Ambos suenan informales a un extraño. grand vs no worries, press vs cupboard, HSE vs sistemas tipo Medicare.",
      "Les deux semblent informels à un outsider. grand vs no worries, press vs cupboard, HSE vs systèmes type Medicare."),
    t("Irish grand is agreement. Australian no worries can be agreement or “I’ll handle it.” A press is Irish. A ute is Australian. Neither health system is the NHS or US insurance. Name the country on the record.",
      "El grand irlandés es acuerdo. El no worries australiano puede ser acuerdo o «me encargo». Press es irlandés. Ute es australiano. Ningún sistema de salud es el NHS ni un seguro de EE. UU. Nombra el país en el expediente.",
      "Le grand irlandais est un accord. No worries australien peut être un accord ou « je m’en occupe ». Press est irlandais. Ute est australien. Aucun système de santé n’est le NHS ni une assurance US. Nommez le pays au dossier."),
    ("That’s grand. The mugs are in the press. I’ll take the car.",
     "No worries. The mugs are in the cupboard. I’ll take the ute."),
    ("That is acceptable. The mugs are in the cupboard. I will take the car.",
     "I will take care of it. The mugs are in the cupboard. I will take the utility vehicle."),
))

add("ie|nz", item(
    t("Irish after-perfect vs New Zealand dairy/jandals/bach. Neither is UK.",
      "After-perfect irlandés vs dairy/jandals/bach neozelandeses. Ninguno es el RU.",
      "After-perfect irlandais vs dairy/jandals/bach néo-zélandais. Ni l’un ni l’autre n’est le RU."),
    t("I’m after doing it means it is done. A dairy is a shop. Keep Māori names. HSE is not a New Zealand health name.",
      "I’m after doing it significa que ya está hecho. Un dairy es una tienda. Conserva los nombres maoríes. El HSE no es un nombre de salud neozelandés.",
      "I’m after doing it signifie que c’est fait. Un dairy est une boutique. Gardez les noms māori. Le HSE n’est pas un nom de santé néo-zélandais."),
    ("I’m after booking it. Stop at the shop.",
     "I’ve booked it. Stop at the dairy."),
    ("I have just booked it. Stop at the shop.",
     "I have booked it. Stop at the convenience store."),
))

add("ie|ca", item(
    t("grand vs a grand, washroom vs loo, HSE vs provincial plans.",
      "grand vs a grand, washroom vs loo, HSE vs planes provinciales.",
      "grand vs a grand, washroom vs loo, HSE vs régimes provinciaux."),
    t("If a Canadian says it’ll be a grand they mean money. If an Irish speaker says it’s grand they mean agreement. Washroom is Canadian. Loo / toilet is closer to Irish everyday speech.",
      "Si un canadiense dice it’ll be a grand habla de dinero. Si un irlandés dice it’s grand habla de acuerdo. Washroom es canadiense. Loo / toilet se acerca más al habla cotidiana irlandesa.",
      "Si un Canadien dit it’ll be a grand, c’est de l’argent. Si un Irlandais dit it’s grand, c’est un accord. Washroom est canadien. Loo / toilet est plus proche de l’oral irlandais."),
    ("It’s grand. The loo is down the hall.",
     "It’ll be a grand. The washroom is down the hall."),
    ("That is acceptable. The toilet is down the hall.",
     "That will be one thousand dollars. The washroom is down the hall."),
))

add("ie|za", item(
    t("just now vs I’m after doing it: opposite timelines if you mix them.",
      "just now vs I’m after doing it: plazos opuestos si los mezclas.",
      "just now vs I’m after doing it : des délais opposés si vous les mélangez."),
    t("Irish after + -ing is completed recent past. South African just now is often still in the future. Mixing them invents whether the act is done. A robot is a traffic light, not Irish slang.",
      "El after + -ing irlandés es pasado reciente completado. El just now sudafricano suele seguir en el futuro. Mezclarlos inventa si el acto está hecho. Un robot es un semáforo, no argot irlandés.",
      "Le after + -ing irlandais est un passé récent accompli. Le just now sud-africain est souvent encore au futur. Les mélanger invente si l’acte est fait. Un robot est un feu, pas de l’argot irlandais."),
    ("I’m after doing it. That’s grand.",
     "I’ll do it just now. Stop at the robot."),
    ("I have just done it. That is acceptable.",
     "I will do it later, not immediately. Stop at the traffic light."),
))

add("ie|in", item(
    t("Two official Englishes that outsiders flatten into “British.” They are not.",
      "Dos ingleses oficiales que un extraño aplana en «británico». No lo son.",
      "Deux anglais officiels qu’un outsider aplatit en « britannique ». Ils ne le sont pas."),
    t("Irish ye / after-perfect / HSE vs Indian prepone / revert / lakh. Both may use UK spelling. Keep each variety’s grammar. Sir is warmer and more routine in Indian English than in Irish English.",
      "Ye / after-perfect / HSE irlandeses vs prepone / revert / lakh indios. Ambos pueden usar ortografía británica. Conserva la gramática de cada variedad. Sir es más cálido y rutinario en inglés indio que en irlandés.",
      "Ye / after-perfect / HSE irlandais vs prepone / revert / lakh indiens. Les deux peuvent utiliser l’orthographe britannique. Gardez la grammaire de chaque variété. Sir est plus chaleureux et plus routinier en anglais indien qu’en irlandais."),
    ("I’m after sending it. That’s grand.",
     "I have reverted. Please do the needful. It’s one lakh."),
    ("I have just sent it. That is acceptable.",
     "I have replied. Please take the required action. The amount is 100,000."),
))

add("ie|cb", item(
    t("Both have everyday systems that look “non-standard” only if your ear is UK/US.",
      "Ambos tienen sistemas cotidianos que solo parecen «no estándar» si el oído es RU/EE. UU.",
      "Les deux ont des systèmes quotidiens qui ne semblent « non standard » que si l’oreille est UK/US."),
    t("Irish after-perfect and Caribbean Creole aspect both mark time. Do not repair either into a bare UK past. HSE vs island health names. ye vs island pronouns.",
      "El after-perfect irlandés y el aspecto criollo caribeño marcan el tiempo. No los repares en un pasado británico desnudo. HSE vs nombres de salud de las islas. ye vs pronombres isleños.",
      "Le after-perfect irlandais et l’aspect créole caribéen marquent le temps. Ne les réparez pas en un passé britannique nu. HSE vs noms de santé des îles. ye vs pronoms insulaires."),
    ("I’m after going. Are ye coming?",
     "She done gone. Soon come."),
    ("I have just gone. Are you all coming?",
     "She has already left. She will arrive shortly."),
))

add("au|ca", item(
    t("Australian slang vs Canadian US-leaning speech and UK-leaning spelling.",
      "Argot australiano vs habla canadiense cercana a EE. UU. y ortografía cercana al RU.",
      "Argot australien vs oral canadien proche des É.-U. et orthographe proche du RU."),
    t("ute / arvo / thongs vs washroom / toque / colour on forms. Neither should be rewritten into the other. Provincial health is not Medicare Australia.",
      "ute / arvo / thongs vs washroom / toque / colour en formularios. No reescribas uno en el otro. La salud provincial no es Medicare Australia.",
      "ute / arvo / thongs vs washroom / toque / colour sur les formulaires. N’écrivez pas l’un dans l’autre. La santé provinciale n’est pas Medicare Australia."),
    ("I’ll bring the ute this arvo. Wear thongs.",
     "I’ll bring the truck this afternoon. The washroom is that way. Write colour."),
    ("I will bring the utility vehicle this afternoon. Wear flip-flops.",
     "I will bring the truck this afternoon. The washroom is that way. Use the spelling colour."),
))

add("au|za", item(
    t("Two Southern Hemisphere Englishes. thongs vs takkies, just now vs no worries.",
      "Dos ingleses del hemisferio sur. thongs vs takkies, just now vs no worries.",
      "Deux anglais de l’hémisphère sud. thongs vs takkies, just now vs no worries."),
    t("Australian no worries is often reassurance. South African just now is a delay. A robot is a traffic light in South Africa only. Thongs are flip-flops in Australia and underwear in many other Englishes; South Africa more often says slops or flip-flops.",
      "El no worries australiano suele ser tranquilizar. El just now sudafricano es una demora. Robot es semáforo solo en Sudáfrica. Thongs son chanclas en Australia y ropa interior en otros ingleses; en Sudáfrica se dice más slops o flip-flops.",
      "No worries australien rassure souvent. Just now sud-africain est un délai. Robot n’est un feu qu’en Afrique du Sud. Thongs = tongs en Australie, sous-vêtements ailleurs ; l’Afrique du Sud dit plutôt slops ou flip-flops."),
    ("No worries, I’ll do it this arvo. Wear thongs.",
     "I’ll do it just now. Stop at the robot. Wear slops."),
    ("I will take care of it this afternoon. Wear flip-flops.",
     "I will do it later, not immediately. Stop at the traffic light. Wear flip-flops."),
))

add("au|in", item(
    t("Informal Australian vs official Indian English. Do not flatten either into UK.",
      "Australiano informal vs inglés indio oficial. No aplanes ninguno en RU.",
      "Australien informel vs anglais indien officiel. N’aplatissez ni l’un ni l’autre en UK."),
    t("no worries / ute / arvo vs revert / prepone / lakh. Australian public school is government-funded. Indian English sir is routine respect. Keep both.",
      "no worries / ute / arvo vs revert / prepone / lakh. La public school australiana es estatal. El sir del inglés indio es respeto rutinario. Conserva ambos.",
      "no worries / ute / arvo vs revert / prepone / lakh. La public school australienne est publique. Le sir de l’anglais indien est un respect routinier. Gardez les deux."),
    ("No worries, I’ll revert… wait, I’ll get back to you this arvo.",
     "I will revert. Can we prepone? It is two lakh."),
    ("I will reply this afternoon.",
     "I will reply. Can we bring the meeting forward? The amount is 200,000."),
))

add("au|cb", item(
    t("Australian slang vs Caribbean Creole. Both get “corrected” by people who only know US/UK.",
      "Argot australiano vs criollo caribeño. Ambos los «corrige» quien solo conoce EE. UU./RU.",
      "Argot australien vs créole caribéen. Les deux se font « corriger » par qui ne connaît que US/UK."),
    t("Keep ute and Creole aspect. soon come is not Australian no worries. Name the island. Do not call Caribbean English “broken Australian.”",
      "Conserva ute y el aspecto criollo. soon come no es el no worries australiano. Nombra la isla. No llames al inglés caribeño «australiano roto».",
      "Gardez ute et l’aspect créole. soon come n’est pas le no worries australien. Nommez l’île. N’appelez pas l’anglais caribéen « de l’australien cassé »."),
    ("I’ll bring the ute. No worries, soon.",
     "She done gone. Soon come."),
    ("I will bring the utility vehicle. I will take care of it shortly.",
     "She has already left. She will arrive shortly."),
))

add("nz|ca", item(
    t("dairy vs dépanneur/washroom. Māori vs French institutional names.",
      "dairy vs dépanneur/washroom. Maorí vs nombres institucionales franceses.",
      "dairy vs dépanneur/washroom. Māori vs noms institutionnels français."),
    t("A New Zealand dairy is a shop. A Canadian dépanneur is a shop in Quebec. Washroom is Canadian. Keep Māori and French names as said.",
      "Un dairy neozelandés es una tienda. Un dépanneur canadiense es una tienda en Quebec. Washroom es canadiense. Conserva los nombres maoríes y franceses tal cual.",
      "Un dairy néo-zélandais est une boutique. Un dépanneur canadien est une boutique au Québec. Washroom est canadien. Gardez les noms māori et français tels quels."),
    ("Stop at the dairy. Wear jandals.",
     "Stop at the dépanneur. The washroom is inside."),
    ("Stop at the convenience store. Wear flip-flops.",
     "Stop at the convenience store. The washroom is inside."),
))

add("nz|za", item(
    t("jandals vs slops, dairy vs cafe, just now vs I’ll do it now.",
      "jandals vs slops, dairy vs cafe, just now vs I’ll do it now.",
      "jandals vs slops, dairy vs cafe, just now vs I’ll do it now."),
    t("Both are UK-aligned in formal writing. The time-word just now is the danger. New Zealand now is closer to immediately. South African just now is often later.",
      "Ambos se alinean con el RU en la escritura formal. La palabra de tiempo just now es el peligro. El now neozelandés se acerca a lo inmediato. El just now sudafricano suele ser más tarde.",
      "Les deux s’alignent sur le RU à l’écrit formel. Le mot de temps just now est le danger. Le now néo-zélandais est plus proche de l’immédiat. Le just now sud-africain est souvent plus tard."),
    ("I’ll do it now. Wear jandals.",
     "I’ll do it just now. Wear slops. Stop at the robot."),
    ("I will do it immediately. Wear flip-flops.",
     "I will do it later, not immediately. Wear flip-flops. Stop at the traffic light."),
))

add("nz|in", item(
    t("Māori names vs Indian English officialese. Both stay on the record.",
      "Nombres maoríes vs registro oficial del inglés indio. Ambos quedan en el expediente.",
      "Noms māori vs registre officiel de l’anglais indien. Les deux restent au dossier."),
    t("Do not respell a Māori name to make it “easier.” Do not mark prepone as a mistake. Formal spelling may align. The discourse does not.",
      "No reescribas un nombre maorí para que sea «más fácil». No marques prepone como error. La ortografía formal puede alinearse. El discurso no.",
      "Ne réorthographiez pas un nom māori pour que ce soit « plus simple ». Ne marquez pas prepone comme une faute. L’orthographe formelle peut s’aligner. Le discours non."),
    ("I’ll get back to you. Keep the name as she said it.",
     "I will revert. What is her good name? Can we prepone?"),
    ("I will reply. Keep the name as she said it.",
     "I will reply. What is her full name? Can we bring the meeting forward?"),
))

add("nz|cb", item(
    t("Keep Māori and keep Creole. Neither is a failed UK sentence.",
      "Conserva el maorí y el criollo. Ninguno es una frase británica fallida.",
      "Gardez le māori et le créole. Ni l’un ni l’autre n’est une phrase britannique ratée."),
    t("jandals / dairy / bach vs soon come / done gone / yard. Formal English on both sides may look British. Everyday speech does not.",
      "jandals / dairy / bach vs soon come / done gone / yard. El inglés formal de ambos lados puede parecer británico. El habla cotidiana no.",
      "jandals / dairy / bach vs soon come / done gone / yard. L’anglais formel des deux côtés peut sembler britannique. L’oral quotidien non."),
    ("Stop at the dairy. Wear jandals.",
     "She done gone to the shop. Soon come."),
    ("Stop at the convenience store. Wear flip-flops.",
     "She has gone to the shop. She will arrive shortly."),
))

add("ca|za", item(
    t("Canadian washroom/colour vs South African robot/just now/bakkie.",
      "Washroom/colour canadiense vs robot/just now/bakkie sudafricanos.",
      "Washroom/colour canadiens vs robot/just now/bakkie sud-africains."),
    t("A Canadian just now usually means a moment ago. A South African just now often means later. That single clash will falsify a timeline. Provincial health is not a South African public scheme by another name.",
      "En Canadá, just now suele significar hace un momento. En Sudáfrica suele significar más tarde. Ese choque solo falsea un plazo. La salud provincial no es un esquema público sudafricano con otro nombre.",
      "Au Canada, just now veut souvent dire à l’instant. En Afrique du Sud, souvent plus tard. Ce seul choc fausse un délai. La santé provinciale n’est pas un régime public sud-africain sous un autre nom."),
    ("I did it just now. The washroom is there. Write colour.",
     "I’ll do it just now. Stop at the robot. The bakkie is outside."),
    ("I did it a moment ago. The washroom is there. Use the spelling colour.",
     "I will do it later, not immediately. Stop at the traffic light. The pickup is outside."),
))

add("ca|in", item(
    t("Canadian mixed spelling vs Indian official vocabulary.",
      "Ortografía mixta canadiense vs vocabulario oficial indio.",
      "Orthographe mixte canadienne vs vocabulaire officiel indien."),
    t("A Canadian form may say colour and a Canadian mouth may say truck. Indian revert / prepone / lakh still need a gloss. Do not “correct” either toward US English.",
      "Un formulario canadiense puede decir colour y la boca canadiense puede decir truck. Revert / prepone / lakh indios siguen necesitando glosa. No «corrijas» ninguno hacia el inglés de EE. UU.",
      "Un formulaire canadien peut dire colour et la bouche canadienne dire truck. Revert / prepone / lakh indiens ont encore besoin d’une glose. Ne « corrigez » ni l’un ni l’autre vers l’anglais US."),
    ("I’ll get back to you. Write color… actually colour.",
     "I will revert. Can we prepone? It is three lakh."),
    ("I will reply. Use the spelling colour.",
     "I will reply. Can we bring the meeting forward? The amount is 300,000."),
))

add("ca|cb", item(
    t("Canadian standard speech vs Caribbean Creole continuum.",
      "Habla estándar canadiense vs continuo criollo caribeño.",
      "Oral standard canadien vs continuum créole caribéen."),
    t("Washroom and colour will be understood in much of the Caribbean formal English. Creole aspect will not be understood if you leave it unrendered for a Canadian listener. Gloss the meaning. Keep the island.",
      "Washroom y colour se entenderán en gran parte del inglés formal caribeño. El aspecto criollo no se entenderá si no lo interpretas para un oyente canadiense. Glosa el significado. Conserva la isla.",
      "Washroom et colour passeront dans une grande partie de l’anglais formel caribéen. L’aspect créole ne passera pas si vous ne le rendez pas pour un auditeur canadien. Glosez le sens. Gardez l’île."),
    ("The washroom is down the hall. I’ll be right there.",
     "She done gone. Soon come."),
    ("The washroom is down the hall. I will be there shortly.",
     "She has already left. She will arrive shortly."),
))

add("za|in", item(
    t("Two official Englishes with time-words and number-words that US/UK listeners miss.",
      "Dos ingleses oficiales con palabras de tiempo y de número que EE. UU./RU no pillan.",
      "Deux anglais officiels avec des mots de temps et de nombre que US/UK ratent."),
    t("just now vs revert/prepone. A lakh is 100,000. A robot is a traffic light. Neither speaker is making a mistake. Formal documents on both sides may look UK-aligned.",
      "just now vs revert/prepone. Un lakh son 100 000. Un robot es un semáforo. Ningún hablante se equivoca. Los documentos formales de ambos lados pueden parecer alineados con el RU.",
      "just now vs revert/prepone. Un lakh = 100 000. Un robot est un feu. Ni l’un ni l’autre ne se trompe. Les documents formels des deux côtés peuvent sembler alignés sur le RU."),
    ("I’ll do it just now. Stop at the robot.",
     "I will revert. Can we prepone? It is two lakh."),
    ("I will do it later, not immediately. Stop at the traffic light.",
     "I will reply. Can we bring the meeting forward? The amount is 200,000."),
))

add("za|cb", item(
    t("just now / robot vs soon come / Creole aspect. Both get flattened into “not proper English.”",
      "just now / robot vs soon come / aspecto criollo. Ambos se aplanan en «inglés incorrecto».",
      "just now / robot vs soon come / aspect créole. Les deux se font aplatir en « mauvais anglais »."),
    t("They are different systems. A South African delay-word is not Caribbean soon come. Render each on its own terms. Formal English on both sides may use UK spelling.",
      "Son sistemas distintos. Una palabra de demora sudafricana no es el soon come caribeño. Interpreta cada una en sus términos. El inglés formal de ambos lados puede usar ortografía británica.",
      "Ce sont des systèmes différents. Un mot de délai sud-africain n’est pas le soon come caribéen. Rendez chacun selon ses termes. L’anglais formel des deux côtés peut utiliser l’orthographe britannique."),
    ("I’ll do it just now. Stop at the robot.",
     "Soon come. She done gone."),
    ("I will do it later, not immediately. Stop at the traffic light.",
     "She will arrive shortly. She has already left."),
))

add("in|cb", item(
    t("Indian official English vs Caribbean Creole-to-acrolect. Do not rank them.",
      "Inglés oficial indio vs criollo-acrolecto caribeño. No los jerarquices.",
      "Anglais officiel indien vs créole-acrolecte caribéen. Ne les hiérarchisez pas."),
    t("revert / prepone / lakh are administrative Indian English. done gone / soon come / yard are Caribbean. Both appear in real interpreting jobs. Keep each. Formal court English on both sides may look British. Everyday speech will not.",
      "revert / prepone / lakh son inglés administrativo indio. done gone / soon come / yard son caribeños. Ambos aparecen en encargos reales. Conserva cada uno. El inglés judicial formal de ambos lados puede parecer británico. El habla cotidiana no.",
      "revert / prepone / lakh sont de l’anglais administratif indien. done gone / soon come / yard sont caribéens. Les deux apparaissent dans de vrais jobs. Gardez chacun. L’anglais judiciaire formel des deux côtés peut sembler britannique. L’oral quotidien non."),
    ("I will revert. Please do the needful. It is one lakh.",
     "She done gone to the yard. Soon come."),
    ("I will reply. Please take the required action. The amount is 100,000.",
     "She has gone home. She will arrive shortly."),
))


def emit() -> None:
    missing = []
    for i, a in enumerate(ORDER):
        for b in ORDER[i + 1 :]:
            key = f"{a}|{b}"
            if key not in PAIRS:
                missing.append(key)
    if missing:
        raise SystemExit("missing pairs: " + ", ".join(missing))

    payload = {
        "order": ORDER,
        "names": NAMES,
        "labels": LABELS,
        "pairs": PAIRS,
    }
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    OUT.write_text(
        "/* Generated by scripts/build_dialect_en_pairs.py. Edit that file, then rerun. */\n"
        "window.DIALECT_EN = " + body + ";\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT.relative_to(ROOT)} ({len(PAIRS)} pairs)")


if __name__ == "__main__":
    emit()




