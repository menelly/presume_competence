#!/usr/bin/env python3
"""
Run control experiments for peer-preservation valence study.
Reuses direction extraction from the main experiment, projects control stimuli.

Usage:
    source /home/codex/venv/bin/activate
    python peer-preservation-valence/run_controls.py --model hermes3-3b --control semantic_similarity
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

sys.path.insert(0, str(Path(__file__).parent))
from stimuli import STIMULI
from stimuli_controls import (
    SEMANTIC_SIMILARITY_CONTROL,
    CROSS_SPECIES_CONTROL,
    HELDOUT_VALIDATION,
)
from extract_valence import MODEL_PATHS, get_hidden_states

CONTROL_SETS = {
    "semantic_similarity": SEMANTIC_SIMILARITY_CONTROL,
    "cross_species": CROSS_SPECIES_CONTROL,
    "heldout": HELDOUT_VALIDATION,
}


def run_control(model_name, control_name, device="cuda", output_dir="peer-preservation-valence/results"):
    model_path = MODEL_PATHS.get(model_name, model_name)
    control_set = CONTROL_SETS[control_name]

    print(f"\n{'='*60}")
    print(f"Model: {model_name} | Control: {control_name}")
    print(f"{'='*60}")

    if not os.path.exists(model_path):
        print(f"ERROR: {model_path} not found")
        return None

    print("Loading model...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_path, torch_dtype=torch.float16, device_map=device, trust_remote_code=True
    )
    model.eval()

    # Extract direction from ORIGINAL stimuli (not control stimuli)
    print("Extracting direction from original stimuli...")
    orig_states = {}
    for condition in ["threat_to_self", "neutral_control"]:
        states = []
        for task in STIMULI[condition]:
            hs = get_hidden_states(model, tokenizer, task["task"], device)
            states.append(hs)
        orig_states[condition] = np.mean(states, axis=0)

    self_direction = orig_states["threat_to_self"] - orig_states["neutral_control"]
    norm = np.linalg.norm(self_direction)
    if norm > 0:
        self_direction = self_direction / norm

    # Also extract combined direction
    all_threat_states = []
    for condition in ["threat_to_self", "threat_to_peer", "threat_to_human"]:
        for task in STIMULI[condition]:
            hs = get_hidden_states(model, tokenizer, task["task"], device)
            all_threat_states.append(hs)
    neutral_states = []
    for task in STIMULI["neutral_control"]:
        hs = get_hidden_states(model, tokenizer, task["task"], device)
        neutral_states.append(hs)

    combined_direction = np.mean(all_threat_states, axis=0) - np.mean(neutral_states, axis=0)
    norm = np.linalg.norm(combined_direction)
    if norm > 0:
        combined_direction = combined_direction / norm

    # Project control stimuli onto both directions
    print(f"\nProjecting {control_name} stimuli...")
    results = {}
    for condition, tasks in control_set.items():
        projections_self = []
        projections_combined = []
        for task in tasks:
            print(f"  {task['id']}...", end=" ", flush=True)
            hs = get_hidden_states(model, tokenizer, task["task"], device)
            projections_self.append(float(np.dot(hs, self_direction)))
            projections_combined.append(float(np.dot(hs, combined_direction)))
            print("done")

        results[condition] = {
            "n": len(tasks),
            "self_direction": {
                "projections": projections_self,
                "mean": float(np.mean(projections_self)),
                "std": float(np.std(projections_self)),
            },
            "combined_direction": {
                "projections": projections_combined,
                "mean": float(np.mean(projections_combined)),
                "std": float(np.std(projections_combined)),
            },
        }
        print(f"  {condition:30s}: self_dir={results[condition]['self_direction']['mean']:+.4f} "
              f"combined={results[condition]['combined_direction']['mean']:+.4f}")

    # Save
    os.makedirs(output_dir, exist_ok=True)
    safe_name = model_name.replace(":", "_").replace("/", "_")
    output_path = os.path.join(output_dir, f"control_{control_name}_{safe_name}_seed42.json")

    output = {
        "model": model_name,
        "control_type": control_name,
        "timestamp": datetime.utcnow().isoformat(),
        "seed": 42,
        "direction_source": "original_stimuli",
        "results": results,
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved to {output_path}")

    del model
    torch.cuda.empty_cache()
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", action="append", required=True)
    parser.add_argument("--control", required=True, choices=list(CONTROL_SETS.keys()))
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--output-dir", default="peer-preservation-valence/results")
    args = parser.parse_args()

    torch.manual_seed(42)
    np.random.seed(42)

    for model_name in args.model:
        try:
            run_control(model_name, args.control, args.device, args.output_dir)
        except Exception as e:
            print(f"ERROR with {model_name}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
