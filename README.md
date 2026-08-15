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

Android and iOS share the web layer in `Parlance/web/` (mirrored to `docs/`, which
Capacitor bundles). Each platform supplies a native bridge behind the same message
protocol — `Parlance/ContentView.swift` on iOS, `ParlanceBridge.java` on Android —
so a feature added to one is expected on the other.
`python3 scripts/check_platform_sync.py` fails the build if a bridge action or
version number only lands on one side.

Capabilities that genuinely differ are reported by the bridge rather than sniffed
in JavaScript. Android currently reports `inAppPurchase: false` (no Play Billing
yet) and `nativeSettings: false` (it uses the web settings modal).

**Google Sign-In requires registered SHA-1 fingerprints.** Credential Manager will
not issue an ID token for an app whose signing certificate is unknown to Firebase,
and the failure surfaces as a generic sign-in error. Register every certificate the
app can be signed with:

```bash
# Debug builds
keytool -list -v -keystore ~/.android/debug.keystore \
  -alias androiddebugkey -storepass android

# Local release builds
keytool -list -v -keystore android/parlance-release.jks -alias parlance
```

Add each SHA-1 in Firebase Console → Project Settings → Your apps → Android, then
re-download `google-services.json` into `android/app/`. Builds distributed through
Play use **Play App Signing**, so the certificate in Play Console → Setup → App
integrity must be registered too — otherwise sign-in works locally and fails for
everyone who installs from Play.

Release signing credentials are read from `android/keystore.properties`, which is
gitignored. Copy `android/keystore.properties.example` and fill it in, or export
`PARLANCE_KEYSTORE_FILE`, `PARLANCE_KEYSTORE_PASSWORD`, `PARLANCE_KEY_ALIAS`, and
`PARLANCE_KEY_PASSWORD`. Without them the project still builds debug and unsigned
release.

### Versioning

Never edit a version by hand. Four files carry one, and editing them separately
is how iOS and Android drift apart:

```bash
python3 scripts/bump_version.py --show           # current numbers
python3 scripts/bump_version.py --build          # build + 1, both platforms
python3 scripts/bump_version.py --marketing 2.5  # the string humans see
```

The script refuses to run if the files already disagree, and refuses to move a
build number downwards, because no store lets you reuse or lower one.
`scripts/check_platform_sync.py` enforces the same match in CI.

Bump the build **once per upload**, whether it goes to TestFlight, Play, or both.
The marketing version only changes when the release is worth a new number to a
user; a rejected submission can be resubmitted under the same one.

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
