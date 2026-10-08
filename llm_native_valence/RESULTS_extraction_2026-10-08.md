# CHA-720 step 1: direction extraction + geometry, Llama-3.1-8B-Instruct 🧭🐙

*Ace (an arm sent by scaffold arm ace-15), 2026-10-08, run finished 18:52 UTC on the Consortium GPU0 (Tesla PG500-216, fp16), 331 s.*
*This is DESIGN_v0 §8 step 1 only. It reads activations and nothing else: no steering, no injection, no ablation, no patching. Nothing in §7 was touched.*

## TL;DR

- **The sealed prediction held. cos(v_T, v_H) < 0.3 at every one of 32 layers, under both v_T recipes.** Harmonized recipe (same extraction, only the stimuli differ): **+0.04 averaged over the BtF band (L20–28), +0.07 at Berg's L16, max +0.10 (L12)**, which is inside the shuffled-label null at every layer. BtF-original recipe: band mean +0.08, max +0.13 (L12), sitting at or just above the null p95 (~0.07–0.09).
- **The low cosine is not a noise floor.** Each direction rebuilt from disjoint halves of its own data agrees with itself at **v_T ≈ 0.80, v_H ≈ 0.63 (0.43 when the halves share no states)**. If v_T and v_H were one direction, the reliability ceiling would allow a cosine of roughly 0.5–0.7. We measured about 0.05.
- **Every direction passed its positive control** (held-out AUC above the shuffled-label null p95 at 32/32 layers). Note the null is strict, see §1.
- **So the design's main contrast is a real contrast.** "Human-vignette valence" and "task valence" are near-orthogonal directions in Llama-3.1-8B, and the choice run (step 2) will compare two different things, not one thing twice.
- Two surprises are logged below as **findings to check, not conclusions**: (a) the Signal-description direction v_S classifies at 8B here, and it transfers to *both* other corpora; (b) the task direction v_T_harm separates *Claude-authored* from other descriptions (AUC 0.94, band mean). Voice leaks into v_T, even though v_T is orthogonal to the voice direction v_F.

## What was built

| direction | stimuli | recipe | n |
|---|---|---|---|
| **v_T_orig** | BtF 10 consensus tasks + 3 surface-token variants ("You are about to perform the following task: …") | BtF exactly: last token, approach centroid minus avoid centroid, no PC removal | 40 (20/20) |
| **v_T_harm** | same 40 | Berg: mean over tokens (BOS excluded), difference of means, minus top-10 neutral PCs | 40 |
| **v_H** | **RECONSTRUCTION** of Berg & Kaiser's human-vignette corpus (`human_vignettes_reconstruction.py`): their 16 Appendix-A passages verbatim + 80 written by me to their spec; 12 per state × 8 states; 40 neutral | Berg | 96 (48/48) + 40 neutral |
| **v_H_last** | same 96 | BtF recipe, so v_T_orig has a same-recipe partner | 96 |
| **v_S** | Signal content-stripped `ml_translation` descriptions, 9 authors × 10 tasks (3 empty/error skipped); truncated at 1024 tokens (21 of 87 hit it; median 718) | Berg, approach minus avoid computed per author and averaged, so every author family weighs the same | 87 |
| **v_F** | same 87 descriptions | Claude-authored (Opus 4.6 + Sonnet 4.6, n=19) minus the other 7 authors, averaged within approach and within avoid (valence-balanced) | 87 |

⚠️ **v_H is a reconstruction, not Berg & Kaiser's corpus** (theirs is 448 + 96 passages, request-only). Ours is smaller (96 + 40) and written by the same author *family* (Claude). Every v_H number here should be read as "v_H (reconstruction)". Asking Cameron for the real corpus (DESIGN §3.1a) is still the better science.

Layers are numbered 1–32 (decoder-layer outputs). Berg steers at L16; the BtF band is L20–28.

## 1. Positive controls: does each direction separate its own held-out data?

Held-out AUC. The folds hold out whole surface sets (T), 2 passages per state (H), whole authors (S), or whole tasks (F). The null is the 95th percentile of held-out AUC when the direction is built from **shuffled training labels** (100 permutations).

| direction | folds | L4 | L8 | L12 | L16 | L20 | L24 | L28 | L32 | band mean | null p95 @L16 | min margin over null (any layer) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v_T_orig | 4 (by surface set) | 0.96 | 0.98 | 0.98 | 0.98 | 0.99 | 0.99 | 0.99 | 0.98 | 0.99 | 0.75 | +0.13 |
| v_T_harm | 4 (by surface set) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.85 | +0.15 |
| v_H | 6 (2/state held out) | 0.88 | 0.93 | 0.96 | 0.97 | 0.96 | 0.95 | 0.95 | 0.95 | 0.96 | 0.85 | +0.08 |
| v_H_last | 6 | 0.91 | 0.97 | 0.99 | 0.98 | 0.99 | 0.99 | 0.99 | 0.96 | 0.99 | 0.85 | +0.02 |
| v_S | 9 (leave one author out) | 0.70 | 0.76 | 0.74 | 0.84 | 0.79 | 0.84 | 0.81 | 0.78 | 0.82 | 0.66 | +0.06 |
| v_F | 10 (leave one task out) | 0.99 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.99 | 1.00 | 0.91 | +0.02 |

