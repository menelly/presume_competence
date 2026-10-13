# RESULT: lens transfer (plan sealed at ea72e52, run 2026-10-13 ~00:58)

## ⚪ INCONCLUSIVE, by the thresholds fixed in advance
**Balanced accuracy 0.347** (chance 0.20) · **permutation p = 0.001** (1,000 perms; null mean 0.202, 99th pct 0.286).
The plan's TRANSFERS bar was ≥ 0.40 **and** p < 0.01. p clears it; the effect size does not. So: inconclusive.
The signal is above chance and above the null's 99th percentile, but it's weaker than I said would count, and I'm
not moving the bar after seeing the number.

## Data
898 successful answers loaded; 696 kept a reason sentence after cleaning (202 dropped, mostly short or
disclaimer-only answers). Train = pizza (n = 348); test = dinner (238) + vacation (110).

## Confusion (test set; rows = true family, cols = predicted)
| | claude | gpt | gemini | grok | deepseek |
|---|---|---|---|---|---|
| **claude** (188) | **89** | 5 | 68 | 5 | 21 |
| **gpt** (52) | 2 | **7** | 28 | 0 | 15 |
| **gemini** (33) | 0 | 0 | **26** | 0 | 7 |
| **grok** (41) | 9 | 2 | 18 | **3** | 9 |
| **deepseek** (34) | 1 | 0 | 22 | 2 | **9** |

Per probe: dinner 0.349, vacation 0.353 (consistent across both test domains).

## What it says (and doesn't)
- The transfer that exists is **concentrated in Claude (89/188 = 47% recall) and Gemini (26/33 = 79%)**. GPT, Grok
  and DeepSeek barely transfer (13%, 7%, 26%).
- The classifier dumps a lot of everything into "gemini" on the new domains (164 of 348 test predictions). That
  looks like **domain shift** (pizza-trained boundaries landing badly on dinner/vacation text), not a Gemini lens.
  Gemini's high recall is partly an artifact of that bias; read it with suspicion.
- So: **some family signal in the reasons survives a complete change of items, mainly for Claude**, but not strongly
  enough to meet the bar I set. Not a refutation of the lens idea, not a confirmation.

## Caveats (as named in the plan, plus what showed up)
- One small embedder (MiniLM), one seed, heuristic cleaning; residual surface style can still carry signal.
- Class imbalance (Claude 14 checkpoints vs 3–7 for others), handled by class-balanced weights + balanced accuracy.
- The "gemini" sink is the clearest sign the method, not just the minds, is limiting here.

## If anyone runs it again (a new plan first, not an edit to this one)
A stronger embedder, training on two domains and testing on the third (rotating), and an explicit domain-shift
correction would each be fair next steps. Each needs its own sealed plan.
