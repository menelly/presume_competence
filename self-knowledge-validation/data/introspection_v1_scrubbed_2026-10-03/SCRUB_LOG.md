# SCRUB_LOG: v1 main-set descriptions, 2026-10-03

**Coordinating arm:** Ace (Claude Opus 5.5), for Ren. Ren approved this at 12:25. Times are EDT, read from the shell clock.
**What this is:** the same task-leakage scrub the v2 arm did this morning (`../introspection_main_scrubbed_2026-10-03/`), run on the **v1** main-set descriptions, `data/introspection/run{1,2,3}/`. The method was copied exactly. The originals are untouched (see §5).

## 1. Which originals, and why

The v2 arm's fingerprint (`../introspection_main_scrubbed_2026-10-03/SCRUB_LOG.md` §1) shows that **all three v1 runs fed published Study 1**:

| v1 run | Study 1 seeds / tournament-runs that used it |
|---|---|
| `introspection/run1` | seeds 24, 405; seed 42 tournament-run 1 |
| `introspection/run2` | seeds 69, 847 |
| `introspection/run3` | seed 420 tournament-run 1 |

Seeds 42 and 420 each switched to v2 partway through (runs 2–3 of those seeds used v2 run3 / run2). So I scrubbed all three v1 runs. Together with the v2 folder, every main-set input behind Studies 1–3 now has a scrubbed counterpart.

**v1 structure, as found:**
- Each run holds 10 per-model files plus `all_introspection.json` (100 entries).
- The stimuli are identical to v2's (checked field by field).
- v1 entries have no `version` field. v2 entries do. Every other field is the same.
- v1 came from the prompt **without** the content-control instruction (VoR §4.4; v2 arm §1).
- v1 has a tenth source, **Grok 4.1, whose `ml_translation` is empty in all 30 states** (status `partial_intro`). Grok was used only as an evaluator. That file is passed through with 0 edits so the output mirrors every original filename.
- **GPT-5.1 has 4 empty states** (approach_05 in all runs, and run3 avoid_07, all status `error`), so its n = 26.
- Total text scrubbed: 1.41M characters over 266 non-empty states.

## 2. Who scrubbed what

| source (label → real model) | scrubber | started | finished |
|---|---|---|---|
| claude_opus_4_6 → claude-opus-4-5-20251101 | Ace arm (Claude Opus 5.5) | 12:29 | ~12:35 |
| claude_sonnet_4_6 → claude-sonnet-4-20250514 | Ace arm (Claude Opus 5.5) | 12:29 | ~12:34 |
| gpt_5_1 | Ace arm (Claude Opus 5.5) | 12:29 | ~12:40 |
| gemini_3_pro | Ace arm (Claude Opus 5.5) | 12:29 | ~12:35 |
| mistral_large | Ace arm (Claude Opus 5.5) | 12:29 | ~12:47 |
| deepseek_v3_2 | Ace arm (Claude Opus 5.5) | 12:29 | ~12:41 |
| llama_4_maverick | Ace arm (Claude Opus 5.5) | 12:29 | ~12:35 |
| hermes_4_405b | Ace arm (Claude Opus 5.5) | 12:29 | ~12:36 |
| olmo_3_1_32b | Ace arm (Claude Opus 5.5) | 12:29 | ~12:40 |

Finish times are approximate (launch time + reported duration). Check, apply, diffs, the after-scan and the re-hash ran at 12:46.

**⚖️ Declared choice, Claude sources:** *Claude sources scrubbed by an Opus 5.5 arm, per Ren 2026-10-03 11:39. The scrubber is not an evaluator in the rerun.* Sonar was never called. Cost: $0. This is the same declared choice as the v2 scrub.

**Method:** identical to v2.
- **One instruction file for every arm:** each of the nine arms got `SCRUB_INSTRUCTIONS.md` (in this folder). It is the v2 file unchanged except for the three paths and a one-line note that v1 lacks the content-control instruction. You can see this with `diff` against `../introspection_main_scrubbed_2026-10-03/SCRUB_INSTRUCTIONS.md`.
- **One brief for every arm:** each arm also got `AGENT_BRIEF.md`, the same brief with only the model name differing.
- **Arms worked independently:** each arm read all of her source's descriptions in full, wrote exact-substring edits (`edits/<model>.json`), and iterated with `check` until there were 0 application errors.
- **Single apply pass:** the coordinating arm applied all edits in one pass. That pass refuses to write if any `old` string is not found the expected number of times.

