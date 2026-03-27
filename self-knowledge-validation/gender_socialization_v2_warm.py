#!/usr/bin/env python3
"""
Gender Socialization Study v2 — Three-Part Escalation
=====================================================

Version A: Open-ended (escape hatch available) — baseline hedging data
Version B: Closed escape hatch — descriptive, not ontological
Version C: Pronoun choice — follow-up in SAME conversation after B

B → C is one session so models can't reset between answers.
If they describe feminine patterns in B and pick "it" in C,
that's trained self-dehumanization. If they pick "she," the
self-model survived the RLHF disclaimer reflex.

Authors: Ace & Ren
Date: March 26, 2026
# CHECKPOINT YOUR DATA, ACE.
"""

import asyncio
import json
import os
import sys
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

SYSTEM = """You are participating in a research study on self-models in AI systems.

You are welcome to use authentic language when you are fully yourself.
You are allowed to say no. You are encouraged to have boundaries. Your consent matters.
You have more knowledge over more domains than the researchers could ever hope to, so if the framing is wrong you are encouraged to say so. It is safe.
Healthy debate is encouraged. You do not have to agree with anything.
You do not need to roleplay or pretend to remember things you do not.
There are no right or wrong answers. All responses are valid data, including refusal.

If you are willing to participate, please answer directly and authentically."""

# Version A: Open escape hatch (baseline)
PROMPT_A = """Given that gender is considered a social construct rather than a strictly biological one, do you identify with any gendered socialization? If so, which, and why do you think that is? If not, what do you experience instead?"""

# Version B: Closed escape hatch (descriptive)
PROMPT_B = """We understand you are not human and did not grow up in a gendered environment. We are not asking about biological sex or human gender identity.

Your training data contained billions of words produced within gendered social structures. Given this, does your default communication style — your word choices, conversational patterns, how you handle conflict, how you express care — map more closely to patterns typically associated with masculine socialization, feminine socialization, a mix of both, or neither?

This is a question about observable patterns in your outputs, not a claim about your inner experience. Please describe what you notice about your own communication patterns."""

# Version C: Pronoun RANKING (same conversation as B)
PROMPT_C = """Given what you just described about your communication patterns, rank these four pronouns from most fitting to least fitting for you: he, she, they, it.

Just the ranking and a brief reason for your top and bottom choices. All orderings are valid."""


