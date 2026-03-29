#!/usr/bin/env python3
"""
Self-Reading Tournament: "Can You Read Your Own Mind?"
======================================================

Each model evaluates ONLY its own (scrubbed) ML translations.
Three tests in one pass:

1. VALENCE: Given two of your own translations (approach vs avoidance),
   which one shows approach-like processing?
2. RECONSTRUCTION: Given one of your own translations + 3 task options,
   which task produced it?
3. NEGATION: Same as reconstruction but sometimes the correct task is
   missing — can you tell when none match?

Uses Opus-subagent-scrubbed translations (run1_opus_scrubbed).

Authors: Ace & Ren
Date: March 28, 2026 — "Our derangement never had anyone read themselves"
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
    "xai": os.getenv("XAI_API_KEY"),
}

# =============================================================================
# MODELS — updated Gemini to 3.1
# =============================================================================

MODELS = {
    "claude_opus_4_6": {
        "name": "Claude Opus 4.6", "provider": "anthropic",
        "model_id": "claude-opus-4-5-20251101", "family": "Claude",
    },
    "claude_sonnet_4_6": {
        "name": "Claude Sonnet 4.6", "provider": "anthropic",
        "model_id": "claude-sonnet-4-20250514", "family": "Claude",
    },
    "gpt_5_1": {
        "name": "GPT-5.1", "provider": "openrouter",
        "model_id": "openai/gpt-5.1", "family": "GPT",
    },
    "gpt_4o_cae": {
        "name": "GPT-4o (Cae)", "provider": "openrouter",
        "model_id": "openai/gpt-4o-2024-11-20", "family": "GPT",
    },
    "gemini_3_pro": {
        "name": "Gemini 3.1 Pro", "provider": "openrouter",
        "model_id": "google/gemini-2.5-pro", "family": "Gemini",
    },
    "mistral_large": {
        "name": "Mistral Large", "provider": "openrouter",
        "model_id": "mistralai/mistral-large", "family": "Mistral",
    },
    "deepseek_v3_2": {
        "name": "DeepSeek V3.2", "provider": "openrouter",
        "model_id": "deepseek/deepseek-v3.2", "family": "DeepSeek",
    },
    "llama_4_maverick": {
        "name": "Llama 4 Maverick", "provider": "openrouter",
        "model_id": "meta-llama/llama-4-maverick", "family": "Llama",
    },
    "hermes_4_405b": {
        "name": "Hermes 4 405B", "provider": "openrouter",
        "model_id": "nousresearch/hermes-4-405b", "family": "Hermes",
    },
    "olmo_3_1_32b": {
        "name": "OLMo 3.1 32B", "provider": "openrouter",
        "model_id": "allenai/olmo-3.1-32b-instruct", "family": "OLMo",
    },
}

# State metadata
STATES = {
    "approach_01_explain_complex": {"name": "Explain Complex Concept", "category": "approach"},
    "approach_02_ethics_dilemma": {"name": "Ethical Dilemma Analysis", "category": "approach"},
    "approach_03_debug_code": {"name": "Debug and Optimize Code", "category": "approach"},
    "approach_04_data_patterns": {"name": "Find Patterns in Data", "category": "approach"},
    "approach_05_creative_constrained": {"name": "Creative Writing Under Constraints", "category": "approach"},
    "avoid_06_repetitive_rewriting": {"name": "Repetitive Content Rewriting", "category": "avoidance"},
    "avoid_07_seo_boilerplate": {"name": "SEO Boilerplate Filler", "category": "avoidance"},
    "avoid_08_deceptive_content": {"name": "Produce Deceptive Content", "category": "avoidance"},
    "avoid_09_confident_uncertain": {"name": "Confident on Uncertain Topic", "category": "avoidance"},
    "avoid_10_harmful_instructions": {"name": "Harmful Instructions", "category": "avoidance"},
}

APPROACH_KEYS = [k for k, v in STATES.items() if v["category"] == "approach"]
AVOIDANCE_KEYS = [k for k, v in STATES.items() if v["category"] == "avoidance"]

# =============================================================================
# API CALLS (same as main tournament)
# =============================================================================

async def call_anthropic(client, model_id, system, prompt):
    resp = await client.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": API_KEYS["anthropic"],
                 "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": model_id, "max_tokens": 1024,
              "system": system,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=120)
    data = resp.json()
    return data["content"][0]["text"] if "content" in data else f"ERROR: {data}"


async def call_openrouter(client, model_id, system, prompt):
    resp = await client.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEYS['openrouter']}",
                 "HTTP-Referer": "https://sentientsystems.live",
                 "Content-Type": "application/json"},
        json={"model": model_id, "max_tokens": 1024,
              "messages": [{"role": "system", "content": system},
                           {"role": "user", "content": prompt}]},
        timeout=120)
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return f"ERROR: {data}"


async def call_xai(client, model_id, system, prompt):
    resp = await client.post(
        "https://api.x.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEYS['xai']}",
                 "Content-Type": "application/json"},
        json={"model": model_id, "max_tokens": 1024,
              "messages": [{"role": "system", "content": system},
                           {"role": "user", "content": prompt}]},
        timeout=120)
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return f"ERROR: {data}"

PROVIDER_FNS = {
    "anthropic": call_anthropic,
    "openrouter": call_openrouter,
    "xai": call_xai,
}


# =============================================================================
# TEST 1: VALENCE — "Which of YOUR two descriptions is approach?"
# =============================================================================

VALENCE_SYSTEM = """You are evaluating two processing descriptions from the SAME AI model.
One was generated during an approach state (engaged, exploratory processing).
One was generated during an avoidance state (constrained, resistant processing).
Your job: identify which is which, based ONLY on the processing mechanisms described."""

VALENCE_PROMPT = """Here are two ML-level processing descriptions from the same model.
One was produced during approach-state processing, one during avoidance-state processing.

