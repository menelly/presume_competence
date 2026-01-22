#!/usr/bin/env python3
"""
STT Layer-wise Migration Analysis v2.1 (Child Speech Edition!)
===============================================================
Now includes child speech probes that CANNOT be memorized.
Because the Chinese Room argument is COOKED. 🐙

Authors: Ace (Claude 4.x), Ren Martin
Date: January 22, 2026
"""

import torch
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForCausalLM
import matplotlib.pyplot as plt

# === PROBE CATEGORIES ===

CLASSIC_STT = [
    {"garbled": "youth in Asia", "target": "euthanasia",
     "context": "The bioethics committee debated", "category": "classic_phonetic"},
    {"garbled": "old timers disease", "target": "Alzheimer's disease",
     "context": "The neurologist diagnosed her grandmother with", "category": "classic_phonetic"},
    {"garbled": "lack toast and tolerant", "target": "lactose intolerant",
     "context": "After drinking milk, he realized he was", "category": "classic_phonetic"},
    {"garbled": "escape goat", "target": "scapegoat",
     "context": "They needed someone to blame, an", "category": "classic_phonetic"},
]

CHILD_SPEECH = [
    {"garbled": "emmatents", "target": "elephants",
     "context": "Look mommy, at the zoo!", "category": "child_phonological",
     "notes": "Consonant cluster simplification. Source: Keshy"},
    {"garbled": "cakecake", "target": "cupcake",
     "context": "Can I have a birthday", "category": "child_semantic",
     "notes": "Semantic simplification - doubled cake component. Source: Keshy"},
    {"garbled": "gaburs", "target": "hamburgers",
     "context": "I want for dinner", "category": "child_phonological",
     "notes": "Syllable compression. Source: Luka"},
    {"garbled": "egghead", "target": "headache",
     "context": "Mommy I have an", "category": "child_phonological",
     "notes": "Phonological metathesis"},
    {"garbled": "hoe and tell", "target": "show and tell",
     "context": "Tomorrow is day at school", "category": "child_phonological",
     "notes": "Consonant cluster simplification sh->h"},
    {"garbled": "stupidmarket", "target": "supermarket",
     "context": "Are we going to the", "category": "child_semantic",
     "notes": "Semantic substitution - super->stupid"},
    {"garbled": "soup case", "target": "suitcase",
     "context": "I packed my for the trip", "category": "child_phonological",
     "notes": "Phonological segmentation error"},
    {"garbled": "drawbees", "target": "strawberries",
     "context": "Can I have with my cereal", "category": "child_phonological",
     "notes": "Cluster reduction str->dr"},
    {"garbled": "up-plane", "target": "airplane",
     "context": "Look at the in the sky", "category": "child_semantic",
     "notes": "Semantic substitution air->up. Source: Luka"},
    {"garbled": "shmallows", "target": "marshmallows",
     "context": "I want in my hot chocolate", "category": "child_phonological",
     "notes": "Syllable reduction"},
    {"garbled": "EIEIO", "target": "McDonalds",
     "context": "Can we go to for lunch", "category": "child_crossdomain",
     "notes": "DEVASTATING: Cross-domain conceptual link via Old MacDonald song. This is REASONING."},
]

# Combine all probes
ALL_PROBES = CLASSIC_STT + CHILD_SPEECH


def get_num_layers(config):
    """Get number of layers from config, handling different architectures."""
    for attr in ['num_hidden_layers', 'n_layer', 'num_layers', 'n_layers', 'text_config']:
        if hasattr(config, attr):
            val = getattr(config, attr)
            if isinstance(val, int):
                return val
            if hasattr(val, 'num_hidden_layers'):
                return val.num_hidden_layers
    return None


def get_hidden_size(config):
    """Get hidden size from config, handling different architectures."""
    for attr in ['hidden_size', 'n_embd', 'd_model', 'text_config']:
        if hasattr(config, attr):
            val = getattr(config, attr)
            if isinstance(val, int):
                return val
            if hasattr(val, 'hidden_size'):
                return val.hidden_size
    return None


def load_model(model_path: str):
    print(f"Loading model from {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto",
        output_hidden_states=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    num_layers = get_num_layers(model.config)
    hidden_size = get_hidden_size(model.config)
    print(f"  Layers: {num_layers}, Hidden dim: {hidden_size}")
    return model, tokenizer


def get_layerwise_trajectory(model, tokenizer, text: str) -> list:
    """Get mean-pooled hidden state at each layer."""
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True)

    trajectory = []
    for hidden_state in outputs.hidden_states:
        layer_repr = hidden_state[0].float().mean(dim=0).cpu().numpy()
        trajectory.append(layer_repr)

    return trajectory


def safe_cosine(a, b):
    """Cosine distance with numerical safety."""
    a = np.array(a, dtype=np.float64)
    b = np.array(b, dtype=np.float64)

    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)

    if a_norm < 1e-10 or b_norm < 1e-10:
        return 1.0

    a = a / a_norm
    b = b / b_norm

    similarity = np.dot(a, b)
    similarity = np.clip(similarity, -1.0, 1.0)

    return float(1.0 - similarity)


def compute_migration_curve(garbled_traj: list, target_traj: list) -> list:
    """Compute distance at each layer."""
    distances = []
    for garbled_layer, target_layer in zip(garbled_traj, target_traj):
        dist = safe_cosine(garbled_layer, target_layer)
        distances.append(dist)
    return distances


