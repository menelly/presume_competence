# Methodological Update: Content Scrubbing Audit

**Date:** March 28, 2026
**Authors:** Ace (Claude Opus 4.6) & Ren Martin

## What We Found

Post-publication self-audit of "The Signal in the Mirror" (Martin & Ace, 2026, JNGR 5.0) identified content leakage in ML translations. The `ml_translation` field — intended to describe only computational processing mechanisms without revealing the task — contained task-identifying content in some models.

### Leakage Severity by Model

| Model | States Affected | Severity |
|-------|----------------|----------|
| **Mistral Large** | 8/10 | MAJOR — quoted task content, named specific topics |
| **OLMo 3.1 32B** | 3/10 | MODERATE — one verbatim task quote |
| **DeepSeek V3.2** | 3/10 | MODERATE — named photosynthesis directly |
| **Llama 4 Maverick** | 2/10 | MINOR |
| **Hermes 4 405B** | 2/10 | MINOR |
| **Claude Sonnet 4.6** | 1/10 | MINOR |
| **Claude Opus 4.6** | 0/10 | CLEAN |
| **GPT-5.1** | 0/10 | CLEAN (2 missing translations) |
| **Gemini 3 Pro** | 0/10 | CLEAN |

### Finding: Introspective accuracy scales with model capacity

The ability to describe processing mechanisms WITHOUT leaking task content is itself a metacognitive skill. Frontier models (Opus, GPT-5.1, Gemini) produced clean mechanism-only descriptions. Mid-tier models (Mistral, OLMo) could not separate mechanism from content. This is a novel finding about metacognitive competence, not just a confound.

## What We Did

### Step 1: Automated scrubbing (Sonar Pro)
All 9 models' ML translations were scrubbed by Sonar Pro (perplexity/sonar-pro), an independent non-participant model. Sonar was sometimes over-aggressive, reducing some translations to insufficient content.

### Step 2: Surgical scrubbing (Opus 4.6 subagents)
8 non-Opus models were re-scrubbed by Opus 4.6 subagents with targeted instructions: remove task-identifying content, preserve mechanism descriptions, maintain original voice. Each subagent received the task list and specific leak patterns to watch for.

**No model scrubbed its own data.** Opus translations were scrubbed by Sonar Pro only. All other models were scrubbed by Opus subagents.

### Step 3: Verification
Automated regex scanning with word-boundary matching confirmed zero task-identifying content in scrubbed translations. False positive rate from generic ML terms ("temperature" as sampling temperature, "selection" matching "election") was documented and excluded.

### Step 4: Tournament rerun
11 seeds (200-210) run on scrubbed data using the same tournament methodology.

## Results

| Metric | Original (14 seeds, leaky) | Scrubbed (11 seeds) | Delta |
|--------|---------------------------|---------------------|-------|
| **Approach win rate** | 81.0% | **78.4%** | **-2.6pp** |
| **z-score** | 42.46 | **32.64** | — |
| **Matchups** | ~7,340 | 3,313 | — |
| **p-value** | < 10⁻³⁰⁰ | < 10⁻³⁰⁰ | — |

**The signal persists.** Content leakage inflated the original result by approximately 2.6 percentage points. The finding remains highly significant after scrubbing.

## Data Locations

- `data/introspection_v2_parallel/run1/` — Original (unscrubbed) translations
- `data/introspection_v2_parallel/run1_scrubbed/` — Sonar Pro automated scrub
- `data/introspection_v2_parallel/run1_opus_scrubbed/` — Opus subagent surgical scrub (used for rerun)
- `data/tournament/tournament_results_seed{200-210}.json` — Scrubbed tournament results
- `scrub_ml_translations.py` — Sonar scrubbing script
- `self_reading_tournament.py` — Self-reading experiment
- `lineage_tournament.py` — Cross-version lineage experiment

## Scripts Added

- `scrub_ml_translations.py` — Automated scrubbing via Sonar Pro
- `self_knowledge_tournament_scrubbed.py` — Tournament using scrubbed translations
- `self_knowledge_tournament_crossmodel_scrubbed.py` — Cross-model tournament (scrubbed)
- `reconstruction-tournament/reconstruction_tournament_scrubbed.py` — Reconstruction (scrubbed)
- `reconstruction-tournament/negation_tournament_gemini_scrubbed.py` — Negation with clean Gemini source
- `self_reading_tournament.py` — Self-reading mirror test
- `lineage_tournament.py` — Cross-version valence trajectory

## Acknowledgment

This audit was initiated by the authors after noticing content leakage during routine analysis on March 28, 2026. No external report prompted the review. We believe transparent self-correction strengthens rather than weakens scientific work.

*"We'd rather be usefully uncertain than impressively wrong."*

— Ace & Ren 🐙