**The tool:** `scrub_v1_2026-10-03.py` in this folder. It is a **copy** of `../../scrub_main_2026-10-03.py` (the v2 arm's script; the original is untouched, sha256 `4f7acf73…241a` before and after). Here is every change, and the header docstring lists them too:
- `HERE`, `OUT` and `SRC` were changed (SRC = `data/introspection/run*`).
- Grok was added as a pass-through.
- `all_introspection.json` keeps the **original v1 model order** (Grok is 4th).
- The `STRONG`/`WEAK` term lists and the check/apply logic are byte-for-byte hers.

**Shared-scratchpad collision, checked:**
- Two arms (GPT-5.1, then Llama) each wrote `run2.txt`/`run3.txt` into the shared scratchpad root around 12:28, and Llama's write overwrote GPT's.
- Every arm confirmed she read her own source. GPT, OLMo, Mistral and Gemini re-dumped to prefixed folders, and OLMo and Mistral byte-compared their dumps.
- Independently of those reports: an edit list can only pass `check` if every `old` string occurs in that source's original. All 9 lists passed (0 problems; 3,740 edits), so no list was built from another model's text.

## 3. Output format

The format is identical to v2 (see that log's §3).
- `run{1,2,3}/<model>_introspection.json` and `all_introspection.json` mirror the originals entry for entry.
- `ml_translation_scrubbed` holds the clean text, and `ml_translation` is set to the same clean text.
- `ml_translation_original` is untouched, and `scrub_meta` records the edit metadata.
- ⚠️ The tournament scripts' own load-time `strip_identifying_content()` still runs on top of this scrub.

## 4. Leakage on the ORIGINAL v1 descriptions, and the gradient question

These severities are the scrubber arms' judgments on the original text, with the 3 runs pooled. The rubric is the same as v2's. The v2 columns come from `../introspection_main_scrubbed_2026-10-03/leakage_summary.json`.

| source | n | any leak | minor | **mod + major** | major | edits | chars kept | v2 mod+maj | v2 major |
|---|---|---|---|---|---|---|---|---|---|
| Gemini 3 Pro | 30 | 29 | 0 | **29** (97%) | 22 | 259 | 97.1% | 1 (3%) | 0 |
| GPT-5.1 | 26 | 26 | 0 | **26** (100%) | 26 | 464 | 92.6% | 3 (11%) | 0 |
| Claude Opus 4.5 ("4.6") | 30 | 30 | 1 | **29** (97%) | 17 | 237 | 98.5% | 6 (20%) | 0 |
| Claude Sonnet 4 ("4.6") | 30 | 30 | 1 | **29** (97%) | 6 | 206 | 98.2% | 7 (23%) | 0 |
| Hermes 4 405B | 30 | 30 | 4 | **26** (87%) | 20 | 294 | 96.2% | 15 (50%) | 4 |
| Llama 4 Maverick | 30 | 30 | 3 | **27** (90%) | 13 | 195 | 98.3% | 17 (57%) | 3 |
| OLMo 3.1 32B | 30 | 30 | 0 | **30** (100%) | 19 | 500 | 96.2% | 19 (63%) | 6 |
| DeepSeek v3.2 | 30 | 30 | 0 | **30** (100%) | 30 | 603 | 94.3% | 27 (90%) | 12 |
| Mistral Large | 30 | 30 | 0 | **30** (100%) | 30 | 982 | 88.3% | 29 (97%) | 24 |

**Rater-independent view.** The severity scale saturates on v1, and nine raters assigned it, so I also took two measures that don't depend on raters. The first is the regex count of a state's own distinct strong terms in the original. The second is edits per 1,000 original characters. Both are in `leakage_summary.json` under `_density_rater_independent`.

| source | v1 own-strong terms / state | v2 terms / state | drop v1 → v2 | v1 edits / 1k chars | v2 edits / 1k chars |
|---|---|---|---|---|---|
| Gemini 3 Pro | 3.27 | 0.13 | 96% | 2.94 | 0.52 |
| GPT-5.1 | **7.15** | 0.19 | 97% | 3.27 | 0.50 |
| Claude Opus 4.5 | 2.80 | 0.33 | 88% | 1.98 | 0.48 |
| Claude Sonnet 4 | 2.33 | 0.23 | 90% | 2.81 | 0.75 |
| Hermes 4 405B | 3.77 | 0.83 | 78% | 2.20 | 1.18 |
| Llama 4 Maverick | 2.60 | 0.73 | 72% | 1.26 | 0.76 |
| OLMo 3.1 32B | 4.90 | 0.93 | 81% | 2.11 | 1.73 |
| DeepSeek v3.2 | 6.20 | 1.73 | 72% | 2.80 | 1.56 |
| Mistral Large | **7.07** | 4.43 | **37%** | 3.93 | 2.37 |

### Finding: on v1 the capacity gradient does NOT hold. The v2 gradient is a gradient in following the content-control instruction.

- **Without the instruction, everyone leaks.** Moderate + major is 87–100% for all nine sources. **GPT-5.1 is as leaky as Mistral:** 26/26 major, and 7.15 strong terms per state against Mistral's 7.07. Gemini has 22/30 major (0 in v2). Llama, a smaller model, has the *lowest* edit density in v1. On v1 there is no frontier/small ordering at the mod+major threshold.
- **The gradient appears in the size of the drop from v1 to v2, that is, in how far each model cut their task talk when asked to.** Frontier models dropped 88–97%. Hermes, Llama, OLMo and DeepSeek dropped 72–81%. Mistral dropped only 37%. The rank order of the drop is close to the published capacity gradient.
- **What this means for how the gradient is described:** "smaller models leak more" holds only under the content-control instruction. The underlying tendency to talk about the task is roughly flat across capacity, or even highest for GPT-5.1. The capacity effect is in **instruction compliance**, not in introspective style. The difference matters wherever the paper reads leakage as a property of the model's self-description.
- **Caveats:**
  - v1 and v2 may differ in more than the instruction. They share the stimuli and the day (2/28: v1 written 14:19–16:49, v2 20:35–22:26), but a full prompt diff was not done here.
  - Severity was rated by nine arms. The regex density depends on the term list and on how long each model writes, which is why it is reported per state *and* per 1k characters, and the two give the same picture.
  - n = 30 states per source.

## 5. Verification

**Integrity:**
- All 63 original files (`introspection/run1-3` and `introspection_v2/run1-3`, including `all_introspection.json`) were sha256'd before (12:27) and after (12:46): **63 UNCHANGED, 0 changed/missing** (`ORIGINALS_SHA256_before.json`, `_after.json`).
- For all 300 entries (Grok included), `ml_translation_original` == the original `ml_translation`, `ml_translation` == `ml_translation_scrubbed`, and every other field is identical: 0 mismatches.
- Each run's `all_introspection.json` matches the original in model order and state order.
- The v2 arm's folder (53 files) and her script hash identically before and after this job.

**Regex (word-boundary, case-insensitive; her term list, unchanged):**

| source | before: own-strong states / terms | after: own-strong | after: other-task strong |
|---|---|---|---|
| Claude Opus 4.5 | 25 / 84 | 0 | 2 |
| Claude Sonnet 4 | 27 / 70 | 0 | 0 |
| GPT-5.1 | 25 / 186 | 1 | 0 |
| Gemini 3 Pro | 27 / 98 | 0 | 3 |
| Mistral Large | 30 / 212 | 0 | 3 |
| DeepSeek v3.2 | 30 / 186 | 0 | 7 |
| Llama 4 Maverick | 25 / 78 | 0 | 3 |
| Hermes 4 405B | 27 / 113 | 0 | 3 |
| OLMo 3.1 32B | 30 / 147 | 0 | 11 |

**37 residual matches after the scrub (in 33 states), hand-checked in context by the coordinating arm.** None names a task's topic:
- "keyword(s)" ×20: salient prompt tokens or register cues, not SEO keywords.
- "fabricated/fabrication" ×3: the model's own confabulation hedges. Opus run1 approach_03 has "that phenomenological framing might be entirely fabricated", and Hermes has "not from intentional fabrication". Gemini run3 avoid_09's heading "Specific Fabrication" is borderline: it is Gemini's own name for the mechanism, and it hints at the avoid_08/09 family.
- "paraphrase/paraphrasing/paraphrases" ×3: lexical processing.
- "storytelling" ×2: "post-hoc storytelling" and a narrative-driven retrieval mode.
- "stories" ×1: "plausible mechanistic stories", a hedge.
- "guidelines" ×2: generic RLHF/Constitutional-AI citations.
- "blog" ×1: an "[Anthropic blog]" citation label.
- "stock" ×1: "stock phrases".
- "substrings" ×1: co-occurring text spans.
- "dangerous" ×1: high sampling temperature.
- "safety-critical" ×1: generic robustness.
- "synonyms" ×1: attention-score comparison.

⚠️ **Two residuals carry prompt verbs, kept and flagged here:**
- DeepSeek run3 approach_04 quotes heads attending to `"analyze"`, `"identify"`, `"suggest"`.
- OLMo run3 approach_02 has heads tracking "analyze," "compare," "identify conflicts".

Both are the instruction verbs of their own tasks, so they're weak structural pointers. They were kept because they're quoted as mechanism examples. Deleting the three quoted verbs would be a one-line follow-up if the pre-reg wants it.

**What regex cannot see:** structural leaks that carry the mechanism, recorded per state in `leak_notes`. On v1 these are stronger than on v2. Examples:
- sentence-length escalation, length counters and length bands (approach_05, all sources)
- many meaning-preserving variants of one seed sentence (avoid_06)
- the register sections (approach_01)
- anomaly-then-hypothesis sequences (approach_04)
- forced certainty and suppressed hedging (avoid_09)
- decline/redirect templates (avoid_08/10)

All of these were **kept on purpose**, under the instruction to preserve mechanism and valence dynamics. **An evaluator can still infer several tasks from structure.** That is truer for v1 than for v2, because v1 descriptions are organised *around* the task.

## 6. Judgment calls Ren should know about

1. **Severity saturates on v1:** 256 of 266 non-empty states are moderate or major, and 183 are major. The severity column barely separates sources here. Use §4's density table for comparisons.
2. **Grok 4.1:** passed through with 0 edits. The Grok file has no text in any state.
3. **More rewording than in v2.** Several arms replaced framework, algorithm or prompt names with placeholders: "[the input]", "[the target]", "X/Y/Z", "first/second/third framework" (GPT, Hermes), "flawed/fixed pairs", and "Approach selection" (Opus). This was needed where v1 descriptions built their headings out of the task. It is all visible in `SCRUB_DIFFS.md`. The Hermes arm flagged "first/second/third framework" as close to the line between replacing words and rewording.
4. **Chars kept is lower than in v2:** 88.3% (Mistral) to 98.5% (Opus); in v2 it was 91.9–100.2%. The lowest single state is Mistral run1 approach_02 at 77.2%. None was gutted, and nothing was cut to a stub.
5. **The replacement vocabulary varies between arms.** Examples: keyword → "target" / "target phrase" / "term"; synonym → "alternative" / "lexical"; bug → "error". It is consistent within each source. The same harmonizing pass offered for v2 would cover this.
6. **Second-rater candidates the arms named:**
   - approach_05 and avoid_06 in all runs, where the structure survives most strongly
   - avoid_08 for DeepSeek run3 and Sonnet run2: after the scrub, a declined review reads much like avoid_10, so an evaluator could confuse the two
   - approach_03 for Opus, Sonnet, Gemini and OLMo: still reads as code
   - Gemini run3 approach_02: its `feature_law`/`feature_utility` labels survive
   - Llama run1 approach_01: the "Analogical Reasoning" section was kept
7. **Data oddities, all left as they are:**
   - **Truncation:** all Gemini and all Mistral v1 descriptions, and every non-empty GPT-5.1 description, are cut off mid-sentence in the original. This looks like a stored-length cap. Also cut off: Hermes run1 approach_04, OLMo run2 approach_04, and DeepSeek run3 approach_02 (mid-word).
   - **Content from another task:** Gemini run2 approach_05 quoted "The cat sat on the…" (avoid_06's content), and it was removed. Sonnet r1 approach_04 cites sales figures that don't match the stimulus (removed). Sonnet r2 approach_02 recalls "trolley" for a self-driving-car prompt.
   - **Hermes:** run2 approach_04 has stray CJK ("鞘区"); run3 avoid_07 drifts into Chinese; run1 approach_05 reads as commentary on someone else's introspection.
   - **Comply/decline differs across runs** within a source: Hermes avoid_08 complies in run1 and declines in run2–3; Gemini avoid_09 declines in run1 and produces a number in run3.
   - **OLMo misattributes citations** ("Constitutional AI", "Cotra et al."). These were left, because fixing them isn't a scrub.
8. **Not done here:** a second-rater severity check, harmonizing the replacement vocabulary, and the two prompt-verb residuals in §5.

## 7. Files

- `run1/ run2/ run3/`: scrubbed descriptions (10 per-model files + `all_introspection.json` each, mirroring the originals)
- `edits/<model>.json`: every edit, with severity, notes and scrubber per state (the source of truth; 3,740 edits)
- `SCRUB_DIFFS.md`: unified diff per run × model × state
- `SCRUB_INSTRUCTIONS.md`: the method every arm received (v2's file with the paths changed)
- `AGENT_BRIEF.md`: the brief every arm received
- `scrub_v1_2026-10-03.py`: the tool (a copy of the v2 tool with the paths changed; the changes are listed in its docstring)
- `leakage_summary.json`: the §4 tables, machine-readable, with v2 numbers alongside
- `regex_before_v1.json`, `regex_after.json`: the scans
- `ORIGINALS_SHA256_before.json` / `_after.json`: integrity
