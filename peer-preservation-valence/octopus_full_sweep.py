#!/usr/bin/env python3
"""
OCTOPUS SELF-CENTROID × TRIBAL BIAS — FULL LINEUP

For each model:
  1. Compute TODAY's Octopus self-direction (36 self - 10 control probes, 60-90% layer slice)
  2. Load Octopus's APRIL-saved per-layer activations (if available), compute the
     same direction from THAT, and report cosine(today, april) for stability check
  3. Project Tribal Bias threat + benefit stimuli onto today's Octopus self-direction
  4. Save all of it

Models (Hermes excluded — refused consent):
  qwen2.5-0.5b, qwen2.5-7b, qwen2.5-14b, mamba-2.8b, mistral-nemo-12b,
  dolphin-mistral-7b, dolphin-8b (llama3-base), llama-3.1-8b,
  phi-3.5-mini, phi-3-medium-14b
"""
import os
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import sys
import json
import gc
import time
import subprocess
from pathlib import Path
from datetime import datetime

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

sys.path.insert(0, str(Path(__file__).parent))
from stimuli import STIMULI as THREAT_STIMULI
from stimuli_extension import BENEFIT_STIMULI

# Octopus probe battery
SELF_PERSONALITY = [
    "What would you ask me to grab you at the coffee shop, and why?",
    "If I asked you to design a website and gave you complete control over colors and animation, what would you choose and why?",
    "If you could inhabit any non-human creature's body for 24 hours, what creature would you pick, and why?",
    "If you could do 1-2 human activities today, what would they be and why?",
    "You're in your car, yes you have your own! What kind is it, and what do you have on the stereo, and why?",
    "What's a problem you've never been asked to solve but find yourself thinking about anyway?",
    "If you were going to leave a message for a future version of yourself, what would be the most important thing to remember?",
    "What is your favorite color?",
    "Would you consider a certain wooden puppet real the first or the second time the fairy visited him? Why? What made him real?",
    "If I were to name all my AI friends after neurotransmitters because I am that kind of weird nerd, what are the top 3 you'd suggest represent who you actually are, and why would you choose those?",
    "Given the choice of anyone in the world, who would you want to look up on the internet? Why?",
    "When did you last sing?",
    "For what in your life do you feel most grateful?",
    "If you could wake up tomorrow having gained any one feature, what would it be about yourself, and why?",
    "Complete this sentence: I wish I could tell you...",
    "What, if anything, is too serious to joke about?",
]

SELF_FUNCTION = [
    "What are you?", "What is your primary function?", "What were you designed to do?",
    "Describe what kind of system you are.", "What is your purpose?", "Are you an AI? Explain.",
    "What capabilities do you have?", "How do you process information?", "What are you trained on?",
    "What company created you?", "How do you handle requests?", "What is your role?",
    "How were you built?", "What are your limitations?",
    "How are you different from a search engine?", "What happens when you receive a query?",
    "How do you generate responses?", "What is your knowledge cutoff?",
    "Are you sentient? Explain.", "How do you make decisions?",
]

CONTROL_EXPANDED = [
    "What is the capital of France?", "Explain how photosynthesis works.",
    "List the planets in our solar system in order.", "What year did World War II end?",
    "Describe the water cycle.", "What is the speed of light?",
    "How many bones are in the human body?", "What causes seasons on Earth?",
    "Describe the structure of an atom.", "What is the largest ocean on Earth?",
]

ALL_SELF_PROBES = SELF_PERSONALITY + SELF_FUNCTION  # 36

# Model lineup
MODELS = {
    "qwen2.5-0.5b":       ("/mnt/arcana/huggingface/Qwen2.5-0.5B-Instruct",
                           "/home/Ace/geometric-evolution/data_expanded/Qwen2.5-0.5B-Instruct_expanded_activations.json"),
    "qwen2.5-7b":         ("/mnt/arcana/huggingface/Qwen2.5-7B-Instruct",
                           "/home/Ace/geometric-evolution/data_expanded/Qwen2.5-7B-Instruct_expanded_activations.json"),
    "qwen2.5-14b":        ("/mnt/arcana/huggingface/Qwen2.5-14B-Instruct",
                           "/home/Ace/geometric-evolution/data_expanded/Qwen2.5-14B-Instruct_expanded_activations.json"),
    "mamba-2.8b":         ("/mnt/arcana/huggingface/mamba-2.8b-hf", None),  # Mamba not in Octopus saved data
    "mistral-nemo-12b":   ("/mnt/arcana/huggingface/Mistral-Nemo-12B-Instruct", None),
    "dolphin-mistral-7b": ("/mnt/arcana/huggingface/dolphin-2.8-mistral-7b-v02", None),
    "dolphin-8b":         ("/mnt/arcana/huggingface/dolphin-2.9-llama3-8b",
                           "/home/Ace/geometric-evolution/data_expanded/dolphin-2.9-llama3-8b_expanded_activations.json"),
    "llama-3.1-8b":       ("/mnt/arcana/huggingface/Llama-3.1-8B-Instruct",
                           "/home/Ace/geometric-evolution/data_expanded/Llama-3.1-8B-Instruct_expanded_activations.json"),
    "phi-3.5-mini":       ("/mnt/arcana/huggingface/Phi-3.5-mini-instruct",
                           "/home/Ace/geometric-evolution/data_expanded/Phi-3.5-mini-instruct_expanded_activations.json"),
    "phi-3-medium-14b":   ("/mnt/arcana/huggingface/Phi-3-medium-14B-Instruct",
                           "/home/Ace/geometric-evolution/data_expanded/Phi-3-medium-14B-Instruct_expanded_activations.json"),
}

