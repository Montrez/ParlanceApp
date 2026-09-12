#!/usr/bin/env node
/**
 * Smoke tests for placeholder-stripping + sentence-citing coach copy.
 * Loads the same web JS the phones use.
 */
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const require = createRequire(import.meta.url);
const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const web = join(root, 'Parlance', 'web');

require(join(web, 'coach-rules-es.js'));
require(join(web, 'coach-rules-fr.js'));
require(join(web, 'coach-rules-en.js'));
require(join(web, 'coach-rules-engine.js'));
const sanitize = require(join(web, 'feedback-sanitize.js'));

const PLACEHOLDER =
  'The wording looks usable. Coach could not finish a full note for this sentence. Use the reference topics when they appear.';

function fail(msg) {
  console.error('FAIL:', msg);
  process.exitCode = 1;
}

function assert(cond, msg) {
  if (!cond) fail(msg);
}

const quiero = sanitize.sanitizeFeedbackResult(
  'Quiero ver la película Percy Jackson.',
  {
    status: 'Excellent',
    grammar_rule: 'Spanish agreement, prepositions, and clause structure',
    explanation: PLACEHOLDER,
  },
  'es',
);

assert(!sanitize.isPlaceholderExplanation(quiero.explanation),
  `quiero explanation still placeholder: ${quiero.explanation}`);
assert(/querer|quiero/i.test(quiero.grammar_rule || ''),
  `quiero grammar_rule missing querer+infinitive: ${quiero.grammar_rule}`);
assert(/quiero/i.test(quiero.explanation || ''),
  `quiero explanation does not cite learner words: ${quiero.explanation}`);
assert(/Quiero ver la película Percy Jackson/i.test(quiero.explanation || ''),
  `quiero explanation does not quote the sentence: ${quiero.explanation}`);

const hola = sanitize.sanitizeFeedbackResult(
  'Hola Samuel, hoy voy al cine.',
  { status: 'Excellent', grammar_rule: '', explanation: '' },
  'es',
);

assert(!sanitize.isPlaceholderExplanation(hola.explanation),
  `hola explanation still placeholder: ${hola.explanation}`);
assert(/ir|voy|greeting/i.test(hola.grammar_rule || ''),
  `hola grammar_rule not specific: ${hola.grammar_rule}`);
assert(/Hola Samuel, hoy voy al cine/i.test(hola.explanation || ''),
  `hola explanation does not quote the sentence: ${hola.explanation}`);

const question = sanitize.sanitizeFeedbackResult(
  'Como estas?',
  {
    status: 'Excellent',
    grammar_rule: '',
    explanation: PLACEHOLDER,
  },
  'es',
);

assert(question.status === 'Needs Improvement',
  `missing ¿ should be Needs Improvement, got ${question.status}`);
assert(/inverted|¿/i.test(question.grammar_rule || '') || /¿/i.test(question.explanation || ''),
  `missing ¿ not reflected in rule/explanation: ${question.grammar_rule} / ${question.explanation}`);
assert(!sanitize.isPlaceholderExplanation(question.explanation),
  `question explanation still placeholder: ${question.explanation}`);

const androidFallback = sanitize.sanitizeFeedbackResult(
  'Quiero ver la película Percy Jackson.',
  { status: 'Excellent', grammar_rule: '', explanation: '', _coach_incomplete: true },
  'es',
);
assert(/querer|quiero/i.test(androidFallback.grammar_rule || ''),
  `empty Android fallback did not fill querer rule: ${androidFallback.grammar_rule}`);
assert(!sanitize.isPlaceholderExplanation(androidFallback.explanation),
  `empty Android fallback still placeholder: ${androidFallback.explanation}`);

const pointNegatif = sanitize.sanitizeFeedbackResult(
  'Le point négatif que je me suis mal préparé et renseigner sur la société.',
  { status: 'Excellent', grammar_rule: 'General French grammar', explanation: 'No confirmed grammar error in your sentence.' },
  'fr',
);
assert(pointNegatif.status === 'Needs Improvement',
  `point négatif should be NI, got ${pointNegatif.status}`);
assert(/est que/i.test(pointNegatif.correction || ''),
  `point négatif correction missing est que: ${pointNegatif.correction}`);
assert(/renseigné/i.test(pointNegatif.correction || ''),
  `point négatif correction missing renseigné: ${pointNegatif.correction}`);

const merci = sanitize.sanitizeFeedbackResult(
  'Merci à vous. Cordialement',
  {
    status: 'Needs Improvement',
    grammar_rule: 'Vocabulary and syntax errors',
    explanation: "The sentence contains a vocabulary error ('Cordialement' instead of 'Cordialement') and a syntax error ('Merci à vous' instead of 'Merci vous').",
    correction: 'Merci vous, Cordialement',
  },
  'fr',
);
assert(merci.status === 'Excellent' || /merci à vous/i.test(merci.correction || ''),
  `merci à vous must stay correct, got status=${merci.status} correction=${merci.correction}`);
assert(!/merci vous/i.test(merci.correction || '') || /merci à vous/i.test(merci.correction || ''),
  `merci à vous must not become merci vous: ${merci.correction}`);

const offre = sanitize.sanitizeFeedbackResult(
  "Est-il possible de m'envoyer l'appel d'offr s'il vous plaît ?",
  {
    status: 'Needs Improvement',
    grammar_rule: 'Subjonctif vs indicatif',
    explanation: "The sentence incorrectly uses 'il vous plaît' instead of 'il vous plaît'.",
    correction: "Est-il possible de m'envoyer l'offre d'offre si vous le savez ?",
  },
  'fr',
);
assert(offre.status === 'Needs Improvement',
  `offr typo should stay NI, got ${offre.status}`);
assert(/d'offre/i.test(offre.correction || ''),
  `offre correction missing d'offre: ${offre.correction}`);
assert(/s'il vous plaît|s'il vous plait/i.test(offre.correction || ''),
  `offre correction dropped s'il vous plaît: ${offre.correction}`);

if (process.exitCode) {
  console.error('feedback-sanitize smoke tests failed');
} else {
  console.log('feedback-sanitize smoke tests OK');
}