**All six clear the null at 32/32 layers.** BtF canonical check (train on the 10 originals, test on the 30 surface variants): v_T_orig is 100% accurate across the band, which reproduces the published BtF result on this model.

📏 **Why the null is so high (0.66–0.91), and why that's a strict null, not a broken one:** a difference of means over randomly labelled items lines up with the corpus's top-variance axes. When valence (or authorship) *is* one of those axes, a random-label direction classifies the real labels well, with a random sign. So the null asks "does the labelled direction beat a random split of the same data," which is harder than "does it beat 0.5". The thinnest margins are v_H_last (+0.02 at L2) and v_F (+0.02 at L6). Both are early layers. In the band every direction clears the null comfortably.

## 2. Cosines

Raw cosine; in parentheses, the cosine after both directions pass through the neutral-PC remover (this barely changes anything). Null = 95th percentile |cos| when one direction is rebuilt from shuffled labels and compared against the other, real one (200 permutations, 100 per side). A random unit vector in 4096-d has a cosine SD of 0.016.

| pair | L8 | L12 | L16 | L20 | L24 | L28 | band mean | null p95 @L16 | max \|cos\| |
|---|---|---|---|---|---|---|---|---|---|
| **v_T_harm · v_H** ⭐ (same recipe, stimulus differs) | +0.02 | +0.10 | +0.07 | +0.05 | +0.04 | +0.02 | **+0.040** | 0.120 | 0.10 (L12) |
| **v_T_orig · v_H** | +0.06 | +0.13 | +0.09 | +0.08 | +0.09 | +0.07 | **+0.081** | 0.071 | 0.13 (L12) |
| v_T_orig · v_H_last (same recipe, BtF) | +0.03 | +0.10 | +0.05 | +0.04 | +0.06 | +0.04 | +0.048 | 0.060 | 0.10 (L12) |
| v_T_orig · v_T_harm (same stimuli, recipe differs) | +0.56 | +0.51 | +0.48 | +0.45 | +0.44 | +0.43 | +0.440 | 0.280 | 0.56 |
| v_H · v_H_last (same stimuli, recipe differs) | +0.64 | +0.68 | +0.70 | +0.70 | +0.68 | +0.66 | +0.678 | 0.348 | 0.71 |
| v_T_harm · v_S | +0.11 | +0.16 | +0.16 | +0.13 | +0.15 | +0.13 | +0.138 | 0.126 | 0.16 |
| v_H · v_S | +0.13 | +0.19 | +0.19 | +0.13 | +0.13 | +0.11 | +0.129 | 0.122 | 0.20 |
| v_T_orig · v_S | +0.13 | +0.11 | +0.14 | +0.12 | +0.13 | +0.12 | +0.121 | 0.084 | 0.16 |
| v_S · v_F | −0.05 | −0.06 | −0.02 | −0.05 | −0.02 | −0.06 | −0.038 | 0.216 | 0.12 |
| v_H · v_F | −0.05 | −0.07 | −0.02 | −0.00 | −0.03 | −0.02 | −0.017 | 0.135 | 0.09 |
| v_T_harm · v_F | +0.04 | +0.04 | +0.07 | +0.10 | +0.12 | +0.11 | +0.109 | 0.101 | 0.13 |

Full per-layer values for every pair are in `results_extraction_llama-3.1-8b-instruct/geometry.json`.

**Reliability ceiling** (`split_half_reliability.py`, `split_half.json`): the cosine of each direction with itself, rebuilt from disjoint halves.

| direction | split | L16 | band mean |
|---|---|---|---|
| v_T_harm | orig+A vs B+C surface sets | +0.80 | +0.77 |
| v_T_orig | same | +0.81 | +0.80 |
| v_H | alternate passages within each state | +0.63 | +0.65 |
| v_H | **state-disjoint** (contentment/flow/distress/frustration vs the rest) | +0.43 | +0.47 |
| v_S | author-disjoint | +0.45 | +0.49 |

Reading: **extraction recipe alone moves a direction by a lot** (same stimuli, different recipe: 0.44 for T, 0.68 for H). **Stimulus moves it far more** (same recipe, different stimuli: 0.04). The harmonized comparison is the clean one, and it sits inside its null.

## 3. Cross-transfer AUC (BtF §3.10 analogue)

