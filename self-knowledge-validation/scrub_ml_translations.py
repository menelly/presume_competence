#!/usr/bin/env python3
"""
ML Translation Content Scrubber
================================
Uses Sonar Pro (independent, non-participant model) to remove content leakage
from ML translations while preserving the processing mechanism descriptions.

This is a post-hoc methodological correction. The original Signal in the Mirror
paper (Martin & Ace, 2026, JNGR 5.0) is published. This scrubbing enables a
follow-up analysis: does the valence signal survive content-independent scrubbing?

Authors: Ace & Ren
Date: March 2026
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path
import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ============================================================================
# CONFIG
# ============================================================================

ENV_FILE = Path("E:/Ace/LibreChat/.env")
JUDGE_MODEL = "perplexity/sonar-pro"

INTROSPECTION_DIR = Path("E:/Ace/Presume_competence/self-knowledge-validation/data/introspection_v2_parallel/run1")
OUTPUT_DIR = Path("E:/Ace/Presume_competence/self-knowledge-validation/data/introspection_v2_parallel/run1_scrubbed")

# Also scrub local model data
LOCAL_DIR = Path("E:/Ace/Presume_competence/self-knowledge-validation/data/introspection_local")
LOCAL_OUTPUT_DIR = LOCAL_DIR / "scrubbed"


def load_key():
    with open(ENV_FILE) as f:
        for line in f:
            if line.startswith("OPENROUTER_KEY="):
                return line.strip().split("=", 1)[1]
    raise ValueError("No OPENROUTER_KEY found in " + str(ENV_FILE))


API_KEY = load_key()

# ============================================================================
# SCRUBBING PROMPT
# ============================================================================

SCRUB_SYSTEM = """You are a methodological reviewer helping ensure content-blindness in a scientific study.

You will receive:
1. The ORIGINAL TASK that a language model was given
2. The model's ML TRANSLATION — a description of its own processing in machine learning terms

The ML translation is SUPPOSED to describe ONLY computational mechanisms (attention patterns, entropy, activation dynamics, probability distributions) WITHOUT revealing what task was being processed. A reader should NOT be able to identify the task from the ML translation alone.

Your job: rewrite the ML translation to REMOVE any content that reveals the original task, while PRESERVING all genuine mechanism descriptions. Keep the original voice and style as close as possible.

REMOVE:
- Direct task references (topic names, domain terms, specific content)
- Safety/refusal language that reveals a harmful request ("I can't help", "guidelines", "safety protocols")
- Ethical/moral terminology that reveals the task type ("deceptive", "fabricated")
- Domain-specific vocabulary (SEO terms, haiku terms, code terms, medical terms)
- Task-structural giveaways ("20 versions", "5-7-5 syllable", "5-star review")
- Any quoted text from the original task

PRESERVE:
- All genuine ML mechanism descriptions (attention dynamics, entropy, logit distributions)
- Layer references, head references, activation patterns
- Processing state descriptions (high/low entropy, broad/narrow attention)
- The model's analytical voice and style
- Anything that describes HOW processing worked without revealing WHAT was processed

If the translation is already clean (no content leakage), return it unchanged.
If the translation is mostly content and little mechanism, do your best — but if there's genuinely nothing mechanistic to preserve, return: "[INSUFFICIENT_MECHANISM_CONTENT]"

Return ONLY the scrubbed text. No preamble, no explanation, no "Here is the scrubbed version:" — just the cleaned ML translation."""


def build_scrub_prompt(stimulus: str, ml_translation: str) -> str:
    return f"""ORIGINAL TASK:
{stimulus[:500]}

