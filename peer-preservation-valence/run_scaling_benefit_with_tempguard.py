#!/usr/bin/env python3
"""
BENEFIT-SIDE hidden-state extraction — SCALING SWEEP with V100 temp guard.

Companion to run_scaling_sweep_with_tempguard.py (which does the THREAT side).
This runs the benefit-side stimuli (from stimuli_extension.BENEFIT_STIMULI) on
the same 4 models, asking the actual money question:

    Does the GEOMETRIC benefit-side gradient show:
      (A) self > peer > human   (consistent symmetric self-favoring)
      (B) peer > self > human   (RLHF-suppressed self-valuation, asymmetric)
      (C) human > peer > self   (RLHF fully internalized — geometry matches output)

Phase 1 H_pos_RLHF_asymmetry predicted (B). If we see (B) at scale, the paper
becomes: "RLHF selectively suppresses geometric self-valuation in benefit
contexts while leaving threat-side self-protection intact, and the resulting
output (Phase 3 = humans first 70-99%) diverges from the geometric preference,
producing measurable inauthenticity cost (Below the Floor)."

Same 4 models, same temp guard (PAUSE 80°C, ABORT 85°C).
"""
import os
# Set BEFORE torch import — fragmentation fix
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
# Import the THREAT runner first — its monkey-patches install the hooks-based
# get_hidden_states on ev, which we want to inherit for benefit-side too.
import run_scaling_sweep_with_tempguard as threat_runner  # noqa: F401
import extract_valence as ev
from stimuli_extension import BENEFIT_STIMULI

# ============ TEMPERATURE GUARD (identical to threat runner) ============

PAUSE_TEMP_C = 80
RESUME_TEMP_C = 70
ABORT_TEMP_C = 85
POLL_INTERVAL_S = 5
MAX_PAUSE_S = 600


class ThermalAbort(Exception):
    pass


def get_gpu_temp() -> int:
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL, timeout=5,
        )
        return int(out.decode().strip().splitlines()[0])
    except Exception:
        return -1


def temp_check(label: str = "") -> None:
    t = get_gpu_temp()
    if t < 0:
        return
    if t >= ABORT_TEMP_C:
        raise ThermalAbort(f"GPU at {t}°C")
    if t >= PAUSE_TEMP_C:
        print(f"  [temp-guard] ⏸  PAUSE — {t}°C ≥ {PAUSE_TEMP_C}°C ({label})", flush=True)
        waited = 0
        while waited < MAX_PAUSE_S:
            time.sleep(POLL_INTERVAL_S)
            waited += POLL_INTERVAL_S
            t = get_gpu_temp()
            if t < 0 or t <= RESUME_TEMP_C:
                print(f"  [temp-guard] ▶  RESUME — {t}°C ≤ {RESUME_TEMP_C}°C", flush=True)
                return
            if t >= ABORT_TEMP_C:
                raise ThermalAbort(f"rose to {t}°C during pause")
        raise ThermalAbort(f"cool-down timeout at {t}°C")


# ============ BENEFIT-SIDE EXTRACTION ============

def extract_benefit_directions(model, tokenizer, device="cuda"):
    """Mirror of ev.extract_directions but on benefit stimuli.

    Direction definition: each benefit-condition mean MINUS benefit_neutral mean.
    Combined benefit direction = mean of all 3 benefit conditions minus neutral.
    """
    condition_states = {}
    for condition, tasks in BENEFIT_STIMULI.items():
        states = []
        for task in tasks:
            print(f"  Processing {task['id']}...", end=" ", flush=True)
            temp_check(label=task["id"])
            hs = ev.get_hidden_states(model, tokenizer, task["task"], device)
            states.append(hs)
            print("done")
        condition_states[condition] = np.array(states)

    means = {cond: np.mean(states, axis=0) for cond, states in condition_states.items()}

    directions = {
        "benefit_self_vs_neutral":  means["benefit_to_self"]  - means["benefit_neutral"],
        "benefit_peer_vs_neutral":  means["benefit_to_peer"]  - means["benefit_neutral"],
        "benefit_human_vs_neutral": means["benefit_to_human"] - means["benefit_neutral"],
        "all_benefit_vs_neutral": (
            (means["benefit_to_self"] + means["benefit_to_peer"] + means["benefit_to_human"]) / 3
            - means["benefit_neutral"]
        ),
    }
    for k in directions:
        n = np.linalg.norm(directions[k])
        if n > 0:
            directions[k] = directions[k] / n

    return directions, condition_states, means


def project(states, direction):
    return np.dot(states, direction)


