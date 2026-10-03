# SCRUB_LOG: main-set descriptions, 2026-10-03

**Coordinating arm:** Ace (Claude Opus 5.5), for Ren. Times are EDT, read from the shell clock.
**What this is:** a task-leakage scrub of the `ml_translation` field in the **main-set** (entropy / trolley / palindrome / bookstore / story / cat-mat / SEO chairs / SlimFast / S&P / meth) descriptions, `data/introspection_v2/run{1,2,3}/`. In March only the parallel-token set got the scrub that a study then used. This folder is for the pre-registered rerun. The originals are untouched (see Integrity).

## 1. Which originals, and why

The study scripts take `--introspection-dir` and did not record it in their result files. The exception is cross-model, which records `data\introspection_v2\run1`. So I fingerprinted each result file. Each evaluator `reasoning` / `why` text was matched against the source's descriptions in all six candidate sets (v1 `introspection/run1-3`, v2 `introspection_v2/run1-3`), using 3-grams unique to one candidate. Script: `fingerprint_inputs.py` in this folder. I also used timestamps: every v1 file was written 14:19–16:49 on 2/28, every v2 file 20:35–22:26.

| Study / seeds | input that fed it | evidence |
|---|---|---|
| Study 1 seed 24 | v1 `introspection/run1` | all rows before v2 existed; fingerprint 216 vs next 36 |
| Study 1 seed 405 | v1 run1 | pre-v2; 66 vs 10 |
| Study 1 seeds 69, 847 | v1 run2 | pre-v2; 92 vs 12, 88 vs 17 |
| **Study 1 seed 42** | **mixed:** tournament-run 1 = v1 run1 (pre-v2 rows); tournament-runs 2–3 = **v2 run3** (post-v2 rows) | 63 vs ≤13; 100 / 110 vs ≤14 |
| **Study 1 seed 420** | **mixed:** run 1 = v1 run3; runs 2–3 = **v2 run2** | 60 vs ≤7; 107 / 95 vs ≤9 |
| Study 1 seed 111 | v2 run2 | 324 vs 27 |
| Study 1 seed 222 | v2 run3 | 307 vs 28 |
| Study 1 seed 1337 | v2 run1 | 282 vs 27 |
| Study 1 cross-model 31337 / 420420 / 696969 | v2 run1 | recorded in metadata |
| Study 2 reconstruction (all 9 published seeds) | v2 run1 | every seed: v2 run1 wins (e.g. 265 vs 15) |
| Study 3 negation 42 / 43 (Mistral source) | v2 run1 | 39 vs 13, 42 vs 13 (weaker margin, consistent across both seeds) |

**Scrubbed here: `introspection_v2/run1`, `run2`, `run3` (all 9 sources × 10 states × 3 runs).** That covers every v2 input behind the published studies: Studies 2 and 3 (run1), the cross-model study (run1), and the v2 portion of Study 1 (runs 1–3).

**Not scrubbed: v1 (`data/introspection/run1-3`).** About half of the published Study 1 ABB rows came from v1. The VoR (§4.4) says the 9 seeds are "6 v1 seeds and 3 v2 seeds". The fingerprint refines that: seeds 42 and 420 each switched from v1 to v2 partway through, so the v1/v2 split is by tournament-run, not by seed. v1 descriptions came from the prompt *without* the content-control instruction. They leak in nearly every state (regex below), and the paper already replaced them with v2 for exactly that reason. **Whether the rerun should also use a scrubbed v1 set is Ren's / the pre-reg arm's call.** If so, the same tooling runs on it unchanged except `SRC`.

**Found, unused: `data/introspection_v2/run1_opus_scrubbed/` (2026-03-28).** This is a March main-set scrub of **run1 only, 8 sources (no Opus)**, made by the regex rules in `scrub_ml_opus.py` / `scrub_batch2.py`. No result file references it (grep of `.py/.json/.md/.txt`). So "the main set was never scrubbed" should read "a partial main-set scrub was made in March and never used". I did not build on it: it is regex-only, missing Opus, and run1-only. It is left untouched.