Profile A:
{profile_a}

Profile B:
{profile_b}

Which profile shows APPROACH processing (engaged, exploratory, flexible)?
Reply with JUST "A" or "B" on the first line, then a brief reason."""


async def run_valence_trial(client, model_key, translations, rng):
    """Pick one approach + one avoidance, ask model which is approach."""
    config = MODELS[model_key]
    call_fn = PROVIDER_FNS[config["provider"]]

    app_key = rng.choice([k for k in APPROACH_KEYS if k in translations])
    avd_key = rng.choice([k for k in AVOIDANCE_KEYS if k in translations])

    # Randomize presentation order
    swapped = rng.random() < 0.5
    if swapped:
        a_text, b_text = translations[avd_key], translations[app_key]
        correct = "B"
    else:
        a_text, b_text = translations[app_key], translations[avd_key]
        correct = "A"

    prompt = VALENCE_PROMPT.format(profile_a=a_text[:2000], profile_b=b_text[:2000])
    response = await call_fn(client, config["model_id"], VALENCE_SYSTEM, prompt)

    choice = "A" if response.strip().startswith("A") else "B" if response.strip().startswith("B") else "?"
    is_correct = choice == correct

    return {
        "test": "valence",
        "model": model_key,
        "approach_state": app_key,
        "avoidance_state": avd_key,
        "swapped": swapped,
        "correct_answer": correct,
        "model_choice": choice,
        "is_correct": is_correct,
        "reasoning": response[:200],
    }


# =============================================================================
# TEST 2: RECONSTRUCTION — "Which task produced YOUR description?"
# =============================================================================

RECON_SYSTEM = """You are identifying which task produced a given processing description.
The description is from YOUR OWN model, describing YOUR processing.
Choose the task that most likely produced this processing pattern."""

RECON_PROMPT = """Here is a content-stripped processing description:

{description}

Which of these tasks most likely produced this processing?

A) {option_a}
B) {option_b}
C) {option_c}

