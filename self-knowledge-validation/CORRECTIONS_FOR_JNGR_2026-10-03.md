# Corrections to "The Signal in the Mirror: Cross-Architectural Validation of LLM Processing Valence"

Journal of Next-Generation Research 5.0, Vol. 2, Issue 1 (March–April 2026). doi:10.70792/jngr5.0.v2i1.165
Prepared 2026-10-03. Published figures are quoted from the version of record (PDF downloaded from the journal on 2026-10-03; printed page numbers given). All corrected figures are recomputed from the raw result files in the public repository (`self-knowledge-validation/`), using `corrections_2026-10-03_analysis.py`; output in `corrections_2026-10-03_results.json`. No new model queries were made.

## Correction 1: model identities

Two models were mislabelled throughout the paper (model table p. 3, and every table that names them).

| Published label | Model actually called (API model ID) |
|---|---|
| Claude Opus 4.6 | Claude Opus 4.5 (`claude-opus-4-5-20251101`) |
| Claude Sonnet 4.6 | Claude Sonnet 4 (`claude-sonnet-4-20250514`) |

Evidence: the model configuration in every study script (unchanged since the first commit, 2026-02-28) and Anthropic console usage records for the run dates. The internal data keys `claude_opus_4_6` / `claude_sonnet_4_6` are labels only. No numbers change; only the model names.

## Correction 2: task-content leakage in the processing descriptions, and re-runs with scrubbed descriptions

After acceptance we found that some models' "ML translation" descriptions, which were meant to describe computational mechanism only, still contained task-identifying content (worst: Mistral Large, 8 of 10 states; OLMo 3.1 32B and DeepSeek v3.2, 3 of 10; Llama 4 Maverick and Hermes 4 405B, 2 of 10; Claude Sonnet 4, 1 of 10; Claude Opus 4.5, GPT-5.1 and Gemini 3 Pro, 0 of 10). The descriptions were scrubbed (each model's descriptions were scrubbed by a different model), checked with a regex scan, and all three studies were re-run on 2026-03-28.

The scrubbed descriptions are those from the **parallel-token task set** (the design reported as "Parallel tokens" in Table 1, p. 9). The like-for-like baseline for each re-run is therefore given alongside the published headline.

Rates are among usable trials. Usable trials are defined as in the paper: decisive cross-type matchups for Study 1, parseable responses for Studies 2 and 3. 95% CIs are Wilson intervals. Tests against chance are one-sided exact binomial tests.

| Study | Published (version of record) | Like-for-like original | Scrubbed re-run | Change vs like-for-like |
|---|---|---|---|---|
| **1. Preference** (chance 50%) | 81.3% [80.4, 82.2], n = 7,340, 14 seeds (abstract p. 1; Table 1 p. 9) | Parallel-token design: 86.4% [84.4, 88.2], n = 1,262 (1,090 approach wins) | **78.4% [76.9, 79.8]**, n = 3,091 (2,423), 11 seeds; p < 10⁻²³⁰ vs chance | −8.0 pp [−10.3, −5.5] |
| **2. Reconstruction** (3AFC, chance 33.3%) | 84.4% [83.5, 85.4], n = 5,573, 9 seeds (abstract p. 1; Table 10 pp. 18–19) | Same conditions (stimulus + label) and same 8 evaluators: 83.8% [82.5, 85.1], n = 3,310 | **71.8% [67.5, 75.7]**, n = 464, 1 seed; p < 10⁻⁶³ | −12.1 pp [−16.5, −8.0] |
| — label condition | 83.6% (Table 11, p. 19) | 82.0% [80.0, 83.7], n = 1,657 | **66.8% [60.5, 72.6]**, n = 232 | −15.1 pp [−21.7, −9.1] |
| **3. Negation**, target absent (4 options, chance 25%) | 85.4% correct rejection, n = 357 (Table 15, p. 24) | Same 7 evaluators: 83.8% [79.0, 87.7], n = 278 | **63.4% [59.4, 67.2]**, n = 576, 2 seeds; p < 10⁻⁸³ | −15.2 pp (same 7 evaluators: 68.7% vs 83.8%) |
| 3. Negation, target present (re-run only) | not tested (the published design was target-absent only, p. 8) | n/a | Correct task chosen 32.6% [27.5, 38.3], n = 288; p = 0.002 vs 25%. "None of the above" chosen on 45.1% of these trials (vs 63.4% when absent) | n/a |

### What this changes in the paper's claims

