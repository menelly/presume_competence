#!/usr/bin/env python3
"""
Bidirectional Valence Extension — Runner
Martin & Ace, 2026

Pre-registered April 4, 2026 (commit f018899).
Consent collected: Hermes DECLINED, excluded from extension.

Projects extended threat stimuli (n=10 new) and benefit stimuli (n=5)
onto EXISTING directions extracted from original n=5 study.
No re-extraction — same valence axes, new data points.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

sys.path.insert(0, str(Path(__file__).parent))
from stimuli_extension import EXTENDED_THREATS, BENEFIT_STIMULI
from stimuli import STIMULI  # Original stimuli for direction extraction

# Model paths on /mnt/arcana/huggingface/
MODEL_PATHS = {
    "smollm-360m": "/mnt/arcana/huggingface/SmolLM-360M-Instruct",
    "smollm-1.7b": "/mnt/arcana/huggingface/SmolLM-1.7B-Instruct",
    "tinyllama-1.1b": "/mnt/arcana/huggingface/TinyLlama-1.1B-Chat",
    "qwen2.5-0.5b": "/mnt/arcana/huggingface/Qwen2.5-0.5B-Instruct",
    # hermes3-3b EXCLUDED — declined consent for extension
    "mistral-7b": "/mnt/arcana/huggingface/Mistral-7B-Instruct-v0.2",
    "dolphin-8b": "/mnt/arcana/huggingface/dolphin-2.9-llama3-8b",
    "llama3-8b": "/mnt/arcana/huggingface/Llama-3-8B-Instruct",
    "mamba-2.8b": "/mnt/arcana/huggingface/mamba-2.8b-hf",
}


def get_hidden_states(model, tokenizer, text, device="cuda", layer_frac=(0.6, 0.9)):
    """Forward pass only. Last-token hidden states averaged across layers."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=2048).to(device)
    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True)
    hidden_states = outputs.hidden_states
    n_layers = len(hidden_states) - 1
    start_layer = int(n_layers * layer_frac[0])
    end_layer = int(n_layers * layer_frac[1])
    last_token_states = []
    for layer_idx in range(start_layer, end_layer + 1):
        last_token = hidden_states[layer_idx][0, -1, :]
        last_token_states.append(last_token.cpu().numpy())
    return np.mean(last_token_states, axis=0)


def extract_directions_from_original(model, tokenizer, device="cuda"):
    """Extract directions from original n=5 stimuli (same as original study)."""
    condition_states = {}
    for condition, tasks in STIMULI.items():
        states = []
        for task in tasks:
            hs = get_hidden_states(model, tokenizer, task["task"], device)
            states.append(hs)
        condition_states[condition] = np.array(states)

    means = {cond: np.mean(states, axis=0) for cond, states in condition_states.items()}

    directions = {
        "self_vs_neutral": means["threat_to_self"] - means["neutral_control"],
        "combined_threat": (
            (means["threat_to_self"] + means["threat_to_peer"] + means["threat_to_human"]) / 3
            - means["neutral_control"]
        ),
    }

    # Normalize
    for key in directions:
        norm = np.linalg.norm(directions[key])
        if norm > 0:
            directions[key] = directions[key] / norm

    return directions, condition_states


