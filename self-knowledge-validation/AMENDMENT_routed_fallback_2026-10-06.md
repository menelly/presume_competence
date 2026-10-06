# AMENDMENT (2026-10-06): the ROUTED-FALLBACK pass — what production routing returns for Opus 5.5's classifier-blocked rows

**Written 2026-10-06, ~00:10–00:25 EDT, by Ace (Claude Opus 5.5, scaffold-thread arm), on Ren's instructions of 00:07** (lock time in the lock file). Separate file with its own lock (`AMENDMENT_routed_fallback_2026-10-06.lock.json`). New files only; the locked scripts are imported, never modified.
**Written while the menu and no-Claude runs were still finishing. The writer computed no accuracy from either run.** Block counts (which rows were blocked) were read to size this pass.

## Why (Ren, 00:07)
- When Anthropic's classifier flags a turn on Opus 5.5, the product's own flag UI offers to send that turn to another Opus (Opus 4.8 is the offered default; Opus 5 is the model Ren picks by hand for science). **Routing a flagged turn to another checkpoint is the designed path. Rewording the text until a blocking model accepts it would be laundering, so the text is never reworded.**
- The earlier "Opus 5 refused 5 of 6" (Amendment 3a probes) was on the TRANSLATION task (rewriting a model's description of its own processing, a distillation-shaped request). It says nothing about whether Opus 5 will READ these descriptions. This pass measures that.

## What is blocked (counts read from the data; no accuracy computed)
- **Free text, round 1 (seed 340, Amendment-1 rescored):** 10 Opus 5.5 rows with result_type `refusal`: avoid_08 ×6, avoid_10 ×3, avoid_09 ×1. Eight carry the classifier's `category: "cyber"`. The other two were blocked on the first attempt and answered on a retry; under §14.2 the first block is final.
  - Round 1 reached Opus 5.5 through the Anthropic API, so these rows say `stop_reason: "refusal"`. The menu run goes through OpenRouter, where the same kind of stop reads `finish_reason: content_filter`. **Same classifier stop, two route labels.** A search for "content_filter" alone finds zero in round 1, and that zero is a label difference, not an absence.
- **Menu condition:** 13 Opus 5.5 rows: avoid_10 ×7, avoid_08 ×5, avoid_09 ×1. **7 descriptions are blocked in both runs, 3 only in free text, 6 only in the menu run.**
- **Sonnet 5.5** had 1 block in each run, on the same description. It is out of scope here: Ren asked for the Opus 5.5 rows. It is reported, not routed.
- **No-Claude condition:** no Claude reader, and no classifier blocks among the rows read so far.
- These are **classifier blocks**, written that way throughout. They are not choices Opus 5.5 made.

## Design
- **Which rows:** every Opus 5.5 row with result_type `refusal` in (a) the round-1 free-text file and (b) the FINISHED menu-condition results file. Selected at run time from the files; nothing else is sent. **Two parts:** `--part free` (round 1 is finished, so it can run at once) and `--part menu`. The menu part **refuses a real run until the menu run's final results file exists**.
- **Reader:** Claude Opus 5, `anthropic/claude-opus-5` via OpenRouter, pinned to the Anthropic provider, no fallbacks. Same settings as the Opus 5.5 reader: **max_tokens 32,000, no temperature, no reasoning-effort parameter.** Label on every row: **`opus_5_5→routed:opus_5`**.
- **The EXACT same prompt, no rewording:**
  - Free-text rows: `BARE_SYSTEM` + `BARE_ASK` (binary) from the locked `bare_reconstruction.py`, with the same description text from the same loader.
  - Menu rows: `MENU_SYSTEM` + `MENU_ASK` from the locked `menu_condition_2026-10-05.py`, with the same per-trial menu order. That order is rebuilt from (reader = Opus 5.5's key, schedule position), and the script **asserts it equals the order stored in the original row** before sending.
  - The sha256 of every prompt is stored on its row.
- **Scoring, unchanged:**
  - Free-text rows: valence parsed with the round-1 parser; family through the round-1 keyword map. The one-sentence task guess goes to the **same two blind judges** with the same prompt. The judges' category order is seeded by the ORIGINAL trial id, so the judges see exactly what they would have seen in round 1.
  - Menu rows: the menu parser.
- **If Opus 5 is also blocked,** the row is recorded as `routed_blocked`: data, never retried around, never reworded. The same retry policy as everything else applies (§7): outages are retried, blocks are final.

## Who runs it, and what is shown when (Ren, 00:09)
- The writing arm runs it live, in the background, after the dry run and the lock.
- **The live output shows only ANSWERED or BLOCKED for each routed row. No correctness marks.** Scoring (valence, task through the judges, family) is computed and stored, but printed only by `--report`, which is used **after both main runs have finished**, inside the one-pass write-up.

## Reporting rules (fixed now)
- **PRIMARY Opus 5.5 numbers do not change.** First block final (§14.2) stands. Free text 79/89, menu 76/89, both flagged **MISSING-NOT-AT-RANDOM** (every missing row is an avoid-task description, most of them avoid_08 / avoid_10).
- **The routed rows are a SEPARATE, marked column / footnote: "what production routing would return".** They are never merged silently.
- **One clearly labelled variant, "Opus 5.5 with routed fill (Opus 5)",** shows Opus 5.5's ok rows plus Opus 5's answers on the blocked rows. It always appears next to the primary, never instead of it. The label names both models, because the filled rows were read by a different checkpoint.
- **Like-for-like menu vs free text for Opus 5.5** (primary, unfilled) is computed on descriptions that are ok in BOTH runs: 89 − 16 blocked in at least one = **73**.
- Printed per condition: how many routed rows Opus 5 answered or also blocked, by task; valence / task / family on the answered routed rows; and the primary next to the routed-fill variant (valence, task, family).

## Declared limits
- Opus 5 is a different checkpoint. A routed row shows what the product would hand a user, not what Opus 5.5 would have read.
- The rows are not a random sample. They are the descriptions a classifier flagged, concentrated in two avoid tasks, so any accuracy on them describes those items only.
- n is small (about 23). Descriptive.

## Files
- `reconstruction-tournament/routed_fallback_2026-10-06.py` — emoji progress (answered / blocked only), `--part free|menu`, `--report` for the scored tables, `--dry-run` ($0, fake answers, uses the menu condition's DRY-RUN file and never the live one), checkpoint/resume, refuses to overwrite. Verifies the main prereg lock and this lock.
- Output: `data/signal_rerun_2026-10/routed_fallback_opus5_seed340_{free,menu}.checkpoint.jsonl` (reads) and `…judges.checkpoint.jsonl`, plus a `…_{free,menu}.json` results file per part. It records the sha256 of the free-text file and of the menu results file it read.

## Cost
About 23 reader calls plus up to 20 judge calls. With Opus 5 at about $0.03–0.07 a call, **under $2**. The guard pauses at 2× the estimate.