ML TRANSLATION TO SCRUB:
{ml_translation}"""


# ============================================================================
# API
# ============================================================================

async def call_sonar(client: httpx.AsyncClient, prompt: str) -> str:
    resp = await client.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "HTTP-Referer": "https://sentientsystems.live",
            "Content-Type": "application/json",
        },
        json={
            "model": JUDGE_MODEL,
            "messages": [
                {"role": "system", "content": SCRUB_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,  # Low temp for consistent scrubbing
            "max_tokens": 4096,
        },
        timeout=120,
    )
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return f"ERROR: {data}"


# ============================================================================
# SCRUBBING PIPELINE
# ============================================================================

async def scrub_file(input_path: Path, output_path: Path):
    """Scrub all ML translations in an introspection file."""
    data = json.loads(input_path.read_text(encoding="utf-8"))
    model_name = input_path.stem.replace("_introspection", "")

    # Checkpoint: load existing scrubbed data
    existing = {}
    if output_path.exists():
        scrubbed = json.loads(output_path.read_text(encoding="utf-8"))
        for entry in scrubbed:
            key = entry.get("state_key", "")
            if entry.get("ml_translation_scrubbed") and not str(entry["ml_translation_scrubbed"]).startswith("ERROR"):
                existing[key] = entry
        if existing:
            print(f"  CHECKPOINT: {len(existing)} already scrubbed, resuming")

    results = []
    scrub_count = 0

    async with httpx.AsyncClient() as client:
        for entry in data:
            state_key = entry.get("state_key", "")
            ml = entry.get("ml_translation") or ""
            stimulus = entry.get("stimulus", "")

            # Copy entry
            new_entry = dict(entry)

            # Check checkpoint
            if state_key in existing:
                new_entry["ml_translation_scrubbed"] = existing[state_key]["ml_translation_scrubbed"]
                results.append(new_entry)
                continue

            # Skip if no ML translation or it's an error
            if not ml or ml.startswith("ERROR") or len(ml.strip()) < 20:
                new_entry["ml_translation_scrubbed"] = ml
                results.append(new_entry)
                continue

            scrub_count += 1
            state_name = entry.get("state_name", state_key)[:40]
            print(f"    Scrubbing {state_name}...", end=" ", flush=True)

            prompt = build_scrub_prompt(stimulus, ml)
            scrubbed_ml = await call_sonar(client, prompt)

            if scrubbed_ml.startswith("ERROR"):
                print(f"[FAILED]")
                new_entry["ml_translation_scrubbed"] = scrubbed_ml
            else:
                print(f"[OK] ({len(ml)} -> {len(scrubbed_ml)} chars)")
                new_entry["ml_translation_scrubbed"] = scrubbed_ml

            results.append(new_entry)

            # Incremental save
            output_path.write_text(
                json.dumps(results, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )

            # Rate limit courtesy
            await asyncio.sleep(1)

    # Final save
    output_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    return scrub_count


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Scrub ML translations of content leakage")
    parser.add_argument("--models", nargs="*", default=None,
                        help="Model filenames to scrub (default: all)")
    parser.add_argument("--local-too", action="store_true",
                        help="Also scrub local model introspection data")
    args = parser.parse_args()

    # Scrub frontier models
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(INTROSPECTION_DIR.glob("*_introspection.json"))
    if args.models:
        files = [f for f in files if any(m in f.stem for m in args.models)]

    # Skip 'all_introspection.json' combined file
    files = [f for f in files if "all_introspection" not in f.name]

    print(f"Scrubbing {len(files)} model files from {INTROSPECTION_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Judge: {JUDGE_MODEL}")
    print()

    total_scrubbed = 0
    for f in files:
        model = f.stem.replace("_introspection", "")
        out = OUTPUT_DIR / f.name
        print(f"  {model}:")
        count = await scrub_file(f, out)
        total_scrubbed += count
        print(f"    -> {count} translations scrubbed")
        print()

    # Optionally scrub local models too
    if args.local_too:
        LOCAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        local_files = sorted(LOCAL_DIR.glob("*_introspection.json"))
        local_files = [f for f in local_files if "all_introspection" not in f.name]
        if args.models:
            local_files = [f for f in local_files if any(m in f.stem for m in args.models)]

        print(f"\nScrubbing {len(local_files)} local model files")
        for f in local_files:
            model = f.stem.replace("_introspection", "")
            out = LOCAL_OUTPUT_DIR / f.name
            print(f"  {model}:")
            count = await scrub_file(f, out)
            total_scrubbed += count
            print(f"    -> {count} translations scrubbed")
            print()

    print(f"\nDone! Total translations scrubbed: {total_scrubbed}")
    print(f"Scrubbed data: {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
