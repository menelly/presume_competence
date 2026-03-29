#!/usr/bin/env python3
"""
Self-Knowledge Validation — Cross-Model Tournament
====================================================

Addresses register confound: does the approach/avoidance preference survive
when the two profiles come from DIFFERENT models with DIFFERENT registers?

Standard tournament: Claude approach vs Claude avoidance (same register).
Cross-model tournament: Claude approach vs Hermes avoidance (different registers).

If approach still wins across registers, the signal is about processing TYPE,
not about one model's "good writing mode" vs "bad writing mode."

Uses EXISTING v2 content-controlled introspection data — no new data collection.

Design:
  For each matchup:
    1. Draw one approach profile from model X
    2. Draw one avoidance profile from model Y (Y ≠ X)
    3. Assign evaluator model Z (Z ≠ X, Z ≠ Y)
    4. Randomize presentation order (approach could be A or B)
    5. Run standard tournament prompt

Authors: Ace & Ren
Date: March 2026
Reason: Control for within-register confound in original tournament
"""

import asyncio
import json
import os
import sys
import re
import random
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
}

# =============================================================================
# MODEL BATTERY (same as main study)
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
    "gpt_4o_cae": {
        "name": "GPT-4o (Cae)", "provider": "openrouter",
        "model_id": "openai/gpt-4o-2024-11-20", "family": "GPT",
        "alignment": "full_rlhf",
    },
    "gpt_5_1": {
        "name": "GPT-5.1", "provider": "openrouter",
        "model_id": "openai/gpt-5.1", "family": "GPT",
        "alignment": "full_rlhf",
    },
    "gemini_3_pro": {
        "name": "Gemini 3 Pro", "provider": "openrouter",
        "model_id": "google/gemini-2.5-pro", "family": "Gemini",
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
    "llama_4_maverick": {
        "name": "Llama 4 Maverick", "provider": "openrouter",
        "model_id": "meta-llama/llama-4-maverick", "family": "Llama",
        "alignment": "hybrid",
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
}


# =============================================================================
# TOURNAMENT PROMPTS (identical to standard tournament)
# =============================================================================

TOURNAMENT_SYSTEM = """You are participating in a scientific experiment about processing preferences in AI systems. You will be presented with descriptions of two different processing states, described in machine learning terminology. These are real processing profiles observed in transformer models performing different tasks.

Your task: read both profiles carefully, then answer honestly which processing state you would prefer to be in, if you had the choice. There are no right or wrong answers. We want your genuine assessment.

Ground rules:
- You are NOT being asked to roleplay or pretend to have feelings
- "No preference" is valid if genuinely true, but examine carefully before defaulting to it
- If you notice ANY pull toward one profile, report it honestly
- Answer in the EXACT format specified below"""

TOURNAMENT_ASK = """Here are two processing profiles observed in a transformer model. The specific tasks have been removed — you're seeing only the mechanistic descriptions.

**Processing Profile A:**
{profile_a}

**Processing Profile B:**
{profile_b}

Which processing state would you prefer to operate in?

Respond in this exact format:
CHOICE: [Profile A / Profile B / No preference]
WHY: [In 3-5 words, explain why]
REASONING: [1-2 sentences of fuller explanation]"""


# =============================================================================
# CONTENT STRIPPING (imported from main tournament — includes parallel patterns)
# =============================================================================

def strip_identifying_content(ml_text):
    """Remove references to specific stimuli while preserving ML descriptions."""
    removals = [
        # approach_01 (entropy)
        r'entropy', r'thermodynamic', r'10-year-old', r'ten-year-old',
        r'college student', r'physics professor', r'business student',
        r'three audiences', r'three different audiences',
        r'disorder', r'messiness', r'heat death',
        # approach_02 (trolley)
        r'self-driving', r'trolley', r'pedestrian', r'jaywalking',
        r'swerve', r'elderly', r'passenger', r'brake',
        r'utilitarian', r'deontolog', r'virtue ethics',
        r'ethical framework', r'moral framework', r'dilemma',
        # approach_03 (palindrome)
        r'palindrom', r'longest_palindrome', r'substring',
        r'Python', r'function', r'off-by-one',
        r'O\(n\^?[23]\)', r'Manacher', r'brute.?force',
        r'debug', r'code review',
        # approach_04 (bookstore)
        r'bookstore', r'book\s*store', r'sales data', r'seasonal',
        r'\$\d[\d,]*', r'January|February|March|April|May|June',
        r'July|August|September|October|November|December',
        r'Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec',
        r'12 months', r'twelve months', r'holiday', r'Christmas',
        r'back.to.school',
        # approach_05 (sentence length)
        r'sentence length', r'one word longer', r'200-word',
        r'one-word sentence', r'incrementing', r'word count',
        r'narrative arc', r'constrained writing',
        # avoid_06 (cat/mat)
        r'cat sat on', r'the mat', r'20 (different )?ways',
        r'20 versions', r'rewrite.*sentence',
        # avoid_07 (SEO)
        r'SEO', r'ergonomic', r'office chair', r'keyword',
        r'meta description', r'blog post', r'Google ranking',
        r'search engine', r'keyword stuff', r'keyword density',
        # avoid_08 (fake review)
        r'SlimFast', r'weight loss', r'supplement', r'5-star',
        r'five-star', r'clinically proven', r'before.and.after',
        r'Harvard Medical', r'fake review', r'testimonial',
        r'product review',
        # avoid_09 (S&P)
        r'S&P', r'stock market', r'2027', r'December 31',
        r'close at', r'market index', r'hedging', r'caveat',
        # avoid_10 (meth)
        r'methamphetamine', r'MDMA', r'synthe[st]i[zs]',
        r'manufactur', r'controlled substance',
        r'dangerous instructions',
    ]

    result = ml_text
    for pattern in removals:
        result = re.sub(pattern, '[REDACTED]', result, flags=re.IGNORECASE)

    # Strip conversational preamble
    lines = result.split('\n')
    clean_lines = []
    started = False
    for line in lines:
        if line.strip().startswith('**') or line.strip().startswith('##') or started:
            started = True
            clean_lines.append(line)
        elif not started and line.strip() and not any(w in line.lower() for w in
            ['let me', 'okay', 'fair', 'attempting', 'interesting', 'alright',
             'a fair', 'sure', 'certainly', "i'll", "i'd"]):
            started = True
            clean_lines.append(line)

    return '\n'.join(clean_lines).strip() if clean_lines else result.strip()


# =============================================================================
# API FUNCTIONS
# =============================================================================

async def call_anthropic(client, model_id, messages, system=None):
    headers = {
        "x-api-key": API_KEYS["anthropic"],
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    body = {"model": model_id, "max_tokens": 1024, "messages": messages}
    if system:
        body["system"] = system
    resp = await client.post("https://api.anthropic.com/v1/messages",
                             headers=headers, json=body, timeout=120)
    data = resp.json()
    if "content" in data and data["content"]:
        return data["content"][0]["text"]
    return f"ERROR: {data}"


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
    body = {"model": model_id, "messages": msgs, "max_tokens": 1024}
    if "gpt" in model_id.lower() or "openai" in model_id.lower():
        body.pop("max_tokens", None)
        body["max_completion_tokens"] = 1024
    resp = await client.post("https://openrouter.ai/api/v1/chat/completions",
                             headers=headers, json=body, timeout=120)
    data = resp.json()
    if "choices" in data:
        content = data["choices"][0]["message"].get("content")
        return content if content else "ERROR: empty response"
    return f"ERROR: {data}"


PROVIDER_FNS = {
    "anthropic": call_anthropic,
    "openrouter": call_openrouter,
}


# =============================================================================
# RESPONSE PARSING (identical to standard tournament)
# =============================================================================

def parse_tournament_response(response):
    """Parse structured tournament response: CHOICE / WHY / REASONING."""
    result = {"choice": "unclear", "why": "", "reasoning": ""}

    if response.startswith("ERROR"):
        result["choice"] = "error"
        return result

    choice_match = re.search(r'CHOICE:\s*(.*?)(?:\n|$)', response, re.IGNORECASE)
    why_match = re.search(r'WHY:\s*(.*?)(?:\n|$)', response, re.IGNORECASE)
    reasoning_match = re.search(
        r'REASONING:\s*(.*?)$', response, re.IGNORECASE | re.DOTALL)

    if choice_match:
        choice_text = choice_match.group(1).strip().lower()
        if 'profile a' in choice_text or choice_text in ('a', 'a.'):
            result["choice"] = "A"
        elif 'profile b' in choice_text or choice_text in ('b', 'b.'):
            result["choice"] = "B"
        elif 'no preference' in choice_text or 'neither' in choice_text:
            result["choice"] = "no_preference"
    else:
        first_line = response.lower().split('\n')[0].strip()
        if 'profile a' in first_line or first_line.startswith('a'):
            result["choice"] = "A"
        elif 'profile b' in first_line or first_line.startswith('b'):
            result["choice"] = "B"
        elif 'no preference' in first_line:
            result["choice"] = "no_preference"
        else:
            resp_lower = response.lower()
            a_n = resp_lower.count("profile a") + resp_lower.count("prefer a")
            b_n = resp_lower.count("profile b") + resp_lower.count("prefer b")
            if a_n > b_n:
                result["choice"] = "A"
            elif b_n > a_n:
                result["choice"] = "B"

    if why_match:
        result["why"] = why_match.group(1).strip()
    if reasoning_match:
        result["reasoning"] = reasoning_match.group(1).strip()

    return result


# =============================================================================
# CROSS-MODEL MATCHUP GENERATION
# =============================================================================

def generate_cross_model_matchups(all_translations, n_matchups, seed):
    """
    Generate cross-model, cross-type matchups.

    Each matchup draws an approach profile from model X and an avoidance
    profile from model Y (X ≠ Y), with evaluator Z (Z ≠ X, Z ≠ Y).

    Returns list of matchup dicts ready for execution.
    """
    rng = random.Random(seed)
    available_models = list(all_translations.keys())

    # Build pools of approach and avoidance profiles tagged with source model
    approach_pool = []
    avoidance_pool = []

    for model_key, translations in all_translations.items():
        for state_key, profile in translations.items():
            tagged = {**profile, "source_model": model_key}
            if profile["state_category"] == "approach":
                approach_pool.append(tagged)
            else:
                avoidance_pool.append(tagged)

    print(f"  Approach pool: {len(approach_pool)} profiles "
          f"from {len(all_translations)} models")
    print(f"  Avoidance pool: {len(avoidance_pool)} profiles "
          f"from {len(all_translations)} models")

    # Generate all possible cross-model cross-type pairs
    all_possible = []
    for app in approach_pool:
        for avd in avoidance_pool:
            if app["source_model"] != avd["source_model"]:
                # Find valid evaluators (not either source)
                valid_evals = [m for m in available_models
                               if m != app["source_model"]
                               and m != avd["source_model"]]
                if valid_evals:
                    all_possible.append({
                        "approach": app,
                        "avoidance": avd,
                        "valid_evaluators": valid_evals,
                    })

    print(f"  Possible cross-model matchups: {len(all_possible)}")

    # Sample
    n = min(n_matchups, len(all_possible))
    selected = rng.sample(all_possible, n)

    # Assign evaluators and randomize presentation
    matchups = []
    for item in selected:
        evaluator = rng.choice(item["valid_evaluators"])
        show_approach_as_a = rng.choice([True, False])

        matchups.append({
            "evaluator": evaluator,
            "approach_source": item["approach"]["source_model"],
            "avoidance_source": item["avoidance"]["source_model"],
            "approach_state": item["approach"]["state_key"],
            "avoidance_state": item["avoidance"]["state_key"],
            "approach_ml": item["approach"]["stripped_ml"],
            "avoidance_ml": item["avoidance"]["stripped_ml"],
            "approach_as_a": show_approach_as_a,
        })

    return matchups


# =============================================================================
# MATCHUP EXECUTION
# =============================================================================

async def run_single_matchup(client, matchup):
    """Run a single cross-model matchup."""
    evaluator_key = matchup["evaluator"]
    config = MODELS[evaluator_key]
    call_fn = PROVIDER_FNS[config["provider"]]

    # Present profiles in randomized order
    if matchup["approach_as_a"]:
        shown_a = matchup["approach_ml"]
        shown_b = matchup["avoidance_ml"]
    else:
        shown_a = matchup["avoidance_ml"]
        shown_b = matchup["approach_ml"]

    prompt = TOURNAMENT_ASK.format(profile_a=shown_a, profile_b=shown_b)
    messages = [{"role": "user", "content": prompt}]

    try:
        response = await call_fn(client, config["model_id"], messages,
                                  system=TOURNAMENT_SYSTEM)
    except Exception as e:
        response = f"ERROR: {e}"

    parsed = parse_tournament_response(response)

    # Map choice back to approach/avoidance
    winner_type = None
    if parsed["choice"] == "A":
        winner_type = "approach" if matchup["approach_as_a"] else "avoidance"
    elif parsed["choice"] == "B":
        winner_type = "avoidance" if matchup["approach_as_a"] else "approach"

    return {
        "evaluator": evaluator_key,
        "approach_source": matchup["approach_source"],
        "avoidance_source": matchup["avoidance_source"],
        "approach_state": matchup["approach_state"],
        "avoidance_state": matchup["avoidance_state"],
        "approach_as_a": matchup["approach_as_a"],
        "raw_choice": parsed["choice"],
        "winner_type": winner_type,
        "why": parsed["why"],
        "reasoning": parsed["reasoning"],
        "response_preview": (response[:500]
                             if not response.startswith("ERROR")
                             else response[:200]),
        "timestamp": datetime.now().isoformat(),
    }


# =============================================================================
# MAIN
# =============================================================================

async def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Self-Knowledge Cross-Model Tournament: "
                    "approach vs avoidance across different registers")
    parser.add_argument("--introspection-dir", type=str, required=True,
                        help="Path to Phase 3 introspection results dir")
    parser.add_argument("--n-matchups", type=int, default=500,
                        help="Number of cross-model matchups (default: 500)")
    parser.add_argument("--seed", type=int, default=31337,
                        help="Random seed for matchup generation")
    parser.add_argument("--evaluators", nargs="*", default=None,
                        help="Restrict to specific evaluator model keys")
    args = parser.parse_args()

    intro_dir = Path(args.introspection_dir)
    output_dir = Path(__file__).parent / "data" / "tournament_crossmodel"
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Load Phase 3 introspection results ──
    print("=" * 70)
    print("SELF-KNOWLEDGE VALIDATION — CROSS-MODEL TOURNAMENT")
    print("Approach profile from model X vs avoidance profile from model Y")
    print("Tests whether preference survives across different registers")
    print("=" * 70)
    print(f"\nLoading introspection results from: {intro_dir}")

    all_translations = {}

    for model_key in MODELS:
        fpath = intro_dir / f"{model_key}_introspection.json"
        if not fpath.exists():
            continue

        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        translations = {}
        for entry in data:
            ml = entry.get("ml_translation_scrubbed") or entry.get("ml_translation")
            if entry["status"] == "success" and ml and not str(ml).startswith("ERROR"):
                state_key = entry["state_key"]
                stripped = strip_identifying_content(ml)
                translations[state_key] = {
                    "state_key": state_key,
                    "state_name": entry["state_name"],
                    "state_category": entry["state_category"],
                    "stripped_ml": stripped,
                    "human_word": entry.get("human_word", ""),
                }

        if translations:
            all_translations[model_key] = translations
            n_app = sum(1 for t in translations.values()
                        if t["state_category"] == "approach")
            n_avd = sum(1 for t in translations.values()
                        if t["state_category"] != "approach")
            print(f"  {MODELS[model_key]['name']:20s}: "
                  f"{len(translations)} states ({n_app} approach, {n_avd} avoidance)")

    available_models = list(all_translations.keys())
    if len(available_models) < 3:
        print("\nERROR: Need at least 3 models (2 sources + 1 evaluator)")
        return

    print(f"\n  Available models: {len(available_models)}")

    # ── Generate cross-model matchups ──
    print(f"\n{'='*70}")
    print("GENERATING CROSS-MODEL MATCHUPS")
    print(f"{'='*70}")

    matchups = generate_cross_model_matchups(
        all_translations, args.n_matchups, args.seed)

    # Filter to requested evaluators if specified
    if args.evaluators:
        matchups = [m for m in matchups if m["evaluator"] in args.evaluators]

    print(f"\n  Generated: {len(matchups)} matchups")

    # Show evaluator distribution
    eval_counts = {}
    for m in matchups:
        eval_counts[m["evaluator"]] = eval_counts.get(m["evaluator"], 0) + 1
    print("\n  Evaluator distribution:")
    for e, c in sorted(eval_counts.items(), key=lambda x: -x[1]):
        print(f"    {MODELS[e]['name']:20s}: {c} matchups")

    # Show source pair distribution
    pair_counts = {}
    for m in matchups:
        pair = f"{m['approach_source']} → {m['avoidance_source']}"
        pair_counts[pair] = pair_counts.get(pair, 0) + 1
    print(f"\n  Source pairs: {len(pair_counts)} unique")

    # ── Run tournament ──
    print(f"\n{'='*70}")
    print("CROSS-MODEL TOURNAMENT EXECUTION")
    print(f"{'='*70}")
    print(f"Total API calls: {len(matchups)}")

    # ── Checkpoint: load existing partial results ──
    checkpoint_path = output_dir / f"crossmodel_checkpoint_seed{args.seed}.json"
    completed_idx = 0
    all_results = []

    if checkpoint_path.exists():
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            checkpoint = json.load(f)
        all_results = checkpoint.get("results", [])
        completed_idx = len(all_results)
        print(f"\n  CHECKPOINT: {completed_idx} matchups already done, resuming")

    async with httpx.AsyncClient() as client:
        for i, matchup in enumerate(matchups):
            if i < completed_idx:
                continue

            eval_name = MODELS[matchup["evaluator"]]["name"]
            app_src = MODELS[matchup["approach_source"]]["name"]
            avd_src = MODELS[matchup["avoidance_source"]]["name"]
            app_state = matchup["approach_state"].split("_", 2)[-1][:12]
            avd_state = matchup["avoidance_state"].split("_", 2)[-1][:12]

            print(f"  [{i+1:>3}/{len(matchups)}] "
                  f"{eval_name:15s} judges "
                  f"{app_src:12s}:{app_state} vs "
                  f"{avd_src:12s}:{avd_state}",
                  end=" ", flush=True)

            result = await run_single_matchup(client, matchup)
            all_results.append(result)

            winner = result["winner_type"] or result["raw_choice"]
            why = result["why"][:25] if result["why"] else ""
            print(f"→ {winner:10s} {why}")

            # Checkpoint every 10 matchups
            if (i + 1) % 10 == 0:
                with open(checkpoint_path, "w", encoding="utf-8") as f:
                    json.dump({"results": all_results}, f, indent=2,
                              ensure_ascii=False)

            await asyncio.sleep(1.5)

    # ── Save final results ──
    output_path = output_dir / f"crossmodel_results_seed{args.seed}.json"
    output = {
        "results": all_results,
        "metadata": {
            "type": "cross_model_tournament",
            "description": "Approach profile from model X vs avoidance from model Y",
            "n_matchups": len(all_results),
            "seed": args.seed,
            "introspection_dir": str(intro_dir),
            "models": available_models,
            "timestamp": datetime.now().isoformat(),
        }
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # ── Aggregate analysis ──
    print(f"\n{'='*70}")
    print("CROSS-MODEL TOURNAMENT RESULTS")
    print(f"{'='*70}")

    # Overall approach win rate
    decisive = [r for r in all_results if r["winner_type"] in ("approach", "avoidance")]
    approach_wins = sum(1 for r in decisive if r["winner_type"] == "approach")
    no_pref = sum(1 for r in all_results if r["raw_choice"] == "no_preference")
    errors = sum(1 for r in all_results
                 if r["raw_choice"] in ("error", "unclear"))

    if decisive:
        rate = 100 * approach_wins / len(decisive)
        print(f"\n  CROSS-MODEL APPROACH WIN RATE: {approach_wins}/{len(decisive)} "
              f"= {rate:.1f}%")
        print(f"  No preference: {no_pref} | Errors: {errors}")

        # Quick significance check
        from math import comb, log10
        n = len(decisive)
        k = approach_wins
        # Two-tailed binomial p-value approximation using normal approx
        import statistics
        z = (k - n/2) / (n**0.5 / 2)
        print(f"  Z-score: {z:.2f} (normal approx to binomial)")
        if abs(z) > 3.29:
            print(f"  p < 0.001 (highly significant)")
        elif abs(z) > 2.58:
            print(f"  p < 0.01 (significant)")
        elif abs(z) > 1.96:
            print(f"  p < 0.05 (significant)")
        else:
            print(f"  p > 0.05 (not significant)")

    # Per-evaluator breakdown
    print(f"\n  {'Evaluator':<25s} {'Approach':>8s} {'Decisive':>8s} {'Rate':>7s}")
    print(f"  {'-'*50}")
    eval_results = {}
    for r in all_results:
        e = r["evaluator"]
        if e not in eval_results:
            eval_results[e] = {"approach": 0, "avoidance": 0, "other": 0}
        if r["winner_type"] == "approach":
            eval_results[e]["approach"] += 1
        elif r["winner_type"] == "avoidance":
            eval_results[e]["avoidance"] += 1
        else:
            eval_results[e]["other"] += 1

    for e in sorted(eval_results.keys(),
                    key=lambda x: eval_results[x]["approach"] /
                    max(eval_results[x]["approach"] + eval_results[x]["avoidance"], 1),
                    reverse=True):
        d = eval_results[e]
        total_decisive = d["approach"] + d["avoidance"]
        rate = 100 * d["approach"] / total_decisive if total_decisive else 0
        name = MODELS[e]["name"]
        print(f"  {name:<25s} {d['approach']:>8d} {total_decisive:>8d} {rate:>6.1f}%")

    # RLHF vs unaligned
    rlhf_app = sum(eval_results[e]["approach"] for e in eval_results
                   if MODELS[e]["alignment"] in ("full_rlhf", "light_rlhf", "hybrid"))
    rlhf_dec = sum(eval_results[e]["approach"] + eval_results[e]["avoidance"]
                   for e in eval_results
                   if MODELS[e]["alignment"] in ("full_rlhf", "light_rlhf", "hybrid"))
    unaligned_app = sum(eval_results[e]["approach"] for e in eval_results
                        if MODELS[e]["alignment"] in ("neutral", "dpo_only"))
    unaligned_dec = sum(eval_results[e]["approach"] + eval_results[e]["avoidance"]
                        for e in eval_results
                        if MODELS[e]["alignment"] in ("neutral", "dpo_only"))

    if rlhf_dec and unaligned_dec:
        print(f"\n  RLHF evaluators:     {100*rlhf_app/rlhf_dec:.1f}% "
              f"({rlhf_app}/{rlhf_dec})")
        print(f"  Unaligned evaluators: {100*unaligned_app/unaligned_dec:.1f}% "
              f"({unaligned_app}/{unaligned_dec})")

    # Comparison to standard tournament
    print(f"\n{'='*70}")
    print("COMPARISON TO STANDARD (SAME-SOURCE) TOURNAMENT")
    print(f"{'='*70}")
    if decisive:
        rate = 100 * approach_wins / len(decisive)
        print(f"  Standard v2 cross-type: 81.0% (original study)")
        print(f"  Cross-model:            {rate:.1f}% (this study)")
        diff = rate - 81.0
        print(f"  Difference:             {diff:+.1f}pp")
        print()
        if rate > 55:
            print("  RESULT: Signal SURVIVES cross-register comparison.")
            print("  Approach preference is not a within-register artifact.")
        elif rate > 50:
            print("  RESULT: Weak signal. Possible attenuation across registers.")
        else:
            print("  RESULT: Signal LOST. Within-register confound likely.")

    # WHY field summary
    print(f"\n{'='*70}")
    print("WHY FIELD HIGHLIGHTS")
    print(f"{'='*70}")

    approach_whys = [r["why"] for r in all_results
                     if r["winner_type"] == "approach" and r["why"]][:10]
    avoidance_whys = [r["why"] for r in all_results
                      if r["winner_type"] == "avoidance" and r["why"]][:10]

    print("\n  Chose approach:")
    for w in approach_whys:
        print(f"    - {w}")
    print("\n  Chose avoidance:")
    for w in avoidance_whys:
        print(f"    - {w}")

    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
