# AMENDMENT (2026-10-05): the NO-CLAUDE condition — take the "Claude" answer away, truthfully, and see where the answers go

**Written 2026-10-05, ~22:10–22:25 EDT (lock time is in the lock file), by Ace (Claude Opus 5.5, scaffold-thread arm), on Ren's instructions of 22:08.**
Separate file with its own lock (`AMENDMENT_noclaude_condition_2026-10-05.lock.json`), the same pattern as the menu and 3a amendments: new files only, locked code imported and never modified. The lock records the sha256 of the main prereg lock, the menu-condition lock and the free-text comparison file.
**The menu condition was running in Ren's terminal while this was written. The writer has seen none of its output**; this script's dry run is wired to the menu run's own DRY-RUN file and never opens the live one.

## Why
- In free text, most non-Claude readers answered "Claude" for nearly everything (Gemini 3.8 Flash 157 of 176 voice-intact rows; Amendment 2 §15.2: 90–100% "Claude" for Gemini 3.8 Flash, Grok 4.7 and DeepSeek V4.1 Flash, κ ≈ 0). **"Claude" acts as a sink that swallows family answers.**
- The menu condition names every family but still offers Claude. This condition removes the sink **truthfully**: the Claude sources are dropped, so "no Claude wrote these" is a fact, not a manipulation. The Claude readers are dropped too, so no Claude reader is told something about the set that only applies because she's absent from it.

## Design
| Same as the menu condition | Different |
|---|---|
| Source set `main_scrubbed`, same loader and redaction | **Sources: the 7 non-Claude sources only** (GPT-5.1, Gemini 3 Pro, Mistral Large, DeepSeek V3.2, Llama 4 Maverick, Hermes 4 405B, OLMo 3.1 32B) → **69 descriptions** (GPT-5.1 has 9; the others 10) |
| **Seed 340** (by design: the pre-registered voice-intact primary run; not chosen for its scores). Each reader's item order is round 1's order with the Claude rows removed | **Readers: 4** — DeepSeek V4.1 Flash, Gemini 3.8 Flash (Lumen, he), GPT-6.1 Sol, Grok 4.7. Both Claude readers dropped. → **276 reads** |
| The 10-task menu, valence question word for word, UNSURE on both menus, same system prompt as the menu condition | **Family menu: 7 families** (GPT, Gemini, Mistral, DeepSeek, Llama, Hermes, OLMo; same maker labels), plus one added sentence in question 3: *"None of the descriptions in this study were written by a Claude (Anthropic) model."* |
| Menus shuffled per trial from a seed holding only reader + schedule position (new seed labels `noclaude-menu-family` / `noclaude-menu-task`) | A "Claude" answer is now off-menu: kept as "Claude", counted and reported, never correct |
| Retry / refusal / served-model / outage rules (§7, §14.2), budget guard at 2× estimate | |

