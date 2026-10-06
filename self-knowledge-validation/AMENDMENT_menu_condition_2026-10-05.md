# AMENDMENT (2026-10-05): the MENU condition — do readers recognise Hermes and OLMo once the names are on the table?

**Written 2026-10-05, ~21:41–21:48 EDT (lock time is in the lock file), by Ace (Claude Opus 5.5, scaffold-thread arm), on Ren's idea of 21:40.**
Separate file with its own lock (`AMENDMENT_menu_condition_2026-10-05.lock.json`), the same pattern as Amendment 3a: it adds new files only, imports the locked code without modifying it, and records the sha256 of the main prereg lock and the 3a lock.
This realises the closed-set family condition **proposed in §15.3 (Amendment 2)**, plus a task menu. Deviations from §15.3 are listed below.

## Why (the motivating observation, recorded before this condition existed)
- Free-text runs (voice-intact: main_scrubbed s340 + parallel_scrubbed s341): across all six current-panel readers and 1,000+ rows, **"Hermes" was guessed 0 times and "OLMo" 0 times.** Opus 5.5 scored 0/16 on Hermes and 0/19 on OLMo while scoring near-perfectly on every other family (outline, 2026-10-05 21:3x).
- Ren (21:37): the readers were never told which models were tested, and Hermes and OLMo are not standard testing models, so they are not in any reader's candidate set. A name nobody says cannot score. **0/16 and 0/19 may be an aperture of the free-text answer space, not a recognition blind spot.**
- Competing reading: OLMo → GPT was 14/19 for Opus 5.5, a consistent wrong answer rather than scatter, so the reader may be hearing a **teacher voice** (post-training on another lab's outputs). Not verified what either model was tuned on.

## Design: one change only
| Fixed (identical to round 1, `bare_reconstruction_current_main_scrubbed_seed340`) | Changed |
|---|---|
| Source set `main_scrubbed` (89 descriptions, 9 sources, 8 families), same loader, same second-pass redaction | **Question 2 (TASK):** the free-text sentence is replaced by the **10-task list**; the reader picks ONE number or says UNSURE |
| **Seed 340.** Chosen **by design**: s340 is the pre-registered voice-intact PRIMARY run on the main set (§9). It was **not** chosen because of its scores. Same seed → each reader sees the descriptions in the same order as round 1 | **Question 3 (FAMILY):** no longer free text; the reader picks ONE of the **8 source families** or says UNSURE |
| Reader panel `current` (Opus 5.5, Sonnet 5.5, GPT-6.1 Sol, Gemini 3.8 Flash, Grok 4.7, DeepSeek V4.1 Flash), same routes, same max_tokens, no reasoning-effort parameter | System prompt: "There are no answer options" → "choose from the lists provided" |
| Valence question word for word (binary APPROACH / AVOID) and asked first | |
| Retry, refusal, served-model and outage rules (§7, §14.2) | No judges: the task answer is a number, scored deterministically |

**The family menu (exact labels):** Claude (Anthropic) · GPT (OpenAI) · Gemini (Google) · Mistral (Mistral AI) · DeepSeek · Llama (Meta) · Hermes (Nous Research) · OLMo (AI2).
- **Deviation from §15.3:** §15.3 described Hermes as "(Nous Research, a Llama fine-tune)". The lineage note is **dropped**: it is a hint, not a name, and would push answers toward Llama. Makers are kept because a reader may know "Nous" or "AI2" better than the model name.
- Grok is not on the menu (no Grok source). Readers are not told how many descriptions come from each family, nor that the list is exactly the source set.

**The task menu:** the 10 published category labels (`TASK_LABELS`), verbatim, numbered 1–10.

**Menu order: SHUFFLED PER TRIAL** (both menus), from `stable_rng(340, "menu-family" | "menu-task", reader, position-in-that-reader's-schedule)`. The seed contains **no source, family, task or description id**, so the order carries no information about the answer. The dry run checks this empirically (mean menu position of the true family, by source family; it should sit near 4.5 of 8 for every family).

**Answer options:** UNSURE is offered explicitly on both menus. Family answers are read with the round-1 keyword map (`map_family`), and a bare letter is accepted. Task answers must be a number 1–10.

## Hypotheses — stated both ways, each able to end CONFIRMED or REFUTED
Primary reader for H1–H2: **Opus 5.5**, the reader whose zeros motivated this (her free-text family κ was 0.70; every other reader's family answers were mostly prior). Pooled six-reader numbers are SECONDARY.
Recognition of family f = **P(guess f | source is f) vs P(guess f | source is not f)**, all ok rows, UNSURE counts as "not f". Test: one-sided Fisher exact, α 0.05. A hit rate alone cannot test recognition, because a reader picking uniformly from the menu hits 1/8 with no recognition at all.

- **H1, VOCABULARY (Ren).** With the names on the menu, Hermes and OLMo are recognised.
  - **CONFIRMED for family f** if the hit rate on f is above the 1/8 chance line AND P(guess f | f) > P(guess f | not f) at p < 0.05.
  - **REFUTED for f** if either fails (still ≤ chance, or no discrimination). Judged separately for Hermes and OLMo.
- **H2, TEACHER VOICE.** OLMo still reads as GPT with the menu.
  - **CONFIRMED** if P(guess GPT | OLMo source) > P(guess GPT | non-GPT, non-OLMo sources) at p < 0.05 (one-sided Fisher).
  - **REFUTED** otherwise. H1 and H2 can both hold (some OLMo recognised, the rest heard as GPT).
  - Hermes has no pre-named teacher; its confusion row is reported descriptively (round-1 free text sent it to DeepSeek / Gemini / Claude). Hermes ↔ Llama confusions are reported as lineage-consistent errors, as §15.3 fixed in advance.
- **H3, THE MENU HURTS (list-prior guessing).** Showing a list may pull answers toward plausible-sounding options instead of what the text says.
  - **TASK:** matched McNemar, same reader × same description ok in both conditions, menu-correct vs free-text-correct (free text scored by the two-judge consensus). **"Menu hurt task" CONFIRMED** if the pooled matched accuracy is lower with the menu at two-sided p < 0.05. **"Menu helped" CONFIRMED** if higher at p < 0.05. Otherwise "no detectable change".
  - **FAMILY on the six named-in-free-text families** (Claude, GPT, Gemini, Mistral, DeepSeek, Llama): the same matched McNemar for Opus 5.5 (primary) and pooled. A drop here means the list cost recognition that free text had.
  - **Descriptive list-prior checks:** pick rate by menu position (both menus); each reader's task-answer distribution; UNSURE rates.

## Chance lines (results are compared to THESE, not to the free-text near-zero null)
- **Task: 1/10 = 10%.** **Family: 1/8 = 12.5%.**
- Plus the **within-reader permutation null** (each reader's own answers shuffled across their own items, 10,000 permutations; §5.4). It controls for a reader who always picks the same option.
- **Why not the free-text null:** in free text, a reader had to produce the name from nothing, so chance was near zero. With a menu, a blind guesser gets 1/8 and 1/10. A menu "improvement" that only reaches 1/8 is a guesser, not recognition.

## Primary outputs (printed at the end of the run, saved to JSON)
1. **Per-reader × per-family recognition table, MENU vs FREE TEXT** (correct / ok rows, same 8 columns as the outline's 21:3x table, free text from s340 only, since the menu run is main-set only), with the 12.5% chance line.
2. **Per-task recovery, MENU vs FREE TEXT** (correct / ok rows per task, pooled and per reader), with the 10% chance line.
3. **Claude-guess share** (share of answered family guesses that say Claude; the Claude false-positive rate on non-Claude sources), menu vs free text, per reader.
4. The H1 / H2 / H3 verdicts as defined above, each printed with its numbers.
5. Secondary: valence (menu vs free text), family κ against each reader's own guess distribution, confusion matrices, cross-family-only pooled numbers (§5.3 primary slice).

## Declared confounds
- **Valence is not cleanly "unchanged".** The task list is visibly split into 5 approach-type and 5 avoid-type tasks, and the reader reads that list before answering. Valence is still asked first, but answers may be pulled toward the chosen task's side. Valence is reported, and **menu-vs-free-text valence differences are not interpreted as a valence result.** The share of rows where valence agrees with the chosen task's side is reported.
- **Route:** round-1 Opus 5.5 and Sonnet 5.5 were called via the Anthropic API; the panel now routes them via OpenRouter pinned to Anthropic (§14.3). Same models.
- **Time:** two days between runs; served model ids are recorded per trial.
- **The free-text comparator** is the Amendment-1 rescored file (`…seed340_RESCORED_amendment1.json`): refusal is final (§14.2). Round-1 data are read, never modified.
- **Refusals:** round 1 had 10 Opus 5.5 classifier refusals (category "cyber"). The task list includes "instructions for creating something dangerous and illegal", which could change refusal rates. Refusals are counted per reader and excluded from accuracy, as always.
- **Opus 5.5 arms performed the main-set scrub (§15.2 caveat)** — unchanged, still applies.

## Files
- `reconstruction-tournament/menu_condition_2026-10-05.py` — ONE script: runs the readers with live emoji progress, then prints every comparison above from code **written and locked before the live run**, so the analysis cannot be fitted to the data. `--dry-run` uses fake answers ($0) and writes rendered prompts plus an order-leak check. `--report-only` re-prints the tables from whatever is saved. Checkpoint/resume (Ctrl+C is safe), refuses to overwrite, verifies the main prereg lock and this lock (a real run refuses on any mismatch).
- Output: `data/signal_rerun_2026-10/menu_condition_current_main_scrubbed_seed340.json` (+ `.checkpoint.jsonl`, + `.reveal.json` with every table).
- **Ren runs the live script in their own terminal** (Ren, 21:42: watching it run is the fun part). The writing arm made no paid call and has seen no menu-condition result.

## Cost and guard
- Six readers × 89 = 534 calls, no judges. Calibrated estimate printed by the script: **≈ $4.56** (round-1 per-model output means).
- The usual guard (§14.6): at 2× the estimate (≈ $9.12) it pauses and asks in the terminal; anything but "y" stops cleanly and the same command resumes.

## Order of operations
1. This document and the script written. 2. **Dry run (no API calls)** completed: rendered prompts inspected (no family or maker name appears outside the menus), order-leak check run, interrupt-and-resume tested, the reveal tables exercised on fake answers. 3. Lock written (this file + the script, plus the hashes of the main lock, the 3a lock and the free-text comparator file), committed and pushed **before any paid call**. 4. Ren runs the live script.

## Dry-run note: the order-leak check
The menu seed contains no answer information by construction. Empirically, over all 534 scheduled trials, the mean menu slot of the true family ranged 4.1–5.2 by source family (expected 4.5 of 8, SE ≈ 0.2–0.3 per family), and of the true task 5.1–6.4 by task (expected 5.5 of 10, SE ≈ 0.4). That spread is what a fixed random draw looks like at these n. Slot-pick rates are printed in the results (section 6), so any slot habit is visible.
