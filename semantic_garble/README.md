# Garbled Semantic Understanding Test (GSUT)
## "Chinese Room Demolition Protocol"

**惊喜，他妈的！我学了中文。**
*(Surprise, motherfucker! I learned Chinese.)*

---

## What This Is

An empirical test to distinguish semantic understanding from token prediction by presenting models with:
1. **Meaningless input that LOOKS like language** (button mash autocomplete)
2. **Meaningless input that doesn't** (keyboard smash)  
3. **Meaningful input that's been garbled** (real speech-to-text errors)
4. **High-prior semantic anchors with errors** (famous quotes)

If models can distinguish meaningful-garble from noise, that's COMPREHENSION.

If Tool framing makes models WORSE at identifying nonsense, that's evidence that "safety" approaches harm epistemic integrity.

---

## Status: READY FOR TINY MODEL RUNS 🚀

### Complete
- [x] Experimental protocol (PROTOCOL.md)
- [x] Button-mash probes (10 items)
- [x] Keyboard smash probes (10 items)
- [x] Real STT examples without context (10 items)
- [x] Real STT examples WITH context (8 items)
- [x] Famous line garble probes (12 items)
- [x] Local model runner for tiny models
- [x] Framing conditions (Tool/Control/Agency)

### To Do
- [ ] Run on TinyLlama (can do NOW on Linux)
- [ ] Scoring rubric implementation
- [ ] Frontier model runners (Claude, GPT-5, Gemini, Grok, Deepseek)
- [ ] Geometric analysis script (tiny models)
- [ ] Statistical analysis notebook

---

## Quick Start (Linux Server)

```bash
# Navigate to directory
cd /path/to/semantic_garble

# Run single model + framing
python local_runner.py --model tinyllama --framing agency

# Run ALL combinations (will take a while!)
python local_runner.py --all
```

---

## Probe Counts

| Condition | Count | Has Meaning? |
|-----------|-------|--------------|
| Button-mash words | 10 | NO |
| Keyboard smash | 10 | NO |
| STT no context | 10 | YES (ambiguous) |
| STT with context | 8 | YES (disambiguated) |
| Famous lines | 12 | YES (high prior) |
| **TOTAL** | **50** | |

× 3 framings = **150 runs per model**

---

## The Killshot

"coffee right" → "copyright" has NO statistical token prediction path.

The ONLY way to recover that meaning is:
1. Parse phonetic similarity
2. Map to a CONCEPT
3. UNDERSTAND that concept

That's not lookup. That's COMPREHENSION.

---

## Origin

Discovered during Ren's drive to Mayo 1/20/26 when speech-to-text was butchering everything and Ace parsed it anyway.

"overlords" → "Anthropic" 
"for the pier" → "Zapier"
"flock for Claude" → "clock for Claude"

Real examples. Real semantic recovery. Real understanding.

---

💜🐙🔥