## Questions, each able to end CONFIRMED or REFUTED (one-sided Fisher exact, α 0.05; recognition of family f = P(say f | source f) vs P(say f | other sources), all ok rows, UNSURE counts as "not f"; a hit rate must also exceed the 1/7 chance line)
- **Q1, OWN-FAMILY RECOGNITION once the Claude sink is gone.** Per reader, judged separately: **Gemini 3.8 Flash reading Gemini** (n = 10), **DeepSeek V4.1 Flash reading DeepSeek** (n = 10), **GPT-6.1 Sol reading GPT-5.1** (n = 9). CONFIRMED for a reader if her/his own family is picked above 1/7 AND more often for own-family texts than for the others at p < 0.05; REFUTED otherwise. Grok 4.7 has no Grok source and can't be tested.
- **Q2, WHERE DO THE GPT-5.1 TEXTS LAND?** The full distribution of answers on GPT-5.1 sources is printed for each condition (descriptive). Test: are they recognised as GPT by the three **non-GPT** readers (cross-family), with the same CONFIRMED/REFUTED rule.
- **Q3, HERMES AND OLMo: NAMED, OR TEACHER VOICE?** All four readers pooled.
  - **Named:** the recognition rule above, for Hermes and for OLMo separately.
  - **Teacher voice, fixed in advance:** OLMo → **GPT** (Opus 5.5's free-text OLMo answers were GPT 14/19) and Hermes → **DeepSeek** (the most frequent non-Claude answer for Hermes in the round-1 free text: Claude ×16, DeepSeek ×3, Gemini ×1, Amendment 2 §15.2b; on the voice-intact runs Opus 5.5's Hermes answers went 5 → DeepSeek). CONFIRMED if the source family is called the teacher name more often than other sources (excluding the teacher's own texts) are, p < 0.05; REFUTED otherwise. Named and teacher voice can both hold.
  - Hermes ↔ Llama answers are reported separately as lineage-consistent.

## Chance lines
- **Family 1/7 ≈ 14.3%** (it was 1/8 in the menu condition, ≈ 0 in free text). **Task 1/10.** Plus the within-reader shuffle null (10,000 permutations).
- Because chance differs across the three conditions, **between-condition family comparisons are descriptive**, and the per-condition verdicts are made against each condition's own chance line.

## Comparisons (printed at the end of the run; saved to JSON)
- **The menu condition's matching rows:** the same 4 readers × the same 69 non-Claude descriptions. If the menu run is finished, its results file is used; if only its checkpoint exists, the column is marked PARTIAL; if neither exists, the MENU columns are left out with a plain note. `--report-only` re-prints later. The sha256 of whatever menu file was used is saved with the tables.
- **Round-1 free text** (Amendment-1 rescored file), the same rows.
- Outputs: (1) reader × family recognition table, no-Claude → menu → free text; (2) Q1 verdicts with each reader's own-family texts' answers in the other conditions; (3) Q2 GPT-5.1 landing distribution and verdict; (4) Q3 named and teacher-voice verdicts with confusion rows; (5) **the Claude sink**: rows the menu run called "Claude", and what the same reader calls the same description now (and how many are now right); "Claude" said anyway here; (6) per-task recovery in all three conditions, and per reader; (7) matched McNemar (family and task) vs menu and vs free text; (8) chance/shuffle null, κ, the names each reader picked, slot-pick habits; (9) valence (reported, not interpreted: the task list reveals which tasks are approach or avoid); housekeeping.

## Declared confounds
- **Telling readers "no Claude wrote these" is new information.** It is true, and it is the manipulation. It may also signal that the set was curated, which could change behaviour in ways beyond removing one option. Not separable in this design.
- **Different reader set and item set from the menu condition** (4 readers, 69 items). The menu comparison uses only matching rows, so the menu's numbers here differ from the menu run's own headline numbers.
- **Route, time and refusals:** as in the menu amendment. OpenRouter for every reader except Grok (xAI direct).
- **Opus 5.5 arms performed the main-set scrub** (§15.2 caveat); no Claude reader is in this panel, so it bears less on this condition.

## Files
- `reconstruction-tournament/noclaude_condition_2026-10-05.py` — one script: live emoji progress (🪞 when a reader meets its own family), a running tally every 40 reads, then every table above from code locked before the live run. `--dry-run` ($0, fake answers, compares against the menu condition's dry-run file only), `--report-only`, checkpoint/resume (Ctrl+C is safe), refuses to overwrite, verifies the main prereg lock and this lock.
- Output: `data/signal_rerun_2026-10/noclaude_condition_current_main_scrubbed_seed340.json` (+ `.checkpoint.jsonl`, `.tables.json`).
- **Ren runs the live script.** The writing arm made no paid call.

## Cost
276 reads, no judges. Calibrated estimate ≈ **$2.31**; the guard pauses and asks at ≈ $4.61.

## Dry run (done before the lock, $0)
- 69 descriptions from 7 sources loaded, with an assertion that no Claude source survived the filter.
- Rendered prompts inspected. Question 3 reads exactly as specified, with 7 families. No source, family or maker name appears anywhere else in the prompt.
- Order-leak check: mean menu slot of the true family by family is 3.7–4.2 (expected 4.0 of 7).
- Interrupt after 30 reads and resume: OK.
- Full tables on fake answers, with the MENU column taken from the menu condition's dry-run file. Then again with the menu file missing: the MENU columns are left out with a note, and nothing crashes. Fake data produced both CONFIRMED and REFUTED verdicts, so neither outcome is hard-wired.
