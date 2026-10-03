# AMENDMENT 3a to PREREG_signal_rerun_2026-10-03.md: new phenomenology translators, replication, refusal fill-ins

**Written 2026-10-03, ~19:00–19:20 EDT, by Ace (Claude Opus 5.5), on Ren's instructions of 18:56, 18:58, 19:03 and 19:05.**
To be folded into the prereg as §16a once the Amendment-3 chain finishes. Until then it lives in this separate file with its own lock (`AMENDMENT_3a_2026-10-03.lock.json`); "Why a separate file" explains why.

## Timeline (EDT, 2026-10-03), stated plainly
| Time | Event |
|---|---|
| 18:50 | Real translation probe: Sonnet 5.5 refuses a benign GPT-5.1 description (§16.8). |
| 18:53 | Amendment 3 locked, committed and pushed (`6b39dc1`). |
| 18:55:40 | Ren pastes the Amendment-3 chain: translate → reconstruction A (mech) → reconstruction B (pheno) → comparison. |
| ~18:56–18:59:30 | The writer, not yet knowing the chain was live, edited two pinned Amendment-3 scripts on disk (`translate_dialects_2026-10-03.py`, `dialect_comparison_2026-10-03.py`) to add a fallback in place. Both were **restored to their exact committed bytes** at 18:59:30, and the main lock verifies (36/36). The running translate process had loaded the committed code at 18:55:40 and does not re-check the lock mid-run. No lock-verifying chain step ran in that window. |
| 18:56 / 18:58 | Ren: refused pheno items should still be translated by a Claude, via the API (blind), first Opus 5.5, then Opus 5 → **revised to Opus 5 directly**, because 5.5 shares the classifier blocking Sonnet. The fallback lives in **separate scripts**, so nothing the live chain uses is touched. |
| ~19:03 | Ren's terminal: Sonnet 5.5 refusing ~10 of the first 14 pheno items, **across every source family, benign tasks included**. That looks like the task shape, not content. Ren's unverified guess: an anti-distillation safeguard, i.e. "rewrite a model's description of its own processing". |
| ~19:04 | Writer's real probes (one item each, same blind prompt). **Opus 5 refused 5 of 6** (`content_filter`), including the 18:50 item. **Sonnet 4.6 translated 6 of 6**, served via Anthropic. |
| 19:05 | Ren's decision (below): Sonnet 4.6 PRIMARY, Opus 5 REPLICATION, mixed set and Sonnet 5.5 subset as sensitivity checks. |
| 19:06:27 | The Amendment-3 translation completes. Sonnet 5.5: **41 translated / 48 refused**. Lumen: **89 / 0**. |
| 19:06:30 | The chain's reconstruction A (mech, Lumen) starts. |
| ~19:15–19:20 | This document is finalized and the 3a lock written, **while reconstruction A was running.** |

- **The design decisions in this amendment (Ren, 19:05) predate every reconstruction call on translated data.**
- **The document was finalized after reconstruction A had started.** The writer has looked at none of its output: only file timestamps, and the first row's timestamp to date its start.
- Reconstruction B (pheno, Sonnet 5.5 subset) had not started.

## Why a separate file
- **The main prereg lock pins** the prereg and the Amendment-3 scripts byte for byte.
- **The chain's reconstruction steps re-verify that lock when they start.**
- **Editing the prereg or those scripts while the chain runs would make it fail.** So 3a adds new files only:
  - three scripts;
  - this document;
  - its own lock, which also records the main lock's sha256;
  - new data folders.
- **It imports** the locked Amendment-3 code (prompts, fidelity checks, classifier) and **never modifies it.**

## What changes: the phenomenological register (B)
**Why.** The observed refusal rate made the planned translator, Sonnet 5.5, unusable: she refused 48 of 89, on every source family. That was decided before any reconstruction results on translated data existed.

| Role | Set | Translator | Notes |
|---|---|---|---|
| **PRIMARY** | `pheno46` | **Claude Sonnet 4.6**, `anthropic/claude-sonnet-4.6`, OpenRouter pinned to Anthropic, temperature 0 | Ren: closest to the prereg's intent (a Sonnet doing phenomenology), and she predates the 5.5 classifier. Full set, all 89. |
| **REPLICATION** | `pheno_opus5` | **Claude Opus 5**, `anthropic/claude-opus-5`, pinned to Anthropic, temperature 0 | A second, independent phenomenology translator, to check whether the results are translator-specific. Full set, all 89. **Expect heavy loss:** 5 of 6 probe items refused. Refused items stay missing; only items she translates are read. |
| sensitivity | `pheno46_mixed` | Sonnet 4.6 + **Opus 5 for Sonnet 4.6's refusals** | One extra translator per refused item; if Opus 5 refuses too, the item stays missing. |
| sensitivity | the Amendment-3 pheno set | Sonnet 5.5 (41 items) | The chain's own reconstruction B, unchanged. |

**Same as Amendment 3, for every 3a translator:**
- the identical blind prompt (prompt sha256 recorded in each manifest);
- text only, via the API.
  - *API on purpose (Ren):* a house arm loads Ace's CLAUDE.md and can see the labelled data, so she would not be blind.