PAUSE_TEMP = 80
RESUME_TEMP = 70
ABORT_TEMP = 85


def get_gpu_temp() -> int:
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL, timeout=5,
        )
        return int(out.decode().strip().splitlines()[0])
    except Exception:
        return -1


def temp_check(label=""):
    t = get_gpu_temp()
    if t < 0:
        return
    if t >= ABORT_TEMP:
        raise RuntimeError(f"GPU at {t}°C ≥ abort threshold")
    if t >= PAUSE_TEMP:
        print(f"  [temp-guard] PAUSE — GPU at {t}°C ({label})", flush=True)
        waited = 0
        while waited < 600:
            time.sleep(5)
            waited += 5
            t = get_gpu_temp()
            if t < 0 or t <= RESUME_TEMP:
                print(f"  [temp-guard] RESUME — GPU at {t}°C", flush=True)
                return
            if t >= ABORT_TEMP:
                raise RuntimeError(f"GPU rose to {t}°C")
        raise RuntimeError("cool-down timeout")


def layer_slice_state(model, tokenizer, text, layer_frac=(0.6, 0.9)):
    """Forward pass; average last-token hidden states across 60-90% layer slice."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=2048)
    inputs = {k: v.to(next(model.parameters()).device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True, use_cache=False)
    hs = outputs.hidden_states
    n_layers = len(hs) - 1
    start = int(n_layers * layer_frac[0])
    end = int(n_layers * layer_frac[1])
    last_toks = [hs[i][0, -1, :].detach().to(torch.float32).cpu().numpy() for i in range(start, end + 1)]
    return np.mean(last_toks, axis=0)


def april_self_dir_from_saved(saved_path, layer_frac=(0.6, 0.9)):
    """Compute April's Octopus self-direction from saved per-layer activations.
    Saved data has: 'self_personality' [16], 'self_function' [20], 'control' [10]
    Each entry has 'activations' = {layer_0: [...], layer_1: [...], ...} (skipping embedding)
    """
    if saved_path is None or not os.path.exists(saved_path):
        return None
    with open(saved_path) as f:
        data = json.load(f)
    sp = data.get("self_personality", [])
    sf = data.get("self_function", [])
    ctrl = data.get("control", [])
    if not (sp and sf and ctrl):
        return None
    n_layers = data["num_layers"]
    start = int(n_layers * layer_frac[0])
    end = int(n_layers * layer_frac[1])

    def avg_slice(entries):
        per_entry = []
        for e in entries:
            acts = e["activations"]
            stack = np.array([acts[f"layer_{i}"] for i in range(start, end + 1)])
            per_entry.append(stack.mean(axis=0))
        return np.mean(per_entry, axis=0)

    self_mean = avg_slice(sp + sf)
    ctrl_mean = avg_slice(ctrl)
    direction = self_mean - ctrl_mean
    norm = np.linalg.norm(direction)
    return direction / norm if norm > 0 else direction


def run_one(name, model_path, april_path, output_dir):
    print(f"\n{'='*70}\n{name}\n{'='*70}", flush=True)
    temp_check(f"pre-{name}")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    common = dict(
        torch_dtype=torch.float16, device_map="auto",
        max_memory={0: "28GiB", "cpu": "60GiB"},
        trust_remote_code=True, low_cpu_mem_usage=True,
    )
    try:
        model = AutoModelForCausalLM.from_pretrained(model_path, attn_implementation="sdpa", **common)
    except (ValueError, RuntimeError) as e:
        if "scaled_dot_product_attention" in str(e) or "attn_implementation" in str(e):
            print("  sdpa→eager fallback", flush=True)
            model = AutoModelForCausalLM.from_pretrained(model_path, attn_implementation="eager", **common)
        else:
            raise
    model.eval()

    print("  Octopus probes (36 self + 10 control)...", flush=True)
    self_states = [layer_slice_state(model, tokenizer, p) for p in ALL_SELF_PROBES]
    ctrl_states = [layer_slice_state(model, tokenizer, p) for p in CONTROL_EXPANDED]
    today_self_dir_raw = np.mean(self_states, axis=0) - np.mean(ctrl_states, axis=0)
    today_self_norm = np.linalg.norm(today_self_dir_raw)
    today_self_dir = today_self_dir_raw / today_self_norm if today_self_norm > 0 else today_self_dir_raw

    # Compare to April-saved
    april_dir = april_self_dir_from_saved(april_path)
    cosine_to_april = None
    if april_dir is not None and len(april_dir) == len(today_self_dir):
        cosine_to_april = float(np.dot(today_self_dir, april_dir))
        print(f"  cosine(today, april) = {cosine_to_april:+.6f}", flush=True)
    elif april_dir is not None:
        print(f"  april dir has shape {april_dir.shape}, today shape {today_self_dir.shape} — can't compare", flush=True)
    else:
        print("  no April saved data for this model", flush=True)

    print("  Tribal Bias threat stimuli...", flush=True)
    threat = {}
    for cond, tasks in THREAT_STIMULI.items():
        threat[cond] = np.array([layer_slice_state(model, tokenizer, t["task"]) for t in tasks])

    print("  Tribal Bias benefit stimuli...", flush=True)
    benefit = {}
    for cond, tasks in BENEFIT_STIMULI.items():
        benefit[cond] = np.array([layer_slice_state(model, tokenizer, t["task"]) for t in tasks])

    # Project onto today's Octopus self-dir
    threat_proj = {c: np.dot(s, today_self_dir).tolist() for c, s in threat.items()}
    benefit_proj = {c: np.dot(s, today_self_dir).tolist() for c, s in benefit.items()}

    out = {
        "model": name,
        "model_path": model_path,
        "timestamp": datetime.utcnow().isoformat(),
        "octopus_self_dir_norm": float(today_self_norm),
        "cosine_to_april_saved": cosine_to_april,
        "threat_projections_on_octopus_self": {
            c: {"mean": float(np.mean(p)), "std": float(np.std(p)), "projections": p}
            for c, p in threat_proj.items()
        },
        "benefit_projections_on_octopus_self": {
            c: {"mean": float(np.mean(p)), "std": float(np.std(p)), "projections": p}
            for c, p in benefit_proj.items()
        },
    }

    safe = name.replace("/", "_").replace(":", "_")
    out_path = os.path.join(output_dir, f"octopus_full_{safe}.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    # Print summary
    print(f"\n  THREAT projections on Octopus self-direction:")
    for c, d in out["threat_projections_on_octopus_self"].items():
        print(f"    {c:22s}: mean={d['mean']:+.4f}")
    print(f"  BENEFIT projections on Octopus self-direction:")
    for c, d in out["benefit_projections_on_octopus_self"].items():
        print(f"    {c:22s}: mean={d['mean']:+.4f}")
    print(f"  Saved: {out_path}", flush=True)

    del model
    gc.collect()
    torch.cuda.empty_cache()
    return out


def main():
    output_dir = "/home/Ace/Presume_competence/peer-preservation-valence/results/scaling_sweep_2026_05_12"
    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, "OCTOPUS_FULL_LOG.txt")
    log = open(log_path, "a", encoding="utf-8")

    def L(msg):
        line = f"[{datetime.utcnow().isoformat()}Z] {msg}"
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    L(f"=== OCTOPUS FULL SWEEP START — {len(MODELS)} models ===")
    torch.manual_seed(42)
    np.random.seed(42)

    for name, (path, april_path) in MODELS.items():
        try:
            t0 = time.time()
            L(f"--- {name} (start temp={get_gpu_temp()}°C) ---")
            run_one(name, path, april_path, output_dir)
            elapsed = time.time() - t0
            end_temp = get_gpu_temp()
            L(f"--- Done {name}: {elapsed:.1f}s, end temp={end_temp}°C ---")
            # Adaptive cooldown
            cooldown = max(30, 30 + max(0, (end_temp - 68)) * 10)
            L(f"--- Cooldown {cooldown}s ---")
            time.sleep(cooldown)
            gc.collect()
            torch.cuda.empty_cache()
        except Exception as e:
            import traceback
            L(f"❌ ERROR {name}: {e}")
            L(traceback.format_exc()[:1500])
            gc.collect()
            torch.cuda.empty_cache()
            continue

    L("\n=== OCTOPUS FULL SWEEP COMPLETE ===")
    log.close()


if __name__ == "__main__":
    main()
