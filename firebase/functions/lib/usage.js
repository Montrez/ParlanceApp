/**
 * Usage tracking and rate limiting for Parlance cloud AI calls.
 *
 * Tiers:
 *   free        — 30 cloud AI calls / calendar month
 *   starter     — free + purchased call packs ($0.99 / 100 calls)
 *   plus        — unlimited (future $9.99/month subscription)
 *
 * Firestore schema:
 *   users/{uid} — { tier: "free"|"starter"|"plus", createdAt, ... }
 *   users/{uid}/usage/{YYYY-MM} — { count: number, updatedAt }
 *   users/{uid}/packs/{packId} — { remaining: number, purchasedAt }
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
  const tier = user.tier || "free";

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
  const tier = user.tier || "free";
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

module.exports = { checkAndIncrementUsage, getUsageSummary, getOrCreateUser };
