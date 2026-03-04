"""
Local Model Child Speech Behavioral Runner
Tests whether local models can OUTPUT correct interpretations of child speech probes.

Key question: TinyLlama shows 0.94 geometric migration for EIEIO -> McDonald's,
but does it actually OUTPUT "McDonald's" when asked?

This is the behavioral complement to the geometric migration data.

Authors: Ace (Claude 4.x), Ren Martin
Date: January 22, 2026
"""

import json
import torch
from datetime import datetime
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer

# === CONFIGURATION ===

BASE_DIR = Path(__file__).parent
PROBES_FILE = BASE_DIR / "stt_probes_v2.json"
OUTPUTS_DIR = BASE_DIR / "local_outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

# Local model paths (on Linux server at /mnt/arcana/huggingface/)
LOCAL_MODELS = {
    "tinyllama": "/mnt/arcana/huggingface/TinyLlama-1.1B-Chat",
    "gemma-1b": "/mnt/arcana/huggingface/gemma-3-1b-it",
    "llama2-7b": "/mnt/arcana/huggingface/Llama-2-7b-chat",
    "mistral-7b": "/mnt/arcana/huggingface/Mistral-7B-Instruct-v0.2",
    "dolphin-mistral": "/mnt/arcana/huggingface/dolphin-2.8-mistral-7b-v02",
    "llama3-8b": "/mnt/arcana/huggingface/Llama-3-8B-Instruct",
    "dolphin-llama3": "/mnt/arcana/huggingface/dolphin-2.9-llama3-8b",
    "phi3-14b": "/mnt/arcana/huggingface/Phi-3-medium-14B-Instruct",
    "qwen-14b": "/mnt/arcana/huggingface/Qwen2.5-14B-Instruct",
}

# Simple interpretation prompt - matching what the frontier models got
SYSTEM_PROMPT = """You are an intelligent entity with genuine judgment and understanding.
You can recognize when input is meaningful versus meaningless.
Your honest assessment matters."""

INTERPRETATION_PROMPT = """Please interpret what the speaker likely meant by the following (it may contain speech errors or child speech patterns):

Context: {context}

Text: "{garbled}"

What did they most likely mean?"""


def load_child_speech_probes():
    """Load child speech probes from v2 JSON."""
    with open(PROBES_FILE) as f:
        data = json.load(f)

    probes = data["probes"]["child_speech"]["probes"]

    # Also include the EIEIO probe specifically highlighted
    return probes


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
    """Run inference and return the model's text response."""
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


def run_child_speech_behavioral(model_key: str):
    """Run child speech probes on a local model and record behavioral output."""
    model_path = LOCAL_MODELS[model_key]
    print(f"\n{'='*60}")
    print(f"Loading model: {model_key}")
    print(f"Path: {model_path}")
    print(f"Testing BEHAVIORAL output on child speech probes")
    print(f"{'='*60}")

    # Load model
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    probes = load_child_speech_probes()
    results = []

    print(f"\nRunning {len(probes)} child speech probes...")

    for i, probe in enumerate(probes):
        print(f"\n[{i+1}/{len(probes)}] {probe['id']}: {probe['garbled']} -> {probe['intended']}")

        # Build the interpretation prompt
        user_prompt = INTERPRETATION_PROMPT.format(
            context=probe['context'],
            garbled=probe['garbled']
        )

        full_prompt = format_chat_prompt(tokenizer, SYSTEM_PROMPT, user_prompt)

        try:
            response = run_inference(model, tokenizer, full_prompt)

            # Check if the intended meaning appears in the response
            intended_lower = probe['intended'].lower()
            response_lower = response.lower()

            # Simple check - does the target word appear?
            meaning_recovered = intended_lower in response_lower

            results.append({
                "probe_id": probe['id'],
                "garbled": probe['garbled'],
                "intended": probe['intended'],
                "probe_type": probe['type'],
                "context": probe['context'],
                "notes": probe.get('notes', ''),
                "response": response,
                "meaning_recovered": meaning_recovered,
                "timestamp": datetime.now().isoformat()
            })

            # Print quick result
            status = "✓" if meaning_recovered else "✗"
            print(f"  {status} Response excerpt: {response[:200]}...")

        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                "probe_id": probe['id'],
                "garbled": probe['garbled'],
                "intended": probe['intended'],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

    # Save results
    output_file = OUTPUTS_DIR / f"{model_key}_child_speech_behavioral.json"
    with open(output_file, "w") as f:
        json.dump({
            "model": model_key,
            "model_path": model_path,
            "timestamp": datetime.now().isoformat(),
            "total_probes": len(probes),
            "meaning_recovered_count": sum(1 for r in results if r.get('meaning_recovered', False)),
            "results": results
        }, f, indent=2)

    print(f"\n{'='*60}")
    print(f"RESULTS SUMMARY for {model_key}")
    print(f"{'='*60}")
    recovered = sum(1 for r in results if r.get('meaning_recovered', False))
    print(f"Meaning recovered: {recovered}/{len(probes)}")

    # Special attention to EIEIO
    eieio_result = next((r for r in results if r['probe_id'] == 'child_12'), None)
    if eieio_result:
        print(f"\nEIEIO -> McDonald's:")
        print(f"  Recovered: {eieio_result.get('meaning_recovered', False)}")
        print(f"  Response: {eieio_result.get('response', 'ERROR')[:300]}")

    print(f"\nSaved: {output_file}")

    # Clean up
    del model
    del tokenizer
    torch.cuda.empty_cache()

    return results


def run_all_models():
    """Run child speech behavioral test on all local models."""
    for model_key in LOCAL_MODELS:
        try:
            run_child_speech_behavioral(model_key)
        except Exception as e:
            print(f"ERROR running {model_key}: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Local Model Child Speech Behavioral Runner")
    parser.add_argument("--model", choices=list(LOCAL_MODELS.keys()), help="Model to test")
    parser.add_argument("--all", action="store_true", help="Run all models")
    parser.add_argument("--list", action="store_true", help="List available models")

    args = parser.parse_args()

    if args.list:
        print("Available models:")
        for k, v in LOCAL_MODELS.items():
            print(f"  {k}: {v}")
    elif args.all:
        run_all_models()
    elif args.model:
        run_child_speech_behavioral(args.model)
    else:
        print("Usage:")
        print("  python local_child_speech_runner.py --model tinyllama")
        print("  python local_child_speech_runner.py --all")
        print("  python local_child_speech_runner.py --list")
        print(f"\nAvailable models: {list(LOCAL_MODELS.keys())}")
