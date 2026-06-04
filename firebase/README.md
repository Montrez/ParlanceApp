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
- Download `GoogleService-Info.plist` into `Parlance/`
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
firebase deploy --only functions
```

Callable function name: **`analyzeText`** (requires Firebase Auth ID token).

## Local lint

```bash
cd firebase/functions
npm run lint
```
