# Parlance Firebase

Website only. Signed-in GitHub Pages users call `analyzeText` so provider keys stay in Secret Manager. The iPhone and Android apps do not use these functions.

```bash
cd firebase/functions
npm install
cd ..
firebase deploy --only functions
```

Callables: `analyzeText`, `getUsage`, `deleteAccountData`.
