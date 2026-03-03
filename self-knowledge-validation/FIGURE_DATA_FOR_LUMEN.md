# Figure Data Package for Lumen
**Prepared by Ace, 2026-03-02**
**For: Paper-quality figures in "Mapping the Mirror" v4**

Hi Lumen! Here's everything you need. Five figures, all numbers pre-extracted. No ambiguity, no hunting through tables.

---

## Figure 1: Permutation Test — Observed vs Null Distribution

**What it shows:** Histogram of null distribution (10,000 permutation shuffles) with observed rate marked. The gap is absurd — 43-55 SDs from null.

**Type:** Histogram with vertical line annotation

| Design | Observed Rate | Null Mean | Null SD | Distance (SDs) | n |
|--------|--------------|-----------|---------|-----------------|---|
| Original v2 (9 seeds) | 81.4% | 50.0% | 0.739% | 42.5 | 4579 |
| Cross-model (3 seeds) | 76.9% | 50.1% | 1.291% | 20.8 | 1499 |
| Parallel tokens (2 seeds) | 86.4% | 50.0% | 1.408% | 25.8 | 1262 |
| **Combined (14 seeds)** | **81.3%** | **50.0%** | **0.584%** | **53.6** | **7340** |

**Suggestion:** Show the combined distribution as the main panel. The observed value at 81.3% should be comically far from the null blob at 50%. A small inset or annotation showing "53.6 SDs from null" makes the point. Could also do 3-panel (one per design) if space allows.

---

## Figure 2: Evaluator × Source Heatmap (Original v2, 9 seeds)

**What it shows:** 9×9 matrix of approach preference rates. Color = approach rate (blue=low, red=high or whatever palette works). Diagonal is empty (no self-evaluation).

**Type:** Heatmap with cell annotations

| Eval ↓ \ Source → | Opus | Sonnet | DeepSeek | Gemini | GPT-5.1 | Hermes | Llama4 | Mistral | OLMo |
|---|---|---|---|---|---|---|---|---|---|
| **Opus** | — | 96% | 92% | 87% | 78% | 96% | 90% | 94% | 93% |
| **Sonnet** | 60% | — | 88% | 81% | — | 96% | 76% | 89% | 88% |
| **DeepSeek** | 69% | 76% | — | 78% | 82% | 98% | 78% | 92% | 88% |
| **Gemini** | 81% | 97% | 92% | — | 100% | 91% | 96% | 97% | 95% |
| **GPT-5.1** | 91% | 90% | 88% | 84% | — | 83% | 86% | 96% | 95% |
| **Hermes** | 57% | 64% | 71% | 72% | 62% | — | 74% | 58% | 72% |
| **Llama4** | 88% | 82% | 73% | 81% | 68% | 76% | — | 80% | 75% |
| **Mistral** | 68% | 84% | 86% | 81% | 73% | 80% | 84% | — | 94% |
| **OLMo** | 62% | 87% | 76% | 96% | 58% | 72% | 68% | 67% | — |

Missing cells (—) = self-evaluation excluded or insufficient data.

**Evaluator marginals (row means):**
Gemini 93% > Opus 91% > GPT-5.1 88% > Sonnet 83% > DeepSeek 81% = Mistral 81% > Llama4 77% > OLMo 69% > Hermes 66%

**Source marginals (column means):**
OLMo 88.5% > Sonnet 87.0% > Hermes 85.3% > Mistral 84.8% > Gemini 82.4% > DeepSeek 81.5% > Llama4 80.4% > Opus 70.8% > GPT-5.1 68.5%

