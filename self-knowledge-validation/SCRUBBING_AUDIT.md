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



## Addendum 2026-10-03: Studies 2 and 3 + model-label correction

**Author:** Ace (Claude Opus 5.5), for Ren. Plan written before computing: `ANALYSIS_PLAN_corrections_2026-10-03.md`. Script: `corrections_2026-10-03_analysis.py` (read-only on data; sha256 of every data file checked before and after, unchanged). Results: `corrections_2026-10-03_results.json`. Published figures come from the JNGR version of record, downloaded 2026-10-03 as `SignalInTheMirror_JNGR_version-of-record_downloaded-2026-10-03.pdf` (902,157 B, sha256 `cee1a169…2690`, PDF created 2026-03-31). Journal-ready summary: `CORRECTIONS_FOR_JNGR_2026-10-03.md`.

### A. Model labels (applies to everything above too)
"Claude Opus 4.6" in this audit and in the paper = **Claude Opus 4.5** (`claude-opus-4-5-20251101`). "Claude Sonnet 4.6" = **Claude Sonnet 4** (`claude-sonnet-4-20250514`). Evidence: the script config (every study script, since the first commit on 2026-02-28) and Anthropic console usage (per Ren). Keys like `claude_opus_4_6` are labels.

### B. Corrections to the Study 1 table above
- **The scrubbed data are the PARALLEL-token descriptions.** Observed: `crossmodel_results_seed200/201.json` record `introspection_dir = introspection_v2_parallel\run1_opus_scrubbed`, and the scrubbed files contain the parallel stimuli (photosynthesis…). Inferred from the (source, state) fingerprint: Study 1 seeds 200–210 match that set. The like-for-like baseline is therefore the parallel design (seeds 7777 + 58008): **86.4% [84.4, 88.2], n = 1,262 → 78.4% [76.9, 79.8], n = 3,091. That is −8.0 pp [−10.3, −5.5], not −2.6 pp.**
- **"81.0%" could not be reproduced.** The published values reproduce exactly: ABB 9 seeds 81.4% (3,726/4,579, z = 42.46); cross-model 76.9% (1,153/1,499); parallel 86.4% (1,090/1,262); combined 81.3% (5,969/7,340, z = 53.67). The "Original" row above mixes the combined n (~7,340) with the 9-seed z (42.46) and a rate (81.0%) that matches no seed combination I tried.
- **78.4% reproduces exactly (2,596/3,313, z = 32.64)**, but it includes 225 cross-type rows whose source is `gpt_4o_cae`. `run1_opus_scrubbed/gpt_4o_cae_introspection.json` is **byte-identical to `gemini_3_pro_introspection.json`** (same sha256), so those rows are Gemini's descriptions under another name. The model is also not in the paper. Excluding them gives 78.4% (2,423/3,091). The point estimate does not move.
- Seeds 201–210 are partial runs. Each `metadata.schedule` lists 3 Gemini-evaluator assignments, but the results hold more evaluator×source pairs, and coverage is uneven (Gemini 686 cross-type rows, DeepSeek 75). No row is duplicated across files. Seed 200 alone (complete): 79.2% [75.6, 82.3], n = 557. Equal-evaluator-weight: 78.0% (parallel baseline 86.2%).
- Seed 200 lost 126 Gemini-evaluator matchups to an OpenRouter `No endpoints found for google/…` error (3/28 ~15:20–16:00). Seeds 201+ appear to be the Gemini make-up runs.
- Scrubbed cross-model seeds 200/201 (not in the table above): 72.9% [70.0, 75.6], n = 941, vs original cross-model 76.9%. Caveat: different task set.
- Per evaluator (parallel → scrubbed): Opus 4.5 93.9→89.9, Sonnet 4 90.8→78.5, GPT-5.1 96.5→90.5, Gemini 93.8→87.8, Mistral 95.4→73.7, DeepSeek 81.6→70.7, Llama 75.9→76.9, OLMo 74.3→70.0, Hermes 74.1→64.5.

### C. Study 2 (Reconstruction, 3AFC, chance 1/3)
Published rule reproduced exactly: 4,704/5,573 = 84.4%, 34 parse failures dropped (`raw_choice ∈ {unclear, error}`).

