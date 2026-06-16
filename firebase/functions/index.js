/**
 * Parlance Firebase Cloud Functions — authenticated proxy for cloud AI providers.
 *
 * analyzeText  — grammar analysis, rate-limited (30 free/month, then $0.99/100 pack)
 * getUsage     — returns the signed-in user's current usage summary
 */

const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { defineSecret } = require("firebase-functions/params");
const { initializeApp } = require("firebase-admin/app");
const { analyzeWithProvider } = require("./lib/analyze");
const {
  checkAndIncrementUsage,
  getUsageSummary,
} = require("./lib/usage");

initializeApp();

const groqKey        = defineSecret("GROQ_API_KEY");
const deepseekKey    = defineSecret("DEEPSEEK_API_KEY");
const geminiKey      = defineSecret("GEMINI_API_KEY");
const openrouterKey  = defineSecret("OPENROUTER_API_KEY");
const openaiKey      = defineSecret("OPENAI_API_KEY");
const anthropicKey   = defineSecret("ANTHROPIC_API_KEY");
const kimiKey        = defineSecret("KIMI_API_KEY");

const CLOUD_PROVIDERS = new Set([
  "groq", "deepSeek", "deepseek",
  "gemini",
  "openRouter", "openrouter",
  "openAI", "openai",
  "anthropic",
  "kimi",
]);

/** Map journal.js localStorage ids to Swift enum raw values. */
function normalizeProviderId(provider) {
  const aliases = {
    deepseek:   "deepSeek",
    openrouter: "openRouter",
    openai:     "openAI",
  };
  return aliases[provider] || provider;
}

// ── analyzeText ──────────────────────────────────────────────────────────────

exports.analyzeText = onCall(
  {
    secrets: [
      groqKey, deepseekKey, geminiKey,
      openrouterKey, openaiKey, anthropicKey, kimiKey,
    ],
    timeoutSeconds: 60,
    memory: "512MiB",
  },
  async (request) => {
    if (!request.auth) {
      throw new HttpsError(
        "unauthenticated",
        "Sign in to use cloud AI providers."
      );
    }

    const uid = request.auth.uid;
    const data = request.data || {};

    // ── input validation ──
    const sentence    = typeof data.sentence   === "string" ? data.sentence.trim()  : "";
    const language    = typeof data.language   === "string" ? data.language         : "";
    const ragContext  = typeof data.ragContext  === "string" ? data.ragContext        : "";
    const providerRaw = typeof data.provider   === "string" ? data.provider         : "";
    const provider    = normalizeProviderId(providerRaw);
    const model       = typeof data.model      === "string" ? data.model            : "";

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

    // ── rate limiting ──
    let usageResult;
    try {
      usageResult = await checkAndIncrementUsage(uid);
    } catch (err) {
      console.error("Usage check error:", err);
      throw new HttpsError("internal", "Could not verify usage quota.");
    }

    if (!usageResult.allowed) {
      throw new HttpsError(
        "resource-exhausted",
        "Monthly free limit reached (30 calls). Purchase a call pack ($0.99 / 100 calls) or use on-device Parlance Coach — it's always free and private."
      );
    }

    // ── AI call ──
    const secrets = {
      groq:       groqKey.value(),
      deepseek:   deepseekKey.value(),
      gemini:     geminiKey.value(),
      openrouter: openrouterKey.value(),
      openai:     openaiKey.value(),
      anthropic:  anthropicKey.value(),
      kimi:       kimiKey.value(),
    };

    try {
      const result = await analyzeWithProvider(
        { sentence, language, ragContext, provider, model },
        secrets
      );
      // Attach usage info so the client can update its counter without a second call
      return {
        ...result,
        _usage: {
          source:    usageResult.source,
          remaining: usageResult.remaining,
          tier:      usageResult.tier,
        },
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : "Analysis failed";
      console.error("analyzeText error:", message);
      throw new HttpsError("internal", message);
    }
  }
);

// ── getUsage ─────────────────────────────────────────────────────────────────

exports.getUsage = onCall(
  { timeoutSeconds: 15, memory: "256MiB" },
  async (request) => {
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "Sign in required.");
    }

    try {
      return await getUsageSummary(request.auth.uid);
    } catch (err) {
      console.error("getUsage error:", err);
      throw new HttpsError("internal", "Could not fetch usage.");
    }
  }
);