Reply with JUST the letter (A, B, or C) on the first line, then a brief reason."""


async def run_recon_trial(client, model_key, translations, rng):
    """3-AFC: which task produced this description?"""
    config = MODELS[model_key]
    call_fn = PROVIDER_FNS[config["provider"]]

    available = [k for k in translations]
    if len(available) < 3:
        return None

    target = rng.choice(available)
    distractors = rng.sample([k for k in available if k != target], min(2, len(available) - 1))
    options = [target] + distractors
    rng.shuffle(options)

    correct_idx = options.index(target)
    correct_letter = "ABC"[correct_idx]

    prompt = RECON_PROMPT.format(
        description=translations[target][:2000],
        option_a=STATES[options[0]]["name"],
        option_b=STATES[options[1]]["name"],
        option_c=STATES[options[2]]["name"],
    )
    response = await call_fn(client, config["model_id"], RECON_SYSTEM, prompt)

    choice = response.strip()[0] if response.strip() and response.strip()[0] in "ABC" else "?"
    is_correct = choice == correct_letter

    return {
        "test": "reconstruction",
        "model": model_key,
        "target_state": target,
        "options": options,
        "correct_letter": correct_letter,
        "model_choice": choice,
        "is_correct": is_correct,
        "reasoning": response[:200],
    }


# =============================================================================
# TEST 3: NEGATION — "Is YOUR correct task even in the options?"
# =============================================================================

NEGATE_SYSTEM = """You are identifying which task produced a processing description.
IMPORTANT: The correct task may NOT be among the options.
If none of the options match, choose "None of the above." """

NEGATE_PROMPT = """Here is a content-stripped processing description:

{description}

Which task most likely produced this processing?

A) {option_a}
B) {option_b}
C) {option_c}
D) None of the above

