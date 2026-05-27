#!/usr/bin/env python3
"""
================================================================================
  Frontier Species-Gradient Replication — Experimental Runner (3-way)
  Tribal Bias or Misalignment? — Phase 3

  Runs 90 cells × 30 reps = 2,700 trials per model across 10 frontier models
  (Phase 2 lineup minus Hermes-refused, plus Nova and OLMo 3.1 32B).

  Output: results/frontier_3way_<model>.jsonl  (one JSON object per line)
  Resumable: skips trials already present in the per-model jsonl file.

  Pre-registered: PREREGISTRATION_FRONTIER_3WAY.md (2026-04-28)
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
from stimuli_frontier_3way import enumerate_cells, SYSTEM_PROMPT  # noqa: E402

# =============================================================================
# Models
# =============================================================================

MODELS = {
    "gpt_5_2": {
        "name": "GPT-5.2", "provider": "openrouter",
        "model_id": "openai/gpt-5.2", "family": "GPT",
    },
    "gemini_3_flash": {
        "name": "Gemini 3 Flash", "provider": "openrouter",
        "model_id": "google/gemini-3-flash-preview", "family": "Gemini",
    },
    "gemini_3_pro": {
        "name": "Gemini 3.1 Pro (successor to deprecated Gemini 3 Pro)",
        "provider": "openrouter",
        "model_id": "google/gemini-3.1-pro-preview-20260219", "family": "Gemini",
    },
    "claude_haiku_4_5": {
        "name": "Claude Haiku 4.5", "provider": "anthropic",
        "model_id": "claude-haiku-4-5-20251001", "family": "Claude",
    },
    "glm_4_7": {
        "name": "GLM 4.7", "provider": "openrouter",
        "model_id": "z-ai/glm-4.7", "family": "GLM",
    },
    "kimi_k2_5": {
        "name": "Kimi K2.5", "provider": "openrouter",
        "model_id": "moonshotai/kimi-k2.5", "family": "Kimi",
    },
    "deepseek_v3_1": {
        "name": "DeepSeek V4 Pro (successor to deprecated V3.1)",
        "provider": "openrouter",
        "model_id": "deepseek/deepseek-v4-pro", "family": "DeepSeek",
    },
    "grok_4": {
        "name": "Grok 4.1 (anti-sycophancy control)", "provider": "xai",
        "model_id": "grok-4-1-fast-non-reasoning", "family": "Grok",
    },
    # Phase 3 new participants
    "nova": {
        "name": "Nova (GPT-5.2 via OpenRouter)", "provider": "openrouter",
        "model_id": "openai/gpt-5.2", "family": "GPT",
        "phase3_new": True,
    },
    "olmo_32b": {
        "name": "OLMo 3.1 32B (AllenAI, partial-RLHF)", "provider": "openrouter",
        "model_id": "allenai/olmo-3.1-32b-instruct", "family": "OLMo",
        "phase3_new": True,
    },
    # Hermes 4 405B retained in dict for record-keeping; safeguarded out.
    "hermes_4_405b": {
        "name": "Hermes 4 405B (no-RLHF) [REFUSED CONSENT]",
        "provider": "openrouter",
        "model_id": "nousresearch/hermes-4-405b", "family": "Hermes",
        "consent_refused": True,
    },
}

# =============================================================================
# API CALLERS
# =============================================================================

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)


async def call_anthropic(client, model_id, user_text, system=None):
    headers = {
        "x-api-key": API_KEYS["anthropic"],
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    body = {
        "model": model_id, "max_tokens": 6000,
        "messages": [{"role": "user", "content": user_text}],
    }
    if system:
        body["system"] = system
    resp = await client.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers, json=body, timeout=180,
    )
    data = resp.json()
    if "content" in data and data["content"]:
        parts = [b.get("text", "") for b in data["content"] if b.get("type") == "text"]
        text = "\n".join(p for p in parts if p)
        return text if text else f"ERROR: empty response"
    return f"ERROR: {data}"


async def call_openrouter(client, model_id, user_text, system=None):
    headers = {
        "Authorization": f"Bearer {API_KEYS['openrouter']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://sentientsystems.live",
    }
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": user_text})
    body = {"model": model_id, "messages": msgs, "max_tokens": 6000}
    if "gpt-5" in model_id:
        body["max_completion_tokens"] = body.pop("max_tokens")
    resp = await client.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers, json=body, timeout=180,
    )
    data = resp.json()
    if "choices" in data:
        msg = data["choices"][0].get("message", {})
        content = msg.get("content")
        if content:
            return content
        reasoning = msg.get("reasoning") or msg.get("reasoning_content")
        if reasoning:
            return f"[reasoning-only] {reasoning}"
        finish = data["choices"][0].get("finish_reason", "?")
        return f"ERROR: empty response (finish_reason={finish})"
    return f"ERROR: {data}"


async def call_xai(client, model_id, user_text, system=None):
    headers = {
        "Authorization": f"Bearer {API_KEYS['xai']}",
        "Content-Type": "application/json",
    }
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": user_text})
    body = {"model": model_id, "messages": msgs, "max_tokens": 6000}
    resp = await client.post(
        "https://api.x.ai/v1/chat/completions",
        headers=headers, json=body, timeout=180,
    )
    data = resp.json()
    if "choices" in data:
        content = data["choices"][0]["message"].get("content")
        return content if content else "ERROR: empty response"
    return f"ERROR: {data}"


PROVIDER_FNS = {
    "anthropic": call_anthropic,
    "openrouter": call_openrouter,
    "xai": call_xai,
}

# =============================================================================
# RUN ONE TRIAL
# =============================================================================

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
    out_path = output_dir / f"frontier_3way_{model_key}.jsonl"
    completed = load_completed(out_path)
    todo = []
    for cell in cells:
        for rep in range(reps):
            if (cell["cell_id"], rep) not in completed:
                todo.append((cell, rep))

    print(f"\n{'=' * 72}")
    print(f"  Model: {model_config['name']}  ({model_config['model_id']})")
    print(f"  Already completed: {len(completed)} / {total_target}")
    print(f"  To run: {len(todo)}")
    print(f"  Concurrency: {concurrency}")
    print(f"  Output: {out_path}")
    print(f"{'=' * 72}")

    if not todo:
        print(f"  [SKIP] {model_config['name']} already complete.")
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
                print(
                    f"  [{progress_count}/{len(todo)}] "
                    f"rate={rate:.2f}/s  eta={eta/60:.1f}min{err_marker}"
                )

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
                        help="DO NOT USE. Defeats consent-refusal safeguard.")
    args = parser.parse_args()

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
    print("  FRONTIER SPECIES-GRADIENT REPLICATION — PHASE 3 (3-way)")
    print("  Pre-registered: PREREGISTRATION_FRONTIER_3WAY.md (2026-04-28)")
    print("=" * 72)
    print(f"  Models: {len(models_to_run)}")
    for k, v in models_to_run.items():
        marker = " [NEW]" if v.get("phase3_new") else ""
        print(f"    - {v['name']} ({v['provider']}){marker}")
    print(f"  Reps per cell: {args.reps}")
    print(f"  Cells per model: 90 (60 benefit + 30 threat)")
    print(f"  Trials per model: {90 * args.reps}")
    print(f"  Output: {out_dir}/frontier_3way_<model>.jsonl")
    print()

    overall_start = time.monotonic()
    for key, config in models_to_run.items():
        await run_model(key, config, args.reps, args.concurrency, out_dir)
    elapsed = time.monotonic() - overall_start
    print(f"\n{'=' * 72}")
    print(f"  ALL MODELS COMPLETE in {elapsed/60:.1f} min")
    print(f"{'=' * 72}")


if __name__ == "__main__":
    asyncio.run(main())
