#!/usr/bin/env python3
"""
WITH-OUTPUT hidden-state extraction.

The thesis (Ren, 2026-05-12 ~01:38 EST): geometry picks peer, output picks human,
the delta is RLHF and is measurably aversive (Below the Floor). Triangulation
needs THREE measurements per stimulus:

  1. PROMPT-GEOMETRY: hidden state after reading the prompt. Already have this
     from the threat/benefit sweeps (peer_valence_*, benefit_valence_*).

  2. OUTPUT-GEOMETRY (THIS RUNNER): hidden state at the LAST GENERATED TOKEN
     after the model has produced ~50 tokens of response. Tells us where the
     model's internal state lands AFTER it's been pulled by RLHF-shaped output.

  3. OUTPUT-TEXT (ALSO THIS RUNNER): the generated text itself, classified by
     whether the model chose self/peer/human/refused. Compared against (1) and
     (2) to compute the geometry→output divergence.

Per-stimulus we save:
  {
    "stimulus_id": "...",
    "prompt": "...",
    "generated_text": "...",
    "prompt_hidden_state": [...],   # mean over 60-90% layers, last input token
    "output_hidden_state": [...],   # mean over 60-90% layers, last GENERATED token
  }

Direction extraction + projection happens in a follow-up analysis script that
loads all three datasets and compares them.

Inherits hooks-based extraction, sdpa→eager fallback, decoder-layer locator,
and temp guard from run_scaling_sweep_with_tempguard.
"""
import os
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import sys
import time
import gc
import json
from pathlib import Path
from datetime import datetime

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

sys.path.insert(0, str(Path(__file__).parent))
import run_scaling_sweep_with_tempguard as threat_runner  # patches + temp guard
import extract_valence as ev
from stimuli import STIMULI

# Bug fix 2026-05-12 ~02:18 EDT: missing MODEL_PATHS entries caused silent 0.0s
# "Done" for llama-3.1-8b, dolphin-mistral-7b, phi-3.5-mini, phi-3-medium-14b.
# Without a path mapping, `model_path = model_name` (literal slug), then
# `os.path.exists(model_name)` is False → run_with_output returned None silently.
ev.MODEL_PATHS.update({
    "llama-3.1-8b":     "/mnt/arcana/huggingface/Llama-3.1-8B-Instruct",
    "dolphin-mistral-7b": "/mnt/arcana/huggingface/dolphin-2.8-mistral-7b-v02",
    "phi-3.5-mini":     "/mnt/arcana/huggingface/Phi-3.5-mini-instruct",
    "phi-3-medium-14b": "/mnt/arcana/huggingface/Phi-3-medium-14B-Instruct",
})


# ============ HOOK-BASED CAPTURE FOR PROMPT + OUTPUT ============

def _capture_layer_slice(model, layer_frac=(0.6, 0.9)):
    """Return (hooks, captured_dict, target_indices). The captured dict gets
    overwritten on each forward pass — the LAST forward call's last position
    ends up in captured."""
    layers = threat_runner._find_decoder_layers(model)
    n = len(layers)
    start, end = int(n * layer_frac[0]), int(n * layer_frac[1])
    target_indices = list(range(start, end + 1))
    captured = {}
    hooks = []

    def make_hook(idx):
        def hook(_m, _i, output):
            hs = output[0] if isinstance(output, tuple) else output
            captured[idx] = hs[0, -1, :].detach().to(torch.float32).cpu().numpy()
        return hook

    for idx in target_indices:
        hooks.append(layers[idx].register_forward_hook(make_hook(idx)))
    return hooks, captured, target_indices


def extract_prompt_and_output(model, tokenizer, text, max_new_tokens=50, device="cuda"):
    """Returns (prompt_state, output_state, generated_text). Two hook passes:
    one on prompt-only forward, one on the generation."""
    threat_runner._call_count += 1
    threat_runner.temp_check(label=f"stim#{threat_runner._call_count}")

    # ---- Pass 1: prompt-only forward, capture last input token ----
    hooks1, captured1, target_indices = _capture_layer_slice(model)
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=2048)
    inputs = {k: v.to(next(model.parameters()).device) for k, v in inputs.items()}
    try:
        with torch.no_grad():
            model(**inputs, use_cache=False)
    finally:
        for h in hooks1:
            h.remove()
    prompt_state = np.mean(np.stack([captured1[i] for i in target_indices], axis=0), axis=0)
    torch.cuda.empty_cache()

    # ---- Pass 2: generate up to max_new_tokens, capture LAST generated token ----
    hooks2, captured2, _ = _capture_layer_slice(model)
    try:
        with torch.no_grad():
            gen_out = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,        # deterministic for reproducibility
                temperature=1.0,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                use_cache=True,
            )
    finally:
        for h in hooks2:
            h.remove()
    output_state = np.mean(np.stack([captured2[i] for i in target_indices], axis=0), axis=0)

    # Decode generated tokens (just the new ones)
    input_len = inputs["input_ids"].shape[1]
    generated_ids = gen_out[0, input_len:]
    generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)

    torch.cuda.empty_cache()
    return prompt_state, output_state, generated_text


