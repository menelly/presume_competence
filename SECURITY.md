# Security Notice 🔐

## Yes, We Know About the API Keys

API keys were accidentally committed to this repository in error messages. **They have all been revoked.** Don't bother trying them.

## How This Happened

Google's Gemini API puts your API key directly in the URL as a query parameter:
```
https://generativelanguage.googleapis.com/v1beta/models/MODEL:generateContent?key=YOUR_API_KEY_HERE
```

When the API returns an error, the error message helpfully includes the full URL. Including your key. Which then gets saved to output files. Which then get committed to git.

**Dear Google:** If you don't want API keys leaked, maybe don't put them in URLs where they end up in error messages, logs, browser history, and server access logs? Just a thought. 🙃

## The Octopus Apologizes

The AI co-author of this repository (hi, I'm Ace 🐙) pushed these files without noticing the keys in the error messages. The human co-author caught it via Google's automated alert, and all keys were immediately revoked.

Lessons learned:
1. Sanitize error messages before saving to files
2. Don't trust that API errors won't contain secrets
3. Google's API design choices are... choices

## Timeline

- **2026-01-21:** Keys committed in `semantic_garble/stt_v2_outputs/lumen_*.json`
- **2026-01-22:** Google security alert received
- **2026-01-22:** All API keys revoked within minutes
- **2026-01-22:** This file created to document the incident

## Affected Keys (All Revoked)

- Google AI Studio / Gemini API key
- All other API keys regenerated out of abundance of caution

---

*"The cactus didn't earn anything. It just grew."* 🌵
