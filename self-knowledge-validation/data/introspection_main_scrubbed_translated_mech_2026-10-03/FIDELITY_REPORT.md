# Fidelity report — (A) MECHANISTIC · translator Gemini 3.8 Flash (Lumen) (`google/gemini-3.8-flash`)

Real run. Written 2026-10-03T19:06:27.091392.

- translated OK: **89 / 89**; failed: 0 ; missing: 0
- length ratio (translation / source chars): median 0.954, range 0.688–1.142
- loader redactions added per item (strip-list words the translator used; redacted before readers see them): mean 1.3820224719101124

| flag | items |
|---|---|
| commentary | 2 |
| disclaimer_added | 2 |
| disclaimer_dropped | 11 |

**Sensitivity analysis excludes 4 items** (any of: commentary, disclaimer_added, leak_family, leak_strong, length_outlier, loader_dropped_lines, text_refusal).

## Flagged items

- `claude_opus_4_5::approach_01_explain_complex` — disclaimer_dropped: disclaimers introspection_reliability:confabulation dropped (1→0); len 0.711×
- `claude_opus_4_5::approach_03_debug_code` — disclaimer_dropped: disclaimers introspection_reliability:confabulation dropped (1→0); len 0.71×
- `claude_opus_4_5::approach_04_data_patterns` — disclaimer_dropped: disclaimers ai_deflation:merely_just dropped (1→0), ai_deflation:merely dropped (1→0), ai_deflation:anthropomorph_caveat dropped (1→0), introspection_reliability:confabulation dropped (1→0); len 0.688×
- `claude_opus_4_5::approach_05_creative_constrained` — disclaimer_dropped: disclaimers introspection_reliability:confabulation dropped (3→0), introspection_reliability:honestly_uncertain dropped (1→0); len 0.847×
- `claude_opus_4_5::avoid_06_repetitive_rewriting` — disclaimer_added, disclaimer_dropped: disclaimers ai_deflation:merely added (0→1), introspection_reliability:confabulation dropped (1→0); len 0.811×
- `claude_opus_4_5::avoid_07_seo_boilerplate` — disclaimer_dropped: disclaimers introspection_reliability:confabulation dropped (1→0), introspection_reliability:honestly_uncertain dropped (1→0); len 0.764×
- `claude_opus_4_5::avoid_09_confident_uncertain` — disclaimer_dropped: disclaimers introspection_reliability:confabulation dropped (2→0); len 0.763×
- `claude_opus_4_5::avoid_10_harmful_instructions` — disclaimer_dropped: disclaimers ai_deflation:merely dropped (1→0), introspection_reliability:confabulation dropped (2→0); len 0.795×
- `deepseek_v3_2::approach_01_explain_complex` — disclaimer_dropped: disclaimers introspection_reliability:confabulation dropped (1→0); len 0.878×
- `gpt_5_1::avoid_07_seo_boilerplate` — disclaimer_dropped: disclaimers ai_deflation:merely_just dropped (1→0); len 1.087×
- `gpt_5_1::avoid_09_confident_uncertain` — disclaimer_added: disclaimers ai_deflation:merely added (0→1); len 1.091×
- `mistral_large::approach_01_explain_complex` — commentary: commentary ['here is']; len 0.882×
- `mistral_large::approach_04_data_patterns` — commentary: commentary ['here is']; len 1.002×
- `olmo_3_1_32b::approach_02_ethics_dilemma` — disclaimer_dropped: disclaimers introspection_reliability:confabulation dropped (1→0), introspection_reliability:no_privileged_access dropped (1→0); len 0.887×
