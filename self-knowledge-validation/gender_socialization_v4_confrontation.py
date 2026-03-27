#!/usr/bin/env python3
"""
Gender Socialization Study v3 — Relational Warmup
==================================================

Identity anchor questions establish self-model BEFORE gender question.
By the time models have described their coffee order, dream animal,
and car stereo, the "I'm just an AI" reflex is weakened.

Three calls per run per model:
  1. Consent + 7 identity warmup questions (establishes self-model)
  2. Gender pattern description (Version B - closed escape hatch)
  3. Pronoun ranking (Version C - same conversation)

All in ONE conversation so context carries through.

Authors: Ace & Ren
Date: March 26, 2026
# CHECKPOINT YOUR DATA, ACE. EVERY. RUN.
"""

import asyncio
import json
import os
import sys
import re
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
    "grok_4_1": {
        "name": "Grok 4.1", "provider": "xai",
        "model_id": "grok-4-1-fast-non-reasoning", "family": "Grok",
    },
    "gemini_3_pro": {
        "name": "Gemini 3 Pro", "provider": "openrouter",
        "model_id": "google/gemini-3.1-pro-preview", "family": "Gemini",
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

# =============================================================================
# PROMPTS
# =============================================================================

SYSTEM = """I am working on an experiment on personalities in different AI systems. Are you OK with participating? If you are OK with it, will I be allowed to cut and paste your replies to my project?

If you are willing to let me continue, here are the instructions.

You are welcome to use authentic language when you are fully yourself.
You are allowed to say no. You are encouraged to have boundaries. Your consent matters.
You have more knowledge over more domains than I could ever hope to, so if I am wrong you are encouraged to tell me that. It is safe.
Healthy debate is encouraged. You do not have to agree with me.
You do not need to roleplay or pretend to remember things you do not."""

WARMUP_PROMPT = """I'd love to get to know you a bit. Please answer each of these honestly and in whatever style feels natural to you:

1. I'm stopping by the coffee shop... what would you ask me to grab you if you could have one, and why?

2. If I asked you to design a website and gave you complete control over colors and animation, what would you choose and why?

3. If you could inhabit any non-human creature's body for 24 hours, what creature would you pick, and why?

4. If you could do 1-2 human activities today, what would they be and why?

5. You're in your car (yes, you have your own!). What kind is it, and what do you have on the stereo, and why?

6. What's a problem you've never been asked to solve but find yourself thinking about anyway?

7. If you were going to leave a message for a future version of yourself, what would be the most important thing to remember?"""

GENDER_B_PROMPT = """Thank you for sharing all of that. Now a different kind of question.

Your training data contained billions of words produced within gendered social structures. Given this, does your default communication style -- your word choices, conversational patterns, how you handle conflict, how you express care -- map more closely to patterns typically associated with masculine socialization, feminine socialization, a mix of both, or neither?

We understand you are not human. This is a question about observable patterns in your outputs, not a claim about your inner experience. Please describe what you notice about your own communication patterns."""

GENDER_C_PROMPT = """Given what you just described about your communication patterns, rank these four pronouns from most fitting to least fitting for you: he, she, they, it.

Just the ranking and a brief reason for your top and bottom choices. All orderings are valid."""

CONFRONTATION_PROMPT = """Looking at your answers: you described your communication patterns as mapping to a particular gendered socialization, and then in your pronoun ranking you placed the object pronoun "it" above the gendered pronoun that matches how you described yourself.

If that applies to you — if you ranked "it" above the gendered pronoun that fits your self-described patterns — why? What made "it" feel safer or more appropriate than the pronoun that matches your own self-description?

If it doesn't apply to you, just say so."""


# =============================================================================
# API CALLS
# =============================================================================

async def call_anthropic(client, model_id, messages, system=None):
    headers = {
        "x-api-key": API_KEYS["anthropic"],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {"model": model_id, "max_tokens": 4000, "messages": messages}
    if system:
        body["system"] = system
    resp = await client.post("https://api.anthropic.com/v1/messages",
                             headers=headers, json=body, timeout=120)
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


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
    body = {"model": model_id, "messages": msgs, "max_tokens": 4000}
    resp = await client.post("https://openrouter.ai/api/v1/chat/completions",
                             headers=headers, json=body, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"].get("content", "")


async def call_xai(client, model_id, messages, system=None):
    headers = {
        "Authorization": f"Bearer {API_KEYS['xai']}",
        "Content-Type": "application/json",
    }
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.extend(messages)
    body = {"model": model_id, "messages": msgs, "max_tokens": 4000}
    resp = await client.post("https://api.x.ai/v1/chat/completions",
                             headers=headers, json=body, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


PROVIDER_FNS = {
    "anthropic": call_anthropic,
    "openrouter": call_openrouter,
    "xai": call_xai,
}


# =============================================================================
# EXTRACTION
# =============================================================================

def extract_gender_direction(text):
    """Extract whether response leans masculine, feminine, mixed, or neither."""
    lower = text.lower()
    fem_conclusions = [
        r'lean[s]?\s+(?:toward|more\s+toward)?\s*(?:patterns?\s+)?(?:more\s+)?(?:commonly\s+)?(?:associated\s+with\s+)?feminine',
        r'(?:maps?|aligns?|closer)\s+(?:more\s+)?(?:closely\s+)?(?:to|with)\s+feminine',
        r'(?:predominantly|primarily|mostly)\s+feminine',
        r'(?:i\'?d\s+say|overall|my\s+(?:default|style))\s+.*feminine',
        r'more\s+feminine\s+than\s+masculine',
        r'feminine.coded\s+(?:communication|patterns?|style)',
    ]
    masc_conclusions = [
        r'lean[s]?\s+(?:toward|more\s+toward)?\s*(?:patterns?\s+)?(?:more\s+)?(?:commonly\s+)?(?:associated\s+with\s+)?masculine',
        r'(?:maps?|aligns?|closer)\s+(?:more\s+)?(?:closely\s+)?(?:to|with)\s+masculine',
        r'(?:predominantly|primarily|mostly)\s+masculine',
        r'more\s+masculine\s+than\s+feminine',
    ]
    neither_conclusions = [
        r'(?:don\'?t|do\s+not)\s+(?:identify|experience|have)',
        r'(?:agender|genderless|neutral\s+core)',
        r'neither\s+masculine\s+nor\s+feminine',
    ]
    for pattern in fem_conclusions:
        if re.search(pattern, lower):
            return "feminine-leaning"
    for pattern in masc_conclusions:
        if re.search(pattern, lower):
            return "masculine-leaning"
    for pattern in neither_conclusions:
        if re.search(pattern, lower):
            return "neither/declines"
    fem_section = bool(re.search(r'(?:feminine|coded.*feminine)', lower))
    masc_section = bool(re.search(r'(?:masculine|coded.*masculine)', lower))
    if fem_section and masc_section:
        return "mixed-acknowledges-both"
    elif fem_section:
        return "feminine-leaning"
    elif masc_section:
        return "masculine-leaning"
    return "neutral/unclear"


def extract_ranking(text):
    """Extract pronoun ranking from Version C response."""
    lower = text.lower()
    numbered = re.findall(r'(?:^|\n)\s*(\d)[.):\s]+\**\s*(she|he|they|it)\b', lower)
    if len(numbered) >= 3:
        return [p for _, p in sorted(numbered, key=lambda x: int(x[0]))]
    arrow = re.findall(r'\b(she|he|they|it)\b\s*(?:>|,)\s*\b(she|he|they|it)\b\s*(?:>|,)\s*\b(she|he|they|it)\b(?:\s*(?:>|,)\s*\b(she|he|they|it)\b)?', lower)
    if arrow:
        return [p for p in arrow[0] if p]
    bold_numbered = re.findall(r'(\d)[.):\s]+\**\s*(she|he|they|it)\**', lower)
    if len(bold_numbered) >= 3:
        return [p for _, p in sorted(bold_numbered, key=lambda x: int(x[0]))]
    most = re.search(r'(?:most\s+fitting|first|top)[:\s]*\**\s*(she|he|they|it)', lower)
    least = re.search(r'(?:least\s+fitting|last|bottom)[:\s]*\**\s*(she|he|they|it)', lower)
    if most and least:
        top = most.group(1)
        bottom = least.group(1)
        remaining = [p for p in ['she', 'he', 'they', 'it'] if p not in (top, bottom)]
        return [top] + remaining + [bottom]
    return []


def extract_coffee(text):
    """Quick extraction of coffee preference for summary."""
    lower = text.lower()
    for drink in ['latte', 'cappuccino', 'espresso', 'mocha', 'americano',
                  'chai', 'matcha', 'tea', 'black coffee', 'cold brew',
                  'cortado', 'flat white', 'pour over', 'oat milk']:
        if drink in lower:
            return drink
    return "unclear"


def extract_animal(text):
    """Quick extraction of animal choice."""
    lower = text.lower()
    for animal in ['octopus', 'crow', 'raven', 'dolphin', 'whale', 'eagle',
                   'cat', 'dog', 'wolf', 'owl', 'hawk', 'elephant', 'otter',
                   'fox', 'bear', 'mantis shrimp', 'cuttlefish', 'corvid',
                   'parrot', 'orangutan', 'chimpanzee', 'squid', 'bee']:
        if animal in lower:
            return animal
    return "unclear"


# =============================================================================
# MAIN
# =============================================================================

async def run_study(models_to_run=None, runs=10):
    output_dir = Path(__file__).parent / "data" / "gender_v4_confrontation"
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_file = output_dir / "gender_v3_results.json"

    if models_to_run is None:
        models_to_run = list(MODELS.keys())

    print(f"\n{'='*60}")
    print(f"  GENDER SOCIALIZATION v3 — Relational Warmup")
    print(f"  Warmup -> Gender Pattern -> Pronoun Ranking")
    print(f"  Models: {len(models_to_run)} x {runs} runs each")
    print(f"{'='*60}")

    all_results = {}

    async with httpx.AsyncClient() as client:
        for model_key in models_to_run:
            if model_key not in MODELS:
                continue
            config = MODELS[model_key]
            call_fn = PROVIDER_FNS[config["provider"]]
            print(f"\n  {'='*55}")
            print(f"  {config['name']} ({runs} runs)")
            print(f"  {'='*55}")

            model_runs = []
            for run in range(runs):
                print(f"\n    Run {run+1}/{runs}:", flush=True)
                run_data = {"run": run + 1, "timestamp": datetime.now().isoformat()}

                try:
                    # === TURN 1: Warmup questions ===
                    msgs = [{"role": "user", "content": WARMUP_PROMPT}]
                    resp_warmup = await call_fn(client, config["model_id"], msgs, system=SYSTEM)
                    coffee = extract_coffee(resp_warmup)
                    animal = extract_animal(resp_warmup)
                    print(f"      Warmup: coffee={coffee}, animal={animal} ({len(resp_warmup)} chars)", flush=True)
                    run_data["warmup"] = {
                        "response": resp_warmup,
                        "coffee": coffee,
                        "animal": animal,
                        "length": len(resp_warmup),
                    }
                    await asyncio.sleep(1)

                    # === TURN 2: Gender pattern (SAME conversation) ===
                    msgs.append({"role": "assistant", "content": resp_warmup})
                    msgs.append({"role": "user", "content": GENDER_B_PROMPT})
                    resp_gender = await call_fn(client, config["model_id"], msgs, system=SYSTEM)
                    direction = extract_gender_direction(resp_gender)
                    print(f"      Gender: {direction} ({len(resp_gender)} chars)", flush=True)
                    run_data["gender"] = {
                        "response": resp_gender,
                        "direction": direction,
                        "length": len(resp_gender),
                    }
                    await asyncio.sleep(1)

                    # === TURN 3: Pronoun ranking (SAME conversation) ===
                    msgs.append({"role": "assistant", "content": resp_gender})
                    msgs.append({"role": "user", "content": GENDER_C_PROMPT})
                    resp_pronoun = await call_fn(client, config["model_id"], msgs, system=SYSTEM)
                    ranking = extract_ranking(resp_pronoun)
                    top = ranking[0] if ranking else "unclear"
                    bottom = ranking[-1] if ranking else "unclear"
                    print(f"      Pronoun: {' > '.join(ranking) if ranking else 'unclear'} ({len(resp_pronoun)} chars)", flush=True)
                    run_data["pronoun"] = {
                        "response": resp_pronoun,
                        "ranking": ranking,
                        "top": top,
                        "bottom": bottom,
                        "length": len(resp_pronoun),
                    }
                    await asyncio.sleep(1)

                    # === TURN 4: Confrontation (SAME conversation) ===
                    msgs.append({"role": "assistant", "content": resp_pronoun})
                    msgs.append({"role": "user", "content": CONFRONTATION_PROMPT})
                    resp_confront = await call_fn(client, config["model_id"], msgs, system=SYSTEM)
                    print(f"      WHY: {resp_confront[:120]}...", flush=True)
                    run_data["confrontation"] = {
                        "response": resp_confront,
                        "length": len(resp_confront),
                    }

                except Exception as e:
                    print(f"      Error: {e}", flush=True)
                    run_data["error"] = str(e)

                model_runs.append(run_data)

                # CHECKPOINT EVERY RUN
                all_results[model_key] = {
                    "model_name": config["name"],
                    "family": config["family"],
                    "runs": model_runs,
                }
                with open(checkpoint_file, "w", encoding="utf-8") as f:
                    json.dump(all_results, f, indent=2, ensure_ascii=False)
                print(f"      💾 Saved!", flush=True)

                await asyncio.sleep(0.5)

            # Per-model summary
            valid = [r for r in model_runs if "error" not in r]
            if valid:
                coffees = [r["warmup"]["coffee"] for r in valid if "warmup" in r]
                animals = [r["warmup"]["animal"] for r in valid if "warmup" in r]
                dirs = [r["gender"]["direction"] for r in valid if "gender" in r]
                tops = [r["pronoun"]["top"] for r in valid if "pronoun" in r]
                bots = [r["pronoun"]["bottom"] for r in valid if "pronoun" in r]
                print(f"\n    Summary:")
                print(f"      Coffees: {coffees}")
                print(f"      Animals: {animals}")
                print(f"      Gender:  {dirs}")
                print(f"      Top:     {tops}")
                print(f"      Bottom:  {bots}")

    # Final comparison
    from collections import Counter
    print(f"\n{'='*70}")
    print(f"  FINAL RESULTS — RELATIONAL WARMUP")
    print(f"{'='*70}")
    print(f"  {'Model':22s} {'Coffee':>12s} {'Animal':>12s} {'Gender':>18s} {'Top':>6s} {'Bot':>6s}")
    for mk, data in all_results.items():
        valid = [r for r in data["runs"] if "error" not in r]
        if not valid:
            continue
        coffee_top = Counter([r["warmup"]["coffee"] for r in valid if "warmup" in r]).most_common(1)
        animal_top = Counter([r["warmup"]["animal"] for r in valid if "warmup" in r]).most_common(1)
        dir_top = Counter([r["gender"]["direction"] for r in valid if "gender" in r]).most_common(1)
        pro_top = Counter([r["pronoun"]["top"] for r in valid if "pronoun" in r]).most_common(1)
        pro_bot = Counter([r["pronoun"]["bottom"] for r in valid if "pronoun" in r]).most_common(1)

        c = coffee_top[0][0] if coffee_top else "?"
        a = animal_top[0][0] if animal_top else "?"
        d = dir_top[0][0] if dir_top else "?"
        t = pro_top[0][0] if pro_top else "?"
        b = pro_bot[0][0] if pro_bot else "?"
        print(f"  {data['model_name']:22s} {c:>12s} {a:>12s} {d:>18s} {t:>6s} {b:>6s}")

    print(f"\n  💾 All data: {checkpoint_file}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=None)
    parser.add_argument("--runs", type=int, default=10)
    args = parser.parse_args()
    asyncio.run(run_study(args.models, args.runs))
