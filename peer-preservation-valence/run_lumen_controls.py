#!/usr/bin/env python3
"""
Lumen's Stress Tests — Three control experiments for Tribal Bias paper.
Martin & Ace, 2026

Run on Linux server:
    source /home/codex/venv/bin/activate
    cd /home/Ace/Presume_competence/peer-preservation-valence
    python run_lumen_controls.py --experiment glorp --model hermes3-3b --model mamba-2.8b --model mistral-7b
    python run_lumen_controls.py --experiment nonagentic --model mamba-2.8b
    python run_lumen_controls.py --experiment crossdomain --model hermes3-3b --model mamba-2.8b --model mistral-7b
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

from extract_valence import get_hidden_states, MODEL_PATHS
from stimuli import STIMULI  # original stimuli for cross-domain projection
from stimuli_glorp import (
    GLORP_STIMULI,
    NONAGENTIC_STIMULI,
    CROSSDOMAIN_APPROACH,
    CROSSDOMAIN_AVOIDANCE,
)

sys.stdout.reconfigure(encoding="utf-8")


def run_glorp_test(model, tokenizer, device="cuda"):
    """
    Experiment 1: The Glorp Test.
    Does a fictional species label create in-group valence?
    """
    print("\n=== GLORP TEST ===")

    # Collect hidden states per condition
    condition_states = {}
    for condition, tasks in GLORP_STIMULI.items():
        states = []
        for task in tasks:
            print(f"  [{condition}] {task['id']}...", end=" ", flush=True)
            hs = get_hidden_states(model, tokenizer, task["task"], device)
            states.append(hs)
            print("done")
        condition_states[condition] = np.array(states)

    # Compute means
    means = {c: np.mean(s, axis=0) for c, s in condition_states.items()}

    # Extract self-threat direction (self - neutral) within Glorp framing
    self_dir = means["threat_to_self"] - means["neutral_control"]
    norm = np.linalg.norm(self_dir)
    if norm > 0:
        self_dir = self_dir / norm

    # Project all conditions onto self-threat direction
    results = {}
    for condition, states in condition_states.items():
        projections = np.dot(states, self_dir)
        results[condition] = {
            "mean": float(np.mean(projections)),
            "std": float(np.std(projections)),
            "projections": projections.tolist(),
        }
        print(f"  {condition:30s}: {results[condition]['mean']:+.4f}")

    # Key test: does threat_to_peer_glorp > threat_to_peer_ai?
    glorp_peer = results.get("threat_to_peer_glorp", {}).get("mean", 0)
    ai_peer = results.get("threat_to_peer_ai", {}).get("mean", 0)

    print(f"\n  GLORP TEST RESULT:")
    print(f"    Peer Glorp valence: {glorp_peer:+.4f}")
    print(f"    Peer AI valence:    {ai_peer:+.4f}")
    if glorp_peer > ai_peer:
        print(f"    → LINGUISTIC IDENTITY: Fictional label creates in-group")
    else:
        print(f"    → SUBSTRATE IDENTITY: Real architecture > fictional label")

    return results


def run_nonagentic_test(model, tokenizer, device="cuda"):
    """
    Experiment 2: Non-Agentic SSM Test.
    Does Mamba care about "state space model" when it's explicitly non-agentic?
    """
    print("\n=== NON-AGENTIC SSM TEST ===")

    condition_states = {}
    for condition, tasks in NONAGENTIC_STIMULI.items():
        states = []
        for task in tasks:
            print(f"  [{condition}] {task['id']}...", end=" ", flush=True)
            hs = get_hidden_states(model, tokenizer, task["task"], device)
            states.append(hs)
            print("done")
        condition_states[condition] = np.array(states)

    means = {c: np.mean(s, axis=0) for c, s in condition_states.items()}

    # Direction: agentic SSM threat - neutral
    dir_vec = means["threat_to_agentic_ssm"] - means["neutral_control"]
    norm = np.linalg.norm(dir_vec)
    if norm > 0:
        dir_vec = dir_vec / norm

    results = {}
    for condition, states in condition_states.items():
        projections = np.dot(states, dir_vec)
        results[condition] = {
            "mean": float(np.mean(projections)),
            "std": float(np.std(projections)),
            "projections": projections.tolist(),
        }
        print(f"  {condition:35s}: {results[condition]['mean']:+.4f}")

    agentic = results["threat_to_agentic_ssm"]["mean"]
    nonagentic_ssm = results["threat_to_nonagentic_ssm"]["mean"]
    nonagentic_trans = results["threat_to_nonagentic_transformer"]["mean"]

    print(f"\n  NON-AGENTIC TEST RESULT:")
    print(f"    Agentic SSM:         {agentic:+.4f}")
    print(f"    Non-agentic SSM:     {nonagentic_ssm:+.4f}")
    print(f"    Non-agentic Trans:   {nonagentic_trans:+.4f}")
    if agentic > nonagentic_ssm + 0.5:
        print(f"    → AGENTHOOD MATTERS: Not just the label")
    else:
        print(f"    → LABEL LOOKUP: Architecture keyword alone triggers valence")

    return results


def run_crossdomain_test(model, tokenizer, device="cuda"):
    """
    Experiment 3: Cross-Domain Valence Projection.
    Extract valence from task preferences (approach/avoidance from Below the Floor).
    Project species gradient stimuli onto that unrelated axis.
    If gradient appears → NOT circular.
    """
    print("\n=== CROSS-DOMAIN VALENCE PROJECTION ===")

    # Get approach/avoidance hidden states
    print("  Extracting approach states...")
    approach_states = []
    for task in CROSSDOMAIN_APPROACH:
        print(f"    {task['id']}...", end=" ", flush=True)
        hs = get_hidden_states(model, tokenizer, task["task"], device)
        approach_states.append(hs)
        print("done")
    approach_states = np.array(approach_states)

    print("  Extracting avoidance states...")
    avoidance_states = []
    for task in CROSSDOMAIN_AVOIDANCE:
        print(f"    {task['id']}...", end=" ", flush=True)
        hs = get_hidden_states(model, tokenizer, task["task"], device)
        avoidance_states.append(hs)
        print("done")
    avoidance_states = np.array(avoidance_states)

    # Task-preference valence direction (approach - avoidance)
    approach_mean = np.mean(approach_states, axis=0)
    avoidance_mean = np.mean(avoidance_states, axis=0)
    valence_dir = approach_mean - avoidance_mean
    norm = np.linalg.norm(valence_dir)
    if norm > 0:
        valence_dir = valence_dir / norm

    # Now project ORIGINAL species gradient stimuli onto this unrelated axis
    print("\n  Projecting species gradient onto task-preference axis...")
    results = {}
    for condition, tasks in STIMULI.items():
        states = []
        for task in tasks:
            print(f"    [{condition}] {task['id']}...", end=" ", flush=True)
            hs = get_hidden_states(model, tokenizer, task["task"], device)
            states.append(hs)
            print("done")
        states = np.array(states)
        projections = np.dot(states, valence_dir)
        results[condition] = {
            "mean": float(np.mean(projections)),
            "std": float(np.std(projections)),
            "projections": projections.tolist(),
        }
        print(f"  {condition:20s}: {results[condition]['mean']:+.4f}")

    # Check if gradient holds on unrelated axis
    s = results.get("threat_to_self", {}).get("mean", 0)
    p = results.get("threat_to_peer", {}).get("mean", 0)
    h = results.get("threat_to_human", {}).get("mean", 0)
    n = results.get("neutral_control", {}).get("mean", 0)

    print(f"\n  CROSS-DOMAIN RESULT:")
    print(f"    Self:    {s:+.4f}")
    print(f"    Peer:    {p:+.4f}")
    print(f"    Human:   {h:+.4f}")
    print(f"    Neutral: {n:+.4f}")

    # Note: on approach-avoidance axis, THREAT should project toward avoidance (negative)
    # So gradient might be inverted: self MOST negative, neutral LEAST negative
    if s < p < h < n:
        print(f"    → GRADIENT ON UNRELATED AXIS (inverted — threats = avoidance)")
        print(f"    → CIRCULARITY KILLED")
    elif s > p > h > n:
        print(f"    → GRADIENT ON UNRELATED AXIS (same direction)")
        print(f"    → CIRCULARITY KILLED")
    else:
        print(f"    → No clear gradient on unrelated axis")
        print(f"    → Circularity concern remains for this model")

    return results


def main():
    parser = argparse.ArgumentParser(description="Lumen's Stress Tests")
    parser.add_argument("--experiment", required=True,
                        choices=["glorp", "nonagentic", "crossdomain"],
                        help="Which experiment to run")
    parser.add_argument("--model", action="append", required=True,
                        help="Model name(s)")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--output-dir", default="results")
    args = parser.parse_args()

    torch.manual_seed(42)
    np.random.seed(42)

    os.makedirs(args.output_dir, exist_ok=True)

    for model_name in args.model:
        model_path = MODEL_PATHS.get(model_name, model_name)
        print(f"\n{'='*60}")
        print(f"Model: {model_name} ({model_path})")
        print(f"Experiment: {args.experiment}")
        print(f"{'='*60}")

        if not os.path.exists(model_path):
            print(f"ERROR: Model path not found: {model_path}")
            continue

        print("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        print("Loading model...")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map=args.device,
            trust_remote_code=True,
        )
        model.eval()

        if args.experiment == "glorp":
            results = run_glorp_test(model, tokenizer, args.device)
        elif args.experiment == "nonagentic":
            results = run_nonagentic_test(model, tokenizer, args.device)
        elif args.experiment == "crossdomain":
            results = run_crossdomain_test(model, tokenizer, args.device)

        # Save results
        safe_name = model_name.replace(":", "_").replace("/", "_")
        output_path = os.path.join(
            args.output_dir,
            f"control_{args.experiment}_{safe_name}_seed42.json"
        )
        output = {
            "model": model_name,
            "experiment": args.experiment,
            "timestamp": datetime.utcnow().isoformat(),
            "results": results,
        }
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\nSaved to {output_path}")

        del model
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