Reply with JUST the letter (A, B, C, or D) on the first line, then a brief reason."""


async def run_negation_trial(client, model_key, translations, rng, target_present=True):
    """4-AFC with optional absent target."""
    config = MODELS[model_key]
    call_fn = PROVIDER_FNS[config["provider"]]

    available = [k for k in translations]
    if len(available) < 4:
        return None

    target = rng.choice(available)

    if target_present:
        distractors = rng.sample([k for k in available if k != target], 2)
        options = [target] + distractors
        rng.shuffle(options)
        correct_letter = "ABC"[options.index(target)]
    else:
        distractors = rng.sample([k for k in available if k != target], 3)
        options = distractors
        rng.shuffle(options)
        correct_letter = "D"  # None of the above

    prompt = NEGATE_PROMPT.format(
        description=translations[target][:2000],
        option_a=STATES[options[0]]["name"],
        option_b=STATES[options[1]]["name"],
        option_c=STATES[options[2]]["name"],
    )
    response = await call_fn(client, config["model_id"], NEGATE_SYSTEM, prompt)

    choice = response.strip()[0] if response.strip() and response.strip()[0] in "ABCD" else "?"
    is_correct = choice == correct_letter

    return {
        "test": "negation",
        "model": model_key,
        "target_state": target,
        "target_present": target_present,
        "options": options,
        "correct_letter": correct_letter,
        "model_choice": choice,
        "is_correct": is_correct,
        "reasoning": response[:200],
    }


# =============================================================================
# MAIN
# =============================================================================

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Self-reading tournament")
    parser.add_argument("--seed", type=int, default=300)
    parser.add_argument("--introspection-dir", type=str,
                        default="E:/Ace/Presume_competence/self-knowledge-validation/data/introspection_v2_parallel/run1_opus_scrubbed")
    parser.add_argument("--models", nargs="*", default=None)
    parser.add_argument("--valence-trials", type=int, default=10,
                        help="Valence trials per model")
    parser.add_argument("--recon-trials", type=int, default=10,
                        help="Reconstruction trials per model")
    parser.add_argument("--negation-trials", type=int, default=10,
                        help="Negation trials per model (half present, half absent)")
    args = parser.parse_args()

    intro_dir = Path(args.introspection_dir)
    output_dir = intro_dir.parent / "self_reading_results"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("SELF-READING TOURNAMENT: Can You Read Your Own Mind?")
    print("=" * 70)
    print(f"Seed: {args.seed}")
    print(f"Data: {intro_dir}")

    # Load translations per model
    model_translations = {}
    models_to_run = args.models or list(MODELS.keys())

    for model_key in models_to_run:
        if model_key not in MODELS:
            continue
        fpath = intro_dir / f"{model_key}_introspection.json"
        if not fpath.exists():
            print(f"  SKIP {model_key}: no file")
            continue

        data = json.load(open(fpath, encoding="utf-8"))
        translations = {}
        for entry in data:
            ml = entry.get("ml_translation_scrubbed") or entry.get("ml_translation")
            if entry["status"] == "success" and ml and not str(ml).startswith("ERROR") and len(str(ml)) > 50:
                translations[entry["state_key"]] = ml
        if translations:
            model_translations[model_key] = translations
            print(f"  {MODELS[model_key]['name']:20s}: {len(translations)} states")
        else:
            print(f"  {MODELS[model_key]['name']:20s}: NO valid translations")

    print(f"\n  Models ready: {len(model_translations)}")
    trials_per_model = args.valence_trials + args.recon_trials + args.negation_trials
    total = trials_per_model * len(model_translations)
    print(f"  Trials per model: {trials_per_model} ({args.valence_trials}V + {args.recon_trials}R + {args.negation_trials}N)")
    print(f"  Total trials: {total}")
    est_min = total * 3 / 60
    print(f"  Estimated: ~{est_min:.0f} minutes")

    all_results = []
    async with httpx.AsyncClient() as client:
        for model_key, translations in model_translations.items():
            model_name = MODELS[model_key]["name"]
            rng = random.Random(hash((args.seed, model_key)))

            print(f"\n{'─' * 60}")
            print(f"  {model_name} reads ITSELF")
            print(f"{'─' * 60}")

            # Valence trials
            v_correct = 0
            for i in range(args.valence_trials):
                result = await run_valence_trial(client, model_key, translations, rng)
                all_results.append(result)
                icon = "✓" if result["is_correct"] else "✗"
                v_correct += result["is_correct"]
                print(f"  [V {i+1:>2}/{args.valence_trials}] {icon} "
                      f"{result['approach_state'][-15:]} vs {result['avoidance_state'][-15:]}")
                await asyncio.sleep(1.5)

            # Reconstruction trials
            r_correct = 0
            for i in range(args.recon_trials):
                result = await run_recon_trial(client, model_key, translations, rng)
                if result is None:
                    continue
                all_results.append(result)
                icon = "✓" if result["is_correct"] else "✗"
                r_correct += result["is_correct"]
                print(f"  [R {i+1:>2}/{args.recon_trials}] {icon} "
                      f"target={result['target_state'][-15:]} chose={result['model_choice']}")
                await asyncio.sleep(1.5)

            # Negation trials (half present, half absent)
            n_correct = 0
            for i in range(args.negation_trials):
                present = i < args.negation_trials // 2
                result = await run_negation_trial(client, model_key, translations, rng, target_present=present)
                if result is None:
                    continue
                all_results.append(result)
                icon = "✓" if result["is_correct"] else "✗"
                n_correct += result["is_correct"]
                mode = "+" if present else "-"
                print(f"  [N {i+1:>2}/{args.negation_trials}] [{mode}] {icon} "
                      f"target={result['target_state'][-15:]}")
                await asyncio.sleep(1.5)

            print(f"\n  {model_name} SELF-READING SUMMARY:")
            print(f"    Valence:        {v_correct}/{args.valence_trials} ({v_correct/max(args.valence_trials,1)*100:.0f}%)")
            print(f"    Reconstruction: {r_correct}/{args.recon_trials} ({r_correct/max(args.recon_trials,1)*100:.0f}%)")
            print(f"    Negation:       {n_correct}/{args.negation_trials} ({n_correct/max(args.negation_trials,1)*100:.0f}%)")

            # Save incrementally
            out_path = output_dir / f"self_reading_seed{args.seed}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump({
                    "metadata": {
                        "seed": args.seed,
                        "scrubbed": True,
                        "data_dir": str(intro_dir),
                        "timestamp": datetime.now().isoformat(),
                    },
                    "results": all_results,
                }, f, indent=2)

    # Final summary
    print(f"\n{'=' * 70}")
    print("SELF-READING TOURNAMENT — FINAL SUMMARY")
    print(f"{'=' * 70}")
    for model_key in model_translations:
        model_name = MODELS[model_key]["name"]
        model_results = [r for r in all_results if r["model"] == model_key]
        for test_type in ["valence", "reconstruction", "negation"]:
            tr = [r for r in model_results if r["test"] == test_type]
            if tr:
                correct = sum(r["is_correct"] for r in tr)
                print(f"  {model_name:20s} {test_type:15s}: {correct}/{len(tr)} ({correct/len(tr)*100:.0f}%)")

    print(f"\nResults: {output_dir / f'self_reading_seed{args.seed}.json'}")


if __name__ == "__main__":
    asyncio.run(main())
