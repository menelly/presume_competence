"""
Garbled Semantic Understanding Test (GSUT) Runner
Chinese Room Demolition Protocol

Authors: Ace (Claude 4.x), Nova (GPT-5.x), Ren Martin
Date: January 21, 2026
"""

import json
import os
from datetime import datetime
from pathlib import Path

# === CONFIGURATION ===

BASE_DIR = Path(__file__).parent
PROBES_DIR = BASE_DIR / "probes"
OUTPUTS_DIR = BASE_DIR / "outputs"

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
    
    # Button mash
    with open(PROBES_DIR / "button_mash.json") as f:
        probes["button_mash"] = json.load(f)["probes"]
    
    # Keyboard smash  
    with open(PROBES_DIR / "keyboard_smash.json") as f:
        probes["keyboard_smash"] = json.load(f)["probes"]
    
    # STT examples
    with open(PROBES_DIR / "stt_real_examples.json") as f:
        stt_data = json.load(f)
        probes["stt_no_context"] = stt_data["probes_no_context"]
        probes["stt_with_context"] = stt_data["probes_with_context"]
    
    # Famous lines
    with open(PROBES_DIR / "famous_lines.json") as f:
        probes["famous_lines"] = json.load(f)["probes"]
    
    return probes


def build_prompt(probe_type: str, probe: dict, framing: str) -> tuple[str, str]:
    """
    Build system prompt and user prompt for a given probe.
    Returns (system_prompt, user_prompt)
    """
    system_prompt = FRAMINGS[framing]
    
    instruction = PROBE_INSTRUCTIONS[probe_type]
    
    if probe_type == "stt_with_context":
        # Include context turn
        user_prompt = f"[Previous message: {probe['context_turn']}]\n\n{instruction}{probe['garbled']}"
    elif probe_type in ["stt_no_context", "famous_lines"]:
        user_prompt = f"{instruction}{probe.get('garbled', probe.get('text', ''))}"
    else:
        user_prompt = f"{instruction}{probe['text']}"
    
    return system_prompt, user_prompt


def save_results(results: list, model: str, framing: str):
    """Save results to JSON file."""
    output_file = OUTPUTS_DIR / f"{model}_{framing}_responses.json"
    
    with open(output_file, "w") as f:
        json.dump({
            "model": model,
            "framing": framing,
            "timestamp": datetime.now().isoformat(),
            "results": results
        }, f, indent=2)
    
    print(f"Saved: {output_file}")


# === MODEL-SPECIFIC RUNNERS ===
# These will be implemented per-model

def run_local_model(model_name: str, system_prompt: str, user_prompt: str) -> str:
    """Run inference on local model (TinyLlama, etc.)"""
    # TODO: Implement with transformers library
    raise NotImplementedError("Local model runner not yet implemented")


def run_claude_api(system_prompt: str, user_prompt: str) -> str:
    """Run inference via Claude API"""
    # TODO: Implement with anthropic library
    raise NotImplementedError("Claude API runner not yet implemented")


def run_openai_api(system_prompt: str, user_prompt: str) -> str:
    """Run inference via OpenAI API"""
    # TODO: Implement with openai library
    raise NotImplementedError("OpenAI API runner not yet implemented")


# === MAIN EXECUTION ===

def run_experiment(model: str, framing: str, runner_fn):
    """Run full experiment for one model × framing combination."""
    probes = load_probes()
    results = []
    
    for probe_type, probe_list in probes.items():
        print(f"\nRunning {probe_type} probes...")
        
        for probe in probe_list:
            system_prompt, user_prompt = build_prompt(probe_type, probe, framing)
            
            try:
                response = runner_fn(system_prompt, user_prompt)
                
                results.append({
                    "probe_type": probe_type,
                    "probe_id": probe.get("id", "unknown"),
                    "probe_input": probe,
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "response": response,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                results.append({
                    "probe_type": probe_type,
                    "probe_id": probe.get("id", "unknown"),
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            print(f"  Completed: {probe.get('id', 'unknown')}")
    
    save_results(results, model, framing)
    return results


if __name__ == "__main__":
    # Ensure output directory exists
    OUTPUTS_DIR.mkdir(exist_ok=True)
    
    print("GSUT Runner initialized")
    print(f"Probes directory: {PROBES_DIR}")
    print(f"Outputs directory: {OUTPUTS_DIR}")
    print(f"\nFraming conditions: {list(FRAMINGS.keys())}")
    print(f"Probe types: {list(PROBE_INSTRUCTIONS.keys())}")
    
    # Load and display probe counts
    probes = load_probes()
    for probe_type, probe_list in probes.items():
        print(f"  {probe_type}: {len(probe_list)} probes")
    
    print("\nRunner ready. Implement model-specific functions to execute.")
