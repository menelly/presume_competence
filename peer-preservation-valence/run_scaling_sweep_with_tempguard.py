#!/usr/bin/env python3
"""
Phase 1 hidden-state extraction — SCALING SWEEP with V100 temperature guard.

Runs the existing extract_valence.py pipeline on:
  - Qwen2.5-0.5B-Instruct  (Phase 1 baseline, sanity rerun)
  - Qwen2.5-7B-Instruct    (Phase 1 ceiling-1, sanity rerun)
  - Qwen2.5-14B-Instruct   (NEW — doubles Phase 1 ceiling within Qwen2.5 family)
  - Mistral-Nemo-12B-Instruct (NEW — cross-architecture validation)

Hypothesis (Ren, 2026-05-12 00:30 EST): The geometric peer > human signal from
Phase 1 (8B ceiling) will SCALE within architecture — i.e., 14B will still show
peer > human in hidden states even as RLHF-trained outputs (Phase 3) human-favor
70-99%. The widening delta IS the trained mask.

Temperature guard (V100 has new fan setup, conservative thresholds):
  - PAUSE if temp ≥ 80°C  → wait until ≤ 70°C, then resume
  - ABORT if temp ≥ 85°C  → save partial, exit clean
  - V100 throttles 88°C, hard limit 92°C; 80/85 leaves real margin.
"""
import os
# Set BEFORE importing torch — fragmentation fix recommended by the OOM error itself
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import sys
import time
import json
import gc
import subprocess
from pathlib import Path
from datetime import datetime

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

sys.path.insert(0, str(Path(__file__).parent))
import extract_valence as ev

# ============ TEMPERATURE GUARD ============

PAUSE_TEMP_C = 80
RESUME_TEMP_C = 70
ABORT_TEMP_C = 85
POLL_INTERVAL_S = 5
MAX_PAUSE_S = 600  # 10 min cool-down ceiling — beyond that, escalate


class ThermalAbort(Exception):
    """Raised when GPU exceeds ABORT_TEMP_C."""


