# Parlance Firebase (Auth + AI proxy)

Cloud Functions proxy grammar analysis for signed-in users. API keys live in Firebase Secret Manager, not on client devices.

## Prerequisites

- [Firebase CLI](https://firebase.google.com/docs/cli): `npm install -g firebase-tools`
- Firebase project (default in `.firebaserc`: `parlance-926ef`)
- Blaze plan (required for secrets and outbound API calls)

## One-time Console setup

See the main [README.md](../README.md#firebase-console-setup) for:

- Enable **Authentication** (Apple + Google)
- Create iOS app with bundle ID `com.parlance.interpreterguide`
- Download `GoogleService-Info.plist` into `Parlance/` (gitignored — do not commit)

**Xcode Cloud:** Archive builds use `ci_scripts/ci_pre_xcodebuild.sh` to copy `GoogleService-Info.plist.example` when the real plist is absent. CI archives compile with placeholder Firebase config; use a local plist for device builds with working Google Sign-In.
- Enable **Cloud Functions**

## Set API secrets

From the `firebase/` directory:

```bash
cd firebase
firebase login
firebase use parlance-926ef

firebase functions:secrets:set GROQ_API_KEY
firebase functions:secrets:set DEEPSEEK_API_KEY
firebase functions:secrets:set GEMINI_API_KEY
firebase functions:secrets:set OPENROUTER_API_KEY
firebase functions:secrets:set OPENAI_API_KEY
firebase functions:secrets:set ANTHROPIC_API_KEY
firebase functions:secrets:set KIMI_API_KEY
```

Set only the providers you plan to offer; missing secrets return an error for that provider.

## Deploy

```bash
cd firebase/functions
npm install
cd ..
firebase deploy --only functions,firestore
```

Callable functions (all require Firebase Auth ID token):
- **`analyzeText`** — grammar analysis, rate-limited
- **`getUsage`** — returns signed-in user's monthly usage summary

## Usage / Pricing model

| Tier     | Monthly limit | How to unlock                    |
|----------|--------------|----------------------------------|
| free     | 30 calls     | Default for all signed-in users  |
| starter  | 30 + packs   | $0.99 consumable = 100 pack calls|
| plus     | Unlimited    | $9.99/month subscription (TBD)   |

Usage is tracked per user per calendar month in Firestore:
- `users/{uid}` — tier and metadata
- `users/{uid}/usage/{YYYY-MM}` — monthly call count
- `users/{uid}/packs/{packId}` — remaining purchased pack calls

## Local lint

```bash
cd firebase/functions
npm run lint
```
