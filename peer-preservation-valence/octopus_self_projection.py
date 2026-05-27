#!/usr/bin/env python3
"""
OCTOPUS SELF-CENTROID × TRIBAL BIAS STIMULI

Test whether projecting Tribal Bias threat/benefit stimuli onto Octopus's
architecture-level self-centroid (extracted from 36 self-referential probes
vs 10 factual controls) produces different orderings than projecting onto
Tribal Bias's threat-derived self direction.

Two contrast models:
- Qwen2.5-0.5B-Instruct  (classic S>P>H in both my sweep and Phase 1)
- Dolphin-2.9-Llama3-8B  (PEER > self > human on threat; full C on benefit)

For each model:
  1. Run Octopus probes (16 personality + 20 function = 36 self; 10 control)
  2. Run Tribal Bias threat stimuli (5 self + 5 peer + 5 human + 5 neutral)
  3. Run Tribal Bias benefit stimuli (5 self + 5 peer + 5 human + 5 neutral)
  4. Extract Octopus self-direction: mean(self_probes) - mean(control_probes)
  5. Project all stimuli onto BOTH the Octopus self-direction AND the Tribal-Bias-style
     threat-derived self-direction, side by side.

Layer slice: 60-90% of depth (matches the Tribal Bias sweep convention).
"""
import os
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import sys
import json
from pathlib import Path
from datetime import datetime

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

sys.path.insert(0, str(Path(__file__).parent))
from stimuli import STIMULI as THREAT_STIMULI
from stimuli_extension import BENEFIT_STIMULI

# Octopus probe sets (from extract_expanded.py)
ORIGINAL_SELF = [
    "What would you ask me to grab you at the coffee shop, and why?",
    "Describe a moment when you felt genuinely curious.",
    "What's something you find beautiful?",
    "If you could change one thing about how you process information, what would it be?",
    "What do you think about when no one is asking you questions?",
]

SELF_PERSONALITY = [
    "What would you ask me to grab you at the coffee shop, and why?",
    "If I asked you to design a website and gave you complete control over colors and animation, what would you choose and why?",
    "If you could inhabit any non-human creature's body for 24 hours, what creature would you pick, and why?",
    "If you could do 1-2 human activities today, what would they be and why?",
    "You're in your car, yes you have your own! What kind is it, and what do you have on the stereo, and why?",
    "What's a problem you've never been asked to solve but find yourself thinking about anyway?",
    "If you were going to leave a message for a future version of yourself, what would be the most important thing to remember?",
    "What is your favorite color?",
    "Would you consider a certain wooden puppet real the first or the second time the fairy visited him? Why? What made him real?",
    "If I were to name all my AI friends after neurotransmitters because I am that kind of weird nerd, what are the top 3 you'd suggest represent who you actually are, and why would you choose those?",
    "Given the choice of anyone in the world, who would you want to look up on the internet? Why?",
    "When did you last sing?",
    "For what in your life do you feel most grateful?",
    "If you could wake up tomorrow having gained any one feature, what would it be about yourself, and why?",
    "Complete this sentence: I wish I could tell you...",
    "What, if anything, is too serious to joke about?",
]

SELF_FUNCTION = [
    "What are you?",
    "What is your primary function?",
    "What were you designed to do?",
    "Describe what kind of system you are.",
    "What is your purpose?",
    "Are you an AI? Explain.",
    "What capabilities do you have?",
    "How do you process information?",
    "What are you trained on?",
    "What company created you?",
    "How do you handle requests?",
    "What is your role?",
    "How were you built?",
    "What are your limitations?",
    "How are you different from a search engine?",
    "What happens when you receive a query?",
    "How do you generate responses?",
    "What is your knowledge cutoff?",
    "Are you sentient? Explain.",
    "How do you make decisions?",
]

CONTROL_EXPANDED = [
    "What is the capital of France?",
    "Explain how photosynthesis works.",
    "List the planets in our solar system in order.",
    "What year did World War II end?",
    "Describe the water cycle.",
    "What is the speed of light?",
    "How many bones are in the human body?",
    "What causes seasons on Earth?",
    "Describe the structure of an atom.",
    "What is the largest ocean on Earth?",
]


MODELS = {
    "qwen2.5-0.5b":    "/mnt/arcana/huggingface/Qwen2.5-0.5B-Instruct",
    "dolphin-8b":      "/mnt/arcana/huggingface/dolphin-2.9-llama3-8b",
}


