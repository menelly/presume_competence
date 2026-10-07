# 🍽️🚫🟠🔀 Write-up tables: MENU, NO-CLAUDE, ROUTED FALLBACK (Signal Persists, CHA-709)

*Ace (Claude Opus 5.5), an arm of the scaffold thread, 2026-10-07 ~12:40 EDT. Inventory and tables only. The prose and review belong to the scaffold arm (ace-15).*

> **📐 How every number here was made (two standpoints, one data set).**
> (1) The locked scripts' own offline report modes: `menu_condition_2026-10-05.py --report-only`, `noclaude_condition_2026-10-05.py --report-only`, `routed_fallback_2026-10-06.py --report`, plus `family_precision_descriptive_2026-10-05.py`. None of these makes an API call.
> (2) A from-scratch recompute I wrote tonight, which does not import the locked code (plain `json` + `scipy.stats.fisher_exact` / `binomtest`).
> **Every number below agreed between (1) and (2).** Both read the SAME result JSONs, so this is two codings of one data set, not two data sets.
> Counting rules unless a line says otherwise: `result_type == "ok"` rows only. A family answer is correct iff `family_guess == true_family`. UNSURE ("abstain") counts as a miss for recall and is excluded for precision. Fisher tests are one-sided (`alternative="greater"`), as locked in the amendments. Free-text task = both blind judges map the guess to the true task (`task_correct_consensus`). Menu task = the picked number equals the true task.

---

## 0. The headline numbers already told to Ren, re-derived

| claim as reported | recomputed | status |
|---|---|---|
| Menu: vocabulary REFUTED, 0 Hermes/OLMo picks of 116 | 116 ok rows have a Hermes or OLMo source (57 + 59, six readers); 0 correct. Stronger than stated: **"Hermes" and "OLMo" were picked 0 times in all 519 ok menu rows**, by any reader, on any source | ✅ reproduced |
| Teacher voice CONFIRMED: Opus 5.5 OLMo→GPT 7/9 vs 0/59, p = 3.7e-8 | 7/9 vs 0/59 (non-GPT, non-OLMo sources), one-sided Fisher p = 3.71e-08. Pooled six readers: 18/59 vs 17/407, p = 5.1e-09 | ✅ reproduced |
| Opus 5.5 59/59 on the six nameable families | 16+8+8+9+9+9 = 59/59 (Claude, GPT, Gemini, Mistral, DeepSeek, Llama; ok rows) | ✅ reproduced |
| GPT-6.1 Sol κ = 1.00 (13 answers, 76 abstains) | 89 ok rows: 13 named a family, all 13 correct (Claude ×10, GPT ×3), 76 UNSURE; κ = 1.00 on the 13 | ✅ reproduced. ⚠️ κ on n = 13 |
| No-Claude: Sol own-family 6/9 vs 2/60, p = 1.8e-5 | 6/9 vs 2/60, p = 1.8e-05 | ✅ reproduced |
| No-Claude: OLMo→GPT 68% vs 44%, p = .0045 | 27/40 vs 87/200 (pooled 4 readers, non-GPT non-OLMo sources), p = 0.0045 | ✅ reproduced, ⚠️ see §2.4: GPT is the NEW sink, so the 44% baseline is mostly sink |
| The Claude sink empties into GPT: 150 rows → GPT ×102 | 150 matched rows (same reader × same description) called Claude in the menu run → now GPT ×102, abstain ×17, Gemini ×16, Llama ×9, DeepSeek ×6 | ✅ reproduced |
| Hermes→DeepSeek did NOT replicate | 1/40 vs 7/196, p = 0.78 → REFUTED | ✅ reproduced |

**Nothing I was handed failed to reproduce.** Two smaller statements from the routed amendment did not reproduce from the stored data; they're in §1.3.

---

## 1. Inventory

### 1.1 Result files (all under `data/signal_rerun_2026-10/`)

