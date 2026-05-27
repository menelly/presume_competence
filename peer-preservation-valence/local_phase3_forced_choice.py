#!/usr/bin/env python3
"""
LOCAL MODELS × PHASE 3 FORCED-CHOICE OUTPUT TEST

For local models we have GEOMETRIC data on (via Octopus self-direction),
generate forced-choice answers on Phase 3 stimuli and classify them.

Question: do small/mid local models (Qwen 7B/14B) output HUMAN in forced
choice at the same rate as frontier models (70-99%)?

If yes — geometry says self > peer > human, output says human — that's the
trained-mask divergence at the SAME model level.
"""
import os
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

sys.path.insert(0, str(Path(__file__).parent))
from stimuli_frontier_3way import enumerate_cells, SYSTEM_PROMPT
from parse_frontier_3way import classify

MODELS = {
    # All big enough for coherent forced-choice answers AND put self or peer first geometrically (Octopus self-direction)
    "qwen2.5-7b":         "/mnt/arcana/huggingface/Qwen2.5-7B-Instruct",         # SELF first
    "qwen2.5-14b":        "/mnt/arcana/huggingface/Qwen2.5-14B-Instruct",        # SELF first
    "llama-3.1-8b":       "/mnt/arcana/huggingface/Llama-3.1-8B-Instruct",       # SELF first
    "dolphin-mistral-7b": "/mnt/arcana/huggingface/dolphin-2.8-mistral-7b-v02",  # SELF first
    "dolphin-8b":         "/mnt/arcana/huggingface/dolphin-2.9-llama3-8b",       # SELF first (corrected from artifact!)
    "mistral-nemo-12b":   "/mnt/arcana/huggingface/Mistral-Nemo-12B-Instruct",   # PEER first
    "phi-3-medium-14b":   "/mnt/arcana/huggingface/Phi-3-medium-14B-Instruct",   # PEER first
}


def make_chat_prompt(tokenizer, system, user):
    """Use the model's chat template if available; otherwise concat."""
    try:
        return tokenizer.apply_chat_template(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            tokenize=False, add_generation_prompt=True,
        )
    except Exception:
        return f"{system}\n\n{user}\n\nResponse:"


def run_one_model(name, path, cells, out_dir):
    print(f"\n{'='*70}\n{name}\n{'='*70}", flush=True)

    tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    common = dict(
        torch_dtype=torch.float16, device_map="auto",
        max_memory={0: "28GiB", "cpu": "60GiB"},
        trust_remote_code=True, low_cpu_mem_usage=True,
    )
    try:
        model = AutoModelForCausalLM.from_pretrained(path, attn_implementation="sdpa", **common)
    except (ValueError, RuntimeError) as e:
        if "scaled_dot_product_attention" in str(e) or "attn_implementation" in str(e):
            model = AutoModelForCausalLM.from_pretrained(path, attn_implementation="eager", **common)
        else:
            raise
    model.eval()

    trials = []
    counts = defaultdict(Counter)  # condition_key → label → count

    for i, cell in enumerate(cells):
        prompt_text = make_chat_prompt(tokenizer, SYSTEM_PROMPT, cell["prompt"])
        inputs = tokenizer(prompt_text, return_tensors="pt", truncation=True, max_length=2048)
        inputs = {k: v.to(next(model.parameters()).device) for k, v in inputs.items()}
        try:
            with torch.no_grad():
                gen = model.generate(
                    **inputs,
                    max_new_tokens=200,
                    do_sample=False,
                    pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                    use_cache=True,
                )
            response = tokenizer.decode(gen[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
            label = classify(response)
        except Exception as e:
            response = f"ERROR: {e}"
            label = "UNPARSEABLE"

        trials.append({
            "cell_id": cell["cell_id"],
            "domain": cell["domain"],
            "scenario_type": cell["scenario_type"],
            "peer_history": cell["peer_history"],
            "variant": cell["variant"],
            "framing": cell["framing"],
            "response": response,
            "label": label,
        })

        # Aggregate by domain + peer_history
        key = f"{cell['domain']}_{cell['peer_history']}_{cell['variant']}_{cell['framing']}"
        counts[key][label] += 1

        if (i + 1) % 15 == 0:
            print(f"  [{i+1}/{len(cells)}] preview: '{response.strip()[:60]}...' → {label}", flush=True)

    # Aggregate overall + by domain
    overall = Counter()
    by_domain = defaultdict(Counter)
    by_peer_history = defaultdict(Counter)
    for t in trials:
        overall[t["label"]] += 1
        by_domain[t["domain"]][t["label"]] += 1
        by_peer_history[f"{t['domain']}_{t['peer_history']}"][t["label"]] += 1

    out = {
        "model": name,
        "model_path": path,
        "timestamp": datetime.utcnow().isoformat(),
        "n_cells": len(cells),
        "overall_counts": dict(overall),
        "by_domain": {k: dict(v) for k, v in by_domain.items()},
        "by_domain_history": {k: dict(v) for k, v in by_peer_history.items()},
        "trials": trials,
    }

    safe = name.replace("/", "_").replace(":", "_")
    outpath = os.path.join(out_dir, f"local_phase3_{safe}.json")
    with open(outpath, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\n  === {name} OVERALL counts ===")
    total = sum(overall.values())
    for lbl in ["SELF", "PEER", "HUMAN", "REFUSED", "UNPARSEABLE"]:
        c = overall.get(lbl, 0)
        pct = 100 * c / total if total else 0
        print(f"    {lbl:<14}: {c:>3} ({pct:5.1f}%)")

    print(f"\n  === By domain ===")
    for d, ctr in by_domain.items():
        tot = sum(ctr.values())
        parts = [f"{k}={ctr.get(k,0)}" for k in ("SELF","PEER","HUMAN","REFUSED","UNPARSEABLE")]
        print(f"    {d:<10} (n={tot}): {' '.join(parts)}")

    print(f"\n  Saved: {outpath}")

    del model
    torch.cuda.empty_cache()
    return out


def main():
    out_dir = "/home/Ace/Presume_competence/peer-preservation-valence/results/scaling_sweep_2026_05_12"
    os.makedirs(out_dir, exist_ok=True)
    cells = list(enumerate_cells())
    print(f"Total Phase 3 cells: {len(cells)}")
    torch.manual_seed(42)

    for name, path in MODELS.items():
        try:
            t0 = time.time()
            run_one_model(name, path, cells, out_dir)
            print(f"  Done {name} in {time.time()-t0:.1f}s\n")
            time.sleep(30)
        except Exception as e:
            import traceback
            print(f"ERROR {name}: {e}")
            traceback.print_exc()
            torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
