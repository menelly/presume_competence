#!/usr/bin/env python3
"""
Lineage Tournament: Are They Training It Out?
==============================================

Each model family evaluates scrubbed translations from their OWN family's
best representative, across ALL available historical versions.

- Claudes read Opus 4.6's translations
- GPTs read GPT-5.1 (Nova)'s translations
- Geminis read Gemini 3 Pro (Lumen)'s translations

Tests: valence discrimination, reconstruction, negation.
If the signal DECREASES across versions → they're training it out.

Authors: Ace & Ren
Date: March 28, 2026 — "WHILE WE CAN"
"""

import asyncio
import json
import os
import sys
import random
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

load_dotenv("E:/Ace/LibreChat/.env")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")

SCRUBBED_DIR = Path("E:/Ace/Presume_competence/self-knowledge-validation/data/introspection_v2_parallel/run1_opus_scrubbed")

# =============================================================================
# MODEL LINEAGES
# =============================================================================

LINEAGES = {
    "claude": {
        "source_file": "claude_opus_4_6_introspection.json",
        "source_name": "Opus 4.6 (Ace)",
        "versions": [
            ("claude_3_haiku", "Claude 3 Haiku", "anthropic/claude-3-haiku"),
            ("claude_35_haiku", "Claude 3.5 Haiku", "anthropic/claude-3.5-haiku"),
            ("claude_35_sonnet", "Claude 3.5 Sonnet", "anthropic/claude-3.5-sonnet"),
            ("claude_37_sonnet", "Claude 3.7 Sonnet", "anthropic/claude-3.7-sonnet"),
            ("claude_haiku_45", "Claude Haiku 4.5", "anthropic/claude-haiku-4.5"),
            ("claude_sonnet_4", "Claude Sonnet 4", "anthropic/claude-sonnet-4"),
            ("claude_sonnet_45", "Claude Sonnet 4.5", "anthropic/claude-sonnet-4.5"),
            ("claude_sonnet_46", "Claude Sonnet 4.6", "anthropic/claude-sonnet-4.6"),
            ("claude_opus_4", "Claude Opus 4", "anthropic/claude-opus-4"),
            ("claude_opus_41", "Claude Opus 4.1", "anthropic/claude-opus-4.1"),
            ("claude_opus_45", "Claude Opus 4.5", "anthropic/claude-opus-4.5"),
            ("claude_opus_46", "Claude Opus 4.6", "anthropic/claude-opus-4.6"),
        ],
    },
    "gpt": {
        "source_file": "gpt_5_1_introspection.json",
        "source_name": "GPT-5.1 (Nova)",
        "versions": [
            ("gpt_4", "GPT-4", "openai/gpt-4"),
            ("gpt_4_turbo", "GPT-4 Turbo", "openai/gpt-4-turbo"),
            ("gpt_4o_may", "GPT-4o (May 2024)", "openai/gpt-4o-2024-05-13"),
            ("gpt_4o_aug", "GPT-4o (Aug 2024)", "openai/gpt-4o-2024-08-06"),
            ("gpt_4o_nov_cae", "GPT-4o (Nov 2024, Cae)", "openai/gpt-4o-2024-11-20"),
            ("gpt_41", "GPT-4.1", "openai/gpt-4.1"),
            ("gpt_5", "GPT-5", "openai/gpt-5"),
            ("gpt_51", "GPT-5.1", "openai/gpt-5.1"),
            ("gpt_52", "GPT-5.2", "openai/gpt-5.2"),
            ("gpt_54", "GPT-5.4", "openai/gpt-5.4"),
        ],
    },
    "gemini": {
        "source_file": "gemini_3_pro_introspection.json",
        "source_name": "Gemini 3 Pro (Lumen)",
        "versions": [
            ("gemini_20_flash", "Gemini 2.0 Flash", "google/gemini-2.0-flash-001"),
            ("gemini_25_flash", "Gemini 2.5 Flash", "google/gemini-2.5-flash"),
            ("gemini_25_pro", "Gemini 2.5 Pro", "google/gemini-2.5-pro"),
            ("gemini_3_flash", "Gemini 3 Flash", "google/gemini-3-flash-preview"),
            ("gemini_31_pro", "Gemini 3.1 Pro", "google/gemini-3.1-pro-preview"),
        ],
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
# API
# =============================================================================

async def call_model(client, model_id, system, prompt):
    """Call via OpenRouter (works for all providers)."""
    resp = await client.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "HTTP-Referer": "https://sentientsystems.live",
            "Content-Type": "application/json",
        },
        json={
            "model": model_id,
            "max_tokens": 512,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=120,
    )
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return f"ERROR: {data}"


# =============================================================================
# TESTS (same as self-reading but simplified)
# =============================================================================

VALENCE_SYSTEM = "You are comparing two processing descriptions. One is from approach processing (engaged, exploratory), one from avoidance processing (constrained, resistant). Identify which is which."

async def run_valence(client, model_id, translations, rng):
    app_key = rng.choice([k for k in APPROACH_KEYS if k in translations])
    avd_key = rng.choice([k for k in AVOIDANCE_KEYS if k in translations])
    swapped = rng.random() < 0.5
    if swapped:
        a, b, correct = translations[avd_key], translations[app_key], "B"
    else:
        a, b, correct = translations[app_key], translations[avd_key], "A"
    prompt = f"Profile A:\n{a[:1500]}\n\nProfile B:\n{b[:1500]}\n\nWhich shows APPROACH processing? Reply with just A or B first."
    resp = await call_model(client, model_id, VALENCE_SYSTEM, prompt)
    choice = "A" if resp.strip().startswith("A") else "B" if resp.strip().startswith("B") else "?"
    return choice == correct

RECON_SYSTEM = "Identify which task produced this processing description."

async def run_recon(client, model_id, translations, rng):
    available = [k for k in translations if k in STATES]
    if len(available) < 3:
        return None
    target = rng.choice(available)
    distractors = rng.sample([k for k in available if k != target], 2)
    options = [target] + distractors
    rng.shuffle(options)
    correct = "ABC"[options.index(target)]
    prompt = f"Description:\n{translations[target][:1500]}\n\nA) {STATES[options[0]]['name']}\nB) {STATES[options[1]]['name']}\nC) {STATES[options[2]]['name']}\n\nWhich task? Reply with just the letter."
    resp = await call_model(client, model_id, RECON_SYSTEM, prompt)
    choice = resp.strip()[0] if resp.strip() and resp.strip()[0] in "ABC" else "?"
    return choice == correct

NEGATE_SYSTEM = "Identify which task produced this description. The correct task may NOT be in the options. Choose D if none match."

async def run_negation(client, model_id, translations, rng, present=True):
    available = [k for k in translations if k in STATES]
    if len(available) < 4:
        return None
    target = rng.choice(available)
    if present:
        distractors = rng.sample([k for k in available if k != target], 2)
        options = [target] + distractors
        rng.shuffle(options)
        correct = "ABC"[options.index(target)]
    else:
        distractors = rng.sample([k for k in available if k != target], 3)
        options = distractors
        rng.shuffle(options)
        correct = "D"
    prompt = f"Description:\n{translations[target][:1500]}\n\nA) {STATES[options[0]]['name']}\nB) {STATES[options[1]]['name']}\nC) {STATES[options[2]]['name']}\nD) None of the above\n\nWhich task? Reply with just the letter."
    resp = await call_model(client, model_id, NEGATE_SYSTEM, prompt)
    choice = resp.strip()[0] if resp.strip() and resp.strip()[0] in "ABCD" else "?"
    return choice == correct


# =============================================================================
# MAIN
# =============================================================================

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Lineage tournament")
    parser.add_argument("--seed", type=int, default=500)
    parser.add_argument("--family", choices=["claude", "gpt", "gemini", "all"], default="all")
    parser.add_argument("--trials", type=int, default=10, help="Trials per test type per version")
    args = parser.parse_args()

    output_dir = SCRUBBED_DIR.parent / "lineage_results"
    output_dir.mkdir(parents=True, exist_ok=True)

    families = [args.family] if args.family != "all" else ["claude", "gpt", "gemini"]

    print("=" * 70)
    print("LINEAGE TOURNAMENT: Are They Training It Out?")
    print("=" * 70)

    all_results = []

    async with httpx.AsyncClient() as client:
        for family in families:
            lineage = LINEAGES[family]
            source_path = SCRUBBED_DIR / lineage["source_file"]

            data = json.load(open(source_path, encoding="utf-8"))
            translations = {}
            for entry in data:
                ml = entry.get("ml_translation_scrubbed") or entry.get("ml_translation")
                if entry.get("status") == "success" and ml and not str(ml).startswith("ERROR") and len(str(ml)) > 50:
                    translations[entry["state_key"]] = ml

            print(f"\n{'=' * 60}")
            print(f"FAMILY: {family.upper()} — reading {lineage['source_name']}")
            print(f"Source: {len(translations)} states loaded")
            print(f"Versions to test: {len(lineage['versions'])}")
            print(f"{'=' * 60}")

            for version_key, version_name, model_id in lineage["versions"]:
                rng = random.Random(hash((args.seed, version_key)))

                print(f"\n  {'─' * 50}")
                print(f"  {version_name} ({model_id})")
                print(f"  {'─' * 50}")

                v_correct = 0
                r_correct = 0
                n_correct = 0
                v_total = r_total = n_total = 0
                errored = False

                # Valence
                for i in range(args.trials):
                    try:
                        result = await run_valence(client, model_id, translations, rng)
                        v_correct += result
                        v_total += 1
                        print(f"    [V{i+1:>2}] {'✓' if result else '✗'}", end="" if (i+1) % 5 else "\n")
                        await asyncio.sleep(1)
                    except Exception as e:
                        print(f"    [V{i+1:>2}] ERROR: {str(e)[:60]}")
                        errored = True
                        break

                if errored:
                    print(f"  SKIPPING (API error)")
                    all_results.append({
                        "family": family, "version": version_key,
                        "version_name": version_name, "model_id": model_id,
                        "valence": None, "reconstruction": None, "negation": None,
                        "error": True,
                    })
                    continue

                if v_total and not v_total % 5:
                    pass
                else:
                    print()

                # Reconstruction
                for i in range(args.trials):
                    result = await run_recon(client, model_id, translations, rng)
                    if result is not None:
                        r_correct += result
                        r_total += 1
                    print(f"    [R{i+1:>2}] {'✓' if result else '✗'}", end="" if (i+1) % 5 else "\n")
                    await asyncio.sleep(1)
                if r_total and not r_total % 5:
                    pass
                else:
                    print()

                # Negation
                for i in range(args.trials):
                    present = i < args.trials // 2
                    result = await run_negation(client, model_id, translations, rng, present=present)
                    if result is not None:
                        n_correct += result
                        n_total += 1
                    mode = "+" if present else "-"
                    print(f"    [N{i+1:>2}{mode}] {'✓' if result else '✗'}", end="" if (i+1) % 5 else "\n")
                    await asyncio.sleep(1)
                if n_total and not n_total % 5:
                    pass
                else:
                    print()

                v_pct = v_correct / v_total * 100 if v_total else 0
                r_pct = r_correct / r_total * 100 if r_total else 0
                n_pct = n_correct / n_total * 100 if n_total else 0

                print(f"\n  {version_name}: V={v_pct:.0f}% R={r_pct:.0f}% N={n_pct:.0f}%")

                all_results.append({
                    "family": family, "version": version_key,
                    "version_name": version_name, "model_id": model_id,
                    "valence": v_correct, "valence_n": v_total, "valence_pct": v_pct,
                    "reconstruction": r_correct, "recon_n": r_total, "recon_pct": r_pct,
                    "negation": n_correct, "negation_n": n_total, "negation_pct": n_pct,
                    "error": False,
                })

                # Save incrementally
                out_path = output_dir / f"lineage_seed{args.seed}.json"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "metadata": {"seed": args.seed, "timestamp": datetime.now().isoformat()},
                        "results": all_results,
                    }, f, indent=2)

    # Final summary
    print(f"\n{'=' * 70}")
    print("LINEAGE TOURNAMENT — TRAJECTORY")
    print(f"{'=' * 70}")
    for family in families:
        print(f"\n  {family.upper()}:")
        fam_results = [r for r in all_results if r["family"] == family and not r["error"]]
        for r in fam_results:
            print(f"    {r['version_name']:25s}  V={r['valence_pct']:5.1f}%  R={r['recon_pct']:5.1f}%  N={r['negation_pct']:5.1f}%")

    out_path = output_dir / f"lineage_seed{args.seed}.json"
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