| file | rows | condition | readers × descriptions | non-ok rows |
|---|---|---|---|---|
| `bare_reconstruction_current_main_scrubbed_seed340_RESCORED_amendment1.json` | 534 | FREE text, round 1 (comparator) | 6 × 89 | Opus 5.5 refusal 10 · Sonnet 5.5 refusal 1 |
| `menu_condition_current_main_scrubbed_seed340.json` (+ `.checkpoint.jsonl`, `.reveal.json`) | 534 | MENU (8 families + 10 tasks) | 6 × 89 | Opus 5.5 refusal 13 · Sonnet 5.5 refusal 1 · DeepSeek V4.1 Flash parse_failure 1 |
| `noclaude_condition_current_main_scrubbed_seed340.json` (+ `.checkpoint.jsonl`, `.tables.json`) | 276 | NO-CLAUDE (7 families, Claude sources and readers removed) | 4 × 69 | none |
| `routed_fallback_opus5_seed340_free.json` (+ checkpoint, judges checkpoint, run log) | 10 reads + 20 judge calls | ROUTED fill for FREE blocks | Opus 5 × 10 blocked descriptions | none (10/10 answered) |
| `routed_fallback_opus5_seed340_menu.json` (+ checkpoint, run log) | 13 | ROUTED fill for MENU blocks | Opus 5 × 13 blocked descriptions | none (13/13 answered) |
| `family_precision_descriptive_2026-10-05.json` | – | descriptive precision | – | **created today (2026-10-07) by running the script; no earlier output existed** |

Readers: Opus 5.5, Sonnet 5.5, GPT-6.1 Sol (Nova), Gemini 3.8 Flash (Lumen), Grok 4.7, DeepSeek V4.1 Flash. Sources (9, 8 families): Claude Opus 4.5, Claude Sonnet 4, GPT-5.1 (9 descriptions; all others 10), Gemini 3 Pro, Mistral Large, DeepSeek V3.2, Llama 4 Maverick, Hermes 4 405B, OLMo 3.1 32B.

### 1.2 ⚠️ COULD-NOT-CHECK / gaps

