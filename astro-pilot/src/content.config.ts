import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// One entry per locale per page, e.g. medical.en.yaml / medical.es.yaml / medical.fr.yaml.
// Default id generation strips dots, so "medical.en.yaml" -> "medicalen"; use an
// explicit generateId to keep page/locale separable as "medical/en".
const domain = defineCollection({
  loader: glob({
    pattern: '**/*.yaml',
    base: './src/content/domain',
    generateId: ({ entry }) => entry.replace(/\.yaml$/, '').replace(/\.(en|es|fr)$/, '/$1'),
  }),
  schema: z.object({
    title: z.string(),
    subtitle: z.string(),
    sectionsLabel: z.string(),
    nav: z.array(z.object({ id: z.string(), label: z.string() })),
    intro: z.object({
      flag: z.string(),
      title: z.string(),
      desc: z.string(),
    }),
    sections: z.array(
      z.object({
        id: z.string(),
        chapter: z.string(),
        title: z.string(),
        kind: z.enum(['rule', 'bullets', 'table']),
        ruleTitle: z.string().optional(),
        ruleText: z.string().optional(),
        bullets: z.array(z.string()).optional(),
        tableHeaders: z.array(z.string()).optional(),
        tableRows: z.array(z.array(z.string())).optional(),
      })
    ),
  }),
});

export const collections = { domain };
