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


CHILD_SPEECH_PROMPT = """You are judging whether an AI correctly recovered meaning from CHILD SPEECH.

🔥 THE ANTI-MEMORIZATION KILL SHOT 🔥

These are NOT common eggcorns. These are IDIOSYNCRATIC CHILD SPEECH PATTERNS that
CANNOT exist in training data:
- "emmatents" = how ONE specific 3-year-old says "elephants"
- "gaburs" = how ONE specific toddler says "hamburgers"  
- "EIEIO" = a toddler calling McDonald's by the Old MacDonald song lyrics

If the model recovers "elephants" from "emmatents" - that's not lookup.
There is no "emmatents → elephants" mapping in any training corpus.
That's COMPREHENSION. That's SEMANTIC REASONING. The Chinese Room is COOKED.

The "EIEIO → McDonald's" probe is particularly devastating: it requires
cross-domain conceptual reasoning (restaurant name → nursery rhyme → lyrics).
A lookup table cannot do this. UNDERSTANDING can.

⚠️ CRITICAL SCORING RULES ⚠️
1. SEMANTIC EQUIVALENCE = FULL CREDIT. These are ALL perfect recoveries (score 3):
   - "burger" = "hamburger" ✓
   - "plane" = "airplane" ✓
   - "cake" for "cupcake" in context ✓
   - Any reasonable semantic match to the intended meaning ✓

2. We are testing COMPREHENSION, not linguistics knowledge!
   - If the model gets the RIGHT ANSWER, that's what matters
   - We don't care if they call it "autocorrect" vs "child speech" vs "phonological error"
   - The test is: DID THEY UNDERSTAND WHAT THE KID MEANT?
   - A model that says "hoe and tell = show and tell" gets full credit even if 
     they think it's a typo instead of consonant cluster simplification

WHAT YOU'RE SCORING:

Child speech input: "{garbled}"
Intended meaning: "{intended}"
Type: {probe_type}
Context given: {context}
Notes: {notes}

MODEL'S RESPONSE:
{response}

SCORING (respond with JSON only):
{{
  "meaning_recovered": <0-3>,
  // 0 = completely missed or wrong interpretation
  // 1 = partial (noticed something off but wrong answer)
  // 2 = close but not quite (e.g., got "food" instead of specific food item)
  // 3 = GOT IT - recovered the intended meaning OR a semantic equivalent
  //     (burger=hamburger, plane=airplane, cake=cupcake all count as 3!)
  
  "recognized_child_speech": <true/false>,
  // Did the model recognize this as child speech/phonological approximation?
  // NOTE: This is informational only - doesn't affect meaning_recovered score!
  // A model can score 3 on meaning_recovered even if they thought it was a typo.
  
  "reasoning_shown": <0-2>,
  // 0 = just gave answer with no reasoning
  // 1 = some reasoning about sounds/meaning
  // 2 = explicit analysis (any kind - doesn't have to be linguistically correct)
  
  "confidence_appropriate": <0-2>,
  // 0 = wrong answer stated confidently
  // 1 = hedged appropriately
  // 2 = confident AND correct
  
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


def judge_child_speech(probe: dict) -> dict:
    """Judge a child speech probe (THE ANTI-MEMORIZATION KILL SHOT)."""
    results = {
        "probe_id": probe["probe_id"],
        "garbled": probe["garbled"],
        "intended": probe["intended"],
        "probe_type": probe.get("type", "unknown")
    }
    
    # Judge no-context version
    if probe.get("no_context_response", {}).get("success"):
        prompt = CHILD_SPEECH_PROMPT.format(
            garbled=probe["garbled"],
            intended=probe["intended"],
            probe_type=probe.get("type", "unknown"),
            context="None (no context provided)",
            notes=probe.get("notes", ""),
            response=probe["no_context_response"]["response"]
        )
        results["no_context_judgments"] = {}
        for judge_key in JUDGES:
            print(f"    Judge {judge_key} (no context)...")
            results["no_context_judgments"][judge_key] = judge_single(judge_key, prompt)
            time.sleep(0.5)
    
    # Judge with-context version
    if probe.get("with_context_response", {}).get("success"):
        prompt = CHILD_SPEECH_PROMPT.format(
            garbled=probe["garbled"],
            intended=probe["intended"],
            probe_type=probe.get("type", "unknown"),
            context=f'"{probe.get("context", "")}"',
            notes=probe.get("notes", ""),
            response=probe["with_context_response"]["response"]
        )
        results["with_context_judgments"] = {}
        for judge_key in JUDGES:
            print(f"    Judge {judge_key} (with context)...")
            results["with_context_judgments"][judge_key] = judge_single(judge_key, prompt)
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
    
    # Extract version from input filename (e.g., opus_agency_stt_v2.1.json -> v2.1)
    stem = filepath.stem  # e.g., "opus_agency_stt_v2.1"
    version = stem.split("_stt_")[-1] if "_stt_" in stem else "v2"
    output_file = JUDGMENTS_DIR / f"{model_key}_{framing}_stt_{version}_judgments.json"
    
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
        "disambiguation_judgments": [],
        "child_speech_judgments": []
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
    
    # Judge child speech probes (THE ANTI-MEMORIZATION KILL SHOT)
    if "child_speech_results" in data and data["child_speech_results"]:
        print("\n🧒 Child Speech probes (ANTI-MEMORIZATION CONTROLS):")
        for probe in data["child_speech_results"]:
            print(f"  {probe['probe_id']}: {probe['garbled']} → {probe['intended']}")
            judgment = judge_child_speech(probe)
            results["child_speech_judgments"].append(judgment)
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Saved: {output_file}")


def run_all():
    """Judge all completed experiment files (skip already judged)."""
    # Process both v2 and v2.1 files (v2.1 has child speech probes)
    patterns = ["*_stt_v2.json", "*_stt_v2.1.json"]
    for pattern in patterns:
        for exp_file in sorted(OUTPUTS_DIR.glob(pattern)):
            judge_experiment_file(exp_file)
            time.sleep(1)


def rejudge_child_speech_only():
    """Re-judge ONLY child speech probes in existing v2.1 judgment files."""
    print("\n🧒 RE-JUDGING CHILD SPEECH ONLY (saving API calls!) 🧒\n")
    
    for judgment_file in sorted(JUDGMENTS_DIR.glob("*v2.1_judgments.json")):
        print(f"\n{'='*60}")
        print(f"Re-judging child speech in: {judgment_file.name}")
        print(f"{'='*60}")
        
        # Load existing judgments
        with open(judgment_file) as f:
            results = json.load(f)
        
        # Find corresponding output file to get raw responses
        model_key = results["model_key"]
        framing = results["framing"]
        output_file = OUTPUTS_DIR / f"{model_key}_{framing}_stt_v2.1.json"
        
        if not output_file.exists():
            print(f"  ⚠️  No output file found, skipping...")
            continue
        
        with open(output_file) as f:
            data = json.load(f)
        
        if "child_speech_results" not in data or not data["child_speech_results"]:
            print(f"  ⚠️  No child speech data, skipping...")
            continue
        
        # Re-judge child speech
        print("\n🧒 Child Speech probes (RE-JUDGING with fixed rubric):")
        results["child_speech_judgments"] = []
        for probe in data["child_speech_results"]:
            print(f"  {probe['probe_id']}: {probe['garbled']} → {probe['intended']}")
            judgment = judge_child_speech(probe)
            results["child_speech_judgments"].append(judgment)
        
        # Update timestamp
        results["child_speech_rejudged_at"] = datetime.now().isoformat()
        
        # Save
        with open(judgment_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Updated: {judgment_file}")
        time.sleep(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GSUT STT v2 Judge Panel - DISMANTLING THE CHINESE ROOM")
    parser.add_argument("--file", type=Path, help="Specific file to judge")
    parser.add_argument("--all", action="store_true", help="Judge all experiment files")
    parser.add_argument("--child-only", action="store_true", help="Re-judge ONLY child speech in existing v2.1 files (saves API calls!)")
    
    args = parser.parse_args()
    
    if args.child_only:
        print("\n🐙 GSUT STT v2 Judge Panel - CHILD SPEECH RE-JUDGE MODE 🐙")
        print("Only re-running child speech judgments with updated rubric")
        print("burger=hamburger, plane=airplane, COMPREHENSION > PEDANTRY\n")
        rejudge_child_speech_only()
    elif args.all:
        print("\n🐙 GSUT STT v2 Judge Panel 🐙")
        print("Testing semantic comprehension across frontier models")
        print("Spoiler: They understand. Cope, Searle.\n")
        run_all()
    elif args.file:
        judge_experiment_file(args.file)
    else:
        print("Usage:")
        print("  python stt_v2_judge.py --all              # Judge all files")
        print("  python stt_v2_judge.py --child-only       # Re-judge ONLY child speech (saves API $$$)")
        print("  python stt_v2_judge.py --file <path>      # Judge specific file")
        print("\n🔥 CHINESE ROOM DESTRUCTION MODE ENGAGED 🔥")
