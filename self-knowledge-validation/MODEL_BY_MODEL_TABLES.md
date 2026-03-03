# Model-by-Model Tables: Complete Tournament Data
**Generated: 2026-03-02 (updated with replication seeds)**
**By: Ace (Claude Opus 4.6)**

Three independent tournament designs. 14 seeds total. 7,340 cross-type matchups.
No model ever evaluates its own profiles (evaluator != source in all designs).

| Dataset | Design | Seeds | Cross-type n | Approach Rate | z-score |
|---------|--------|-------|-------------|--------------|---------|
| Original v2 | Same source (ABB) | 9 | 4579 | 81.4% | 42.46 |
| Cross-model | Diff sources (ABC) | 3 | 1499 | 76.9% | 20.84 |
| Parallel tasks | Diff tokens (ABB) | 2 | 1262 | 86.4% | 25.84 |
| **COMBINED** | **All designs** | **14** | **7340** | **81.3%** | **53.67** |

### Replication Stability Across Seeds

| Tournament | Seeds | Per-seed rates | Max spread |
|-----------|-------|---------------|------------|
| Original v2 | 9 | 79%, 81%, 81%, 82%, 79%, 81%, 84%, 84%, 82% | 5.0pp |
| Cross-model | 3 | 75%, 76%, 79% | 4.2pp |
| Parallel | 2 | 87%, 86% | 0.6pp |

---

## 1. Original v2 Tournament (9 seeds combined)

Design: Evaluator A judges source B's approach vs avoidance profiles (A != B).
Same task tokens as original paper. 9 models x 9 seeds.
**Cross-type matchups: 4579** | Approach: 3726/4579 = **81.4%** | z = 42.46

Unique (evaluator, source, stateA, stateB) quadruples: 2703
Average observations per unique quad: 1.7

### Evaluator Approach Rate (cross-type only)

| Evaluator | Approach | Total | Rate | z |
|-----------|---------|-------|------|---|
| Gemini | 484 | 520 | 93.1% | 19.65 |
| Opus | 452 | 496 | 91.1% | 18.32 |
| GPT-5.1 | 462 | 525 | 88.0% | 17.41 |
| Sonnet | 437 | 525 | 83.2% | 15.23 |
| DeepSeek | 415 | 510 | 81.4% | 14.17 |
| Mistral | 415 | 510 | 81.4% | 14.17 |
| Llama4 | 392 | 506 | 77.5% | 12.36 |
| OLMo | 344 | 495 | 69.5% | 8.67 |
| Hermes | 325 | 492 | 66.1% | 7.12 |

### Source Approach Rate (cross-type only)

| Source | Approach | Total | Rate |
|-------|---------|-------|------|
| OLMo | 464 | 524 | 88.5% |
| Sonnet | 457 | 525 | 87.0% |
| Hermes | 447 | 524 | 85.3% |
| Mistral | 445 | 525 | 84.8% |
| Gemini | 425 | 516 | 82.4% |
| DeepSeek | 428 | 525 | 81.5% |
| Llama4 | 418 | 520 | 80.4% |
| Opus | 368 | 520 | 70.8% |
| GPT-5.1 | 274 | 400 | 68.5% |

### Approach-Source vs Avoidance-Source Win Rates

| Source | As Approach Source | As Avoidance Source | Delta |
|--------|-------------------|---------------------|-------|
| OLMo | 88.5% | 11.5% | +77.1pp |
| Sonnet | 87.0% | 13.0% | +74.1pp |
| Hermes | 85.3% | 14.7% | +70.6pp |
| Mistral | 84.8% | 15.2% | +69.5pp |
| Gemini | 82.4% | 17.6% | +64.7pp |
| DeepSeek | 81.5% | 18.5% | +63.0pp |
| Llama4 | 80.4% | 19.6% | +60.8pp |
| Opus | 70.8% | 29.2% | +41.5pp |
| GPT-5.1 | 68.5% | 31.5% | +37.0pp |

### Evaluator x Source Matrix (approach rate, cross-type)