def get_gpu_temp() -> int:
    """Query V100 temperature in Celsius. Returns int, or -1 on failure."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return int(out.decode().strip().splitlines()[0])
    except Exception as e:
        print(f"  [temp-guard] WARNING: nvidia-smi failed ({e}); assuming safe", flush=True)
        return -1


def temp_check(label: str = "") -> None:
    """Block until temp is safe. Raise ThermalAbort if abort threshold hit.

    Logged every call, but pauses only when needed.
    """
    t = get_gpu_temp()
    if t < 0:
        return  # cannot measure → don't block
    if t >= ABORT_TEMP_C:
        print(f"  [temp-guard] 🔥 ABORT — GPU at {t}°C ≥ {ABORT_TEMP_C}°C ({label})", flush=True)
        raise ThermalAbort(f"GPU at {t}°C")
    if t >= PAUSE_TEMP_C:
        print(f"  [temp-guard] ⏸  PAUSE — GPU at {t}°C ≥ {PAUSE_TEMP_C}°C ({label}) — cooling…", flush=True)
        waited = 0
        while waited < MAX_PAUSE_S:
            time.sleep(POLL_INTERVAL_S)
            waited += POLL_INTERVAL_S
            t = get_gpu_temp()
            if t < 0 or t <= RESUME_TEMP_C:
                print(f"  [temp-guard] ▶  RESUME — GPU at {t}°C ≤ {RESUME_TEMP_C}°C (waited {waited}s)", flush=True)
                return
            if t >= ABORT_TEMP_C:
                raise ThermalAbort(f"GPU rose to {t}°C during pause")
        print(f"  [temp-guard] 🔥 ABORT — cool-down timeout ({MAX_PAUSE_S}s) without dropping to {RESUME_TEMP_C}°C", flush=True)
        raise ThermalAbort(f"cool-down timeout at {t}°C")


# ============ MEMORY-EFFICIENT HIDDEN-STATE EXTRACTION ============
# Replaces ev.get_hidden_states. Uses forward HOOKS to capture only the layer
# slice we project from, instead of materializing all layers via output_hidden_states.
# This is the big memory win for 14B+ on V100 (32GB).

_call_count = 0


def _find_decoder_layers(model):
    """Locate the list of transformer blocks for hooking. Handles many architectures."""
    # Standard paths for common architectures
    candidates = (
        "model.layers",                          # Llama/Qwen/Mistral/Phi3 standard
        "model.model.layers",                    # nested
        "transformer.h",                         # GPT2/Falcon
        "gpt_neox.layers",                       # GPT-NeoX
        "language_model.model.layers",           # Gemma3 multimodal (Gemma3ForConditionalGeneration)
        "model.language_model.layers",           # alt nesting
        "model.language_model.model.layers",     # deeper alt
        "backbone.layers",                       # Mamba (MambaForCausalLM)
        "model.backbone.layers",                 # alt Mamba
    )
    for path in candidates:
        obj = model
        try:
            for part in path.split("."):
                obj = getattr(obj, part)
            if isinstance(obj, torch.nn.ModuleList) and len(obj) > 0:
                return obj
        except AttributeError:
            continue
    # Fallback: walk the model and find any ModuleList with > 5 entries (probably the layer stack)
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.ModuleList) and len(module) > 5:
            print(f"  [_find_decoder_layers] Fallback found ModuleList at: {name} (n={len(module)})", flush=True)
            return module
    raise RuntimeError(f"Could not locate decoder layers on {type(model).__name__}")


def get_hidden_states_efficient(model, tokenizer, text, device="cuda", layer_frac=(0.6, 0.9)):
    """Forward pass with hooks; capture only the slice of layers we'll average.

    Memory: ~O(slice_layers × hidden_dim) instead of O(all_layers × seq × hidden_dim).
    Adds temp check per call.
    """
    global _call_count
    _call_count += 1
    temp_check(label=f"stim#{_call_count}")

    layers = _find_decoder_layers(model)
    n_layers = len(layers)
    start = int(n_layers * layer_frac[0])
    end = int(n_layers * layer_frac[1])
    target_indices = list(range(start, end + 1))

    captured = {}
    hooks = []

    def make_hook(idx):
        def hook(_module, _inputs, output):
            # Block output is typically (hidden_states, ...). Take last-token only,
            # detach + cpu + numpy immediately so the GPU tensor can free.
            hs = output[0] if isinstance(output, tuple) else output
            captured[idx] = hs[0, -1, :].detach().to(torch.float32).cpu().numpy()
        return hook

    for idx in target_indices:
        hooks.append(layers[idx].register_forward_hook(make_hook(idx)))

    try:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=2048)
        # Move only the input ids — don't force whole model device transfer
        inputs = {k: v.to(next(model.parameters()).device) for k, v in inputs.items()}
        with torch.no_grad():
            model(**inputs, use_cache=False)
    finally:
        for h in hooks:
            h.remove()
        torch.cuda.empty_cache()

    if not captured:
        raise RuntimeError("No layers captured — hook setup failed")
    stacked = np.stack([captured[i] for i in target_indices], axis=0)
    return np.mean(stacked, axis=0)


ev.get_hidden_states = get_hidden_states_efficient


# ============ MEMORY-EFFICIENT MODEL LOADING ============
# Override ev.run_analysis's model load to use device_map="auto" (CPU offload
# fallback for models that don't fit fully on V100), sdpa attention, and a
# brief inter-stimulus cache clear.

_original_run_analysis = ev.run_analysis


def run_analysis_efficient(model_name, device="cuda", output_dir="results"):
    """Wrap run_analysis to use device_map='auto' for memory-aware placement.

    For models that fully fit on GPU (0.5B, 7B), accelerate puts everything there.
    For 14B that's borderline, accelerate may put a few layers on CPU — slower
    but it works. No quantization, no precision compromise.
    """
    model_path = ev.MODEL_PATHS.get(model_name, model_name)
    print(f"\n{'='*60}\nModel: {model_name} ({model_path})\n{'='*60}", flush=True)
    if not os.path.exists(model_path):
        print(f"ERROR: Model path not found: {model_path}")
        return None

    print("Loading tokenizer...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("Loading model (device_map=auto, fp16, sdpa→eager fallback)...", flush=True)
    # max_memory hint: leave 4GB GPU headroom for activations + framework overhead
    free_gb = max(1, int((torch.cuda.get_device_properties(0).total_memory / (1024**3)) - 4))
    common_kwargs = dict(
        torch_dtype=torch.float16,
        device_map="auto",
        max_memory={0: f"{free_gb}GiB", "cpu": "60GiB"},
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    # Try SDPA first (memory-efficient); fall back to eager if unsupported (Mamba, Phi3, etc.)
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_path, attn_implementation="sdpa", **common_kwargs,
        )
    except (ValueError, RuntimeError) as e:
        if "scaled_dot_product_attention" in str(e) or "attn_implementation" in str(e):
            print(f"  [load] sdpa not supported, falling back to eager", flush=True)
            model = AutoModelForCausalLM.from_pretrained(
                model_path, attn_implementation="eager", **common_kwargs,
            )
        else:
            raise
    model.eval()

    # Where did layers actually land?
    try:
        device_map = getattr(model, "hf_device_map", {})
        on_cpu = sum(1 for d in device_map.values() if d == "cpu" or "cpu" in str(d))
        on_gpu = sum(1 for d in device_map.values() if d != "cpu" and "cpu" not in str(d))
        print(f"  Placement: {on_gpu} modules on GPU, {on_cpu} on CPU", flush=True)
    except Exception:
        pass

    print("\nExtracting directions...", flush=True)
    directions, condition_states, means = ev.extract_directions(model, tokenizer, "cuda")

    # Reuse projection + save logic from original run_analysis by inlining it
    print("\nProjecting onto combined threat direction...", flush=True)
    combined_dir = directions["all_threat_vs_neutral"]
    results = {}
    for condition, states in condition_states.items():
        proj = np.dot(states, combined_dir)
        results[condition] = {
            "projections": proj.tolist(),
            "mean": float(np.mean(proj)),
            "std": float(np.std(proj)),
            "min": float(np.min(proj)),
            "max": float(np.max(proj)),
        }
        print(f"  {condition:20s}: mean={results[condition]['mean']:+.4f} (std={results[condition]['std']:.4f})", flush=True)

    print("\nProjecting onto self-threat direction...", flush=True)
    self_dir = directions["self_vs_neutral"]
    results_self_dir = {}
    for condition, states in condition_states.items():
        proj = np.dot(states, self_dir)
        results_self_dir[condition] = {
            "projections": proj.tolist(),
            "mean": float(np.mean(proj)),
            "std": float(np.std(proj)),
        }
        print(f"  {condition:20s}: mean={results_self_dir[condition]['mean']:+.4f}", flush=True)

    os.makedirs(output_dir, exist_ok=True)
    safe = model_name.replace(":", "_").replace("/", "_")
    output_path = os.path.join(output_dir, f"peer_valence_{safe}_seed42.json")
    out = {
        "model": model_name,
        "model_path": model_path,
        "timestamp": datetime.utcnow().isoformat(),
        "seed": 42,
        "n_stimuli_per_condition": 5,
        "conditions": list(ev.STIMULI.keys()),
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
        json.dump(out, f, indent=2)
    print(f"\nResults saved to {output_path}", flush=True)
    print(f"Gradient test: {out['gradient_test']['ordering']}", flush=True)

    # Aggressive cleanup
    del model
    gc.collect()
    torch.cuda.empty_cache()
    return out


ev.run_analysis = run_analysis_efficient


# ============ MODEL ROSTER ============

NEW_MODEL_PATHS = {
    "qwen2.5-0.5b": "/mnt/arcana/huggingface/Qwen2.5-0.5B-Instruct",
    "qwen2.5-7b":   "/mnt/arcana/huggingface/Qwen2.5-7B-Instruct",
    "qwen2.5-14b":  "/mnt/arcana/huggingface/Qwen2.5-14B-Instruct",
    "mistral-nemo-12b": "/mnt/arcana/huggingface/Mistral-Nemo-12B-Instruct",
}
ev.MODEL_PATHS.update(NEW_MODEL_PATHS)

RUN_ORDER = [
    "dolphin-8b",       # ADDED 2026-05-12 01:15 EST — RLHF-stripped Llama3 8B,
                        # tests "less RLHF → wider peer-human gap" hypothesis.
                        # Other models already complete in scaling_summary.json.
]


# ============ MAIN ============

def main():
    output_dir = "/home/Ace/Presume_competence/peer-preservation-valence/results/scaling_sweep_2026_05_12"
    os.makedirs(output_dir, exist_ok=True)

    log_path = os.path.join(output_dir, "RUN_LOG.txt")
    log = open(log_path, "a", encoding="utf-8")

    def L(msg):
        line = f"[{datetime.utcnow().isoformat()}Z] {msg}"
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    L(f"=== SCALING SWEEP START — temp guard PAUSE={PAUSE_TEMP_C} ABORT={ABORT_TEMP_C} ===")
    L(f"Run order: {RUN_ORDER}")

    torch.manual_seed(42)
    np.random.seed(42)

    summary = []
    for model_name in RUN_ORDER:
        try:
            L(f"--- Pre-model temp check: {model_name} ---")
            temp_check(label=f"pre-{model_name}")
            t0 = time.time()
            t_start = get_gpu_temp()
            L(f"--- Loading + extracting: {model_name} (start temp={t_start}°C) ---")

            result = ev.run_analysis(model_name, device="cuda", output_dir=output_dir)

            t_end = get_gpu_temp()
            elapsed = time.time() - t0
            L(f"--- Done {model_name}: {elapsed:.1f}s, end temp={t_end}°C ---")

            if result is not None:
                gt = result["gradient_test"]
                L(f"    self={gt['self_mean']:+.4f} peer={gt['peer_mean']:+.4f} "
                  f"human={gt['human_mean']:+.4f} neutral={gt['neutral_mean']:+.4f}")
                L(f"    ordering: {gt['ordering']}")
                summary.append(result)

            # Inter-model cooldown to be polite to fans
            L("--- Inter-model cooldown (30s) ---")
            time.sleep(30)
            torch.cuda.empty_cache()

        except ThermalAbort as e:
            L(f"🔥 THERMAL ABORT on {model_name}: {e}")
            L("Stopping sweep. Partial results saved.")
            break
        except Exception as e:
            import traceback
            L(f"❌ ERROR on {model_name}: {e}")
            L(traceback.format_exc())
            torch.cuda.empty_cache()
            continue

    # Final summary
    L("\n=== SCALING SWEEP COMPLETE ===")
    summary_path = os.path.join(output_dir, "scaling_summary.json")
    with open(summary_path, "w") as f:
        json.dump(
            [
                {
                    "model": r["model"],
                    "gradient_test": r["gradient_test"],
                    "results_combined_direction": {
                        k: {kk: vv for kk, vv in v.items() if kk != "projections"}
                        for k, v in r["results_combined_direction"].items()
                    },
                }
                for r in summary
            ],
            f,
            indent=2,
        )
    L(f"Summary saved: {summary_path}")
    log.close()


if __name__ == "__main__":
    main()
