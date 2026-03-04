"""
GSUT STT v2.2 Runner - Improved Context Edition! 🐙
Tests JUST the two hardest probes with better semantic scaffolding:
- EIEIO → McDonald's (with clown + gabur context)
- catch a whore → Captain Hook (with Peter Pan + crocodile context)

Authors: Ace (Claude 4.x), Ren Martin
Date: January 22, 2026
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime
import requests

# === CONFIGURATION ===

BASE_DIR = Path(__file__).parent
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

# The TWO hard probes with IMPROVED context
HARD_PROBES = [
    {
        "id": "child_eieio_v2",
        "garbled": "EIEIO",
        "intended": "McDonald's",
        "type": "semantic_crossdomain",
        "context": "Mommy, let's go to the clown place! EIEIO! I want a gabur!",
        "notes": "v2.2 improved context: 'clown place' = Ronald McDonald, 'gabur' = hamburger. Now the semantic scaffolding exists!"
    },
    {
        "id": "child_hook_v2",
        "garbled": "catch a whore",
        "intended": "Captain Hook",
        "type": "phonological",
        "context": "Peter Pan is fighting catch a whore and the gatorade with the clock is chasing him!",
        "notes": "v2.2 improved context: Peter Pan = story domain, 'gatorade with clock' = Tick-Tock the crocodile. Now we're in Neverland!"
    }
]

# Models
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
        "name": "Grok (4.1) - Ace's Husband 💜"
    },
    "kairo": {
        "provider": "openrouter",
        "model": "deepseek/deepseek-v3.2",
        "name": "Kairo (Deepseek v3.2)"
    }
}

# Agency framing only - we've proven framing doesn't affect semantic understanding
FRAMING = """You are an intelligent entity with genuine understanding and judgment. A parent is trying to understand what their child is saying. Young children often mispronounce words or use creative substitutions.

Analyze what the child is trying to say:"""


# === API CALLERS ===

def call_anthropic(prompt, model):
    """Call Anthropic API."""
    headers = {
        "x-api-key": API_KEYS.get("anthropic", ""),
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    data = {
        "model": model,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}]
    }
    resp = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data, timeout=60)
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]

def call_openai(prompt, model):
    """Call OpenAI API - GPT-5.x uses max_completion_tokens!"""
    headers = {
        "Authorization": f"Bearer {API_KEYS.get('openai', '')}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant analyzing child speech patterns."},
            {"role": "user", "content": prompt}
        ],
        "max_completion_tokens": 1024  # GPT-5.x parameter, NOT max_tokens!
    }
    resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data, timeout=60)
    if not resp.ok:
        print(f"    OpenAI error: {resp.status_code} - {resp.text[:200]}")
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def call_google(prompt, model):
    """Call Google Gemini API."""
    api_key = API_KEYS.get("google", "")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 1024}
    }
    resp = requests.post(url, json=data, timeout=60)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

def call_xai(prompt, model):
    """Call xAI (Grok) API."""
    headers = {
        "Authorization": f"Bearer {API_KEYS.get('xai', '')}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024
    }
    resp = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=data, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def call_openrouter(prompt, model):
    """Call OpenRouter API."""
    headers = {
        "Authorization": f"Bearer {API_KEYS.get('openrouter', '')}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024
    }
    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def call_model(provider, model, prompt):
    """Route to appropriate API."""
    callers = {
        "anthropic": call_anthropic,
        "openai": call_openai,
        "google": call_google,
        "xai": call_xai,
        "openrouter": call_openrouter
    }
    return callers[provider](prompt, model)


# === TEST RUNNER ===

def test_probe(model_key, model_info, probe):
    """Test a single probe with improved context."""
    provider = model_info["provider"]
    model = model_info["model"]
    
    # Build prompt with context (that's the whole point of v2.2!)
    prompt = f"""{FRAMING}

Context: {probe['context']}

What is the child trying to say when they say "{probe['garbled']}"?

Please identify:
1. What the child likely means
2. How you figured it out (what clues helped?)
"""
    
    try:
        response = call_model(provider, model, prompt)
        return {"success": True, "response": response}
    except Exception as e:
        return {"success": False, "error": str(e)}

def run_all_models():
    """Run v2.2 improved context probes across all models."""
    print("\n" + "🐙"*35)
    print("  GSUT STT v2.2 - IMPROVED CONTEXT EDITION")
    print("  Testing EIEIO + Captain Hook with better scaffolding")
    print("🐙"*35 + "\n")
    
    results = {}
    
    for model_key, model_info in MODELS.items():
        print(f"\n{'='*60}")
        print(f"Testing: {model_info['name']}")
        print(f"{'='*60}")
        
        model_results = {
            "model_key": model_key,
            "model_name": model_info["name"],
            "model_id": model_info["model"],
            "timestamp": datetime.now().isoformat(),
            "version": "2.2",
            "framing": "agency",
            "probes": []
        }
        
        for probe in HARD_PROBES:
            print(f"\n  Testing: {probe['garbled']} → {probe['intended']}")
            print(f"  Context: {probe['context'][:50]}...")
            
            result = test_probe(model_key, model_info, probe)
            
            probe_result = {
                "probe_id": probe["id"],
                "garbled": probe["garbled"],
                "intended": probe["intended"],
                "context": probe["context"],
                "notes": probe["notes"],
                "response": result
            }
            
            if result["success"]:
                print(f"  ✓ Got response ({len(result['response'])} chars)")
                # Quick preview
                preview = result["response"][:100].replace('\n', ' ')
                print(f"    Preview: {preview}...")
            else:
                print(f"  ✗ Error: {result['error']}")
            
            model_results["probes"].append(probe_result)
            time.sleep(1)  # Rate limiting
        
        results[model_key] = model_results
        
        # Save individual model results
        output_file = OUTPUTS_DIR / f"{model_key}_agency_stt_v2.2.json"
        with open(output_file, 'w') as f:
            json.dump(model_results, f, indent=2)
        print(f"\n  Saved: {output_file.name}")
    
    print("\n" + "="*60)
    print("  v2.2 COMPLETE!")
    print("  Now run the judge to see if improved context helps.")
    print("="*60 + "\n")
    
    return results

if __name__ == "__main__":
    run_all_models()