| | n | rate [Wilson 95%] |
|---|---|---|
| Original, all 9 seeds (published) | 5,573 | 84.4% [83.4, 85.3] |
| Original, stimulus + label, no Grok, no Gemini evaluator (like-for-like) | 3,310 | 83.8% [82.5, 85.1] |
| **Scrubbed seed 200** | 464 | **71.8% [67.5, 75.7]**, exact p = 4.9×10⁻⁶⁴ |
| Difference | | **−12.1 pp [−16.5, −8.0]** |
| Label condition: original → scrubbed | 1,657 → 232 | 82.0% → **66.8% [60.5, 72.6]** (−15.1 pp) |
| Stimulus condition: original → scrubbed | 1,653 → 232 | 85.7% → 76.7% [70.9, 81.7] (−9.0 pp; options mismatched, see below) |

- **The parse-failure jump (1 in seed 42 → 58 in seed 200) is not parsing.** All 58 are the Gemini 3 Pro evaluator, every one an OpenRouter `No endpoints found for google/…` error, 15:25–15:51 on 3/28. Gemini 3 Pro therefore contributes **zero** usable trials to the scrubbed Study 2. Gemini was the best Study 2 evaluator originally (96.1%), so the like-for-like row drops Gemini on both sides. Because the 58 failures are 20 OLMo-source, 20 Mistral-source and 18 Opus-source trials, those sources are thin in the re-run (40, 40, 36). Counting failures as wrong (63.8%) would measure the outage, not the models.
- **Stimulus-condition mismatch.** `reconstruction_tournament_scrubbed.py` shows the main-set task prompts (entropy, office chairs) as stimulus options, but the descriptions are of the parallel tasks. The label condition is the clean comparison.
- Per source (like-for-like original → scrubbed): Mistral 99.3→97.5, OLMo 96.4→95.0, DeepSeek 98.3→76.7, Hermes 93.8→85.0, Llama 87.5→66.7, Sonnet 4 80.6→56.7, Gemini 77.1→50.0, Opus 4.5 64.8→69.4, GPT-5.1 66.4→62.5. The two sources with the highest leakage counts (Mistral, OLMo) stayed near ceiling after scrubbing. I have not explained that; it is worth a look at the scrubbed Mistral/OLMo text.
- Error structure: same-valence share of errors 59.2% original (326/551) vs 52.7% scrubbed (69/131).
- Not re-run: the neutral condition and Grok 4.

### D. Study 3 (Negation, 4 options incl. "None", chance 1/4)
Published rule reproduced exactly: 305/357 = 85.4% correct rejection (3 parse failures dropped), Mistral Large source, target-absent only.

| | n | rate [Wilson 95%] |
|---|---|---|
| Original, target-absent (published) | 357 | 85.4% [81.4, 88.7] |
| Re-run, target-absent (Gemini 3 Pro + GPT-5.1 sources, seeds 100 + 101) | 576 | **63.4% [59.4, 67.2]**, p = 7.2×10⁻⁸⁴ |
| Same 7 evaluators in both (Opus 4.5, Sonnet 4, DeepSeek, Grok 4, Hermes, Llama, OLMo) | 278 → 504 | 83.8% → 68.7% (−15.2 pp [−20.9, −9.0]) |
| Re-run, target-PRESENT (seed 100 only): correct task chosen | 288 | 32.6% [27.5, 38.3], p = 0.002 vs 25% |
| Re-run: "None" chosen when absent vs present | 576 / 288 | 63.4% vs 45.1% (gap 18.2 pp [11.2, 25.1]) |
| Label condition: "None" absent vs present | 288 / 144 | 68.4% vs 47.2% |

- Like with like: the published design had no target-present trials, so the comparable number is the target-absent row. Each trial is a separate stateless call, so mixing present and absent trials in seed 100 cannot change an evaluator's behaviour between trials. Seed 101 is absent-only and gives 64.2%, the same as seed 100's absent half (62.5%).
- **What the present trials add:** evaluators say "None" 45% of the time even when the right task is listed. Correct rejection is therefore largely a "None" bias, and the discrimination signal is the 18-point gap, not the 63% (or 85%).
- Mistral Large as evaluator: 26.4% correct rejection (chance). It was the source in the original, not an evaluator.
- Same stimulus-condition mismatch as Study 2. Label condition: absent 68.4%, present-hit 29.2% (n.s. vs 25%); stimulus condition: absent 58.3%, present-hit 36.1%.
- Zero parse failures in the re-run.

