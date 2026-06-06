/** Auto-synced from shared/coach-rules/es.json — run scripts/sync_coach_rules.sh */
(function (root) {
  root.ParlanceCoachRulesES = {
  "version": 2,
  "lang": "es",
  "standard_version": 1,
  "standard_path": "shared/standards/es-coach-standard.json",
  "grammar_rule_default": "Spanish agreement, prepositions, and clause structure",
  "feminine_nouns": [
    "aplicación",
    "aplicacion",
    "cosa",
    "cosas",
    "casa",
    "mesa",
    "tarea",
    "tareas"
  ],
  "rules": [
    {
      "id": "si_clause_conditional_protasis",
      "category": "verb_mood",
      "priority": 8,
      "detect": {
        "pattern": "\\bsi\\b[^.!?]*\\b(tendr[ií]a|har[ií]a|ser[ií]a|podr[ií]a|querr[ií]a|dir[ií]a|vendr[ií]a)\\b",
        "flags": "i"
      },
      "issue": "After «si» (hypothetical), use imperfect subjunctive in the protasis (e.g. «tuviera»), not conditional («tendría»).",
      "mention": [
        "tuviera",
        "imperfect subjunctive",
        "si clause"
      ],
      "repair": [
        {
          "pattern": "\\btendr[ií]a\\b",
          "replace": "tuviera",
          "flags": "gi"
        },
        {
          "pattern": "\\bhar[ií]a\\b",
          "replace": "hiciera",
          "flags": "gi"
        },
        {
          "pattern": "\\bser[ií]a\\b",
          "replace": "fuera",
          "flags": "gi"
        },
        {
          "pattern": "\\bpodr[ií]a\\b",
          "replace": "pudiera",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Si clauses: imperfect subjunctive in protasis, conditional in main clause",
      "source": {
        "authority": "RAE-DPD",
        "topic": "Oraciones condicionales",
        "url": "https://www.rae.es/dpd/oracion%20condicional"
      },
      "cefr": {
        "teach_from": "B2",
        "band": "B2"
      },
      "regression": [
        "si_clause_tendria"
      ]
    },
    {
      "id": "que_clause_infinitive_subjunctive",
      "category": "verb_mood",
      "priority": 6,
      "detect": {
        "pattern": "\\b(espero|quiero|deseo|necesito|ojal[aá])\\s+que\\s+[^.!?]*\\b(todos|todo|t[uú]|ell[oa]|nosotros|usted|ustedes)\\s+(ir|ser|estar|tener|hacer|poder|venir|decir)\\b",
        "flags": "i",
        "unless_pattern": "\\b(vaya|vayan|sea|sean|est[eé]|est[eé]n|tenga|tengan|haga|hagan|pueda|puedan|venga|vengan|diga|digan)\\b"
      },
      "issue": "After a subjunctive trigger («espero que», «quiero que»…), use subjunctive in the subordinate clause — not a bare infinitive («todos ir» → «todos vayan»).",
      "mention": [
        "subjunctive",
        "espero que",
        "vayan",
        "present subjunctive"
      ],
      "repair": [
        {
          "pattern": "\\btodos\\s+ir\\b",
          "replace": "todos vayan",
          "flags": "gi"
        },
        {
          "pattern": "\\btodo\\s+ir\\b",
          "replace": "todo vaya",
          "flags": "gi"
        },
        {
          "pattern": "\\btodos\\s+ser\\b",
          "replace": "todos sean",
          "flags": "gi"
        },
        {
          "pattern": "\\btodo\\s+ser\\b",
          "replace": "todo sea",
          "flags": "gi"
        },
        {
          "pattern": "\\btodos\\s+estar\\b",
          "replace": "todos estén",
          "flags": "gi"
        },
        {
          "pattern": "\\btodo\\s+estar\\b",
          "replace": "todo esté",
          "flags": "gi"
        },
        {
          "pattern": "\\btodos\\s+tener\\b",
          "replace": "todos tengan",
          "flags": "gi"
        },
        {
          "pattern": "\\btodo\\s+tener\\b",
          "replace": "todo tenga",
          "flags": "gi"
        },
        {
          "pattern": "\\btodos\\s+hacer\\b",
          "replace": "todos hagan",
          "flags": "gi"
        },
        {
          "pattern": "\\btodo\\s+hacer\\b",
          "replace": "todo haga",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Subjunctive after «espero que» / «quiero que» — not infinitive in the subordinate clause",
      "source": {
        "authority": "RAE-DPD",
        "topic": "Modo subjuntivo / oraciones subordinadas",
        "url": "https://www.rae.es/dpd/modo%20subjuntivo"
      },
      "cefr": {
        "teach_from": "B2",
        "band": "B2"
      },
      "regression": [
        "espero_que_subjunctive"
      ]
    },
    {
      "id": "leismo_echar_de_menos_feminine",
      "category": "pronouns",
      "priority": 9,
      "detect": {
        "pattern": "\\b(le|les)\\s+echo\\s+de\\s+menos\\b",
        "flags": "i",
        "require_pattern": "\\b(novia|novia|madre|hermana|esposa|mujer|amiga|hija|abuela|ella)\\b"
      },
      "issue": "«Echar de menos» takes a direct object: «la echo de menos», not leísmo «le echo de menos».",
      "mention": [
        "la echo de menos",
        "direct object",
        "leísmo"
      ],
      "repair": [
        {
          "pattern": "\\bles\\s+echo\\s+de\\s+menos\\b",
          "replace": "las echo de menos",
          "flags": "gi"
        },
        {
          "pattern": "\\ble\\s+echo\\s+de\\s+menos\\b",
          "replace": "la echo de menos",
          "flags": "gi"
        }
      ],
      "grammar_rule": "«Echar de menos» + direct object pronoun (lo/la)",
      "source": {
        "authority": "RAE-DPD",
        "topic": "Pronombres átonos / leísmo",
        "url": "https://www.rae.es/dpd/le%C3%ADsmo"
      },
      "cefr": {
        "teach_from": "B1",
        "band": "B1-B2"
      },
      "regression": [
        "leismo_novia"
      ]
    },
    {
      "id": "accent_comi",
      "category": "orthography",
      "priority": 12,
      "detect": {
        "pattern": "\\bcomi\\b",
        "flags": "i",
        "unless_pattern": "\\bcomí\\b"
      },
      "issue": "Preterite «comí» requires a written accent on the final syllable.",
      "mention": [
        "comí",
        "accent",
        "tilde"
      ],
      "repair": [
        {
          "pattern": "\\bcomi\\b",
          "replace": "comí",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Written accent marks (tildes) on past-tense verb forms",
      "source": {
        "authority": "RAE",
        "topic": "Ortografía / acentuación",
        "url": "https://www.rae.es/dpd/tilde%20diacr%C3%ADtica"
      },
      "cefr": {
        "teach_from": "A2",
        "band": "A2"
      },
      "regression": [
        "accent_comi_ayer"
      ]
    },
    {
      "id": "punctuation_question",
      "category": "punctuation",
      "priority": 15,
      "detect": {
        "pattern": "\\?",
        "unless": "¿"
      },
      "issue": "Spanish questions need an opening «¿» before the question clause.",
      "mention": [
        "¿",
        "inverted question"
      ],
      "repair": [
        {
          "pattern": "^",
          "replace": "¿",
          "flags": "",
          "once": true
        }
      ],
      "grammar_rule": "Inverted question marks (¿…?)",
      "source": {
        "authority": "RAE",
        "topic": "Signos de interrogación",
        "url": "https://www.rae.es/dpd/signos%20de%20interrogaci%C3%B3n"
      },
      "cefr": {
        "teach_from": "A1",
        "band": "A1-A2"
      },
      "regression": []
    },
    {
      "id": "como_es_wellbeing",
      "category": "verb_mood",
      "priority": 14,
      "detect": {
        "pattern": "[Cc][óo]mo\\s+es\\b",
        "flags": "i",
        "require_pattern": "(?i)\\b(usted|t[uú]|se[nñ]or|se[nñ]ora|d[ií]a)\\b",
        "unless_pattern": "(?i)usted\\s+d[ií]a\\s+se[nñ]"
      },
      "issue": "Asking after someone's state uses «¿Cómo está …?» (estar), not «Cómo es …» (ser).",
      "mention": [
        "cómo está",
        "ser vs estar",
        "wellbeing"
      ],
      "repair": [
        {
          "pattern": "\\b[Cc][óo]mo\\s+es\\b",
          "replace": "¿Cómo está",
          "flags": "g"
        }
      ],
      "grammar_rule": "Ser vs estar — «¿Cómo está?» for wellbeing",
      "source": {
        "authority": "RAE-DPD",
        "topic": "Ser / estar",
        "url": "https://www.rae.es/dpd/ser"
      },
      "cefr": {
        "teach_from": "A1",
        "band": "A1-A2"
      },
      "regression": [
        "como_es_greeting"
      ]
    },
    {
      "id": "greeting_vocative_order",
      "category": "syntax",
      "priority": 16,
      "detect": {
        "pattern": "(?i)\\b(usted|t[uú])\\s+(d[ií]a)\\b",
        "unless_pattern": "(?i)\\b(su|t[uú])\\s+d[ií]a\\b|\\bhoy\\b"
      },
      "issue": "Use «¿Cómo está usted hoy, señor?» — estar (not ser) for wellbeing, with natural vocative order.",
      "mention": [
        "cómo está",
        "ser vs estar",
        "word order",
        "vocative",
        "hoy"
      ],
      "repair": [
        {
          "pattern": "(?i)[Cc][óo]mo\\s+es\\s+usted\\s+d[ií]a\\s+(se[nñ]or|se[nñ]ora)\\b",
          "replace": "¿Cómo está usted hoy, \\1",
          "flags": "g"
        },
        {
          "pattern": "(?i)¿Cómo está\\s+usted\\s+d[ií]a\\s+(se[nñ]or|se[nñ]ora)\\b",
          "replace": "¿Cómo está usted hoy, \\1",
          "flags": "g"
        }
      ],
      "grammar_rule": "Ser vs estar + word order in formal greetings",
      "source": {
        "authority": "RAE",
        "topic": "Orden de palabras / vocativo",
        "url": "https://www.rae.es/dpd/vocativo"
      },
      "cefr": {
        "teach_from": "A2",
        "band": "A2-B1"
      },
      "regression": [
        "como_es_greeting"
      ]
    },
    {
      "id": "para_purpose_infinitive",
      "category": "prepositions",
      "priority": 27,
      "detect": {
        "pattern": "\\b(a)\\s+(ver|hacer|comprar|ir|llegar|terminar)\\s+(un|una|el|la|al|a la)\\b",
        "flags": "i",
        "unless_pattern": "\\bpara\\s+(ver|hacer|comprar|ir|llegar|terminar)\\b"
      },
      "issue": "Purpose before an infinitive uses «para» (e.g. «dinero para ver»), not bare «a».",
      "mention": [
        "para ver",
        "por vs para",
        "purpose"
      ],
      "repair": [
        {
          "pattern": "\\b(a)\\s+(ver|hacer|comprar|ir|llegar|terminar)\\s+(un|una|el|la|al|a la)\\b",
          "replace": "para \\2 \\3",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Por vs para — purpose before infinitive",
      "source": {
        "authority": "RAE-DPD",
        "topic": "Por / para",
        "url": "https://www.rae.es/dpd/por"
      },
      "cefr": {
        "teach_from": "A2",
        "band": "A2-B1"
      },
      "regression": [
        "para_purpose_ver"
      ]
    },
    {
      "id": "gender_muchas_cosas",
      "category": "agreement",
      "priority": 20,
      "detect": {
        "pattern": "\\bmuchos\\s+cosas\\b",
        "flags": "i"
      },
      "issue": "«muchos cosas» → «muchas cosas»: cosas is feminine — the adjective must agree.",
      "mention": [
        "muchas cosas",
        "feminine agreement"
      ],
      "repair": [
        {
          "pattern": "\\bmuchos\\s+cosas\\b",
          "replace": "muchas cosas",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Gender agreement (adjective + noun)",
      "source": {
        "authority": "RAE-DPD",
        "topic": "Concordancia de género",
        "url": "https://www.rae.es/dpd/concordancia"
      },
      "cefr": {
        "teach_from": "A1",
        "band": "A1-A2"
      },
      "regression": [
        "gender_muchas"
      ]
    },
    {
      "id": "que_before_infinitive",
      "category": "syntax",
      "priority": 25,
      "detect": {
        "pattern": "\\bcosas\\s+hacer\\b",
        "flags": "i",
        "unless_pattern": "\\bcosas\\s+que\\s+hacer\\b"
      },
      "issue": "Missing «que» before the infinitive: say «cosas que hacer», not «cosas hacer».",
      "mention": [
        "cosas que hacer",
        "que before the infinitive"
      ],
      "repair": [
        {
          "pattern": "\\bcosas\\s+(?!que\\s+)hacer\\b",
          "replace": "cosas que hacer",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Complementizer «que» before infinitive clauses",
      "source": {
        "authority": "RAE",
        "topic": "Oraciones subordinadas",
        "url": "https://www.rae.es/dpd/que"
      },
      "cefr": {
        "teach_from": "A2",
        "band": "A2-B1"
      },
      "regression": [
        "que_infinitive"
      ]
    },
    {
      "id": "por_para_trabajo",
      "category": "prepositions",
      "priority": 30,
      "detect": {
        "pattern": "\\bpor\\s+(el\\s+)?trabajo\\b",
        "flags": "i",
        "unless_pattern": "\\bpara\\s+(el\\s+)?trabajo\\b"
      },
      "issue": "Purpose or goal uses «para (el) trabajo», not «por trabajo».",
      "mention": [
        "para el trabajo",
        "por vs para"
      ],
      "repair": [
        {
          "pattern": "\\bpor\\s+(el\\s+)?trabajo\\b",
          "replace": "para el trabajo",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Por vs para (purpose/destination)",
      "source": {
        "authority": "RAE-DPD",
        "topic": "Por / para",
        "url": "https://www.rae.es/dpd/por"
      },
      "cefr": {
        "teach_from": "B1",
        "band": "A2-B1"
      },
      "regression": [
        "por_para_trabajo"
      ]
    },
    {
      "id": "para_el_trabajo",
      "category": "articles",
      "priority": 31,
      "detect": {
        "pattern": "\\bpara\\s+trabajo\\b",
        "flags": "i",
        "unless_pattern": "\\bpara\\s+el\\s+trabajo\\b"
      },
      "issue": "Add the definite article: «para el trabajo», not «para trabajo».",
      "mention": [
        "para el trabajo"
      ],
      "repair": [
        {
          "pattern": "\\bpara\\s+trabajo\\b",
          "replace": "para el trabajo",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Definite article with abstract/work nouns",
      "source": {
        "authority": "RAE",
        "topic": "Artículo definido",
        "url": "https://www.rae.es/dpd/articulo%20definido"
      },
      "cefr": {
        "teach_from": "A2",
        "band": "A2-B1"
      },
      "regression": [
        "workday_app"
      ]
    },
    {
      "id": "tenemos_que_tenamos_todo_app",
      "category": "verb_mood",
      "priority": 40,
      "detect": {
        "pattern": "\\btenamos\\s+todo\\s+por\\s+la\\s+aplicaci",
        "flags": "i"
      },
      "issue": "Use «tenemos que + infinitive» and feminine «toda la aplicación», not «tenamos todo por la aplicación».",
      "mention": [
        "tenemos que",
        "toda la aplicación"
      ],
      "repair": [
        {
          "pattern": "\\btenamos\\s+todo\\s+por\\s+la\\s+aplicaci([oó]n)",
          "replace": "tenemos que terminar toda la aplicación",
          "flags": "gi"
        }
      ],
      "grammar_rule": "«Tener que + infinitive» and gender agreement",
      "source": {
        "authority": "RAE",
        "topic": "Perífrasis «tener que + infinitivo»",
        "url": "https://www.rae.es/dpd/tener%20que"
      },
      "cefr": {
        "teach_from": "B1",
        "band": "B1"
      },
      "regression": [
        "workday_app"
      ]
    },
    {
      "id": "tenemos_que_tenamos_terminar",
      "category": "verb_mood",
      "priority": 41,
      "detect": {
        "pattern": "\\btenamos\\s+terminar\\b",
        "flags": "i"
      },
      "issue": "Use indicative «tenemos que + infinitive», not «tenamos terminar».",
      "mention": [
        "tenemos que",
        "tenamos terminar"
      ],
      "repair": [
        {
          "pattern": "\\btenamos\\s+terminar\\b",
          "replace": "tenemos que terminar",
          "flags": "gi"
        }
      ],
      "grammar_rule": "«Tener que + infinitive» (obligation)",
      "source": {
        "authority": "RAE",
        "topic": "Perífrasis «tener que + infinitivo»",
        "url": "https://www.rae.es/dpd/tener%20que"
      },
      "cefr": {
        "teach_from": "B1",
        "band": "B1"
      },
      "regression": []
    },
    {
      "id": "tenemos_que_tenamos",
      "category": "verb_mood",
      "priority": 42,
      "detect": {
        "pattern": "\\btenamos\\b",
        "flags": "i"
      },
      "issue": "Use indicative «tenemos que + infinitive», not subjunctive «tenamos».",
      "mention": [
        "tenemos que",
        "tenamos"
      ],
      "repair": [
        {
          "pattern": "\\btenamos\\b",
          "replace": "tenemos que",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Indicative vs subjunctive with obligation",
      "source": {
        "authority": "RAE",
        "topic": "Modo subjuntivo vs indicativo",
        "url": "https://www.rae.es/dpd/subjuntivo"
      },
      "cefr": {
        "teach_from": "B1",
        "band": "B1"
      },
      "regression": []
    },
    {
      "id": "todo_por_la_aplicacion",
      "category": "agreement",
      "priority": 50,
      "detect": {
        "pattern": "\\btodo\\s+por\\s+la\\s+aplicaci",
        "flags": "i"
      },
      "issue": "«Aplicación» is feminine — use «toda la aplicación»; avoid «todo por la aplicación».",
      "mention": [
        "toda la aplicación",
        "todo por la"
      ],
      "repair": [
        {
          "pattern": "\\btodo\\s+por\\s+la\\s+aplicaci([oó]n)",
          "replace": "toda la aplicación",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Gender agreement (todo/toda + feminine noun)",
      "source": {
        "authority": "RAE-DPD",
        "topic": "Concordancia de género",
        "url": "https://www.rae.es/dpd/concordancia"
      },
      "cefr": {
        "teach_from": "A2",
        "band": "A2-B1"
      },
      "regression": [
        "workday_app"
      ]
    },
    {
      "id": "todo_la_aplicacion",
      "category": "agreement",
      "priority": 51,
      "detect": {
        "pattern": "\\btodo\\s+la\\s+aplicaci",
        "flags": "i"
      },
      "issue": "«Aplicación» is feminine — use «toda la aplicación», not «todo la aplicación».",
      "mention": [
        "toda la aplicación",
        "feminine todo/toda"
      ],
      "repair": [
        {
          "pattern": "\\btodo\\s+la\\s+aplicaci([oó]n)",
          "replace": "toda la aplicación",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Gender agreement (todo/toda + feminine noun)",
      "source": {
        "authority": "RAE-DPD",
        "topic": "Concordancia de género",
        "url": "https://www.rae.es/dpd/concordancia"
      },
      "cefr": {
        "teach_from": "A2",
        "band": "A2-B1"
      },
      "regression": []
    },
    {
      "id": "nuestra_la_aplicacion",
      "category": "articles",
      "priority": 53,
      "detect": {
        "pattern": "\\bnuestra\\s+la\\s+aplicaci",
        "flags": "i"
      },
      "issue": "Do not stack possessive + article: «nuestra aplicación», not «nuestra la aplicación».",
      "mention": [
        "nuestra la",
        "nuestra aplicación"
      ],
      "repair": [
        {
          "pattern": "\\bnuestra\\s+la\\s+aplicaci([oó]n)",
          "replace": "nuestra aplicación",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Possessive + noun (no extra article)",
      "source": {
        "authority": "RAE",
        "topic": "Posesivos",
        "url": "https://www.rae.es/dpd/posesivo"
      },
      "cefr": {
        "teach_from": "A2",
        "band": "A2-B1"
      },
      "regression": []
    },
    {
      "id": "double_que",
      "category": "syntax",
      "priority": 90,
      "detect": {
        "pattern": "\\btenemos que que\\b",
        "flags": "i"
      },
      "issue": "Remove the duplicated «que»: «tenemos que + infinitive».",
      "mention": [
        "tenemos que que"
      ],
      "repair": [
        {
          "pattern": "\\btenemos que que\\b",
          "replace": "tenemos que",
          "flags": "gi"
        }
      ],
      "grammar_rule": "«Tener que + infinitive»",
      "source": {
        "authority": "RAE",
        "topic": "Perífrasis «tener que + infinitivo»",
        "url": "https://www.rae.es/dpd/tener%20que"
      },
      "cefr": {
        "teach_from": "B1",
        "band": "B1"
      },
      "regression": []
    }
  ]
};
})(typeof globalThis !== "undefined" ? globalThis : this);
