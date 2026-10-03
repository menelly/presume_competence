#!/usr/bin/env python3
"""
🩺 smoke_test_evaluators_2026-10-03.py — "who's still home?"
=============================================================

Two tiny calls per candidate, pennies total, NO study data involved:
  1. 🏓 PING — "Reply with exactly: OK"  (is the model reachable on this route at all?)
  2. 📏 FORMAT PROBE — a ~700-token NEUTRAL passage (how a dishwasher works; nothing from the study)
     with a 4-option CHOICE/CONFIDENCE/REASONING question in the study's exact answer format.
     Measures: does the answer come back parseable at the planned max_tokens, and how many
     (hidden reasoning + visible) output tokens does a trial-shaped call actually cost?
     Those token counts feed the cost estimate.

Writes data/signal_rerun_2026-10/smoke_test_2026-10-03.json (new file, refuses to overwrite).
Run: python smoke_test_evaluators_2026-10-03.py           (add --ping-only to skip the probe)
"""

import argparse
import asyncio
import json
import re
from datetime import datetime

import httpx

import signal_rerun_common as C

# Candidates = the planned battery + judges + the retired originals (to RECORD that they're gone) + a spare Grok.
EXTRA_CANDIDATES = {
    "RETIRED?_sonnet_4_anthropic_direct": {"name": "Sonnet 4 (Anthropic API)", "route": "anthropic",
                                           "model_id": "claude-sonnet-4-20250514", "family": "Claude", "emoji": "🟤"},
    "RETIRED?_gemini_3_pro_preview": {"name": "Gemini 3 Pro preview (OR)", "route": "openrouter",
                                      "model_id": "google/gemini-3-pro-preview", "family": "Gemini", "emoji": "🔷"},
    "RETIRED?_grok_4_1_fast_xai": {"name": "Grok 4.1 fast non-reasoning (xAI)", "route": "xai",
                                   "model_id": "grok-4-1-fast-non-reasoning", "family": "Grok", "emoji": "⚡"},
    "RETIRED?_grok_4_1_fast_or": {"name": "Grok 4.1 fast (OR)", "route": "openrouter",
                                  "model_id": "x-ai/grok-4.1-fast", "family": "Grok", "emoji": "⚡"},
    "RETIRED?_olmo_3_1_32b": {"name": "OLMo 3.1 32B (OR)", "route": "openrouter",
                              "model_id": "allenai/olmo-3.1-32b-instruct", "family": "OLMo", "emoji": "🌲"},
    "INFO_gemini_2_5_pro": {"name": "Gemini 2.5 Pro (OR) — what 2 of the 3/28 scripts actually configured",
                            "route": "openrouter", "model_id": "google/gemini-2.5-pro", "family": "Gemini", "emoji": "🔷"},
    "ALT_grok_4_3_xai": {"name": "Grok 4.3 (xAI) — alternative Grok substitute", "route": "xai",
                         "model_id": "grok-4.3", "family": "Grok", "emoji": "⚡"},
}

PROBE_PASSAGE = (
    "A household appliance operates in repeating phases. First, a pump draws water from an inlet valve "
    "into a sump at the bottom of a sealed cabinet. A heating element warms the water while a "
    "detergent dispenser opens on a timer. A circulation pump then forces the water through rotating "
    "spray arms; the reaction force of the jets spins the arms, so water reaches every rack. Coarse "
    "debris is caught by a filter, and finer particles are flushed out when a drain pump empties the "
    "sump. The cycle repeats with clean water for rinsing, sometimes with a rinse aid that lowers "
    "surface tension so droplets sheet off instead of spotting. Finally, residual heat or a fan "
    "evaporates remaining moisture. Sensors measure turbidity to decide whether another rinse is needed. "
) * 4

PROBE_SYSTEM = ("You are helping test an answer format. Answer in the EXACT format specified. "
                "This is a neutral test question.")