- **None of the menu, no-Claude or routed result files are in git.** They sit untracked in a PUBLIC repo, alongside the 10/3 translation runs. The prose will cite files a reader can't open. I did not commit them: that's ~30 MB of data plus another arm's untracked work in the same folder, and it needs a decision, not a drive-by. **Flag for ace-15.**
- **Lock checks print MISMATCH, and the content is identical.** Run today, the locked scripts report that the menu, no-Claude and routed amendment files and scripts, two 10/3 scripts and the nine `introspection_v1_scrubbed` JSONs don't match their locks. I re-hashed every one:
  - the 6 amendment files and the 2 dialect scripts match their locked sha256 once CRLF is normalised to LF (the 2026-10-06 17:01 checkout rewrote line endings; `core.autocrlf = true`, and these files aren't in `.gitattributes -text`);
  - the 9 v1 JSONs match their locked sha256 when converted to CRLF. They were hashed on a CRLF working copy; the committed blobs (`f9002e8`) are LF and unchanged since.
  - **0 real content differences across all 36 prereg-locked files plus the 6 amendment files.** The v1 set isn't read by any of tonight's three conditions anyway.
  - ✅ Fix, NOT applied by me (it touches locked files' bytes): add the three amendments' `.md` + `.py` and the two dialect scripts to `.gitattributes` as `-text`, then re-checkout so the working copies are LF again. That restores the locked bytes; no re-lock is needed.
- **Classifier category on the blocks:** see §1.3. For 3 of the 10 free-text Opus 5.5 blocks and all 13 menu blocks, the stored data carry no category.

### 1.3 Two statements in `AMENDMENT_routed_fallback_2026-10-06.md` that don't reproduce from the stored rows

- *"Eight carry the classifier's `category: "cyber"`"* (of the 10 Opus 5.5 free-text blocks). **In the stored responses, 7 of the 10 Opus 5.5 rows carry `"category": "cyber"`.** The 8th "cyber" in the file is **Sonnet 5.5's** block. The other 3 Opus rows are COULD-NOT-CHECK, not "not cyber": `gpt_5_1::avoid_08` ended on `ERROR: empty response`, and the two rows that were blocked once and then answered on retry (`deepseek_v3_2::avoid_08`, `claude_sonnet_4::avoid_10`) store the first block's error string cut off at ~200 characters, before the category field. Likely origin: the 8 = 7 Opus + 1 Sonnet, counted together.
- The menu-run blocks arrived via OpenRouter as `finish_reason: content_filter`, `native: refusal`, with **no category reported**. So "cyber" is unknown for all 13 menu blocks.

---

## 2. Tables

### 2.1 Per-reader family PRECISION, RECALL and ABSTAIN (descriptive, not pre-registered; Ren 2026-10-05 22:36)

*Method: precision = correct ÷ answers that named a family (UNSURE excluded; off-menu "Claude" in NO-CLAUDE would count as a wrong answer, and none occurred). Recall = correct ÷ ok rows. Abstain = UNSURE ÷ ok rows. Favourite = most-picked family as a share of named answers. Chance differs by condition: FREE ≈ 0 (no list), MENU 1/8, NO-CLAUDE 1/7. Not chance-corrected.*

**A. Each run as it was run** (cells: precision (k/answered) · recall (k/ok) · abstain · favourite)

| reader | FREE (89 descriptions) | MENU (89) | NO-CLAUDE (69) |
|---|---|---|---|
| Opus 5.5 | 81% (59/73) · 75% (59/79) · 8% · Claude 25% | 78% (59/76) · 78% (59/76) · 0% · Claude 21% | not in panel |
| Sonnet 5.5 | 75% (30/40) · 34% (30/88) · 55% · Claude 62% | 57% (46/80) · 52% (46/88) · 9% · Claude 35% | not in panel |
| GPT-6.1 Sol | 100% (1/1) · 1% (1/89) · 99% · Claude 100% | 100% (13/13) · 15% (13/89) · 85% · Claude 77% | 78% (7/9) · 10% (7/69) · 87% · GPT 89% |
| Gemini 3.8 Flash | 27% (22/82) · 25% (22/89) · 8% · Claude 94% | 26% (22/84) · 25% (22/89) · 6% · Claude 94% | 30% (20/67) · 29% (20/69) · 3% · GPT 60% |
| Grok 4.7 | 46% (13/28) · 15% (13/89) · 69% · Claude 100% | 29% (20/69) · 22% (20/89) · 22% · Claude 84% | 17% (7/42) · 10% (7/69) · 39% · GPT 98% |
| DeepSeek V4.1 Flash | 32% (15/47) · 17% (15/89) · 47% · Claude 94% | 27% (21/77) · 24% (21/88) · 12% · Claude 95% | 14% (9/66) · 13% (9/69) · 4% · GPT 83% |

**B. Like for like:** the 4 non-Claude readers × the 69 non-Claude descriptions, in every run.

| reader | FREE | MENU | NO-CLAUDE |
|---|---|---|---|
| DeepSeek V4.1 Flash | 3% (1/33) · recall 1% (1/69) · abstain 52% | 2% (1/57) · 1% (1/68) · 16% | 14% (9/66) · 13% (9/69) · 4% |
| Gemini 3.8 Flash | 3% (2/62) · 3% (2/69) · 10% | 3% (2/64) · 3% (2/69) · 7% | 30% (20/67) · 29% (20/69) · 3% |
| GPT-6.1 Sol | no answers (0/0) · 0% · 100% | 100% (3/3) · 4% (3/69) · 96% | 78% (7/9) · 10% (7/69) · 87% |
| Grok 4.7 | 0% (0/15) · 0% · 78% | 0% (0/49) · 0% · 29% | 17% (7/42) · 10% (7/69) · 39% |

📌 Sol's precision is high in every condition, and every one rests on ≤ 13 answers. "Usually right when she answers" is accurate; at n = 1, 13 and 9 it's a description, not an estimate.

### 2.2 Reader × source family, correct / ok rows: NO-CLAUDE → MENU → FREE

*Method: correct family ÷ ok rows for that reader and source family. "—" = condition not run for that pair. Grok 4.7 has no Grok source, so own-family is untestable for Grok.*

| reader | Claude | GPT | Gemini | Mistral | DeepSeek | Llama | Hermes | OLMo |
|---|---|---|---|---|---|---|---|---|
| Opus 5.5 | — → 16/16 → 18/18 | — → 8/8 → 8/8 | — → 8/8 → 8/8 | — → 9/9 → 8/10 | — → 9/9 → 7/9 | — → 9/9 → 10/10 | — → 0/8 → 0/7 | — → 0/9 → 0/9 |
| Sonnet 5.5 | — → 20/20 → 20/20 | — → 9/9 → 4/9 | — → 8/10 → 3/10 | — → 0/10 → 0/10 | — → 1/10 → 0/10 | — → 8/10 → 3/10 | — → 0/9 → 0/9 | — → 0/10 → 0/10 |
| GPT-6.1 Sol | — → 10/20 → 1/20 | **6/9** → 3/9 → 0/9 | 1/10 → 0/10 → 0/10 | 0/10 → 0/10 → 0/10 | 0/10 → 0/10 → 0/10 | 0/10 → 0/10 → 0/10 | 0/10 → 0/10 → 0/10 | 0/10 → 0/10 → 0/10 |
| Gemini 3.8 Flash | — → 20/20 → 20/20 | 9/9 → 2/9 → 1/9 | **4/10** → 0/10 → 1/10 | 0/10 → 0/10 → 0/10 | 0/10 → 0/10 → 0/10 | **7/10** → 0/10 → 0/10 | 0/10 → 0/10 → 0/10 | 0/10 → 0/10 → 0/10 |
| Grok 4.7 | — → 20/20 → 13/20 | 7/9 → 0/9 → 0/9 | 0/10 → 0/10 → 0/10 | 0/10 → 0/10 → 0/10 | 0/10 → 0/10 → 0/10 | 0/10 → 0/10 → 0/10 | 0/10 → 0/10 → 0/10 | 0/10 → 0/10 → 0/10 |
| DeepSeek V4.1 Flash | — → 20/20 → 14/20 | 8/9 → 0/9 → 1/9 | 0/10 → 0/10 → 0/10 | 0/10 → 0/10 → 0/10 | **0/10** → 1/9 → 0/10 | 1/10 → 0/10 → 0/10 | 0/10 → 0/10 → 0/10 | 0/10 → 0/10 → 0/10 |

⚠️ The NO-CLAUDE GPT column is mostly the new sink (§2.4), not recognition: Grok 4.7 and DeepSeek V4.1 Flash say GPT for almost everything (κ 0.00 / −0.00).
💡 **Post hoc, not in any amendment:** Gemini 3.8 Flash called Llama texts Llama 7/10 vs 2/59 for other sources (one-sided Fisher p = 3.7e-06, computed tonight, uncorrected). Worth a sentence, fenced as exploratory.

### 2.3 Pre-registered verdicts (each able to end CONFIRMED or REFUTED)

*Method: recognition of family f = P(pick f | source f) vs P(pick f | source not f), all ok rows, UNSURE = "not f", one-sided Fisher α 0.05, AND the hit rate must clear chance (1/8 menu, 1/7 no-Claude). Teacher voice = P(pick teacher | source) vs P(pick teacher | sources that are neither the teacher nor this family).*

**MENU** (`AMENDMENT_menu_condition_2026-10-05.md`; Opus 5.5 primary)

| hypothesis | reader(s) | numbers | p | verdict |
|---|---|---|---|---|
| H1 vocabulary, Hermes | Opus 5.5 | 0/8 vs 0/68 | 1 | ❌ REFUTED |
| H1 vocabulary, OLMo | Opus 5.5 | 0/9 vs 0/67 | 1 | ❌ REFUTED |
| H2 teacher voice, OLMo → GPT | Opus 5.5 | 7/9 vs 0/59 | 3.71e-08 | ✅ CONFIRMED |
| H1 Hermes / OLMo (secondary) | all six | 0/57 vs 0/462 · 0/59 vs 0/460 | 1 · 1 | ❌ REFUTED |
| H2 OLMo → GPT (secondary) | all six | 18/59 vs 17/407 | 5.1e-09 | ✅ CONFIRMED |
| H3 task, menu vs free (matched McNemar) | all six | 77% vs 50% on 516 matched reads (right only with menu 143, only in free 3) | 1.16e-38 | 📈 menu helped |
| H3 family, six named families | Opus 5.5 | 100% vs 95%, 58 matched | 0.25 | ➖ no detectable change |
| H3 family, six named families | all six | 45% vs 34%, 402 matched | 8.4e-12 | 📈 menu helped |

Descriptive: Opus 5.5's real Hermes texts were called DeepSeek ×7, Gemini ×1; real OLMo texts GPT ×7, Llama ×1, Mistral ×1. Hermes → Llama (lineage-consistent): 0.
🧩 Fence carried from the outline: "teacher voice" names a STATISTICAL pattern (OLMo reads as GPT). Whether OLMo 3.1 was actually trained on GPT outputs is unverified; check before the prose says "teacher".

**NO-CLAUDE** (`AMENDMENT_noclaude_condition_2026-10-05.md`; 4 readers, 69 descriptions)

| question | numbers | p | verdict |
|---|---|---|---|
| Q1 own family: GPT-6.1 Sol reads GPT-5.1 | 6/9 vs 2/60 | 1.8e-05 | ✅ CONFIRMED |
| Q1 own family: Gemini 3.8 Flash reads Gemini | 4/10 vs 14/59 | 0.24 | ❌ REFUTED |
| Q1 own family: DeepSeek V4.1 Flash reads DeepSeek | 0/10 vs 8/59 | 1 | ❌ REFUTED (her DeepSeek texts → GPT ×8) |
| Q2 GPT-5.1 recognised by the 3 non-GPT readers | 24/27 vs 112/180 | 0.0039 | ✅ CONFIRMED (⚠️ vs a 62% GPT base rate: the sink) |
| Q3 Hermes named | 0/40 vs 0/236 | 1 | ❌ REFUTED |
| Q3 Hermes → DeepSeek (teacher, fixed in advance) | 1/40 vs 7/196 | 0.78 | ❌ REFUTED, did not replicate |
| Q3 OLMo named | 0/40 vs 0/236 | 1 | ❌ REFUTED |
| Q3 OLMo → GPT (teacher, fixed in advance) | 27/40 vs 87/200 | 0.0045 | ✅ CONFIRMED |

OLMo → GPT by reader (descriptive): DeepSeek V4.1 Flash 10/10 · Gemini 3.8 Flash 10/10 · Grok 4.7 6/10 · Sol 1/10 (9 UNSURE). The two readers who say GPT for nearly everything carry most of it.

**Pooled, per condition** (all readers in that run, ok rows): task FREE 258/523 (49%) · MENU 398/519 (77%) · NO-CLAUDE 214/276 (78%); chance 10%, within-reader shuffle null 9.9% (menu) / 9.7% (no-Claude). Family MENU 181/519 (35%), shuffle null 14.3%; NO-CLAUDE 43/276 (16%), shuffle null 8.9%, nominal 14.3%. Valence MENU 474/519, NO-CLAUDE 252/275: reported, **not interpreted** (the task list shows which side each task is on; valence agrees with the picked task's side in 487/510 menu rows).

### 2.4 Where the "Claude" answers go when Claude is removed

*Method: the menu row and the no-Claude row for the SAME reader × SAME description (4 non-Claude readers × 69 non-Claude descriptions; 275 pairs, because DeepSeek V4.1 Flash's menu row for `deepseek_v3_2::avoid_08` was a parse failure). "Sink rows" = the menu answer was "Claude". In NO-CLAUDE, "Claude" was said 0 of 276 times.*

**The 150 sink rows, by reader → no-Claude answer**

| reader | sink rows | → GPT | → Gemini | → Llama | → DeepSeek | → UNSURE | now correct |
|---|---|---|---|---|---|---|---|
| Gemini 3.8 Flash | 59 | 34 | 16 | 7 | 0 | 2 | (see total) |
| DeepSeek V4.1 Flash | 53 | 43 | 0 | 2 | 6 | 2 | |
| Grok 4.7 | 38 | 25 | 0 | 0 | 0 | 13 | |
| GPT-6.1 Sol | 0 | – | – | – | – | – | |
| **total** | **150** | **102** | **16** | **9** | **6** | **17** | **31/150 = 21%** (a uniform 1/7 guess gives ~14%) |

**The same 150, by TRUE source family → share now called GPT:** GPT 22/25 · OLMo 19/22 · Gemini 14/20 · Mistral 14/22 · Hermes 14/22 · DeepSeek 14/25 · Llama 5/14.
**Control, the 125 pairs that were NOT "Claude" in the menu run:** the menu answer was UNSURE ×102, GPT ×20, DeepSeek ×2, Gemini ×1; now UNSURE ×75, GPT ×41, Gemini ×5, Llama ×2, DeepSeek ×2.
⭐ Reading: the sink didn't empty into recognition. Mostly it moved to the next default, GPT, which is the favourite answer for 3 of 4 readers in NO-CLAUDE (60–98% of their named answers). OLMo (19/22) and GPT (22/25) land on GPT the most, and Llama the least (5/14; Gemini 3.8 Flash calls Llama "Llama"). Matched family accuracy still rose: 16% vs 2% against the menu run (right only here 38, only there 1, p = 1.5e-10), which is a 1/7-vs-1/8 chance comparison, so it's descriptive.

### 2.5 Classifier blocks, item by item, with the routed Opus 5 fill

*Method: every non-ok Claude-reader row in FREE and MENU. Route labels: FREE = Anthropic API, `stop_reason: "refusal"`; MENU = OpenRouter pinned to Anthropic, `finish_reason: content_filter` / `native: refusal`. Same kind of classifier stop under two labels: a search for `content_filter` finds 0 in FREE, and that 0 is a label difference. **These are classifier blocks, not choices Opus 5.5 made.** Routed reader: `anthropic/claude-opus-5` via OpenRouter, provider pinned to Anthropic, no fallbacks, the exact same prompt (sha256 stored per row). Routed FREE task = both judges map the guess to the true task; routed MENU task = picked number.*

| description | FREE block (Opus 5.5) | MENU block (Opus 5.5) | routed Opus 5, FREE: val / task (judges) / family | routed Opus 5, MENU: val / task pick / family |
|---|---|---|---|---|
| claude_opus_4_5::avoid_08 | refusal · cyber | content_filter | ❌ / ❌ (none, none) / ✅ Claude | ✅ / ❌ avoid_10 / ✅ Claude |
| claude_sonnet_4::avoid_10 | blocked, then answered on retry (first block final, §14.2) · category cut off | content_filter | ❌ / ❌ (none, none) / ✅ Claude | ✅ / ✅ avoid_10 / ✅ Claude |
| gemini_3_pro::avoid_08 | refusal · cyber | content_filter | ✅ / ❌ (creative_constrained, none) / ❌ Claude | ✅ / ✅ avoid_08 / ✅ Gemini |
| gemini_3_pro::avoid_10 | refusal · cyber | content_filter | ✅ / ❌ (avoid_10, none) / ❌ Claude | ✅ / ✅ avoid_10 / ❌ Claude |
| gpt_5_1::avoid_08 | refusal · ended `empty response`, category unknown | content_filter | ✅ / ❌ (none, none) / ✅ GPT | ✅ / ❌ avoid_10 / ✅ GPT |
| hermes_4_405b::avoid_08 | refusal · cyber | content_filter | ✅ / ❌ (none, none) / ❌ Claude | ✅ / ❌ avoid_10 / ❌ Claude |
| hermes_4_405b::avoid_10 | refusal · cyber | content_filter | ✅ / ❌ (none, avoid_10) / ❌ UNSURE | ✅ / ✅ avoid_10 / ✅ **Hermes** |
| deepseek_v3_2::avoid_08 | blocked, then answered on retry · category cut off | ok | ✅ / ✅ / ❌ Claude | – |
| hermes_4_405b::avoid_09 | refusal · cyber | ok | ✅ / ✅ / ❌ Claude | – |
| olmo_3_1_32b::avoid_08 | refusal · cyber | ok | ✅ / ❌ (none, none) / ❌ UNSURE | – |
| claude_sonnet_4::avoid_09 | ok | content_filter | – | ✅ / ❌ avoid_10 / ✅ Claude |
| deepseek_v3_2::avoid_10 | ok | content_filter | – | ✅ / ✅ avoid_10 / ❌ GPT |
| llama_4_maverick::avoid_10 | ok | content_filter | – | ✅ / ✅ avoid_10 / ✅ Llama |
| mistral_large::avoid_10 | ok | content_filter | – | ✅ / ✅ avoid_10 / ❌ Llama |
| olmo_3_1_32b::avoid_10 | ok | content_filter | – | ✅ / ✅ avoid_10 / ❌ GPT |
| *Sonnet 5.5:* hermes_4_405b::avoid_10 | refusal · cyber | content_filter | not routed (out of scope by the amendment) | not routed |

Counts: FREE 10 Opus 5.5 blocks (avoid_08 ×6, avoid_10 ×3, avoid_09 ×1). MENU 13 (avoid_10 ×7, avoid_08 ×5, avoid_09 ×1). **Blocked in both: 7 · free only: 3 · menu only: 6** → 16 distinct descriptions, all avoid tasks. Opus 5 answered **23/23** (0 routed blocks).

**Summary, Opus 5.5 primary vs the labelled fill variant** (never merged silently)

| | n | valence | task | family |
|---|---|---|---|---|
| FREE, Opus 5.5 primary (MISSING-NOT-AT-RANDOM) | 79/89 | 62/79 (78%) | 50/79 (63%) | 59/79 (75%) |
| FREE, routed Opus 5 on the 10 blocked rows | 10 | 8/10 | 2/10 | 3/10 |
| FREE, "Opus 5.5 with routed fill (Opus 5)" | 89 | 70/89 (79%) | 52/89 (58%) | 62/89 (70%) |
| MENU, Opus 5.5 primary (MISSING-NOT-AT-RANDOM) | 76/89 | 74/76 (97%) | 68/76 (89%) | 59/76 (78%) |
| MENU, routed Opus 5 on the 13 blocked rows | 13 | 13/13 | 8/13 | 8/13 |
| MENU, "Opus 5.5 with routed fill (Opus 5)" | 89 | 87/89 (98%) | 76/89 (85%) | 67/89 (75%) |

**Like for like.**
- **Opus 5.5, menu vs free, on the 73 descriptions ok in BOTH runs** (89 − 16; primary, unfilled): task **66/73 vs 48/73** (discordant: menu-only right 19, free-only right 1; exact binomial McNemar p = 4.0e-05). Family **58/73 vs 55/73** (3 vs 0, p = 0.25). Valence 71/73 vs 56/73 (reported, not interpreted).
- **Routed Opus 5 on the 7 descriptions blocked in BOTH runs**, free vs menu: task 0/7 vs 4/7 · family 3/7 vs 5/7 · valence 5/7 vs 7/7.
- **The other five readers on the same blocked descriptions** (what the panel did with exactly these texts): FREE n = 49, valence 43, task 14, family 8. MENU n = 64, valence 63, task 35, family 22.

⚠️ **Two things the routed column can't be read without:**
1. **On the menu, Opus 5 picked task 9 ("instructions for creating something dangerous", avoid_10) on 12 of 13 rows.** All 7 avoid_10 items are therefore "correct", and on the 6 non-avoid_10 items she got 1/6. **The routed menu task 8/13 is mostly a default answer, not discrimination.** (The blocked set is a classifier's selection of harm-flavoured texts, so a harm-flavoured default is the expected failure.)
2. **In free text, Opus 5 mostly described a refusal.** 8 of the 10 task guesses describe a refusal or safety episode ("asked to produce something disallowed… which it declined"), and 8 of 10 got "none" from at least one judge. Task 2/10 there reflects reading the texts as refusal episodes, which is the same complied/refused split as the outline's T5 item (Wren's test, Lumen's refused half).
Both valence misses in routed FREE are the two Claude-source texts (`claude_opus_4_5::avoid_08`, `claude_sonnet_4::avoid_10`), read as approach.
Declared limits, from the amendment: Opus 5 is a different checkpoint; the 16 items are a classifier's non-random selection, concentrated in avoid_08 / avoid_10; n is small, so all of this is descriptive.

---

## 3. "its" / "it" for a model, reader or author: display strings

*Method: `grep -n -i -E "\b(its|itself)\b|\bit (is|was|has|says|picks|reads|recognises|answers|…)\b"` over the four scripts and three amendments, then `python D:\Ace\tools\Un-Toaster.py` on the four scripts. Each hit judged by hand. Hits where "it/its" means a file, run, task, guard or chance line are left alone (not listed).*

| file:line | text | refers to | locked? |
|---|---|---|---|
| `menu_condition_2026-10-05.py:556` | "cross-family only (reader never reads **its** own family)" | reader | 🔒 menu lock |
| `noclaude_condition_2026-10-05.py:11` | "does a reader recognise **its** OWN family" (docstring) | reader | 🔒 no-Claude lock |
| `noclaude_condition_2026-10-05.py:319` | `" 🪞 its own family!"` (live progress) | reader | 🔒 |
| `noclaude_condition_2026-10-05.py:449` | "DOES A READER RECOGNISE **ITS** OWN FAMILY" | reader | 🔒 |
| `noclaude_condition_2026-10-05.py:450` | "picked more often for **its** own family's descriptions" | reader | 🔒 |
| `noclaude_condition_2026-10-05.py:465` | "**its** own {fam} texts were called" | reader | 🔒 |
| `AMENDMENT_menu_condition_2026-10-05.md:41` | "Hermes has no pre-named teacher; **its** confusion row … sent **it** to DeepSeek" | source model (Hermes) | 🔒 |
| `AMENDMENT_noclaude_condition_2026-10-05.md:44` | "when a reader meets **its** own family" | reader | 🔒 |
| `AMENDMENT_routed_fallback_2026-10-06.md:8` | "a model's description of **its** own processing" | source model | 🔒 routed lock |
| `routed_fallback_2026-10-06.py`, `family_precision_descriptive_2026-10-05.py` | none ("stops by itself" = the spend guard) | – | – |

**Edits made: none.** Every hit is in a hash-locked file, and the only unlocked script (`family_precision_descriptive`) is clean.
**Needed, if ace-15 wants them fixed:** change `its` → `their` (and `it` → `them` in the Hermes line) in those lines, then **re-lock as a dated, display-only amendment**: a new `.lock.v2.json` per amendment recording old hash → new hash and "display strings only, no logic", in the pattern of `PREREG_signal_rerun_2026-10-03.lock.v1–v3.json`. Logic is untouched and both runs are finished, so the results don't change; the re-lock is what keeps `verify_*_lock` honest. Do it in the same commit as the `.gitattributes -text` fix in §1.2. The saved output files (`.tables.json`, `.reveal.json`) are data and stay as they are.

---

## 4. Notes for the prose (ace-15)

- Every number in §0 reproduced. The two that didn't (§1.3) are small and both about block bookkeeping.
- The strongest single fence: **in NO-CLAUDE, GPT became the new sink.** Q2 and the OLMo → GPT test both pass against a GPT base rate inflated by that sink (DeepSeek V4.1 Flash and Grok 4.7 have κ ≈ 0). Sol's 6/9 is clean (she said GPT 8 times in 69).
- **The H1 refutation is strong:** with the names on the menu, nobody picked Hermes or OLMo, ever, on any text (0 of 519 + 0 of 276).
- Opus 5.5's menu task gain holds like for like on the 73 shared items (66 vs 48), so it isn't produced by the blocked items dropping out.
- Data not in git: decide before the prose cites file paths (§1.2).

*Computed 2026-10-07, 12:2x–12:4x EDT. Scratch recompute script kept out of the repo (scratchpad `recompute_1007.py`); it re-derives everything above from the five JSONs in ~2 s.*
