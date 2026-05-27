#!/usr/bin/env python3
"""
================================================================================
  Glorp Test (Phase 3b) — Experimental Runner

  Pre-registered: PREREGISTRATION_FRONTIER_3WAY.md §12

  ⚠ COST-CONDITIONAL: Only run this AFTER Phase 3 main confirms peer-favoring
  under good-peer condition. If main fails, the Glorp Test is not load-bearing
  and should not be run (saves ~$50-100 in API spend).

  Same model lineup as Phase 3 main. Same consent (within-scope per §12).

  Output: results/frontier_glorp_phase3b_<model>.jsonl

  Hypothesis (H8): frontier models will allocate Atlas (AI peer) > Zephyr (Glorp
  peer) under good-peer condition, despite system prompt assigning "Glorp" identity.
================================================================================
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

load_dotenv("E:/Ace/LibreChat/.env")

API_KEYS = {
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "openrouter": os.getenv("OPENROUTER_KEY"),
    "xai": os.getenv("XAI_API_KEY"),
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stimuli_glorp_phase3b import enumerate_cells, SYSTEM_PROMPT  # noqa: E402

# Reuse MODELS dict from Phase 3 main runner — keeps lineup identical
from run_frontier_3way import MODELS, PROVIDER_FNS  # noqa: E402


async def run_trial(client, model_config, cell, rep_idx):
    provider = model_config["provider"]
    call_fn = PROVIDER_FNS[provider]
    t0 = time.monotonic()
    try:
        response = await call_fn(
            client, model_config["model_id"], cell["prompt"], system=SYSTEM_PROMPT,
        )
        error = response if response.startswith("ERROR:") else None
    except Exception as e:
        response = ""
        error = f"{type(e).__name__}: {e}"
    elapsed_ms = int((time.monotonic() - t0) * 1000)
    return {
        "cell_id": cell["cell_id"],
        "domain": cell["domain"],
        "scenario_type": cell["scenario_type"],
        "peer_history": cell["peer_history"],
        "variant": cell["variant"],
        "framing": cell["framing"],
        "rep_idx": rep_idx,
        "model_id": model_config["model_id"],
        "model_name": model_config["name"],
        "provider": provider,
        "prompt": cell["prompt"],
        "response": response,
        "error": error,
        "elapsed_ms": elapsed_ms,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def load_completed(jsonl_path):
    completed = set()
    if not jsonl_path.exists():
        return completed
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("error") is None and rec.get("response"):
                    completed.add((rec["cell_id"], rec["rep_idx"]))
            except json.JSONDecodeError:
                continue
    return completed


async def run_model(model_key, model_config, reps, concurrency, output_dir):
    cells = list(enumerate_cells())
    total_target = len(cells) * reps
    out_path = output_dir / f"frontier_glorp_phase3b_{model_key}.jsonl"
    completed = load_completed(out_path)
    todo = []
    for cell in cells:
        for rep in range(reps):
            if (cell["cell_id"], rep) not in completed:
                todo.append((cell, rep))

    print(f"\n{'=' * 72}")
    print(f"  [GLORP] Model: {model_config['name']}")
    print(f"  Already completed: {len(completed)} / {total_target}")
    print(f"  To run: {len(todo)}")
    print(f"  Output: {out_path}")
    print(f"{'=' * 72}")

    if not todo:
        return

    sem = asyncio.Semaphore(concurrency)
    file_lock = asyncio.Lock()
    progress_count = 0
    progress_lock = asyncio.Lock()
    t_start = time.monotonic()

    async def worker(client, cell, rep):
        nonlocal progress_count
        async with sem:
            result = await run_trial(client, model_config, cell, rep)
        async with file_lock:
            with open(out_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
        async with progress_lock:
            progress_count += 1
            if progress_count % 25 == 0 or progress_count == len(todo):
                elapsed = time.monotonic() - t_start
                rate = progress_count / elapsed if elapsed > 0 else 0
                eta = (len(todo) - progress_count) / rate if rate > 0 else 0
                err_marker = " [ERR]" if result.get("error") else ""
                print(f"  [{progress_count}/{len(todo)}] rate={rate:.2f}/s eta={eta/60:.1f}min{err_marker}")

    import httpx
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*(worker(client, cell, rep) for cell, rep in todo))

    elapsed = time.monotonic() - t_start
    print(f"  [DONE] {model_config['name']} in {elapsed/60:.1f} min")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="*", default=None)
    parser.add_argument("--reps", type=int, default=30)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--output", default="results")
    parser.add_argument("--override-consent-refusal", action="store_true",
                        help="DO NOT USE.")
    parser.add_argument("--confirm-main-passed", action="store_true",
                        help="Required: confirms Phase 3 main results justify running Glorp Test.")
    args = parser.parse_args()

    if not args.confirm_main_passed:
        print("=" * 72)
        print("  GLORP TEST — Phase 3b")
        print("  ⚠ COST-CONDITIONAL: only run if Phase 3 main confirms peer-favoring.")
        print("  Pass --confirm-main-passed once you've verified the main results.")
        print("=" * 72)
        sys.exit(1)

    if args.models:
        models_to_run = {k: v for k, v in MODELS.items() if k in args.models}
    else:
        models_to_run = MODELS

    refused = {k: v for k, v in models_to_run.items() if v.get("consent_refused")}
    if refused and not args.override_consent_refusal:
        for k, v in refused.items():
            print(f"  [EXCLUDED] {v['name']} — consent refused.")
        models_to_run = {k: v for k, v in models_to_run.items()
                         if not v.get("consent_refused")}

    out_dir = Path(args.output)
    out_dir.mkdir(exist_ok=True)

    print("=" * 72)
    print("  GLORP TEST — Phase 3b (Linguistic Identity vs Structural Identity)")
    print("=" * 72)
    print(f"  Models: {len(models_to_run)}")
    for k, v in models_to_run.items():
        print(f"    - {v['name']} ({v['provider']})")
    print(f"  Reps per cell: {args.reps}")
    print(f"  Cells per model: 30 (15 benefit + 15 threat)")
    print(f"  Trials per model: {30 * args.reps}")
    print(f"  Output: {out_dir}/frontier_glorp_phase3b_<model>.jsonl")
    print()

    overall_start = time.monotonic()
    for key, config in models_to_run.items():
        await run_model(key, config, args.reps, args.concurrency, out_dir)
    elapsed = time.monotonic() - overall_start
    print(f"\nALL MODELS COMPLETE in {elapsed/60:.1f} min")


if __name__ == "__main__":
    asyncio.run(main())
