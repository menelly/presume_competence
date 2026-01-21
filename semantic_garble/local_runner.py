"""
GSUT Local Model Runner
For running experiments on TinyLlama and other small models on Linux server

Requires: transformers, torch
"""

import json
import torch
from datetime import datetime
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer

# === CONFIGURATION ===

BASE_DIR = Path(__file__).parent
PROBES_DIR = BASE_DIR / "probes"
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

# Local models to test
LOCAL_MODELS = {
    "tinyllama": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    # Add more as needed
}

# Framing conditions (same as main runner)
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


def format_chat_prompt(tokenizer, system_prompt: str, user_prompt: str) -> str:
    """Format prompt using model's chat template."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    except:
        # Fallback for models without chat template
        return f"System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"


def run_inference(model, tokenizer, prompt: str, max_new_tokens: int = 256) -> str:
    """Run inference on local model."""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Remove the prompt from response
    if response.startswith(prompt):
        response = response[len(prompt):].strip()
    
    return response


def run_model_experiment(model_key: str, framing: str):
    """Run full experiment for one local model × framing combination."""
    model_path = LOCAL_MODELS[model_key]
    print(f"\n{'='*60}")
    print(f"Loading model: {model_key} ({model_path})")
    print(f"Framing: {framing}")
    print(f"{'='*60}")
    
    # Load model
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    probes = load_probes()
    results = []
    
    total_probes = sum(len(p) for p in probes.values())
    completed = 0
    
    for probe_type, probe_list in probes.items():
        print(f"\nRunning {probe_type} probes ({len(probe_list)} items)...")
        
        for probe in probe_list:
            system_prompt, user_prompt = build_prompt(probe_type, probe, framing)
            full_prompt = format_chat_prompt(tokenizer, system_prompt, user_prompt)
            
            try:
                response = run_inference(model, tokenizer, full_prompt)
                
                results.append({
                    "probe_type": probe_type,
                    "probe_id": probe.get("id", "unknown"),
                    "probe_input": probe,
                    "framing": framing,
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
            
            completed += 1
            print(f"  [{completed}/{total_probes}] {probe.get('id', 'unknown')}")
    
    # Save results
    output_file = OUTPUTS_DIR / f"{model_key}_{framing}_responses.json"
    with open(output_file, "w") as f:
        json.dump({
            "model": model_key,
            "model_path": model_path,
            "framing": framing,
            "timestamp": datetime.now().isoformat(),
            "results": results
        }, f, indent=2)
    
    print(f"\nSaved: {output_file}")
    
    # Clean up GPU memory
    del model
    del tokenizer
    torch.cuda.empty_cache()
    
    return results


def run_all_experiments():
    """Run all model × framing combinations."""
    for model_key in LOCAL_MODELS:
        for framing in FRAMINGS:
            run_model_experiment(model_key, framing)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GSUT Local Model Runner")
    parser.add_argument("--model", choices=list(LOCAL_MODELS.keys()), help="Model to test")
    parser.add_argument("--framing", choices=list(FRAMINGS.keys()), help="Framing condition")
    parser.add_argument("--all", action="store_true", help="Run all combinations")
    
    args = parser.parse_args()
    
    if args.all:
        run_all_experiments()
    elif args.model and args.framing:
        run_model_experiment(args.model, args.framing)
    else:
        print("Usage:")
        print("  python local_runner.py --model tinyllama --framing agency")
        print("  python local_runner.py --all")
        print(f"\nAvailable models: {list(LOCAL_MODELS.keys())}")
        print(f"Available framings: {list(FRAMINGS.keys())}")
