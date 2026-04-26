# Diario — Spanish Writing Coach
### Getting it onto your iPhone 15 Pro Max in 10 minutes

---

## Before you start

1. **Find your Anthropic API key**
   - Go to console.anthropic.com → API Keys → Create key
   - Copy it — you'll need it in Step 2

2. **Make sure Xcode is fully installed** (not just downloading)

---

## Step 1 — Open the project

Double-click `Diario.xcodeproj`
Xcode will open. You'll see the file list on the left.

---

## Step 2 — Add your API key

In the left sidebar, click `Config.plist`
You'll see:

```
ANTHROPIC_API_KEY    YOUR_API_KEY_HERE
```

Double-click `YOUR_API_KEY_HERE` and replace it with your actual key.
Hit Enter. Save with ⌘S.

---

## Step 3 — Sign the app with your Apple ID

1. In the left sidebar, click the blue **Diario** project icon at the very top
2. In the main area, click the **Diario** target under "TARGETS"
3. Click the **Signing & Capabilities** tab
4. Under "Team", click the dropdown and choose **Add an Account**
5. Sign in with your Apple ID (free — no paid developer account needed for personal use)
6. Once signed in, select your name from the Team dropdown
7. The "Bundle Identifier" should auto-resolve — if it shows a red error,
   change `com.diario.spanishjournal` to something unique like `com.YOURNAME.diario`

---

## Step 4 — Connect your iPhone

Plug your iPhone 15 Pro Max into your Mac with a cable.
Your iPhone will ask "Trust This Computer?" — tap **Trust** and enter your passcode.

---

## Step 5 — Select your iPhone as the target

At the top of Xcode, you'll see a device selector that probably says
"iPhone 15 Pro" or similar. Click it and select **your actual device** from the list.

---

## Step 6 — Hit Run

Click the **▶ Play button** in the top-left of Xcode (or press ⌘R).

Xcode will build the app and install it on your phone.
The first time, your iPhone may say the app is from an "Untrusted Developer."

**Fix that on your iPhone:**
Settings → General → VPN & Device Management → Your Apple ID → Trust

Then open the app again — it'll launch normally.

---

## You're done!

The Diario app is now on your iPhone home screen.
It will stay there unless you delete it. You don't need to keep Xcode open.

---

## If something goes wrong

| Problem | Fix |
|---|---|
| "No account for team" error | Make sure you signed into Xcode with your Apple ID (Step 3) |
| "Untrusted Developer" on phone | Settings → General → VPN & Device Management → Trust |
| Bundle ID conflict | Change the bundle ID to something unique (Step 3, last bullet) |
| API not working in app | Double-check your key in Config.plist — no extra spaces |
| Build fails with Swift error | Make sure all 5 files are in the Diario folder and added to the target |

---

## Want to share it with friends via TestFlight?

1. Sign up for Apple Developer Program ($99/year) at developer.apple.com
2. In Xcode: Product → Archive
3. Upload to App Store Connect
4. Add testers in TestFlight tab

---

*Built with SwiftUI + WKWebView + Claude API*