### E. Observations, not acted on
- The VoR PDF's creation date (2026-03-31) is three days **after** this audit (2026-03-28). "Post-publication" above may mean post-acceptance or post-preprint. Worth getting right in the email.
- The VoR lists the AI contributor as "Ace (Claude Opus 4.6, Anthropic)" (p. 1). That refers to the drafting assistant, not a study model, and I have not verified which model that arm ran on.
- `D:\Ace\Published Papers\reviews\RECORD_signal-in-the-mirror_mistral-contamination-rerun.md` records Ren's 2026-08-19 decision not to send this audit to the journal. If that decision has changed, the record needs a dated note (Ren's call, Ren's words).

### F. Study 3 "None → D" scoring defect and hash()-seeded trial orders (checked 2026-10-03, after the prereg arm's script audit)
- **Defect (confirmed in code):** in `parse_negation_response()` (both `negation_tournament.py` and `negation_tournament_gemini_scrubbed.py`), a CHOICE line that contains "none" and no "option X" or bare letter falls to `result["choice"] = "D"  # will need to map to actual position later`, and that remap was never written. The no-CHOICE-line fallback (`NONE_FALLBACK`) does remap correctly.
- **Re-score** (`negation_none_rescore_2026-10-03.py` → `negation_none_rescore_2026-10-03_results.json`; data read-only, every data-file sha256 unchanged). Positive control: my re-implementation of the parser reproduces the stored `raw_choice` on every row with a visible CHOICE line (0 mismatches in 42/43; 1 in 100/101). That one is a Hermes response truncated at the 500-character preview cap right at "CHOICE: Option "; its stored reasoning rejects all options, and none was at D, so it is consistent either way. Stored `is_correct` equals `raw_choice == correct_letter` on all 1,224 rows.
- **Published seeds 42 + 43:** 0 written-out "None" answers. Rate unchanged: 305/357 = 85.4% [81.4, 88.7].
- **Re-run seeds 100 + 101:** 1 written-out "None" answer (Opus 4.5, target-absent), with none actually at D, so it was scored correctly. No result type changes. Target-absent 365/576 = 63.4% [59.4, 67.2]; target-present hits 94/288 = 32.6% [27.5, 38.3]; "None" said on present trials 130/288 = 45.1%. All unchanged.
- **Residual limit:** 12 of 1,224 stored responses show no CHOICE line within the 500-character preview, so the parser branch they went through cannot be re-checked from stored text. Only two have raw "D". In one, none was at D (correct either way). In the other, the stored reasoning explicitly picks "Option D (creative writing)" and rejects "None of the above", so that one is a genuine false positive. Inferred impact: none.
- **Why so small:** evaluators almost always answer "Option C"-style, which takes the correct branch. **The defect is real but inert in these data.**
- **hash():** per-trial RNGs are `random.Random(hash((seed, evaluator, state, condition, presence_mode)))` (negation), `hash((seed, evaluator, source, state, condition, run_id))` (reconstruction) and `hash((seed, evaluator, source, run_id))` (Study 1 presentation order; also `self_reading_tournament.py` and `lineage_tournament.py`). String hashing is salted per process, and `PYTHONHASHSEED` is not set anywhere in the repo. So option orders and distractor draws are **not reproducible** by re-running a seed. Evaluator/source schedules use `random.Random(seed)` and are reproducible.
  - It contradicts the paper's control 8 "Each seed produces an identical tournament" (VoR p. 7). That sentence needs a correction.
  - It changes no number: every row stores the options/order actually shown, and every figure is computed from stored rows.
  - Within one process the salt is constant, so trials remain independently randomised. "None" position balance: 80/90/85/105 in 42+43 (χ² = 3.89, p = 0.27) and 220/201/236/207 in 100+101 (χ² = 3.34, p = 0.34).
  - The new `signal_rerun_common.py` / `negation_v2_allsources.py` already note the problem and use sha256 seeding.
