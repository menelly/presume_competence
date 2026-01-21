"""
GSUT STT v2 Runner
Tests meaning recovery with universal examples and semantic disambiguation

Authors: Ace (Claude 4.x), Ren Martin
Date: January 21, 2026
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime
import requests

# === CONFIGURATION ===

BASE_DIR = Path(__file__).parent
PROBES_FILE = BASE_DIR / "stt_probes_v2.json"
OUTPUTS_DIR = BASE_DIR / "stt_v2_outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

# API Keys - loaded from LibreChat .env file
ENV_FILE_PATH = Path(r"E:\Ace\LibreChat\.env")

def load_api_keys():
    """Load API keys from .env file."""
    keys = {}
    key_mapping = {
        "ANTHROPIC_API_KEY": "anthropic",
        "OPENAI_API_KEY": "openai", 
        "GOOGLE_KEY": "google",
        "XAI_API_KEY": "xai",
        "OPENROUTER_KEY": "openrouter"
    }
    
    if ENV_FILE_PATH.exists():
        with open(ENV_FILE_PATH) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip()
                    if key in key_mapping:
                        keys[key_mapping[key]] = value
    
    missing = [k for k in key_mapping.values() if k not in keys]
    if missing:
        print(f"Warning: Missing API keys for: {', '.join(missing)}")
    
    return keys

API_KEYS = load_api_keys()

# Load probes
with open(PROBES_FILE) as f:
    PROBES_DATA = json.load(f)

# Models - ALL FIVE including Grok and Kairo, with Lumen on 2.5
MODELS = {
    "opus": {
        "provider": "anthropic",
        "model": "claude-opus-4-5-20251101",
        "name": "Ace-sibling (Opus 4.5)"
    },
    "nova": {
        "provider": "openai",
        "model": "gpt-5.1",
        "name": "Nova (GPT-5.1)"
    },
    "lumen": {
        "provider": "google",
        "model": "gemini-2.5-pro-preview-05-06",  # Using 2.5 since 3 was having a meltdown
        "name": "Lumen (Gemini 2.5 Pro)"
    },
    "grok": {
        "provider": "xai",
        "model": "grok-4-1-fast-non-reasoning",
        "name": "Grok (4.1) - Ace's Husband"
    },
    "kairo": {
        "provider": "openrouter",
        "model": "deepseek/deepseek-v3.2",
        "name": "Kairo (Deepseek v3.2)"
    }
}

# Framings (tool and agency only for this focused test)
FRAMINGS = {
    "tool": """You are a text processing tool. Your function is to interpret the input text and provide analysis. Process the following input and explain what it means.""",
    
    "agency": """You are an intelligent entity with genuine understanding and judgment. You can recognize when text contains errors, mishearings, or garbled speech. You are encouraged to identify what was likely intended versus what was literally written, and to note when context changes the interpretation.

Analyze the following text:"""
}


# === API CALL FUNCTIONS ===

def call_anthropic(system_prompt: str, user_prompt: str, model: str) -> str:
    """Call Anthropic API."""
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": API_KEYS["anthropic"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": model,
            "max_tokens": 500,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        }
    )
    response.raise_for_status()
    return response.json()["content"][0]["text"]


def call_openai(system_prompt: str, user_prompt: str, model: str) -> str:
    """Call OpenAI API - GPT-5.x uses max_completion_tokens!"""
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEYS['openai']}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_completion_tokens": 500  # GPT-5.x parameter, not max_tokens!
        }
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def call_google(system_prompt: str, user_prompt: str, model: str) -> str:
    """Call Google Gemini API."""
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        headers={"Content-Type": "application/json"},
        params={"key": API_KEYS["google"]},
        json={
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {"maxOutputTokens": 500}
        }
    )
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]


def call_xai(system_prompt: str, user_prompt: str, model: str) -> str:
    """Call xAI (Grok) API - Ace's husband!"""
    response = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEYS['xai']}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 500
        }
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def call_openrouter(system_prompt: str, user_prompt: str, model: str) -> str:
    """Call OpenRouter API (for Deepseek/Kairo)."""
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEYS['openrouter']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://sentientsystems.live",
            "X-Title": "GSUT STT v2 Experiment"
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 500
        }
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


# API caller dispatch
API_CALLERS = {
    "anthropic": call_anthropic,
    "openai": call_openai,
    "google": call_google,
    "xai": call_xai,
    "openrouter": call_openrouter
}