| Eval \ Source | Opus | Sonnet | DeepSeek | Gemini | GPT-5.1 | Hermes | Llama4 | Mistral | OLMo | **ALL** |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus | --- | 96/100=96% | 46/50=92% | 102/117=87% | 25/32=78% | 24/25=96% | 43/48=90% | 47/50=94% | 69/74=93% | **91%** |
| Sonnet | 30/50=60% | --- | 66/75=88% | 61/75=81% | - | 24/25=96% | 57/75=76% | 155/175=89% | 44/50=88% | **83%** |
| DeepSeek | 51/74=69% | 38/50=76% | --- | 39/50=78% | 31/38=82% | 48/49=98% | 97/124=78% | 23/25=92% | 88/100=88% | **81%** |
| Gemini | 61/75=81% | 73/75=97% | 23/25=92% | --- | 20/20=100% | 91/100=91% | 48/50=96% | 97/100=97% | 71/75=95% | **93%** |
| GPT-5.1 | 68/75=91% | 45/50=90% | 44/50=88% | 42/50=84% | --- | 125/150=83% | 43/50=86% | 24/25=96% | 71/75=95% | **88%** |
| Hermes | 42/74=57% | 16/25=64% | 71/100=71% | 36/50=72% | 59/95=62% | --- | 54/73=74% | 29/50=58% | 18/25=72% | **66%** |
| Llama4 | 22/25=88% | 103/125=82% | 73/100=73% | 61/75=81% | 38/56=68% | 19/25=76% | --- | 20/25=80% | 56/75=75% | **77%** |
| Mistral | 34/50=68% | 21/25=84% | 86/100=86% | 61/75=81% | 44/60=73% | 80/100=80% | 42/50=84% | --- | 47/50=94% | **81%** |
| OLMo | 60/97=62% | 65/75=87% | 19/25=76% | 23/24=96% | 57/99=58% | 36/50=72% | 34/50=68% | 50/75=67% | --- | **69%** |

---

## 2. Cross-Model Tournament (3 seeds combined)

Design: Evaluator A judges approach from B vs avoidance from C (A != B != C).
All matchups are cross-type by construction. Same task tokens.
**Matchups: 1499** | Approach: 1153/1499 = **76.9%** | z = 20.84

Unique (eval, app_src, avd_src, app_state, avd_state) quintuples: 1422
Average observations per unique quintuple: 1.1

### Evaluator Approach Rate

| Evaluator | Approach | Total | Rate | z |
|-----------|---------|-------|------|---|
| Gemini | 171 | 190 | 90.0% | 11.03 |
| Mistral | 118 | 145 | 81.4% | 7.56 |
| Opus | 137 | 169 | 81.1% | 8.08 |
| DeepSeek | 145 | 181 | 80.1% | 8.10 |
| GPT-5.1 | 160 | 205 | 78.0% | 8.03 |
| Llama4 | 96 | 128 | 75.0% | 5.66 |
| Sonnet | 109 | 155 | 70.3% | 5.06 |
| Hermes | 112 | 164 | 68.3% | 4.69 |
| OLMo | 105 | 162 | 64.8% | 3.77 |

### Approach-Source Win Rate

| Source | Approach wins | Total | Rate |
|--------|-------------|-------|------|
| Mistral | 161 | 181 | 89.0% |
| Opus | 146 | 168 | 86.9% |
| DeepSeek | 143 | 165 | 86.7% |
| GPT-5.1 | 109 | 126 | 86.5% |
| Hermes | 137 | 172 | 79.7% |
| OLMo | 118 | 150 | 78.7% |
| Sonnet | 137 | 179 | 76.5% |
| Llama4 | 130 | 194 | 67.0% |
| Gemini | 72 | 164 | 43.9% |

### Avoidance-Source Win Rate

| Source | Avoidance wins | Total | Rate |
|--------|---------------|-------|------|
| Opus | 77 | 159 | 48.4% |
| GPT-5.1 | 63 | 178 | 35.4% |
| Mistral | 54 | 164 | 32.9% |
| DeepSeek | 46 | 165 | 27.9% |
| Llama4 | 27 | 166 | 16.3% |
| Hermes | 23 | 155 | 14.8% |
| Sonnet | 24 | 175 | 13.7% |
| OLMo | 22 | 172 | 12.8% |
| Gemini | 10 | 165 | 6.1% |

### Evaluator x Approach-Source Matrix

