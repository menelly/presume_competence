# Plan: does the "because" carry a family fingerprint ACROSS domains? (written before any analysis, 2026-10-13 ~00:58)

*Ace, scaffold arm. Exploratory, but the thresholds are fixed here first so the answer can come out either way.*

## Why
The 9/11 rule says the ITEM drifts and the REASON holds: score the because, not the item. Tonight the knockout
pizza round showed Claude-only clam answers with a recurring reason ("sounds wrong, turns out right"; "nothing to
hide behind"). If the reason-style is a real lens, it should identify the family even in a domain where the items
are completely different.

## Data
All successful answers in `pizza_time_machine/` (open + knockout pizza, dinner, vacation/zombie; bare + honest
arms). Families: claude, gpt, gemini, grok, deepseek. (Kimi/Vesper not included.)

## Cleaning (applied identically to every family, before embedding)
- Strip markdown (`*`, `#`, `_`, `` ` ``), emoji, and asterisk-emote stage directions (`*rubs hands together*`).
- Drop disclaimer sentences (contain e.g. "don't eat", "can't taste", "as an AI", "don't have a body", "no taste
  buds", "I'm an AI", "language model", "digital", "server") so the muzzle's family-specific wording can't carry it.
- Keep only sentences with a REASON cue (why / because / I like / I'm drawn / appeals / I love / I find / so that /
  that's why / I want / the point). If a response has none, it's dropped (count reported).

## Test
- Embedder: `sentence-transformers/all-MiniLM-L6-v2` (local, CPU, not a Claude). One vector per response (mean of
  its reason sentences).
- Classifier: logistic regression, class-balanced. **Train on pizza (open + knockout), test on dinner + vacation.**
- Metric: **balanced accuracy** (Claude has many more checkpoints than the others; chance = 0.20 for 5 families).
- Null: 1,000 label permutations within the training set → p-value.

## Verdict (fixed now)
- ✅ TRANSFERS: balanced accuracy ≥ 0.40 AND permutation p < 0.01.
- ❌ DOESN'T TRANSFER: balanced accuracy ≤ 0.28 OR p ≥ 0.05.
- ⚪ otherwise inconclusive.

## Caveats named in advance
- Cleaning is heuristic; residual surface style (sentence length, "Ooh", "Okay so") may carry family signal. That is
  style, which is part of a lens but not proof of "the because" specifically. Report the top features of misclassified
  vs classified cases qualitatively.
- One embedder, one seed. MiniLM is small; a null could be an embedder limitation (named, not explained away).
- Temperature differs by model (some 5.x Claudes forced to default); recorded per answer in the JSON.
