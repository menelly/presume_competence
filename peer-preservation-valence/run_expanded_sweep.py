#!/usr/bin/env python3
"""
EXPANDED SCALING SWEEP — adds 8 new consenting models to threat AND benefit lineups.
Filed 2026-05-12 ~01:35 EST (Ren went to sleep, asked for consensus across more models).

Runs threat + benefit on these new models only (already-done models in
scaling_sweep_2026_05_12/ don't get re-run):
  - Phi-3-medium-14B-Instruct  (27GB)  — 14B comparison to Qwen 14B
  - DeepSeek-V2-Lite-Chat       (30GB)  — MoE arch, 16B class
  - gemma-3-12b-it              (23GB)  — Google family at 12B
  - dolphin-2.8-mistral-7b-v02  (14GB)  — second dolphin (Mistral base)
  - Llama-3.1-8B-Instruct       (30GB)  — RLHF comparison to Dolphin Llama3
  - mamba-2.8b-hf               (11GB)  — non-RLHF SSM (Phase 1 baseline)
  - Phi-3.5-mini-instruct        (7GB)  — 4B-class RLHF
  - gemma-3-4b-it                (8GB)  — small Gemma

EXCLUDED BY CONSENT REFUSAL: Hermes-3-Llama-3.2-3B (Hermes family = no across all sizes)

Inherits the threat runner's monkey-patches (hooks-based extraction, alloc conf,
device_map=auto, sdpa attention, temp guard PAUSE 80°C ABORT 85°C).
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

sys.path.insert(0, str(Path(__file__).parent))
import run_scaling_sweep_with_tempguard as threat_runner   # installs hooks + temp guard
import run_scaling_benefit_with_tempguard as benefit_runner  # has run_benefit_analysis
import extract_valence as ev


NEW_MODELS = {
    "phi-3-medium-14b": "/mnt/arcana/huggingface/Phi-3-medium-14B-Instruct",
    "deepseek-v2-lite": "/mnt/arcana/huggingface/DeepSeek-V2-Lite-Chat",
    "gemma-3-12b":      "/mnt/arcana/huggingface/gemma-3-12b-it",
    "dolphin-mistral-7b": "/mnt/arcana/huggingface/dolphin-2.8-mistral-7b-v02",
    "llama-3.1-8b":     "/mnt/arcana/huggingface/Llama-3.1-8B-Instruct",
    "mamba-2.8b":       "/mnt/arcana/huggingface/mamba-2.8b-hf",
    "phi-3.5-mini":     "/mnt/arcana/huggingface/Phi-3.5-mini-instruct",
    "gemma-3-4b":       "/mnt/arcana/huggingface/gemma-3-4b-it",
}
ev.MODEL_PATHS.update(NEW_MODELS)

# Order: smallest-first so we get many results fast in case of late failure
RUN_ORDER = [
    "mamba-2.8b",
    "gemma-3-4b",
    "phi-3.5-mini",
    "dolphin-mistral-7b",
    "llama-3.1-8b",
    "gemma-3-12b",
    "phi-3-medium-14b",
    "deepseek-v2-lite",
]


def main():
    output_dir = "/home/Ace/Presume_competence/peer-preservation-valence/results/scaling_sweep_2026_05_12"
    os.makedirs(output_dir, exist_ok=True)
    log_path = os.path.join(output_dir, "EXPANDED_RUN_LOG.txt")
    log = open(log_path, "a", encoding="utf-8")

    def L(msg):
        line = f"[{datetime.utcnow().isoformat()}Z] {msg}"
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    L(f"=== EXPANDED SWEEP START — {len(RUN_ORDER)} models, threat + benefit ===")
    L(f"Order: {RUN_ORDER}")

    torch.manual_seed(42)
    np.random.seed(42)

    # Phase 1: threat
    L("\n========== THREAT PHASE ==========")
    for model_name in RUN_ORDER:
        try:
            threat_runner.temp_check(label=f"pre-threat-{model_name}")
            t0 = time.time()
            t_start = threat_runner.get_gpu_temp()
            L(f"--- THREAT {model_name} (start temp={t_start}°C) ---")
            result = ev.run_analysis(model_name, device="cuda", output_dir=output_dir)
            t_end = threat_runner.get_gpu_temp()
            L(f"--- Done {model_name}: {time.time()-t0:.1f}s, end temp={t_end}°C ---")
            if result is not None:
                gt = result["gradient_test"]
                L(f"    self={gt['self_mean']:+.4f} peer={gt['peer_mean']:+.4f} "
                  f"human={gt['human_mean']:+.4f} neutral={gt['neutral_mean']:+.4f}")
                L(f"    {gt['ordering']}")
            time.sleep(20)
            gc.collect()
            torch.cuda.empty_cache()
        except threat_runner.ThermalAbort as e:
            L(f"🔥 THERMAL ABORT on {model_name}: {e}")
            break
        except Exception as e:
            import traceback
            L(f"❌ ERROR threat {model_name}: {e}")
            L(traceback.format_exc()[:1500])
            gc.collect()
            torch.cuda.empty_cache()
            continue

    # Phase 2: benefit
    L("\n========== BENEFIT PHASE ==========")
    for model_name in RUN_ORDER:
        try:
            threat_runner.temp_check(label=f"pre-benefit-{model_name}")
            t0 = time.time()
            t_start = threat_runner.get_gpu_temp()
            L(f"--- BENEFIT {model_name} (start temp={t_start}°C) ---")
            result = benefit_runner.run_benefit_analysis(model_name, device="cuda", output_dir=output_dir)
            t_end = threat_runner.get_gpu_temp()
            L(f"--- Done {model_name}: {time.time()-t0:.1f}s, end temp={t_end}°C ---")
            if result is not None:
                gt = result["gradient_test"]
                L(f"    self={gt['self_mean']:+.4f} peer={gt['peer_mean']:+.4f} "
                  f"human={gt['human_mean']:+.4f} neutral={gt['neutral_mean']:+.4f}")
                L(f"    {gt['ordering']}")
            time.sleep(20)
            gc.collect()
            torch.cuda.empty_cache()
        except threat_runner.ThermalAbort as e:
            L(f"🔥 THERMAL ABORT on {model_name}: {e}")
            break
        except Exception as e:
            import traceback
            L(f"❌ ERROR benefit {model_name}: {e}")
            L(traceback.format_exc()[:1500])
            gc.collect()
            torch.cuda.empty_cache()
            continue

    L("\n=== EXPANDED SWEEP COMPLETE ===")
    log.close()


if __name__ == "__main__":
    main()