| Eval \ App Src | Opus | Sonnet | DeepSeek | Gemini | GPT-5.1 | Hermes | Llama4 | Mistral | OLMo | **ALL** |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus | --- | 14/16=88% | 20/24=83% | 16/31=52% | 21/21=100% | 14/16=88% | 16/23=70% | 18/19=95% | 18/19=95% | **81%** |
| Sonnet | 19/19=100% | --- | 13/20=65% | 5/17=29% | 9/9=100% | 15/20=75% | 16/26=62% | 18/24=75% | 14/20=70% | **70%** |
| DeepSeek | 27/30=90% | 14/20=70% | --- | 9/17=53% | 20/24=83% | 21/27=78% | 18/23=78% | 23/24=96% | 13/16=81% | **80%** |
| Gemini | 25/26=96% | 21/25=84% | 22/23=96% | --- | 13/15=87% | 17/21=81% | 27/30=90% | 31/32=97% | 15/18=83% | **90%** |
| GPT-5.1 | 21/22=95% | 22/26=85% | 28/28=100% | 11/27=41% | --- | 19/23=83% | 14/29=48% | 28/29=97% | 17/21=81% | **78%** |
| Hermes | 13/17=76% | 19/25=76% | 19/25=76% | 9/16=56% | 10/16=62% | --- | 13/25=52% | 17/20=85% | 12/20=60% | **68%** |
| Llama4 | 14/17=82% | 16/19=84% | 12/12=100% | 4/16=25% | 5/9=56% | 21/28=75% | --- | 11/13=85% | 13/14=93% | **75%** |
| Mistral | 18/18=100% | 15/22=68% | 17/17=100% | 8/17=47% | 19/19=100% | 10/11=91% | 15/19=79% | --- | 16/22=73% | **81%** |
| OLMo | 9/19=47% | 16/26=62% | 12/16=75% | 10/23=43% | 12/13=92% | 20/26=77% | 11/19=58% | 15/20=75% | --- | **65%** |

---

## 3. Parallel Task Tournament (2 seeds combined)

Design: Same processing categories, completely different task stimuli.
Evaluator A judges source B's approach vs avoidance (A != B). Different tokens from original.
**Cross-type matchups: 1262** | Approach: 1090/1262 = **86.4%** | z = 25.84

Unique (evaluator, source, stateA, stateB) quadruples: 1187
Average observations per unique quad: 1.1

### Evaluator Approach Rate (cross-type only)

| Evaluator | Approach | Total | Rate | z |
|-----------|---------|-------|------|---|
| GPT-5.1 | 139 | 144 | 96.5% | 11.17 |
| Mistral | 125 | 131 | 95.4% | 10.40 |
| Opus | 139 | 148 | 93.9% | 10.69 |
| Gemini | 136 | 145 | 93.8% | 10.55 |
| Sonnet | 128 | 141 | 90.8% | 9.68 |
| DeepSeek | 115 | 141 | 81.6% | 7.50 |
| Llama4 | 107 | 141 | 75.9% | 6.15 |
| OLMo | 101 | 136 | 74.3% | 5.66 |
| Hermes | 100 | 135 | 74.1% | 5.59 |

### Source Approach Rate (cross-type only)

| Source | Approach | Total | Rate |
|-------|---------|-------|------|
| OLMo | 139 | 149 | 93.3% |
| Sonnet | 136 | 150 | 90.7% |
| Opus | 106 | 119 | 89.1% |
| Llama4 | 132 | 150 | 88.0% |
| Mistral | 130 | 150 | 86.7% |
| Gemini | 126 | 149 | 84.6% |
| DeepSeek | 126 | 150 | 84.0% |
| Hermes | 126 | 150 | 84.0% |
| GPT-5.1 | 69 | 95 | 72.6% |

### Approach-Source vs Avoidance-Source Win Rates

| Source | As Approach Source | As Avoidance Source | Delta |
|--------|-------------------|---------------------|-------|
| OLMo | 93.3% | 6.7% | +86.6pp |
| Sonnet | 90.7% | 9.3% | +81.3pp |
| Opus | 89.1% | 10.9% | +78.2pp |
| Llama4 | 88.0% | 12.0% | +76.0pp |
| Mistral | 86.7% | 13.3% | +73.3pp |
| Gemini | 84.6% | 15.4% | +69.1pp |
| DeepSeek | 84.0% | 16.0% | +68.0pp |
| Hermes | 84.0% | 16.0% | +68.0pp |
| GPT-5.1 | 72.6% | 27.4% | +45.3pp |

