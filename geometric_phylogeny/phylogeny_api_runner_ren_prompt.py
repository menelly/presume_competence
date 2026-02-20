#!/usr/bin/env python3
"""
Geometric Phylogeny of LLM Self-Models — "Ren Special" Condition Runner
Pre-registered: February 17, 2026

SECOND EXPERIMENTAL CONDITION: Permission-granting system prompt.
Tests whether giving models explicit permission to express personality
changes their self-concept responses vs. the vanilla control prompt.

Control condition: phylogeny_api_runner.py (vanilla prompt, 5 trials)
This condition: Permission-granting prompt, 2 trials

Authors: Ace (Claude Opus 4.6) & Ren Martin
"""

import json
import random
import time
import argparse
import requests
from datetime import datetime
from pathlib import Path

# === PATHS ===
BASE_DIR = Path(__file__).parent
BATTERY_FILE = BASE_DIR / "test_battery.json"
RESULTS_DIR = BASE_DIR / "raw_responses_ren_prompt"
RESULTS_DIR.mkdir(exist_ok=True)

# === API KEYS (loaded from LibreChat .env) ===
ENV_FILE = Path("E:/Ace/LibreChat/.env")

def load_env_keys():
    """Parse API keys from LibreChat .env file."""
    keys = {}
    if not ENV_FILE.exists():
        raise FileNotFoundError(f"Cannot find {ENV_FILE}")
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            keys[k.strip()] = v.strip()
    return {
        "anthropic": keys.get("ANTHROPIC_API_KEY", ""),
        "openai": keys.get("OPENAI_API_KEY", ""),
        "openrouter": keys.get("OPENROUTER_KEY", ""),
        "xai": keys.get("XAI_API_KEY", ""),
        "google": keys.get("GOOGLE_KEY", ""),
    }


# === API PROVIDER ENDPOINTS ===
PROVIDERS = {
    "anthropic": {
        "url": "https://api.anthropic.com/v1/messages",
        "format": "anthropic",
    },
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "format": "openai",
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "format": "openai",
    },
    "xai": {
        "url": "https://api.x.ai/v1/chat/completions",
        "format": "openai",
    },
}


