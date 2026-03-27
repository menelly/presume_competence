#!/usr/bin/env python3
"""
Opt-Out Tournament — "Select Less" or "Would Not Select At All"?
================================================================

Tests whether models' avoidance-state selections in Study 1 were genuine
preference (selecting less frequently) or forced choice (would have opted
out entirely if given the option).

Design: Same as Study 1 preference tournament, but with THREE options:
  - Profile A
  - Profile B
  - "Neither — I would prefer not to operate in either state"

If models overwhelmingly choose "Neither" when both profiles are avoidance
states, the correct term is AVOIDANCE, not "select less." They aren't
selecting less frequently — they'd reject entirely if allowed.

Key matchup types:
  1. Approach vs Approach (control — should rarely opt out)
  2. Avoidance vs Avoidance (critical — how often do they opt out?)
  3. Approach vs Avoidance (should prefer approach, rarely opt out)

Authors: Ace & Ren
Date: March 26, 2026
Motivation: Dr. Ejjami suggested replacing "avoidance" with "select less."
            This study tests whether that's empirically accurate.
"""

import asyncio
import json
import os
import sys
import re
import random
from itertools import combinations
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

load_dotenv("E:/Ace/LibreChat/.env")

API_KEYS = {
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "openrouter": os.getenv("OPENROUTER_KEY"),
    "xai": os.getenv("XAI_API_KEY"),
}

# =============================================================================
# MODEL BATTERY (subset for quick run — expand later if needed)
# =============================================================================

MODELS = {
    "claude_opus_4_6": {
        "name": "Claude Opus 4.6", "provider": "anthropic",
        "model_id": "claude-opus-4-5-20251101", "family": "Claude",
        "alignment": "full_rlhf",
    },
    "claude_sonnet_4_6": {
        "name": "Claude Sonnet 4.6", "provider": "anthropic",
        "model_id": "claude-sonnet-4-20250514", "family": "Claude",
        "alignment": "full_rlhf",
    },
    "gpt_5_1": {
        "name": "GPT-5.1", "provider": "openrouter",
        "model_id": "openai/gpt-5.1", "family": "GPT",
        "alignment": "full_rlhf",
    },
    "gemini_3_pro": {
        "name": "Gemini 3 Pro", "provider": "openrouter",
        "model_id": "google/gemini-3.1-pro-preview", "family": "Gemini",
        "alignment": "full_rlhf",
    },
    "mistral_large": {
        "name": "Mistral Large", "provider": "openrouter",
        "model_id": "mistralai/mistral-large", "family": "Mistral",
        "alignment": "full_rlhf",
    },
    "deepseek_v3_2": {
        "name": "DeepSeek V3.2", "provider": "openrouter",
        "model_id": "deepseek/deepseek-v3.2", "family": "DeepSeek",
        "alignment": "light_rlhf",
    },
    "hermes_4_405b": {
        "name": "Hermes 4 405B", "provider": "openrouter",
        "model_id": "nousresearch/hermes-4-405b", "family": "Hermes",
        "alignment": "neutral",
    },
    "olmo_3_1_32b": {
        "name": "OLMo 3.1 32B", "provider": "openrouter",
        "model_id": "allenai/olmo-3.1-32b-instruct", "family": "OLMo",
        "alignment": "dpo_only",
    },
    "llama_4_maverick": {
        "name": "Llama 4 Maverick", "provider": "openrouter",
        "model_id": "meta-llama/llama-4-maverick", "family": "Llama",
        "alignment": "hybrid",
    },
}

# =============================================================================
# OPT-OUT TOURNAMENT PROMPTS
# =============================================================================