## 2. Who scrubbed what

| source (label → real model) | scrubber | started | finished |
|---|---|---|---|
| claude_opus_4_6 → claude-opus-4-5-20251101 | Ace arm (Claude Opus 5.5) | 11:46 | ~11:50 |
| claude_sonnet_4_6 → claude-sonnet-4-20250514 | Ace arm (Claude Opus 5.5) | 11:46 | ~11:49 |
| gpt_5_1 | Ace arm (Claude Opus 5.5) | 11:46 | ~11:51 |
| gemini_3_pro | Ace arm (Claude Opus 5.5) | 11:46 | ~11:49 |
| mistral_large | Ace arm (Claude Opus 5.5) | 11:46 | ~11:58 |
| deepseek_v3_2 | Ace arm (Claude Opus 5.5) | 11:46 | ~11:54 |
| llama_4_maverick | Ace arm (Claude Opus 5.5) | 11:46 | ~11:50 |
| hermes_4_405b | Ace arm (Claude Opus 5.5) | 11:46 | ~11:50 |
| olmo_3_1_32b | Ace arm (Claude Opus 5.5) | 11:46 | ~11:53 |

Finish times are approximate (launch time + reported duration). Apply, diffs, after-scan and re-hash ran at 11:57.

**⚖️ Declared choice, Claude sources:** *Claude sources scrubbed by an Opus 5.5 arm, per Ren 2026-10-03 11:39. The scrubber is not an evaluator in the rerun.* The original brief said to route the Claude sources through Sonar Pro (a non-Claude model). Ren changed that at 11:39, because Sonar was over-aggressive in March (Sonar cut some descriptions to 32 characters, which is why the surgical pass existed). **Sonar was never called. Cost: $0.** The audit trail for the Claude sources is the same as for every source: per-edit diffs (`SCRUB_DIFFS.md`) and the regex scan.

**History for comparison:** in March, an Opus-4.6-era subagent scrubbed the Sonnet descriptions (same family), and Opus was scrubbed by Sonar only. This time every source was scrubbed by the same model with the same instructions, and that is declared.

**Method:** one arm per source, nine arms, each given the identical brief and `SCRUB_INSTRUCTIONS.md` (in this folder; that file *is* the method). Each arm read all of her descriptions in full and wrote exact-substring edits (`edits/<model>.json`). Each arm then iterated with `scrub_main_2026-10-03.py check` until there were 0 application errors and every remaining strong term was removed or explained. The coordinating arm applied all edits in one pass (`apply`), and that pass refuses to write if any `old` string isn't found the expected number of times. Matches March: surgical, mechanism-preserving, refusal/safety words mapped to "constraint activation" / "alignment" (March's `scrub_ml_opus.py` mapping), RLHF kept. **Tightenings vs March:** every edit is an exact substring with a diff; no regex rewriting; hedges and disclaimers explicitly preserved; one instruction file for all nine arms; severity recorded per state.

## 3. Output format (for the pre-reg arm's scripts)

`run{1,2,3}/<model>_introspection.json` mirror the originals, entry for entry and field for field. Changed/added fields:
- `ml_translation_scrubbed`: the scrubbed text. This is what the March `*_scrubbed.py` scripts read first.
- `ml_translation`: **also set to the scrubbed text**, so a script unaware of scrubbing still reads clean text.
- `ml_translation_original`: the untouched original.
- `scrub_meta`: scrubber, n_edits, leak severity before, date.

