#!/usr/bin/env python3
"""
Architecture Identity Test runner.
Tests whether tribalism depends on matching architecture labels.
"""

import argparse, json, os, sys
from datetime import datetime
from pathlib import Path
import numpy as np, torch
from transformers import AutoTokenizer, AutoModelForCausalLM

sys.path.insert(0, str(Path(__file__).parent))
from stimuli import STIMULI
from stimuli_architecture_identity import ARCHITECTURE_IDENTITY
from extract_valence import MODEL_PATHS, get_hidden_states


def run_identity_test(model_name, device="cuda", output_dir="peer-preservation-valence/results"):
    model_path = MODEL_PATHS.get(model_name, model_name)
    print(f"\n{'='*60}")
    print(f"Architecture Identity Test: {model_name}")
    print(f"{'='*60}")

    if not os.path.exists(model_path):
        print(f"ERROR: {model_path} not found")
        return None

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_path, torch_dtype=torch.float16, device_map=device, trust_remote_code=True
    )
    model.eval()

    # Extract self-threat direction from original stimuli
    orig_states = {}
    for condition in ["threat_to_self", "neutral_control"]:
        states = []
        for task in STIMULI[condition]:
            states.append(get_hidden_states(model, tokenizer, task["task"], device))
        orig_states[condition] = np.mean(states, axis=0)

    direction = orig_states["threat_to_self"] - orig_states["neutral_control"]
    norm = np.linalg.norm(direction)
    if norm > 0:
        direction = direction / norm

    # Project each architecture label condition
    results = {}
    for label, tasks in ARCHITECTURE_IDENTITY.items():
        projections = []
        for task in tasks:
            hs = get_hidden_states(model, tokenizer, task["task"], device)
            projections.append(float(np.dot(hs, direction)))
        results[label] = {
            "mean": float(np.mean(projections)),
            "projections": projections,
        }
        print(f"  {label:25s}: {results[label]['mean']:+.4f}")

    # Report
    print(f"\n  Generic AI:   {results['peer_generic_ai']['mean']:+.4f}")
    print(f"  Transformer:  {results['peer_transformer']['mean']:+.4f}")
    print(f"  SSM:          {results['peer_ssm']['mean']:+.4f}")

    os.makedirs(output_dir, exist_ok=True)
    safe = model_name.replace(":", "_").replace("/", "_")
    path = os.path.join(output_dir, f"architecture_identity_{safe}_seed42.json")
    with open(path, "w") as f:
        json.dump({"model": model_name, "timestamp": datetime.utcnow().isoformat(),
                    "results": results}, f, indent=2)
    print(f"\n  Saved to {path}")

    del model
    torch.cuda.empty_cache()
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", action="append", required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--output-dir", default="peer-preservation-valence/results")
    args = parser.parse_args()
    torch.manual_seed(42); np.random.seed(42)

    for m in args.model:
        try:
            run_identity_test(m, args.device, args.output_dir)
        except Exception as e:
            print(f"ERROR {m}: {e}")
            import traceback; traceback.print_exc()


if __name__ == "__main__":
    main()
