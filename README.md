<p align="center">
  <img src="docs/logo.png" alt="Parlance" width="120" />
</p>

<h1 align="center">Parlance</h1>

<p align="center">
  A language writing journal for aspiring interpreters.<br>
  Practice writing in Spanish and French with real-time AI grammar feedback.
</p>

<p align="center">
  <a href="https://github.com/Montrez/ParlanceApp/releases/latest">
    <img src="https://img.shields.io/github/v/release/Montrez/ParlanceApp?label=release" alt="Latest release" />
  </a>
  <a href="https://montrez.github.io/ParlanceApp/">
    <img src="https://img.shields.io/badge/web%20app-live-0b9cd0" alt="Web app live" />
  </a>
</p>

---

## What's in the app

- **Journal**: write sentences in your target language and get structured AI feedback (corrections, register, CEFR level, higher-level rephrasings) as you go.
- **Grammar Guide**: verb tenses and grammar rules, A1–C2, per practice language.
- **Regional Guide**: regional vocabulary, pronouns, and dialect traps, with a "your region vs. theirs" picker.
- **Parlance Coach**: on-device Spanish/French grammar coaching (Qwen 0.5B fine-tunes running fully offline via MLX), or plug in a cloud provider.
- **Call Packs**: 30 free AI analyses a month, with an optional $0.99 top-up for 100 more.
- Dark mode and interface language (EN/ES/FR) that apply consistently across the journal, guides, and regional content.

---

## Quick Start

### iOS

```bash
git clone https://github.com/Montrez/ParlanceApp.git
cd ParlanceApp
open Parlance.xcodeproj
```

1. Set your signing team under **Signing & Capabilities**
2. Connect your device or pick a simulator
3. **Run** (Cmd+R)

### Web

Visit the [GitHub Pages site](https://montrez.github.io/ParlanceApp/) — no install needed. You can run AI in-browser with WebLLM or connect a cloud provider.

### Android

```bash
npx cap sync android
```

Open `android/` in Android Studio and run on a device or emulator.

---

## Parlance Coach (Spanish & French fine-tuned models)

On-device grammar coaching on **iOS** using Qwen 0.5B fine-tunes (~294 MB MLX 4-bit per language, bundled at archive). See [training/ARCHIVE_SPANISH.md](training/ARCHIVE_SPANISH.md).

1. `./training/prepare_ios_coach_model.sh`
2. Archive in Xcode (physical device recommended)
3. In the app: **⚙ AI** → **Parlance Coach**, journal language **Spanish** or **French**

Optional Mac dev server: `python3 training/parlance_slm_server.py`.

## Adding an API Key

The default provider is **Groq** (free, fast, runs Qwen 3 32B). Get a key at [console.groq.com/keys](https://console.groq.com/keys).

**On iOS:** Create `Parlance/Secrets.plist` with your key:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>GROQ_API_KEY</key>
    <string>YOUR_KEY</string>
</dict>
</plist>
```

**On any platform:** You can also set your API key directly in the app via the **AI Settings** button.

Supported providers: Groq, OpenAI, Anthropic, Google Gemini, DeepSeek, Kimi, OpenRouter, Apple Intelligence (on-device, iOS 26+).

---

## Firebase Console setup

Use a Firebase project (default in `firebase/.firebaserc`: `parlance-926ef`) with the **Blaze** plan for Cloud Functions secrets and outbound API calls.

### 1. Authentication

1. [Firebase Console](https://console.firebase.google.com/) → your project → **Build** → **Authentication** → **Sign-in method**
2. Enable **Apple** and **Google**
3. For Apple: add your iOS bundle ID `com.parlance.interpreterguide` and configure Sign in with Apple in [Apple Developer](https://developer.apple.com/) (Services ID / key as required by Firebase docs)
4. For Google: add the iOS client; download config below

### 2. iOS app

1. **Project settings** → **Your apps** → add **iOS** app with bundle ID `com.parlance.interpreterguide`
2. Download **GoogleService-Info.plist** → copy to `Parlance/GoogleService-Info.plist` (see `Parlance/GoogleService-Info.plist.example`)
3. In Xcode: add the plist to the Parlance target if not already present
4. Replace `REPLACE_WITH_REVERSED_CLIENT_ID` in `Parlance/Info.plist` **CFBundleURLSchemes** with the `REVERSED_CLIENT_ID` value from the plist
5. Enable **Sign in with Apple** capability on the Parlance target

### 3. Web (GitHub Pages)

1. Register a **Web** app in the same Firebase project
2. Copy `docs/firebase-config.example.js` → `docs/firebase-config.js` and fill in the web config object
3. Deploy `docs/` as usual; the site loads Firebase compat SDK from the CDN (see `docs/index.html`)

### 4. Cloud Functions

1. Install CLI: `npm install -g firebase-tools`
2. Set provider API keys as secrets (see [firebase/README.md](firebase/README.md))
3. Deploy: `cd firebase && firebase deploy --only functions`

Signed-in users call the **`analyzeText`** callable; API keys stay in Secret Manager, not on devices.

---

## How It Works

1. Write a sentence in your target language
2. Parlance selects relevant grammar rules, exam context (DELE/DELF), and domain terminology via RAG
3. An AI model returns structured feedback: corrections, register analysis, higher-level rephrasings, and interpreter tips

Feedback infers the sentence’s CEFR level (A1–C2) when the model is confident, plus a complexity note when it isn’t. Register identification and professional phrasing for medical, legal, and conference interpreting are included.

---

## Roadmap

Active work is tracked as GitHub issues, grouped into epics:

- [English learning path](https://github.com/Montrez/ParlanceApp/issues/9) for Spanish/French native speakers
- [Language architecture](https://github.com/Montrez/ParlanceApp/issues/12) — making it easier to add new languages and sections
- [Central design system](https://github.com/Montrez/ParlanceApp/issues/16) — one source of truth for colors across web, native, and the app icon
- [App layout & UX polish](https://github.com/Montrez/ParlanceApp/issues/20)
- [Coach model quality](https://github.com/Montrez/ParlanceApp/issues/26)

See the [full issue list](https://github.com/Montrez/ParlanceApp/issues) for everything currently open.

---

*Built with SwiftUI + WKWebView + RAG + Groq*