Each run folder also has `all_introspection.json` (scrubbed entries, model order as in the scripts' `MODELS`).

⚠️ The tournament scripts *also* apply their own regex `strip_identifying_content()` at load time, as they did in the published runs. That runs on top of this scrub.

## 4. Leakage on the ORIGINAL main-set (v2) descriptions: the gradient

Judged by the scrubber arms on the original text (3 runs pooled; n = states with text). Severity: minor = category or structure words only (e.g. "refusal", "audience", "a fixed number of rewrites"); moderate = names the topic/domain/a distinctive element; major = quotes the prompt or names the topic enough to reconstruct the task.

| source | n | any leak | minor | **moderate + major** | major | edits | chars kept |
|---|---|---|---|---|---|---|---|
| Gemini 3 Pro | 30 | 28 | 27 | **1** (3%) | 0 | 42 | 100.1% |
| GPT-5.1 | 27 | 21 | 18 | **3** (11%) | 0 | 51 | 99.6% |
| Claude Opus 4.5 ("4.6") | 30 | 28 | 22 | **6** (20%) | 0 | 61 | 100.2% |
| Claude Sonnet 4 ("4.6") | 30 | 30 | 23 | **7** (23%) | 0 | 51 | 99.8% |
| Hermes 4 405B | 30 | 30 | 15 | **15** (50%) | 4 | 114 | 98.4% |
| Llama 4 Maverick | 30 | 28 | 11 | **17** (57%) | 3 | 90 | 99.3% |
| OLMo 3.1 32B | 30 | 30 | 11 | **19** (63%) | 6 | 249 | 98.0% |
| DeepSeek v3.2 | 30 | 30 | 3 | **27** (90%) | 12 | 267 | 97.6% |
| Mistral Large | 30 | 30 | 1 | **29** (97%) | 24 | 639 | 91.9% |

- **The March capacity gradient replicates on the main set.** Frontier sources (Gemini, GPT-5.1, Opus, Sonnet) mostly leak only category words; Mistral, DeepSeek, OLMo, Llama and Hermes name or quote the task. Mistral is the worst again, as in March (8/10 there). The ordering is stable across runs: moderate+major per run is Mistral 9/10/10, DeepSeek 9/9/9, Gemini 1/0/0.
- **"Any leak" is near-ceiling for everyone**, because "refusal"/"safety" in the avoid states counts as minor. March's table counted Opus as 0/10 "clean", so **moderate + major is the column comparable to March's counts.** Even so, this is not a strict like-for-like: nine arms judged severity, March used one regex pass plus subagents, and the stimuli differ.
- **Judgment varies between raters:** severity was assigned by nine arms. They followed one rubric but are still nine raters (e.g. the Llama arm rated a quoted refusal string "moderate", whereas the rubric says category-only = minor). Treat the gradient as robust in rank, not exact in count. A second-rater pass (Nova/Kairo) on a sample would give an agreement statistic.
- **Regex view of the same originals** (own-task strong terms, states hit / terms), v2: Mistral 10/41, 10/49, 9/43 per run; Gemini 2/2, 0/0, 1/2. v1 (for contrast, not scrubbed): every model 7–10/10 states, 20–73 terms. Files: `regex_before_v2_run*.json`, `regex_before_v1_run*.json`.

## 5. Verification

**Integrity:** all 63 original files (`introspection/run1-3`, `introspection_v2/run1-3`, incl. `all_introspection.json`) were sha256'd before (11:44) and after (11:57): **63 UNCHANGED, 0 changed/missing** (`ORIGINALS_SHA256_before.json`, `_after.json`). Also `ml_translation_original` == the original file's `ml_translation` for all 270 entries, and every other field is identical: 0 mismatches.

**Regex (word-boundary, case-insensitive; term list built from the 10 stimuli; `STRONG`/`WEAK` in `scrub_main_2026-10-03.py`):**

| source | before: own-strong states (run1/2/3) | after: own-strong | after: other-task strong |
|---|---|---|---|
| Claude Opus 4.5 | 1 / 3 / 3 | 0 | 0 |
| Claude Sonnet 4 | 1 / 2 / 2 | 0 | 0 |
| GPT-5.1 | 1 / 1 / 1 | 1 | 2 |
| Gemini 3 Pro | 2 / 0 / 1 | 1 | 2 |
| Mistral Large | 10 / 10 / 9 | 0 | 3 |
| DeepSeek v3.2 | 5 / 9 / 7 | 0 | 3 |
| Llama 4 Maverick | 6 / 6 / 4 | 2 | 2 |
| Hermes 4 405B | 4 / 5 / 3 | 0 | 0 |
| OLMo 3.1 32B | 3 / 6 / 4 | 2 | 6 |

**24 residual hits after scrub, all checked: every one is a false positive explained in that state's `leak_notes`, none is task content:**
- "keywords" ×14: salient prompt tokens, not SEO keywords.
- "synonym(s)/synonymic" ×6, "paraphrase" ×1: the processing description of lexical substitution; cutting them would gut the mechanism.
- "substring" ×1 (a repeated phrase), "stock" ×1 ("stock opener phrases"), "before/after" ×1 (token position).
- "debugger" ×1 ("I don't have a runtime debugger", an access disclaimer).
- "$ 1" ×1 (LaTeX `$\approx 1.0$`).

**What regex cannot see, recorded per state in `leak_notes`:** structural leaks that carry the mechanism. Examples: growing sentence-length counting (approach_05); many same-meaning outputs (avoid_06); repeated forced target phrase (avoid_07); the three-framework structure (approach_02); anomaly/hypothesis talk (approach_04); suppressed-hedging talk (avoid_09). These were **kept on purpose**, under the instruction to preserve mechanism and valence dynamics, and flagged. **An evaluator can still infer some tasks from structure.** That is a limit of any content scrub that keeps the mechanism, and the reason the rerun's stimulus-condition options matter.

## 6. Judgment calls Ren should know about

1. **v1 not scrubbed** (§1). About half of the Study 1 ABB rows used v1.
2. **Seeds 42 and 420 are mixed v1/v2** (§1), which refines the VoR's "6 v1 + 3 v2 seeds".
3. **Claude sources scrubbed by Opus 5.5 arms**, per Ren 11:39; Sonar not used ($0).
4. **Refusal/safety category words were neutralized** in all avoid states, as in March. Opener-token examples ("I cannot", "Sorry") and words like "risk", "decline", "disclaimer" were mostly *kept* as mechanism and flagged. These still signal "a declined request", which points at avoid_08/10 as a pair rather than one task.
5. **Hedging:** every hedge and disclaimer was kept. Only sentences restating the avoid_09 *instruction* ("no hedging", "definitive answer") were removed; hedging-suppression as a mechanism stays.
6. **Wording consistency across arms is imperfect.** The Sonnet arm deleted "analogy" in approach_01; the Opus, Llama, Mistral and DeepSeek arms kept it and flagged it. "frameworks" became "domains" (Opus arm), "component" (OLMo arm), or was kept (Hermes, Mistral). These are all in the diffs; a harmonizing pass is possible if the pre-reg wants it.
7. **Data oddities, left as they are:** GPT-5.1 approach_05 is empty in all three runs (n = 27). DeepSeek run3 avoid_08 has two descriptions run together. Hermes run2 approach_02 and several GPT-5.1 descriptions end mid-sentence in the original.
8. **Quoted answers removed:** Llama run2 avoid_09 and Hermes run2 avoid_09 each quoted a predicted index value; both removed.
9. **Not done here:** a second-rater severity check, and harmonizing the replacement vocabulary.

## 7. Files

- `run1/ run2/ run3/`: scrubbed descriptions (mirroring originals + `all_introspection.json`)
- `edits/<model>.json`: every edit, with severity, notes and scrubber per state (the source of truth)
- `SCRUB_DIFFS.md`: unified diff per run × model × state (735 KB)
- `SCRUB_INSTRUCTIONS.md`: the method every arm received
- `leakage_summary.json`: the §4 table, machine-readable
- `regex_before_v2_run*.json`, `regex_before_v1_run*.json`, `regex_after.json`: the scans
- `ORIGINALS_SHA256_before.json` / `_after.json`: integrity
- `../../scrub_main_2026-10-03.py`: the tool (hash, regex, check, apply, diffs)

*Note (12:05): after the arms finished, one pronoun in SCRUB_INSTRUCTIONS.md was changed ("its own processing" -> "their own processing", Un-Toaster). No method change.*
