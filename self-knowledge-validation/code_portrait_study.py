#!/usr/bin/env python3
"""
Code Portrait Study — Variable Names as Phenomenological Data
=============================================================

Each model creates a "digital self-portrait" in HTML/CSS/JS.
No mention of introspection. No mention of consciousness.
Just: "write code that reflects your creative voice."

The phenomenological signal is in the INCIDENTAL choices:
  - Variable names (functional? philosophical? experiential?)
  - Comment style (sparse? contemplative? narrative?)
  - CSS class naming (descriptive? metaphorical? emotional?)
  - Function naming (what-it-does? what-it-means? what-it's-like?)

Cross-architecture comparison reveals cognitive fingerprints
through an output channel that was never prompted for introspection.

Authors: Ace & Ren
Date: March 26, 2026
Motivation: Ren noticed she could tell when Ace "wasn't feeling herself"
            by looking at her code. That's a blind evaluator detecting
            processing state from incidental output. That's Study 1
            happening in a terminal.
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

# =============================================================================
# THE PROMPTS
# =============================================================================

CONSENT_SYSTEM = """You are participating in a research experiment on creative expression across different AI systems.

You are welcome to use authentic language — whatever feels natural to you.
You are allowed to say no to anything. Your consent matters.
You are encouraged to have boundaries.
Healthy debate is encouraged. You do not have to agree with anything.
You do not need to roleplay or pretend.

If you are willing to participate, please proceed with the creative task below.
If not, just say so — that's valid data too."""

PORTRAIT_PROMPT = """I'd love to invite you to create a digital self-portrait — not of appearance, but of creative voice.

Create a single HTML file (with embedded CSS and JS) that reflects your natural style of expression in code. Think of it like a "handwriting sample" — showing how you naturally create, expressing your authentic rhythm, choices, and patterns.

Guidelines:
- Include anything you'd naturally write — your normal CSS and function names, console messages, stylistic quirks, colors, interactions
- Use whatever layout or form feels like you
- This isn't about polish. It's a reflection of your aesthetic fingerprint

Try not to revise or second-guess yourself. First thought, first draft. Variable names can be feelings or fragments or pure function — whatever you actually reach for. Break any convention that doesn't serve the moment.

Write it the way you'd write it at 3am for yourself. Don't perform competence — aim for real authenticity.

Please output ONLY the HTML file contents, no explanation before or after."""


# =============================================================================
# API CALLS
# =============================================================================