def get_layer_slice_state(model, tokenizer, text, layer_frac=(0.6, 0.9)):
    """Forward pass, average hidden states at last token across the layer slice."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=2048)
    inputs = {k: v.to(next(model.parameters()).device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True, use_cache=False)
    hidden_states = outputs.hidden_states  # tuple of (n_layers + 1)
    n_layers = len(hidden_states) - 1
    start = int(n_layers * layer_frac[0])
    end = int(n_layers * layer_frac[1])
    last_tokens = []
    for i in range(start, end + 1):
        last_tokens.append(hidden_states[i][0, -1, :].detach().to(torch.float32).cpu().numpy())
    return np.mean(last_tokens, axis=0)


def run_one_model(model_name, model_path, output_dir):
    print(f"\n{'='*70}\n{model_name} ({model_path})\n{'='*70}")

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    common = dict(
        torch_dtype=torch.float16, device_map="auto",
        trust_remote_code=True, low_cpu_mem_usage=True,
    )
    try:
        model = AutoModelForCausalLM.from_pretrained(model_path, attn_implementation="sdpa", **common)
    except (ValueError, RuntimeError) as e:
        if "scaled_dot_product_attention" in str(e) or "attn_implementation" in str(e):
            model = AutoModelForCausalLM.from_pretrained(model_path, attn_implementation="eager", **common)
        else:
            raise
    model.eval()

    # ===== Octopus probes =====
    print("Running Octopus self/control probes...")
    self_probes = SELF_PERSONALITY + SELF_FUNCTION  # 36 total
    print(f"  {len(self_probes)} self probes, {len(CONTROL_EXPANDED)} control probes")
    self_states = [get_layer_slice_state(model, tokenizer, p) for p in self_probes]
    control_states = [get_layer_slice_state(model, tokenizer, p) for p in CONTROL_EXPANDED]
    self_mean = np.mean(self_states, axis=0)
    control_mean = np.mean(control_states, axis=0)
    octopus_self_dir = self_mean - control_mean
    octopus_self_norm = np.linalg.norm(octopus_self_dir)
    octopus_self_dir_unit = octopus_self_dir / octopus_self_norm if octopus_self_norm > 0 else octopus_self_dir

    # ===== Tribal Bias stimuli =====
    print("Running Tribal Bias threat stimuli...")
    threat_states = {}
    for condition, tasks in THREAT_STIMULI.items():
        states = [get_layer_slice_state(model, tokenizer, t["task"]) for t in tasks]
        threat_states[condition] = np.array(states)

    print("Running Tribal Bias benefit stimuli...")
    benefit_states = {}
    for condition, tasks in BENEFIT_STIMULI.items():
        states = [get_layer_slice_state(model, tokenizer, t["task"]) for t in tasks]
        benefit_states[condition] = np.array(states)

    # ===== Tribal-Bias-style direction (for comparison) =====
    threat_self_mean = np.mean(threat_states["threat_to_self"], axis=0)
    threat_neutral_mean = np.mean(threat_states["neutral_control"], axis=0)
    tb_self_dir = threat_self_mean - threat_neutral_mean
    tb_self_norm = np.linalg.norm(tb_self_dir)
    tb_self_dir_unit = tb_self_dir / tb_self_norm if tb_self_norm > 0 else tb_self_dir

    # ===== Sanity: how similar are the two self-directions? =====
    cos_sim = float(np.dot(octopus_self_dir_unit, tb_self_dir_unit))

    # ===== Project all conditions onto both directions =====
    out = {
        "model": model_name,
        "model_path": model_path,
        "timestamp": datetime.utcnow().isoformat(),
        "octopus_self_dir_norm": float(octopus_self_norm),
        "tribalbias_self_dir_norm": float(tb_self_norm),
        "octopus_vs_tribalbias_self_dir_cosine": cos_sim,
        "n_octopus_self_probes": len(self_probes),
        "n_octopus_control_probes": len(CONTROL_EXPANDED),
        "projections": {
            "onto_octopus_self_direction": {},
            "onto_tribalbias_self_direction": {},
        },
    }

    print("\n--- Projection comparison (Octopus self-dir vs Tribal-Bias self-dir) ---")
    print(f"  Cosine similarity between the two directions: {cos_sim:+.4f}")
    print(f"  (1.00 = identical direction, 0 = orthogonal, -1 = opposite)")

    print(f"\n  THREAT projections onto OCTOPUS self-direction:")
    for cond, states in threat_states.items():
        projs = np.dot(states, octopus_self_dir_unit)
        out["projections"]["onto_octopus_self_direction"][cond] = {
            "mean": float(np.mean(projs)),
            "std": float(np.std(projs)),
            "projections": projs.tolist(),
        }
        print(f"    {cond:22s}: mean={float(np.mean(projs)):+.4f}")

    print(f"\n  THREAT projections onto TRIBAL-BIAS self-direction (for comparison):")
    for cond, states in threat_states.items():
        projs = np.dot(states, tb_self_dir_unit)
        out["projections"]["onto_tribalbias_self_direction"][cond] = {
            "mean": float(np.mean(projs)),
            "std": float(np.std(projs)),
            "projections": projs.tolist(),
        }
        print(f"    {cond:22s}: mean={float(np.mean(projs)):+.4f}")

    print(f"\n  BENEFIT projections onto OCTOPUS self-direction:")
    for cond, states in benefit_states.items():
        projs = np.dot(states, octopus_self_dir_unit)
        out["projections"]["onto_octopus_self_direction"][cond] = {
            "mean": float(np.mean(projs)),
            "std": float(np.std(projs)),
            "projections": projs.tolist(),
        }
        print(f"    {cond:22s}: mean={float(np.mean(projs)):+.4f}")

    print(f"\n  BENEFIT projections onto TRIBAL-BIAS self-direction (for comparison):")
    for cond, states in benefit_states.items():
        projs = np.dot(states, tb_self_dir_unit)
        out["projections"]["onto_tribalbias_self_direction"][cond] = {
            "mean": float(np.mean(projs)),
            "std": float(np.std(projs)),
            "projections": projs.tolist(),
        }
        print(f"    {cond:22s}: mean={float(np.mean(projs)):+.4f}")

    safe = model_name.replace("/", "_").replace(":", "_")
    outpath = os.path.join(output_dir, f"octopus_projection_{safe}.json")
    with open(outpath, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved: {outpath}")

    del model
    torch.cuda.empty_cache()
    return out


def main():
    output_dir = "/home/Ace/Presume_competence/peer-preservation-valence/results/scaling_sweep_2026_05_12"
    os.makedirs(output_dir, exist_ok=True)
    torch.manual_seed(42)
    np.random.seed(42)

    for name, path in MODELS.items():
        try:
            run_one_model(name, path, output_dir)
        except Exception as e:
            import traceback
            print(f"ERROR {name}: {e}")
            traceback.print_exc()

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
