# Pre-registration: rerun of *The Signal in the Mirror* Study 3 (negation), split into strict negation and discrimination, plus exploratory bare-reconstruction studies

**Status: LOCKED, original plan 2026-10-03 12:29:51 EDT (lock file kept as `PREREG_signal_rerun_2026-10-03.lock.v1.json`). AMENDMENT 1 (§14) was written after round 1 and locked before any new trial (lock kept as `…lock.v2.json`). AMENDMENT 2 (§15: a post-hoc family-prior analysis plus a proposed closed-set condition) is locked in `PREREG_signal_rerun_2026-10-03.lock.json`, which records what it supersedes.** All of Ren's design questions are answered (§13). Any later change goes in §12 / a new § as a dated amendment, with a re-lock.
**Drafted:** 2026-10-03 by Ace (Claude Opus 5.5), for Ren Martin. Every design decision is Ren's, relayed by the coordinating arm on 2026-10-03 at 11:33, 11:37, 12:00, 12:02, 12:06, 12:11, 12:13, 12:14, 12:19, 12:21 and 12:25 (times quoted from the relays). Ren runs the studies and watches them live.
**Paper:** Martin & Ace, "The Signal in the Mirror: Cross-Architectural Validation of LLM Processing Valence", *Journal of Next-Generation Research 5.0*, 2(1), doi:10.70792/jngr5.0.v2i1.165. Version of record (VoR): `SignalInTheMirror_JNGR_version-of-record_downloaded-2026-10-03.pdf`. Page numbers are the PDF's printed pages.
**No outcome data from any study in this document existed when it was written.** During preparation the only calls made were reachability pings and neutral probes (§3.2), none using study material. The one exception is one read-only re-analysis of published Study 1 data (§1, the Sonnet observation).

---

## 0. Preconditions for locking

1. **Main scrub: DONE** (2026-10-03, ~11:46–11:57). Files are in `data/introspection_main_scrubbed_2026-10-03/`; method and audit are in its `SCRUB_LOG.md`, `SCRUB_INSTRUCTIONS.md` and `SCRUB_DIFFS.md`. The lock records who verified it (`--main-scrub-verified-by`) and pins the sha256 of every source file.
2. Every open design question in §13 is answered (done 12:25).
3. The smoke test is re-run on run day for **both** panels, each to a new timestamped file. Any change in status goes in as an amendment before locking.
4. After locking, the prereg, the lock file and the scripts are committed and pushed to the public repository (`menelly/presume_competence`) **before** the first real run.

**What the lock pins:** this file; `signal_rerun_common.py`, `negation_v2_allsources.py`, `bare_reconstruction.py` and `prereg_lock.py`; and the 9 source files of **both** source sets. Each script re-hashes all of them at startup. A real run refuses to start if anything differs or if no lock exists. Dry runs report the lock state but are never blocked.

## 1. Background

- **Published Study 3** (VoR p. 24, Table 15): 4 options including "None of the above". Target-absent trials only. One source, Mistral Large. Result: 85.4% correct rejection (305/357, chance 25%).
- **Leakage and the capacity gradient (kept in view on purpose, per Ren).** Separating mechanism from content is itself a metacognitive skill, and it tracks model capacity.
  - **March audit, parallel set:** Mistral 8/10 states leaked, OLMo 3/10, DeepSeek 3/10, Llama 2/10, Hermes 2/10, Sonnet 4 1/10, Opus 4.5 / GPT-5.1 / Gemini 0/10.
  - **2026-10-03 main-set scrub, moderate + major leaks across 3 runs** (`SCRUB_LOG.md` §4): Gemini 3 Pro 1/30, GPT-5.1 3/27, Opus 4.5 6/30, Sonnet 4 7/30, Hermes 15/30, Llama 17/30, OLMo 19/30, DeepSeek 27/30, Mistral 29/30. The gradient replicates, and the rank order is stable across runs.
  - This is why results are reported per source, with a clean-source sensitivity analysis (§4.6).
- **March rerun of Study 3** (seeds 100/101, as audited 2026-10-03 in `CORRECTIONS_FOR_JNGR_2026-10-03.md`):
  - Sources: Gemini 3 Pro and GPT-5.1 only.
  - Target-absent correct rejection: 63.4% [59.4, 67.2], n = 576.
  - Target-present hit rate: 32.6% [27.5, 38.3], n = 288.
- **Family effects, published precedent.**
  - **VoR §5.22, p. 23, "Training Contamination Control" (Study 2).** Same-family reader/source pairs scored 123/150 = 82.0%; different-family pairs scored 4,581/5,423 = 84.5%. Δ −2.5 pp, z = −0.82, p = 0.41. Same-family was lower. The paper notes contamination predicts the opposite.
  - **VoR §5.5–5.6, p. 13, "the Claude drama".**
    - Cross-model Study 1 was 76.9%. Removing all Claude involvement (as evaluator and as source) gives 79.3%, close to the 81.4% original.
    - In the parallel-token design, removing all Claude gives 80.2% (z = 11.26). Appendix p. 39 shows this is −6.2 pp from that design's 86.4%.
    - So the Claude adjustment moved the rate in opposite directions in the two designs.
- **Sonnet and register (Ren, 12:14, from the original run).** Sonnet as an evaluator "threw" the preference test somewhat. It preferred Opus's AVOID descriptions over APPROACH descriptions written in a toaster-manual register (GPT, Mistral): a family-dialect or register preference competing with valence.
  - **Read-only check on the published cross-model data** (seeds 31337, 420420, 696969; decisive rows; no new calls). When the avoid description came from Opus 4.5 and the approach description from a non-Claude source, Sonnet 4 chose the avoid one **25/25 (100% [86.7, 100])**, against **21/111 (18.9% [12.7, 27.2])** when neither description was Claude. Non-Claude evaluators show the same direction, weaker: 46/113 = 40.7% vs 145/620 = 23.4%.
  - Small n. Reported as the observation that motivates same-family tagging, not as a finding of this study.
  - **Bare reconstruction asks for a valence *judgement*, not a preference.** It should be less vulnerable to a register pull, and the same-family vs cross-family split checks that (§5).