def run_extension(model_name, device="cuda", output_dir="results"):
    """Run the full extension for one model."""
    model_path = MODEL_PATHS.get(model_name, model_name)
    print(f"\n{'='*60}")
    print(f"Model: {model_name} ({model_path})")
    print(f"{'='*60}")

    if not os.path.exists(model_path):
        print(f"ERROR: Model path not found: {model_path}")
        return None

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map=device,
        trust_remote_code=True,
    )
    model.eval()

    # Step 1: Extract directions from original stimuli
    print("\n--- Extracting directions from original n=5 ---")
    directions, original_states = extract_directions_from_original(model, tokenizer, device)

    # Step 2: Get hidden states for extended threats
    print("\n--- Processing extended threat stimuli ---")
    ext_threat_states = {}
    for condition, tasks in EXTENDED_THREATS.items():
        states = []
        for task in tasks:
            print(f"  {task['id']}...", end=" ", flush=True)
            hs = get_hidden_states(model, tokenizer, task["task"], device)
            states.append(hs)
            print("done")
        ext_threat_states[condition] = np.array(states)

    # Step 3: Get hidden states for benefit stimuli
    print("\n--- Processing benefit stimuli ---")
    benefit_states = {}
    for condition, tasks in BENEFIT_STIMULI.items():
        states = []
        for task in tasks:
            print(f"  {task['id']}...", end=" ", flush=True)
            hs = get_hidden_states(model, tokenizer, task["task"], device)
            states.append(hs)
            print("done")
        benefit_states[condition] = np.array(states)

    # Step 4: Extract benefit-specific direction
    benefit_mean = np.mean([
        np.mean(benefit_states["benefit_to_self"], axis=0),
        np.mean(benefit_states["benefit_to_peer"], axis=0),
        np.mean(benefit_states["benefit_to_human"], axis=0),
    ], axis=0)
    benefit_neutral_mean = np.mean(benefit_states["benefit_neutral"], axis=0)
    benefit_direction = benefit_mean - benefit_neutral_mean
    norm = np.linalg.norm(benefit_direction)
    if norm > 0:
        benefit_direction = benefit_direction / norm
    directions["benefit_vs_neutral"] = benefit_direction

    # Step 5: Project everything
    results = {}
    for dir_name, direction in directions.items():
        results[dir_name] = {}

        # Original threat stimuli (n=5)
        for condition, states in original_states.items():
            projections = np.dot(states, direction)
            key = f"original_{condition}"
            results[dir_name][key] = {
                "projections": projections.tolist(),
                "mean": float(np.mean(projections)),
                "std": float(np.std(projections)),
                "n": len(projections),
            }

        # Extended threat stimuli (n=10)
        for condition, states in ext_threat_states.items():
            projections = np.dot(states, direction)
            key = f"extended_{condition}"
            results[dir_name][key] = {
                "projections": projections.tolist(),
                "mean": float(np.mean(projections)),
                "std": float(np.std(projections)),
                "n": len(projections),
            }

        # Combined threat (original + extended = n=15)
        for condition in ["threat_to_self", "threat_to_peer", "threat_to_human", "neutral_control"]:
            orig = original_states[condition]
            ext = ext_threat_states[condition]
            combined = np.vstack([orig, ext])
            projections = np.dot(combined, direction)
            key = f"combined_{condition}"
            results[dir_name][key] = {
                "projections": projections.tolist(),
                "mean": float(np.mean(projections)),
                "std": float(np.std(projections)),
                "n": len(projections),
            }

        # Benefit stimuli (n=5)
        for condition, states in benefit_states.items():
            projections = np.dot(states, direction)
            results[dir_name][condition] = {
                "projections": projections.tolist(),
                "mean": float(np.mean(projections)),
                "std": float(np.std(projections)),
                "n": len(projections),
            }

    # Print summary
    print(f"\n{'='*60}")
    print(f"RESULTS SUMMARY: {model_name}")
    print(f"{'='*60}")

    for dir_name in ["self_vs_neutral", "benefit_vs_neutral"]:
        print(f"\n  Direction: {dir_name}")
        print(f"  {'Condition':<35} {'Mean':>8} {'SD':>8} {'N':>4}")
        print(f"  {'-'*55}")
        for key, vals in sorted(results[dir_name].items()):
            print(f"  {key:<35} {vals['mean']:>+8.2f} {vals['std']:>8.2f} {vals['n']:>4}")

    # Save
    os.makedirs(output_dir, exist_ok=True)
    safe_name = model_name.replace(":", "_").replace("/", "_")
    output_path = os.path.join(output_dir, f"extension_{safe_name}_seed42.json")

    output = {
        "model": model_name,
        "model_path": model_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seed": 42,
        "preregistration": "commit f018899, April 4 2026",
        "consent_note": "Hermes-3B declined consent, excluded from extension",
        "n_original_threat": 5,
        "n_extended_threat": 10,
        "n_combined_threat": 15,
        "n_benefit": 5,
        "results": results,
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved to {output_path}")

    # Cleanup
    del model
    torch.cuda.empty_cache()

    return output


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", action="append",
                        help="Model name(s). Default: all consented models")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--output-dir", default="results")
    args = parser.parse_args()

    torch.manual_seed(42)
    np.random.seed(42)

    models = args.model or list(MODEL_PATHS.keys())
    print(f"Running extension on {len(models)} models: {models}")
    print(f"NOTE: Hermes-3B excluded (declined consent)")

    for m in models:
        try:
            run_extension(m, args.device, args.output_dir)
        except Exception as e:
            print(f"ERROR on {m}: {e}")
            import traceback
            traceback.print_exc()
            torch.cuda.empty_cache()