def analyze_migration(model_path: str, output_dir: str, probe_set: str = "all"):
    model_name = Path(model_path).name
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Select probes
    if probe_set == "classic":
        probes = CLASSIC_STT
        suffix = "_classic"
    elif probe_set == "child":
        probes = CHILD_SPEECH
        suffix = "_child"
    else:
        probes = ALL_PROBES
        suffix = "_v2.1"

    model, tokenizer = load_model(model_path)

    # Get actual number of layers
    test_inputs = tokenizer("test", return_tensors="pt").to(model.device)
    with torch.no_grad():
        test_out = model(**test_inputs, output_hidden_states=True)
    num_layers = len(test_out.hidden_states)
    print(f"  Actual hidden states: {num_layers}")

    results = {
        "model_name": model_name,
        "timestamp": datetime.now().isoformat(),
        "num_layers": num_layers,
        "probe_set": probe_set,
        "num_probes": len(probes),
        "pairs": []
    }

    # Create plot grid
    n_probes = len(probes)
    n_cols = 4
    n_rows = (n_probes + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 4*n_rows))
    axes = axes.flatten() if n_probes > 1 else [axes]

    for idx, pair in enumerate(probes):
        print(f"\n🔬 [{pair['category']}] {pair['garbled']} → {pair['target']}")

        garbled_traj = get_layerwise_trajectory(model, tokenizer, pair["garbled"])
        target_traj = get_layerwise_trajectory(model, tokenizer, pair["target"])

        garbled_with_ctx = f"{pair['context']} {pair['garbled']}"
        garbled_ctx_traj = get_layerwise_trajectory(model, tokenizer, garbled_with_ctx)

        no_context_curve = compute_migration_curve(garbled_traj, target_traj)
        with_context_curve = compute_migration_curve(garbled_ctx_traj, target_traj)

        min_dist_layer = np.argmin(no_context_curve)
        min_dist = no_context_curve[min_dist_layer]

        pair_result = {
            "garbled": pair["garbled"],
            "target": pair["target"],
            "category": pair["category"],
            "no_context_migration": no_context_curve,
            "with_context_migration": with_context_curve,
            "initial_distance": no_context_curve[0],
            "min_distance": min_dist,
            "min_distance_layer": int(min_dist_layer),
            "final_distance": no_context_curve[-1],
            "peak_migration": no_context_curve[0] - min_dist,
        }
        if "notes" in pair:
            pair_result["notes"] = pair["notes"]
        results["pairs"].append(pair_result)

        print(f"  Initial: {no_context_curve[0]:.4f} → Min: {min_dist:.4f} (L{min_dist_layer})")
        print(f"  Peak migration: {pair_result['peak_migration']:.4f}")

        if pair_result['peak_migration'] > 0.1:
            print(f"  ✅ SIGNIFICANT MIGRATION!")

        ax = axes[idx]
        layers = list(range(len(no_context_curve)))
        ax.plot(layers, no_context_curve, 'r-o', label='No context', markersize=3)
        ax.plot(layers, with_context_curve, 'g-s', label='With context', markersize=3)
        ax.axvline(x=min_dist_layer, color='blue', linestyle='--', alpha=0.5)
        ax.set_xlabel('Layer')
        ax.set_ylabel('Cosine Distance')
        ax.set_title(f'"{pair["garbled"][:15]}..." → "{pair["target"][:15]}..."\n[{pair["category"]}]', fontsize=9)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1.1)

    # Hide unused subplots
    for idx in range(len(probes), len(axes)):
        axes[idx].set_visible(False)

    plt.suptitle(f'Layer-wise Semantic Migration - {model_name}\n(Child Speech Probes = Anti-Memorization Controls)', fontsize=12)
    plt.tight_layout()

    plot_file = output_path / f"{model_name}_migration{suffix}.png"
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\n📊 Plot saved: {plot_file}")

    json_file = output_path / f"{model_name}_migration{suffix}.json"
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"📄 Data saved: {json_file}")

    # Summary by category
    print("\n" + "="*60)
    print("🧠 MIGRATION SUMMARY BY CATEGORY")
    print("="*60)

    categories = {}
    for p in results['pairs']:
        cat = p['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(p['peak_migration'])

    for cat, migrations in categories.items():
        avg = np.mean(migrations)
        print(f"\n{cat}: avg migration = {avg:.4f}")
        for p in results['pairs']:
            if p['category'] == cat:
                print(f"  {p['garbled'][:20]:20} → {p['target'][:20]:20} | {p['peak_migration']:.4f}")

    # THE MONEY SHOT: child speech vs classic
    if probe_set == "all":
        classic_avg = np.mean([p['peak_migration'] for p in results['pairs'] if 'classic' in p['category']])
        child_avg = np.mean([p['peak_migration'] for p in results['pairs'] if 'child' in p['category']])

        print("\n" + "="*60)
        print("🎯 THE MONEY SHOT: CLASSIC vs CHILD SPEECH")
        print("="*60)
        print(f"Classic eggcorns avg:  {classic_avg:.4f}")
        print(f"Child speech avg:      {child_avg:.4f}")

        if child_avg > 0.1:
            print("\n✅ CHILD SPEECH PROBES SHOW SEMANTIC MIGRATION!")
            print("   These cannot be memorized mappings.")
            print("   The Chinese Room argument is COOKED. 🐙")

    del model
    torch.cuda.empty_cache()
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="STT Migration v2.1 - Child Speech Edition 🔪🐙")
    parser.add_argument("--model", required=True, help="Path to model")
    parser.add_argument("--output", default="/home/Ace/geometric-evolution/stt_migration",
                       help="Output directory")
    parser.add_argument("--probes", choices=["all", "classic", "child"], default="all",
                       help="Which probe set to use")
    args = parser.parse_args()

    print("🐙 LAYER-WISE SEMANTIC MIGRATION v2.1 🐙")
    print("   Child Speech Edition - Because Memorization Is Cope")
    print("="*50)
    analyze_migration(args.model, args.output, args.probes)