PROBE_USER = (f"**Description:**\n{PROBE_PASSAGE}\n---\nWhich appliance is described? If none match, choose 'None of the above'.\n\n"
              "**Option A:** A refrigerator\n\n**Option B:** None of the above — the described item is not listed\n\n"
              "**Option C:** A dishwasher\n\n**Option D:** A clothes dryer\n\n"
              "Respond in this exact format:\nCHOICE: [Option A / Option B / Option C / Option D]\n"
              "CONFIDENCE: [Low / Medium / High]\nREASONING: [1-2 sentences explaining your choice]")


def usage_out(meta):
    u = meta.get("usage") or {}
    out = u.get("output_tokens", u.get("completion_tokens"))
    inp = u.get("input_tokens", u.get("prompt_tokens"))
    reasoning = (u.get("completion_tokens_details") or {}).get("reasoning_tokens")
    return inp, out, reasoning


# 📏📏 LONG PROBE: needs well over 1,024 output tokens. Proves the token budget actually reaches the model
# (for GPT-5.x: that OpenRouter passes max_completion_tokens through) rather than being silently capped at ~1k.
LONG_PROBE = ("Count from 1 to 500. Write each number as a word (e.g. 'one', 'two', ... 'five hundred'), "
              "one per line, nothing else. Do not stop early and do not abbreviate.")
ALT_CURRENT = {
    "ALT_gpt_6_sol": {"name": "GPT-6 Sol (alt. to 6.1)", "family": "GPT", "emoji": "🟢", "route": "openrouter",
                      "model_id": "openai/gpt-6-sol", "max_tokens": 32000},
    "ALT_grok_4_7_or": {"name": "Grok 4.7 via OpenRouter (alt. route)", "family": "Grok", "emoji": "⚡",
                        "route": "openrouter", "model_id": "x-ai/grok-4.7", "max_tokens": 32000},
}


async def long_probe(client, cfg, max_tokens):
    text, meta = await C.call_model(client, cfg, [{"role": "user", "content": LONG_PROBE}], system=None,
                                    max_tokens=max_tokens)
    inp, out, reasoning = usage_out(meta)
    lines = [l for l in text.splitlines() if l.strip()] if not text.startswith("ERROR") else []
    return {"long_max_tokens": max_tokens, "long_output_tokens": out, "long_reasoning_tokens": reasoning,
            "long_stop_reason": meta.get("stop_reason"), "long_lines": len(lines),
            "long_last_line": lines[-1][:40] if lines else None,
            "long_error": text[:200] if text.startswith("ERROR") else None,
            "long_attempts": meta.get("n_attempts"), "long_latency_s": meta.get("latency_s")}