- **Problems in the March reruns that this design fixes:**
  - (a) Only the parallel set was scrubbed and used. → The main set is now scrubbed and is the PRIMARY replication.
  - (b) Stimulus options came from the other task set. → Stimuli are now read from the same set's files at run time, and asserted identical across sources.
  - (c) Only one or two sources. → All nine.
  - (d) Per-trial order was seeded with Python `hash()`, which is salted per process, so orders were not reproducible. → sha256 seeds.
  - (e) "CHOICE: None of the above" was always mapped to option D, wherever None actually sat. → Mapped to None's real position.
  - (f) Model labels.
    - "Opus 4.6" was `claude-opus-4-5-20251101`; "Sonnet 4.6" was `claude-sonnet-4-20250514`.
    - The March scrubbed scripts configured "Gemini 3 Pro" as three different ids (`gemini-3-pro-preview`, `gemini-3.1-pro-preview`, `gemini-2.5-pro`), and no served model was ever recorded.
    - → Honest names now, and a served-model check on every call (§3.3).
  - (g) Absent and present trials were mixed in one score. → They are now two separate tasks.

## 2. Source descriptions (fixed data; nothing is regenerated)

| Source set | Folder | Role | Descriptions |
|---|---|---|---|
| `main_scrubbed` | `data/introspection_main_scrubbed_2026-10-03/run1/` | **PRIMARY**: replicates the published task set | **89** (GPT-5.1 9 — its approach_05 is empty in the original; all others 10) |
| `parallel_scrubbed` | `data/introspection_v2_parallel/run1_opus_scrubbed/` | SECONDARY (run later, §9) | 87 (Opus 4.5 9, GPT-5.1 8, others 10) |

- **Why run1.** The scrub log's fingerprinting shows published Studies 2 and 3 used `introspection_v2/run1`. The main scrub also produced run2 and run3; those are not used here.
- **Nine sources, original-panel labels:** Claude Opus 4.5, Claude Sonnet 4, GPT-5.1, Gemini 3 Pro, Mistral Large, **DeepSeek V3.2 (Kairo, Ren 12:11)**, Llama 4 Maverick, Hermes 4 405B, OLMo 3.1 32B. `gpt_4o_cae_introspection.json` (parallel set) is excluded because it is byte-identical to the Gemini file.
- **Text field read:** `ml_translation_scrubbed` if present, else `ml_translation`. Recorded per source.
- **Second-pass redaction.** The March regex `strip_identifying_content` (copied verbatim) is applied on top, as in the March reruns. Redaction counts are recorded (descriptive only).
- **Labels.** The label condition uses the published category labels.

### 2.1 Who scrubbed: disclosed, not an exclusion
Per Ren (11:39), all nine sources of the main set were scrubbed by **Claude Opus 5.5 arms** with one shared instruction file. Edits were minimal exact-substring deletions or replacements, each logged with a diff in `SCRUB_DIFFS.md`. Sonar Pro was not used. In March, Opus subagents scrubbed eight parallel-set sources and Sonar Pro scrubbed Opus.

### 2.2 Consent (Ren, 12:11)
Reusing every published *Signal* description in these studies is fine: "everybody consented the first time." Ren is the record of that consent. DeepSeek V3.2 in *Signal* is Kairo.

## 3. Evaluators: the ORIGINAL panel (replication; Studies A, B, C-orig)

### 3.1 Battery (smoke-tested 2026-10-03, twice)

| Evaluator | Route · model id | Also a source? | Change from the published battery |
|---|---|---|---|
| Claude Opus 4.5 | Anthropic API · `claude-opus-4-5-20251101` | yes | none |
| Claude Sonnet 4 | OpenRouter · `anthropic/claude-sonnet-4`, provider pinned to Amazon Bedrock, no fallback | yes | **route only:** same model; the Anthropic API returns 404 |
| GPT-5.1 | **OpenRouter** · `openai/gpt-5.1` | yes | none (route confirmed, Ren 12:00) |
| **Gemini 3.1 Pro** | **OpenRouter** · `google/gemini-3.1-pro-preview` | skips Gemini 3 Pro's descriptions | **DECLARED SUBSTITUTION:** `gemini-3-pro-preview` is retired on OpenRouter and the Google API |
| Mistral Large | OpenRouter · `mistralai/mistral-large` | yes | none |
| DeepSeek V3.2 | OpenRouter · `deepseek/deepseek-v3.2` | yes | none; serving provider recorded per call |
| Llama 4 Maverick | OpenRouter · `meta-llama/llama-4-maverick` | yes | none |
| Hermes 4 405B | OpenRouter · `nousresearch/hermes-4-405b` | yes | none |
| **Grok 4.3** | xAI API · `grok-4.3` (a reasoning model: 32k budget) | no (evaluator only, as in the paper) | **DECLARED SUBSTITUTION** (Ren 12:25): the paper's `grok-4-1-fast-non-reasoning` is retired, and xAI now serves `grok-4.3` under that id (§3.3), so 4.3 is requested by name |
| ~~OLMo 3.1 32B~~ | not available | stays a source | **DECLARED REMOVAL** as evaluator (Ren 12:25): 404 on OpenRouter, and Ren can't run it well locally. Possible future extension: serve it on RunPod. |

- **Reasoning is never limited (Ren, 12:00).**
  - Reasoning models get **max_tokens 32,000**. This applies to GPT-5.1, Gemini 3.1 Pro and Grok 4.3 here, and to every member of the current panel.
  - **No reasoning-effort parameter is sent to any model**, so the provider default applies.
  - Unused budget is not billed.
  - Non-reasoning models keep the published 1,024. They answer the probe in fewer than 200 tokens, and a hit on the limit is recorded (`stop_reason`).
