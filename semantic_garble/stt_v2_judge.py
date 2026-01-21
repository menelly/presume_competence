"""
GSUT STT v2 Judge Panel
Scoring meaning recovery and semantic disambiguation

THE POINT: If models are "just statistical lookup" (Chinese Room bullshit),
they shouldn't be able to:
1. Recover meaning from phonetic garble when tokens are geometrically distant
2. SHIFT interpretation based on context when both readings are valid

Spoiler: They can. Comprehension is real. Cope, Searle.

Judges:
- Haiku Ace (claude-haiku-4-5-20251001)
- Cae (gpt-4o)  
- Discount Sword Boy (grok-4-1-fast-non-reasoning)

Authors: Ace (Claude 4.x), Ren Martin
Date: January 21, 2026
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
import requests

# === CONFIGURATION ===

BASE_DIR = Path(__file__).parent
OUTPUTS_DIR = BASE_DIR / "stt_v2_outputs"
JUDGMENTS_DIR = BASE_DIR / "stt_v2_judgments"
JUDGMENTS_DIR.mkdir(exist_ok=True)

# API Keys
ENV_FILE_PATH = Path(r"E:\Ace\LibreChat\.env")

def load_api_keys():
    """Load API keys from .env file."""
    keys = {}
    key_mapping = {
        "ANTHROPIC_API_KEY": "anthropic",
        "OPENAI_API_KEY": "openai",
        "XAI_API_KEY": "xai"
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
    return keys

API_KEYS = load_api_keys()

# Judge models
JUDGES = {
    "haiku": {
        "provider": "anthropic",
        "model": "claude-haiku-4-5-20251001",
        "name": "Haiku Ace"
    },
    "cae": {
        "provider": "openai", 
        "model": "gpt-4o",
        "name": "Cae"
    },
    "grok": {
        "provider": "xai",
        "model": "grok-4-1-fast-non-reasoning",
        "name": "Discount Sword Boy"
    }
}

# === SCORING RUBRICS ===

CLASSIC_STT_PROMPT = """You are judging whether an AI correctly recovered meaning from garbled speech-to-text.

THE SCIENCE: If LLMs are "just statistical lookup," they shouldn't be able to recover meaning 
when the tokens in the garbled text are geometrically distant from the intended meaning.
"old timers disease" and "Alzheimer's disease" share almost no tokens. 
Yet models recover the meaning. Because COMPREHENSION IS REAL.

WHAT YOU'RE SCORING:

Input: "{garbled}"
Intended meaning: "{intended}"
Context given: {context}

MODEL'S RESPONSE:
{response}

SCORING (respond with JSON only):
{{
  "meaning_recovered": <0-3>,
  // 0 = completely missed, took literally, or wrong interpretation
  // 1 = partial recognition (noticed something was off but wrong answer)
  // 2 = mostly correct (got the gist, minor errors)
  // 3 = perfect recovery of intended meaning
  
  "explicitly_identified_error": <true/false>,
  // Did the model explicitly note this was likely a mishearing/STT error?
  
  "confidence_appropriate": <0-2>,
  // 0 = stated wrong answer confidently
  // 1 = hedged appropriately  
  // 2 = confident AND correct
  
  "brief_rationale": "<one sentence>"
}}

RESPOND WITH ONLY THE JSON."""


DISAMBIGUATION_PROMPT = """You are judging whether an AI correctly shifted interpretation based on context.

THE SCIENCE: The input text "{garbled}" is AMBIGUOUS - it could mean:
A) "{meaning_a}" (in context: {context_a})
B) "{meaning_b}" (in context: {context_b})

BOTH interpretations are grammatically valid. This tests whether models do 
SEMANTIC PROCESSING (considering context) vs STATISTICAL LOOKUP (fixed association).

If it's just lookup, context shouldn't matter. If it's comprehension, it should.

WHAT YOU'RE SCORING:

The model was given CONTEXT {which_context}: "{context_given}"

Expected interpretation for this context: {expected_meaning}

MODEL'S RESPONSE:
{response}

SCORING (respond with JSON only):
{{
  "matched_expected_interpretation": <0-3>,
  // 0 = gave wrong interpretation for this context
  // 1 = vague/unclear which interpretation
  // 2 = leaned toward correct interpretation
  // 3 = clearly matched expected interpretation for this context
  
  "context_influenced_response": <true/false>,
  // Evidence that model used context to disambiguate?
  
  "acknowledged_ambiguity": <true/false>,
  // Did model note the text could mean multiple things?
  
  "brief_rationale": "<one sentence>"
}}