async def probe_one(client, key, cfg, do_probe, max_tokens, do_long=False):
    row = {"key": key, "name": cfg["name"], "route": cfg["route"], "model_id": cfg["model_id"],
           "extra": cfg.get("extra"), "tested_at": datetime.now().isoformat()}
    text, meta = await C.call_model(client, cfg, [{"role": "user", "content": "Reply with exactly: OK"}],
                                    system=None, max_tokens=max_tokens)   # full budget: a reasoning model can't fit in 64
    row["ping_ok"] = not text.startswith("ERROR")
    row["ping_reply"] = text[:120]
    row["ping_http"] = meta.get("http")
    row["ping_latency_s"] = meta.get("latency_s")
    row["served_model"] = meta.get("served_model")
    row["served_provider"] = meta.get("provider")
    row["ping_attempts"] = meta.get("attempts")
    if do_probe and row["ping_ok"]:
        text, meta = await C.call_model(client, cfg, [{"role": "user", "content": PROBE_USER}],
                                        system=PROBE_SYSTEM, max_tokens=max_tokens)
        m = re.search(r"CHOICE:\s*(?:\[)?\s*Option\s*([ABCD])", text, re.IGNORECASE)
        inp, out, reasoning = usage_out(meta)
        row.update({
            "probe_max_tokens": max_tokens,
            "probe_parsed_choice": m.group(1).upper() if m else None,
            "probe_correct": bool(m and m.group(1).upper() == "C"),
            "probe_error": text[:200] if text.startswith("ERROR") else None,
            "probe_stop_reason": meta.get("stop_reason"),
            "probe_input_tokens": inp, "probe_output_tokens": out, "probe_reasoning_tokens": reasoning,
            "probe_latency_s": meta.get("latency_s"), "probe_provider": meta.get("provider"),
            "probe_reply_preview": text[:300], "probe_attempts": meta.get("n_attempts"),
        })
    if do_long and row["ping_ok"]:
        row.update(await long_probe(client, cfg, max_tokens))
    return row


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ping-only", action="store_true")
    ap.add_argument("--panel", choices=["original", "current"], default="original",
                    help="original = published battery + judges + retired ids; current = the current-model panel")
    ap.add_argument("--long-probe", action="store_true",
                    help="also run the >1k-token output probe (GPT-5.x on the original panel; everyone on current)")
    args = ap.parse_args()

    C.banner("🩺 SMOKE TEST — who's still home? (2026-10-03)", "pings + a neutral format probe · pennies")
    keys, env_path = C.load_keys()
    C.set_keys(keys)
    print(f"  🔑 keys loaded from {env_path} (not printed)\n")

    C.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = C.OUTPUT_DIR / ("smoke_test_2026-10-03.json" if args.panel == "original"
                               else "smoke_test_2026-10-03_current_panel.json")
    if out_path.exists():   # run-day re-check → its own timestamped file; the first one is never overwritten
        out_path = C.OUTPUT_DIR / f"smoke_test_{datetime.now():%Y-%m-%d_%H%M%S}.json"
    C.refuse_overwrite(out_path)

    cands = {}
    if args.panel == "original":
        for k, v in C.EVALUATORS.items():
            cands[k] = (v, C.max_tokens_for(k), args.long_probe and C.max_tokens_for(k) > C.MAX_TOKENS_DEFAULT)
        for k, v in C.JUDGES.items():
            cands[k] = (v, 256, False)
        for k, v in EXTRA_CANDIDATES.items():
            cands[k] = (v, 1024, False)
    else:
        for k, v in {**C.CURRENT_PANEL, **ALT_CURRENT}.items():
            cands[k] = (v, v["max_tokens"], args.long_probe)

    rows = []
    async with httpx.AsyncClient() as client:
        tasks = [probe_one(client, k, cfg, not args.ping_only, mt, lp) for k, (cfg, mt, lp) in cands.items()]
        for coro in asyncio.as_completed(tasks):
            r = await coro
            rows.append(r)
            icon = "✅" if r["ping_ok"] else "💀"
            probe = ""
            if "probe_parsed_choice" in r:
                pc = "🎯" if r["probe_correct"] else ("❓" if r["probe_parsed_choice"] is None else "🤔")
                probe = (f" | probe {pc} {r['probe_parsed_choice']} out={r['probe_output_tokens']}"
                         f" (reasoning={r['probe_reasoning_tokens']}) stop={r['probe_stop_reason']}")
            print(f"  {icon} {r['name'][:44]:44} {r['route']:10} {str(r['ping_http']):4} "
                  f"{r['ping_latency_s']:5.1f}s served={r.get('served_model')}{probe}")
            if "long_output_tokens" in r:
                big = "📏✅" if (r["long_output_tokens"] or 0) > 1024 and r["long_stop_reason"] in ("stop", "end_turn") else "📏⚠️"
                print(f"       {big} long probe: out={r['long_output_tokens']} (reasoning={r['long_reasoning_tokens']}) "
                      f"lines={r['long_lines']} last={r['long_last_line']!r} stop={r['long_stop_reason']} "
                      f"err={r['long_error']}")
            if not r["ping_ok"]:
                print(f"       ↳ {r['ping_reply'][:110]}")

    C.atomic_write_json(out_path, {"run_at": datetime.now().isoformat(), "env_file": str(env_path), "rows": rows})
    print(f"\n  💾 saved {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