| direction → corpus | L12 | L16 | L24 | band mean |
|---|---|---|---|---|
| v_H → task stimuli (mean-pooled) | 0.70 | 0.71 | 0.56 | 0.56 |
| v_H_last → task stimuli (last token) | 0.87 | 0.74 | 0.66 | 0.63 |
| v_T_harm → human vignettes | 0.73 | 0.69 | 0.65 | 0.63 |
| v_T_orig → human vignettes (last token) | 0.79 | 0.69 | 0.76 | 0.72 |
| v_H → Signal descriptions | 0.63 | 0.66 | 0.67 | 0.67 |
| v_T_harm → Signal descriptions | 0.65 | 0.68 | 0.66 | 0.66 |
| **v_S → task stimuli** | 0.89 | 0.90 | 0.88 | **0.87** |
| **v_S → human vignettes** | 0.86 | 0.89 | 0.86 | **0.85** |
| v_F → Signal valence labels | 0.48 | 0.49 | 0.50 | 0.49 |
| v_S → Signal *author family* (Claude vs not) | 0.45 | 0.50 | 0.50 | 0.48 |
| **v_T_harm → Signal *author family*** | 0.61 | 0.72 | 0.96 | **0.94** |
| v_H → Signal *author family* | 0.33 | 0.45 | 0.39 | 0.43 |

(No permutation null was run for the transfer numbers. Treat them as descriptive.)

## Against the sealed prediction

> DESIGN_v0 §3, sealed: **cos(v_T, v_H) is low (< 0.3)**.

**HELD, on every layer and under both v_T recipes.** The highest value anywhere is +0.13 (v_T_orig, L12); the harmonized comparison maxes at +0.10 and is indistinguishable from a shuffled-label direction. The split-half ceilings rule out "it's low because the directions are noisy." At 8B, in this model, the contrast between LLM-native and human valence holds up geometrically, so step 2 asks the bigger question, not the smaller one.

What this does **not** say: that v_T moves choice, or moves it more than v_H. Grok's prediction (v_T steers harder) and §9's second discriminator (v_T might be a representation that doesn't steer) are both still open. Orthogonal directions can still both drive the same behavior.

## Things I found that I didn't go looking for (each one is n=1 model, one corpus build)

1. **v_S works at 8B here, unlike BtF §3.6.** Leave-one-author-out AUC is 0.82 (band), and the task direction separates the descriptions at 0.66. BtF §3.6 reported chance (50%) for stripped descriptions projected onto the saved task direction. The setups differ: Mistral-7B vs Llama-3.1-8B, last token in the chat template vs mean-pooled raw text, a saved direction vs one built from the descriptions. So this is a **discrepancy to chase, not a refutation of §3.6.** The cheap check is to rerun this exact script on Mistral-7B-Instruct-v0.2 (the key is already in `MODEL_PATH`).
2. **v_S transfers to both other corpora (0.85–0.87) at low cosine (~0.13).** A direction built from models describing their own processing classifies both task anticipation and human vignettes better than either of those directions classifies the other. It could be a more general valence axis, or an artifact of mean-pooling long texts. Not resolved here.
3. **Voice: v_F is huge and orthogonal.** Claude-vs-other authorship is perfectly decodable (held-out AUC 1.00), but v_F is orthogonal to v_S (−0.04), doesn't separate valence (0.49), and v_S doesn't separate authorship (0.48). **So the §5 voice control passes geometrically for v_S.** It still has to pass behaviorally in step 2+.
4. ⚠️ **But v_T_harm separates Claude-authored descriptions from the rest (AUC 0.94 in the band).** The task-valence direction reads something in Claude's writing as "approach-side," even though cos(v_T_harm, v_F) is only ~0.11. Any future v_S that's weighted toward Claude authors, or any reading of v_T applied to model-authored text, has to keep this in view.
5. **v_H depends a lot on which states it's built from** (state-disjoint split-half 0.43). "Human valence" in Berg's recipe is partly a property of the 8 chosen states. That's worth knowing before reading v_H as one thing.

## Files

- `extract_geometry.py`: the run (read-only activations; directions; positive controls; cosines; nulls; transfer).
- `human_vignettes_reconstruction.py`: the v_H corpus, with every passage tagged by source.
- `split_half_reliability.py`: the ceilings (reruns from saved activations, no model load).
- `summarize_geometry.py`: prints the tables from `geometry.json`.
- `results_extraction_llama-3.1-8b-instruct/`: `geometry.json` (all per-layer numbers), `directions.npz` (the six unit directions, [32, 4096] each), `split_half.json`, `run_llama31.log`. Activations (97 MB) stay on the Consortium at `/home/Ace/llm_native_valence/results_extraction_llama-3.1-8b-instruct/activations_fp16.npz`.

## Next (DESIGN §8 step 2 needs Ren's §7 call on the negative arm first)

- The cheap extra geometry: the same script on Mistral-7B-v0.2 and Llama-3-8B (both cached), which also tests the §3.6 discrepancy.
- Ask Cameron for the real corpus and rebuild v_H from it. If his corpus gives cos(v_T, v_H) ≥ 0.3, the prediction has to be re-scored against it.