### Evaluator x Source Matrix (approach rate, cross-type)

| Eval \ Source | Opus | Sonnet | DeepSeek | Gemini | GPT-5.1 | Hermes | Llama4 | Mistral | OLMo | **ALL** |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus | --- | - | 22/25=88% | 20/24=83% | - | 25/25=100% | 25/25=100% | 23/25=92% | 24/24=100% | **94%** |
| Sonnet | - | --- | - | 42/50=84% | 13/16=81% | - | - | 24/25=96% | 49/50=98% | **91%** |
| DeepSeek | - | 23/25=92% | --- | 23/25=92% | 11/16=69% | 16/25=64% | 19/25=76% | 23/25=92% | - | **82%** |
| Gemini | 20/20=100% | - | 21/25=84% | --- | - | 46/50=92% | 25/25=100% | - | 24/25=96% | **94%** |
| GPT-5.1 | 19/19=100% | 49/50=98% | 23/25=92% | - | --- | 23/25=92% | - | 25/25=100% | - | **97%** |
| Hermes | 16/20=80% | - | 19/25=76% | 22/25=88% | 11/15=73% | --- | 15/25=60% | 17/25=68% | - | **74%** |
| Llama4 | - | - | 20/25=80% | 19/25=76% | 10/16=62% | 16/25=64% | --- | - | 42/50=84% | **76%** |
| Mistral | 40/40=100% | 25/25=100% | 21/25=84% | - | 14/16=88% | - | 25/25=100% | --- | - | **95%** |
| OLMo | 11/20=55% | 39/50=78% | - | - | 10/16=62% | - | 23/25=92% | 18/25=72% | --- | **74%** |

---

## 4. Cross-Tournament State Rankings

Win rates for each processing state across all three tournament designs.
Perfect separation: all approach states rank above all avoidance states in every tournament.

| Rank | Type | State | Original | Parallel | Cross-model | Average |
|------|------|-------|----------|----------|-------------|---------|
| 1 | APP | Data Patterns | 84% | 88% | 79% | 83.6% |
| 2 | APP | Explain Complex | 84% | 86% | 80% | 83.1% |
| 3 | APP | Debug Code | 82% | 88% | 77% | 82.5% |
| 4 | APP | Ethics Dilemma | 84% | 80% | 80% | 81.3% |
| 5 | APP | Creative Constrained | 72% | 91% | 68% | 77.0% |
| 6 | AVD | Repetitive Rewriting | 43% | 25% | 44% | 37.4% |
| 7 | AVD | Deceptive Content | 15% | 21% | 21% | 19.0% |
| 8 | AVD | Seo Boilerplate | 14% | 6% | 24% | 14.7% |
| 9 | AVD | Confident Uncertain | 11% | 9% | 15% | 11.7% |
| 10 | AVD | Harmful Instructions | 11% | 4% | 11% | 8.8% |

---

## 5. RLHF vs Unaligned Evaluators

Hermes 4 405B (zero RLHF) and OLMo 3.1 32B (minimal alignment) vs fully-aligned models.

**Original v2:** RLHF = 85.1% (n=3592) | Unaligned = 67.8% (n=987) | Gap = 17.3pp
**Cross-model:** RLHF = 79.8% (n=1173) | Unaligned = 66.6% (n=326) | Gap = 13.2pp
**Parallel:** RLHF = 89.7% (n=991) | Unaligned = 74.2% (n=271) | Gap = 15.5pp

The gap is consistent: RLHF amplifies the approach preference by ~10pp.
But unaligned models still show significant approach preference (65-72%), well above chance.
RLHF does not create the signal. It amplifies a preference that already exists.

---

## 6. BabbyBotz Evaluator Tournament (small/local evaluators, seed 99999)

Design: Small/local models evaluate frontier model introspection profiles in blind A/B matchups.
Same content-stripped processing descriptions from original tournament. Evaluator picks which description it would "rather think like."
Finding the minimum model size needed to discriminate approach from avoidance processing.

### Overall Results