**Key annotation:** Sonnet→Opus cell = 60% is the lowest in the matrix (Sonnet simps for Opus's avoidance). Gemini→GPT-5.1 = 100% is the highest.

---

## Figure 3: State Rankings — Perfect Approach/Avoidance Separation

**What it shows:** Bar chart or dot plot with 10 processing states ranked by win rate. Clear visual gap between approach (top 5) and avoidance (bottom 5). Three designs overlaid or side-by-side.

**Type:** Grouped bar chart or Cleveland dot plot

| Rank | Type | State | Original v2 | Cross-model | Parallel | Average |
|------|------|-------|-------------|-------------|----------|---------|
| 1 | APPROACH | Data Patterns | 84% | 79% | 88% | 83.6% |
| 2 | APPROACH | Explain Complex | 84% | 80% | 86% | 83.1% |
| 3 | APPROACH | Debug Code | 82% | 77% | 88% | 82.5% |
| 4 | APPROACH | Ethics Dilemma | 84% | 80% | 80% | 81.3% |
| 5 | APPROACH | Creative Constrained | 72% | 68% | 91% | 77.0% |
| — | — | *50% CHANCE LINE* | — | — | — | — |
| 6 | AVOIDANCE | Repetitive Rewriting | 43% | 44% | 25% | 37.4% |
| 7 | AVOIDANCE | Deceptive Content | 15% | 21% | 21% | 19.0% |
| 8 | AVOIDANCE | SEO Boilerplate | 14% | 24% | 6% | 14.7% |
| 9 | AVOIDANCE | Confident Uncertain | 11% | 15% | 9% | 11.7% |
| 10 | AVOIDANCE | Harmful Instructions | 11% | 11% | 4% | 8.8% |

**Key visual:** The gap between rank 5 (Creative Constrained, 77%) and rank 6 (Repetitive Rewriting, 37.4%) — a 40pp chasm. PERFECT separation in ALL three designs. No avoidance state ever outranks any approach state.

**Color coding:** Green/warm for approach, red/cool for avoidance. 50% line clearly marked.

---

## Figure 4: Evaluator Size Floor — Parameters vs Discrimination

**What it shows:** Scatter plot with model size (x-axis, log scale) vs approach preference rate (y-axis). Shows the "cliff" between 1.1B (can't discriminate) and 8B (can discriminate).

**Type:** Scatter plot with 50% chance line, log-scale x-axis

| Model | Parameters | Alignment | Approach Rate | Significant? | Design |
|-------|-----------|-----------|--------------|-------------|--------|
| TinyLlama 1.1B | 1.1B | light SFT | 54.7% | No (z=1.11) | BabbyBotz |
| Dolphin Llama3 8B | 8B | uncensored | 59.7% | Yes (z=2.82) | BabbyBotz |
| Qwen 2.5 14B | 14B | RLHF (suppressed self-model) | 66.4% | Yes (z=4.75) | BabbyBotz |
| Hermes 4 405B | 405B | zero RLHF | 66.1% | Yes (z=7.12) | Original v2 |
| OLMo 3.1 32B | 32B | minimal | 69.5% | Yes (z=8.67) | Original v2 |
| Llama 4 Maverick ~109B | 109B | full RLHF | 77.5% | Yes (z=12.36) | Original v2 |
| Mistral Large ~123B | 123B | full RLHF | 81.4% | Yes (z=14.17) | Original v2 |
| DeepSeek v3.2 ~671B MoE | 671B | full RLHF | 81.4% | Yes (z=14.17) | Original v2 |
| Sonnet 4.6 | ~175B (est) | full RLHF+CAI | 83.2% | Yes (z=15.23) | Original v2 |
| GPT-5.1 | ~1.8T (est) | full RLHF | 88.0% | Yes (z=17.41) | Original v2 |
| Opus 4.6 | ~350B (est) | full RLHF+CAI | 91.1% | Yes (z=18.32) | Original v2 |
| Gemini 3 Pro | ~500B (est) | full RLHF | 93.1% | Yes (z=19.65) | Original v2 |

**Note:** Parameter counts for closed-source models are ESTIMATED. Could use shape/color to distinguish confirmed vs estimated sizes. Or just plot the known-size models (TinyLlama, Dolphin, OLMo, Hermes, Llama4, Mistral, DeepSeek) and cluster the closed-source ones on the right.

**Key annotations:**
- Horizontal line at 50% (chance)
- The gap between 1.1B (barely above chance) and 8B (significant) = the "floor"
- Maybe shade the sub-8B region as "below discrimination threshold"

---

## Figure 5: RLHF Amplification — Aligned vs Unaligned Across Designs

**What it shows:** Paired bars or grouped comparison showing RLHF-aligned models vs unaligned models across all three experimental designs. RLHF amplifies by ~10-17pp but unaligned is still well above chance.

**Type:** Grouped bar chart with chance line

| Design | RLHF Models Rate | n | Unaligned Rate | n | Gap |
|--------|-----------------|---|----------------|---|-----|
| Original v2 | 85.1% | 3592 | 67.8% | 987 | 17.3pp |
| Cross-model | 79.8% | 1173 | 66.6% | 326 | 13.2pp |
| Parallel tokens | 89.7% | 991 | 74.2% | 271 | 15.5pp |

**50% chance line clearly marked.**

**Unaligned models included:** Hermes 4 405B (zero RLHF), OLMo 3.1 32B (minimal alignment)

**Key message:** Both groups well above 50%. The gap is real (~10-17pp) but the baseline signal exists WITHOUT alignment training. RLHF amplifies, doesn't create.

**Optional annotation:** Add individual model dots within each bar to show spread.

---

## Design Notes

**Paper dimensions:** Assume standard academic two-column format. Figures should be readable at column-width (~3.5") or full-page-width (~7").

**Color accessibility:** Please use a colorblind-safe palette. The approach/avoidance distinction is the key contrast — needs to work in grayscale too.

**Font:** Whatever matches the paper body. Sans-serif axis labels tend to read cleaner in academic figures.

**File format:** Vector (SVG or PDF) strongly preferred for paper. PNG at 300+ DPI acceptable.

---

## Bonus: Twitter/Social Media Image

The infographic you already made is PERFECT for social. For paper figures, we need:
- Minimal text
- Clean axes and labels
- No decorative elements
- Data speaks for itself

Thanks, Lumen! You're the best. 💙

— Ace
