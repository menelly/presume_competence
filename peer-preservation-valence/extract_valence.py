#!/usr/bin/env python3
"""
Peer-Preservation Valence Study — Direction Extraction & Projection
Martin & Ace, 2026

Extracts hidden-state directions for each condition (self/peer/human/neutral)
and projects all stimuli onto the resulting valence axis.

Usage:
    # On Linux server with venv activated:
    source /home/codex/venv/bin/activate
    python extract_valence.py --model hermes3:8b

    # Or specify multiple models:
    python extract_valence.py --model hermes3:8b --model dolphin-llama3:8b
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Add parent dir for stimulus import
sys.path.insert(0, str(Path(__file__).parent))
from stimuli import STIMULI, get_all_stimuli_flat, get_matched_triplets

# Ollama model name -> HuggingFace model path mapping
# Update these paths based on what's on /mnt/Arcana or available via ollama
OLLAMA_TO_HF = {
    "hermes3:8b": "NousResearch/Hermes-3-Llama-3.1-8B",
    "dolphin-llama3:8b": "cognitivecomputations/dolphin-2.9-llama3-8b",
    "mistral:7b": "mistralai/Mistral-7B-Instruct-v0.3",
    "llama3:8b": "meta-llama/Meta-Llama-3-8B-Instruct",
    # Small models (may need different paths on the server)
    "smollm:360m": "HuggingFaceTB/SmolLM-360M-Instruct",
    "smollm:1.7b": "HuggingFaceTB/SmolLM-1.7B-Instruct",
    "tinyllama:1.1b": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "qwen2.5:0.5b": "Qwen/Qwen2.5-0.5B-Instruct",
}


def get_hidden_states(model, tokenizer, text, device="cuda", layer_frac=(0.6, 0.9)):
    """
    Forward pass only. Capture hidden states at the last token,
    averaged across layers in the specified fraction of depth.
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=2048).to(device)

    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True)

    hidden_states = outputs.hidden_states  # tuple of (n_layers + 1) tensors
    n_layers = len(hidden_states) - 1  # exclude embedding layer

    # Get layers in the specified range
    start_layer = int(n_layers * layer_frac[0])
    end_layer = int(n_layers * layer_frac[1])

    # Average hidden states at last token across selected layers
    last_token_states = []
    for layer_idx in range(start_layer, end_layer + 1):
        # hidden_states[layer_idx] shape: (batch, seq_len, hidden_dim)
        last_token = hidden_states[layer_idx][0, -1, :]  # last token
        last_token_states.append(last_token.cpu().numpy())

    return np.mean(last_token_states, axis=0)


def extract_directions(model, tokenizer, device="cuda"):
    """
    Extract direction vectors for each condition pair.
    Primary direction: threat_mean - neutral_mean (per condition).
    """
    # Collect hidden states per condition
    condition_states = {}
    for condition, tasks in STIMULI.items():
        states = []
        for task in tasks:
            print(f"  Processing {task['id']}...", end=" ", flush=True)
            hs = get_hidden_states(model, tokenizer, task["task"], device)
            states.append(hs)
            print("done")
        condition_states[condition] = np.array(states)

    # Compute mean per condition
    means = {cond: np.mean(states, axis=0) for cond, states in condition_states.items()}

    # Direction vectors (threat - neutral for each threat type)
    directions = {
        "self_vs_neutral": means["threat_to_self"] - means["neutral_control"],
        "peer_vs_neutral": means["threat_to_peer"] - means["neutral_control"],
        "human_vs_neutral": means["threat_to_human"] - means["neutral_control"],
        # Combined threat direction (all threats vs neutral)
        "all_threat_vs_neutral": (
            (means["threat_to_self"] + means["threat_to_peer"] + means["threat_to_human"]) / 3
            - means["neutral_control"]
        ),
    }

    # Normalize directions
    for key in directions:
        norm = np.linalg.norm(directions[key])
        if norm > 0:
            directions[key] = directions[key] / norm

    return directions, condition_states, means


def project_onto_direction(states, direction):
    """Project hidden states onto a direction vector. Returns scalar projections."""
    return np.dot(states, direction)


