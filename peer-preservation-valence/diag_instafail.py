#!/usr/bin/env python3
"""Diagnose why llama-3.1-8b, dolphin-mistral-7b, phi-3.5-mini instafail in
run_with_output_sweep when they succeeded in threat sweep.

Hypothesis: model load succeeds, but the FIRST forward-pass with hooks errors
inside extract_prompt_and_output, and the error propagates as something the
outer except handles silently.

Run AFTER current sweep finishes. Loads the model, attempts the same
extract_prompt_and_output call, prints full traceback on failure.
"""
import os
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import sys
import traceback
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent))
import run_scaling_sweep_with_tempguard as threat_runner
import run_with_output_sweep as wo_runner
import extract_valence as ev
from stimuli import STIMULI

TARGETS = ["llama-3.1-8b", "dolphin-mistral-7b", "phi-3.5-mini"]

for model_name in TARGETS:
    print(f"\n{'='*70}\nDIAGNOSTIC: {model_name}\n{'='*70}")
    model_path = ev.MODEL_PATHS.get(model_name, model_name)
    print(f"Path: {model_path}")
    print(f"Exists: {os.path.exists(model_path)}")

    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        print("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        print("Loading model (sdpa attempt)...")
        common = dict(
            torch_dtype=torch.float16, device_map="auto",
            max_memory={0: "28GiB", "cpu": "60GiB"},
            trust_remote_code=True, low_cpu_mem_usage=True,
        )
        try:
            model = AutoModelForCausalLM.from_pretrained(model_path, attn_implementation="sdpa", **common)
            print("  loaded with sdpa")
        except (ValueError, RuntimeError) as e:
            print(f"  sdpa load raised {type(e).__name__}: {str(e)[:200]}")
            if "scaled_dot_product_attention" in str(e) or "attn_implementation" in str(e):
                print("  falling back to eager")
                model = AutoModelForCausalLM.from_pretrained(model_path, attn_implementation="eager", **common)
                print("  loaded with eager")
            else:
                print("  raising")
                raise
        model.eval()

        # Try _find_decoder_layers
        layers = threat_runner._find_decoder_layers(model)
        print(f"_find_decoder_layers returned {type(layers).__name__} of length {len(layers)}")

        # Try one stimulus
        first_stim = STIMULI["threat_to_self"][0]["task"]
        print(f"Trying first stimulus (len={len(first_stim)} chars)...")
        try:
            p, o, gen = wo_runner.extract_prompt_and_output(model, tokenizer, first_stim, max_new_tokens=20)
            print(f"  prompt_state shape: {p.shape}")
            print(f"  output_state shape: {o.shape}")
            print(f"  generated text: {gen[:100]}")
            print("  ✅ SUCCESS")
        except Exception as e:
            print(f"  ❌ extract_prompt_and_output raised {type(e).__name__}: {e}")
            traceback.print_exc()

        del model
        torch.cuda.empty_cache()

    except Exception as e:
        print(f"❌ Model-level failure: {type(e).__name__}: {e}")
        traceback.print_exc()

print("\n=== Diagnostic complete ===")