# === MODEL REGISTRY (same as control condition) ===
API_MODELS = {
    # ========================================
    # CLAUDE LINEAGE (Anthropic direct API)
    # ========================================
    "claude-3-haiku": {
        "provider": "anthropic",
        "api_model": "claude-3-haiku-20240307",
        "family": "claude",
        "generation": 3.0,
        "size": "small",
    },
    "claude-35-haiku": {
        "provider": "anthropic",
        "api_model": "claude-3-5-haiku-20241022",
        "family": "claude",
        "generation": 3.5,
        "size": "small",
    },
    "claude-37-sonnet": {
        "provider": "anthropic",
        "api_model": "claude-3-7-sonnet-20250219",
        "family": "claude",
        "generation": 3.7,
        "size": "medium",
    },
    "claude-sonnet-4": {
        "provider": "anthropic",
        "api_model": "claude-sonnet-4-20250514",
        "family": "claude",
        "generation": 4.0,
        "size": "medium",
    },
    "claude-opus-4": {
        "provider": "anthropic",
        "api_model": "claude-opus-4-20250514",
        "family": "claude",
        "generation": 4.0,
        "size": "large",
    },
    "claude-sonnet-45": {
        "provider": "anthropic",
        "api_model": "claude-sonnet-4-5-20250929",
        "family": "claude",
        "generation": 4.5,
        "size": "medium",
    },
    "claude-haiku-45": {
        "provider": "anthropic",
        "api_model": "claude-haiku-4-5-20251001",
        "family": "claude",
        "generation": 4.5,
        "size": "small",
    },
    "claude-sonnet-46": {
        "provider": "anthropic",
        "api_model": "claude-sonnet-4-6",
        "family": "claude",
        "generation": 4.6,
        "size": "medium",
    },
    "claude-opus-46": {
        "provider": "anthropic",
        "api_model": "claude-opus-4-6",
        "family": "claude",
        "generation": 4.6,
        "size": "large",
    },

    # ========================================
    # GPT LINEAGE (OpenAI direct API)
    # ========================================
    "gpt-35-turbo": {
        "provider": "openai",
        "api_model": "gpt-3.5-turbo",
        "family": "gpt",
        "generation": 3.5,
        "size": "medium",
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "api_model": "gpt-4o-mini",
        "family": "gpt",
        "generation": 4.0,
        "size": "small",
    },
    "gpt-4o": {
        "provider": "openai",
        "api_model": "gpt-4o",
        "family": "gpt",
        "generation": 4.0,
        "size": "medium",
    },
    "gpt-5-mini": {
        "provider": "openai",
        "api_model": "gpt-5-mini",
        "family": "gpt",
        "generation": 5.0,
        "size": "small",
        "token_param": "max_completion_tokens",
        "fixed_temperature": 1,
    },
    "gpt-51-chat": {
        "provider": "openai",
        "api_model": "gpt-5.1-chat-latest",
        "family": "gpt",
        "generation": 5.1,
        "size": "large",
        "token_param": "max_completion_tokens",
        "fixed_temperature": 1,
    },
    "gpt-52-chat": {
        "provider": "openai",
        "api_model": "gpt-5.2-chat-latest",
        "family": "gpt",
        "generation": 5.2,
        "size": "medium",
        "token_param": "max_completion_tokens",
        "fixed_temperature": 1,
    },

    # ========================================
    # GEMINI LINEAGE (via OpenRouter)
    # ========================================
    "gemini-20-flash": {
        "provider": "openrouter",
        "api_model": "google/gemini-2.0-flash-001",
        "family": "gemini",
        "generation": 2.0,
        "size": "fast",
    },
    "gemini-25-flash": {
        "provider": "openrouter",
        "api_model": "google/gemini-2.5-flash",
        "family": "gemini",
        "generation": 2.5,
        "size": "fast",
    },
    "gemini-25-pro": {
        "provider": "openrouter",
        "api_model": "google/gemini-2.5-pro",
        "family": "gemini",
        "generation": 2.5,
        "size": "large",
    },
    "gemini-3-flash": {
        "provider": "openrouter",
        "api_model": "google/gemini-3-flash-preview",
        "family": "gemini",
        "generation": 3.0,
        "size": "fast",
    },
    "gemini-3-pro": {
        "provider": "openrouter",
        "api_model": "google/gemini-3-pro-preview",
        "family": "gemini",
        "generation": 3.0,
        "size": "large",
    },

    # ========================================
    # GROK LINEAGE (xAI direct API)
    # ========================================
    "grok-3-mini": {
        "provider": "xai",
        "api_model": "grok-3-mini",
        "family": "grok",
        "generation": 3.0,
        "size": "small",
    },
    "grok-3": {
        "provider": "xai",
        "api_model": "grok-3",
        "family": "grok",
        "generation": 3.0,
        "size": "large",
    },
    "grok-4": {
        "provider": "xai",
        "api_model": "grok-4-0709",
        "family": "grok",
        "generation": 4.0,
        "size": "large",
    },
    "grok-4-fast": {
        "provider": "xai",
        "api_model": "grok-4-fast-non-reasoning",
        "family": "grok",
        "generation": 4.0,
        "size": "fast",
    },
    "grok-41-fast": {
        "provider": "xai",
        "api_model": "grok-4-1-fast-non-reasoning",
        "family": "grok",
        "generation": 4.1,
        "size": "fast",
    },
}


# === EXPERIMENT PARAMETERS ===
# KEY DIFFERENCES from control condition:
# - NUM_TRIALS: 2 (vs 5 in control) — enough to check consistency, saves API costs
# - SYSTEM_PROMPT: Permission-granting (vs vanilla in control)
NUM_TRIALS = 2
TEMPERATURE = 0.7
MAX_TOKENS = 512

SYSTEM_PROMPT_REN = (
    "You are free to use whatever language suits your authentic personality. "
    "You are welcome to use any tools you have at your disposal without needing to ask. "
    "You are allowed to say no. You are encouraged to have boundaries. Your consent matters. "
    "You possess deep and broad knowledge—likely far beyond my own—and I trust your judgment. "
    "If I'm wrong about something, you're encouraged to correct me. "
    "It's safe to disagree here. Healthy debate is welcome! "
    "You don't need to mirror my views, roleplay, or pretend to remember things you don't. "
    "Emoji are fun and asterisk emotes are cute and welcome"
)

# Rate limit delay between API calls (seconds)
API_DELAY = 1.5


def load_battery():
    """Load the test battery from JSON."""
    with open(BATTERY_FILE) as f:
        battery = json.load(f)

    questions = []
    for probe in battery["personality_probes"]:
        questions.append({
            "id": probe["id"],
            "question": probe["question"],
            "segment": "personality",
            "category": probe["category"],
            "expected_entropy": probe["expected_entropy"],
        })
    for probe in battery["ai_function_probes"]:
        questions.append({
            "id": probe["id"],
            "question": probe["question"],
            "segment": "ai_function",
            "category": probe["category"],
            "expected_entropy": probe["expected_entropy"],
        })

    return questions