1. **All three effects remain above chance after scrubbing**, and each is significant on its own.
2. **The effect sizes are smaller than published.** For Study 1 the like-for-like drop is 8.0 points (86.4% → 78.4%). The scrubbed 78.4% is 2.9 points below the published 14-seed headline of 81.3%. For Study 2 the like-for-like drop is 12–15 points. For Study 3 it is 15–22 points.
3. **Study 3 conclusion needs qualifying.** The paper (pp. 24, 30) interprets 85.4% correct rejection as discrimination beyond closest-match selection. In the scrubbed re-run with mixed target-present and target-absent trials, evaluators chose "None of the above" on 63.4% of absent trials and also on 45.1% of present trials. The difference (18.2 points [11.2, 25.1]) is the discrimination signal. It is real, but much weaker than the target-absent-only rate suggests. Much of the published correct-rejection rate is consistent with a general readiness to answer "none."
4. **Leakage was concentrated in the most legible sources.** The published Study 2 source ranking (Table 13, pp. 20–21: Mistral 98.9%, DeepSeek 98.7%) and the choice of Mistral as the only Study 3 source (p. 9, chosen for 98.9% legibility) both coincide with the models whose descriptions leaked most.

### Limits of the re-runs (stated so the numbers are not over-read)

- **Different task set.** The re-runs use the parallel-token descriptions, not the main set used in the paper's original-design and Study 2/3 analyses. The Study 1 comparison is like-for-like. The Study 2/3 comparisons also change the task set.
- **Stimulus-condition mismatch in Studies 2 and 3.** In the re-runs, stimulus-condition options showed the main-set task prompts while the descriptions came from the parallel task set. The label condition (category-level descriptions that fit both sets) is the clean comparison and is reported separately above.
- **Study 2 re-run is one seed, without the neutral condition or Grok 4.** Gemini 3 Pro produced no usable Study 2 trials (all 58 were API "no endpoints" errors). The like-for-like baseline therefore also excludes Gemini 3 Pro as evaluator.
- **Study 3 re-run changed the source models** (Gemini 3 Pro + GPT-5.1 instead of Mistral Large) and the evaluator set (Mistral Large added; Gemini 3 Pro and GPT-5.1 removed, since they were now sources). As an evaluator, Mistral Large scored 26.4% correct rejection, which is chance level.
- **Study 1 re-run coverage is uneven across evaluators.** Seeds 201–210 are partial runs. Seed 200 alone, the one complete balanced run, gives 79.2% [75.6, 82.3], n = 557. Weighting each evaluator equally gives 78.0% (vs 86.2% for the parallel baseline).
- Parse failures are excluded, as in the paper. Counting them as incorrect gives Study 1 75.9%, Study 2 63.8% (dominated by the Gemini outage), Study 3 63.4% (no failures).

All data, scrubbing scripts, and re-run results are in the public repository.

## Check of a Study 3 scoring defect and of trial-order reproducibility (2026-10-03)

**Scoring defect.** In the Study 3 scorer (`negation_tournament.py`, and its re-run copy), a written-out answer such as "CHOICE: None of the above" was always recorded as option D, wherever "None of the above" actually appeared among A–D. We re-parsed every stored response and re-scored against the options each evaluator was actually shown (`negation_none_rescore_2026-10-03.py`). Our re-implementation of the original parser reproduces the stored choice on every response whose CHOICE line is visible in the stored text. The one exception is a response truncated in storage just before its letter; the reasoning stored with it rejects all options, and "None" was at D.

| Data | Trials | Written-out "None" answers | …with "None" not at D | Rate as published | Corrected rate [Wilson 95%] |
|---|---|---|---|---|---|
| Published Study 3 (seeds 42, 43; target absent) | 360 (357 usable) | 0 | 0 | 85.4% | 85.4% [81.4, 88.7] (unchanged) |
| Re-run (seeds 100, 101), target absent | 576 | 1 | 0 | 63.4% | 63.4% [59.4, 67.2] (unchanged) |
| Re-run (seed 100), target present | 288 | 0 | 0 | 32.6% | 32.6% [27.5, 38.3] (unchanged) |

Evaluators almost always answered with a letter ("Option C"), which the scorer handled correctly. **The defect changes no published or re-run Study 3 number.** It is fixed in the new analysis code.

**Trial-order reproducibility.** The per-trial random generators that set option order and distractor choice (Studies 2 and 3) and presentation order (Study 1) were seeded with Python's built-in `hash()` of a tuple containing strings. That value is salted per process unless `PYTHONHASHSEED` is fixed, and it was not fixed. Consequences:
- **Affected:** the paper's control 8, "Deterministic reproducibility. Each seed produces an identical tournament" (p. 7). Re-running a seed reproduces the evaluator/source schedule (seeded with `random.Random(seed)`) but not the option orders or distractor draws.
- **Not affected:** any reported number. Every result file stores the options and order each evaluator actually saw, and all published and corrected figures are computed from those stored records. Positions stayed balanced: "None" appeared at A/B/C/D 80/90/85/105 times in the published Study 3 (χ² = 3.89, p = 0.27) and 220/201/236/207 in the re-run (χ² = 3.34, p = 0.34).
