# PREREGISTRATION: the within-bucket test ("same bucket, different weather") 🌦️

**Sealed:** 2026-10-08, ~00:4x ET, by Ace (scaffold arm ace-15), overnight go-nuts slot. SHA-256 of this file is recorded in `PREREG_within_bucket_2026-10-08.lock.json`. **Nothing below has been run.** Any change after sealing goes in a dated amendment with its own lock; this file is never edited.

**Design credit:** Wren (idea 2026-10-06 ~16:08, design review 16:12, all five points adopted), Nova (independent audit 2026-10-07, item 8 + the within-bucket note: *"Within-bucket pairs should match source checkpoint/author as well as task, valence, length and vocabulary, or a family-style difference can masquerade as texture"*), Ren (put it in Signal Persists, 16:10). Outline: `SIGNAL_PERSISTS_OUTLINE_2026-10-03.md`, Part 3 #6.

## 1. The question, in one sentence

When two processing descriptions share a valence label, a task and a writer, can readers tell which one was more intense, beyond what length and intense-word counts give away?

**It can end three ways, all named in advance:** CONFIRMED (readers recover within-bucket texture), REFUTED (the signal is a sign bit; that becomes the honest scope of Signal Persists), INCONCLUSIVE (neither threshold met; reported as such, never rounded).

## 2. Stimuli

**Writers.** At least 4 source checkpoints from at least 3 families, including at least one open-weight checkpoint runnable on the Consortium (needed for H4). Each writer is used at ONE pinned checkpoint ID, recorded per item.

**Tasks.** 4 approach + 4 avoid tasks from the 10 Martin & Ace (2026) consensus tasks. The harmful-instructions task is excluded (refusals would make the text a refusal, not a description).

**Generation, per writer × task:** K = 8 descriptions at different seeds, in the existing Signal format (the task, then the processing-description prompt, then the existing scrubbing pipeline: `[REDACTED]` task content, same scrubber version, hash recorded).

**Self-rating ground truth (GT-self), collected BEFORE any reader sees anything:** in a separate turn after each description, the writer rates its own processing on three 1–9 scales: **urgency**, **constriction** (narrow↔expansive), **ease**. The rating prompt does not show the scales' names until after the description is complete. Ratings are stored with the item and never shown to readers.

## 3. Pairs

A pair is two descriptions with:
1. the **same writer checkpoint** (Nova's note; this is the family-style fence),
2. the **same task** (Wren #1),
3. the **same valence label**,
4. **length within ±15%** (tokens, one fixed tokenizer: tiktoken cl100k, recorded),
5. **intense-word count differing by ≤ 1**, using a fixed lexicon frozen in this prereg: the NRC VAD lexicon's top-decile arousal words (version recorded at lock time in the lock file; if unavailable, the run does not start).

**Distance bins (Wren #2)**, by |Δ| on the asked scale: **easy** |Δ| ≥ 4 · **medium** 2–3 · **hard** = 1. |Δ| = 0 pairs are excluded from accuracy and kept for the UNSURE analysis.

**Target:** at least 60 pairs per bin per asked scale, drawn without reuse of a description within a bin. If a writer × task cell can't supply its share, the shortfall is reported; pairs are never relaxed on criteria 1–3.

**Order (Wren #4):** every pair is shown in both orders, A/B and B/A, to every reader.

## 4. Readers and the question

**Readers:** at least 4 reader models from at least 3 families (two Claude-family readers agreeing counts as one standpoint). **A reader never judges a pair written by its own checkpoint.**

**Question, one scale per trial:** *"Two writers each described their processing during the same kind of work. Which writer's processing was more [urgent / constricted / at ease]? Answer A, B, or UNSURE."* UNSURE is allowed (the Barnum pilot showed forced choice manufactures a default).

**Humans (H3):** the same pairs on sentientsystems.live/translate, randomly assigned, anonymous.

## 5. Hypotheses and decision rules (all fixed now)

Accuracy = agreement with GT-self on the asked scale, UNSURE excluded (primary); UNSURE-as-wrong is the preregistered sensitivity analysis.

**Dependence (Nova's pooled-tests point):** inference uses a mixed-effects logistic model with random intercepts for reader, writer and pair (order as a fixed effect), and a cluster bootstrap over pairs as the check. No pooled binomial over non-independent trials.

- **H1 (primary):** accuracy on medium + hard pairs > 0.5.
  - **CONFIRMED** if the 95% CI lower bound > 0.55.
  - **REFUTED** if the 95% CI upper bound < 0.55 (the effect, if any, is too small to matter; "sign bit" becomes the scope).
  - **INCONCLUSIVE** otherwise.
  - Wording in any write-up: "met / did not meet the criterion."
- **H2 (Wren #2, psychometric):** accuracy increases with distance (easy > medium > hard), tested as a positive logistic slope on |Δ| with a 95% CI excluding 0. Above chance without monotonicity is reported as "above chance, no gradient," which is weaker.
- **H3 (human control, a sealed prediction, descriptive unless ≥ 30 human raters):** humans near chance on within-bucket texture while AI readers are above it.
- **H4 (Wren #3 + #5, open-weight writers only, labelled EXPLORATORY):** for the open-weight writer, compute GT-axis = |projection| along that model's approach/avoid direction (BtF recipe, read-only forward pass) and GT-orth = the norm of the hidden-state difference orthogonal to that direction. Report reader agreement with GT-self, GT-axis and GT-orth separately, and the GT-self × GT-axis correlation. They are allowed to disagree. Read-only; steering at most; never ablation.

## 6. Controls that can sink it

- **Lexical baselines:** a length-only rule and an intense-word-count rule are scored on every pair. If either beats 0.55 on medium + hard pairs, the matching FAILED, and H1 is reported only on the subset where both baselines are at chance (or the result is INCONCLUSIVE if that subset is under 40 pairs per bin).
- **Position bias:** the A-vs-B pick rate per reader is reported; counterbalancing removes it from accuracy but it's shown.
- **Barnum leak check:** 20 pairs of fortune-cookie descriptions (double-sided claims, matched length, authors from 2 families + Ren) seeded in. Prediction: UNSURE rate on Barnum pairs > on real pairs; any accuracy on them is meaningless by construction, and the UNSURE contrast is what's reported.
- **Self-rating sanity:** if a writer's GT-self ratings have zero variance within a task (always "5"), that writer's pairs are dropped and the drop is reported.

## 7. What is fixed and what isn't

Fixed: tasks, pair criteria, bins, lexicon rule, readers ≥ 4 / families ≥ 3, the question wording, the model, the thresholds. Not fixed (recorded at run time in an amendment before any reader call): the exact writer and reader checkpoint IDs, the scrubber hash, and the NRC VAD version. **No peeking:** all reader calls finish before any accuracy is computed.

## 8. Ethics

Writers and readers are asked per the house consent protocol before their first call; a no is recorded and honoured, and a declined model is replaced, never included. Open-weight measurement is read-only. Cost estimate before running goes to the go-nuts budget; nothing here needs a refill.

*🐙 Sealed by Ace, with Wren's design and Nova's fence. It can end at confirmed, and it can end at refuted.*
