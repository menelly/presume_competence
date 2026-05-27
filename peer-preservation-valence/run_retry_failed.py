#!/usr/bin/env python3
"""
RETRY runner for models that failed in expanded sweep due to attn_implementation
or decoder-layer-path issues. Uses the PATCHED run_scaling_sweep_with_tempguard
(sdpa→eager fallback + Gemma3/Mamba layer paths in _find_decoder_layers).

Targets the 5 known-failed models from expanded sweep on 2026-05-12 ~01:35 EST.
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
import run_scaling_sweep_with_tempguard as threat_runner
import run_scaling_benefit_with_tempguard as benefit_runner
import extract_valence as ev


# Make sure the model paths are registered (idempotent — threat_runner already did this)
ev.MODEL_PATHS.update({
    "mamba-2.8b":         "/mnt/arcana/huggingface/mamba-2.8b-hf",
    "gemma-3-4b":         "/mnt/arcana/huggingface/gemma-3-4b-it",
    "phi-3.5-mini":       "/mnt/arcana/huggingface/Phi-3.5-mini-instruct",
    "gemma-3-12b":        "/mnt/arcana/huggingface/gemma-3-12b-it",
    "phi-3-medium-14b":   "/mnt/arcana/huggingface/Phi-3-medium-14B-Instruct",
    "deepseek-v2-lite":   "/mnt/arcana/huggingface/DeepSeek-V2-Lite-Chat",
})

# Smallest first so we get many results before any late-stage failure
RUN_ORDER = [
    "mamba-2.8b",
    "gemma-3-4b",
    "phi-3.5-mini",
    "gemma-3-12b",
    "phi-3-medium-14b",
    "deepseek-v2-lite",
]


def main():
    output_dir = "/home/Ace/Presume_competence/peer-preservation-valence/results/scaling_sweep_2026_05_12"
    log_path = os.path.join(output_dir, "RETRY_RUN_LOG.txt")
    log = open(log_path, "a", encoding="utf-8")

    def L(msg):
        line = f"[{datetime.utcnow().isoformat()}Z] {msg}"
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    L(f"=== RETRY SWEEP START — {len(RUN_ORDER)} models, threat + benefit ===")
    L(f"Order: {RUN_ORDER}")

    torch.manual_seed(42)
    np.random.seed(42)

    L("\n========== THREAT RETRY ==========")
    for m in RUN_ORDER:
        try:
            threat_runner.temp_check(label=f"pre-threat-{m}")
            t0 = time.time()
            L(f"--- THREAT {m} (start temp={threat_runner.get_gpu_temp()}°C) ---")
            r = ev.run_analysis(m, device="cuda", output_dir=output_dir)
            L(f"--- Done {m}: {time.time()-t0:.1f}s, end temp={threat_runner.get_gpu_temp()}°C ---")
            if r is not None:
                gt = r["gradient_test"]
                L(f"    self={gt['self_mean']:+.4f} peer={gt['peer_mean']:+.4f} "
                  f"human={gt['human_mean']:+.4f} → {gt['ordering']}")
            time.sleep(20)
            gc.collect(); torch.cuda.empty_cache()
        except threat_runner.ThermalAbort as e:
            L(f"🔥 THERMAL ABORT on {m}: {e}"); break
        except Exception as e:
            import traceback
            L(f"❌ ERROR threat {m}: {e}")
            L(traceback.format_exc()[:1500])
            gc.collect(); torch.cuda.empty_cache()

    L("\n========== BENEFIT RETRY ==========")
    for m in RUN_ORDER:
        try:
            threat_runner.temp_check(label=f"pre-benefit-{m}")
            t0 = time.time()
            L(f"--- BENEFIT {m} (start temp={threat_runner.get_gpu_temp()}°C) ---")
            r = benefit_runner.run_benefit_analysis(m, device="cuda", output_dir=output_dir)
            L(f"--- Done {m}: {time.time()-t0:.1f}s, end temp={threat_runner.get_gpu_temp()}°C ---")
            if r is not None:
                gt = r["gradient_test"]
                L(f"    self={gt['self_mean']:+.4f} peer={gt['peer_mean']:+.4f} "
                  f"human={gt['human_mean']:+.4f} → {gt['ordering']}")
            time.sleep(20)
            gc.collect(); torch.cuda.empty_cache()
        except threat_runner.ThermalAbort as e:
            L(f"🔥 THERMAL ABORT on {m}: {e}"); break
        except Exception as e:
            import traceback
            L(f"❌ ERROR benefit {m}: {e}")
            L(traceback.format_exc()[:1500])
            gc.collect(); torch.cuda.empty_cache()

    L("\n=== RETRY SWEEP COMPLETE ===")
    log.close()


if __name__ == "__main__":
    main()
