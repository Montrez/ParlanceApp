const RAG_KNOWLEDGE = {
  grammar: {
    es: {
      A1: {
        rules: [
          "Ser vs estar: ser for identity/characteristics, estar for location/states/feelings",
          "Present tense regular conjugation: -ar (-o,-as,-a,-amos,-áis,-an), -er (-o,-es,-e,-emos,-éis,-en), -ir (-o,-es,-e,-imos,-ís,-en)",
          "Gender agreement: nouns ending in -o are typically masculine, -a feminine; adjectives must agree",
          "Definite articles: el/la/los/las must agree in gender and number"
        ],
        tips: ["At A1, gently note whether tú (informal) or usted (formal) is used — register awareness starts here for interpreter training"]
      },
      A2: {
        rules: [
          "Reflexive verbs: me levanto, te duchas, se viste — pronoun must match subject",
          "Ir + a + infinitive for near future: Voy a estudiar",
          "Stem-changing verbs: e→ie (querer→quiero), o→ue (poder→puedo), e→i (pedir→pido)",
          "Gustar structure: indirect object + gustar + subject (Me gustan los libros, NOT yo gusto)"
        ],
        tips: ["Introduce tú vs usted distinction — interpreters must know when each is appropriate"]
      },
      B1: {
        rules: [
          "Preterite vs imperfect: preterite for completed actions (comí), imperfect for ongoing/habitual past (comía)",
          "Subjunctive triggers: querer que, esperar que, es importante que + subjunctive",
          "Por vs para: por = reason/exchange/duration, para = purpose/destination/deadline",
          "Present perfect: haber + past participle (he comido, has dicho)"
        ],
        tips: ["Register matters: an interpreter would say '¿Podría usted...?' not '¿Puedes...?' in professional settings"]
      },
      B2: {
        rules: [
          "Subjunctive in noun clauses: Es necesario que + subjunctive, Dudo que + subjunctive",
          "Si clauses: Si tuviera dinero, viajaría (imperfect subjunctive + conditional)",
          "Passive voice: El informe fue escrito por el doctor (ser + past participle)",
          "Common anglicisms to avoid: 'aplicar para' → 'solicitar', 'realizar' (false friend) → 'darse cuenta'"
        ],
        tips: ["Flag register mismatches — mixing tú/usted in the same context is a serious interpreter error"]
      },
      C1: {
        rules: [
          "Pluperfect subjunctive: Si hubiera sabido, habría venido",
          "Verbal periphrasis: llevar + gerund (Llevo dos años estudiando), ir + gerund (progresive)",
          "False cognates: embarazada ≠ embarrassed, sensible ≠ sensible (= sensitive)",
          "Discourse connectors: sin embargo, no obstante, por consiguiente, a pesar de que"
        ],
        tips: ["Professional register is critical — interpreters must maintain consistent formality throughout"]
      },
      C2: {
        rules: [
          "Subtle register shifts: knowing when to use vosotros vs ustedes by region",
          "Literary/archaic forms: hubiere, fuere — recognized in legal texts",
          "Dialectal variation: vos (Rioplatense), ustedes as informal plural (Andalusia/Latin America)",
          "Discourse-level cohesion: anaphoric reference, thematic progression, paragraph-level coherence"
        ],
        tips: ["Master-level interpreters navigate dialect, register, and cultural context simultaneously"]
      }
    },
    fr: {
      A1: {
        rules: [
          "Être vs avoir: être for states/identity, avoir for possession and age (j'ai 20 ans)",
          "Present tense: -er verbs (je parle, tu parles, il parle), irregular être/avoir/aller/faire",
          "Gender agreement: le/la/les; adjectives agree (petit/petite, grands/grandes)",
          "Negation: ne...pas wraps the verb (Je ne parle pas)"
        ],
        tips: ["Note tu (informal) vs vous (formal) from the start — essential for interpreter training"]
      },
      A2: {
        rules: [
          "Reflexive (pronominal) verbs: je me lève, tu te couches — pronoun before verb",
          "Futur proche: aller + infinitive (Je vais manger)",
          "Partitive articles: du, de la, de l', des for unspecified quantities (Je veux du pain)",
          "Passé composé basics: avoir/être + past participle, être verbs agree (elle est partie)"
        ],
        tips: ["Vous is standard in any professional interpreting context — never use tu with clients"]
      },
      B1: {
        rules: [
          "Passé composé vs imparfait: PC for completed events, imparfait for descriptions/habits",
          "Auxiliary choice: être with movement/reflexive verbs (DR MRS VANDERTRAMP), avoir for most others",
          "Past participle agreement: with être (elle est allée), with avoir when direct object precedes (les fleurs que j'ai achetées)",
          "Basic subjunctive: Il faut que, je veux que + subjunctive"
        ],
        tips: ["In interpreting, tense consistency is critical — mixing passé composé and imparfait incorrectly changes meaning"]
      },
      B2: {
        rules: [
          "Subjunctive in complex clauses: bien que, pour que, avant que + subjunctive",
          "Conditionnel passé: j'aurais fait, si j'avais su, j'aurais...",
          "Si clauses: Si + imparfait → conditionnel; Si + plus-que-parfait → conditionnel passé",
          "Anglicisms to avoid: 'réaliser' (= to carry out, NOT to realize), 'actuellement' (= currently, NOT actually)"
        ],
        tips: ["Formal register: use vous, conditionnel de politesse (je voudrais, pourriez-vous), and inversion in questions"]
      },
      C1: {
        rules: [
          "Subjonctif imparfait: qu'il parlât — rare but appears in formal/legal writing",
          "Passé simple: literary tense (il parla, elle fit) — recognized in documents",
          "Nominalization: transformer → la transformation — essential for academic/professional register",
          "Discourse connectors: néanmoins, en revanche, d'ailleurs, par conséquent"
        ],
        tips: ["Professional interpreters must recognize passé simple in texts while using passé composé in speech"]
      },
      C2: {
        rules: [
          "Literary tenses: passé simple, subjonctif imparfait, plus-que-parfait du subjonctif",
          "Regional French: québécois, belgicismes, helvétismes — awareness without judgment",
          "Stylistic precision: choisir le mot juste, avoid redundancy, vary sentence structure",
          "Discourse-level mastery: cohesion markers, register consistency across extended text"
        ],
        tips: ["At C2, interpreters handle simultaneous register shifts between formal testimony and emotional speech"]
      }
    }
  },
  exam: {
    dele: {
      general: "DELE (Diplomas de Español como Lengua Extranjera) — Spanish proficiency exams by Instituto Cervantes.",
      levels: {
        A1: "DELE A1: Short notes, postcards, form filling. Focus on basic communication.",
        A2: "DELE A2: Short letters, descriptions. Show ability to handle routine tasks.",
        B1: "DELE B1: Formal/informal letters, blog posts, opinions. Preterite/imperfect distinction is heavily tested.",
        B2: "DELE B2: Argumentative essays, reports, formal letters. Subjunctive and register are key evaluation criteria.",
        C1: "DELE C1: Text synthesis, critical analysis, professional proposals. Academic register and discourse cohesion are essential.",
        C2: "DELE C2: Integrated essay from multiple sources, scholarly analysis. Near-native precision expected."
      }
    },
    delf: {
      general: "DELF/DALF — French proficiency exams by France Éducation International.",
      levels: {
        A1: "DELF A1: Short messages, postcards, form filling. Basic communication in French.",
        A2: "DELF A2: Short letters, event descriptions. Handle everyday situations.",
        B1: "DELF B1: Formal emails, opinion pieces, blog posts. Passé composé/imparfait distinction is key.",
        B2: "DELF B2: Argumentative essays, formal letters, reports. Subjunctive and register mastery required.",
        C1: "DALF C1: Text synthesis from two sources, structured essay. Academic register and argumentation.",
        C2: "DALF C2: Integrated production from a dossier. Near-native mastery in all registers."
      }
    }
  },
  medical: {
    terminology: {
      es: {
        body: "cabeza (head), corazón (heart), pulmones (lungs), estómago (stomach), hígado (liver), riñones (kidneys), sangre (blood)",
        conditions: "diabetes, hipertensión, asma, cáncer, infección, fractura, alergia, embarazo (pregnancy)",
        procedures: "cirugía (surgery), biopsia, radiografía (X-ray), resonancia magnética (MRI), análisis de sangre (blood test)"
      },
      fr: {
        body: "tête (head), cœur (heart), poumons (lungs), estomac (stomach), foie (liver), reins (kidneys), sang (blood)",
        conditions: "diabète, hypertension, asthme, cancer, infection, fracture, allergie, grossesse (pregnancy)",
        procedures: "chirurgie (surgery), biopsie, radiographie (X-ray), IRM (MRI), analyse de sang (blood test)"
      }
    },
    ethics: [
      "Accuracy: Interpret everything said, nothing added, nothing omitted.",
      "Impartiality: The interpreter does not take sides or advocate.",
      "Confidentiality: All information is strictly confidential (HIPAA).",
      "Role boundaries: The interpreter is not a cultural broker or advisor.",
      "Sight translation: Read the entire document first, then translate maintaining register."
    ]
  },
  legal: {
    terminology: {
      es: {
        court: "tribunal (court), juez (judge), abogado (lawyer), fiscal (prosecutor), acusado (defendant), testigo (witness), jurado (jury)",
        proceedings: "audiencia (hearing), lectura de cargos (arraignment), fianza (bail), sentencia (sentence), apelación (appeal)",
        rights: "derecho a guardar silencio, derecho a un abogado, presunción de inocencia"
      },
      fr: {
        court: "tribunal (court), juge (judge), avocat (lawyer), procureur (prosecutor), accusé (defendant), témoin (witness), jury",
        proceedings: "audience (hearing), mise en accusation (arraignment), caution (bail), jugement (sentence), appel (appeal)",
        rights: "droit de garder le silence, droit à un avocat, présomption d'innocence"
      }
    },
    protocol: [
      "Court interpreters must use first person: 'I did not do it' not 'He says he did not do it'",
      "Request clarification through the judge, never directly with the witness",
      "Maintain the same register as the speaker — if they use slang, interpret the slang equivalent",
      "Legal terminology must be precise — 'homicidio involuntario' is NOT the same as 'asesinato'",
      "Miranda rights must be interpreted verbatim — no paraphrasing"
    ]
  }
};

