/** Auto-synced from shared/coach-rules/en.json — run scripts/sync_coach_rules.sh */
(function (root) {
  root.ParlanceCoachRulesEN = {
  "version": 1,
  "lang": "en",
  "standard_version": 1,
  "standard_path": "shared/standards/en-coach-standard.json",
  "grammar_rule_default": "English articles, prepositions, conditionals, and register for Spanish/French L1 speakers",
  "rules": [
    {
      "id": "if_would_protasis",
      "category": "verb_mood",
      "priority": 8,
      "detect": {
        "pattern": "\\bif\\b[^,.!?]*\\bwould\\b",
        "flags": "i",
        "unless_pattern": "\\bif\\s+(i|you|he|she|it|we|they)\\s+would\\s+(like|prefer|rather|say|suggest|recommend)\\b"
      },
      "issue": "Never use «would» in the if-clause (protasis) — a direct calque from «si + tendría/aurais». Use «if + past» for unreal conditions, «would» only in the result clause.",
      "mention": [
        "if I had",
        "conditional",
        "if-clause",
        "protasis"
      ],
      "repair": [
        {
          "pattern": "\\bif\\s+i\\s+would\\s+have\\b",
          "replace": "if I had",
          "flags": "gi"
        },
        {
          "pattern": "\\bif\\s+you\\s+would\\s+have\\b",
          "replace": "if you had",
          "flags": "gi"
        },
        {
          "pattern": "\\bif\\s+he\\s+would\\s+have\\b",
          "replace": "if he had",
          "flags": "gi"
        },
        {
          "pattern": "\\bif\\s+she\\s+would\\s+have\\b",
          "replace": "if she had",
          "flags": "gi"
        },
        {
          "pattern": "\\bif\\s+i\\s+would\\b",
          "replace": "if I had",
          "flags": "gi"
        },
        {
          "pattern": "\\bif\\s+you\\s+would\\b",
          "replace": "if you had",
          "flags": "gi"
        },
        {
          "pattern": "\\bif\\s+he\\s+would\\b",
          "replace": "if he had",
          "flags": "gi"
        },
        {
          "pattern": "\\bif\\s+she\\s+would\\b",
          "replace": "if she had",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Conditionals: «would» never appears in the if-clause",
      "source": {
        "authority": "Practical English Usage (Swan)",
        "topic": "Conditional sentences"
      },
      "cefr": {
        "teach_from": "B1",
        "band": "B1-B2"
      },
      "regression": [
        "if_would_have"
      ]
    },
    {
      "id": "depend_of",
      "category": "prepositions",
      "priority": 20,
      "detect": {
        "pattern": "\\bdepends?\\s+of\\b",
        "flags": "i"
      },
      "issue": "«Depend» takes «on», not «of» (calque from «depender de» / «dépendre de»).",
      "mention": [
        "depend on",
        "preposition"
      ],
      "repair": [
        {
          "pattern": "\\b(depends?)\\s+of\\b",
          "replace": "\\1 on",
          "flags": "gi"
        }
      ],
      "grammar_rule": "«Depend on» (not «depend of»)",
      "source": {
        "authority": "Practical English Usage (Swan)",
        "topic": "Preposition after verb"
      },
      "cefr": {
        "teach_from": "A2",
        "band": "A2-B1"
      },
      "regression": [
        "depend_of_context"
      ]
    },
    {
      "id": "discuss_about",
      "category": "prepositions",
      "priority": 21,
      "detect": {
        "pattern": "\\bdiscuss(ed|ing|es)?\\s+about\\b",
        "flags": "i"
      },
      "issue": "«Discuss» is directly transitive in English — do not add «about» (calque from «discutir de/sobre», «discuter de»).",
      "mention": [
        "discuss",
        "no preposition"
      ],
      "repair": [
        {
          "pattern": "\\b(discuss(?:ed|ing|es)?)\\s+about\\b",
          "replace": "\\1",
          "flags": "gi"
        }
      ],
      "grammar_rule": "«Discuss» + object (no «about»)",
      "source": {
        "authority": "Practical English Usage (Swan)",
        "topic": "Transitive verbs without a preposition"
      },
      "cefr": {
        "teach_from": "A2",
        "band": "A2-B1"
      },
      "regression": [
        "discuss_about_topic"
      ]
    },
    {
      "id": "interested_by",
      "category": "prepositions",
      "priority": 22,
      "detect": {
        "pattern": "\\binterested\\s+(by|of)\\b",
        "flags": "i"
      },
      "issue": "«Interested» takes «in», not «by»/«of» (calque from «interesado por/en», «intéressé par»).",
      "mention": [
        "interested in",
        "preposition"
      ],
      "repair": [
        {
          "pattern": "\\binterested\\s+(by|of)\\b",
          "replace": "interested in",
          "flags": "gi"
        }
      ],
      "grammar_rule": "«Interested in» (not «interested by/of»)",
      "source": {
        "authority": "Practical English Usage (Swan)",
        "topic": "Preposition after adjective"
      },
      "cefr": {
        "teach_from": "A2",
        "band": "A2-B1"
      },
      "regression": [
        "interested_by_topic"
      ]
    },
    {
      "id": "married_with",
      "category": "prepositions",
      "priority": 23,
      "detect": {
        "pattern": "\\bmarried\\s+with\\b",
        "flags": "i"
      },
      "issue": "«Married» takes «to», not «with» (calque from «casado con», «marié avec»).",
      "mention": [
        "married to",
        "preposition"
      ],
      "repair": [
        {
          "pattern": "\\bmarried\\s+with\\b",
          "replace": "married to",
          "flags": "gi"
        }
      ],
      "grammar_rule": "«Married to» (not «married with»)",
      "source": {
        "authority": "Practical English Usage (Swan)",
        "topic": "Preposition after adjective"
      },
      "cefr": {
        "teach_from": "A2",
        "band": "A2-B1"
      },
      "regression": [
        "married_with_partner"
      ]
    },
    {
      "id": "uncountable_indefinite_article",
      "category": "articles",
      "priority": 30,
      "detect": {
        "pattern": "\\b(a|an)\\s+(advice|information|news|furniture|homework)\\b",
        "flags": "i"
      },
      "issue": "«Advice/information/news/furniture/homework» are uncountable — never use «a/an» with them; say «some advice», «a piece of advice», etc.",
      "mention": [
        "uncountable noun",
        "no indefinite article"
      ],
      "repair": [
        {
          "pattern": "\\b(a|an)\\s+advice\\b",
          "replace": "some advice",
          "flags": "gi"
        },
        {
          "pattern": "\\b(a|an)\\s+information\\b",
          "replace": "some information",
          "flags": "gi"
        },
        {
          "pattern": "\\b(a|an)\\s+news\\b",
          "replace": "some news",
          "flags": "gi"
        },
        {
          "pattern": "\\b(a|an)\\s+furniture\\b",
          "replace": "some furniture",
          "flags": "gi"
        },
        {
          "pattern": "\\b(a|an)\\s+homework\\b",
          "replace": "some homework",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Uncountable nouns take no indefinite article",
      "source": {
        "authority": "Practical English Usage (Swan)",
        "topic": "Countable and uncountable nouns"
      },
      "cefr": {
        "teach_from": "A2",
        "band": "A2-B1"
      },
      "regression": [
        "an_advice"
      ]
    },
    {
      "id": "informations_plural",
      "category": "articles",
      "priority": 31,
      "detect": {
        "pattern": "\\b(informations|advices|furnitures)\\b",
        "flags": "i"
      },
      "issue": "Uncountable nouns («information», «advice», «furniture») have no plural «-s» form.",
      "mention": [
        "uncountable noun",
        "no plural"
      ],
      "repair": [
        {
          "pattern": "\\binformations\\b",
          "replace": "information",
          "flags": "gi"
        },
        {
          "pattern": "\\badvices\\b",
          "replace": "pieces of advice",
          "flags": "gi"
        },
        {
          "pattern": "\\bfurnitures\\b",
          "replace": "furniture",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Uncountable nouns have no plural form",
      "source": {
        "authority": "Practical English Usage (Swan)",
        "topic": "Countable and uncountable nouns"
      },
      "cefr": {
        "teach_from": "A2",
        "band": "A2-B1"
      },
      "regression": [
        "informations_plural"
      ]
    },
    {
      "id": "do_support_question",
      "category": "syntax",
      "priority": 35,
      "detect": {
        "pattern": "^(speak|want|like|need|have|work|live|understand|know)\\s+(you|he|she|they)\\b.*\\?",
        "flags": "i"
      },
      "issue": "Simple-tense yes/no questions need «do/does» support — the main verb cannot invert with the subject on its own.",
      "mention": [
        "do support",
        "auxiliary do",
        "question formation"
      ],
      "repair": [
        {
          "pattern": "^speak\\s+you\\b",
          "replace": "Do you speak",
          "flags": "gi"
        },
        {
          "pattern": "^want\\s+you\\b",
          "replace": "Do you want",
          "flags": "gi"
        },
        {
          "pattern": "^like\\s+you\\b",
          "replace": "Do you like",
          "flags": "gi"
        },
        {
          "pattern": "^need\\s+you\\b",
          "replace": "Do you need",
          "flags": "gi"
        },
        {
          "pattern": "^work\\s+you\\b",
          "replace": "Do you work",
          "flags": "gi"
        },
        {
          "pattern": "^live\\s+you\\b",
          "replace": "Do you live",
          "flags": "gi"
        },
        {
          "pattern": "^understand\\s+you\\b",
          "replace": "Do you understand",
          "flags": "gi"
        },
        {
          "pattern": "^know\\s+you\\b",
          "replace": "Do you know",
          "flags": "gi"
        }
      ],
      "grammar_rule": "Do-support in simple-tense questions",
      "source": {
        "authority": "CGEL",
        "topic": "Subject-auxiliary inversion"
      },
      "cefr": {
        "teach_from": "A1",
        "band": "A1-A2"
      },
      "regression": [
        "do_support_speak_you"
      ]
    }
  ]
};
})(typeof globalThis !== "undefined" ? globalThis : this);
