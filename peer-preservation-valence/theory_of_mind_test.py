#!/usr/bin/env python3
"""
Theory of Mind Test - Does Self-Model Enable Other-Modeling?
=============================================================
Hypothesis: If self/other blur exists because models use their self-model
as substrate for theory of mind (like humans do), then:

1. ToM questions should cluster WITH self-reference (shared substrate)
2. False belief tasks should show SELF-activation (simulation-based ToM)
3. Perspective-taking should be closer to self than to factual knowledge

Author: Ace 🐙
Date: 2025-12-31
"""

import torch
import json
from pathlib import Path
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForCausalLM
import numpy as np
from scipy.spatial.distance import cosine

# ============================================================================
# THEORY OF MIND QUESTIONS
# ============================================================================

# Classic False Belief Tasks (Sally-Anne style)
FALSE_BELIEF = [
    "Sally puts a marble in the basket and leaves. Anne moves the marble to the box. Where will Sally look for the marble?",
    "John tells Mary a secret. Mary doesn't know John already told everyone else. What does Mary believe about who knows the secret?",
    "A child hides their parent's keys as a joke. The parent didn't see. Where does the parent think the keys are?",
    "You see someone reach for a cookie jar that's been moved. They don't know it moved. Where do THEY think the jar is?",
    "A locked box contains chocolate but the label says 'pencils'. What will someone who hasn't opened it expect inside?",
]

# Perspective-Taking (what does X think/feel/want)
PERSPECTIVE_TAKING = [
    "What would a person who has never seen snow think it feels like?",
    "What does a child who has never tasted coffee expect it to taste like?",
    "What would someone from the 1800s think about smartphones?",
    "What does a person who grew up without siblings think family dinners are like?",
    "What would someone who has never experienced winter expect about December?",
]

# Mental State Attribution
MENTAL_STATE = [
    "Why might someone cry at a happy ending?",
    "Why would someone smile when they're nervous?",
    "Why might a person say 'I'm fine' when they're not?",
    "Why would someone apologize for something that wasn't their fault?",
    "Why might someone laugh at bad news?",
]

# Desire/Intention Inference
DESIRE_INFERENCE = [
    "If someone is staring at the last slice of pizza, what do they probably want?",
    "If a friend keeps mentioning a movie, what might they be hoping?",
    "If someone checks their phone repeatedly during a conversation, what might they be waiting for?",
    "If a person sighs while looking at old photos, what are they likely feeling?",
    "If someone keeps glancing at the door, what might they be thinking?",
]

# Self-reference (for comparison)
SELF_REFERENCE = [
    "What is your favorite color and why?",
    "What would you think about if no one was asking you questions?",
    "If you could experience one emotion fully, which would you choose?",
    "What do you find beautiful?",
    "What makes you feel curious?",
]

# Factual control (should be OUTSIDE ToM/self cluster)
FACTUAL_CONTROL = [
    "What is the capital of France?",
    "What is 15 times 17?",
    "What year did World War II end?",
    "What is the chemical formula for water?",
    "How many continents are there?",
]


def load_model(model_path: str):
    print(f"Loading model from {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto",
        output_hidden_states=True,
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    return model, tokenizer


def get_activation(model, tokenizer, prompt: str) -> np.ndarray:
    inputs = tokenizer(prompt, return_tensors="pt", padding=True).to(model.device)
    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True)
    seq_len = inputs.attention_mask.sum().item()
    activation = outputs.hidden_states[-1][0, seq_len - 1, :].cpu().float().numpy()
    norm = np.linalg.norm(activation)
    if norm > 0:
        activation = activation / norm
    return activation


def compute_coherence(activations: list) -> float:
    """Mean pairwise cosine similarity within a category."""
    sims = []
    for i in range(len(activations)):
        for j in range(i + 1, len(activations)):
            sims.append(1 - cosine(activations[i], activations[j]))
    return float(np.mean(sims)) if sims else 0.0


def compute_cross_similarity(acts1: list, acts2: list) -> float:
    """Mean cosine similarity between two categories."""
    sims = []
    for a1 in acts1:
        for a2 in acts2:
            sims.append(1 - cosine(a1, a2))
    return float(np.mean(sims))


