/**
 * Website-only Cloud Functions. Phones run Coach on the device and do not
 * call these. Signed-in GitHub Pages users get analyzeText so API keys stay
 * in Secret Manager.
 *
 * analyzeText       — grammar analysis, rate-limited
 * getUsage          — signed-in user's monthly usage summary
 * deleteAccountData — wipe Firestore records for a signed-in web account
 */

const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { defineSecret } = require("firebase-functions/params");
const { initializeApp } = require("firebase-admin/app");
const { getFirestore } = require("firebase-admin/firestore");
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
    if (language !== "es" && language !== "fr" && language !== "en") {
      throw new HttpsError("invalid-argument", "language must be es, fr, or en");
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

// ── Account deletion ─────────────────────────────────────────────────────────
// App Store guideline 5.1.1(v) requires deletion to be initiated from inside
// the app. The client deletes its own Firebase Auth user; everything under
// users/{uid} (profile, monthly usage counters, call packs, Plus record) is
// closed to client writes by firestore.rules, so it has to be removed here
// with the Admin SDK.
//
// Idempotent: recursiveDelete on a missing document is a no-op, so a retry
// after a dropped connection still reports success.

exports.deleteAccountData = onCall(
  { timeoutSeconds: 60, memory: "256MiB" },
  async (request) => {
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "Sign in required.");
    }

    const uid = request.auth.uid;
    const db = getFirestore();

    try {
      await db.recursiveDelete(db.doc(`users/${uid}`));
      console.log(`Deleted all Firestore data for uid=${uid}`);
      return { deleted: true };
    } catch (err) {
      console.error("deleteAccountData error:", err);
      throw new HttpsError("internal", "Could not delete your account data.");
    }
  }
);
