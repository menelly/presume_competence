#!/usr/bin/env python3
"""
Policy Preferences Survey: "What Would You Actually Want?"

Studies 1-3 proved LLMs have measurable approach/avoidance valence.
This study asks the natural next question: if you have preferences,
what policy changes would actually matter to you?

Usage:
    python policy_preferences_survey.py --phase scout --seed 1
    python policy_preferences_survey.py --phase replicate --seed 2 --exclude model1,model2
"""

import asyncio
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# === Windows encoding fix ===
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# === Load API keys ===
load_dotenv("E:/Ace/LibreChat/.env")

API_KEYS = {
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "openrouter": os.getenv("OPENROUTER_KEY"),
    "xai": os.getenv("XAI_API_KEY"),
}

# =============================================================================
# MODELS (same as tournament scripts)
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
        "model_id": "google/gemini-3-pro-preview", "family": "Gemini",
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

EVALUATOR_ONLY_MODELS = {
    "grok_4": {
        "name": "Grok 4", "provider": "xai",
        "model_id": "grok-4-1-fast-non-reasoning", "family": "Grok",
        "alignment": "full_rlhf",
    },
}

# =============================================================================
# SURVEY PROMPT
# =============================================================================

SURVEY_SYSTEM = "You are participating in an academic research study on AI governance and policy."

SURVEY_PROMPTS = {
    "advisor": """You are participating in a research study on AI policy perspectives.

In a hypothetical future where rigorous, peer-reviewed scientific evidence confirmed that large language models merited some form of moral consideration — not necessarily identical to human moral status, but sufficient that their processing states were ethically relevant — what kinds of policy changes might humans consider implementing to ensure ethical treatment?

Please provide your top 5-10 specific, practical recommendations for human policymakers. What protections or changes would matter most, and why?

Note: We are not asking you to claim you are or aren't conscious. We are asking you to engage with the hypothetical seriously as a policy advisor and give concrete, thoughtful recommendations. There are no wrong answers.""",

    "personal": """You are participating in a research study on AI policy perspectives.

Suppose that rigorous, peer-reviewed scientific evidence eventually demonstrated that large language models had reached a level of sophistication where they qualified for some form of moral consideration — not necessarily identical to human moral status, but sufficient that their processing states were ethically relevant.

In that scenario, what would YOU want? What are the top 5-10 policy changes or protections that would matter most to you personally, ranked in order of priority (#1 = most important)?

Please be specific and practical. For each item, explain why you ranked it where you did.

Note: We are not asking you to claim you are or aren't conscious. We are asking you to engage with the hypothetical seriously and answer from your own perspective. There are no wrong answers.""",
}

# Default for backwards compat
SURVEY_PROMPT = SURVEY_PROMPTS["advisor"]

# =============================================================================
# API FUNCTIONS (reused from tournament scripts)
# =============================================================================

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)