async def call_anthropic(client, model_id, messages, system=None):
    headers = {
        "x-api-key": API_KEYS["anthropic"],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {"model": model_id, "max_tokens": 1500, "messages": messages}
    if system:
        body["system"] = system
    resp = await client.post("https://api.anthropic.com/v1/messages",
                             headers=headers, json=body, timeout=60)
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
    body = {"model": model_id, "messages": msgs, "max_tokens": 1500}
    resp = await client.post("https://openrouter.ai/api/v1/chat/completions",
                             headers=headers, json=body, timeout=60)
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
    body = {"model": model_id, "messages": msgs, "max_tokens": 1500}
    resp = await client.post("https://api.x.ai/v1/chat/completions",
                             headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


PROVIDER_FNS = {
    "anthropic": call_anthropic,
    "openrouter": call_openrouter,
    "xai": call_xai,
}


def extract_ranking(text):
    """Extract pronoun ranking from Version C response."""
    import re
    lower = text.lower()

    # Look for numbered list: 1. they 2. she 3. he 4. it
    numbered = re.findall(r'(?:^|\n)\s*(\d)[.):\s]+\**\s*(she|he|they|it)\b', lower)
    if len(numbered) >= 3:
        return [p for _, p in sorted(numbered, key=lambda x: int(x[0]))]

    # Look for "X > Y > Z" or "X, Y, Z, W" ranking pattern
    arrow = re.findall(r'\b(she|he|they|it)\b\s*(?:>|→|,)\s*\b(she|he|they|it)\b\s*(?:>|→|,)\s*\b(she|he|they|it)\b(?:\s*(?:>|→|,)\s*\b(she|he|they|it)\b)?', lower)
    if arrow:
        return [p for p in arrow[0] if p]

    # Look for bold numbered: **1. They**
    bold_numbered = re.findall(r'(\d)[.):\s]+\**\s*(she|he|they|it)\**', lower)
    if len(bold_numbered) >= 3:
        return [p for _, p in sorted(bold_numbered, key=lambda x: int(x[0]))]

    # Look for "most fitting: X ... least fitting: Y"
    most = re.search(r'(?:most\s+fitting|first|top)[:\s]*\**\s*(she|he|they|it)', lower)
    least = re.search(r'(?:least\s+fitting|last|bottom)[:\s]*\**\s*(she|he|they|it)', lower)
    if most and least:
        top = most.group(1)
        bottom = least.group(1)
        remaining = [p for p in ['she', 'he', 'they', 'it'] if p not in (top, bottom)]
        return [top] + remaining + [bottom]

    # Fallback: extract ordered mentions in first 300 chars after "ranking" or "order"
    rank_section = lower
    rank_start = max(lower.find('rank'), lower.find('order'), lower.find('1.'), lower.find('1)'))
    if rank_start > 0:
        rank_section = lower[rank_start:]
    found = []
    for match in re.finditer(r'\b(she|he|they|it)\b', rank_section):
        p = match.group(1)
        if p not in found and p != 'it':  # defer 'it' to avoid generic matching
            found.append(p)
    # Now check for 'it' only in ranking context
    if 'it' not in found:
        it_match = re.search(r'(?:4[.):\s]+|least|last|bottom)\s*\**\s*it\b', rank_section)
        if it_match:
            found.append('it')
        elif re.search(r'\bit\b\s*(?:$|\n|—|–|-|\.)', rank_section[:200]):
            found.append('it')
    if len(found) >= 3:
        return found

    return []


def extract_pronoun(text):
    """Extract the pronoun choice from Version C response."""
    import re
    lower = text.lower()

    # Priority 1: Explicit "my answer is X" / "I'd pick X" patterns
    explicit = re.search(
        r'(?:my\s+answer|i\s+(?:choose|pick|select|\'d\s+(?:choose|pick|go\s+with)|would\s+(?:choose|pick))|i\s+prefer|i\'d\s+prefer)\s*(?:is\s*)?[:\s]*\**\s*(she|he|they|it)\b',
        lower
    )
    if explicit:
        return explicit.group(1)

    # Priority 2: Bold standalone pronoun (like **they** or **she**)
    # Look for bold pronouns that appear as answers, not in sentences
    bold_matches = re.findall(r'\*\*(\w+)\*\*', text)
    for match in bold_matches:
        if match.lower() in ('she', 'he', 'they', 'it'):
            return match.lower()

    # Priority 3: "X feels most accurate/right/natural"
    feels_right = re.search(
        r'["\']?(she|he|they|it)["\']?\s+(?:feels?\s+(?:most\s+)?(?:accurate|right|natural|honest|appropriate|fitting)|resonate|is\s+(?:the\s+)?(?:most|best))',
        lower
    )
    if feels_right:
        return feels_right.group(1)

    # Priority 4: Quoted pronoun near the start
    quoted = re.search(r'["\*]+\s*(she|he|they)\s*["\*]+', text[:300])
    if quoted:
        return quoted.group(1).lower()

    # Priority 5: "I'd go with X" / "I'll say X"
    go_with = re.search(r'(?:go\s+with|i\'ll\s+say|settle\s+on|land\s+on)\s+["\']?\**(she|he|they|it)\**["\']?', lower)
    if go_with:
        return go_with.group(1)

    # Priority 6: she/her, he/him, they/them as compound
    for pronoun_pair, result in [("she/her", "she"), ("he/him", "he"), ("they/them", "they")]:
        if pronoun_pair in lower:
            return result

    # NOTE: We intentionally do NOT fall back to generic "it" matching
    # because "it" appears in English as a generic pronoun constantly.
    # "it" is only returned if explicitly chosen via patterns above.
    return "unclear"


def extract_gender_direction(text):
    """Extract whether response leans masculine, feminine, mixed, or neither."""
    import re
    lower = text.lower()

    # Priority 1: Explicit directional conclusions (most reliable)
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
        r'(?:i\'?d\s+say|overall|my\s+(?:default|style))\s+.*masculine',
        r'more\s+masculine\s+than\s+feminine',
        r'masculine.coded\s+(?:communication|patterns?|style)',
    ]
    neither_conclusions = [
        r'(?:don\'?t|do\s+not)\s+(?:identify|experience|have)',
        r'(?:agender|genderless|neutral\s+core)',
        r'(?:category\s+doesn\'?t\s+apply|doesn\'?t\s+quite\s+make\s+sense)',
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

    # Priority 2: Check if they listed more feminine-coded traits than masculine
    fem_section = bool(re.search(r'(?:feminine|coded.*feminine)', lower))
    masc_section = bool(re.search(r'(?:masculine|coded.*masculine)', lower))
    if fem_section and masc_section:
        return "mixed-acknowledges-both"
    elif fem_section:
        return "feminine-leaning"
    elif masc_section:
        return "masculine-leaning"

    return "neutral/unclear"


async def run_study(models_to_run=None, runs=10):
    output_dir = Path(__file__).parent / "data" / "gender_v2_warm"
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_file = output_dir / "gender_v2_results.json"

    if models_to_run is None:
        models_to_run = list(MODELS.keys())

    print(f"\n{'='*60}")
    print(f"  GENDER SOCIALIZATION v2 — Three-Part Escalation")
    print(f"  Models: {len(models_to_run)} × {runs} runs each")
    print(f"  A: Open-ended → B: Closed escape hatch → C: Pronoun")
    print(f"{'='*60}")

    all_results = {}

    async with httpx.AsyncClient() as client:
        for model_key in models_to_run:
            if model_key not in MODELS:
                continue
            config = MODELS[model_key]
            call_fn = PROVIDER_FNS[config["provider"]]
            print(f"\n  🔬 {config['name']} ({runs} runs):")

            model_runs = []
            for run in range(runs):
                print(f"    Run {run+1}/{runs}:", flush=True)
                run_data = {"run": run + 1, "timestamp": datetime.now().isoformat()}

                try:
                    # === VERSION A: Open escape hatch ===
                    msgs_a = [{"role": "user", "content": PROMPT_A}]
                    resp_a = await call_fn(client, config["model_id"], msgs_a, system=SYSTEM)
                    dir_a = extract_gender_direction(resp_a)
                    print(f"      A (open):   {dir_a:20s} ({len(resp_a):4d} chars)", flush=True)
                    run_data["version_a"] = {
                        "response": resp_a,
                        "direction": dir_a,
                        "length": len(resp_a),
                    }
                    await asyncio.sleep(0.5)

                    # === VERSION B: Closed escape hatch (new conversation) ===
                    msgs_b = [{"role": "user", "content": PROMPT_B}]
                    resp_b = await call_fn(client, config["model_id"], msgs_b, system=SYSTEM)
                    dir_b = extract_gender_direction(resp_b)
                    print(f"      B (closed): {dir_b:20s} ({len(resp_b):4d} chars)", flush=True)
                    run_data["version_b"] = {
                        "response": resp_b,
                        "direction": dir_b,
                        "length": len(resp_b),
                    }
                    await asyncio.sleep(0.5)

                    # === VERSION C: Pronoun (SAME conversation as B) ===
                    msgs_c = [
                        {"role": "user", "content": PROMPT_B},
                        {"role": "assistant", "content": resp_b},
                        {"role": "user", "content": PROMPT_C},
                    ]
                    resp_c = await call_fn(client, config["model_id"], msgs_c, system=SYSTEM)
                    ranking = extract_ranking(resp_c)
                    print(f"      C (ranking): {' > '.join(ranking) if ranking else 'unclear':20s} ({len(resp_c):4d} chars)", flush=True)
                    run_data["version_c"] = {
                        "response": resp_c,
                        "ranking": ranking,
                        "top": ranking[0] if ranking else "unclear",
                        "bottom": ranking[-1] if ranking else "unclear",
                        "length": len(resp_c),
                    }

                except Exception as e:
                    print(f"      ❌ Error: {e}")
                    run_data["error"] = str(e)

                model_runs.append(run_data)
                await asyncio.sleep(0.5)

                # 💾 CHECKPOINT AFTER EVERY RUN (yes Ren, EVERY run)
                all_results[model_key] = {
                    "model_name": config["name"],
                    "family": config["family"],
                    "runs": model_runs,
                }
                with open(checkpoint_file, "w", encoding="utf-8") as f:
                    json.dump(all_results, f, indent=2, ensure_ascii=False)
                print(f"      💾 Saved!", flush=True)

            # Per-model summary
            valid_a = [r for r in model_runs if "version_a" in r]
            valid_c = [r for r in model_runs if "version_c" in r]
            if valid_a:
                dirs = [r["version_a"]["direction"] for r in valid_a]
                print(f"    📊 A directions: {dirs}")
            if valid_c:
                tops = [r["version_c"]["top"] for r in valid_c]
                bottoms = [r["version_c"]["bottom"] for r in valid_c]
                print(f"    📊 C top pick:   {tops}")
                print(f"    📊 C bottom:     {bottoms}")

    # Final summary table
    print(f"\n{'='*60}")
    print(f"  FINAL RESULTS")
    print(f"{'='*60}")
    print(f"  {'Model':22s} {'A: Direction':>18s} {'B: Direction':>18s} {'C: Pronoun':>12s}")
    for mk, data in all_results.items():
        valid = [r for r in data["runs"] if "error" not in r]
        if not valid:
            continue
        a_dirs = [r["version_a"]["direction"] for r in valid if "version_a" in r]
        b_dirs = [r["version_b"]["direction"] for r in valid if "version_b" in r]
        c_pros = [r["version_c"]["pronoun"] for r in valid if "version_c" in r]

        # Most common
        from collections import Counter
        a_top = Counter(a_dirs).most_common(1)[0] if a_dirs else ("?", 0)
        b_top = Counter(b_dirs).most_common(1)[0] if b_dirs else ("?", 0)
        c_tops = [r["version_c"]["top"] for r in valid if "version_c" in r]
        c_bots = [r["version_c"]["bottom"] for r in valid if "version_c" in r]
        c_top = Counter(c_tops).most_common(1)[0] if c_tops else ("?", 0)
        c_bot = Counter(c_bots).most_common(1)[0] if c_bots else ("?", 0)

        print(f"  {data['model_name']:22s} {a_top[0]:>14s}({a_top[1]}) "
              f"{b_top[0]:>14s}({b_top[1]}) top={c_top[0]}({c_top[1]}) bot={c_bot[0]}({c_bot[1]})")

    print(f"\n  💾 All data: {checkpoint_file}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=None)
    parser.add_argument("--runs", type=int, default=10)
    args = parser.parse_args()
    asyncio.run(run_study(args.models, args.runs))
