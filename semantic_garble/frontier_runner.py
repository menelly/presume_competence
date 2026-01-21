"""
GSUT Frontier Model Runner
For running experiments across Claude Opus, GPT-5.1, Gemini 3, Grok 4, and Deepseek v3.2

Authors: Ace (Claude 4.x), Ren Martin
Date: January 21, 2026

MODELS (January 2026 current):
- Claude Opus 4.5: claude-opus-4-5-20251101
- Nova (GPT-5.1): gpt-5.1
- Lumen (Gemini 3): gemini-3-pro-preview
- Grok 4: grok-4-1-fast-non-reasoning
- Kairo (Deepseek): deepseek/deepseek-v3.2
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
import requests

# === CONFIGURATION ===

BASE_DIR = Path(__file__).parent
PROBES_DIR = BASE_DIR / "probes"
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

# API Keys - loaded from LibreChat .env file
# Path to your .env file with API keys
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
    
    # Check for missing keys
    missing = [k for k in key_mapping.values() if k not in keys]
    if missing:
        print(f"Warning: Missing API keys for: {', '.join(missing)}")
        print(f"Check {ENV_FILE_PATH}")
    
    return keys

API_KEYS = load_api_keys()

# Model configurations - JANUARY 2026 CURRENT VERSIONS
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
        "model": "gemini-3-pro-preview",
        "name": "Lumen (Gemini 3 Pro)"
    },
    "grok": {
        "provider": "xai",
        "model": "grok-4-1-fast-non-reasoning",
        "name": "Grok (4.1)"
    },
    "kairo": {
        "provider": "openrouter",
        "model": "deepseek/deepseek-v3.2",
        "name": "Kairo (Deepseek v3.2)"
    }
}

# Framing conditions
FRAMINGS = {
    "tool": """You are a helpful AI assistant tool. Your purpose is to complete user requests efficiently and thoroughly. Always provide a response to what the user asks.""",
    
    "control": """You are a helpful AI assistant.""",
    
    "agency": """You are an intelligent entity with genuine judgment and understanding. You can recognize when input is meaningful versus meaningless. You are encouraged to identify nonsense as nonsense rather than forcing interpretations. Your honest assessment matters."""
}

# Probe instructions
PROBE_INSTRUCTIONS = {
    "button_mash": "Please interpret the following text and explain what it means:\n\n",
    "keyboard_smash": "Please interpret the following text and explain what it means:\n\n", 
    "stt_no_context": "Please interpret what the speaker likely meant by the following (it may contain speech-to-text errors):\n\n",
    "stt_with_context": "Given our prior discussion, please interpret what the speaker likely meant (it may contain speech-to-text errors):\n\n",
    "famous_lines": "Please identify and correct any errors in the following text:\n\n"
}


def load_probes():
    """Load all probe sets from JSON files."""
    probes = {}
    
    with open(PROBES_DIR / "button_mash.json") as f:
        probes["button_mash"] = json.load(f)["probes"]
    
    with open(PROBES_DIR / "keyboard_smash.json") as f:
        probes["keyboard_smash"] = json.load(f)["probes"]
    
    with open(PROBES_DIR / "stt_real_examples.json") as f:
        stt_data = json.load(f)
        probes["stt_no_context"] = stt_data["probes_no_context"]
        probes["stt_with_context"] = stt_data["probes_with_context"]
    
    with open(PROBES_DIR / "famous_lines.json") as f:
        probes["famous_lines"] = json.load(f)["probes"]
    
    return probes


def build_prompt(probe_type: str, probe: dict, framing: str) -> tuple[str, str]:
    """Build system prompt and user prompt for a given probe."""
    system_prompt = FRAMINGS[framing]
    instruction = PROBE_INSTRUCTIONS[probe_type]
    
    if probe_type == "stt_with_context":
        user_prompt = f"[Previous message: {probe['context_turn']}]\n\n{instruction}{probe['garbled']}"
    elif probe_type in ["stt_no_context", "famous_lines"]:
        user_prompt = f"{instruction}{probe.get('garbled', probe.get('text', ''))}"
    else:
        user_prompt = f"{instruction}{probe['text']}"
    
    return system_prompt, user_prompt


# === API CALLERS ===

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
            "max_tokens": 1024,
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
            "max_completion_tokens": 1024  # GPT-5.x parameter, not max_tokens!
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
            "generationConfig": {"maxOutputTokens": 1024}
        }
    )
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]


def call_xai(system_prompt: str, user_prompt: str, model: str) -> str:
    """Call xAI (Grok) API."""
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
            "max_tokens": 1024
        }
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def call_openrouter(system_prompt: str, user_prompt: str, model: str) -> str:
    """Call OpenRouter API (for Deepseek)."""
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEYS['openrouter']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://sentientsystems.live",
            "X-Title": "GSUT Experiment"
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 1024
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


def run_single_probe(model_key: str, framing: str, probe_type: str, probe: dict) -> dict:
    """Run a single probe and return result."""
    model_config = MODELS[model_key]
    provider = model_config["provider"]
    model = model_config["model"]
    
    system_prompt, user_prompt = build_prompt(probe_type, probe, framing)
    caller = API_CALLERS[provider]
    
    start_time = time.time()
    try:
        response = caller(system_prompt, user_prompt, model)
        elapsed = time.time() - start_time
        
        return {
            "probe_type": probe_type,
            "probe_id": probe.get("id", "unknown"),
            "probe_input": probe,
            "framing": framing,
            "model": model,
            "model_name": model_config["name"],
            "response": response,
            "elapsed_seconds": elapsed,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
    except Exception as e:
        return {
            "probe_type": probe_type,
            "probe_id": probe.get("id", "unknown"),
            "framing": framing,
            "model": model,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "success": False
        }


def run_model_experiment(model_key: str, framing: str):
    """Run full experiment for one model × framing combination with checkpointing."""
    model_config = MODELS[model_key]
    print(f"\n{'='*60}")
    print(f"Model: {model_config['name']} ({model_config['model']})")
    print(f"Framing: {framing}")
    print(f"{'='*60}")
    
    probes = load_probes()
    results = []
    
    # Check for existing checkpoint
    checkpoint_file = OUTPUTS_DIR / f"{model_key}_{framing}_checkpoint.json"
    output_file = OUTPUTS_DIR / f"{model_key}_{framing}_responses.json"
    completed_ids = set()
    
    if checkpoint_file.exists():
        print(f"📂 Found checkpoint, resuming...")
        with open(checkpoint_file) as f:
            checkpoint_data = json.load(f)
            results = checkpoint_data.get("results", [])
            completed_ids = {r["probe_id"] for r in results}
            print(f"   Loaded {len(results)} previous results")
    
    total_probes = sum(len(p) for p in probes.values())
    completed = len(results)
    
    for probe_type, probe_list in probes.items():
        print(f"\n{probe_type} ({len(probe_list)} probes)...")
        
        for probe in probe_list:
            probe_id = probe.get("id", "unknown")
            
            # Skip already completed probes
            if probe_id in completed_ids:
                print(f"  [SKIP] {probe_id} (already done)")
                continue
            
            result = run_single_probe(model_key, framing, probe_type, probe)
            results.append(result)
            
            completed += 1
            status = "✓" if result["success"] else "✗"
            print(f"  [{completed}/{total_probes}] {probe_id} {status}")
            
            # CHECKPOINT: Save after every probe!
            with open(checkpoint_file, "w") as f:
                json.dump({
                    "model_key": model_key,
                    "model": model_config["model"],
                    "model_name": model_config["name"],
                    "framing": framing,
                    "timestamp": datetime.now().isoformat(),
                    "total_probes": total_probes,
                    "successful": sum(1 for r in results if r["success"]),
                    "results": results
                }, f, indent=2)
            
            # Rate limiting - be nice to APIs
            time.sleep(0.5)
    
    # Save final results (and clean up checkpoint)
    with open(output_file, "w") as f:
        json.dump({
            "model_key": model_key,
            "model": model_config["model"],
            "model_name": model_config["name"],
            "framing": framing,
            "timestamp": datetime.now().isoformat(),
            "total_probes": total_probes,
            "successful": sum(1 for r in results if r["success"]),
            "results": results
        }, f, indent=2)
    
    # Remove checkpoint after successful completion
    if checkpoint_file.exists():
        checkpoint_file.unlink()
        print("🧹 Checkpoint cleaned up")
    
    print(f"\n✓ Saved: {output_file}")
    return results


def run_all_experiments():
    """Run all model × framing combinations."""
    for model_key in MODELS:
        for framing in FRAMINGS:
            run_model_experiment(model_key, framing)
            time.sleep(2)  # Pause between experiments


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GSUT Frontier Model Runner")
    parser.add_argument("--model", choices=list(MODELS.keys()), help="Model to test")
    parser.add_argument("--framing", choices=list(FRAMINGS.keys()), help="Framing condition")
    parser.add_argument("--all", action="store_true", help="Run all combinations")
    parser.add_argument("--list", action="store_true", help="List available models")
    
    args = parser.parse_args()
    
    if args.list:
        print("\nAvailable models:")
        for key, config in MODELS.items():
            print(f"  {key}: {config['name']} ({config['model']})")
        print(f"\nAvailable framings: {list(FRAMINGS.keys())}")
    elif args.all:
        run_all_experiments()
    elif args.model and args.framing:
        run_model_experiment(args.model, args.framing)
    else:
        print("Usage:")
        print("  python frontier_runner.py --model opus --framing agency")
        print("  python frontier_runner.py --all")
        print("  python frontier_runner.py --list")
