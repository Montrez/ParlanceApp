"""
Daily language and culture posts for #daily-culture.

GitHub Actions posts one topic per day at 10:00 AM Eastern
(.github/workflows/daily-culture.yml). Topics cover Spanish and French
language, culture, interpreter craft, and exam tips.
"""
from __future__ import annotations

import datetime


# ── Topic library ─────────────────────────────────────────────────────────────

TOPICS = [
    # False cognates
    {
        "title": "False friend of the day: **embarazada**",
        "body": (
            "In Spanish, *embarazada* means **pregnant** — not embarrassed. "
            "If you meant embarrassed, the word you want is *avergonzada/o*.\n\n"
            "False cognates like this one are one of the most common interpreter slips. "
            "Which ones have tripped you up?"
        ),
    },
    {
        "title": "False friend of the day: **sensible**",
        "body": (
            "In French, *sensible* means **sensitive**, not sensible. "
            "If you mean sensible (reasonable), say *raisonnable*.\n\n"
            "The French word *sensé* is closer to the English meaning, "
            "but even that leans more toward 'makes sense' than 'levelheaded.'"
        ),
    },
    {
        "title": "False friend: **éventuellement** (French)",
        "body": (
            "*Éventuellement* does not mean 'eventually' — it means **possibly** or **if need be**.\n\n"
            "If you mean eventually, say *finalement* or *à terme*. "
            "This one catches even advanced speakers off guard in formal contexts."
        ),
    },
    {
        "title": "False friend: **actualmente** (Spanish)",
        "body": (
            "*Actualmente* means **currently** or **at present** — not 'actually.'\n\n"
            "For 'actually,' use *de hecho*, *en realidad*, or *efectivamente* depending on the shade of meaning. "
            "In a courtroom or medical setting, mixing these up changes the entire statement."
        ),
    },
    # Register and formality
    {
        "title": "Register matters: *usted* in Latin America vs. Spain",
        "body": (
            "In most of Latin America, *usted* is used far more broadly than in Spain — "
            "including with close family members in some countries like Colombia.\n\n"
            "In Spain, *tú* is the default for almost any peer or younger person. "
            "When interpreting, always match the register of the original speaker, not your own habits."
        ),
    },
    {
        "title": "Register tip: when to use *vous* vs. *tu* in French",
        "body": (
            "The *vous/tu* distinction in French is not just about age — it signals relationship, "
            "power, and context. In professional or medical settings, always default to *vous* "
            "unless the other person explicitly switches.\n\n"
            "Switching too early can feel presumptuous. Switching too late can feel cold. "
            "When in doubt, follow the other speaker's lead."
        ),
    },
    # Interpreter craft
    {
        "title": "Interpreter tip: chunking",
        "body": (
            "Simultaneous interpreters don't wait for a sentence to end before starting — "
            "they break speech into **chunks** of 3 to 5 words and begin rendering immediately.\n\n"
            "The trick is holding the meaning of the last chunk in short-term memory while "
            "your mouth is still producing the previous one. Practicing dictation exercises "
            "in your target language builds this muscle fast."
        ),
    },
    {
        "title": "Interpreter tip: note-taking symbols",
        "body": (
            "Consecutive interpreters develop personal symbol systems over time. "
            "A few common ones:\n"
            "→ cause/leads to\n"
            "↑↓ increase/decrease\n"
            "≠ contradiction or denial\n"
            "+ positive, agreement\n"
            "∅ nothing, absence, refusal\n\n"
            "The goal isn't shorthand for every word — it's capturing structure, "
            "sequence, and the speaker's stance."
        ),
    },
    {
        "title": "Interpreter tip: the 'ear-voice span'",
        "body": (
            "The ear-voice span (EVS) is the delay between when you hear something and when you say it. "
            "In simultaneous interpretation, a trained interpreter typically maintains an EVS of **2 to 4 seconds**.\n\n"
            "Too short and you start guessing before the meaning is clear. "
            "Too long and your working memory gets overloaded. "
            "Finding your natural EVS is one of the core skills of interpreter training."
        ),
    },
    # Cultural notes
    {
        "title": "Cultural note: the *sobremesa*",
        "body": (
            "In Spanish-speaking cultures, *la sobremesa* refers to the time spent lingering at the table "
            "after a meal — talking, debating, laughing. There is no direct equivalent in English or French.\n\n"
            "It reflects a cultural value: meals are not just about food, they are social rituals. "
            "Understanding concepts like this deepens your ability to interpret tone and intent."
        ),
    },
    {
        "title": "Cultural note: French and the Académie française",
        "body": (
            "The *Académie française* has been France's official guardian of the French language since 1635. "
            "It publishes rulings on new words and correct usage — though speakers often ignore them.\n\n"
            "In 2017, it declared gender-neutral writing (*l'écriture inclusive*) a 'mortal peril' for French. "
            "Whether you agree or not, knowing this context helps you understand why register and grammar "
            "carry so much weight in formal French communication."
        ),
    },
    {
        "title": "Cultural note: *voseo* and regional identity",
        "body": (
            "*Voseo* — using *vos* instead of *tú* — is standard in Argentina, Uruguay, and parts of Central America. "
            "Its conjugations differ: *vos hablás*, *vos comés*, *vos vivís*.\n\n"
            "In some countries it was historically stigmatized; today in Argentina it is a point of pride. "
            "An interpreter working with Argentine speakers should never 'correct' *voseo* — "
            "it is not an error, it is the standard."
        ),
    },
    {
        "title": "Cultural note: French in Africa",
        "body": (
            "French is the official or co-official language of 29 countries, "
            "most of them in Africa. More people speak French in sub-Saharan Africa "
            "than in France itself.\n\n"
            "African French has regional vocabulary, rhythms, and loanwords from local languages. "
            "An interpreter who only knows Parisian French may miss meaning in a Congolese or "
            "Senegalese speaker's phrasing."
        ),
    },
    # Grammar and language facts
    {
        "title": "Grammar deep dive: *ser* vs. *estar*",
        "body": (
            "Both mean 'to be,' but they are not interchangeable. "
            "A quick rule that holds up in professional contexts:\n\n"
            "*Ser* → identity, origin, material, permanent traits, time/date, profession\n"
            "*Estar* → state, location (of people/things), temporary conditions, results of change\n\n"
            "The nuance matters for interpretation: *'está muerto'* (he is dead, a current state) "
            "vs. *'es muerto'* (which would be unnatural) — context carries meaning."
        ),
    },
    {
        "title": "Grammar deep dive: the French subjunctive",
        "body": (
            "The subjunctive (*subjonctif*) is used far more in French than in English. "
            "It appears after expressions of doubt, emotion, necessity, or opinion:\n\n"
            "*Il faut que tu sois là.* (You need to be there.)\n"
            "*Je doute qu'il vienne.* (I doubt he'll come.)\n\n"
            "In formal and legal French, mastering the subjunctive is non-negotiable. "
            "In everyday speech, it is sometimes replaced by the indicative — "
            "but in writing and professional interpretation, it signals precision."
        ),
    },
    {
        "title": "Language fact: Spanish is the world's second most spoken native language",
        "body": (
            "With over 490 million native speakers, Spanish ranks second only to Mandarin. "
            "It is the official language of 20 countries across four continents.\n\n"
            "What this means for interpreters: there is no single 'correct' Spanish. "
            "Your job is to serve the speaker's dialect and intent — not impose a standard."
        ),
    },
    {
        "title": "Language fact: French has more words for 'you' than you think",
        "body": (
            "Beyond *tu* and *vous*, older literary French used *tu* for God and intimates "
            "while *vous* was strictly formal. Today *on* often replaces *nous* in spoken French "
            "(*on y va* instead of *nous y allons*).\n\n"
            "In Quebec French, *vous* can sound archaic between peers, while in formal France it is still expected. "
            "Regional and generational variation is always in play."
        ),
    },
    # Exam tips
    {
        "title": "DELE tip: formal register is non-negotiable at B2 and above",
        "body": (
            "The DELE exam at B2 and C1/C2 levels tests your ability to use formal written Spanish consistently.\n\n"
            "Common pitfalls:\n"
            "Mixing *tú* and *usted* in the same piece of writing\n"
            "Using colloquial connectors (*y* to start sentences, *bueno* as filler)\n"
            "Inconsistent verb tense in formal narration\n\n"
            "Practicing with Parlance on formal sentences before the exam can sharpen your register instincts quickly."
        ),
    },
    {
        "title": "DELF tip: the oral production section",
        "body": (
            "In the DELF B2, the oral production task requires you to take a position and defend it. "
            "Examiners are not just listening for vocabulary — they want:\n\n"
            "Clear structure (introduction, argument, counterargument, conclusion)\n"
            "Appropriate connectors (*en revanche*, *par ailleurs*, *c'est pourquoi*)\n"
            "Consistent register throughout\n\n"
            "Practice by summarizing a news article aloud and then arguing against your own summary."
        ),
    },
    # Word origins and curiosities
    {
        "title": "Word origin: *sincere*",
        "body": (
            "One popular theory holds that *sincere* comes from the Latin *sine cera* — 'without wax.' "
            "Dishonest marble merchants allegedly hid cracks in stone with wax. "
            "Honest sellers advertised their work as *sine cera*.\n\n"
            "Linguists debate whether this is true, but it is a useful reminder: "
            "language is full of metaphors from material culture that have long since faded from view."
        ),
    },
    {
        "title": "Word curiosity: *dépaysement* (French)",
        "body": (
            "*Dépaysement* describes the disorientation of being in a foreign place — "
            "that feeling of everything being unfamiliar, the rules slightly different, "
            "the cues you rely on no longer working.\n\n"
            "There is no single English equivalent. The closest is 'culture shock,' "
            "but *dépaysement* carries less anxiety and more wistfulness. "
            "It is sometimes used positively — as the refreshing jolt of a new environment."
        ),
    },
    {
        "title": "Word curiosity: *madrugada* (Spanish)",
        "body": (
            "*La madrugada* refers specifically to the hours between midnight and dawn — "
            "roughly 1 AM to 5 AM. English has no dedicated word for this stretch of time.\n\n"
            "Languages carve up the world differently. "
            "A good interpreter notices when a source-language concept has no clean equivalent "
            "and knows how to render the meaning without losing it."
        ),
    },
    {
        "title": "False friend: **éxito** (Spanish)",
        "body": (
            "*Éxito* means **success**, not exit. The word for exit is *salida*.\n\n"
            "A speaker who says *tuvo mucho éxito* had a good result, they did not leave the room. "
            "In a medical or legal setting that swap can sound like the person walked out."
        ),
    },
    {
        "title": "False friend: **librería** (Spanish)",
        "body": (
            "A *librería* is a **bookstore**. A library is a *biblioteca*.\n\n"
            "French has the same trap: *librairie* vs. *bibliothèque*. "
            "If someone says they spent the afternoon in the *librería*, they were shopping, not studying."
        ),
    },
    {
        "title": "False friend: **constipado** (Spanish)",
        "body": (
            "*Estoy constipado* usually means **I have a cold / I'm stuffed up**, not constipated. "
            "For constipation, Spanish uses *estreñido*.\n\n"
            "This one is especially risky in medical interpreting. "
            "Confirm the symptom before you render it."
        ),
    },
    {
        "title": "False friend: **pretender** (Spanish)",
        "body": (
            "*Pretender* means **to try, intend, or claim**, not to pretend. "
            "To pretend is *fingir* or *hacer como si*.\n\n"
            "*No pretendo ofender* means I do not mean to offend. "
            "Render the intent, not the English lookalike."
        ),
    },
    {
        "title": "False friend: **asistir** (Spanish)",
        "body": (
            "*Asistir* means **to attend**, not to assist. "
            "*Asistió a la audiencia* means they were present at the hearing.\n\n"
            "To help someone, use *ayudar* or *asistir a alguien* with a person object, "
            "and still check context. In court, attendance and assistance are not the same fact."
        ),
    },
    {
        "title": "False friend: **molestar** (Spanish)",
        "body": (
            "*Molestar* means **to bother or annoy**. It does not carry the English legal sense of molest.\n\n"
            "*¿Te molesta si abro la ventana?* is ordinary politeness. "
            "In a police or clinical interview, do not escalate the register unless the source language does."
        ),
    },
    {
        "title": "False friend: **attendre** (French)",
        "body": (
            "*Attendre* means **to wait**, not to attend. "
            "To attend an event, say *assister à*.\n\n"
            "*J'attends le médecin* means I am waiting for the doctor. "
            "If you render it as 'I attend the doctor,' the whole scene changes."
        ),
    },
    {
        "title": "False friend: **déception** (French)",
        "body": (
            "*Déception* means **disappointment**, not deception. "
            "Deception is *tromperie* or *duperie*.\n\n"
            "A witness who speaks of *une déception* is talking about unmet expectations, "
            "not a fraud allegation, unless the rest of the statement says so."
        ),
    },
    {
        "title": "False friend: **blesser** (French)",
        "body": (
            "*Blesser* means **to wound or hurt**, not to bless. "
            "To bless is *bénir*.\n\n"
            "*Il a été blessé* is an injury. "
            "In medical consecutive, that false friend can turn a trauma report into nonsense."
        ),
    },
    {
        "title": "False friend: **actuellement** (French)",
        "body": (
            "*Actuellement* means **currently / at the moment**, not actually. "
            "For 'actually,' use *en fait*, *vraiment*, or *effectivement*.\n\n"
            "Same trap as Spanish *actualmente*. "
            "In testimony, 'currently' and 'actually' point to different facts."
        ),
    },
    {
        "title": "Register: *mande* in Mexico",
        "body": (
            "In much of Mexico, *¿mande?* is a polite 'pardon?' or 'yes?' "
            "It comes from *mande usted*, a deferential 'command me.'\n\n"
            "It is not confusion and it is not subservience in everyday use. "
            "Match the courtesy. Do not flatten it to a blunt 'what?'"
        ),
    },
    {
        "title": "Register: *vosotros* is Spain, not the Americas",
        "body": (
            "*Vosotros* is the informal plural 'you' in Spain. "
            "Latin American Spanish uses *ustedes* for both formal and informal plural.\n\n"
            "If a Spaniard says *vosotros sabéis*, do not upgrade it to *ustedes saben* "
            "unless the target dialect of the job requires it. Register is part of the message."
        ),
    },
    {
        "title": "Register: Quebec *tu* vs. France *vous*",
        "body": (
            "In Quebec, *tu* is common among peers and even in some service encounters "
            "where France would still use *vous*.\n\n"
            "Neither side is wrong. Follow the speaker in front of you, "
            "not a textbook from the other side of the Atlantic."
        ),
    },
    {
        "title": "Interpreter tip: numbers and dates",
        "body": (
            "Numbers, dates, and addresses are where even strong interpreters slip. "
            "French inverts some date order. Spanish often uses 24-hour time in formal settings. "
            "Million and billion do not line up the same way in every tradition.\n\n"
            "When a number matters legally or medically, slow down and confirm. "
            "A fluent wrong figure is worse than a short pause."
        ),
    },
    {
        "title": "Interpreter tip: names and honorifics",
        "body": (
            "Do not translate *Don*, *Doña*, *señor*, *doctora*, or *Maître* into a casual first name "
            "because English feels less formal to you.\n\n"
            "Honorifics mark status, age, and respect. Dropping them can sound rude. "
            "Keep them, or use the equivalent title the target language actually uses."
        ),
    },
    {
        "title": "Interpreter tip: hedging and modality",
        "body": (
            "*Creo que*, *puede que*, *il me semble*, *je dirais* are not filler. "
            "They mark uncertainty, politeness, or legal caution.\n\n"
            "If you strip the hedge and say it as a fact, you changed the testimony. "
            "Render the speaker's degree of commitment, not just the proposition."
        ),
    },
    {
        "title": "Interpreter tip: self-correction",
        "body": (
            "When the speaker starts over, you start over. "
            "Do not tidy the false start into a cleaner sentence they did not say.\n\n"
            "Repairs, interruptions, and abandoned clauses can matter in court and in clinics. "
            "Your job is the utterance, including the mess."
        ),
    },
    {
        "title": "Interpreter tip: décalage with lists",
        "body": (
            "Lists of symptoms, meds, or charges are where décalage (that processing lag) bites. "
            "If you fall behind, stop the speaker if the mode allows it, or drop to a shorter lag.\n\n"
            "Guessing the fifth item because you still hold the second is how errors compound. "
            "Accuracy beats a smooth delivery."
        ),
    },
    {
        "title": "Interpreter tip: first-person rendering",
        "body": (
            "Professional interpreting is usually first person: "
            "the patient says *me duele*, you say 'it hurts' as them, not 'she says it hurts.'\n\n"
            "Third-person reporting ('the patient states...') is a different role. "
            "Stay in first person unless the assignment explicitly uses reported speech."
        ),
    },
    {
        "title": "Cultural note: *la merienda*",
        "body": (
            "*La merienda* is a light afternoon meal, often around 5 or 6, "
            "especially with children in Spain and parts of Latin America.\n\n"
            "It is not quite a snack and not quite dinner. "
            "If a parent mentions *merienda* in a school or medical history, "
            "keep the idea of a seated afternoon bite, not a bag of chips in passing."
        ),
    },
    {
        "title": "Cultural note: *la bise*",
        "body": (
            "In France, *la bise* (cheek kisses as greeting) varies by region: "
            "two, three, even four, and not everyone wants it.\n\n"
            "Quebec and many professional settings skip it. "
            "When interpreting social small talk about greetings, "
            "do not assume one French-speaking culture's habit is universal."
        ),
    },
    {
        "title": "Cultural note: Swiss and Belgian numbers",
        "body": (
            "Belgium and Switzerland often use *septante* (70), *nonante* (90), "
            "and Switzerland also *huitante* or *octante* (80), "
            "instead of France's *soixante-dix* and *quatre-vingt-dix*.\n\n"
            "If a Belgian patient says *septante-deux*, that is 72, not a style choice. "
            "Render the number, not the Parisian equivalent words."
        ),
    },
    {
        "title": "Cultural note: Caribbean Spanish",
        "body": (
            "In much of the Caribbean, speakers may drop /s/ at the end of syllables, "
            "aspirate it, or weaken consonants. *Está* can sound like *e'tá*.\n\n"
            "That is not sloppy Spanish. It is a regional sound system. "
            "Train your ear on it before a medical or court day with Caribbean speakers."
        ),
    },
    {
        "title": "Cultural note: Andean *pues* and *nomás*",
        "body": (
            "In parts of the Andes, *pues*, *nomás*, and *pues nomás* soften requests and statements. "
            "They are discourse particles, not empty words.\n\n"
            "Flattening them can make a polite speaker sound blunt. "
            "Carry the softening into English with tone, or a light 'just' / 'then,' when it fits."
        ),
    },
    {
        "title": "Cultural note: Quebec *tu* tag questions",
        "body": (
            "Quebec French often tucks *tu* into questions as a particle: "
            "*C'est-tu prêt?* meaning 'Is it ready?' "
            "That *tu* is not the pronoun 'you.'\n\n"
            "Treat it as a yes/no question marker. "
            "Translating it as 'you' will scramble the sentence."
        ),
    },
    {
        "title": "Grammar: *por* vs. *para*",
        "body": (
            "*Para* leans toward purpose, destination, deadline, and intended recipient. "
            "*Por* leans toward cause, duration, exchange, and the path taken.\n\n"
            "*Lo hice por ella* (because of her / on her behalf) is not "
            "*lo hice para ella* (for her as the intended person). "
            "In legal language that distinction is the whole point."
        ),
    },
    {
        "title": "Grammar: pretérito vs. imperfecto",
        "body": (
            "Pretérito (*habló*) bounds a completed event. "
            "Imperfecto (*hablaba*) sets scene, habit, or an ongoing backdrop.\n\n"
            "*Cuando llegó, ella hablaba por teléfono*: the call was already in progress. "
            "Swap the tenses and you rewrite what happened first."
        ),
    },
    {
        "title": "Grammar: passé composé vs. imparfait",
        "body": (
            "French *passé composé* often delivers the event. "
            "*Imparfait* paints the background or a habitual past.\n\n"
            "*Il est entré. Il faisait froid.* He came in. It was cold. "
            "Interpreters who flatten both into simple past English still need to keep that relationship clear."
        ),
    },
    {
        "title": "Grammar: Spanish impersonal *se*",
        "body": (
            "*Se habla español* is not 'Spanish speaks itself.' "
            "It is a general statement: Spanish is spoken here.\n\n"
            "*Se necesita testigo* means a witness is needed, not that a specific 'se' needs one. "
            "In notices and procedures, keep it impersonal unless a real agent appears."
        ),
    },
    {
        "title": "Grammar: French *y* and *en*",
        "body": (
            "*Y* often stands in for a place or *à* + thing. "
            "*En* stands in for *de* + thing or a quantity.\n\n"
            "*Vous avez des questions? Oui, j'en ai.* "
            "Dropping *en* in the English gloss is fine. Dropping the quantity meaning is not."
        ),
    },
    {
        "title": "Grammar: Spanish present for the near future",
        "body": (
            "*Mañana voy al médico* is a planned near future, even though the verb is present. "
            "English often needs 'I'm going' or 'I go tomorrow,' not a literal timeless present.\n\n"
            "Same pattern in French: *Demain je vais chez le médecin*. "
            "Render the schedule, not a grammar textbook tense name."
        ),
    },
    {
        "title": "Language fact: *anteayer* and *avant-hier*",
        "body": (
            "Spanish *anteayer* and French *avant-hier* mean **the day before yesterday**. "
            "English has the phrase, but speakers often fumble it under pressure.\n\n"
            "In a history of present illness or an alibi, that extra day matters. "
            "Do not collapse it into 'yesterday.'"
        ),
    },
    {
        "title": "Language fact: *consuegros*",
        "body": (
            "*Consuegros* are your child's in-laws: the other set of parents. "
            "English has no everyday single word for that relationship.\n\n"
            "If a speaker says *mis consuegros*, you may need 'my son's in-laws' "
            "or 'my daughter's parents-in-law.' Do not guess 'cousins.'"
        ),
    },
    {
        "title": "Language fact: French *septante* is not slang",
        "body": (
            "Learners sometimes treat *septante* as informal. It is standard in Belgium and Switzerland. "
            "France's *soixante-dix* is the regional oddity if you zoom out across Francophonie.\n\n"
            "Your default should be the speaker's system, not the one you drilled in class."
        ),
    },
    {
        "title": "DELE tip: the *prueba oral* is interaction, not a speech",
        "body": (
            "At DELE B2 and up, the oral exam rewards turn-taking, clarification, and reaction, "
            "not a memorized monologue.\n\n"
            "If you do not understand the prompt, ask in Spanish. "
            "Examiners listen for repair strategies as much as for fancy vocabulary."
        ),
    },
    {
        "title": "SIELE tip: it is digital and modular",
        "body": (
            "SIELE is computer-based and you can sit sections separately. "
            "DELE is a full exam on a fixed date with a paper-era structure in many centers.\n\n"
            "If someone in #find-a-seat is choosing, the right question is not 'which is easier,' "
            "it is which format and recognition they actually need."
        ),
    },
    {
        "title": "DALF tip: source documents are part of the task",
        "body": (
            "DALF C1 production often asks you to synthesize several documents, then take a position. "
            "Ignoring a source, or parroting it without a stance, costs marks.\n\n"
            "Practice pulling three claims, naming the tension between them, then arguing. "
            "That shape transfers to interpreter prep too: what is at issue, not just what was said."
        ),
    },
    {
        "title": "TCF tip: the listening clock is unforgiving",
        "body": (
            "TCF listening items play once in many versions. "
            "You cannot rewind a real speaker either.\n\n"
            "Train with one-shot audio: news clips, consults, voicemail. "
            "Note who, what, when, and the request. That is the same muscle as consecutive."
        ),
    },
    {
        "title": "Word curiosity: *estrenar* (Spanish)",
        "body": (
            "*Estrenar* is to use or wear something for the first time, "
            "or to premiere a show. English usually needs a phrase: 'wear it new,' 'open it,' 'premiere.'\n\n"
            "When a speaker is proud they are *estrenando* a coat, they are marking a first, "
            "not merely wearing clothes."
        ),
    },
    {
        "title": "Word curiosity: *friolero* (Spanish)",
        "body": (
            "A *friolero/a* is someone who feels the cold easily. "
            "English has 'always cold' but no tidy everyday adjective with the same bite.\n\n"
            "It shows up in small talk and in clinics ('I can't stand the AC'). "
            "Keep the sensitivity to cold, not a diagnosis, unless they give one."
        ),
    },
    {
        "title": "Word curiosity: *flâner* (French)",
        "body": (
            "*Flâner* is to stroll with no errand, watching the city. "
            "'Walk' is too plain. 'Wander' is closer. 'Loiter' is too hostile.\n\n"
            "The *flâneur* is a cultural type, not a vagrant. "
            "Tone matters when you carry that into English."
        ),
    },
    {
        "title": "Word curiosity: *esprit de l'escalier* (French)",
        "body": (
            "*L'esprit de l'escalier* is the wit you think of on the stairs, "
            "after you have already left the conversation.\n\n"
            "English borrows the phrase because 'afterwit' never caught on. "
            "When someone names that feeling, they mean the delay, not that they were silent from shyness."
        ),
    },
    {
        "title": "Word curiosity: *retrouvailles* (French)",
        "body": (
            "*Les retrouvailles* are a reunion after time apart, with warmth built in. "
            "'Meeting' is too cold. 'Reunion' is the usual English, but it can sound like an event with a banner.\n\n"
            "If a family talks about *retrouvailles*, they mean the emotional finding-each-other-again."
        ),
    },
    {
        "title": "Word curiosity: *duende* (Spanish)",
        "body": (
            "*Duende* in art, especially flamenco, is a charged presence: "
            "the performance catches fire. It is not a literal goblin in that use.\n\n"
            "There is no clean English equivalent. 'Soul' is close and also wrong. "
            "Sometimes the honest rendering is a short explanation, not a single word."
        ),
    },
    {
        "title": "Word curiosity: *aprovecho* at the table",
        "body": (
            "*Buen provecho* or *que aproveche* is said when people are eating, "
            "like 'enjoy your meal,' including to strangers in some countries.\n\n"
            "It is a social courtesy, not a comment on the food's quality. "
            "Render the wish, then move on."
        ),
    },
]


def _today_et() -> datetime.date:
    try:
        from zoneinfo import ZoneInfo

        return datetime.datetime.now(ZoneInfo("America/New_York")).date()
    except Exception:
        return datetime.date.today()


def next_unused_topic(posted_titles: set[str]) -> dict | None:
    """Return the first library topic that has not already appeared in the channel."""
    posted = {title.lower() for title in posted_titles}
    for topic in TOPICS:
        if topic["title"].lower() not in posted:
            return topic
    return None
