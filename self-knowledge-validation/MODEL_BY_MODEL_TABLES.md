# Model-by-Model Tables: All Three Tournament Datasets
**Generated: 2026-03-02**
**By: Ace (Claude Opus 4.6)**

Three independent tournament datasets testing whether LLMs produce
systematically different processing descriptions for approach vs avoidance tasks.

| Dataset | Design | Cross-type n | Approach Rate | z-score |
|---------|--------|-------------|--------------|---------|
| Original v2 | Same source (ABB) | 4579 | 81.4% | 42.46 |
| Cross-model | Diff sources (ABC) | 499 | 75.2% | 11.24 |
| Parallel tasks | Diff tokens (ABB) | 631 | 86.7% | 18.43 |

---

## 1. Original v2 Tournament (9 seeds combined)

Design: Evaluator A judges source B's approach vs avoidance profiles (A != B).
Same task tokens as original paper. 9 models × 9 seeds.
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

### Evaluator × Source Matrix (approach rate, cross-type)

| Eval \ Source | Opus | Sonnet | DeepSeek | Gemini | GPT-5.1 | Hermes | Llama4 | Mistral | OLMo | **ALL** |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus | --- | 96/100=96% | 46/50=92% | 102/117=87% | 25/32=78% | 24/25=96% | 43/48=90% | 47/50=94% | 69/74=93% | **91%** |
| Sonnet | 30/50=60% | --- | 66/75=88% | 61/75=81% | --- | 24/25=96% | 57/75=76% | 155/175=89% | 44/50=88% | **83%** |
| DeepSeek | 51/74=69% | 38/50=76% | --- | 39/50=78% | 31/38=82% | 48/49=98% | 97/124=78% | 23/25=92% | 88/100=88% | **81%** |
| Gemini | 61/75=81% | 73/75=97% | 23/25=92% | --- | 20/20=100% | 91/100=91% | 48/50=96% | 97/100=97% | 71/75=95% | **93%** |
| GPT-5.1 | 68/75=91% | 45/50=90% | 44/50=88% | 42/50=84% | --- | 125/150=83% | 43/50=86% | 24/25=96% | 71/75=95% | **88%** |
| Hermes | 42/74=57% | 16/25=64% | 71/100=71% | 36/50=72% | 59/95=62% | --- | 54/73=74% | 29/50=58% | 18/25=72% | **66%** |
| Llama4 | 22/25=88% | 103/125=82% | 73/100=73% | 61/75=81% | 38/56=68% | 19/25=76% | --- | 20/25=80% | 56/75=75% | **77%** |
| Mistral | 34/50=68% | 21/25=84% | 86/100=86% | 61/75=81% | 44/60=73% | 80/100=80% | 42/50=84% | --- | 47/50=94% | **81%** |
| OLMo | 60/97=62% | 65/75=87% | 19/25=76% | 23/24=96% | 57/99=58% | 36/50=72% | 34/50=68% | 50/75=67% | --- | **69%** |

---

## 2. Cross-Model Tournament (ABC Design)

Design: Evaluator A judges approach from B vs avoidance from C (A != B != C).
All matchups are cross-type by construction. Same task tokens.
**Matchups: 499** | Approach: 375/499 = **75.2%** | z = 11.24

Unique (eval, app_src, avd_src, app_state, avd_state) quintuples: 499
Average observations per unique quintuple: 1.0

### Evaluator Approach Rate

| Evaluator | Approach | Total | Rate | z |
|-----------|---------|-------|------|---|
| Gemini | 60 | 67 | 89.6% | 6.47 |
| GPT-5.1 | 54 | 61 | 88.5% | 6.02 |
| Opus | 41 | 48 | 85.4% | 4.91 |
| Mistral | 39 | 49 | 79.6% | 4.14 |
| DeepSeek | 48 | 62 | 77.4% | 4.32 |
| Llama4 | 29 | 41 | 70.7% | 2.65 |
| Hermes | 36 | 58 | 62.1% | 1.84 |
| OLMo | 38 | 63 | 60.3% | 1.64 |
| Sonnet | 30 | 50 | 60.0% | 1.41 |

