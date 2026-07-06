/**
 * Parlance Firebase Cloud Functions — authenticated proxy for cloud AI providers.
 *
 * analyzeText  — grammar analysis, rate-limited (30 free/month, then $0.99/100 pack)
 * getUsage     — returns the signed-in user's current usage summary
 */

const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { defineSecret } = require("firebase-functions/params");
const crypto = require("crypto");
const { initializeApp } = require("firebase-admin/app");
const { getFirestore, FieldValue } = require("firebase-admin/firestore");
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
const appleRootCerts = defineSecret("APPLE_ROOT_CERTS_BASE64");

const BUNDLE_ID = "com.parlance.interpreterguide";
const CALL_PACK_PRODUCT_ID = "com.parlance.interpreterguide.callpack100";

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

function base64UrlDecode(value) {
  return Buffer.from(value, "base64url");
}

function decodeAppleRootCertificates() {
  const raw = appleRootCerts.value();
  if (!raw || !raw.trim()) {
    throw new HttpsError(
      "failed-precondition",
      "Apple root certificates are not configured for StoreKit verification."
    );
  }

  let entries;
  try {
    const parsed = JSON.parse(raw);
    entries = Array.isArray(parsed) ? parsed : [String(parsed)];
  } catch (_) {
    entries = raw.split(/[,\n]/).map((item) => item.trim()).filter(Boolean);
  }

  const certs = entries.map((entry) => {
    const cleaned = entry
      .replace(/-----BEGIN CERTIFICATE-----/g, "")
      .replace(/-----END CERTIFICATE-----/g, "")
      .replace(/\s+/g, "");
    return new crypto.X509Certificate(Buffer.from(cleaned, "base64"));
  });

  if (!certs.length) {
    throw new HttpsError(
      "failed-precondition",
      "No Apple root certificates were configured for StoreKit verification."
    );
  }
  return certs;
}

function sameCertificate(a, b) {
  return Buffer.compare(a.raw, b.raw) === 0;
}

function dateWithinCertificate(cert, date) {
  const validFrom = Date.parse(cert.validFrom);
  const validTo = Date.parse(cert.validTo);
  return date.getTime() >= validFrom && date.getTime() <= validTo;
}

function verifyAppleCertificateChain(certificates, signedDate) {
  if (certificates.length < 2) {
    throw new HttpsError("invalid-argument", "Apple transaction certificate chain is incomplete.");
  }

  const roots = decodeAppleRootCertificates();
  const leaf = certificates[0];
  const chain = certificates.slice(1);
  const effectiveDate = signedDate || new Date();

  if (!dateWithinCertificate(leaf, effectiveDate)) {
    throw new HttpsError("permission-denied", "Apple transaction leaf certificate is not valid.");
  }

  let issuer = chain[0];
  if (!leaf.verify(issuer.publicKey)) {
    throw new HttpsError("permission-denied", "Apple transaction leaf certificate failed verification.");
  }

  for (let i = 0; i < chain.length - 1; i += 1) {
    const subject = chain[i];
    issuer = chain[i + 1];
    if (!dateWithinCertificate(subject, effectiveDate) || !subject.verify(issuer.publicKey)) {
      throw new HttpsError("permission-denied", "Apple transaction certificate chain failed verification.");
    }
  }

  const terminal = chain[chain.length - 1];
  const trustedRoot = roots.find((root) => sameCertificate(root, terminal) || terminal.verify(root.publicKey));
  if (!trustedRoot) {
    throw new HttpsError("permission-denied", "Apple transaction certificate chain is not rooted in Apple.");
  }
}

function verifySignedTransactionInfo(signedTransactionInfo) {
  if (!signedTransactionInfo || typeof signedTransactionInfo !== "string") {
    throw new HttpsError("invalid-argument", "signedTransactionInfo is required.");
  }

  const parts = signedTransactionInfo.split(".");
  if (parts.length !== 3) {
    throw new HttpsError("invalid-argument", "signedTransactionInfo must be a JWS compact string.");
  }

  let header;
  let payload;
  try {
    header = JSON.parse(base64UrlDecode(parts[0]).toString("utf8"));
    payload = JSON.parse(base64UrlDecode(parts[1]).toString("utf8"));
  } catch (err) {
    throw new HttpsError("invalid-argument", "Could not decode Apple transaction JWS.");
  }

  if (!Array.isArray(header.x5c) || header.x5c.length < 2) {
    throw new HttpsError("invalid-argument", "Apple transaction JWS is missing certificate chain.");
  }

  const certificates = header.x5c.map((cert) => (
    new crypto.X509Certificate(Buffer.from(cert, "base64"))
  ));
  const signedDate = payload.signedDate ? new Date(payload.signedDate) : undefined;
  verifyAppleCertificateChain(certificates, signedDate);

  const signingInput = Buffer.from(`${parts[0]}.${parts[1]}`);
  const signature = base64UrlDecode(parts[2]);
  const verified = crypto.verify(
    "sha256",
    signingInput,
    { key: certificates[0].publicKey, dsaEncoding: "ieee-p1363" },
    signature
  );
  if (!verified) {
    throw new HttpsError("permission-denied", "Apple transaction JWS signature verification failed.");
  }

  if (payload.bundleId !== BUNDLE_ID) {
    throw new HttpsError("permission-denied", "Apple transaction bundle ID does not match Parlance.");
  }
  if (payload.productId !== CALL_PACK_PRODUCT_ID) {
    throw new HttpsError("invalid-argument", `Unknown product: ${payload.productId}`);
  }
  if (!payload.transactionId) {
    throw new HttpsError("invalid-argument", "Apple transaction payload is missing transactionId.");
  }

  return payload;
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

// ── grantCallPack ─────────────────────────────────────────────────────────────
//
// Called by the iOS app after a successful StoreKit 2 purchase.
// Receives the signed JWS transaction payload from Apple and creates a
// pack document (remaining: 100) under users/{uid}/packs/{transactionId}.
//
// Idempotent: if the pack document already exists (duplicate delivery),
// it returns success without creating a duplicate.

exports.grantCallPack = onCall(
  { timeoutSeconds: 30, memory: "256MiB", secrets: [appleRootCerts] },
  async (request) => {
    if (!request.auth) {
      throw new HttpsError("unauthenticated", "Sign in required.");
    }

    const uid = request.auth.uid;
    const { signedTransactionInfo } = request.data || {};
    const transaction = verifySignedTransactionInfo(signedTransactionInfo);
    const transactionId = String(transaction.transactionId);
    const productId = transaction.productId;

    const db = getFirestore();
    const packRef = db.doc(`users/${uid}/packs/${transactionId}`);

    try {
      const snap = await packRef.get();
      if (snap.exists) {
        // Already granted — idempotent, return current state
        return { granted: false, reason: "already_granted", remaining: snap.data().remaining };
      }

      await packRef.set({
        productId,
        originalTransactionId: transaction.originalTransactionId || null,
        environment: transaction.environment || null,
        remaining: 100,
        purchasedAt: FieldValue.serverTimestamp(),
        updatedAt: FieldValue.serverTimestamp(),
      });

      console.log(`Granted 100-call pack to uid=${uid} transactionId=${transactionId}`);
      return { granted: true, remaining: 100 };
    } catch (err) {
      console.error("grantCallPack error:", err);
      throw new HttpsError("internal", "Could not grant call pack.");
    }
  }
);
