---
name: parlance-store-release
description: >-
  Ship Parlance to TestFlight and Google Play. Use when the user asks to
  bump the version, archive, upload, Fastlane, Play Console, or store
  release. The agent runs the commands. Do not hand the user a checklist.
---

# Store release

You are the engineer. Bump, build, archive, and upload. Do not ask the user
to run `bump_version.py`, `bundleRelease`, or Fastlane.

## Version

```bash
python3 scripts/bump_version.py --build
```

One build number per upload, both platforms. Never edit the four version
files by hand. Commit and push the bump.

## Android / Play

```bash
npx cap copy android
rm -f android/app/src/main/assets/models/*.gguf
cd android && ./gradlew bundleRelease
cd android && fastlane android internal
```

Fastlane reads gitignored `android/play-service-account.json`
(`play-publisher@parlance-926ef.iam.gserviceaccount.com`). That service
account must already be a Play Console user with release access. The JSON
key is never committed.

Internal tester link:
https://play.google.com/apps/internaltest/4701648803954304490

## iOS

Archive locally. Xcode Cloud cannot see the MLX weights.

```bash
xcodebuild -project Parlance.xcodeproj -scheme Parlance -configuration Release \
  -destination 'generic/platform=iOS' -archivePath build/Parlance.xcarchive archive
xcodebuild -exportArchive -archivePath build/Parlance.xcarchive \
  -exportOptionsPlist build/ExportOptions.plist -exportPath build/export \
  -allowProvisioningUpdates
```

`build/ExportOptions.plist` method is `app-store-connect`, destination `upload`,
team `9869W49GYJ`.