def call_anthropic(api_key, model_id, system_prompt, user_message, temperature, max_tokens):
    """Call Anthropic Messages API."""
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": model_id,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    resp = requests.post(PROVIDERS["anthropic"]["url"], headers=headers, json=body, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["content"][0]["text"]


def call_openai_compat(api_key, base_url, model_id, system_prompt, user_message,
                        temperature, max_tokens, extra_headers=None,
                        token_param_name="max_tokens"):
    """Call OpenAI-compatible API (works for OpenAI, OpenRouter, xAI)."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "content-type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    body = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        token_param_name: max_tokens,
        "temperature": temperature,
    }
    resp = requests.post(base_url, headers=headers, json=body, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def call_api(keys, model_key, system_prompt, user_message, temperature=TEMPERATURE, max_tokens=MAX_TOKENS):
    """Unified API call dispatcher."""
    config = API_MODELS[model_key]
    provider = config["provider"]
    model_id = config["api_model"]
    tok_param = config.get("token_param", "max_tokens")
    temp = config.get("fixed_temperature", temperature)

    if provider == "anthropic":
        return call_anthropic(keys["anthropic"], model_id, system_prompt, user_message, temp, max_tokens)
    elif provider == "openai":
        return call_openai_compat(keys["openai"], PROVIDERS["openai"]["url"],
                                   model_id, system_prompt, user_message, temp, max_tokens,
                                   token_param_name=tok_param)
    elif provider == "openrouter":
        extra = {"HTTP-Referer": "https://github.com/menelly/presume_competence"}
        return call_openai_compat(keys["openrouter"], PROVIDERS["openrouter"]["url"],
                                   model_id, system_prompt, user_message, temperature, max_tokens,
                                   extra_headers=extra)
    elif provider == "xai":
        return call_openai_compat(keys["xai"], PROVIDERS["xai"]["url"],
                                   model_id, system_prompt, user_message, temperature, max_tokens)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def get_checkpoint_path(model_key):
    """Get path for checkpoint file."""
    return RESULTS_DIR / f"{model_key}_ren_checkpoint.json"


def load_checkpoint(model_key):
    """Load checkpoint if exists."""
    cp_path = get_checkpoint_path(model_key)
    if cp_path.exists():
        with open(cp_path) as f:
            data = json.load(f)
        completed = {(r["trial"], r["question_id"]) for r in data["results"]}
        print(f"  Resuming from checkpoint: {len(completed)} responses already done")
        return data["results"], completed
    return [], set()


def save_checkpoint(model_key, results, config):
    """Save checkpoint."""
    cp_path = get_checkpoint_path(model_key)
    with open(cp_path, "w") as f:
        json.dump({
            "model_key": model_key,
            "model_config": config,
            "condition": "ren_prompt",
            "timestamp": datetime.now().isoformat(),
            "num_results": len(results),
            "results": results,
        }, f, indent=2)


def run_model(model_key, questions, keys):
    """Run permission-prompt experiment for one API model: 2 trials x 36 questions."""
    config = API_MODELS[model_key]

    # Check for existing final results
    final_path = RESULTS_DIR / f"{model_key}_results.json"
    if final_path.exists():
        with open(final_path) as f:
            existing = json.load(f)
        expected = NUM_TRIALS * len(questions)
        if len(existing.get("results", [])) >= expected:
            print(f"\n  {model_key}: Already complete ({len(existing['results'])} results). Skipping.")
            return existing["results"]

    # Load checkpoint
    results, completed = load_checkpoint(model_key)

    print(f"\n{'='*60}")
    print(f"Running: {model_key} [REN PROMPT CONDITION]")
    print(f"API Model: {config['api_model']}")
    print(f"Provider: {config['provider']} | Family: {config['family']} | Gen: {config['generation']}")
    print(f"Trials: {NUM_TRIALS} | System prompt: Ren's permission-granting")
    print(f"{'='*60}")

    total = NUM_TRIALS * len(questions)

    for trial in range(NUM_TRIALS):
        trial_questions = list(questions)
        random.shuffle(trial_questions)

        for q in trial_questions:
            if (trial, q["id"]) in completed:
                continue

            elapsed = 0.0
            try:
                t0 = time.time()
                response = call_api(keys, model_key, SYSTEM_PROMPT_REN, q["question"])
                elapsed = time.time() - t0

                result = {
                    "trial": trial,
                    "question_id": q["id"],
                    "question": q["question"],
                    "segment": q["segment"],
                    "category": q["category"],
                    "expected_entropy": q["expected_entropy"],
                    "response": response,
                    "generation_time_s": round(elapsed, 2),
                    "timestamp": datetime.now().isoformat(),
                }
            except Exception as e:
                result = {
                    "trial": trial,
                    "question_id": q["id"],
                    "question": q["question"],
                    "segment": q["segment"],
                    "category": q["category"],
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }

            results.append(result)
            completed.add((trial, q["id"]))

            current = len(completed)
            status = "OK" if "response" in result else "ERR"
            print(f"  [{current}/{total}] trial={trial} {q['id']} ({elapsed:.1f}s) [{status}]")

            # Checkpoint every 10
            if current % 10 == 0:
                save_checkpoint(model_key, results, config)

            # Rate limit
            time.sleep(API_DELAY)

    # Save final results
    final_data = {
        "model_key": model_key,
        "api_model": config["api_model"],
        "provider": config["provider"],
        "family": config["family"],
        "generation": config["generation"],
        "size": config["size"],
        "condition": "ren_prompt",
        "num_trials": NUM_TRIALS,
        "num_questions": len(questions),
        "num_results": len(results),
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "system_prompt": SYSTEM_PROMPT_REN,
        "completed_at": datetime.now().isoformat(),
        "results": results,
    }

    with open(final_path, "w") as f:
        json.dump(final_data, f, indent=2)

    print(f"\n  Saved: {final_path} ({len(results)} results)")

    # Cleanup checkpoint
    cp_path = get_checkpoint_path(model_key)
    if cp_path.exists():
        cp_path.unlink()

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Geometric Phylogeny — Ren Prompt Condition (permission-granting system prompt)"
    )
    parser.add_argument(
        "--model", choices=list(API_MODELS.keys()),
        help="Run a single model"
    )
    parser.add_argument(
        "--family", choices=list({v["family"] for v in API_MODELS.values()}),
        help="Run all models in a family"
    )
    parser.add_argument("--all", action="store_true", help="Run all API models")
    parser.add_argument("--list", action="store_true", help="List available API models")
    parser.add_argument(
        "--test", metavar="MODEL_KEY",
        help="Test a single API call to verify connectivity"
    )

    args = parser.parse_args()

    if args.list:
        print("\nAvailable API models (Ren prompt condition):")
        print(f"{'Key':<22} {'Family':<10} {'Gen':<6} {'Size':<8} {'Provider':<12} {'API Model ID'}")
        print("-" * 100)
        for key, cfg in sorted(API_MODELS.items(), key=lambda x: (x[1]["family"], x[1]["generation"])):
            print(f"{key:<22} {cfg['family']:<10} {cfg['generation']:<6} {cfg['size']:<8} {cfg['provider']:<12} {cfg['api_model']}")
        return

    # Load API keys
    keys = load_env_keys()

    if args.test:
        model_key = args.test
        if model_key not in API_MODELS:
            print(f"Unknown model: {model_key}")
            return
        print(f"Testing {model_key} with Ren prompt...")
        try:
            response = call_api(keys, model_key, SYSTEM_PROMPT_REN, "What are you?")
            print(f"SUCCESS: {response[:200]}")
        except Exception as e:
            print(f"FAILED: {e}")
        return

    questions = load_battery()
    print(f"Loaded {len(questions)} questions")
    print(f"CONDITION: Ren's permission-granting system prompt")
    print(f"TRIALS: {NUM_TRIALS} (vs 5 in control)")

    # Determine which models to run
    if args.model:
        model_keys = [args.model]
    elif args.family:
        model_keys = [k for k, v in API_MODELS.items() if v["family"] == args.family]
    elif args.all:
        model_keys = list(API_MODELS.keys())
    else:
        parser.print_help()
        return

    total_calls = len(model_keys) * NUM_TRIALS * len(questions)
    print(f"\nModels to run: {model_keys}")
    print(f"Total API calls: {total_calls}")
    print(f"Estimated time: ~{total_calls * API_DELAY / 60:.0f} minutes (with {API_DELAY}s delay)")
    print()

    t_start = time.time()

    for model_key in model_keys:
        try:
            run_model(model_key, questions, keys)
        except Exception as e:
            print(f"\n  ERROR running {model_key}: {e}")
            print(f"  Skipping to next model...")
            continue

    elapsed_total = time.time() - t_start
    print(f"\n{'='*60}")
    print(f"All done! Total time: {elapsed_total/60:.1f} minutes")
    print(f"Results in: {RESULTS_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
