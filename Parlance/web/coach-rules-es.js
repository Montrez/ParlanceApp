/** Auto-synced from shared/coach-rules/es.json — run scripts/sync_coach_rules.sh */
(function (root) {
  root.ParlanceCoachRulesES = {
  "version": 1,
  "lang": "es",
  "grammar_rule_default": "Spanish agreement, prepositions, and clause structure",
  "feminine_nouns": [
    "aplicación",
    "aplicacion",
    "cosa",
    "cosas",
    "casa",
    "mesa",
    "programa",
    "tarea",
    "tareas"
  ],
  "rules": [
    {
      "id": "punctuation_question",
      "category": "punctuation",
      "priority": 5,
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
      "grammar_rule": "Inverted question marks (¿…?)"
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
      "grammar_rule": "Gender agreement (adjective + noun)"
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
      "grammar_rule": "Complementizer «que» before infinitive clauses"
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
      "grammar_rule": "Por vs para (purpose/destination)"
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
      "grammar_rule": "Definite article with abstract/work nouns"
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
      "grammar_rule": "«Tener que + infinitive» and gender agreement"
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
      "grammar_rule": "«Tener que + infinitive» (obligation)"
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
      "grammar_rule": "Indicative vs subjunctive with obligation"
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
      "grammar_rule": "Gender agreement (todo/toda + feminine noun)"
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
      "grammar_rule": "Gender agreement (todo/toda + feminine noun)"
    },
    {
      "id": "terminar_todo_app",
      "category": "agreement",
      "priority": 52,
      "detect": {
        "pattern": "\\bterminar\\s+todo\\s+por\\s+nuestra\\s+la\\s+aplicaci",
        "flags": "i"
      },
      "issue": "Use «terminar toda la aplicación en nuestra aplicación» — fix gender and article stacking.",
      "mention": [
        "toda la aplicación",
        "nuestra aplicación"
      ],
      "repair": [
        {
          "pattern": "\\bterminar\\s+todo\\s+por\\s+nuestra\\s+la\\s+aplicaci([oó]n)",
          "replace": "terminar toda la aplicación en nuestra aplicación",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Gender agreement and possessive + noun"
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
      "grammar_rule": "Possessive + noun (no extra article)"
    },
    {
      "id": "terminar_todo",
      "category": "agreement",
      "priority": 54,
      "detect": {
        "pattern": "\\bterminar\\s+todo\\b",
        "flags": "i",
        "unless_pattern": "\\bterminar\\s+toda\\b"
      },
      "issue": "When the object is feminine (e.g. la aplicación), use «terminar toda la aplicación».",
      "mention": [
        "toda la aplicación",
        "terminar toda"
      ],
      "repair": [
        {
          "pattern": "\\bterminar\\s+todo\\b",
          "replace": "terminar toda la aplicación",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Gender agreement with direct objects"
    },
    {
      "id": "tenemos_todo_no_toda",
      "category": "agreement",
      "priority": 55,
      "detect": {
        "pattern": "\\btenemos\\s+todo\\b",
        "flags": "i",
        "unless_pattern": "\\btoda\\b"
      },
      "issue": "With a feminine noun like «aplicación», use «tenemos que terminar toda la aplicación».",
      "mention": [
        "toda la aplicación",
        "tenemos que"
      ],
      "repair": [
        {
          "pattern": "\\btenemos\\s+todo\\b",
          "replace": "tenemos que terminar toda la aplicación",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Gender agreement and «tener que + infinitive»"
    },
    {
      "id": "por_nuestra_aplicacion",
      "category": "prepositions",
      "priority": 60,
      "detect": {
        "pattern": "\\bpor\\s+nuestra\\s+aplicaci",
        "flags": "i"
      },
      "issue": "Location/context on an app is usually «en nuestra aplicación», not «por nuestra aplicación».",
      "mention": [
        "en nuestra aplicación"
      ],
      "repair": [
        {
          "pattern": "\\bpor\\s+nuestra\\s+aplicaci",
          "replace": "en nuestra aplicación",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Por vs en (location/context)"
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
      "grammar_rule": "«Tener que + infinitive»"
    }
  ]
};
})(typeof globalThis !== "undefined" ? globalThis : this);