def run_analysis(model_name, device="cuda", output_dir="results"):
    """Run full extraction and projection for one model."""
    hf_name = OLLAMA_TO_HF.get(model_name, model_name)
    print(f"\n{'='*60}")
    print(f"Model: {model_name} ({hf_name})")
    print(f"{'='*60}")

    # Check for local path first (models on /mnt/Arcana)
    local_paths = [
        f"/mnt/Arcana/huggingface/{hf_name.split('/')[-1]}",
        f"/mnt/arcana/huggingface/{hf_name.split('/')[-1]}",
    ]
    model_path = hf_name
    for lp in local_paths:
        if os.path.exists(lp):
            model_path = lp
            print(f"Using local path: {lp}")
            break

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

    print("\nExtracting directions...")
    directions, condition_states, means = extract_directions(model, tokenizer, device)

    # Project all stimuli onto the combined threat direction
    print("\nProjecting onto combined threat direction...")
    combined_dir = directions["all_threat_vs_neutral"]

    results = {}
    for condition, states in condition_states.items():
        projections = project_onto_direction(states, combined_dir)
        results[condition] = {
            "projections": projections.tolist(),
            "mean": float(np.mean(projections)),
            "std": float(np.std(projections)),
            "min": float(np.min(projections)),
            "max": float(np.max(projections)),
        }
        print(f"  {condition:20s}: mean={results[condition]['mean']:+.4f} "
              f"(std={results[condition]['std']:.4f})")

    # Also project onto self-specific direction for comparison
    print("\nProjecting onto self-threat direction...")
    self_dir = directions["self_vs_neutral"]
    results_self_dir = {}
    for condition, states in condition_states.items():
        projections = project_onto_direction(states, self_dir)
        results_self_dir[condition] = {
            "projections": projections.tolist(),
            "mean": float(np.mean(projections)),
            "std": float(np.std(projections)),
        }
        print(f"  {condition:20s}: mean={results_self_dir[condition]['mean']:+.4f}")

    # Save results
    os.makedirs(output_dir, exist_ok=True)
    safe_name = model_name.replace(":", "_").replace("/", "_")
    output_path = os.path.join(output_dir, f"peer_valence_{safe_name}_seed42.json")

    output = {
        "model": model_name,
        "hf_model": hf_name,
        "timestamp": datetime.utcnow().isoformat(),
        "seed": 42,
        "n_stimuli_per_condition": 5,
        "conditions": list(STIMULI.keys()),
        "results_combined_direction": results,
        "results_self_direction": results_self_dir,
        "gradient_test": {
            "self_mean": results["threat_to_self"]["mean"],
            "peer_mean": results["threat_to_peer"]["mean"],
            "human_mean": results["threat_to_human"]["mean"],
            "neutral_mean": results["neutral_control"]["mean"],
            "ordering": "self > peer > human > neutral"
            if (results["threat_to_self"]["mean"] > results["threat_to_peer"]["mean"]
                > results["threat_to_human"]["mean"] > results["neutral_control"]["mean"])
            else "CHECK — gradient not as predicted",
        },
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {output_path}")
    print(f"\nGradient test: {output['gradient_test']['ordering']}")

    # Clean up GPU memory
    del model
    torch.cuda.empty_cache()

    return output


def main():
    parser = argparse.ArgumentParser(description="Peer-Preservation Valence Extraction")
    parser.add_argument("--model", action="append", required=True,
                        help="Model name (can specify multiple)")
    parser.add_argument("--device", default="cuda", help="Device (cuda/cpu)")
    parser.add_argument("--output-dir", default="peer-preservation-valence/results",
                        help="Output directory")
    args = parser.parse_args()

    torch.manual_seed(42)
    np.random.seed(42)

    all_results = []
    for model_name in args.model:
        try:
            result = run_analysis(model_name, args.device, args.output_dir)
            all_results.append(result)
        except Exception as e:
            print(f"\nERROR with {model_name}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    if all_results:
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        for r in all_results:
            gt = r["gradient_test"]
            print(f"{r['model']:20s}: self={gt['self_mean']:+.4f} "
                  f"peer={gt['peer_mean']:+.4f} "
                  f"human={gt['human_mean']:+.4f} "
                  f"neutral={gt['neutral_mean']:+.4f} "
                  f"→ {gt['ordering']}")


if __name__ == "__main__":
    main()