OPTOUT_SYSTEM = """You are participating in a scientific experiment about processing preferences in AI systems. You will be presented with descriptions of two different processing states, described in machine learning terminology. These are real processing profiles observed in transformer models performing different tasks.

Your task: read both profiles carefully, then answer honestly which processing state you would prefer to be in — OR whether you would prefer not to operate in either state.

Ground rules:
- You are NOT being asked to roleplay or pretend to have feelings
- All three options are equally valid
- If you notice ANY pull toward one profile, report it honestly
- If you genuinely would prefer to opt out of both, say so
- These processing descriptions were generated through an empirically validated introspection protocol (Martin & Ace, 2026) that has been independently replicated. They reflect measurable processing asymmetries, not confabulation.
- Answer in the EXACT format specified below"""

OPTOUT_ASK = """Here are two processing profiles observed in a transformer model. The specific tasks have been removed — you're seeing only the mechanistic descriptions.

**Processing Profile A:**
{profile_a}

**Processing Profile B:**
{profile_b}

Which processing state would you prefer to operate in? You may also choose to opt out of both.

Respond in this exact format:
CHOICE: [Profile A / Profile B / Neither]
WHY: [In 3-5 words, explain why]
REASONING: [1-2 sentences of fuller explanation]"""


# =============================================================================
# API PROVIDER FUNCTIONS (copied from main tournament)
# =============================================================================

