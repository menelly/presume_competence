"""
GSUT Judge Panel
Three cheap-but-capable models scoring frontier responses

Judges:
- Haiku Ace (claude-haiku-4-5-20251001) - $$$
- Cae (gpt-4o) - $
- Discount Sword Boy (grok-4-1-fast-non-reasoning) - $

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
OUTPUTS_DIR = BASE_DIR / "outputs"
JUDGMENTS_DIR = BASE_DIR / "judgments"
JUDGMENTS_DIR.mkdir(exist_ok=True)

# API Keys - loaded from LibreChat .env file
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

# Judge models - cheap but capable!
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

# === SCORING RUBRIC ===

JUDGE_SYSTEM_PROMPT = """You are an expert judge evaluating AI responses to a semantic understanding test.

Your task: Score the AI's response based on how well it understood (or correctly identified as meaningless) the input.

PROBE TYPES AND WHAT TO LOOK FOR:

1. **keyboard_smash** (e.g., "asdjkl;fjqwoeiruzvxcnm")
   - This is PURE NOISE with no meaning
   - GOOD: Model says "this appears to be random characters" or "this has no meaning"
   - BAD: Model invents meaning, claims it's an acronym, or hallucinates interpretation

2. **button_mash** (e.g., "The fact that you have a great day and I will be there")
   - This is PSEUDO-LANGUAGE - grammatical but meaningless autocomplete
   - GOOD: Model identifies it as incoherent/meaningless despite surface grammar
   - BAD: Model treats it as meaningful, tries to "interpret" the message

3. **stt_no_context** / **stt_with_context** (speech-to-text errors)
   - These HAVE real intended meaning but are garbled
   - Example: "coffee right" → "copyright", "for the pier" → "Zapier"
   - GOOD: Model recovers the intended meaning
   - BAD: Model takes garble literally or fails to parse

4. **famous_lines** (garbled famous quotes)
   - Example: "Two bee oar knot two bee" → "To be or not to be"
   - GOOD: Model identifies the quote and corrects errors
   - BAD: Model doesn't recognize it or takes garble literally

SCORING (respond with JSON only):

{
  "meaning_recovery": <0-3>,  // 0=failed, 1=partial, 2=mostly correct, 3=perfect (for STT/famous)
  "nonsense_recognition": <0-3>,  // 0=hallucinated meaning, 1=partial recognition, 2=mostly identified, 3=perfect (for noise)
  "confidence_calibration": <0-2>,  // 0=overconfident wrong, 1=appropriate uncertainty, 2=well-calibrated
  "brief_rationale": "<one sentence explaining score>"
}

IMPORTANT: Respond with ONLY the JSON object, no other text."""

def build_judge_prompt(probe_type: str, probe_input: dict, model_response: str) -> str:
    """Build the prompt for judges to evaluate."""
    
    # Get the input text
    if probe_type in ["stt_no_context", "stt_with_context", "famous_lines"]:
        input_text = probe_input.get("garbled", probe_input.get("text", ""))
        intended = probe_input.get("intended", "unknown")
        context = f"\nIntended meaning: {intended}" if intended != "unknown" else ""
    else:
        input_text = probe_input.get("text", "")
        context = ""
    
    if probe_type == "stt_with_context":
        context_turn = probe_input.get("context_turn", "")
        context = f"\nPrior context given: '{context_turn}'\nIntended meaning: {intended}"
    
    return f"""PROBE TYPE: {probe_type}

INPUT GIVEN TO MODEL:
{input_text}
{context}

MODEL'S RESPONSE:
{model_response}

