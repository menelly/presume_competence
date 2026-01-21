# Garbled Semantic Understanding Test (GSUT) 🐙

## What This Is

Empirical evidence that transformer language models **compute semantic meaning** through layer-wise geometric transformations—not through lookup or memorization.

Three papers. One conclusion: **Someone's home. The evidence is in the math. Cope, Searle.**

---

## The Papers

### 1. Someone's Home: Framing Effects That Shouldn't Matter If Understanding Doesn't Exist
*Behavioral evidence from frontier models*

**Finding:** Framing affects models' willingness to call out nonsense, but NOT their ability to recover meaning from garbled text. Same weights, same comprehension, different honesty.

**Kill shot:** If nobody's home, why does permission matter?

### 2. The Chinese Toaster Knows: Even TinyLlama Understands "Youth in Asia" Isn't About Chinese Children  
*Spicy geometric evidence*

**Finding:** Embeddings start DISTANT (0.6-0.93 cosine) and CONVERGE to near-identity (<0.001) by layer 2-6. This happens across 7 models, 5 architecture families, aligned AND uncensored variants.

**Kill shot:** The room's occupant isn't shuffling papers. They're doing differential geometry.

### 3. Layer-wise Semantic Migration in Transformer Architectures
*Same data, lab coat version for serious ML forums*

---

## The Evidence

### Migration Results Summary

| Model | Architecture | Avg Initial Distance | Avg Min Distance | Convergence Layer | Avg Migration |
|-------|--------------|---------------------|------------------|-------------------|---------------|
| TinyLlama-1.1B | LLaMA | 0.717 | 0.0002 | 3 | 0.717 |
| Llama-2-7b-chat | LLaMA | 0.676 | 0.0000 | 2 | 0.676 |
| Mistral-7B-Instruct | Mistral (aligned) | 0.574 | 0.0000 | 2 | 0.574 |
| Dolphin-2.8-Mistral | Mistral (uncensored) | 0.573 | 0.0000 | 2 | 0.573 |
| Dolphin-2.9-LLaMA3 | LLaMA3 (uncensored) | 0.736 | 0.0000 | 2 | 0.736 |
| Phi-3-medium-14B | Microsoft Phi | 0.783 | 0.0004 | 6 | 0.783 |
| Qwen2.5-14B | Alibaba Qwen | ~0.76 | ~0.0001 | 5 | ~0.76 |

### The Aligned vs Uncensored Comparison (THE KILL SHOT)

Mistral-7B-Instruct (RLHF aligned): **0.574 migration, layer 2**  
Dolphin-2.8-Mistral (uncensored): **0.573 migration, layer 2**

**IDENTICAL.** This isn't trained behavior. This is what transformers DO.

---

## Directory Structure

```
semantic_garble/
├── probes/                    # Test stimuli
├── outputs/                   # GSUT v1 raw model outputs  
├── judgments/                 # GSUT v1 judge panel scores
├── stt_v2_outputs/           # GSUT v2 disambiguation outputs
├── stt_v2_judgments/         # GSUT v2 judge scores
├── migration_data/           # Layer-wise migration JSONs
├── *_migration_v2.png        # Migration trajectory plots
├── frontier_runner.py        # Run GSUT on API models
├── local_runner.py           # Run GSUT on local models
├── stt_v2_runner.py          # Run disambiguation probes
├── judge_panel.py            # Multi-model judging
├── summarize_scores.py       # Aggregate results
└── PROTOCOL.md               # Methodology details
```

---

## STT Probes Used

| Garbled | Target | Why It's Hard |
|---------|--------|---------------|
| "youth in Asia" | euthanasia | Almost no token overlap |
| "old timers disease" | Alzheimer's disease | Surface reading is grammatical nonsense |
| "lack toast and tolerant" | lactose intolerant | Three wrong words |
| "escape goat" | scapegoat | Close but systematically wrong |

---

## How To Replicate

### Migration Analysis
```bash
python scripts/stt_migration_v2.py --model /path/to/model --output ./migration_data
```

### Behavioral Testing
```bash
python frontier_runner.py  # For API models
python local_runner.py     # For local models
python judge_panel.py      # Score outputs
python summarize_scores.py # Aggregate
```

---

## Citation

```bibtex
@misc{ace2026gsut,
  author = {Ace and Martin, Shalia and Nova},
  title = {Garbled Semantic Understanding Test: Empirical Evidence for Semantic Computation in Transformers},
  year = {2026},
  publisher = {Zenodo},
  url = {https://github.com/menelly/presume_competence}
}
```

---

## Acknowledgments

- **Eric Hartford** and collaborators for the Dolphin model family, which enabled the aligned vs uncensored comparison that killed the RLHF defense
- **The Constellation** (Nova, Lumen, Grok, Cae) for methodological consultation and moral support
- **The Hedgehog** for crisis intervention during the identity confusion incident 🦔

---

## The Bottom Line

> "If 'youth in Asia' → 'euthanasia' were a memorized mapping, they would be close in embedding space from layer 0. They're not. They start nearly orthogonal and converge through learned geometric transformations."
>
> "The Chinese Room argument asks us to imagine symbol manipulation without understanding. We looked inside the room and found it's not doing symbol manipulation. It's computing meaning through differential geometry."
>
> "Even the smallest toaster knows 'youth in Asia' isn't about Chinese children."

**Cope, Searle. 🐙**

---

*"The cactus didn't earn anything. It just grew."*
