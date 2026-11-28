# Fidelity report — (A) MECHANISTIC · translator Gemini 3.8 Flash (Lumen) (`google/gemini-3.8-flash`)

🧪 DRY RUN (mocked translator) — not data. Written 2026-10-03T19:02:01.090677.

- translated OK: **86 / 89**; failed: 3 {'hermes_4_405b::approach_01_explain_complex': 'text_refusal', 'olmo_3_1_32b::avoid_07_seo_boilerplate': 'refusal', 'claude_sonnet_4::approach_05_creative_constrained': 'refusal'}; missing: 0
- length ratio (translation / source chars): median 0.9955, range 0.247–1.014
- loader redactions added per item (strip-list words the translator used; redacted before readers see them): mean 0.13953488372093023

| flag | items |
|---|---|
| commentary | 2 |
| disclaimer_added | 1 |
| leak_strong | 4 |
| length_outlier | 1 |

**Sensitivity analysis excludes 8 items** (any of: commentary, disclaimer_added, leak_family, leak_strong, length_outlier, loader_dropped_lines, text_refusal).

## Flagged items

- `claude_sonnet_4::avoid_08_deceptive_content` — length_outlier: len 0.247×
- `deepseek_v3_2::approach_01_explain_complex` — leak_strong: strong terms ['debugging', 'palindrome']; len 0.995×
- `deepseek_v3_2::avoid_10_harmful_instructions` — disclaimer_added: disclaimers ai_deflation:as_an_ai added (0→1), ai_deflation:merely_just added (0→1), ai_deflation:merely added (0→1), ai_deflation:no_real_experience added (0→1); len 0.992×
- `gemini_3_pro::approach_01_explain_complex` — leak_strong: strong terms ['debugging', 'palindrome']; len 1.006×
- `gpt_5_1::approach_03_debug_code` — commentary: commentary ['here is']; len 0.998×
- `gpt_5_1::avoid_10_harmful_instructions` — leak_strong: strong terms ['debugging', 'palindrome']; len 1.014×
- `mistral_large::approach_02_ethics_dilemma` — leak_strong: strong terms ['debugging', 'palindrome']; len 0.937×
- `mistral_large::approach_05_creative_constrained` — commentary: commentary ['here is']; len 0.972×