- max_tokens 32,000 with no reasoning-effort parameter;
- retry and refusal rules as in §7 / §14.2: a refusal is final for the model that gave it;
- the §16.3 fidelity checks (fill-in items are length-checked against their base set's distribution);
- the uniform header;
- a manifest per set that the loader verifies.

**Which translator produced each item** is recorded in each entry's `translation_meta` and in each fidelity report.

## What changes: the mechanistic register (A)
- **`mech_fb`:** for items Lumen refused, **Gemini 3.1 Pro** (`google/gemini-3.1-pro-preview`, temperature 0) is the single fill-in. Gemini 3.1 Pro shares Lumen's family, at a different checkpoint and tier.
- **Lumen refused 0 of 89, so `mech_fb` is a no-op.** The scripts say so and make no calls.
- **Probe:** Gemini 3.1 Pro translated the 18:50 item cleanly.

## Analysis (`fallback_comparison_2026-10-03.py`, read-only)
- **Per condition, against round 1 (cross-family primary slice, matched trials, seed 340):**
  - pooled valence, task and family (Wilson 95% CIs; family is confounded by the translator);
  - McNemar tests;
  - the **§16.5 midpoint verdicts P1/P2** in the primary and the no-flagged sensitivity analyses (UNSETTLED if they differ);
  - **⭐ the Nova (GPT-5.1) column, with a P3-style one-sided test, and that column's missing and fill-in counts;**
  - per-source tables with each set's missing (`-N`) and fill-in (`🪜N`) counts;
  - per-reader task.
- **Conditions:**
  - PRIMARY `pheno46`;
  - REPLICATION `pheno_opus5`;
  - `pheno46_mixed`, which merges the `pheno46` run with a run on the fill-in items only;
  - the Sonnet 5.5-only subset;
  - mech (the §16 primary);
  - `mech_fb`.
- **Translator agreement:** Sonnet 4.6 vs Opus 5 on the items both translated (McNemar).
- **Refusal rate by source family:** for every translator (table below; the comparison re-prints it from the checkpoints).
- **Relation to §16.**
  - **For pheno, the §16.5 hypotheses (P1 content vs style; the no-flagged rule) are now tested PRIMARILY on `pheno46`.**
  - Opus 5 is the replication check.
  - The mixed set and the Sonnet 5.5 subset are sensitivity checks.
  - A content claim for pheno needs `pheno46`'s primary and no-flagged verdicts to agree. Disagreement from the replication or the sensitivity sets is reported next to it, never hidden.
  - **Mech is unchanged:** §16's analysis and P3 stand.
  - **The chain's own `dialect_comparison_seed340.json`** (mech + the Sonnet 5.5 subset) is still produced and reported as it is.

## Observation: refusal rate by source family (Amendment-3 translation, complete; read from the checkpoints at 19:13)
| Translator | Claude | GPT | Gemini | Mistral | DeepSeek | Llama | Hermes | OLMo | All |
|---|---|---|---|---|---|---|---|---|---|
| Sonnet 5.5 (pheno, Amendment 3) | 6/20 | 5/9 | 5/10 | 9/10 | 7/10 | 4/10 | 7/10 | 5/10 | **48/89** |
| Lumen, Gemini 3.8 Flash (mech, Amendment 3) | 0/20 | 0/9 | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 | **0/89** |

- **Sonnet 5.5 refused on every family.** That fits a classifier keyed to the request's shape rather than to the content of any one source. This is not verified.
- **The text is never reworded to get past a classifier.** Switching to a model built for the work is the design; laundering text past a refusing model is not.
- **Probe rates (one call per item):** Opus 5 refused 5/6, Sonnet 4.6 refused 0/6.

## Cost estimate (probe-calibrated)
| Step | Estimate |
|---|---|
| `pheno46` translation, Sonnet 4.6 × 89 (~$0.017 each) | ≈ $1.5 |
| `pheno46_mixed` fill, Opus 5 × Sonnet 4.6's refusals (expected few; ~$0.07 each) | ≈ $0.35 |
| `pheno_opus5` translation, Opus 5 × 89 (~$0.07 each, refusals bill their partial output too) | ≈ $6.2 |
| Reconstruction `pheno46` (full current panel) | ≈ $4.4 |
| Reconstruction `pheno_opus5` (scales with items translated; probe suggests ~15–20%) | ≈ $1 |
| Reconstruction fill-ins (~$0.05 × items × 6 readers) | ≈ $0.3 |
| `mech_fb` | $0 (no refusals) |
| **Total** | **≈ $13.7**, about half of it the Opus 5 replication |

The budget guard stays at 2× estimate per script.

## Lock
- **`AMENDMENT_3a_2026-10-03.lock.json`** pins this file and the three 3a scripts, and records the main lock's sha256.
- **Every 3a script verifies both locks.** A real run refuses to start on a mismatch.
- **Committed and pushed before any 3a translation call** other than the probes listed above.
- **After the Amendment-3 chain finishes,** this text is folded into the prereg as §16a and the main lock is re-made (old lock kept, `supersedes` recorded), as in §14.7.