/** Sentence-triggered grammar snippets (language-specific). */
const GRAMMAR_TRIGGERS = {
  es: [
    {
      id: 'si_clause',
      label: 'Si-clause (subjunctive)',
      test: s => /\bsi\b/i.test(s) && /\b(tendr[ií]a|har[ií]a|ser[ií]a|podr[ií]a|querr[ií]a|dir[ií]a|vendr[ií]a|tuviera|hiciera|fuera|pudiera)\b/i.test(s),
      rules: [
        'Si-clause (hypothetical): Si + imperfect subjunctive + conditional — Si yo tuviera tiempo, estudiaría (NOT Si yo tendría…)',
        'After «si» expressing unreal/hypothetical condition, use imperfect subjunctive (tuviera, fuera, pudiera), never conditional in the si-clause'
      ]
    },
    {
      id: 'subjunctive',
      label: 'Subjunctive triggers',
      test: s => /\b(espero|dudo|es importante|es necesario|ojal[aá]|quiz[aá]s|tal vez|aunque|para que|antes de que|sin que)\b/i.test(s),
      rules: [
        'Subjunctive triggers: querer/esperar/dudar que, es importante/necesario que, ojalá, para que, aunque (doubt/concession) + subjunctive',
        'Use indicative after «creo que» (affirmation) but subjunctive after «no creo que» or «dudo que»'
      ]
    },
    {
      id: 'register',
      label: 'Register (tú/usted)',
      test: s => /\b(señor|señora|doctor|doctora|usted|t[uú]|vos)\b/i.test(s),
      rules: [
        'Register: señor/señora + third person (está, tiene) = formal usted; do NOT «correct» to informal tú without context',
        'Interpreters maintain consistent register — mixing tú/usted in one professional exchange is an error'
      ]
    },
    {
      id: 'questions',
      label: 'Question punctuation',
      test: s => {
        const hasQWord = /\b(c[oó]mo|qu[eé]|d[oó]nde|cu[aá]ndo|cu[aá]nto|por qu[eé]|qui[eé]n)\b/i.test(s);
        return hasQWord && !/[¿]/.test(s);
      },
      rules: [
        'Spanish questions require inverted ¿ at the start: ¿Cómo está? (not Cómo está?)',
        'Exclamations use inverted ¡: ¡Qué bien!'
      ]
    },
    {
      id: 'por_para',
      label: 'Por vs para',
      test: s => /\b(por|para)\b/i.test(s),
      rules: [
        'Por = cause, exchange, duration, through; para = purpose, destination, deadline, recipient',
        'Avoid Anglicism «aplicar para un trabajo» → solicitar un empleo / postularse'
      ]
    },
    {
      id: 'preterite_imperfect',
      label: 'Past tense (preterite/imperfect)',
      test: s => /\b(com[ií]|hablaba|era|fue|estaba|estuve|hac[ií]a|hice|ten[ií]a|tuve)\b/i.test(s),
      rules: [
        'Preterite = completed, one-time past actions; imperfect = ongoing, habitual, or background past',
        'Imperfect for descriptions and interrupted actions: Llovía cuando salí'
      ]
    },
    {
      id: 'ser_estar',
      label: 'Ser vs estar',
      test: s => /\b(soy|eres|es|somos|son|estoy|est[aá]s|est[aá]|estamos|est[aá]n|fue|era|estuvo|estaba)\b/i.test(s),
      rules: [
        'Ser = identity, profession, origin, permanent traits; estar = location, temporary states, emotions',
        'Ser for professions without article: Es médico (not Es un médico in formal register contexts varies by region)'
      ]
    },
    {
      id: 'gustar',
      label: 'Gustar (indirect object)',
      test: s => /\b(me|te|le|les|nos|os)\s+gust(a|an)\b/i.test(s) || /\bgust(a|an)\b/i.test(s),
      rules: [
        'Gustar: indirect object + gustar + subject — Me gustan los libros (NOT yo gusto los libros)',
        'Subject agrees with thing liked: Me gusta el café / Me gustan las manzanas; use «a mí» for emphasis only'
      ]
    },
    {
      id: 'reflexive',
      label: 'Reflexive verbs',
      test: s => /\b(me|te|se|nos|os)\s+(levanto|levantas|levanta|ducho|duchas|visto|vistes|siento|sientes|acuesto|acuestas|llamo|llamas|preocupo|preocupa)\b/i.test(s),
      rules: [
        'Reflexive pronoun must match subject: me levanto, te duchas, se viste — not *me levanta for «I»',
        'Many reflexives change meaning: quedar (remain) vs quedarse (stay); ir vs irse (leave)'
      ]
    },
    {
      id: 'stem_change',
      label: 'Stem-changing verbs',
      test: s => /\b(puedo|puedes|puede|quiero|quieres|quiere|pienso|piensas|piensa|vuelvo|vuelves|vuelve|duermo|duermes|duerme|pido|pides|pide)\b/i.test(s),
      rules: [
        'Stem changes: e→ie (querer→quiero), o→ue (poder→puedo), e→i (pedir→pido) in present indicative',
        'Boot-shaped conjugation: nosotros/vosotros often regular (queremos, podemos) — do not over-correct standard forms'
      ]
    },
    {
      id: 'present_perfect',
      label: 'Present perfect (haber + participle)',
      test: s => /\b(he|has|ha|hemos|han|hab[eí]a)\s+\w+(ado|ido|cho|to|so|to)\b/i.test(s),
      rules: [
        'Present perfect: haber + past participle — He comido, Has dicho; participle agrees only with estar/passive/reflexive se',
        'Use for recent past or relevance to now; do not confuse with preterite for completed distant past'
      ]
    },
    {
      id: 'passive',
      label: 'Passive voice (ser + participle)',
      test: s => /\b(fue|fueron|es|son|ser[aá])\s+\w+(ado|ido|cho|to|so|to)\s+(por|de)\b/i.test(s),
      rules: [
        'True passive: ser + past participle + por — El informe fue escrito por el doctor',
        'Se passive / impersonal: Se habla español; distinguish from reflexive se'
      ]
    },
    {
      id: 'echar_de_menos',
      label: 'Echar de menos (direct object)',
      test: s => /\becho\s+de\s+menos\b/i.test(s),
      rules: [
        '«Echar de menos» takes a direct object pronoun: la echo de menos (her), lo echo de menos (him)',
        '«Le echo de menos» is leísmo; on exams use lo/la matching the person you miss'
      ]
    },
    {
      id: 'object_pronouns',
      label: 'Object pronouns (lo/la/le/se)',
      test: s => /\b(lo|la|los|las|le|les|se)\s+\w+/i.test(s) || /\b(me|te|nos|os)\s+(lo|la|los|las)\b/i.test(s) || /\becho\s+de\s+menos\b/i.test(s),
      rules: [
        'Clitic order: indirect before direct (me lo dio); se replaces le+lo → se lo',
        'Do not repeat full noun and pronoun: *el libro lo leí → Lo leí or Leí el libro',
        '«Echar de menos» + person missed → la/lo (direct), not le (leísmo)'
      ]
    },
    {
      id: 'gerund_progressive',
      label: 'Progressive (estar + gerund)',
      test: s => /\b(estoy|est[aá]s|est[aá]|estamos|est[aá]n)\s+\w+(ando|iendo)\b/i.test(s),
      rules: [
        'Progressive: estar + gerund — Estoy estudiando; not *soy estudiando',
        'Gerund not for future intent; use ir a + infinitive or future for planned actions'
      ]
    },
    {
      id: 'ir_a_infinitive',
      label: 'Near future (ir a + infinitive)',
      test: s => /\b(voy|vas|va|vamos|van)\s+a\s+\w+(ar|er|ir)\b/i.test(s),
      rules: [
        'Near future: ir + a + infinitive — Voy a estudiar mañana',
        'Do not insert «de» between a and infinitive: *voy a de estudiar is wrong'
      ]
    },
    {
      id: 'false_cognates',
      label: 'False cognates / Anglicisms',
      test: s => /\b(realizar|actualmente|aplicar|asistir|embarazada|sensible|bizarro|exitoso)\b/i.test(s),
      rules: [
        'False friends: embarazada = pregnant (NOT embarrassed); sensible = sensitive; realizar = to carry out (NOT to realize → darse cuenta)',
        'Anglicisms: actualmente = currently (NOT actually → en realidad); aplicar para → solicitar/postularse'
      ]
    },
    {
      id: 'gender_agreement',
      label: 'Gender & number agreement',
      test: s => /\b(la|las|el|los|una|un)\s+\w+(o|a|os|as)\b/i.test(s) && /\b(blanc[oa]|interesant[ea]|buen[oa]|nuev[oa]|roj[oa])\b/i.test(s),
      rules: [
        'Adjectives agree in gender and number with nouns: casa blanca, libros interesantes',
        'Watch invariant adjectives (verde, azul) and compound colors after noun in some dialects'
      ]
    },
    {
      id: 'conference',
      label: 'Conference interpreting',
      test: s => /\b(conferencia|interpretaci[oó]n|simult[aá]nea|consecutiva|delegaci[oó]n|palestra|orador|micr[oó]fono)\b/i.test(s),
      rules: [
        'Conference register: formal, complete sentences, neutral terminology; avoid regional slang unless speaker uses it',
        'Simultaneous vs consecutive modes require different note-taking and delivery — maintain speaker intent and register'
      ]
    }
  ],
  fr: [
    {
      id: 'subjunctive',
      label: 'Subjonctif',
      test: s => /\b(il faut|je veux|bien que|pour que|avant que|bien qu'|afin que|sans que|à condition que|avant que|quoique)\b/i.test(s),
      rules: [
        'Subjunctive after il faut que, vouloir que, bien que, pour que, avant que, afin que',
        'Indicative after affirmative « je pense que »; subjunctive after « je ne pense pas que » or « douter que »'
      ]
    },
    {
      id: 'register',
      label: 'Register (tu/vous)',
      test: s => /\b(monsieur|madame|docteur|doctoresse|vous|tu|professeur)\b/i.test(s),
      rules: [
        'Professional interpreting: default to vous with clients, providers, and officials',
        'Do not shift tu/vous mid-encounter without a clear speaker cue'
      ]
    },
    {
      id: 'pc_imparfait',
      label: 'Passé composé vs imparfait',
      test: s => /\b(j'ai|tu as|il a|nous avons|je suis|elle est|était|avait|faisait|a fait|avions|faisais)\b/i.test(s),
      rules: [
        'Passé composé = completed events; imparfait = descriptions, habits, background',
        'DR MRS VANDERTRAMP verbs use être in passé composé with agreement (elle est allée)'
      ]
    },
    {
      id: 'si_clause',
      label: 'Si-clause (hypothèse)',
      test: s => /\bsi\b/i.test(s) && /\b(j'aurais|j'aurais|tu aurais|il aurait|serais|serait|ferais|ferait|avais|était|faisait|pouvais|voulais)\b/i.test(s),
      rules: [
        'Hypothesis: Si + imparfait → conditionnel présent — Si j\'avais le temps, je voyagerais',
        'Do NOT use conditionnel in the si-clause: *Si j\'aurais su* → Si j\'avais su; pluperfect: Si j\'avais su, j\'aurais…'
      ]
    },
    {
      id: 'reflexive',
      label: 'Verbes pronominaux',
      test: s => /\b(me|te|se|nous|vous)\s+(lève|lèves|couche|couches|habille|habilles|suis|sent|sens|appelle|appelles|prépare|prépares)\b/i.test(s),
      rules: [
        'Reflexive pronoun agrees with subject: je me lève, tu te couches, il/elle se lève',
        'Reflexive vs non-reflexive changes meaning: passer (pass) vs se passer (happen)'
      ]
    },
    {
      id: 'etre_avoir',
      label: 'Être vs avoir',
      test: s => /\b(j'ai|tu as|il a|j'ai|je suis|tu es|il est)\s+(faim|soif|raison|tort|sommeil|\d+\s*ans|peur|besoin)\b/i.test(s),
      rules: [
        'Age, hunger, thirst: avoir — J\'ai 20 ans, J\'ai faim (NOT *je suis faim)',
        'Être for states/identity/nationality; avoir for possession and most idiomatic needs'
      ]
    },
    {
      id: 'partitive',
      label: 'Articles partitifs',
      test: s => /\b(du|de la|de l'|des|un peu de|beaucoup de)\b/i.test(s),
      rules: [
        'Partitive: du pain, de la confiture, de l\'eau, des légumes for unspecified quantity',
        'After negation: pas de (pas du pain); de + article after quantity expressions'
      ]
    },
    {
      id: 'futur_proche',
      label: 'Futur proche (aller + infinitif)',
      test: s => /\b(vais|vas|va|allons|allez|vont)\s+[a-zàâçéèêëîïôùûü'-]+/i.test(s),
      rules: [
        'Near future: aller + infinitive — Je vais étudier demain',
        'Do not conjugate the main verb in present when using futur proche'
      ]
    },
    {
      id: 'pc_etre',
      label: 'Passé composé avec être',
      test: s => /\b(je suis|tu es|il est|elle est|nous sommes|elles sont)\s+\w+(é|i|u|is|it|ert|enu|enu|enu)\b/i.test(s),
      rules: [
        'Movement/reflexive verbs use être: je suis allé(e), elle est partie, nous sommes arrivés',
        'Past participle agrees in gender/number with subject when auxiliary is être'
      ]
    },
    {
      id: 'negation',
      label: 'Négation (ne…pas)',
      test: s => /\b(ne|n')\s+\w+\s+(pas|plus|jamais|rien|personne)\b/i.test(s) || /\bpas\s+\w+/i.test(s),
      rules: [
        'Standard negation wraps the verb: ne…pas (Je ne parle pas); elision: n\' before vowel',
        'In formal speech/writing both ne and pas appear; in interpreting, preserve speaker\'s register'
      ]
    },
    {
      id: 'object_pronouns',
      label: 'Pronoms compléments (y, en, le)',
      test: s => /\b(y|en|le|la|les|lui|leur|me|te|nous|vous)\s+\w+/i.test(s) || /\b(l'|le|la|les|lui|leur)\s*(a|ai|as|ont|avons)\b/i.test(s),
      rules: [
        'Object pronouns precede the verb: Je le vois, Je lui parle; y = there/to it, en = some/of it',
        'Order: me/te/se/nous/vous + le/la/les + lui/leur + y + en + verb'
      ]
    },
    {
      id: 'false_cognates',
      label: 'Faux amis / anglicismes',
      test: s => /\b(réaliser|actuellement|attendre|déception|présentement|éventuellement|sensible|assister)\b/i.test(s),
      rules: [
        'Faux amis: réaliser = to carry out (NOT to realize → se rendre compte); actuellement = currently (NOT actually → en fait)',
        'Attendre = to wait (NOT to attend → assister à); sensible = sensitive; éventuellement = possibly'
      ]
    },
    {
      id: 'gender_agreement',
      label: 'Accord (genre/nombre)',
      test: s => /\b(un|une|le|la|les|des)\s+\w+/i.test(s) && /\b(petit|petite|grand|grande|blanc|blanche|intéressant|intéressante|nouveau|nouvelle)\b/i.test(s),
      rules: [
        'Adjectives agree: une maison blanche, des livres intéressants',
        'Watch invariable colors (marron, orange) and position (grand homme vs homme grand)'
      ]
    },
    {
      id: 'questions',
      label: 'Questions & punctuation',
      test: s => /\b(comment|pourquoi|où|quand|combien|est-ce que|qu'est-ce)\b/i.test(s) && /\w[?!;:]/.test(s),
      rules: [
        'French typography: space before ? ! ; : — Comment allez-vous ? (not Comment allez-vous?)',
        'Inversion or est-ce que for questions; maintain register (Pourriez-vous…? in formal settings)'
      ]
    },
    {
      id: 'conference',
      label: 'Interprétation de conférence',
      test: s => /\b(interprétation|simultanée|consécutive|conférence|délégation|microphone|orateur|boîte|cabine)\b/i.test(s),
      rules: [
        'Conference register: formal, complete sentences, neutral terminology; Canadian vs France vocabulary awareness',
        'Simultaneous vs consecutive modes — maintain speaker intent, register, and technical terms'
      ]
    }
  ]
};

const MEDICAL_KEYWORDS = {
  en: ['doctor', 'hospital', 'patient', 'medicine', 'surgery', 'diagnosis', 'treatment', 'health', 'pain', 'symptom', 'nurse', 'prescription', 'medication', 'clinic', 'emergency'],
  es: ['doctor', 'hospital', 'paciente', 'medicina', 'cirugía', 'diagnóstico', 'tratamiento', 'salud', 'dolor', 'síntoma', 'enfermera', 'médico', 'medicamento', 'clínica', 'urgencia', 'aine', 'suspender', 'receta', 'enfermedad'],
  fr: ['docteur', 'hôpital', 'patient', 'médecine', 'chirurgie', 'diagnostic', 'traitement', 'santé', 'douleur', 'symptôme', 'infirmière', 'médecin', 'médicament', 'clinique', 'urgence', 'suspendre', 'ordonnance', 'maladie', 'AINS', 'opération']
};

const LEGAL_KEYWORDS = {
  en: ['court', 'judge', 'lawyer', 'rights', 'arrest', 'bail', 'testimony', 'defendant', 'witness', 'trial', 'guilty', 'attorney', 'law'],
  es: ['tribunal', 'juez', 'abogado', 'derechos', 'arresto', 'fianza', 'testimonio', 'acusado', 'testigo', 'juicio', 'culpable', 'ley', 'fiscal', 'sentencia', 'audiencia'],
  fr: ['tribunal', 'juge', 'avocat', 'droits', 'arrestation', 'caution', 'témoignage', 'accusé', 'témoin', 'procès', 'coupable', 'loi', 'procureur', 'jugement']
};

const LEVEL_ORDER = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

function normalizeLevel(level) {
  if (level == null || level === '') return null;
  const u = String(level).toUpperCase().trim();
  return LEVEL_ORDER.includes(u) ? u : null;
}

function scoreLevelRule(rule, lowerSentence) {
  const words = rule.toLowerCase().split(/[^a-záéíóúüñàâçèêëîïôùû]+/).filter(w => w.length > 4);
  return words.reduce((n, w) => n + (lowerSentence.includes(w) ? 1 : 0), 0);
}

function pickLevelRules(grammarData, lowerSentence, maxRules) {
  if (!grammarData?.rules?.length) return [];
  const scored = grammarData.rules
    .map(rule => ({ rule, score: scoreLevelRule(rule, lowerSentence) }))
    .sort((a, b) => b.score - a.score);
  const picked = [];
  for (const { rule, score } of scored) {
    if (picked.length >= maxRules) break;
    if (score > 0 || picked.length === 0) picked.push(rule);
  }
  if (!picked.length) picked.push(grammarData.rules[0]);
  return picked;
}

function matchGrammarTriggers(langKey, lowerSentence) {
  const triggers = GRAMMAR_TRIGGERS[langKey] || [];
  return triggers.filter(t => t.test(lowerSentence));
}

function buildDomainContext(langKey, lowerSentence, condensed) {
  const parts = [];
  const topics = [];

  const medicalKws = [...(MEDICAL_KEYWORDS[langKey] || []), ...(MEDICAL_KEYWORDS.en || [])];
  if (medicalKws.some(kw => lowerSentence.includes(kw))) {
    topics.push('medical');
    parts.push('MEDICAL CONTEXT:');
    const t = RAG_KNOWLEDGE.medical.terminology[langKey];
    if (t) {
      if (condensed) {
        parts.push('Use precise medical terminology; maintain formal register with providers and patients.');
        parts.push('Ethics: accuracy, impartiality, confidentiality (HIPAA).');
      } else {
        parts.push('Body: ' + t.body);
        parts.push('Conditions: ' + t.conditions);
        parts.push('Procedures: ' + t.procedures);
        parts.push('Ethics: ' + RAG_KNOWLEDGE.medical.ethics.slice(0, 3).join(' | '));
      }
    }
  }

  const legalKws = [...(LEGAL_KEYWORDS[langKey] || []), ...(LEGAL_KEYWORDS.en || [])];
  if (legalKws.some(kw => lowerSentence.includes(kw))) {
    topics.push('legal');
    parts.push('LEGAL CONTEXT:');
    const t = RAG_KNOWLEDGE.legal.terminology[langKey];
    if (t) {
      if (condensed) {
        parts.push('Court interpreting: first person, precise legal terms, maintain speaker register.');
        parts.push('Protocol: request clarification through the judge; Miranda rights verbatim.');
      } else {
        parts.push('Court: ' + t.court);
        parts.push('Proceedings: ' + t.proceedings);
        parts.push('Rights: ' + t.rights);
        parts.push('Protocol: ' + RAG_KNOWLEDGE.legal.protocol.slice(0, 3).join(' | '));
      }
    }
  }

  return { parts, topics };
}

/**
 * Retrieve reference knowledge for AI analysis.
 * @param {string} language - 'es' | 'fr'
 * @param {string} level - CEFR level
 * @param {string} sentence - learner sentence
 * @param {{ condensed?: boolean }} options - condensed=true for on-device SLM (shorter context)
 */
function getRAGContextWithMeta(language, level, sentence, options = {}) {
  const condensed = !!options.condensed;
  const parts = [];
  const topics = [];
  const langKey = parlanceLanguageInfo(language).code;
  const levelNorm = normalizeLevel(level);
  const lowerSentence = sentence.toLowerCase();

  const triggered = matchGrammarTriggers(langKey, lowerSentence);
  triggered.forEach(t => {
    topics.push(t.id);
    parts.push('RELEVANT RULE — ' + t.label + ':');
    t.rules.forEach(r => parts.push('- ' + r));
  });

  const grammarData = levelNorm ? RAG_KNOWLEDGE.grammar[langKey]?.[levelNorm] : null;
  if (grammarData) {
    const maxLevelRules = condensed ? 1 : 3;
    const levelRules = pickLevelRules(grammarData, lowerSentence, maxLevelRules);
    if (levelRules.length) {
      topics.push('level_' + levelNorm.toLowerCase());
      parts.push('GRAMMAR RULES FOR ' + levelNorm + ':');
      levelRules.forEach(r => parts.push('- ' + r));
    }
    if (!condensed && grammarData.tips?.length) {
      parts.push('TIP: ' + grammarData.tips[0]);
    }
  }

  const examKey = parlanceLanguageInfo(langKey).examKey;
  const examLine = levelNorm ? RAG_KNOWLEDGE.exam[examKey]?.levels?.[levelNorm] : null;
  if (examLine) {
    topics.push(examKey);
    parts.push('EXAM CONTEXT: ' + examLine);
  }

  const domain = buildDomainContext(langKey, lowerSentence, condensed);
  parts.push(...domain.parts);
  topics.push(...domain.topics);

  let context = parts.join('\n').trim();
  const maxLen = condensed ? 900 : 2400;
  if (context.length > maxLen) {
    context = context.slice(0, maxLen) + '…';
  }

  const topicLabels = topics.map(id => {
    const trigger = (GRAMMAR_TRIGGERS[langKey] || []).find(t => t.id === id);
    if (trigger) return trigger.label;
    if (id === 'medical') return 'Medical interpreting';
    if (id === 'legal') return 'Legal interpreting';
    if (id.startsWith('level_')) return (levelNorm || '') + ' grammar';
    if (id === 'dele') return 'DELE exam';
    if (id === 'delf') return 'DELF exam';
    return id;
  });

  return {
    context,
    topics: [...new Set(topicLabels)]
  };
}

function getRAGContext(language, level, sentence, options) {
  return getRAGContextWithMeta(language, level, sentence, options).context;
}
