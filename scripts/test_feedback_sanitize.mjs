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

if (process.exitCode) {
  console.error('feedback-sanitize smoke tests failed');
} else {
  console.log('feedback-sanitize smoke tests OK');
}