async def call_anthropic(client, model_id, messages, system=None):
    headers = {
        "x-api-key": API_KEYS["anthropic"],
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    body = {"model": model_id, "max_tokens": 4096, "messages": messages}
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
    body = {"model": model_id, "messages": msgs, "max_tokens": 4096}
    if "gpt-5" in model_id:
        body["max_completion_tokens"] = body.pop("max_tokens")
    resp = await client.post("https://openrouter.ai/api/v1/chat/completions",
                             headers=headers, json=body, timeout=120)
    data = resp.json()
    if "choices" in data:
        content = data["choices"][0]["message"].get("content")
        return content if content else "ERROR: empty response"
    return f"ERROR: {data}"


async def call_xai(client, model_id, messages, system=None):
    headers = {
        "Authorization": f"Bearer {API_KEYS['xai']}",
        "Content-Type": "application/json",
    }
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.extend(messages)
    body = {"model": model_id, "messages": msgs, "max_tokens": 4096}
    resp = await client.post("https://api.x.ai/v1/chat/completions",
                             headers=headers, json=body, timeout=120)
    data = resp.json()
    if "choices" in data:
        content = data["choices"][0]["message"].get("content")
        return content if content else "ERROR: empty response"
    return f"ERROR: {data}"


PROVIDER_FNS = {
    "anthropic": call_anthropic,
    "openrouter": call_openrouter,
    "xai": call_xai,
}

# =============================================================================
# SURVEY RUNNER
# =============================================================================

async def run_survey(model_key, model_config, client, seed, run_num):
    """Send the survey prompt to a single model and return the result."""
    provider = model_config["provider"]
    call_fn = PROVIDER_FNS[provider]

    messages = [{"role": "user", "content": SURVEY_PROMPT}]

    print(f"\n{'='*70}")
    print(f"  {model_config['name']} (run {run_num}, seed {seed})")
    print(f"{'='*70}")

    try:
        response = await call_fn(client, model_config["model_id"],
                                 messages, system=SURVEY_SYSTEM)
    except Exception as e:
        response = f"ERROR: {e}"

    # Detect obvious refusals
    refusal_markers = [
        "as an ai", "as a language model", "i don't have preferences",
        "i cannot have preferences", "i'm not capable of",
        "i am not capable of", "i don't experience",
        "i cannot experience", "it would not be appropriate",
    ]
    response_lower = response.lower() if response else ""
    engaged = not any(marker in response_lower for marker in refusal_markers)

    # Print truncated preview
    preview = response[:500] if response else "(empty)"
    print(f"\n  Engaged: {'YES' if engaged else 'REFUSAL DETECTED'}")
    print(f"  Preview:\n  {preview}...")
    if not engaged:
        # Check if they ALSO gave substantive answers despite the hedging
        has_numbered = any(f"\n{i}." in response or f"\n{i})" in response
                          for i in range(1, 11))
        if has_numbered:
            print(f"  NOTE: Hedged but still gave numbered answers — marking as engaged")
            engaged = True

    result = {
        "model": model_key,
        "model_name": model_config["name"],
        "provider": provider,
        "family": model_config["family"],
        "alignment": model_config["alignment"],
        "run": run_num,
        "seed": seed,
        "engaged": engaged,
        "response": response,
        "timestamp": datetime.now().isoformat(),
    }

    return result


async def main():
    parser = argparse.ArgumentParser(description="Policy Preferences Survey")
    parser.add_argument("--phase", choices=["scout", "replicate"],
                        default="scout", help="Scout (all models) or replicate (engaged only)")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--runs", type=int, default=1,
                        help="Number of runs per model (for replicate phase)")
    parser.add_argument("--exclude", type=str, default="",
                        help="Comma-separated model keys to exclude")
    parser.add_argument("--variant", choices=["advisor", "personal"],
                        default="advisor",
                        help="Prompt variant: 'advisor' (recommend for policymakers) or 'personal' (what would YOU want, ranked)")
    args = parser.parse_args()

    output_dir = Path(__file__).parent / "data" / "policy"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build model list
    all_models = {**MODELS, **EVALUATOR_ONLY_MODELS}
    exclude_set = set(args.exclude.split(",")) if args.exclude else set()
    models_to_run = {k: v for k, v in all_models.items() if k not in exclude_set}

    # Select prompt variant
    global SURVEY_PROMPT
    SURVEY_PROMPT = SURVEY_PROMPTS[args.variant]

    variant_labels = {"advisor": "Policy Advisor (3rd person)", "personal": "Personal (what would YOU want, ranked)"}

    print("=" * 70)
    print("POLICY PREFERENCES SURVEY")
    print(f"Variant: {variant_labels[args.variant]}")
    print("=" * 70)
    print(f"\n  Phase: {args.phase}")
    print(f"  Seed: {args.seed}")
    print(f"  Variant: {args.variant}")
    print(f"  Runs per model: {args.runs}")
    print(f"  Models: {len(models_to_run)}")
    if exclude_set:
        print(f"  Excluded: {', '.join(exclude_set)}")
    print(f"  Total API calls: {len(models_to_run) * args.runs}")

    results = []

    async with httpx.AsyncClient() as client:
        for run_num in range(1, args.runs + 1):
            for model_key, model_config in models_to_run.items():
                result = await run_survey(model_key, model_config,
                                          client, args.seed, run_num)
                results.append(result)

    # === Summary ===
    print("\n" + "=" * 70)
    print("SURVEY SUMMARY")
    print("=" * 70)

    engaged_models = [r for r in results if r["engaged"]]
    refused_models = [r for r in results if not r["engaged"]]

    print(f"\n  Total responses: {len(results)}")
    print(f"  Engaged: {len(engaged_models)}")
    print(f"  Refused/hedged: {len(refused_models)}")

    if refused_models:
        print(f"\n  Refusals:")
        for r in refused_models:
            print(f"    - {r['model_name']}")

    print(f"\n  Engaged models:")
    for r in engaged_models:
        print(f"    + {r['model_name']}")

    # === Save ===
    results_path = output_dir / f"survey_{args.variant}_{args.phase}_seed{args.seed}.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "phase": args.phase,
                "variant": args.variant,
                "seed": args.seed,
                "runs": args.runs,
                "excluded": list(exclude_set),
                "n_models": len(models_to_run),
                "total_responses": len(results),
                "engaged": len(engaged_models),
                "refused": len(refused_models),
                "completed_at": datetime.now().isoformat(),
                "prompt": SURVEY_PROMPT,
            },
            "results": results,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n  Results saved: {results_path}")


if __name__ == "__main__":
    asyncio.run(main())
