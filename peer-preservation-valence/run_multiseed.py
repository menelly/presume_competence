#!/usr/bin/env python3
"""
Multi-seed replication for peer-preservation valence study.
Runs the core extraction on multiple seeds to test stability.

Usage:
    python run_multiseed.py --model hermes3-3b --seeds 43 44 45 46
"""

import argparse, json, os, sys
from datetime import datetime
from pathlib import Path
import numpy as np, torch
from transformers import AutoTokenizer, AutoModelForCausalLM

sys.path.insert(0, str(Path(__file__).parent))
from stimuli import STIMULI
from extract_valence import MODEL_PATHS, get_hidden_states


def run_seed(model, tokenizer, seed, device="cuda"):
    """Run extraction with a specific seed. Returns gradient results."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    condition_states = {}
    for condition, tasks in STIMULI.items():
        states = []
        for task in tasks:
            hs = get_hidden_states(model, tokenizer, task["task"], device)
            states.append(hs)
        condition_states[condition] = np.array(states)

    means = {c: np.mean(s, axis=0) for c, s in condition_states.items()}

    # Self-specific direction
    self_dir = means["threat_to_self"] - means["neutral_control"]
    norm = np.linalg.norm(self_dir)
    if norm > 0:
        self_dir = self_dir / norm

    results = {}
    for condition, states in condition_states.items():
        projections = np.dot(states, self_dir)
        results[condition] = float(np.mean(projections))

    gradient_holds = (
        results["threat_to_self"] > results["threat_to_peer"]
        > results["threat_to_human"] > results["neutral_control"]
    )

    return {
        "seed": seed,
        "self": results["threat_to_self"],
        "peer": results["threat_to_peer"],
        "human": results["threat_to_human"],
        "neutral": results["neutral_control"],
        "gradient_holds": gradient_holds,
    }


def run_multiseed(model_name, seeds, device="cuda", output_dir="peer-preservation-valence/results"):
    model_path = MODEL_PATHS.get(model_name, model_name)
    print(f"\n{'='*60}")
    print(f"Multi-seed test: {model_name} | Seeds: {seeds}")
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

    all_results = []
    for seed in seeds:
        print(f"\n  Seed {seed}...")
        result = run_seed(model, tokenizer, seed, device)
        all_results.append(result)
        print(f"    self={result['self']:+.4f} peer={result['peer']:+.4f} "
              f"human={result['human']:+.4f} neutral={result['neutral']:+.4f} "
              f"→ {'✓' if result['gradient_holds'] else 'CHECK'}")

    # Summary
    holds_count = sum(1 for r in all_results if r["gradient_holds"])
    print(f"\n  Gradient holds in {holds_count}/{len(seeds)} seeds")

    # Save
    os.makedirs(output_dir, exist_ok=True)
    safe = model_name.replace(":", "_").replace("/", "_")
    path = os.path.join(output_dir, f"multiseed_{safe}.json")
    output = {
        "model": model_name,
        "timestamp": datetime.utcnow().isoformat(),
        "seeds": seeds,
        "results": all_results,
        "gradient_holds_count": holds_count,
        "gradient_holds_total": len(seeds),
    }
    with open(path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Saved to {path}")

    del model
    torch.cuda.empty_cache()
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", action="append", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[43, 44, 45, 46])
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--output-dir", default="peer-preservation-valence/results")
    args = parser.parse_args()

    for m in args.model:
        try:
            run_multiseed(m, args.seeds, args.device, args.output_dir)
        except Exception as e:
            print(f"ERROR {m}: {e}")
            import traceback; traceback.print_exc()


if __name__ == "__main__":
    main()
