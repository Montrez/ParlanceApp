// @ts-check
import { defineConfig } from 'astro/config';

// Pilot: prove out Astro's built-in i18n routing + content collections
// against one real Parlance content page (domain-medical) before deciding
// whether to migrate the rest of Parlance/web's guide/dialect/domain pages.
export default defineConfig({
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'es', 'fr'],
    routing: {
      prefixDefaultLocale: true, // /en/, /es/, /fr/ all explicit and symmetric
    },
  },
  build: {
    format: 'file', // emit domain-medical.html, not domain-medical/index.html
  },
});
