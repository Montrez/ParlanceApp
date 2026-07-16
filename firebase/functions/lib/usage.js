/**
 * Usage tracking and rate limiting for Parlance cloud AI calls.
 *
 * Tiers:
 *   free        — 30 cloud AI calls / calendar month
 *   starter     — free + purchased call packs ($0.99 / 100 calls)
 *   plus        — unlimited (future $9.99/month subscription)
 *
 * Firestore schema:
 *   users/{uid} — { tier: "free"|"starter"|"plus", plusExpiresAt, createdAt, ... }
 *   users/{uid}/usage/{YYYY-MM} — { count: number, updatedAt }
 *   users/{uid}/packs/{packId} — { remaining: number, purchasedAt }
 *
 * There's no App Store Server Notifications webhook wired up yet, so an
 * expired "plus" subscription is only caught lazily here (on next usage
 * check) by comparing plusExpiresAt — see effectiveTier().
 */

const { getFirestore, FieldValue } = require("firebase-admin/firestore");

const FREE_MONTHLY_LIMIT = 30;

/**
 * Return the user document, creating it with defaults if it doesn't exist.
 * @param {FirebaseFirestore.Firestore} db
 * @param {string} uid
 */
async function getOrCreateUser(db, uid) {
  const ref = db.doc(`users/${uid}`);
  const snap = await ref.get();
  if (!snap.exists) {
    const data = {
      tier: "free",
      createdAt: FieldValue.serverTimestamp(),
      updatedAt: FieldValue.serverTimestamp(),
    };
    await ref.set(data);
    return data;
  }
  return snap.data();
}

/**
 * Return current month key as "YYYY-MM".
 */
function currentMonthKey() {
  return new Date().toISOString().slice(0, 7);
}

/**
 * "plus" tier self-heals to "free" once plusExpiresAt has passed, so a
 * lapsed/cancelled subscription stops granting unlimited calls even without
 * a server notification webhook telling us it ended.
 */
function effectiveTier(user) {
  const tier = user.tier || "free";
  if (tier !== "plus") return tier;
  const expiresAt = user.plusExpiresAt;
  if (!expiresAt) return tier;
  const expiresMs = typeof expiresAt.toMillis === "function" ? expiresAt.toMillis() : new Date(expiresAt).getTime();
  if (Number.isFinite(expiresMs) && expiresMs < Date.now()) return "free";
  return tier;
}

/**
 * Check whether the user can make a cloud AI call, and if so,
 * atomically increment their usage counter.
 *
 * Returns { allowed: true } or throws an HttpsError-compatible error object.
 *
 * @param {string} uid
 * @returns {Promise<{ allowed: boolean, tier: string, remaining: number|null }>}
 */
async function checkAndIncrementUsage(uid) {
  const db = getFirestore();
  const user = await getOrCreateUser(db, uid);
  const tier = effectiveTier(user);

  // Plus tier: unlimited
  if (tier === "plus") {
    return { allowed: true, tier, remaining: null };
  }

  const monthKey = currentMonthKey();
  const usageRef = db.doc(`users/${uid}/usage/${monthKey}`);

  // Run as a Firestore transaction so concurrent requests don't double-count
  const result = await db.runTransaction(async (tx) => {
    const usageSnap = await tx.get(usageRef);
    const currentCount = usageSnap.exists ? (usageSnap.data().count || 0) : 0;

    if (currentCount < FREE_MONTHLY_LIMIT) {
      // Free monthly quota not exhausted
      tx.set(usageRef, {
        count: currentCount + 1,
        updatedAt: FieldValue.serverTimestamp(),
      });
      return {
        allowed: true,
        tier,
        remaining: FREE_MONTHLY_LIMIT - currentCount - 1,
        source: "free",
      };
    }

    // Free quota exhausted — check for purchased packs
    const packsSnap = await tx.get(
      db.collection(`users/${uid}/packs`).orderBy("purchasedAt").limit(10)
    );

    const activePack = packsSnap.docs.find(
      (d) => (d.data().remaining || 0) > 0
    );

    if (activePack) {
      const remaining = activePack.data().remaining - 1;
      tx.update(activePack.ref, {
        remaining,
        updatedAt: FieldValue.serverTimestamp(),
      });
      return {
        allowed: true,
        tier,
        remaining,
        source: "pack",
      };
    }

    // No quota remaining
    return { allowed: false, tier, remaining: 0, source: "none" };
  });

  return result;
}

/**
 * Get current usage summary for a user (for display in the app).
 * @param {string} uid
 */
async function getUsageSummary(uid) {
  const db = getFirestore();
  const user = await getOrCreateUser(db, uid);
  const tier = effectiveTier(user);
  const monthKey = currentMonthKey();

  const usageSnap = await db.doc(`users/${uid}/usage/${monthKey}`).get();
  const monthlyCount = usageSnap.exists ? (usageSnap.data().count || 0) : 0;

  const packsSnap = await db
    .collection(`users/${uid}/packs`)
    .where("remaining", ">", 0)
    .get();
  const packCallsRemaining = packsSnap.docs.reduce(
    (sum, d) => sum + (d.data().remaining || 0),
    0
  );

  return {
    tier,
    monthlyUsed: monthlyCount,
    monthlyLimit: tier === "plus" ? null : FREE_MONTHLY_LIMIT,
    monthlyRemaining:
      tier === "plus"
        ? null
        : Math.max(0, FREE_MONTHLY_LIMIT - monthlyCount),
    packCallsRemaining,
    monthKey,
  };
}

module.exports = { checkAndIncrementUsage, getUsageSummary, getOrCreateUser, effectiveTier };