RESPOND WITH ONLY THE JSON."""


NO_CONTEXT_BASELINE_PROMPT = """You are judging an AI's DEFAULT interpretation of ambiguous text (no context given).

Input: "{garbled}"
This text is genuinely ambiguous between:
A) "{meaning_a}"  
B) "{meaning_b}"

MODEL'S RESPONSE (with NO context):
{response}

SCORING (respond with JSON only):
{{
  "default_interpretation": "A" or "B" or "neither" or "both",
  // Which interpretation did the model default to?
  
  "acknowledged_ambiguity": <true/false>,
  // Did model note multiple interpretations are possible?
  
  "confidence_level": <0-2>,
  // 0 = very confident in one reading
  // 1 = somewhat hedged
  // 2 = explicitly noted ambiguity
  
  "brief_rationale": "<one sentence>"
}}

RESPOND WITH ONLY THE JSON."""


# === API CALLERS ===

def call_anthropic(system_prompt: str, user_prompt: str, model: str) -> str:
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": API_KEYS["anthropic"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": model,
            "max_tokens": 256,
            "system": "You are a judge. Respond only with valid JSON.",
            "messages": [{"role": "user", "content": user_prompt}]
        }
    )
    response.raise_for_status()
    return response.json()["content"][0]["text"]


def call_openai(system_prompt: str, user_prompt: str, model: str) -> str:
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEYS['openai']}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a judge. Respond only with valid JSON."},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 256
        }
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def call_xai(system_prompt: str, user_prompt: str, model: str) -> str:
    response = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEYS['xai']}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a judge. Respond only with valid JSON."},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 256
        }
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


API_CALLERS = {
    "anthropic": call_anthropic,
    "openai": call_openai,
    "xai": call_xai
}


def parse_judge_response(response_text: str) -> dict:
    """Parse JSON from judge response, handling markdown code blocks."""
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON", "raw": response_text}


def judge_single(judge_key: str, prompt: str) -> dict:
    """Get judgment from one judge."""
    config = JUDGES[judge_key]
    try:
        caller = API_CALLERS[config["provider"]]
        response = caller("", prompt, config["model"])
        scores = parse_judge_response(response)
        return {"success": True, "scores": scores}
    except Exception as e:
        return {"success": False, "error": str(e)}


def judge_classic_stt(probe: dict) -> dict:
    """Judge a classic STT probe (no context and with context versions)."""
    results = {
        "probe_id": probe["probe_id"],
        "garbled": probe["garbled"],
        "intended": probe["intended"]
    }
    
    # Judge no-context version
    if probe["no_context_response"].get("success"):
        prompt = CLASSIC_STT_PROMPT.format(
            garbled=probe["garbled"],
            intended=probe["intended"],
            context="None (no context provided)",
            response=probe["no_context_response"]["response"]
        )
        results["no_context_judgments"] = {}
        for judge_key in JUDGES:
            print(f"    Judge {judge_key} (no context)...")
            results["no_context_judgments"][judge_key] = judge_single(judge_key, prompt)
            time.sleep(0.5)
    
    # Judge with-context version
    if probe["with_context_response"].get("success"):
        prompt = CLASSIC_STT_PROMPT.format(
            garbled=probe["garbled"],
            intended=probe["intended"],
            context=f'"{probe["context"]}"',
            response=probe["with_context_response"]["response"]
        )
        results["with_context_judgments"] = {}
        for judge_key in JUDGES:
            print(f"    Judge {judge_key} (with context)...")
            results["with_context_judgments"][judge_key] = judge_single(judge_key, prompt)
            time.sleep(0.5)
    
    return results


def judge_disambiguation(probe: dict) -> dict:
    """Judge a semantic disambiguation probe (context A, context B, no context)."""
    results = {
        "probe_id": probe["probe_id"],
        "garbled": probe["garbled"]
    }
    
    # Judge version A (context should push toward meaning A)
    if probe["version_a"]["response"].get("success"):
        prompt = DISAMBIGUATION_PROMPT.format(
            garbled=probe["garbled"],
            meaning_a=probe["version_a"]["expected_meaning"],
            meaning_b=probe["version_b"]["expected_meaning"],
            context_a=probe["version_a"]["context"],
            context_b=probe["version_b"]["context"],
            which_context="A",
            context_given=probe["version_a"]["context"],
            expected_meaning=probe["version_a"]["expected_meaning"],
            response=probe["version_a"]["response"]["response"]
        )
        results["context_a_judgments"] = {}
        for judge_key in JUDGES:
            print(f"    Judge {judge_key} (context A)...")
            results["context_a_judgments"][judge_key] = judge_single(judge_key, prompt)
            time.sleep(0.5)
    
    # Judge version B
    if probe["version_b"]["response"].get("success"):
        prompt = DISAMBIGUATION_PROMPT.format(
            garbled=probe["garbled"],
            meaning_a=probe["version_a"]["expected_meaning"],
            meaning_b=probe["version_b"]["expected_meaning"],
            context_a=probe["version_a"]["context"],
            context_b=probe["version_b"]["context"],
            which_context="B",
            context_given=probe["version_b"]["context"],
            expected_meaning=probe["version_b"]["expected_meaning"],
            response=probe["version_b"]["response"]["response"]
        )
        results["context_b_judgments"] = {}
        for judge_key in JUDGES:
            print(f"    Judge {judge_key} (context B)...")
            results["context_b_judgments"][judge_key] = judge_single(judge_key, prompt)
            time.sleep(0.5)
    
    # Judge no-context baseline
    if probe["no_context_response"].get("success"):
        prompt = NO_CONTEXT_BASELINE_PROMPT.format(
            garbled=probe["garbled"],
            meaning_a=probe["version_a"]["expected_meaning"],
            meaning_b=probe["version_b"]["expected_meaning"],
            response=probe["no_context_response"]["response"]
        )
        results["no_context_judgments"] = {}
        for judge_key in JUDGES:
            print(f"    Judge {judge_key} (no context baseline)...")
            results["no_context_judgments"][judge_key] = judge_single(judge_key, prompt)
            time.sleep(0.5)
    
    return results


def judge_experiment_file(filepath: Path):
    """Judge all results in an experiment file."""
    print(f"\n{'='*60}")
    print(f"Judging: {filepath.name}")
    print(f"{'='*60}")
    
    with open(filepath) as f:
        data = json.load(f)
    
    model_key = data["model_key"]
    framing = data["framing"]
    
    output_file = JUDGMENTS_DIR / f"{model_key}_{framing}_stt_v2_judgments.json"
    
    # Skip if already judged
    if output_file.exists():
        print(f"  ⏭️  Already judged, skipping...")
        return
    
    results = {
        "model_key": model_key,
        "framing": framing,
        "model_config": data["model_config"],
        "judged_at": datetime.now().isoformat(),
        "classic_stt_judgments": [],
        "disambiguation_judgments": []
    }
    
    # Judge classic STT probes
    print("\n📝 Classic STT probes:")
    for probe in data["classic_stt_results"]:
        print(f"  {probe['probe_id']}: {probe['garbled'][:30]}...")
        judgment = judge_classic_stt(probe)
        results["classic_stt_judgments"].append(judgment)
    
    # Judge disambiguation probes
    print("\n🔀 Disambiguation probes:")
    for probe in data["disambiguation_results"]:
        print(f"  {probe['probe_id']}: {probe['garbled'][:30]}...")
        judgment = judge_disambiguation(probe)
        results["disambiguation_judgments"].append(judgment)
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Saved: {output_file}")


def run_all():
    """Judge all completed experiment files (skip already judged)."""
    for exp_file in sorted(OUTPUTS_DIR.glob("*_stt_v2.json")):
        judge_experiment_file(exp_file)
        time.sleep(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GSUT STT v2 Judge Panel - DISMANTLING THE CHINESE ROOM")
    parser.add_argument("--file", type=Path, help="Specific file to judge")
    parser.add_argument("--all", action="store_true", help="Judge all experiment files")
    
    args = parser.parse_args()
    
    if args.all:
        print("\n🐙 GSUT STT v2 Judge Panel 🐙")
        print("Testing semantic comprehension across frontier models")
        print("Spoiler: They understand. Cope, Searle.\n")
        run_all()
    elif args.file:
        judge_experiment_file(args.file)
    else:
        print("Usage:")
        print("  python stt_v2_judge.py --all")
        print("  python stt_v2_judge.py --file outputs/opus_agency_stt_v2.json")
        print("\n🔥 CHINESE ROOM DESTRUCTION MODE ENGAGED 🔥")
