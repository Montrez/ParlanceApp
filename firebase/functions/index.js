/**
 * Parlance Firebase Cloud Functions — authenticated proxy for cloud AI providers.
 */

const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { defineSecret } = require("firebase-functions/params");
const { initializeApp } = require("firebase-admin/app");
const { analyzeWithProvider } = require("./lib/analyze");

initializeApp();

const groqKey = defineSecret("GROQ_API_KEY");
const deepseekKey = defineSecret("DEEPSEEK_API_KEY");
const geminiKey = defineSecret("GEMINI_API_KEY");
const openrouterKey = defineSecret("OPENROUTER_API_KEY");
const openaiKey = defineSecret("OPENAI_API_KEY");
const anthropicKey = defineSecret("ANTHROPIC_API_KEY");
const kimiKey = defineSecret("KIMI_API_KEY");

const CLOUD_PROVIDERS = new Set([
  "groq",
  "deepSeek",
  "deepseek",
  "gemini",
  "openRouter",
  "openrouter",
  "openAI",
  "openai",
  "anthropic",
  "kimi",
]);

/** Map journal.js localStorage ids to Swift enum raw values. */
function normalizeProviderId(provider) {
  const aliases = {
    deepseek: "deepSeek",
    openrouter: "openRouter",
    openai: "openAI",
  };
  return aliases[provider] || provider;
}

exports.analyzeText = onCall(
  {
    secrets: [
      groqKey,
      deepseekKey,
      geminiKey,
      openrouterKey,
      openaiKey,
      anthropicKey,
      kimiKey,
    ],
    timeoutSeconds: 60,
    memory: "512MiB",
  },
  async (request) => {
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "Sign in required to analyze text.");
    }

    const data = request.data || {};
    const sentence = typeof data.sentence === "string" ? data.sentence.trim() : "";
    const language = typeof data.language === "string" ? data.language : "";
    const ragContext = typeof data.ragContext === "string" ? data.ragContext : "";
    const providerRaw = typeof data.provider === "string" ? data.provider : "";
    const provider = normalizeProviderId(providerRaw);
    const model = typeof data.model === "string" ? data.model : "";

    if (!sentence) {
      throw new HttpsError("invalid-argument", "sentence is required");
    }
    if (language !== "es" && language !== "fr") {
      throw new HttpsError("invalid-argument", "language must be es or fr");
    }
    if (!CLOUD_PROVIDERS.has(providerRaw) && !CLOUD_PROVIDERS.has(provider)) {
      throw new HttpsError("invalid-argument", `Unsupported provider: ${providerRaw}`);
    }
    if (!model) {
      throw new HttpsError("invalid-argument", "model is required");
    }

    const secrets = {
      groq: groqKey.value(),
      deepseek: deepseekKey.value(),
      gemini: geminiKey.value(),
      openrouter: openrouterKey.value(),
      openai: openaiKey.value(),
      anthropic: anthropicKey.value(),
      kimi: kimiKey.value(),
    };

    try {
      return await analyzeWithProvider(
        { sentence, language, ragContext, provider, model },
        secrets
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : "Analysis failed";
      console.error("analyzeText error:", message);
      throw new HttpsError("internal", message);
    }
  }
);
