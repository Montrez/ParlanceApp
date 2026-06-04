#!/usr/bin/env node
/**
 * Smoke test for sentence-triggered RAG in Parlance/web/rag-knowledge.js
 * Run: node training/test_rag_triggers.mjs
 */
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import vm from 'vm';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ragPath = join(__dirname, '../Parlance/web/rag-knowledge.js');
const code = readFileSync(ragPath, 'utf8');
const sandbox = {};
vm.createContext(sandbox);
vm.runInContext(code, sandbox);
const { getRAGContextWithMeta } = sandbox;

const ES_CASES = [
  { sentence: 'Si yo tendría más tiempo, estudiaría más.', level: 'B2', expectTopics: ['Si-clause (subjunctive)'] },
  { sentence: 'Me gustan mucho los libros de historia.', level: 'A2', expectTopics: ['Gustar (indirect object)'] },
  { sentence: 'Yo me levanto temprano todos los días.', level: 'A2', expectTopics: ['Reflexive verbs'] },
  { sentence: 'No puedo ir porque tengo mucho trabajo.', level: 'A2', expectTopics: ['Stem-changing verbs'] },
  { sentence: 'He comido en ese restaurante antes.', level: 'B1', expectTopics: ['Present perfect (haber + participle)'] },
  { sentence: 'El informe fue escrito por el doctor.', level: 'B2', expectTopics: ['Passive voice (ser + participle)'] },
  { sentence: 'Se lo di ayer por la tarde.', level: 'B1', expectTopics: ['Object pronouns (lo/la/le/se)'] },
  { sentence: 'Estoy estudiando para el examen DELE.', level: 'A2', expectTopics: ['Progressive (estar + gerund)'] },
  { sentence: 'Voy a visitar a mi familia el fin de semana.', level: 'A2', expectTopics: ['Near future (ir a + infinitive)'] },
  { sentence: 'Actualmente estoy realizando un proyecto importante.', level: 'B2', expectTopics: ['False cognates / Anglicisms'] },
  { sentence: 'Compré una casa blanca cerca del hospital.', level: 'A1', expectTopics: ['Gender & number agreement'] },
  { sentence: 'La interpretación simultánea requiere mucha concentración.', level: 'C1', expectTopics: ['Conference interpreting'] },
  { sentence: 'La paciente debe suspender los AINEs antes de la cirugía.', level: 'B2', expectTopics: ['Medical interpreting'] },
  { sentence: 'Cómo está usted señora García?', level: 'B2', expectTopics: ['Question punctuation', 'Register (tú/usted)'] },
];

const FR_CASES = [
  { sentence: "Si j'aurais su, j'aurais voyagé.", level: 'B2', expectTopics: ['Si-clause (hypothèse)'] },
  { sentence: 'Je me lève tôt tous les matins.', level: 'A2', expectTopics: ['Verbes pronominaux'] },
  { sentence: "J'ai faim et j'ai soif.", level: 'A1', expectTopics: ['Être vs avoir'] },
  { sentence: 'Je voudrais du pain et de la confiture.', level: 'A2', expectTopics: ['Articles partitifs'] },
  { sentence: 'Je vais étudier demain matin.', level: 'A2', expectTopics: ['Futur proche (aller + infinitif)'] },
  { sentence: 'Il faut que tu viennes à la réunion.', level: 'B1', expectTopics: ['Subjonctif'] },
  { sentence: 'Je ne parle pas français couramment.', level: 'A1', expectTopics: ['Négation (ne…pas)'] },
  { sentence: "Je le lui ai donné hier.", level: 'B1', expectTopics: ['Pronoms compléments (y, en, le)'] },
  { sentence: 'Actuellement je réalise un projet important.', level: 'B2', expectTopics: ['Faux amis / anglicismes'] },
  { sentence: 'Une petite maison blanche près de la rivière.', level: 'A1', expectTopics: ['Accord (genre/nombre)'] },
  { sentence: "L'interprétation simultanée exige beaucoup de concentration.", level: 'C1', expectTopics: ['Interprétation de conférence'] },
  { sentence: 'Le patient doit suspendre les AINS avant l\'opération.', level: 'B2', expectTopics: ['Medical interpreting'] },
  { sentence: 'Comment allez-vous madame?', level: 'B2', expectTopics: ['Questions & punctuation', 'Register (tu/vous)'] },
  { sentence: "Hier il faisait beau et j'ai marché longtemps.", level: 'B1', expectTopics: ['Passé composé vs imparfait'] },
  { sentence: 'Elle est allée à la clinique ce matin.', level: 'B1', expectTopics: ['Passé composé avec être'] },
];

function runSuite(lang, cases) {
  let passed = 0;
  let failed = 0;
  console.log(`\n=== ${lang.toUpperCase()} ===`);
  for (const { sentence, level, expectTopics } of cases) {
    const meta = getRAGContextWithMeta(lang, level, sentence, { condensed: true });
    const missing = expectTopics.filter(t => !meta.topics.includes(t));
    if (missing.length) {
      failed++;
      console.error(`FAIL: "${sentence.slice(0, 50)}…"`);
      console.error(`  expected: ${expectTopics.join(', ')}`);
      console.error(`  got:      ${meta.topics.join(', ')}`);
      console.error(`  missing:  ${missing.join(', ')}`);
    } else {
      passed++;
      console.log(`OK  [${expectTopics.join(' + ')}]`);
    }
    if (!meta.context || meta.context.length < 20) {
      failed++;
      console.error(`FAIL: empty context for "${sentence.slice(0, 40)}…"`);
    }
  }
  console.log(`${passed}/${cases.length} ${lang} cases passed`);
  return failed;
}

const totalFailed = runSuite('es', ES_CASES) + runSuite('fr', FR_CASES);
if (totalFailed) process.exit(1);
console.log('\nAll RAG trigger tests passed (Spanish + French).');