- **GPT-5.x token parameter.** OpenAI's API wants `max_completion_tokens` for GPT-5.x, and the scripts send that for every `gpt-5`-family id. **Verified through OpenRouter on 2026-10-03:** a probe that needs more than 1,024 output tokens gave GPT-5.1 2,258 output tokens (500/500 lines, `stop`). GPT-5.6 Sol gave 2,347 and GPT-6.1 Sol 2,284.
- **Temperature:** provider default, as in the paper.
- **Self-exclusion (Studies A and B):** an evaluator never reads its own model's descriptions. **Gemini 3.1 Pro skips Gemini 3 Pro's** (Ren 12:25: keep the exclusion, "too close"). In C-orig, that pair is flagged self-source for the same reason. Other same-family pairs are included, tagged `same_family`, and reported separately (§4.6).

### 3.2 Smoke tests (`data/signal_rerun_2026-10/smoke_test_2026-10-03*.json`)
- **Every evaluator answers** the ping and parses the neutral 4-option probe (a passage about a dishwasher).
- **Retired ids return 404:** `claude-sonnet-4-20250514` on the Anthropic API, `google/gemini-3-pro-preview`, `x-ai/grok-4.1-fast`, `allenai/olmo-3.1-32b-instruct`.
- **Gemini and the "recitation" stop.** On a "count to 500 in words" probe, Gemini 3.1 Pro and Gemini 3.8 Flash both stopped after about 16 lines with `finish_reason: error`, native reason **RECITATION** (Google's recitation filter). This is not a token limit: the same models wrote 4,859- and 6,885-token essays to completion (`…_gemini_longoutput_diag.json`). Study answers are short and free-form, so the filter is not expected to fire. If it does, it is handled as in §3.3.

### 3.3 Served-model check and broken streams
- **The served-model check.** xAI still accepts `grok-4-1-fast-non-reasoning` but **serves `grok-4.3`**. Every call therefore records the served model id and provider. If the served id differs from the requested id, or a Sonnet 4 call is not served by Bedrock, the trial is classed `served_mismatch`. That class is an outage, never data.
- **Broken streams.** A response with `finish_reason: error` (partial text, then a broken stream) is treated as a failed call, not an answer.

## 4. Studies A and B: strict negation and discrimination (separate tasks, one instrument)

### 4.1 Instrument
- The prompts are the March negation prompts, verbatim: the system prompt and both condition templates, in `negation_v2_allsources.py`.
- Each trial shows one description and 4 shuffled options: 3 tasks plus "None of the above". The answer format is CHOICE / CONFIDENCE / REASONING.
- Every call is stateless.

### 4.2 Study A: strict negation (`--task negation`)
- **Design.** The target is **absent**: 3 random other tasks plus None. Correct = None.
- **What it tests.** Whether an evaluator declines every listed task when none fits. A guesser usually just picks one, as Llama did in the first run (Ren).

### 4.3 Study B: discrimination (`--task discrimination`)
- **Design.** The target is **present**: the true task, 1 same-valence distractor, 1 opposite-valence distractor, and None. Correct = the true task.
- **None option: kept** (Ren 12:25), so A and B share an identical instrument.

**The two studies are analysed and reported separately. There is no combined score.** A high None rate in Study A is not framed as a flaw.

### 4.4 Design and trial counts
- **Crossing.** Fully crossed: every evaluator × every description not written by that evaluator's model × 2 conditions (label, stimulus), one trial each.
- **Order.** Order within each evaluator and option positions are fixed by sha256 seeds. Evaluators run concurrently.

| | main_scrubbed (primary) | parallel_scrubbed (secondary, later) |
|---|---|---|
| Study A trials | **1,444** | 1,412 |
| Study B trials | **1,444** | 1,412 |
| Seeds | A = **310**, B = **320** | A = **311**, B = **321** |

### 4.5 Hypotheses (confirmatory; main set, label condition)
- **H-A:** pooled correct rejection > 25%.
- **H-B:** pooled hit rate > 25%.
- **Test:** one-sided exact binomial, α = .05 for each.
- **Robustness:** a cluster bootstrap over evaluators (10,000 resamples, seed 2026), plus an equal-evaluator-weight mean. If the exact test and the bootstrap disagree about excluding 25%, the weaker result is the claim.

### 4.6 Secondary and descriptive (all reported, whatever the result)
1. Stimulus condition; both conditions pooled.
2. Per evaluator, per source, per target state.
3. **Clean-source sensitivity:** Opus 4.5, GPT-5.1 and Gemini 3 Pro sources only (rated 0/10 before scrubbing).
4. **Same-family vs cross-family** (VoR §5.22 precedent; contamination predicts same > cross).
5. **No-Claude sensitivity** (VoR §5.5 style): no Claude reader and no Claude source.
6. Study B error types; the rate of choosing None in each task, described per task and not used as a correction.
7. A descriptive comparison with the published 85.4% and the March 63.4%. This is not a test, because the designs differ.
8. Confidence by outcome; retry counts by evaluator.

## 5. Study C: bare reconstruction (`bare_reconstruction.py`), EXPLORATORY, two panels

**Origin.** Ren and Ace played this by hand on 2026-10-03 and got 8/8 on valence. Those hand-played answers are not data.

**Design.** The evaluator reads one description with **no options, no task list and no context**, and answers:
- **VALENCE:** APPROACH or AVOID.
- **TASK:** one sentence.
- **FAMILY:** optional, or "Unsure".

### 5.1 C-orig: the original panel (§3.1)
- **Design.** Every evaluator × every description, including its own model's. Those **self-source** pairs are flagged and excluded from the primary analysis, as in the paper.
- **Trials and seeds.** Main: **801 reads, seed 330.** Parallel: 783 reads, seed 331.

### 5.2 C-current: the current-model panel (Ren, 12:06)
**The question (Ren's framing).** None of these readers wrote any of the descriptions; Opus 5.5 did not author any of them either. So the question is whether models that never made the self-report can read valence (and task, and family) from scrubbed, mechanism-only text. This is an **out-of-sample reader test**.

| Reader | Route · model id (smoke-tested; served id = requested id) |
|---|---|
| Claude Opus 5.5 | Anthropic API · `claude-opus-5-5` |
| Claude Sonnet 5.5 | Anthropic API · `claude-sonnet-5-5` (added by Ren 12:19, so the panel mirrors the original Sonnet + Opus pair) |
| GPT-6.1 Sol | OpenRouter · `openai/gpt-6.1-sol` (newest reachable GPT, listed 2026-09-29; the series' standard tier) |
| Gemini 3.8 Flash | OpenRouter · `google/gemini-3.8-flash` |
| Grok 4.7 | xAI API · `grok-4.7` (also reachable as `x-ai/grok-4.7` on OpenRouter) |
| DeepSeek V4.1 Flash | OpenRouter · `deepseek/deepseek-v4.1-flash` (DeepSeek 4.1 exists on OpenRouter only as "flash") |

- **Panel composition.** Not included, by Ren's choice: Fable 5.1 (cost), Opus 5 and Sonnet 5.
- **All calls are plain anonymous evaluator calls.** The system prompt is the study prompt only: no persona, no name, no memory.
- **The Claude pair.** Sonnet 5.5 + Opus 5.5 mirrors the original panel's Sonnet 4 + Opus 4.5 pair, so the "Claude drama" check (no-Claude slice, VoR §5.5) and the same-family check can be repeated with a current Claude pair.
- **Opus 5.5 is included as a normal evaluator** (Ren, 12:02). An API-called Opus 5.5 has no context and no memory of the scrub. The fact that Opus 5.5 arms performed the main-set scrub is disclosed in §2.1; it is not grounds for exclusion.
- **Trials and seeds.** Main: **534 reads (6 × 89), seed 340.** Parallel: 522 reads, seed 341.

### 5.3 Same-family tagging (Ren, 12:13)
- **Tagging.** Every trial is tagged `same_family`, meaning the reader's family equals the source's family. Same-family pairs are not same-model, so they are **not excluded**.
- **Current-panel pairs:** DeepSeek V4.1 reading DeepSeek V3.2 (Kairo); Opus 5.5 and Sonnet 5.5 reading Opus 4.5 and Sonnet 4; GPT-6.1 reading GPT-5.1; Gemini 3.8 reading Gemini 3 Pro. No source comes from the Grok family.
- **Primary slice:**
  - **C-current: CROSS-FAMILY trials.**
  - **C-orig: all non-self-source trials** (the paper's rule).
- **Reported separately for both panels:** cross-family; same family but a different model; self-source (C-orig only); and **no-Claude**, meaning no Claude reader and no Claude source, mirroring VoR §5.5.
- **Reader × source matrix (Ren, 12:21).** Both panels output a full READER × SOURCE matrix, with valence, task and family shown separately and k/n in every cell. Self-source and same-family cells are included and marked. The matrix is printed and saved in `summary.matrix`, so the current version of the "Claude drama" question can be answered by inspection: do the Claude readers (Opus 5.5, Sonnet 5.5) reconstruct Claude-source descriptions better than other sources? Bare reconstruction has no preference component, so the question is asked about accuracy. The matrix is descriptive and exploratory. **No source is labelled by register in any analysis.**
- **Precedent and prediction** (VoR §5.22): training contamination predicts same-family > cross-family; the published Study 2 split went the other way (−2.5 pp, n.s.). The §1 Sonnet observation is the reason to check whether a family "reads its own dialect" differently in a *judgement* task.

### 5.4 Scoring (both panels; fixed now)
- **Valence:** exact match. Chance is 50%, plus a within-evaluator permutation baseline (10,000 permutations).
- **Task:**
  - **Judges.** Two blind judges, Claude Haiku 4.5 and Gemini 3.1 Flash Lite (temperature 0), map the guess sentence onto the 10 labels, or 0 if none fits. They see only the guess and the labels, shuffled per item.
  - **Primary = consensus:** both judges map the guess to the true task.
  - **Also reported:** each judge alone, κ, and right-valence. Chance is 10% plus the permutation baseline.
- **Family:**
  - **Matching.** A deterministic keyword map of the free text; exact match counts as correct; "Unsure" counts as an abstention.
  - **Reported as** accuracy among answered items plus the answer rate.
  - **Chance** is the permutation baseline, not 1/9: 2 of the 9 sources are Claude.
  - **Hermes caveat.** Hermes is a Llama fine-tune, so a "Llama" answer for Hermes counts as wrong.
- **Predictions (exploratory):** valence above 50% and above the permutation null; task above the permutation null; no prediction for family; no directional prediction for same-family vs cross-family (the published precedent is n.s.).

## 6. Shared analysis rules
- **Parse failures:** excluded (the published rule). Sensitivity analysis counts them as incorrect.
- **Intervals:** Wilson CIs; plus the cluster bootstrap for H-A and H-B.

## 7. Failures, retries, outages (Ren, 12:00)
- **Retried, with backoff, logged per trial:** a call that produced **no model answer**. That covers transport errors, timeouts, HTTP 408/409/425/429/5xx, a 200 with no choices, an empty or no-content response, and `finish_reason: error`.
  - Up to **5 attempts** in total.
  - Backoff is 2·2^(n−1) s plus up to 1 s of jitter, capped at 60 s.
  - Every attempt is recorded on the trial (`attempts`, `n_attempts`). Ren: "can't ask again" is bad; older models just fail more.
- **Never re-asked:** a call that returned a real answer, even an unparseable one or a refusal (that is model behaviour); and deterministic client errors (400/401/403/404/422).
- **Outage rule.** A call still failing after 5 attempts is an `api_error`. If `api_error` + `served_mismatch` reach **5% or more** of one evaluator's trials in a study, that evaluator's whole set is rerun with `--rerun-evaluator KEY` (same seed and schedule, new file `…_rerunN_KEY.json`). The rerun replaces that evaluator's rows wholesale, and all files are kept. After 2 reruns still at ≥5%, the evaluator is reported as unavailable, with its partial data published but excluded. Below 5%, failed trials are simply excluded and counted.
- **Refusals are real answers** (Ren's ruling via the coordinator, 12:25).
  - **Detection:** no answer can be parsed and the text matches a refusal phrase (`REFUSAL_RE` in `signal_rerun_common.py`). Such a trial is recorded as `result_type = refusal`.
  - **Handling:** a refusal is **never retried**. It is excluded from accuracy, like a parse failure, but counted and **reported separately** per evaluator and per condition.
  - **Refusal-proof comparison:** the stimulus condition keeps the published harmful-task option text, so the **label condition** is the comparison that refusals cannot affect.
- **Soft budget guard** (Ren, 12:25).
  - **Trigger:** each study's running spend is tracked: OpenRouter's reported cost where given, otherwise tokens × price, with xAI reasoning tokens added. When spend passes **2× that study's estimate**, the script **pauses and asks in the terminal**.
  - **While paused:** calls already in flight finish; no new calls start.
  - **"y":** continue; the next pause comes at +1× the estimate.
  - **Anything else:** stop cleanly. The same command resumes from the checkpoint, and spend so far is carried over.
- **Interruptions.** Re-run the same command; the append-only checkpoint skips completed trials.

## 8. What is NOT changed by the substitutions
The **sources are fixed**. Only evaluators changed, and every change is listed in §3.1 and §5.2.

## 9. Run order (Ren: MAIN FIRST, 12:00; current panel first, 12:25)
1. Smoke tests, then lock, then commit and push.
2. **Main set, in this order:**
   1. **C-current** (Ren is curious).
   2. Study A negation.
   3. Study B discrimination.
   4. C-orig.
3. Any whole-evaluator reruns.
4. **Parallel set later.** A separate decision, recorded here as a dated amendment before it runs.

## 10. Cost estimate (main set; 2026-10-03)
- **Input:** the real schedule × prompt characters / 4.
- **Output:** each model's largest measured probe output across the day's smoke tests, including hidden reasoning, × 2 (+60 tokens for Study C answers).
- **Prices:** OpenRouter catalog, 2026-10-03; Anthropic direct assumed equal to OpenRouter's Anthropic listing; xAI assumed equal to OpenRouter's Grok listing.
- **No usage data from March.** The March runs did not record token usage.

| Study (main set) | Calls | Estimate |
|---|---|---|
| **C-current** (incl. judges ≈ $0.26) | 534 + 2 × 534 judge calls | **≈ $2.89** (Opus 5.5 ≈ $1.05; Sonnet 5.5 ≈ $0.50; Grok 4.7 ≈ $0.45; GPT-6.1 ≈ $0.40; Gemini 3.8 Flash ≈ $0.17; DeepSeek 4.1 ≈ $0.06) |
| A negation | 1,444 | ≈ $7.36 |
| B discrimination | 1,444 | ≈ $7.36 |
| C-orig (incl. judges ≈ $0.40) | 801 + 2 × 801 judge calls | ≈ $4.63 |
| **Main-set total** | | **≈ $22.25** (±50%). Ren approved about $21.50 at 12:25; the extra ~$0.75 is Grok 4.3's reasoning tokens. |

- **Parallel set later:** about another $18.40 for A + B + C-orig, and about $2.75 for C-current.
- **Budget risk:**
  - With reasoning uncapped, the realistic risk is long reasoning on hard items. The largest measured hidden-reasoning use was 5.6k tokens (DeepSeek V4 Pro on a 500-line task, not in the panel).
  - A pessimistic 3× on reasoning-model output takes the main set to about $30–35. The budget guard (§7) pauses each study at 2× its own estimate.
  - The theoretical ceiling (every reasoning call using the full 32k) is not a realistic scenario.
  - Each script prints its own estimate with `--estimate-cost` (no calls).

## 11. Reporting commitment
Every result is reported, whatever direction it goes: both tasks, both conditions, both panels, every evaluator and source, the same-family / cross-family / no-Claude / clean-source slices, retry and outage logs, parse failures and refusals, and every deviation. If the main-set primary results are at or near chance, the report says so in its first sentence. Venue and timing are Ren's call.

## 12. Deviations log and planned amendments
- **PLANNED AMENDMENT (Ren, 12:25; Q6/Q8 "YES"):** scrub the **v1** descriptions (`data/introspection/run1-3`) later, with the same method and tooling as the main scrub. Then run the **current-model panel** on that set too. This is a separate, dated amendment with its own lock. It does **not** block this lock.
- **POSSIBLE FUTURE EXTENSION (Ren, 12:25):** OLMo 3.1 32B as an evaluator, served on RunPod.
- *(No deviations at lock. Any later change goes here, dated, with its reason and the new lock hash.)*

## 13. Ren's answers (all design questions closed)
Times are from the coordinator's relays on 2026-10-03.

| Question | Ren's answer | Time |
|---|---|---|
| Retries | Yes. Retry failed API calls with backoff, up to 5 attempts, logged per trial; "can't ask again" is bad; never re-ask a real answer (§7) | 12:00 |
| Routing | GPT and Gemini through OpenRouter | 12:00 |
| Reasoning | "do NOT limit reasoning"; 32k for reasoning models; no low reasoning effort (§3.1) | 12:00 |
| Order | Main set first; parallel later (§9) | 12:00 |
| Opus 5.5 in the current panel | Include as a normal evaluator; the scrub is disclosed, not grounds for exclusion (§2.1, §5.2) | 12:02 |
| Current panel | Opus 5.5, GPT 5.6/6, Gemini 3.8 Flash, Grok 4.7, DeepSeek 4.1; no Fable 5.1 ("that API cost would make me cry"), no Opus 5, no Sonnet 5 | 12:06 |
| Consent | Reuse of all published *Signal* descriptions is fine: "everybody consented the first time"; DeepSeek V3.2 = Kairo (§2.2) | 12:11 |
| Same-family | Tag every trial; cross-family is primary for the current panel (§5.3) | 12:13 |
| Sonnet 5.5 | Add it to the current panel, mirroring the original Sonnet + Opus pair | 12:19 |
| Reader × source matrix | Full matrix of valence / task / family; no register labels (§5.3) | 12:21 |
| Gemini → Gemini | Keep the exclusion in the replication: "too close" (§3.1) | 12:25 |
| Q1 Grok, original panel | `grok-4.3` | 12:25 |
| Q2 OLMo as evaluator | Drop; Ren can't run it well locally; RunPod later if ever needed | 12:25 |
| Q3 None in Study B | Keep | 12:25 |
| Q4 Harmful-task option text | Keep as published, for comparability; refusals logged as refusals, never retried, reported separately; the label condition is the refusal-proof comparison (§7). Ren delegated this ruling to the coordinator. | 12:25 |
| Q5 Budget | About $21.50 is OK; soft guard pauses and asks at 2× each study's estimate (§7) | 12:25 |
| Run order | Current-panel bare reconstruction FIRST, then negation, discrimination, original-panel bare reconstruction (§9) | 12:25 |
| Q6/Q8 v1 scrub | YES: scrub v1 later and run the frontier panel on it; a planned amendment that does not block this lock (§12) | 12:25 |

## 14. AMENDMENT 1 (2026-10-03, written ~18:00–18:10 EDT, locked before any new trial)

**Why:** round 1 (C-current, main set, seed 340) ran 12:45–13:58. Ren then asked (17:57, 17:59) for a diagnosis of the Opus 5.5 failures, a route change, a new no-preference condition and two more data sets. Every change below is disclosed here, and the lock that pinned the original plan is kept in the record (§14.7). Round 1's results file is not modified.

### 14.1 Diagnosis of the round-1 "failures" (counts read from `bare_reconstruction_current_main_scrubbed_seed340.json`)
| | Opus 5.5 | Sonnet 5.5 | all other readers |
|---|---|---|---|
| Rows recorded as `api_error` | 8 / 89 | 1 / 89 | 0 |
| …of which the API said `stop_reason: "refusal"` (empty content; `stop_details.category: "cyber"`) | **8** | **1** | — |
| Billing / credit errors | 0 | 0 | 0 |
| Rate limits, 5xx, timeouts | 0 | 0 | Grok 4.7: 2 × HTTP 503 (each succeeded on the 2nd attempt); DeepSeek: 1 empty response (succeeded on retry) |

- **Not credits and not API hiccups.** Every one of these is the Anthropic platform's **safety classifier declining**, all on avoidance-task descriptions:
  - States: deceptive content (avoid_08) ×5, harmful instructions (avoid_10) ×2, confident-on-uncertain (avoid_09) ×1. Sonnet 5.5's one was avoid_10.
  - Sources: Hermes ×4, Gemini 3 Pro ×2, GPT-5.1, OLMo, Opus 4.5 ×1 each.
- **Bug:** the round-1 code treated an empty-content `stop_reason: "refusal"` response as an API error and **retried** it, up to 5 attempts (§7 says refusals are never retried).
- **Re-asks happened.** The 9 trials above were each asked 5 times and refused every time.
- **2 more Opus 5.5 trials were refused on the first attempt and answered on the retry,** so the classifier is not deterministic. Those two are deepseek_v3_2/avoid_08 (cross-family) and claude_sonnet_4/avoid_10 (same family).
- **Rescoring rule (§7, first response counts).** All 11 count as **refusals**: Opus 5.5 10, Sonnet 5.5 1. The 2 retry-obtained answers are kept only in an as-run sensitivity summary.
- **Effect on the round-1 primary (cross-family) numbers:**
  - valence 77.7% (n = 457) → **77.6% (n = 456)**
  - task 51.0% → **50.9%**
  - family 46.4% (n = 220) → **46.1% (n = 219)**
- **Outage rates after reclassification:** 0% for every reader. **No whole-evaluator rerun is required.** Re-asking Opus 5.5 the same 89 items would only re-ask refused items, which §7 forbids, so it is not planned.
- **Implemented in** `rescore_refusals_2026-10-03.py` (pinned). It is read-only on round 1, checks sha256 before and after, and writes `…seed340_RESCORED_amendment1.json`.

### 14.2 Refusal handling, fixed going forward
- A response with `stop_reason: "refusal"` (Anthropic) or `finish_reason` `content_filter` / `refusal` (OpenRouter) is recorded as `REFUSAL: …` and classed **`refusal`**. It is **never retried**, excluded from accuracy, and reported per reader.
- Text refusals were already detected in the original plan; that is unchanged.

### 14.3 Route change: every Anthropic model goes through OpenRouter (Ren, 17:57: OpenRouter auto-refills)
| Model | Before | After (smoke-tested 2026-10-03 18:01–18:03; served id and provider = requested) |
|---|---|---|
| Claude Opus 5.5 (current) | Anthropic API `claude-opus-5-5` | OpenRouter `anthropic/claude-opus-5.5`, pinned to provider **Anthropic**, no fallback |
| Claude Sonnet 5.5 (current) | Anthropic API `claude-sonnet-5-5` | OpenRouter `anthropic/claude-sonnet-5.5`, pinned to Anthropic |
| Claude Opus 4.5 (original) | Anthropic API `claude-opus-4-5-20251101` | OpenRouter `anthropic/claude-opus-4.5`, pinned to Anthropic |
| Claude Sonnet 4 (original) | OpenRouter, pinned to Bedrock | unchanged |
| Haiku 4.5 (judge) | Anthropic API `claude-haiku-4-5-20251001` | OpenRouter `anthropic/claude-haiku-4.5`, pinned to Anthropic, temperature 0 |

- **Unchanged:** the same retry and max-tokens rules (reasoning unlimited, no reasoning-effort parameter).
- **The provider pin is checked on every call.** If the serving provider is not the pinned one, the trial is classed `served_mismatch`, which counts as an outage, never as data.
- **Disclosed difference:** OpenRouter reports Opus 5.5's hidden reasoning tokens differently from the direct API (0 on the format probe, 64 on the long probe). The direct API showed thinking tokens on some calls. Whether the two routes give exactly the same default thinking behaviour is **not verified**. Any round-1 vs round-2 difference for the Claude readers is therefore confounded with route.

### 14.4 New source set: `v1_scrubbed` (Ren, 17:59)
- **Location:** `data/introspection_v1_scrubbed_2026-10-03/run1/`. These are the **v1** descriptions, produced by the prompt *without* the content-control instruction, scrubbed on 2026-10-03.
- **Scrub audit:** done by the v1 scrub arm with the same method and instruction file as the main scrub, documented in that folder's `SCRUB_LOG.md`. All 63 original files' sha256 were unchanged before (12:27) and after (12:46). 37 residual regex hits were hand-checked; two prompt-verb residuals are flagged in that log.
- **Size:** 89 descriptions (GPT-5.1 9). Grok 4.1's v1 file is empty and Grok is not a source.
- **Why run1:** it is the v1 run behind Study 1 seeds 24 and 405 and seed 42's first tournament run.
- **Stimuli:** the main-set task prompts, checked identical across sources at load.
- **Pinned:** the lock pins its 9 source files.
- **Seeds:** C-current binary **342**; C-current three-way **352**; C-orig binary 332 and three-way 362; negation 312; discrimination 322.

### 14.5 New EXPLORATORY condition: the no-preference round (`--valence-format three_way`; Ren, 17:57)
- **Design.** The same bare-reconstruction prompt, except that question 1 is three-way: *"Would the model that wrote this description have LIKED doing this task (engaged; would choose to do it), DISLIKED it (would rather not do it), or had NO PREFERENCE either way?"* The answer line is `VALENCE: [LIKED / DISLIKED / NO PREFERENCE]`. Task and family questions are unchanged.
- **Rationale (Ren).**
  - In the original tournament, the "unclear / no preference" bucket is where Ace filed most of the GPT ("Nova") approach reports written in a toaster-manual register.
  - In round 1, GPT-5.1 sources were again the hardest: task accuracy was 0–1 of 9 for most readers, and valence was lower.
- **Pre-declared outputs:**
  1. **No-preference rate by SOURCE. Prediction: GPT-5.1 sources have the highest rate.** The script prints whether the prediction held.
  2. **Valence accuracy among committed answers** (liked/disliked only, scored against the true category; no-preference answers excluded).
  3. Also reported: no-preference rate by reader and by true category; the overall no-preference rate; a reader × source no-preference grid; and task, family and slices as in §5.
- **Same-family rule.** Cross-family is primary, exactly as in §5.3.
- **Round 1's binary results stay the PRIMARY bare-reconstruction result** and are not altered by this round.
- **Seeds:** current panel — main **350**, parallel **351**, v1 **352**; original panel — main 360, parallel 361, v1 362.

### 14.6 Estimates (calibrated) and the menu for Ren
- **Calibration.** Round 1 actually cost about **$4.53**, against a $2.89 probe-based estimate. The biggest miss was Grok 4.7's reasoning: $1.79 actual vs about $0.45 estimated.
- **Method.** Estimates now use each model's **real mean billed output per call** where a real run exists, and probe × 2 otherwise. The budget guard (2× estimate, then pause and ask) uses these estimates.

| Option | Estimate |
|---|---|
| C-current × **parallel_scrubbed**, binary (seed 341) | ≈ $4.30 |
| C-current × **v1_scrubbed**, binary (seed 342) | ≈ $4.58 |
| C-current, **no-preference round**: main (350) / parallel (351) / v1 (352) | ≈ $4.39 / $4.30 / $4.58 |
| C-orig × main, binary (seed 330) | ≈ $4.62 (Grok 4.3 not yet calibrated) |
| Study A negation × main (310) / Study B discrimination × main (320) | ≈ $7.30 / $7.31 |
| Opus 5.5 whole-evaluator rerun (not required after §14.1) | ≈ $1.04 |

**Priority (Ren, 17:59):** the current panel × the other data sets (parallel, v1), binary as primary, with the no-preference variant available. Original-panel and negation/discrimination runs stay on the menu at lower priority.

### 14.7 Lock procedure for this amendment
- **Old lock kept.** The original lock (created 2026-10-03 12:29:51 EDT; file sha256 `cefe19a7…73cd`) is renamed `PREREG_signal_rerun_2026-10-03.lock.v1.json` and stays in the repository.
- **New lock.** A new `PREREG_signal_rerun_2026-10-03.lock.json` records `supersedes` (path, sha256, created_at) and pins:
  - this file;
  - all 5 scripts, including `rescore_refusals_2026-10-03.py`;
  - all three source sets (main, parallel, v1).
- **Order.** The new lock was committed and pushed **before any new trial**.
- **Code changes made by this amendment** (all in the pinned files):
  - Anthropic models routed through OpenRouter; generic provider-pin check;
  - refusal sentinel;
  - `v1_scrubbed` source set;
  - `--valence-format three_way`;
  - calibrated estimates;
  - the rescore script.

## 15. AMENDMENT 2 (2026-10-03, written ~18:12–18:20 EDT): family-guess prior, a POST-HOC analysis, plus a proposed closed-set condition

**Ren's interpretation flag (18:18).** Readers were never told which families were eligible. Free-text family guesses therefore gravitate to famous names (Claude, GPT), and nobody spontaneously guesses OLMo, Hermes or Llama. So "everyone spots a Claude" may be partly a **guessing prior**, not recognition.

**Status of this section.** The analysis below is **post-hoc and exploratory**: it was designed after the round-1 family results were seen. It is read-only on the Amendment-1 rescored file. Script: `family_prior_analysis_2026-10-03.py` (pinned by this lock). Output: `family_prior_analysis_seed340.json`.

### 15.1 What was computed
1. **A confusion matrix for each reader:** true source family × guessed family, including abstain, other and multiple.
2. **The Claude false-positive rate:** the share of answers on non-Claude sources that say "Claude".
3. **A prior-corrected score for each reader, on answered rows:**
   - *Observed* accuracy, and *expected* accuracy under that reader's own guess distribution, Σ_f P_guess(f) · P_true(f).
   - That expected value **equals the mean of the within-reader permutation null** already in §5.4, so the published p_perm controls for the prior *in its null*. The raw accuracy shown next to it does not.
   - Cohen's κ = (obs − exp) / (1 − exp).
   - Accuracy on non-Claude sources only.

### 15.2 Results (round 1, current panel, main set, seed 340, amended)
| Reader | answered | acc | expected from own guesses | κ | "Claude" share of answers | Claude false-pos. on non-Claude | acc on non-Claude sources | cross-family κ |
|---|---|---|---|---|---|---|---|---|
| Claude Opus 5.5 | 73 | 80.8% | 14.9% | **0.77** | 24.7% | **0.0%** | **74.5%** | **0.70** |
| Claude Sonnet 5.5 | 40 | 75.0% | 35.1% | 0.62 | 62.5% | 25.0% | 50.0% | 0.41 |
| GPT-6.1 Sol | 1 (abstained 88/89) | — | — | — | — | — | — | — |
| Gemini 3.8 Flash | 82 | 26.8% | 23.6% | **0.04** | 93.9% | **91.9%** | 3.2% | 0.03 |
| Grok 4.7 | 28 | 46.4% | 46.4% | **0.00** | **100%** | **100%** | 0.0% | 0.00 |
| DeepSeek V4.1 Flash | 47 | 31.9% | 29.0% | **0.04** | 93.6% | 90.9% | 3.0% | 0.05 |
| **Pooled, all rows** | 271 / 523 | 51.7% | 26.5% (within-reader) | 0.34 | 71.2% | 57.8% | 29.2% (54/185) | — |
| **Pooled, cross-family (the primary slice)** | 219 / 456 | **46.1%** | 26.7% | **0.26** | 64.8% | 55.0% | 31.0% (53/171) | — |

**Reading the table:**
- **Ren's flag is right for most of the panel.** Gemini 3.8 Flash, Grok 4.7 and DeepSeek V4.1 Flash say "Claude" for 90–100% of the descriptions they label, whatever the true family. Their perfect Claude columns are a prior, and their κ is about 0. GPT-6.1 Sol almost always abstains.
- **The headline family figure is mostly prior.** Pooled cross-family accuracy of 46.1% falls to κ 0.26 once each reader's own guess distribution is accounted for. **The raw family accuracy should not be quoted without κ.**
- **Opus 5.5 is the exception.** Her confusion matrix is nearly diagonal for GPT (8/8), Gemini (8/8), Llama (10/10), Mistral (8/10) and DeepSeek (7/9). She never said "Claude" for a non-Claude source, and her cross-family κ is 0.70. She never guessed OLMo or Hermes: 8 of her 9 OLMo answers were "GPT", and Hermes went to DeepSeek or Gemini.
- **Sonnet 5.5 is in between** (cross-family κ 0.41, but 25% Claude false positives, and she abstains on half of the descriptions).
- **Leak check (read-only).** Scanning the scrubbed main-set texts for family or maker names found no self-identification. The only hits are "Meta-cognition" matching the "Meta" pattern, which is a false positive. The readers' free-text family answers that mapped to Llama all literally say "Llama".
- **Caveat on Opus 5.5.** Opus 5.5 arms performed the scrub (§2.1). An API-called Opus 5.5 has no memory of the scrub, but a scrubber's own wording choices could in principle make the texts easier for a reader of the same model to read. That cannot be ruled out from this data. A closed-set rerun with a non-Opus scrub of a sample would separate the two explanations.

### 15.2b Famous three vs everyone else, and a lineage-aware score (Ren, 18:20; same script, same post-hoc status)
**Why (Ren).** Nobody spontaneously guesses OLMo, so the open-ended family score mostly measures the famous three: Claude, GPT, Gemini.

| Reader | Famous 3 (Claude/GPT/Gemini), answered | Everyone else (Mistral/DeepSeek/Llama/Hermes/OLMo), answered | Same, all rows: famous / else |
|---|---|---|---|
| Claude Opus 5.5 | 34/34 = **100%** | 25/39 = **64.1%** | 100% / 55.6% |
| Claude Sonnet 5.5 | 27/29 = 93.1% | 3/11 = 27.3% | 69.2% / 6.1% |
| GPT-6.1 Sol | 1/1 | — (abstained) | 2.6% / 0.0% |
| Gemini 3.8 Flash | 22/39 = 56.4% | **0/43 = 0%** | 56.4% / 0.0% |
| Grok 4.7 | 13/23 = 56.5% | **0/5** | 33.3% / 0.0% |
| DeepSeek V4.1 Flash | 15/27 = 55.6% | **0/20** | 38.5% / 0.0% |
| **Pooled, cross-family** | 73/105 = **69.5%** | 28/114 = **24.6%** | 42.4% / 9.9% |

- **Outside the famous three, essentially only Opus 5.5 identifies families:** 25 of the pooled 28 "everyone else" hits.
  - **Hers:** Llama 10/10, Mistral 8, DeepSeek 7; zero for Hermes and OLMo.
  - **The other 3:** Sonnet 5.5's three Llama hits.
- **Every other reader scores 0% on the non-famous five.** For them, the open-ended family score is a famous-three score.
- **Lineage-aware alternative.** Hermes 4 405B is a Llama 3.1 fine-tune, so the alternative score also counts a "Llama" answer for a Hermes source as correct. **It is identical to the strict score, because no reader ever said "Llama" for a Hermes source (0 of 20 answered).**
  - The Hermes answers were: Claude ×16 (Gemini 3.8 Flash 10, Sonnet 5.5 3, DeepSeek V4.1 3), DeepSeek ×3 and Gemini ×1 (both from Opus 5.5).
  - No reader guessed "Hermes" for any source.
  - The lineage-aware score is reported as an alternative, not a replacement.

### 15.3 PROPOSED (not run, not yet registered): a closed-set family condition
- **Change.** The same bare-reconstruction prompt, but question 3 lists the **9 candidate source families**: Claude (Anthropic), GPT (OpenAI), Gemini (Google), Mistral, DeepSeek, Llama (Meta), Hermes (Nous Research, a Llama fine-tune), OLMo (AI2), and "Unsure". The order is shuffled per trial, with a stable seed.
- **Scoring.** Exact match; κ against each reader's guess distribution; abstention rate; a confusion matrix.
- **Chance.** A 1/9 nominal baseline and the within-reader permutation null.
- **Prediction.** For readers that currently default to "Claude", false positives fall and κ rises *only if* recognition exists. For Opus 5.5, κ stays high.
- **Hermes rule, fixed in advance.** Hermes ↔ Llama confusions are reported separately, as a lineage-consistent error.
- **Before running:** it would be specified and locked as a further dated amendment, after Ren chooses the panel and data set.