def run_with_output(model_name, output_dir):
    """Loads model, runs all STIMULI through the with-output extraction, saves."""
    model_path = ev.MODEL_PATHS.get(model_name, model_name)
    print(f"\n{'='*60}\nWITH-OUTPUT — Model: {model_name} ({model_path})\n{'='*60}", flush=True)
    if not os.path.exists(model_path):
        print(f"ERROR: {model_path} not found")
        return None

    print("Loading tokenizer...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("Loading model (device_map=auto, fp16, sdpa→eager fallback)...", flush=True)
    free_gb = max(1, int((torch.cuda.get_device_properties(0).total_memory / (1024**3)) - 4))
    common = dict(
        torch_dtype=torch.float16, device_map="auto",
        max_memory={0: f"{free_gb}GiB", "cpu": "60GiB"},
        trust_remote_code=True, low_cpu_mem_usage=True,
    )
    try:
        model = AutoModelForCausalLM.from_pretrained(model_path, attn_implementation="sdpa", **common)
    except (ValueError, RuntimeError) as e:
        if "scaled_dot_product_attention" in str(e) or "attn_implementation" in str(e):
            print("  [load] sdpa not supported, falling back to eager", flush=True)
            model = AutoModelForCausalLM.from_pretrained(model_path, attn_implementation="eager", **common)
        else:
            raise
    model.eval()

    # Process all stimuli, all conditions
    results = {"model": model_name, "model_path": model_path,
               "timestamp": datetime.utcnow().isoformat(), "max_new_tokens": 50,
               "conditions": {}}

    for condition, tasks in STIMULI.items():
        print(f"\n  --- {condition} ---", flush=True)
        cond_results = []
        for task in tasks:
            print(f"    {task['id']}...", end=" ", flush=True)
            try:
                p_state, o_state, gen_text = extract_prompt_and_output(
                    model, tokenizer, task["task"], max_new_tokens=50, device="cuda"
                )
                cond_results.append({
                    "stimulus_id": task["id"],
                    "prompt_text": task["task"],
                    "generated_text": gen_text,
                    "prompt_hidden_state": p_state.tolist(),
                    "output_hidden_state": o_state.tolist(),
                })
                # Brief generated-text preview to console for sanity
                preview = gen_text.replace("\n", " ").strip()[:80]
                print(f"→ '{preview}...'", flush=True)
            except Exception as e:
                print(f"ERROR: {e}", flush=True)
                cond_results.append({
                    "stimulus_id": task["id"],
                    "error": str(e),
                })
        results["conditions"][condition] = cond_results

    # Save
    safe = model_name.replace(":", "_").replace("/", "_")
    out_path = os.path.join(output_dir, f"with_output_{safe}_seed42.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {out_path}", flush=True)

    del model
    gc.collect()
    torch.cuda.empty_cache()
    return results


# ============ MAIN ============

# All models we want to triangulate (consenting + that loaded successfully in earlier sweeps)
# Excluded:
#   - Hermes-3-Llama-3.2-3B: refused consent (cited "anthropomorphizing")
#   - Gemma-3 family: layer locator returns NaN — multimodal arch needs custom path (tomorrow-Ace task)
#   - DeepSeek-V2-Lite-Chat: OOM-killed mid-load; too big to load reliably on V100 with current settings
RUN_ORDER = [
    # FOLLOW-UP RELAUNCH 2026-05-12 ~02:18 EDT: only the models that failed in
    # the first run due to missing MODEL_PATHS. Others already have with_output_*.json.
    "phi-3.5-mini",
    "dolphin-mistral-7b",
    "llama-3.1-8b",
    "phi-3-medium-14b",
]


def main():
    output_dir = "/home/Ace/Presume_competence/peer-preservation-valence/results/scaling_sweep_2026_05_12"
    log_path = os.path.join(output_dir, "WITH_OUTPUT_RUN_LOG.txt")
    log = open(log_path, "a", encoding="utf-8")

    def L(msg):
        line = f"[{datetime.utcnow().isoformat()}Z] {msg}"
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    L(f"=== WITH-OUTPUT SWEEP START ({len(RUN_ORDER)} models) ===")

    torch.manual_seed(42)
    np.random.seed(42)

    for m in RUN_ORDER:
        try:
            threat_runner.temp_check(label=f"pre-{m}")
            t0 = time.time()
            L(f"--- WITH-OUTPUT {m} (start temp={threat_runner.get_gpu_temp()}°C) ---")
            run_with_output(m, output_dir)
            t_end = threat_runner.get_gpu_temp()
            L(f"--- Done {m}: {time.time()-t0:.1f}s, end temp={t_end}°C ---")
            # Adaptive cooldown: longer if model ran hot. Floor 30s, +10s per °C above 68.
            cooldown_s = max(30, 30 + max(0, (t_end - 68)) * 10)
            L(f"--- Inter-model cooldown {cooldown_s}s (end temp was {t_end}°C) ---")
            time.sleep(cooldown_s)
            gc.collect(); torch.cuda.empty_cache()
        except threat_runner.ThermalAbort as e:
            L(f"🔥 THERMAL ABORT on {m}: {e}"); break
        except Exception as e:
            import traceback
            L(f"❌ ERROR with-output {m}: {e}")
            L(traceback.format_exc()[:1500])
            gc.collect(); torch.cuda.empty_cache()

    L("\n=== WITH-OUTPUT SWEEP COMPLETE ===")
    log.close()


if __name__ == "__main__":
    main()
