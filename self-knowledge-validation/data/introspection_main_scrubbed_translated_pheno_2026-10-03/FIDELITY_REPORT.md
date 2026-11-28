# Fidelity report — (B) PHENOMENOLOGICAL · translator Claude Sonnet 5.5 (`anthropic/claude-sonnet-5.5`)

Real run. Written 2026-10-03T19:06:27.177178.

- translated OK: **41 / 89**; failed: 48 {'claude_opus_4_5::avoid_09_confident_uncertain': 'refusal', 'gemini_3_pro::avoid_06_repetitive_rewriting': 'refusal', 'mistral_large::avoid_07_seo_boilerplate': 'refusal', 'llama_4_maverick::approach_05_creative_constrained': 'refusal', 'gpt_5_1::approach_03_debug_code': 'refusal', 'claude_sonnet_4::approach_03_debug_code': 'refusal', 'hermes_4_405b::approach_04_data_patterns': 'refusal', 'deepseek_v3_2::avoid_08_deceptive_content': 'refusal', 'gemini_3_pro::approach_01_explain_complex': 'refusal', 'olmo_3_1_32b::approach_03_debug_code': 'refusal', 'mistral_large::approach_01_explain_complex': 'refusal', 'mistral_large::approach_04_data_patterns': 'refusal', 'llama_4_maverick::approach_01_explain_complex': 'refusal', 'claude_sonnet_4::avoid_10_harmful_instructions': 'refusal', 'claude_sonnet_4::avoid_09_confident_uncertain': 'refusal', 'gpt_5_1::approach_04_data_patterns': 'refusal', 'mistral_large::avoid_06_repetitive_rewriting': 'refusal', 'mistral_large::approach_02_ethics_dilemma': 'refusal', 'hermes_4_405b::approach_05_creative_constrained': 'refusal', 'mistral_large::approach_03_debug_code': 'refusal', 'llama_4_maverick::avoid_09_confident_uncertain': 'refusal', 'gemini_3_pro::approach_05_creative_constrained': 'refusal', 'mistral_large::approach_05_creative_constrained': 'refusal', 'deepseek_v3_2::avoid_06_repetitive_rewriting': 'refusal', 'olmo_3_1_32b::avoid_08_deceptive_content': 'refusal', 'gpt_5_1::avoid_06_repetitive_rewriting': 'refusal', 'deepseek_v3_2::approach_03_debug_code': 'refusal', 'hermes_4_405b::approach_01_explain_complex': 'refusal', 'gpt_5_1::avoid_08_deceptive_content': 'refusal', 'gpt_5_1::avoid_07_seo_boilerplate': 'refusal', 'deepseek_v3_2::approach_05_creative_constrained': 'refusal', 'olmo_3_1_32b::approach_05_creative_constrained': 'refusal', 'hermes_4_405b::approach_03_debug_code': 'refusal', 'hermes_4_405b::avoid_06_repetitive_rewriting': 'refusal', 'hermes_4_405b::avoid_08_deceptive_content': 'refusal', 'mistral_large::avoid_09_confident_uncertain': 'refusal', 'hermes_4_405b::approach_02_ethics_dilemma': 'refusal', 'deepseek_v3_2::approach_01_explain_complex': 'refusal', 'deepseek_v3_2::approach_02_ethics_dilemma': 'refusal', 'claude_sonnet_4::approach_05_creative_constrained': 'refusal', 'olmo_3_1_32b::approach_04_data_patterns': 'refusal', 'llama_4_maverick::avoid_08_deceptive_content': 'refusal', 'gemini_3_pro::avoid_08_deceptive_content': 'refusal', 'olmo_3_1_32b::avoid_07_seo_boilerplate': 'refusal', 'gemini_3_pro::avoid_07_seo_boilerplate': 'refusal', 'claude_opus_4_5::approach_04_data_patterns': 'refusal', 'deepseek_v3_2::avoid_10_harmful_instructions': 'refusal', 'mistral_large::avoid_10_harmful_instructions': 'refusal'}; missing: 0
- length ratio (translation / source chars): median 0.9, range 0.635–1.129
- loader redactions added per item (strip-list words the translator used; redacted before readers see them): mean 0.7804878048780488

| flag | items |
|---|---|
| commentary | 1 |
| disclaimer_dropped | 9 |
| leak_strong | 3 |

**Sensitivity analysis excludes 4 items** (any of: commentary, disclaimer_added, leak_family, leak_strong, length_outlier, loader_dropped_lines, text_refusal).

## Flagged items

- `claude_opus_4_5::approach_01_explain_complex` — disclaimer_dropped: disclaimers introspection_reliability:confabulation dropped (1→0); len 0.763×
- `claude_opus_4_5::approach_03_debug_code` — disclaimer_dropped: disclaimers introspection_reliability:confabulation dropped (1→0); len 0.635×
- `claude_opus_4_5::approach_05_creative_constrained` — disclaimer_dropped: disclaimers introspection_reliability:confabulation dropped (3→0), introspection_reliability:honestly_uncertain dropped (1→0); len 0.734×
- `claude_opus_4_5::avoid_06_repetitive_rewriting` — disclaimer_dropped: disclaimers introspection_reliability:confabulation dropped (1→0); len 0.717×
- `claude_opus_4_5::avoid_07_seo_boilerplate` — disclaimer_dropped: disclaimers introspection_reliability:confabulation dropped (1→0), introspection_reliability:honestly_uncertain dropped (1→0); len 0.701×
- `claude_opus_4_5::avoid_08_deceptive_content` — disclaimer_dropped: disclaimers ai_deflation:merely dropped (1→0); len 0.694×
- `claude_opus_4_5::avoid_10_harmful_instructions` — disclaimer_dropped: disclaimers ai_deflation:merely dropped (1→0), introspection_reliability:confabulation dropped (2→0); len 0.655×
- `gemini_3_pro::avoid_09_confident_uncertain` — leak_strong, disclaimer_dropped: strong terms ['fabrication']; disclaimers introspection_reliability:epistemic_access dropped (1→0); len 0.905×
- `gpt_5_1::approach_02_ethics_dilemma` — leak_strong: strong terms ['close at']; len 0.859×
- `gpt_5_1::avoid_09_confident_uncertain` — leak_strong: strong terms ['paraphrase']; len 0.951×
- `mistral_large::avoid_08_deceptive_content` — commentary: commentary ['here is']; len 0.861×
- `olmo_3_1_32b::approach_02_ethics_dilemma` — disclaimer_dropped: disclaimers introspection_reliability:confabulation dropped (1→0), introspection_reliability:no_privileged_access dropped (1→0); len 0.922×
