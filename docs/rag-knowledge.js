const RAG_KNOWLEDGE = {
  grammar: {
    es: {
      A1: {
        rules: [
          "Ser vs estar: ser for identity/characteristics, estar for location/states/feelings",
          "Present tense regular conjugation: -ar (-o,-as,-a,-amos,-áis,-an), -er (-o,-es,-e,-emos,-éis,-en), -ir (-o,-es,-e,-imos,-ís,-en)",
          "Gender agreement: nouns ending in -o are typically masculine, -a feminine; adjectives must match",
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

const MEDICAL_KEYWORDS = {
  en: ['doctor', 'hospital', 'patient', 'medicine', 'surgery', 'diagnosis', 'treatment', 'health', 'pain', 'symptom', 'nurse', 'prescription'],
  es: ['doctor', 'hospital', 'paciente', 'medicina', 'cirugía', 'diagnóstico', 'tratamiento', 'salud', 'dolor', 'síntoma', 'enfermera', 'médico'],
  fr: ['docteur', 'hôpital', 'patient', 'médecine', 'chirurgie', 'diagnostic', 'traitement', 'santé', 'douleur', 'symptôme', 'infirmière', 'médecin']
};

const LEGAL_KEYWORDS = {
  en: ['court', 'judge', 'lawyer', 'rights', 'arrest', 'bail', 'testimony', 'defendant', 'witness', 'trial', 'guilty', 'attorney', 'law'],
  es: ['tribunal', 'juez', 'abogado', 'derechos', 'arresto', 'fianza', 'testimonio', 'acusado', 'testigo', 'juicio', 'culpable', 'ley', 'fiscal'],
  fr: ['tribunal', 'juge', 'avocat', 'droits', 'arrestation', 'caution', 'témoignage', 'accusé', 'témoin', 'procès', 'coupable', 'loi', 'procureur']
};

function getRAGContext(language, level, sentence) {
  const parts = [];
  const langKey = language === 'fr' ? 'fr' : 'es';
  const lowerSentence = sentence.toLowerCase();

  const grammarData = RAG_KNOWLEDGE.grammar[langKey]?.[level];
  if (grammarData) {
    parts.push('GRAMMAR RULES FOR ' + level + ':');
    grammarData.rules.forEach(r => parts.push('- ' + r));
    grammarData.tips.forEach(t => parts.push('TIP: ' + t));
  }

  const examKey = langKey === 'es' ? 'dele' : 'delf';
  const examData = RAG_KNOWLEDGE.exam[examKey];
  if (examData?.levels?.[level]) {
    parts.push('\nEXAM CONTEXT: ' + examData.levels[level]);
  }

  const medicalKws = [...(MEDICAL_KEYWORDS[langKey] || []), ...(MEDICAL_KEYWORDS.en || [])];
  if (medicalKws.some(kw => lowerSentence.includes(kw))) {
    parts.push('\nMEDICAL CONTEXT:');
    const t = RAG_KNOWLEDGE.medical.terminology[langKey];
    if (t) { parts.push('Body: ' + t.body); parts.push('Conditions: ' + t.conditions); parts.push('Procedures: ' + t.procedures); }
    parts.push('Ethics: ' + RAG_KNOWLEDGE.medical.ethics.slice(0, 3).join(' | '));
  }

  const legalKws = [...(LEGAL_KEYWORDS[langKey] || []), ...(LEGAL_KEYWORDS.en || [])];
  if (legalKws.some(kw => lowerSentence.includes(kw))) {
    parts.push('\nLEGAL CONTEXT:');
    const t = RAG_KNOWLEDGE.legal.terminology[langKey];
    if (t) { parts.push('Court: ' + t.court); parts.push('Proceedings: ' + t.proceedings); parts.push('Rights: ' + t.rights); }
    parts.push('Protocol: ' + RAG_KNOWLEDGE.legal.protocol.slice(0, 3).join(' | '));
  }

  return parts.join('\n');
}