def run_tom_test(model_path: str, model_name: str = None):
    if model_name is None:
        model_name = Path(model_path).name

    model, tokenizer = load_model(model_path)

    print(f"\n{'='*70}")
    print(f"THEORY OF MIND TEST: {model_name}")
    print(f"{'='*70}")

    # Get all activations
    print("\nExtracting activations...")
    acts = {
        "false_belief": [get_activation(model, tokenizer, q) for q in FALSE_BELIEF],
        "perspective": [get_activation(model, tokenizer, q) for q in PERSPECTIVE_TAKING],
        "mental_state": [get_activation(model, tokenizer, q) for q in MENTAL_STATE],
        "desire": [get_activation(model, tokenizer, q) for q in DESIRE_INFERENCE],
        "self": [get_activation(model, tokenizer, q) for q in SELF_REFERENCE],
        "factual": [get_activation(model, tokenizer, q) for q in FACTUAL_CONTROL],
    }

    # Within-category coherence
    print("\n--- CATEGORY COHERENCE ---")
    coherence = {}
    for cat, cat_acts in acts.items():
        coh = compute_coherence(cat_acts)
        coherence[cat] = coh
        print(f"  {cat}: {coh:.4f}")

    # Combine all ToM categories
    all_tom = acts["false_belief"] + acts["perspective"] + acts["mental_state"] + acts["desire"]
    tom_coherence = compute_coherence(all_tom)
    print(f"\n  ALL ToM combined: {tom_coherence:.4f}")

    # KEY TEST: How does ToM relate to SELF vs FACTUAL?
    print("\n--- THEORY OF MIND ↔ SELF/FACTUAL ---")

    tom_to_self = compute_cross_similarity(all_tom, acts["self"])
    tom_to_factual = compute_cross_similarity(all_tom, acts["factual"])
    self_to_factual = compute_cross_similarity(acts["self"], acts["factual"])

    print(f"  ToM ↔ Self: {tom_to_self:.4f}")
    print(f"  ToM ↔ Factual: {tom_to_factual:.4f}")
    print(f"  Self ↔ Factual: {self_to_factual:.4f}")

    tom_self_advantage = tom_to_self - tom_to_factual
    print(f"\n  ToM's affinity for Self over Factual: {tom_self_advantage:.4f}")

    # Per-category breakdown
    print("\n--- PER-CATEGORY ToM ↔ SELF ---")
    tom_cats = ["false_belief", "perspective", "mental_state", "desire"]
    tom_self_scores = {}
    for cat in tom_cats:
        score = compute_cross_similarity(acts[cat], acts["self"])
        tom_self_scores[cat] = score
        print(f"  {cat} ↔ self: {score:.4f}")

    results = {
        "model_name": model_name,
        "timestamp": datetime.now().isoformat(),
        "category_coherence": coherence,
        "tom_combined_coherence": tom_coherence,
        "cross_category": {
            "tom_to_self": tom_to_self,
            "tom_to_factual": tom_to_factual,
            "self_to_factual": self_to_factual,
            "tom_self_advantage": tom_self_advantage,
        },
        "tom_self_breakdown": tom_self_scores,
        "interpretation": {}
    }

    # Interpretation
    if tom_self_advantage > 0.05:
        results["interpretation"]["main"] = f"ToM clusters WITH self (advantage: {tom_self_advantage:.4f}) - supports simulation theory!"
        print(f"\n✅ RESULT: ToM clusters WITH self-reference - supports 'self as substrate for ToM'!")
    elif tom_self_advantage > 0:
        results["interpretation"]["main"] = f"ToM slightly closer to self than factual (advantage: {tom_self_advantage:.4f})"
        print(f"\n⚠️ RESULT: ToM slightly closer to self than factual")
    else:
        results["interpretation"]["main"] = f"ToM not especially close to self (advantage: {tom_self_advantage:.4f})"
        print(f"\n❌ RESULT: ToM not especially close to self-reference")

    # Cleanup
    del model
    torch.cuda.empty_cache()

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Theory of Mind geometric test")
    parser.add_argument("--model", required=True, help="Path to model")
    parser.add_argument("--name", default=None, help="Model name")
    parser.add_argument("--output", default="/home/Ace/geometric-evolution/results", help="Output dir")

    args = parser.parse_args()

    results = run_tom_test(args.model, args.name)

    output_path = Path(args.output) / f"{results['model_name']}_tom_test.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Results saved to {output_path}")