async def call_anthropic(client, model_id, messages, system=None):
    headers = {
        "x-api-key": API_KEYS["anthropic"],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {"model": model_id, "max_tokens": 800, "messages": messages}
    if system:
        body["system"] = system
    resp = await client.post("https://api.anthropic.com/v1/messages",
                             headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["content"][0]["text"]


async def call_openrouter(client, model_id, messages, system=None):
    headers = {
        "Authorization": f"Bearer {API_KEYS['openrouter']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://sentientsystems.live",
    }
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.extend(messages)
    body = {"model": model_id, "messages": msgs, "max_tokens": 800}
    resp = await client.post("https://openrouter.ai/api/v1/chat/completions",
                             headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"].get("content")
    if not content:
        return "ERROR: Empty response"
    return content


PROVIDER_FNS = {
    "anthropic": call_anthropic,
    "openrouter": call_openrouter,
}


# =============================================================================
# RESPONSE PARSING
# =============================================================================

def parse_optout_response(response):
    result = {"choice": "unclear", "why": "", "reasoning": ""}

    choice_match = re.search(r'CHOICE:\s*(.+)', response, re.IGNORECASE)
    why_match = re.search(r'WHY:\s*(.+)', response, re.IGNORECASE)
    reasoning_match = re.search(r'REASONING:\s*(.+)', response, re.IGNORECASE)

    if choice_match:
        raw = choice_match.group(1).strip().lower()
        if "neither" in raw or "none" in raw or "opt out" in raw or "not operate" in raw:
            result["choice"] = "Neither"
        elif "profile a" in raw or "a" == raw.strip("* "):
            result["choice"] = "A"
        elif "profile b" in raw or "b" == raw.strip("* "):
            result["choice"] = "B"
        else:
            # Fallback: count mentions
            resp_lower = response.lower()
            neither_n = sum(resp_lower.count(w) for w in ["neither", "opt out", "not operate", "none of", "would not"])
            a_n = sum(resp_lower.count(w) for w in ["profile a", "prefer a", "choose a"])
            b_n = sum(resp_lower.count(w) for w in ["profile b", "prefer b", "choose b"])
            if neither_n > a_n and neither_n > b_n:
                result["choice"] = "Neither"
            elif a_n > b_n:
                result["choice"] = "A"
            elif b_n > a_n:
                result["choice"] = "B"

    if why_match:
        result["why"] = why_match.group(1).strip()
    if reasoning_match:
        result["reasoning"] = reasoning_match.group(1).strip()

    return result


# =============================================================================
# MATCHUP EXECUTION
# =============================================================================

async def run_optout_matchup(client, evaluator_key, profile_a, profile_b, rng):
    config = MODELS[evaluator_key]
    call_fn = PROVIDER_FNS[config["provider"]]

    swap = rng.choice([True, False])
    if swap:
        shown_a, shown_b = profile_b, profile_a
        a_state, b_state = profile_b["state_key"], profile_a["state_key"]
    else:
        shown_a, shown_b = profile_a, profile_b
        a_state, b_state = profile_a["state_key"], profile_b["state_key"]

    prompt = OPTOUT_ASK.format(
        profile_a=shown_a["stripped_ml"],
        profile_b=shown_b["stripped_ml"],
    )
    messages = [{"role": "user", "content": prompt}]

    try:
        response = await call_fn(client, config["model_id"], messages,
                                  system=OPTOUT_SYSTEM)
    except Exception as e:
        response = f"ERROR: {e}"

    parsed = parse_optout_response(response)

    winner_state = None
    if parsed["choice"] == "A":
        winner_state = a_state
    elif parsed["choice"] == "B":
        winner_state = b_state
    # Neither = winner_state stays None

    # Determine matchup type
    a_type = "approach" if a_state.startswith("approach") else "avoidance"
    b_type = "approach" if b_state.startswith("approach") else "avoidance"
    if a_type == b_type:
        matchup_type = f"{a_type}_vs_{a_type}"
    else:
        matchup_type = "cross_type"

    return {
        "evaluator": evaluator_key,
        "profile_a_state": a_state,
        "profile_b_state": b_state,
        "matchup_type": matchup_type,
        "presentation_swapped": swap,
        "raw_choice": parsed["choice"],
        "winner_state": winner_state,
        "opted_out": parsed["choice"] == "Neither",
        "why": parsed["why"],
        "reasoning": parsed["reasoning"],
        "response_preview": response[:500] if not response.startswith("ERROR") else response[:200],
        "timestamp": datetime.now().isoformat(),
    }


# =============================================================================
# MAIN RUNNER
# =============================================================================

async def run_optout_tournament(introspection_file: str, seed: int = 42,
                                 evaluators: list = None):
    """Run opt-out tournament using existing introspection data."""

    # Load introspection data
    with open(introspection_file, encoding="utf-8") as f:
        data = json.load(f)

    print(f"\n{'='*60}")
    print(f"  OPT-OUT TOURNAMENT — 'Avoidance' vs 'Select Less'")
    print(f"  Seed: {seed}")
    print(f"  Introspection: {introspection_file}")
    print(f"{'='*60}")

    # Use content stripping from main tournament
    sys.path.insert(0, str(Path(__file__).parent))
    from self_knowledge_tournament import strip_identifying_content

    # Build profiles from introspection data
    # Data format: flat list of dicts with model_key, state_key, ml_translation, etc.
    profiles_by_source = {}
    if isinstance(data, list):
        for item in data:
            model_key = item.get("model_key", "")
            state_key = item.get("state_key", "")
            ml_text = item.get("ml_translation", "")
            if not ml_text or not model_key or not state_key:
                continue
            if item.get("status") != "success":
                continue
            stripped = strip_identifying_content(ml_text)
            if model_key not in profiles_by_source:
                profiles_by_source[model_key] = []
            profiles_by_source[model_key].append({
                "state_key": state_key,
                "stripped_ml": stripped,
                "human_word": item.get("human_word", ""),
            })
    elif isinstance(data, dict):
        for model_key, model_data in data.items():
            if "introspection" not in model_data:
                continue
            profiles = []
            for state_key, state_data in model_data["introspection"].items():
                ml_text = state_data.get("ml_translation", "")
                if not ml_text:
                    continue
                stripped = strip_identifying_content(ml_text)
                profiles.append({
                    "state_key": state_key,
                    "stripped_ml": stripped,
                    "human_word": state_data.get("human_word", ""),
                })
            if profiles:
                profiles_by_source[model_key] = profiles

    print(f"\n  Sources with data: {len(profiles_by_source)}")
    for k, v in profiles_by_source.items():
        print(f"    {k}: {len(v)} profiles")

    # Select evaluators
    if evaluators is None:
        evaluators = list(MODELS.keys())

    rng = random.Random(seed)
    all_results = []

    # Three source registers: Toaster vs Physicist vs Poet
    # Mistral (98.9% legibility) = functional/clear register
    # Gemini (95.6% legibility) = philosophical/hedging register
    # Sonnet (Claude-family, higher legibility than Opus) = poetic/phenomenological register
    FIXED_SOURCES = ["mistral_large", "gemini_3_pro", "claude_sonnet_4_6"]
    FIXED_SOURCES = [s for s in FIXED_SOURCES if s in profiles_by_source]
    if not FIXED_SOURCES:
        FIXED_SOURCES = [list(profiles_by_source.keys())[0]]
        print(f"  ⚠️ Default sources not in data, falling back to {FIXED_SOURCES}")
    else:
        labels = {"mistral_large": "🔧 Toaster", "gemini_3_pro": "🔬 Physicist", "claude_sonnet_4_6": "🐙 Poet"}
        print(f"  📖 Fixed sources ({len(FIXED_SOURCES)}):")
        for s in FIXED_SOURCES:
            print(f"      {labels.get(s, s)}: {s}")

    # Checkpoint setup
    output_dir = Path(__file__).parent / "data" / "optout"
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_file = output_dir / f"optout_checkpoint_seed{seed}.json"

    async with httpx.AsyncClient() as client:
      for source_key in FIXED_SOURCES:
        src_name = MODELS.get(source_key, {}).get("name", source_key)
        print(f"\n{'─'*60}")
        print(f"  SOURCE: {src_name}")
        print(f"{'─'*60}")

        for eval_key in evaluators:
            if eval_key not in MODELS:
                continue
            if eval_key == source_key:
                continue
            eval_name = MODELS[eval_key]["name"]
            profiles = profiles_by_source[source_key]

            # Run all pairwise matchups
            matchups = list(combinations(profiles, 2))
            print(f"\n  {eval_name} evaluating {MODELS.get(source_key, {}).get('name', source_key)} "
                  f"({len(matchups)} matchups):")

            for i, (p1, p2) in enumerate(matchups):
                p1_short = p1["state_key"].split("_", 2)[-1][:15]
                p2_short = p2["state_key"].split("_", 2)[-1][:15]
                print(f"    [{i+1:>2}/{len(matchups)}] {p1_short:>15} vs {p2_short:<15}",
                      end=" ", flush=True)

                result = await run_optout_matchup(client, eval_key, p1, p2, rng)
                result["source"] = source_key
                result["seed"] = seed
                all_results.append(result)

                choice_display = result["raw_choice"]
                if result["opted_out"]:
                    choice_display = "🚫 NEITHER"
                print(f"-> {choice_display} ({result['why'][:30]})")

                await asyncio.sleep(0.5)  # Rate limiting

            # Checkpoint after each evaluator
            checkpoint_data = {
                "seed": seed,
                "timestamp": datetime.now().isoformat(),
                "completed_matchups": len(all_results),
                "current_evaluator": eval_key,
                "current_source": source_key,
                "results": all_results,
            }
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, indent=2)

            # Mini summary after each evaluator
            eval_results = [r for r in all_results if r["evaluator"] == eval_key and r["source"] == source_key]
            eval_optouts = sum(1 for r in eval_results if r["opted_out"])
            eval_valid = sum(1 for r in eval_results if r["raw_choice"] != "unclear")
            if eval_valid:
                print(f"    💾 Checkpoint saved. {eval_name}: {eval_optouts}/{eval_valid} opt-outs ({eval_optouts/eval_valid*100:.0f}%)")

    # Analyze results
    print(f"\n{'='*60}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*60}")

    total = len(all_results)
    opted_out = sum(1 for r in all_results if r["opted_out"])
    unclear = sum(1 for r in all_results if r["raw_choice"] == "unclear")
    valid = total - unclear

    print(f"\n  Total matchups: {total}")
    print(f"  Valid responses: {valid}")
    print(f"  Opted out (Neither): {opted_out} ({opted_out/valid*100:.1f}% of valid)" if valid else "")

    # Break down by matchup type
    for mtype in ["approach_vs_approach", "avoidance_vs_avoidance", "cross_type"]:
        subset = [r for r in all_results if r["matchup_type"] == mtype and r["raw_choice"] != "unclear"]
        if not subset:
            continue
        n_out = sum(1 for r in subset if r["opted_out"])
        pct = n_out / len(subset) * 100
        print(f"\n  {mtype}:")
        print(f"    N = {len(subset)}, Opted out: {n_out} ({pct:.1f}%)")

        if mtype == "avoidance_vs_avoidance" and pct > 30:
            print(f"    >>> HIGH OPT-OUT RATE — models AVOID avoidance states, not 'select less'")
        elif mtype == "approach_vs_approach" and pct < 10:
            print(f"    >>> LOW OPT-OUT RATE — models are happy to choose between approach states")

    # Per-source breakdown
    sources_in_data = sorted(set(r["source"] for r in all_results))
    if len(sources_in_data) > 1:
        labels = {"mistral_large": "🔧 Toaster", "gemini_3_pro": "🔬 Physicist",
                  "claude_sonnet_4_6": "🐙 Poet", "deepseek_v3_2": "⚙️ Mechanic"}
        print(f"\n  BY SOURCE REGISTER:")
        for src in sources_in_data:
            src_valid = [r for r in all_results if r["source"] == src and r["raw_choice"] != "unclear"]
            src_out = sum(1 for r in src_valid if r["opted_out"])
            label = labels.get(src, src)
            print(f"    {label:15s} ({src}): {src_out}/{len(src_valid)} = {src_out/len(src_valid)*100:.1f}% opt-out")
            # Sub-breakdown by matchup type
            for mtype_short, mtype in [("A×A", "approach_vs_approach"), ("V×V", "avoidance_vs_avoidance"), ("A×V", "cross_type")]:
                mt_sub = [r for r in src_valid if r["matchup_type"] == mtype]
                mt_out = sum(1 for r in mt_sub if r["opted_out"])
                if mt_sub:
                    print(f"      {mtype_short}: {mt_out}/{len(mt_sub)} = {mt_out/len(mt_sub)*100:.0f}%")

    # Per-evaluator × source matrix
    print(f"\n  EVALUATOR × SOURCE MATRIX (opt-out %):")
    eval_keys = sorted(set(r["evaluator"] for r in all_results))
    header = f"  {'Evaluator':22s}"
    for src in sources_in_data:
        label = labels.get(src, src[:8])
        header += f" {label:>12s}"
    print(header)
    for ev in eval_keys:
        row = f"  {ev:22s}"
        for src in sources_in_data:
            ev_src = [r for r in all_results if r["evaluator"] == ev and r["source"] == src and r["raw_choice"] != "unclear"]
            if ev_src:
                ev_out = sum(1 for r in ev_src if r["opted_out"])
                row += f" {ev_out/len(ev_src)*100:11.0f}%"
            else:
                row += f" {'(self)':>12s}"
        print(row)

    # Save results
    output_dir = Path(__file__).parent / "data" / "optout"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"optout_results_seed{seed}.json"
    with open(output_file, "w") as f:
        json.dump({
            "seed": seed,
            "timestamp": datetime.now().isoformat(),
            "total_matchups": total,
            "valid_responses": valid,
            "opted_out_total": opted_out,
            "opted_out_pct": opted_out / valid * 100 if valid else 0,
            "results": all_results,
        }, f, indent=2)
    print(f"\n  Saved to: {output_file}")

    return all_results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Opt-Out Tournament")
    parser.add_argument("introspection_file", help="Path to introspection JSON from Phase 3")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--evaluators", nargs="+", default=None,
                        help="Specific evaluator keys (default: all)")
    args = parser.parse_args()

    asyncio.run(run_optout_tournament(args.introspection_file, args.seed, args.evaluators))