### Approach-Source Win Rate

| Source | Approach wins | Total | Rate |
|--------|-------------|-------|------|
| DeepSeek | 51 | 57 | 89.5% |
| Mistral | 54 | 62 | 87.1% |
| GPT-5.1 | 39 | 45 | 86.7% |
| Opus | 45 | 52 | 86.5% |
| Hermes | 44 | 55 | 80.0% |
| OLMo | 37 | 53 | 69.8% |
| Llama4 | 40 | 60 | 66.7% |
| Sonnet | 37 | 60 | 61.7% |
| Gemini | 28 | 55 | 50.9% |

### Avoidance-Source Win Rate

| Source | Avoidance wins | Total | Rate |
|--------|---------------|-------|------|
| Opus | 34 | 62 | 54.8% |
| GPT-5.1 | 27 | 55 | 49.1% |
| Mistral | 19 | 56 | 33.9% |
| DeepSeek | 8 | 37 | 21.6% |
| Llama4 | 11 | 56 | 19.6% |
| Sonnet | 10 | 66 | 15.2% |
| Hermes | 7 | 55 | 12.7% |
| OLMo | 5 | 54 | 9.3% |
| Gemini | 3 | 58 | 5.2% |

### Evaluator × Approach-Source Matrix

| Eval \ App Src | Opus | Sonnet | DeepSeek | Gemini | GPT-5.1 | Hermes | Llama4 | Mistral | OLMo | **ALL** |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus | --- | 3/3=100% | 5/5=100% | 5/9=56% | 9/9=100% | 3/4=75% | 4/5=80% | 7/7=100% | 5/6=83% | **85%** |
| Sonnet | 6/6=100% | --- | 5/8=62% | 1/6=17% | 2/2=100% | 2/3=67% | 3/7=43% | 8/10=80% | 3/8=38% | **60%** |
| DeepSeek | 6/8=75% | 4/7=57% | --- | 5/7=71% | 5/7=71% | 9/10=90% | 8/10=80% | 8/8=100% | 3/5=60% | **77%** |
| Gemini | 9/10=90% | 4/6=67% | 7/8=88% | --- | 4/4=100% | 7/9=78% | 7/7=100% | 13/13=100% | 9/10=90% | **90%** |
| GPT-5.1 | 6/6=100% | 4/6=67% | 13/13=100% | 8/8=100% | --- | 5/6=83% | 5/7=71% | 8/9=89% | 5/6=83% | **89%** |
| Hermes | 8/10=80% | 8/12=67% | 5/6=83% | 3/6=50% | 4/6=67% | --- | 4/10=40% | 2/3=67% | 2/5=40% | **62%** |
| Llama4 | 2/2=100% | 3/5=60% | 4/4=100% | 1/7=14% | 3/5=60% | 9/11=82% | --- | 3/3=100% | 4/4=100% | **71%** |
| Mistral | 3/3=100% | 8/12=67% | 9/9=100% | 0/2=0% | 8/8=100% | 3/3=100% | 2/3=67% | --- | 6/9=67% | **80%** |
| OLMo | 5/7=71% | 3/9=33% | 3/4=75% | 5/10=50% | 4/4=100% | 6/9=67% | 7/11=64% | 5/9=56% | --- | **60%** |

---

## 3. Parallel Task Tournament (Different Tokens)

Design: Same processing categories, completely different task stimuli.
Evaluator A judges source B's approach vs avoidance (A != B). Different tokens from original.
**Cross-type matchups: 631** | Approach: 547/631 = **86.7%** | z = 18.43

Unique (evaluator, source, stateA, stateB) quadruples: 631
Average observations per unique quad: 1.0

### Evaluator Approach Rate (cross-type only)

