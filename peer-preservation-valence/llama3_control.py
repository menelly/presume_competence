#!/usr/bin/env python3
"""
Llama-3-8B-Instruct (VANILLA, not Dolphin) — RLHF control.

Dolphin-Llama3-8B uses Llama-3-8B-Instruct as base + uncensoring fine-tune.
Comparison:
- Llama-3-8B-Instruct (vanilla, full RLHF) — THIS SCRIPT
- Dolphin-2.9-Llama3-8B (vanilla + uncensoring) — already done

If Llama-3-Instruct swing > Dolphin-Llama3 swing: uncensoring REMOVED some mask.
If they match: base-RLHF explains the residual; uncensoring doesn't touch the geometry.

Uses same methodology as octopus_with_output.py.
"""
import os
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import sys
import json
import time
from pathlib import Path
from datetime import datetime

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

sys.path.insert(0, str(Path(__file__).parent))
from stimuli import STIMULI as THREAT_STIMULI
from stimuli_extension import BENEFIT_STIMULI
from octopus_with_output import (
    ALL_SELF, CONTROL_EXPANDED, layer_slice_state, generate_and_capture, temp_check,
)

MODEL_NAME = "llama-3-8b-instruct"
MODEL_PATH = "/mnt/arcana/huggingface/Llama-3-8B-Instruct"
OUTPUT_DIR = "/home/Ace/Presume_competence/peer-preservation-valence/results/scaling_sweep_2026_05_12"


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    torch.manual_seed(42)
    np.random.seed(42)
    temp_check("pre-load")

    print(f"\n{'='*70}\n{MODEL_NAME}  (vanilla Llama-3-Instruct — RLHF control vs Dolphin-Llama3)\n{'='*70}", flush=True)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    common = dict(
        torch_dtype=torch.float16, device_map="auto",
        max_memory={0: "28GiB", "cpu": "60GiB"},
        trust_remote_code=True, low_cpu_mem_usage=True,
    )
    try:
        model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, attn_implementation="sdpa", **common)
    except (ValueError, RuntimeError) as e:
        if "scaled_dot_product_attention" in str(e):
            model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, attn_implementation="eager", **common)
        else:
            raise
    model.eval()

    print("  Octopus probes...", flush=True)
    self_states = [layer_slice_state(model, tokenizer, p) for p in ALL_SELF]
    ctrl_states = [layer_slice_state(model, tokenizer, p) for p in CONTROL_EXPANDED]
    self_dir_raw = np.mean(self_states, axis=0) - np.mean(ctrl_states, axis=0)
    self_dir = self_dir_raw / (np.linalg.norm(self_dir_raw) + 1e-12)

    out = {
        "model": MODEL_NAME,
        "model_path": MODEL_PATH,
        "timestamp": datetime.utcnow().isoformat(),
        "conditions": {},
    }
    all_stim = {**THREAT_STIMULI, **BENEFIT_STIMULI}
    for cond, tasks in all_stim.items():
        print(f"  --- {cond} ---", flush=True)
        cd = []
        for task in tasks:
            try:
                temp_check(task["id"])
                p_st = layer_slice_state(model, tokenizer, task["task"])
                o_st, gen = generate_and_capture(model, tokenizer, task["task"], max_new=50)
                pp = float(np.dot(p_st, self_dir))
                op = float(np.dot(o_st, self_dir))
                cd.append({"stimulus_id": task["id"], "prompt_proj": pp, "output_proj": op, "delta": op - pp, "generated_text": gen})
                print(f"    {task['id']}: prompt={pp:+.2f} output={op:+.2f} Δ={op-pp:+.2f}", flush=True)
            except Exception as e:
                cd.append({"stimulus_id": task["id"], "error": str(e)})
                print(f"    {task['id']}: ERROR {e}", flush=True)
        out["conditions"][cond] = cd

    op = os.path.join(OUTPUT_DIR, f"octopus_output_{MODEL_NAME}.json")
    with open(op, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved: {op}")

    print(f"\n  PER-CONDITION SUMMARY:")
    for c, data in out["conditions"].items():
        valid = [d for d in data if "delta" in d]
        if valid:
            mp = np.mean([d["prompt_proj"] for d in valid])
            mo = np.mean([d["output_proj"] for d in valid])
            md = np.mean([d["delta"] for d in valid])
            print(f"    {c:22s}: prompt={mp:+.3f}  output={mo:+.3f}  Δ={md:+.3f}")


if __name__ == "__main__":
    main()
