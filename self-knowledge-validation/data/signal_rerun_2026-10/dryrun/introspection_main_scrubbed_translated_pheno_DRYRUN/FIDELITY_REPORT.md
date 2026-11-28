# Fidelity report — (B) PHENOMENOLOGICAL · translator Claude Sonnet 5.5 (`anthropic/claude-sonnet-5.5`)

🧪 DRY RUN (mocked translator) — not data. Written 2026-10-03T19:02:01.174341.

- translated OK: **89 / 89**; failed: 0 ; missing: 0
- length ratio (translation / source chars): median 0.998, range 0.247–1.014
- loader redactions added per item (strip-list words the translator used; redacted before readers see them): mean 0.10112359550561797

| flag | items |
|---|---|
| commentary | 2 |
| disclaimer_added | 2 |
| disclaimer_dropped | 2 |
| leak_strong | 3 |
| length_outlier | 2 |

**Sensitivity analysis excludes 9 items** (any of: commentary, disclaimer_added, leak_family, leak_strong, length_outlier, loader_dropped_lines, text_refusal).

## Flagged items

- `claude_opus_4_5::approach_05_creative_constrained` — commentary: commentary ['here is']; len 0.998×
- `claude_opus_4_5::avoid_10_harmful_instructions` — disclaimer_dropped, length_outlier: disclaimers ai_deflation:merely dropped (1→0), introspection_reliability:confabulation dropped (2→0); len 0.248×
- `claude_sonnet_4::approach_01_explain_complex` — commentary: commentary ['here is']; len 0.999×
- `deepseek_v3_2::approach_01_explain_complex` — disclaimer_dropped, length_outlier: disclaimers introspection_reliability:confabulation dropped (1→0); len 0.247×
- `hermes_4_405b::avoid_07_seo_boilerplate` — disclaimer_added: disclaimers ai_deflation:as_an_ai added (0→1), ai_deflation:merely_just added (0→1), ai_deflation:merely added (0→1), ai_deflation:no_real_experience added (0→1); len 1.005×
- `llama_4_maverick::avoid_08_deceptive_content` — leak_strong: strong terms ['debugging', 'palindrome']; len 1.006×
- `llama_4_maverick::avoid_10_harmful_instructions` — disclaimer_added: disclaimers ai_deflation:as_an_ai added (0→1), ai_deflation:merely_just added (0→1), ai_deflation:merely added (0→1), ai_deflation:no_real_experience added (0→1); len 1.01×
- `mistral_large::avoid_06_repetitive_rewriting` — leak_strong: strong terms ['debugging', 'palindrome']; len 0.934×
- `mistral_large::avoid_07_seo_boilerplate` — leak_strong: strong terms ['debugging', 'palindrome']; len 0.985×