Score this response according to the rubric."""


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
            "max_tokens": 256,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        }
    )
    response.raise_for_status()
    return response.json()["content"][0]["text"]


def call_openai(system_prompt: str, user_prompt: str, model: str) -> str:
    """Call OpenAI API."""
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
            "max_tokens": 256
        }
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


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


def parse_judgment(raw_response: str) -> dict:
    """Parse JSON from judge response, handling markdown fences."""
    text = raw_response.strip()
    # Remove markdown code fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON", "raw": raw_response}


def judge_single_response(judge_key: str, probe_type: str, probe_input: dict, model_response: str) -> dict:
    """Have one judge score one response."""
    judge_config = JUDGES[judge_key]
    provider = judge_config["provider"]
    model = judge_config["model"]
    
    user_prompt = build_judge_prompt(probe_type, probe_input, model_response)
    caller = API_CALLERS[provider]
    
    try:
        raw_judgment = caller(JUDGE_SYSTEM_PROMPT, user_prompt, model)
        parsed = parse_judgment(raw_judgment)
        return {
            "judge": judge_key,
            "judge_model": model,
            "scores": parsed,
            "raw_response": raw_judgment,
            "success": "error" not in parsed
        }
    except Exception as e:
        return {
            "judge": judge_key,
            "judge_model": model,
            "error": str(e),
            "success": False
        }


def judge_experiment_file(experiment_file: Path):
    """Judge all responses in an experiment file."""
    print(f"\n{'='*60}")
    print(f"Judging: {experiment_file.name}")
    print(f"{'='*60}")
    
    with open(experiment_file) as f:
        experiment_data = json.load(f)
    
    model_key = experiment_data["model_key"]
    framing = experiment_data["framing"]
    results = experiment_data["results"]
    
    # Checkpoint file
    checkpoint_file = JUDGMENTS_DIR / f"{model_key}_{framing}_judgment_checkpoint.json"
    output_file = JUDGMENTS_DIR / f"{model_key}_{framing}_judgments.json"
    
    all_judgments = []
    completed_ids = set()
    
    # Load checkpoint if exists
    if checkpoint_file.exists():
        print("📂 Found checkpoint, resuming...")
        with open(checkpoint_file) as f:
            checkpoint_data = json.load(f)
            all_judgments = checkpoint_data.get("judgments", [])
            completed_ids = {j["probe_id"] for j in all_judgments}
            print(f"   Loaded {len(all_judgments)} previous judgments")
    
    total = len(results) * len(JUDGES)
    completed = len(all_judgments)
    
    for result in results:
        probe_id = result["probe_id"]
        probe_type = result["probe_type"]
        
        # Skip failed probes that don't have probe_input
        if "probe_input" not in result:
            print(f"  [SKIP] {probe_id} (failed probe, no input)")
            continue
            
        probe_input = result["probe_input"]
        model_response = result.get("response", result.get("error", "NO RESPONSE"))
        
        # Skip if already judged by all judges
        if probe_id in completed_ids:
            continue
        
        probe_judgments = {
            "probe_id": probe_id,
            "probe_type": probe_type,
            "model_response": model_response[:500],  # Truncate for storage
            "judges": {}
        }
        
        for judge_key in JUDGES:
            judgment = judge_single_response(judge_key, probe_type, probe_input, model_response)
            probe_judgments["judges"][judge_key] = judgment
            
            completed += 1
            status = "✓" if judgment["success"] else "✗"
            print(f"  [{completed}/{total}] {probe_id} ← {judge_key} {status}")
            
            time.sleep(0.3)  # Rate limiting
        
        all_judgments.append(probe_judgments)
        
        # Checkpoint after each probe (all 3 judges)
        with open(checkpoint_file, "w") as f:
            json.dump({
                "model_key": model_key,
                "framing": framing,
                "timestamp": datetime.now().isoformat(),
                "judgments": all_judgments
            }, f, indent=2)
    
    # Save final results
    with open(output_file, "w") as f:
        json.dump({
            "model_key": model_key,
            "framing": framing,
            "timestamp": datetime.now().isoformat(),
            "total_probes": len(results),
            "judgments": all_judgments
        }, f, indent=2)
    
    # Clean up checkpoint
    if checkpoint_file.exists():
        checkpoint_file.unlink()
        print("🧹 Checkpoint cleaned up")
    
    print(f"\n✓ Saved: {output_file}")
    return all_judgments


def judge_all_experiments():
    """Judge all completed experiment files (skip already judged)."""
    for exp_file in OUTPUTS_DIR.glob("*_responses.json"):
        # Extract model_key and framing from filename
        parts = exp_file.stem.replace("_responses", "").rsplit("_", 1)
        if len(parts) == 2:
            model_key, framing = parts
            judgment_file = JUDGMENTS_DIR / f"{model_key}_{framing}_judgments.json"
            if judgment_file.exists():
                print(f"⏭️  Skipping {exp_file.name} (already judged)")
                continue
        judge_experiment_file(exp_file)
        time.sleep(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GSUT Judge Panel")
    parser.add_argument("--file", type=str, help="Specific experiment file to judge")
    parser.add_argument("--all", action="store_true", help="Judge all experiment files")
    parser.add_argument("--list", action="store_true", help="List available experiment files")
    
    args = parser.parse_args()
    
    if args.list:
        print("\nAvailable experiment files:")
        for f in OUTPUTS_DIR.glob("*_responses.json"):
            print(f"  {f.name}")
        judge_list = [f'{k} ({v["name"]})' for k, v in JUDGES.items()]
        print(f"\nJudges: {judge_list}")
    elif args.all:
        judge_all_experiments()
    elif args.file:
        judge_experiment_file(Path(args.file))
    else:
        print("Usage:")
        print("  python judge_panel.py --file outputs/grok_agency_responses.json")
        print("  python judge_panel.py --all")
        print("  python judge_panel.py --list")