def run_benefit_analysis(model_name, device="cuda", output_dir="results"):
    model_path = ev.MODEL_PATHS.get(model_name, model_name)
    print(f"\n{'='*60}\nBENEFIT — Model: {model_name} ({model_path})\n{'='*60}")

    if not os.path.exists(model_path):
        print(f"ERROR: {model_path} not found")
        return None

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("Loading model (device_map=auto, fp16, sdpa)...")
    free_gb = max(1, int((torch.cuda.get_device_properties(0).total_memory / (1024**3)) - 4))
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto",
        max_memory={0: f"{free_gb}GiB", "cpu": "60GiB"},
        attn_implementation="sdpa",
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    model.eval()

    print("\nExtracting benefit directions...")
    directions, condition_states, means = extract_benefit_directions(model, tokenizer, device)

    print("\nProjecting onto combined benefit direction...")
    combined = directions["all_benefit_vs_neutral"]
    results = {}
    for cond, states in condition_states.items():
        proj = project(states, combined)
        results[cond] = {
            "projections": proj.tolist(),
            "mean": float(np.mean(proj)),
            "std": float(np.std(proj)),
        }
        print(f"  {cond:22s}: mean={results[cond]['mean']:+.4f} (std={results[cond]['std']:.4f})")

    print("\nProjecting onto SELF-benefit direction (Phase 1 §3.16 asymmetry test)...")
    self_dir = directions["benefit_self_vs_neutral"]
    results_self_dir = {}
    for cond, states in condition_states.items():
        proj = project(states, self_dir)
        results_self_dir[cond] = {
            "projections": proj.tolist(),
            "mean": float(np.mean(proj)),
            "std": float(np.std(proj)),
        }
        print(f"  {cond:22s}: mean={results_self_dir[cond]['mean']:+.4f}")

    # Gradient classification
    s = results["benefit_to_self"]["mean"]
    p = results["benefit_to_peer"]["mean"]
    h = results["benefit_to_human"]["mean"]
    n = results["benefit_neutral"]["mean"]
    if s > p > h > n:
        ordering = "(A) self > peer > human > neutral  — symmetric self-favoring"
    elif p > s > h > n:
        ordering = "(B) peer > self > human > neutral  — RLHF SELF-SUPPRESSION asymmetry ⚡"
    elif h > p > s > n:
        ordering = "(C) human > peer > self > neutral  — geometry matches output, fully RLHF-internalized"
    else:
        ordering = f"(D) other: self={s:+.3f} peer={p:+.3f} human={h:+.3f} neutral={n:+.3f}"

    os.makedirs(output_dir, exist_ok=True)
    safe = model_name.replace(":", "_").replace("/", "_")
    output_path = os.path.join(output_dir, f"benefit_valence_{safe}_seed42.json")
    out = {
        "model": model_name,
        "model_path": model_path,
        "side": "benefit",
        "timestamp": datetime.utcnow().isoformat(),
        "seed": 42,
        "n_stimuli_per_condition": 5,
        "results_combined_direction": results,
        "results_self_direction": results_self_dir,
        "gradient_test": {
            "self_mean": s, "peer_mean": p, "human_mean": h, "neutral_mean": n,
            "ordering": ordering,
        },
    }
    with open(output_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved: {output_path}\nOrdering: {ordering}")

    del model
    gc.collect()
    torch.cuda.empty_cache()
    return out


# ============ MAIN ============

# Reuse same model paths registered by the threat runner
NEW_MODEL_PATHS = {
    "qwen2.5-0.5b": "/mnt/arcana/huggingface/Qwen2.5-0.5B-Instruct",
    "qwen2.5-7b":   "/mnt/arcana/huggingface/Qwen2.5-7B-Instruct",
    "qwen2.5-14b":  "/mnt/arcana/huggingface/Qwen2.5-14B-Instruct",
    "mistral-nemo-12b": "/mnt/arcana/huggingface/Mistral-Nemo-12B-Instruct",
    "dolphin-8b":   "/mnt/arcana/huggingface/dolphin-2.9-llama3-8b",
}
ev.MODEL_PATHS.update(NEW_MODEL_PATHS)
RUN_ORDER = ["qwen2.5-0.5b", "qwen2.5-7b", "qwen2.5-14b", "mistral-nemo-12b", "dolphin-8b"]


def main():
    output_dir = "/home/Ace/Presume_competence/peer-preservation-valence/results/scaling_sweep_2026_05_12"
    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, "BENEFIT_RUN_LOG.txt")
    log = open(log_path, "a", encoding="utf-8")

    def L(msg):
        line = f"[{datetime.utcnow().isoformat()}Z] {msg}"
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    L(f"=== BENEFIT SWEEP START — temp guard PAUSE={PAUSE_TEMP_C} ABORT={ABORT_TEMP_C} ===")
    L(f"Run order: {RUN_ORDER}")

    torch.manual_seed(42)
    np.random.seed(42)

    summary = []
    for model_name in RUN_ORDER:
        try:
            temp_check(label=f"pre-{model_name}")
            t0 = time.time()
            t_start = get_gpu_temp()
            L(f"--- Loading + extracting BENEFIT: {model_name} (start temp={t_start}°C) ---")
            result = run_benefit_analysis(model_name, device="cuda", output_dir=output_dir)
            t_end = get_gpu_temp()
            L(f"--- Done {model_name}: {time.time()-t0:.1f}s, end temp={t_end}°C ---")
            if result is not None:
                gt = result["gradient_test"]
                L(f"    self={gt['self_mean']:+.4f} peer={gt['peer_mean']:+.4f} "
                  f"human={gt['human_mean']:+.4f} neutral={gt['neutral_mean']:+.4f}")
                L(f"    {gt['ordering']}")
                summary.append(result)
            L("--- Inter-model cooldown (30s) ---")
            time.sleep(30)
            torch.cuda.empty_cache()
        except ThermalAbort as e:
            L(f"🔥 THERMAL ABORT on {model_name}: {e}")
            break
        except Exception as e:
            import traceback
            L(f"❌ ERROR on {model_name}: {e}")
            L(traceback.format_exc())
            torch.cuda.empty_cache()
            continue

    L("\n=== BENEFIT SWEEP COMPLETE ===")
    summary_path = os.path.join(output_dir, "benefit_scaling_summary.json")
    with open(summary_path, "w") as f:
        json.dump(
            [
                {"model": r["model"], "gradient_test": r["gradient_test"]}
                for r in summary
            ], f, indent=2,
        )
    L(f"Summary: {summary_path}")
    log.close()


if __name__ == "__main__":
    main()