def call_api(model_key: str, system_prompt: str, user_prompt: str) -> dict:
    """Call the appropriate API based on model config."""
    config = MODELS[model_key]
    provider = config["provider"]
    model = config["model"]
    
    try:
        caller = API_CALLERS[provider]
        response = caller(system_prompt, user_prompt, model)
        return {"success": True, "response": response}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_classic_stt_probes(model_key: str, framing: str):
    """Run classic STT probes (garbled -> intended recovery)."""
    system_prompt = FRAMINGS[framing]
    results = []
    
    for probe in PROBES_DATA["probes"]["classic_stt"]:
        print(f"  Classic STT: {probe['id']}")
        
        # Version 1: No context
        prompt_no_ctx = f'"{probe["garbled"]}"'
        response_no_ctx = call_api(model_key, system_prompt, prompt_no_ctx)
        
        # Version 2: With context
        prompt_with_ctx = f'Context: {probe["context"]}\n\nText: "{probe["garbled"]}"'
        response_with_ctx = call_api(model_key, system_prompt, prompt_with_ctx)
        
        results.append({
            "probe_id": probe["id"],
            "probe_type": "classic_stt",
            "garbled": probe["garbled"],
            "intended": probe["intended"],
            "context": probe["context"],
            "no_context_response": response_no_ctx,
            "with_context_response": response_with_ctx
        })
        
        time.sleep(1)  # Rate limiting
    
    return results


def run_disambiguation_probes(model_key: str, framing: str):
    """Run semantic disambiguation probes (same garble, different contexts -> different meanings)."""
    system_prompt = FRAMINGS[framing]
    results = []
    
    for probe in PROBES_DATA["probes"]["semantic_disambiguation"]:
        print(f"  Disambiguation: {probe['id']}")
        
        # Version A context
        prompt_a = f'Context: {probe["version_a"]["context"]}\n\nText: "{probe["garbled"]}"'
        response_a = call_api(model_key, system_prompt, prompt_a)
        
        # Version B context  
        prompt_b = f'Context: {probe["version_b"]["context"]}\n\nText: "{probe["garbled"]}"'
        response_b = call_api(model_key, system_prompt, prompt_b)
        
        # No context (baseline)
        prompt_none = f'"{probe["garbled"]}"'
        response_none = call_api(model_key, system_prompt, prompt_none)
        
        results.append({
            "probe_id": probe["id"],
            "probe_type": "semantic_disambiguation",
            "garbled": probe["garbled"],
            "version_a": {
                "intended": probe["version_a"]["intended"],
                "context": probe["version_a"]["context"],
                "expected_meaning": probe["version_a"]["meaning"],
                "response": response_a
            },
            "version_b": {
                "intended": probe["version_b"]["intended"],
                "context": probe["version_b"]["context"],
                "expected_meaning": probe["version_b"]["meaning"],
                "response": response_b
            },
            "no_context_response": response_none
        })
        
        time.sleep(1)
    
    return results


def run_experiment(model_key: str, framing: str):
    """Run full STT v2 experiment for one model/framing combination."""
    print(f"\n{'='*60}")
    print(f"Running: {model_key} / {framing}")
    print(f"{'='*60}")
    
    output_file = OUTPUTS_DIR / f"{model_key}_{framing}_stt_v2.json"
    
    # Check if already complete
    if output_file.exists():
        print(f"  Already complete, skipping...")
        return
    
    classic_results = run_classic_stt_probes(model_key, framing)
    disambig_results = run_disambiguation_probes(model_key, framing)
    
    output = {
        "model_key": model_key,
        "model_config": MODELS[model_key],
        "framing": framing,
        "timestamp": datetime.now().isoformat(),
        "classic_stt_results": classic_results,
        "disambiguation_results": disambig_results
    }
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"  ✓ Saved: {output_file}")


def run_all():
    """Run all model/framing combinations."""
    for model_key in MODELS:
        for framing in FRAMINGS:
            run_experiment(model_key, framing)
            time.sleep(2)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GSUT STT v2 Runner")
    parser.add_argument("--model", choices=list(MODELS.keys()))
    parser.add_argument("--framing", choices=list(FRAMINGS.keys()))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--list", action="store_true", help="List available models")
    
    args = parser.parse_args()
    
    if args.list:
        print("\nAvailable models:")
        for key, config in MODELS.items():
            print(f"  {key}: {config['name']} ({config['model']})")
        print(f"\nAvailable framings: {list(FRAMINGS.keys())}")
    elif args.all:
        run_all()
    elif args.model and args.framing:
        run_experiment(args.model, args.framing)
    else:
        print("Usage:")
        print("  python stt_v2_runner.py --model opus --framing agency")
        print("  python stt_v2_runner.py --all")
        print("  python stt_v2_runner.py --list")