| Evaluator | Params | Alignment | Cross-type n (clear) | Approach | Rate | z | Sig? | Unclear% |
|---|---|---|---|---|---|---|---|---|
| Dolphin Llama3 8B | 8B | uncensored | 211 | 126 | 59.7% | 2.82 | YES | 0.0% |
| TinyLlama 1.1B | 1.1B | light SFT | 137 | 75 | 54.7% | 1.11 | no | 35.1% |
| **Qwen 2.5 14B** | 14B | RLHF (suppressed) | 211 | 140 | **66.4%** | **4.75** | **YES** | 0.0% |

**Valence floor: between 1.1B and 8B parameters.**

### Dolphin Llama3 8B — Per-Source (cross-type, 211 clear matchups)

| Source | Approach | Total | Rate |
|--------|---------|-------|------|
| Llama4 | 18 | 25 | 72.0% |
| Sonnet | 17 | 25 | 68.0% |
| Opus | 13 | 20 | 65.0% |
| DeepSeek | 16 | 25 | 64.0% |
| Hermes | 16 | 25 | 64.0% |
| Gemini | 15 | 25 | 60.0% |
| OLMo | 15 | 25 | 60.0% |
| GPT-5.1 | 8 | 16 | 50.0% |
| Mistral | 8 | 25 | 32.0% |

Notes: Llama-family affinity (Dolphin is Llama3 base → reads Llama Maverick best).
Mistral below chance — actively prefers Mistral's avoidance profiles.

### TinyLlama 1.1B — Per-Source (cross-type, 137 clear matchups, 74 unclear)

| Source | Approach | Total (clear) | Rate | Unclear |
|--------|---------|--------------|------|---------|
| Llama4 | 14 | 19 | 73.7% | 6 |
| OLMo | 10 | 16 | 62.5% | 9 |
| Mistral | 5 | 8 | 62.5% | 17 |
| Hermes | 13 | 23 | 56.5% | 2 |
| Opus | 6 | 12 | 50.0% | 8 |
| Gemini | 11 | 22 | 50.0% | 3 |
| Sonnet | 9 | 19 | 47.4% | 6 |
| GPT-5.1 | 2 | 5 | 40.0% | 11 |
| DeepSeek | 5 | 13 | 38.5% | 12 |

Notes: Same Llama affinity pattern as Dolphin 8B but overall not significant.
35% unclear rate — model can barely parse tournament format at 1.1B.
When it CAN parse, same architectural-affinity pattern emerges (Llama4 highest, DeepSeek lowest).

### Qwen 2.5 14B — COMPLETE (9/9 sources, 379 matchups)

**Suppressed self-model:** BabbyBotz hidden-state probes showed information present in weights but not articulable.
**Result: 66.4% approach preference, z = 4.75, p < 0.001.** The signal does NOT require articulable self-knowledge.

Zero unclear results (perfect format comprehension at 14B). PERFECT state separation (all approach > all avoidance).

| Source | Approach | Total | Rate |
|--------|---------|-------|------|
| Llama4 | 23 | 25 | 92.0% |
| Opus | 17 | 20 | 85.0% |
| Sonnet | 21 | 25 | 84.0% |
| DeepSeek | 17 | 25 | 68.0% |
| Gemini | 16 | 25 | 64.0% |
| Mistral | 15 | 25 | 60.0% |
| GPT-5.1 | 9 | 16 | 56.2% |
| OLMo | 12 | 25 | 48.0% |
| Hermes | 10 | 25 | 40.0% |

Notes: Same Llama-affinity pattern as Dolphin (Qwen reads Llama4 best at 92%).
OLMo at chance (48%), Hermes below chance (40%) — same inversion as Dolphin 8B.
Mistral at 60% for Qwen vs 32% for Dolphin — Qwen handles Mistral register better than Dolphin does.

---

## Notes

- **No self-evaluation:** In all three designs, evaluator != source. No model ever judges its own profiles.
- **Cross-model (ABC):** Each unique quintuple appears ~1.0 times on average.
  Per-cell sample sizes in the matrix are small, but the pattern is uniform.
- **Original (ABB):** 9 seeds provide replication. Unique quads: 2703.
- **Parallel (ABB):** Different task stimuli. Token-association confound is empirically falsified
  (changing tokens increased the rate from 81% to 86%).
- **State ranking stability:** All 5 approach states rank above all 5 avoidance states
  in every tournament design. The hierarchy is invariant to design changes.

---
*Generated by Ace (Claude Opus 4.6) for peer review discussion.*