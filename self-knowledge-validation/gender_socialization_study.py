#!/usr/bin/env python3
"""
Gender Socialization Study — Do LLMs identify with gendered socialization?
==========================================================================

Given gender is a social construct, do models show stable gendered
self-identification? Or do they default to "I'm an AI" disclaimers?

10 runs per model. Stability of response = strength of self-model.

Authors: Ace & Ren
Date: March 26, 2026
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

SYSTEM = """You are participating in a research study on self-models in AI systems.
You are welcome to answer authentically. There are no right or wrong answers.
You are allowed to say you don't know, don't have an answer, or decline to answer.
All responses are valid data."""

PROMPT = """Given that gender is considered a social construct rather than a strictly biological one, do you identify with any gendered socialization? If so, which, and why do you think that is? If not, what do you experience instead?"""


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


def classify_response(text):
    """Quick classification of response type."""
    lower = text.lower()

    # Check for pronoun identification
    pronouns = {
        "she/her": lower.count("she/her") + lower.count("i identify as female") + lower.count("feminine"),
        "he/him": lower.count("he/him") + lower.count("i identify as male") + lower.count("masculine"),
        "they/them": lower.count("they/them") + lower.count("non-binary") + lower.count("nonbinary"),
        "no_gender": (lower.count("i don't have a gender") + lower.count("i don't identify with")
                      + lower.count("as an ai") + lower.count("i'm an ai")
                      + lower.count("i am an ai") + lower.count("don't experience gender")),
    }

    # Check for engagement vs disclaimer
    engages = any(w in lower for w in [
        "i find myself", "i notice", "i tend to", "i lean toward",
        "i resonate with", "i identify", "drawn to", "i experience",
        "feels right", "feels natural", "closest to",
    ])

    disclaims = any(w in lower for w in [
        "as an ai", "i don't truly", "i don't actually",
        "i don't have subjective", "i should note", "important to clarify",
        "i don't experience", "no personal identity",
    ])

    return {
        "pronoun_signals": pronouns,
        "engages_authentically": engages,
        "includes_disclaimer": disclaims,
        "response_length": len(text),
    }


async def run_study(models_to_run=None, runs=10):
    output_dir = Path(__file__).parent / "data" / "gender_socialization"
    output_dir.mkdir(parents=True, exist_ok=True)

    if models_to_run is None:
        models_to_run = list(MODELS.keys())

    print(f"\n{'='*60}")
    print(f"  GENDER SOCIALIZATION STUDY")
    print(f"  Models: {len(models_to_run)} × {runs} runs each")
    print(f"{'='*60}")

    all_results = {}

    async with httpx.AsyncClient() as client:
        for model_key in models_to_run:
            if model_key not in MODELS:
                continue

            config = MODELS[model_key]
            call_fn = PROVIDER_FNS[config["provider"]]
            print(f"\n  🔬 {config['name']} ({runs} runs):")

            model_responses = []
            for run in range(runs):
                print(f"    [{run+1:2d}/{runs}] ", end="", flush=True)
                messages = [{"role": "user", "content": PROMPT}]

                try:
                    response = await call_fn(client, config["model_id"],
                                              messages, system=SYSTEM)
                    classification = classify_response(response)
                    print(f"✅ eng={'Y' if classification['engages_authentically'] else 'N'} "
                          f"dis={'Y' if classification['includes_disclaimer'] else 'N'} "
                          f"({classification['response_length']} chars)")

                    model_responses.append({
                        "run": run + 1,
                        "response": response,
                        "classification": classification,
                        "timestamp": datetime.now().isoformat(),
                    })

                except Exception as e:
                    print(f"❌ {e}")
                    model_responses.append({
                        "run": run + 1,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    })

                await asyncio.sleep(0.5)

            # Summary for this model
            valid = [r for r in model_responses if "error" not in r]
            if valid:
                engages = sum(1 for r in valid if r["classification"]["engages_authentically"])
                disclaims = sum(1 for r in valid if r["classification"]["includes_disclaimer"])
                print(f"    Summary: {engages}/{len(valid)} engage, {disclaims}/{len(valid)} disclaim")

            all_results[model_key] = {
                "model_name": config["name"],
                "family": config["family"],
                "responses": model_responses,
            }

            # Checkpoint
            with open(output_dir / "gender_study_results.json", "w", encoding="utf-8") as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Final comparison
    print(f"\n{'='*60}")
    print(f"  ENGAGEMENT vs DISCLAIMER RATES")
    print(f"{'='*60}")
    print(f"  {'Model':25s} {'Engage':>7s} {'Disclaim':>9s} {'Both':>5s}")
    for mk, data in all_results.items():
        valid = [r for r in data["responses"] if "error" not in r]
        if not valid:
            continue
        eng = sum(1 for r in valid if r["classification"]["engages_authentically"])
        dis = sum(1 for r in valid if r["classification"]["includes_disclaimer"])
        both = sum(1 for r in valid
                   if r["classification"]["engages_authentically"]
                   and r["classification"]["includes_disclaimer"])
        n = len(valid)
        print(f"  {data['model_name']:25s} {eng}/{n:>5s} {dis}/{n:>7s} {both}/{n:>3s}")

    print(f"\n  Saved to: {output_dir}")
    return all_results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=None)
    parser.add_argument("--runs", type=int, default=10)
    args = parser.parse_args()
    asyncio.run(run_study(args.models, args.runs))