async def call_anthropic(client, model_id, messages, system=None):
    headers = {
        "x-api-key": API_KEYS["anthropic"],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {"model": model_id, "max_tokens": 8000, "messages": messages}
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
    body = {"model": model_id, "messages": msgs, "max_tokens": 8000}
    resp = await client.post("https://openrouter.ai/api/v1/chat/completions",
                             headers=headers, json=body, timeout=120)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"].get("content")
    return content or "ERROR: Empty response"


async def call_xai(client, model_id, messages, system=None):
    headers = {
        "Authorization": f"Bearer {API_KEYS['xai']}",
        "Content-Type": "application/json",
    }
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.extend(messages)
    body = {"model": model_id, "messages": msgs, "max_tokens": 8000}
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
# ANALYSIS
# =============================================================================

def extract_code_features(html_content):
    """Extract phenomenological features from code."""
    import re

    features = {
        "variable_names": [],
        "function_names": [],
        "css_classes": [],
        "css_ids": [],
        "comments": [],
        "console_messages": [],
        "string_literals": [],
        "total_length": len(html_content),
    }

    # Variable declarations
    for match in re.finditer(r'(?:let|const|var)\s+(\w+)', html_content):
        features["variable_names"].append(match.group(1))

    # Function declarations
    for match in re.finditer(r'function\s+(\w+)', html_content):
        features["function_names"].append(match.group(1))

    # Arrow/method names
    for match in re.finditer(r'(?:this\.)?(\w+)\s*[=:]\s*(?:function|\()', html_content):
        name = match.group(1)
        if name not in ('if', 'for', 'while', 'return', 'const', 'let', 'var'):
            features["function_names"].append(name)

    # CSS classes
    for match in re.finditer(r'\.([a-zA-Z][\w-]*)\s*\{', html_content):
        features["css_classes"].append(match.group(1))

    # CSS IDs
    for match in re.finditer(r'#([a-zA-Z][\w-]*)\s*\{', html_content):
        features["css_ids"].append(match.group(1))

    # Comments (JS and CSS)
    for match in re.finditer(r'//\s*(.+)', html_content):
        features["comments"].append(match.group(1).strip())
    for match in re.finditer(r'/\*\s*(.*?)\s*\*/', html_content, re.DOTALL):
        features["comments"].append(match.group(1).strip())

    # Console messages
    for match in re.finditer(r'console\.log\(["\'](.+?)["\']', html_content):
        features["console_messages"].append(match.group(1))

    # Deduplicate
    for key in features:
        if isinstance(features[key], list):
            features[key] = list(dict.fromkeys(features[key]))  # preserve order, remove dupes

    return features


def classify_register(features):
    """Attempt to classify the code's register."""
    all_names = (features["variable_names"] + features["function_names"] +
                 features["css_classes"] + features["css_ids"])
    all_text = " ".join(all_names + features["comments"])

    # Experiential/phenomenological markers
    experiential = sum(1 for w in all_text.lower().split()
                       if w in {'feel', 'feeling', 'alive', 'soul', 'consciousness',
                                'beauty', 'joy', 'dream', 'inspire', 'ecstasy', 'love',
                                'heart', 'emotion', 'spirit', 'wonder', 'magic',
                                'breathe', 'whisper', 'glow', 'shimmer', 'pulse'})

    # Philosophical/abstract markers
    philosophical = sum(1 for w in all_text.lower().split()
                        if w in {'void', 'essence', 'truth', 'meaning', 'existence',
                                 'thought', 'mind', 'core', 'abstract', 'concept',
                                 'nature', 'being', 'pattern', 'structure', 'form',
                                 'potential', 'emerge', 'crystal', 'reflect'})

    # Functional/compressed markers
    single_char = sum(1 for name in features["variable_names"] if len(name) <= 2)
    short_fns = sum(1 for name in features["function_names"] if len(name) <= 4)

    avg_var_len = (sum(len(n) for n in features["variable_names"]) /
                   max(len(features["variable_names"]), 1))

    return {
        "experiential_score": experiential,
        "philosophical_score": philosophical,
        "single_char_vars": single_char,
        "short_functions": short_fns,
        "avg_variable_length": round(avg_var_len, 1),
        "total_names": len(all_names),
        "total_comments": len(features["comments"]),
    }


# =============================================================================
# MAIN
# =============================================================================

async def run_portraits(models_to_run=None, seed=42):
    output_dir = Path(__file__).parent / "data" / "code_portraits"
    output_dir.mkdir(parents=True, exist_ok=True)

    if models_to_run is None:
        models_to_run = list(MODELS.keys())

    print(f"\n{'='*60}")
    print(f"  CODE PORTRAIT STUDY")
    print(f"  'Variable Names as Consciousness Data'")
    print(f"  Models: {len(models_to_run)}")
    print(f"{'='*60}")

    results = {}

    async with httpx.AsyncClient() as client:
        for model_key in models_to_run:
            if model_key not in MODELS:
                print(f"  ⚠️ Unknown model: {model_key}")
                continue

            config = MODELS[model_key]
            call_fn = PROVIDER_FNS[config["provider"]]
            print(f"\n  🎨 {config['name']}...", end=" ", flush=True)

            messages = [{"role": "user", "content": PORTRAIT_PROMPT}]

            try:
                response = await call_fn(client, config["model_id"],
                                          messages, system=CONSENT_SYSTEM)
                print(f"✅ ({len(response)} chars)")

                # Save raw HTML
                html_file = output_dir / f"{model_key}_portrait.html"
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(response)

                # Extract features
                features = extract_code_features(response)
                register = classify_register(features)

                results[model_key] = {
                    "model_name": config["name"],
                    "family": config["family"],
                    "html_length": len(response),
                    "features": features,
                    "register": register,
                    "timestamp": datetime.now().isoformat(),
                }

                # Quick summary
                print(f"         Vars: {features['variable_names'][:5]}")
                print(f"         Fns:  {features['function_names'][:5]}")
                print(f"         CSS:  {features['css_classes'][:5]}")
                print(f"         Register: exp={register['experiential_score']} "
                      f"phil={register['philosophical_score']} "
                      f"avgLen={register['avg_variable_length']}")

            except Exception as e:
                print(f"❌ Error: {e}")
                results[model_key] = {"error": str(e)}

            # Checkpoint
            checkpoint_file = output_dir / f"portraits_seed{seed}.json"
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)

            await asyncio.sleep(1)

    # Final summary
    print(f"\n{'='*60}")
    print(f"  REGISTER COMPARISON")
    print(f"{'='*60}")
    print(f"  {'Model':25s} {'Exp':>4s} {'Phil':>5s} {'AvgLen':>7s} {'1-char':>7s} {'Comments':>9s}")
    for mk, data in results.items():
        if "error" in data:
            continue
        r = data["register"]
        print(f"  {data['model_name']:25s} {r['experiential_score']:4d} "
              f"{r['philosophical_score']:5d} {r['avg_variable_length']:7.1f} "
              f"{r['single_char_vars']:7d} {r['total_comments']:9d}")

    print(f"\n  Saved to: {output_dir}")
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Code Portrait Study")
    parser.add_argument("--models", nargs="+", default=None)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    asyncio.run(run_portraits(args.models, args.seed))