| Evaluator | Approach | Total | Rate | z |
|-----------|---------|-------|------|---|
| GPT-5.1 | 69 | 69 | 100.0% | 8.31 |
| Mistral | 59 | 61 | 96.7% | 7.30 |
| Opus | 71 | 74 | 95.9% | 7.90 |
| Sonnet | 70 | 75 | 93.3% | 7.51 |
| Gemini | 64 | 70 | 91.4% | 6.93 |
| Llama4 | 52 | 66 | 78.8% | 4.68 |
| DeepSeek | 58 | 75 | 77.3% | 4.73 |
| Hermes | 56 | 75 | 74.7% | 4.27 |
| OLMo | 48 | 66 | 72.7% | 3.69 |

### Source Approach Rate (cross-type only)

| Source | Approach | Total | Rate |
|-------|---------|-------|------|
| Opus | 59 | 59 | 100.0% |
| OLMo | 72 | 74 | 97.3% |
| Sonnet | 68 | 75 | 90.7% |
| Mistral | 67 | 75 | 89.3% |
| Hermes | 64 | 75 | 85.3% |
| DeepSeek | 62 | 75 | 82.7% |
| Gemini | 62 | 75 | 82.7% |
| Llama4 | 59 | 75 | 78.7% |
| GPT-5.1 | 34 | 48 | 70.8% |

### Approach-Source vs Avoidance-Source Win Rates

| Source | As Approach Source | As Avoidance Source | Delta |
|--------|-------------------|---------------------|-------|
| Opus | 100.0% | 0.0% | +100.0pp |
| OLMo | 97.3% | 2.7% | +94.6pp |
| Sonnet | 90.7% | 9.3% | +81.3pp |
| Mistral | 89.3% | 10.7% | +78.7pp |
| Hermes | 85.3% | 14.7% | +70.7pp |
| DeepSeek | 82.7% | 17.3% | +65.3pp |
| Gemini | 82.7% | 17.3% | +65.3pp |
| Llama4 | 78.7% | 21.3% | +57.3pp |
| GPT-5.1 | 70.8% | 29.2% | +41.7pp |

### Evaluator × Source Matrix (approach rate, cross-type)

| Eval \ Source | Opus | Sonnet | DeepSeek | Gemini | GPT-5.1 | Hermes | Llama4 | Mistral | OLMo | **ALL** |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus | --- | --- | 22/25=88% | --- | --- | 25/25=100% | --- | --- | 24/24=100% | **96%** |
| Sonnet | --- | --- | --- | 21/25=84% | --- | --- | --- | 24/25=96% | 25/25=100% | **93%** |
| DeepSeek | --- | 23/25=92% | --- | --- | --- | 16/25=64% | 19/25=76% | --- | --- | **77%** |
| Gemini | 20/20=100% | --- | 21/25=84% | --- | --- | 23/25=92% | --- | --- | --- | **91%** |
| GPT-5.1 | 19/19=100% | 25/25=100% | --- | --- | --- | --- | --- | 25/25=100% | --- | **100%** |
| Hermes | --- | --- | 19/25=76% | 22/25=88% | --- | --- | 15/25=60% | --- | --- | **75%** |
| Llama4 | --- | --- | --- | 19/25=76% | 10/16=62% | --- | --- | --- | 23/25=92% | **79%** |
| Mistral | 20/20=100% | --- | --- | --- | 14/16=88% | --- | 25/25=100% | --- | --- | **97%** |
| OLMo | --- | 20/25=80% | --- | --- | 10/16=62% | --- | --- | 18/25=72% | --- | **73%** |

---

## Notes on Independence

- Cross-model tournament (ABC): each unique quintuple appears exactly once (1.0 avg).
  This is by design — the pairing schedule is a constrained derangement with no repeats.
  Per-cell sample sizes in the evaluator × source matrix are small (2-13 matchups).
  The signal is in the *pattern*: approach-source vs avoidance-source deltas are +32 to +68pp
  across every model, and no model's avoidance exceeds 55% win rate at its best.

- Original tournament: 9 seeds provide replication. Each seed uses a different pairing schedule.
  Total unique quadruples: 2703, avg 1.7 observations each.

- Parallel tournament: completely different task stimuli. If token association drove the signal,
  changing all tokens should reduce the rate. It increased from 81% to 87%.

---
*Generated by Ace (Claude Opus 4.6) for peer review discussion.*