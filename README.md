# Parlance

A language writing journal for aspiring interpreters. Practice writing in Spanish and French with real-time AI grammar feedback, register analysis, and CEFR-leveled progression from A1 to C2.

Built for interpreter training — every analysis includes register identification (formal/informal), professional phrasing alternatives, and tips specific to medical, legal, and conference interpreting contexts.

## How It Works

Parlance uses a **RAG + LLM** architecture:

1. **You write** a sentence in Spanish or French
2. **RAG** (Retrieval-Augmented Generation) selects relevant grammar rules, exam context (DELE/DELF), and domain terminology (medical/legal) based on your CEFR level and sentence content
3. **An AI model** analyzes your sentence using that context and returns structured feedback:
   - Grammar rule identification
   - Explanation of what's correct or incorrect
   - Corrected sentence (if needed)
   - Register analysis (formal vs informal, appropriate for interpreting?)
   - Higher-level rephrasing (e.g., your B2 sentence at C1 and C2 levels)
   - Practical interpreter training tip

### AI Providers

Parlance supports multiple AI backends. Choose your provider in the AI Settings:

| Provider | Platform | Cost | Notes |
|----------|----------|------|-------|
| **Groq** (default) | Cloud API | Free tier (30K tokens/min) | Runs **Qwen 3 32B** — fast, accurate, free |
| **OpenAI** | Cloud API | Paid | GPT-4o / GPT-4o Mini |
| **Anthropic** | Cloud API | Paid | Claude Sonnet / Haiku |
| **Google Gemini** | Cloud API | Free tier available | Gemini 2.0 Flash |
| **Kimi (Moonshot)** | Cloud API | Paid | Moonshot v1 models |
| **Apple Intelligence** | On-device | Free | Private, no internet. Requires iOS 26+ |

**Groq is the recommended default** — it's free, fast, and runs Qwen 3 32B which produces accurate grammar feedback. Groq is the API platform; Qwen 3 32B is the AI model running on it.

> **Note on Apple Intelligence:** The on-device option uses Apple's FoundationModels framework (iOS 26+). It runs entirely on-device — no API key, no internet, fully private. Select "On-Device" in AI Settings to use it. If the on-device model isn't available on your device, the app falls back to your first configured cloud provider.

### RAG Knowledge Base

The RAG system (`rag-knowledge.js`) contains curated interpreter training knowledge:

- **Grammar rules** for each CEFR level (A1-C2), Spanish and French
- **DELE/DELF exam context** — what's tested at each level
- **Medical terminology** — body parts, conditions, procedures (CCHI/NBCMI aligned)
- **Legal terminology** — court terms, proceedings, rights (Miranda, etc.)
- **Interpreter ethics** — accuracy, impartiality, confidentiality, role boundaries
- **Keyword detection** — medical/legal context is injected only when your sentence contains relevant terms

---

## iOS App Setup

### Prerequisites
- Mac with Xcode installed
- iPhone running iOS 18+ (iOS 26+ for on-device AI)

### Step 1 — Clone and open
```bash
git clone https://github.com/Montrez/ParlanceApp.git
cd ParlanceApp
open Parlance.xcodeproj
```

### Step 2 — Add your API key (for Groq)

Create a file at `Parlance/Secrets.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>GROQ_API_KEY</key>
    <string>YOUR_GROQ_KEY_HERE</string>
</dict>
</plist>
```

Get a free Groq API key at [console.groq.com/keys](https://console.groq.com/keys).

> `Secrets.plist` is gitignored and never committed. You can also configure API keys directly in the app via the AI Settings button.

### Step 3 — Sign and run

1. Select your Apple ID team under **Signing & Capabilities**
2. Connect your iPhone or select a simulator
3. Press **Run** (Cmd+R)

---

## Web Version (GitHub Pages)

A standalone web version is available at the GitHub Pages URL. It includes:

- **WebLLM** — runs a small AI model directly in your browser (no API key needed)
- **Cloud providers** — connect Groq, OpenAI, Anthropic, Gemini, or Kimi with your own API key
- Full journaling with save/load
- Writing prompts and conjugation guides
- Same RAG knowledge base as the iOS app

---

## Project Structure

```
Parlance/
  AIProvider.swift          # Provider enum, settings, Keychain storage
  AISettingsView.swift      # SwiftUI settings UI for provider selection
  UnifiedAnalyzer.swift     # Routes analysis to selected provider
  ExternalAnalyzer.swift    # OpenAI-compatible API handler (Groq, OpenAI, Kimi)
  AnthropicAnalyzer.swift   # Anthropic API handler
  GeminiAnalyzer.swift      # Google Gemini API handler
  OnDeviceAnalyzer.swift    # Apple FoundationModels (on-device)
  ContentView.swift         # Main SwiftUI view + WKWebView bridge
  Config.swift              # Configuration loading (Secrets.plist, env vars)
  web/
    journal.js              # Journal UI + Swift bridge
    rag-knowledge.js        # RAG knowledge base
    index.html              # Main HTML
    styles.css              # Styles
    guide-es.html           # Spanish conjugation guide
    guide-fr.html           # French conjugation guide
docs/                       # GitHub Pages web version
training/                   # Training data generation scripts (historical)
```

---

## Training Data (Historical)

The `training/` directory contains scripts used to generate 2,241 training examples for a fine-tuning experiment (Qwen 2.5 3B). The fine-tuning was ultimately replaced by the RAG + cloud API approach, but the training data and scripts are preserved for reference. See `training/README.md` for details.

---

*Built with SwiftUI + WKWebView + RAG + Groq (Qwen 3 32B)*
