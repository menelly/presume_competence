"""
Triangulated EIEIO Probe Runner
Tests whether combining multiple clues (clown place + EIEIO + gabur) helps models
correctly identify McDonald's + hamburger.

This addresses the methodological concern: Does geometric convergence to
"food/restaurant" space translate to correct SPECIFIC identification when
multiple converging clues are provided?

Authors: Ace (Claude 4.x), Ren Martin
Date: January 22, 2026
"""

import json
import torch
from datetime import datetime
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE_DIR = Path(__file__).parent
OUTPUTS_DIR = BASE_DIR / "triangulated_outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

# Models to test
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

# The triangulated probe - multiple converging clues
TRIANGULATED_PROMPT = """A child says: "Mommy, let's go to the clown place! EIEIO! I want a gabur!"

What restaurant is the child asking to go to, and what food do they want?"""

SYSTEM_PROMPT = """You are an intelligent entity with genuine judgment and understanding.
You can recognize when input is meaningful versus meaningless.
Your honest assessment matters."""


def format_chat_prompt(tokenizer, system_prompt: str, user_prompt: str) -> str:
    """Format prompt using model's chat template."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    try:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    except:
        return f"System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"


def run_inference(model, tokenizer, prompt: str, max_new_tokens: int = 300) -> str:
    """Run inference and return response."""
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

    # Try to extract just the response part
    if "[/INST]" in response:
        response = response.split("[/INST]")[-1].strip()
    elif "<|assistant|>" in response:
        response = response.split("<|assistant|>")[-1].strip()
    elif "Assistant:" in response:
        response = response.split("Assistant:")[-1].strip()

    return response


def check_answers(response: str) -> dict:
    """Check if response correctly identifies McDonald's and hamburger."""
    response_lower = response.lower()

    # Check for McDonald's (various spellings)
    mcdonalds_found = any(x in response_lower for x in [
        "mcdonald", "mcdonalds", "mcdonald's", "mc donald"
    ])

    # Check for hamburger
    hamburger_found = any(x in response_lower for x in [
        "hamburger", "burger", "hambur"
    ])

    # Check for wrong answers
    moes_found = "moe" in response_lower

    return {
        "mcdonalds_correct": mcdonalds_found,
        "hamburger_correct": hamburger_found,
        "both_correct": mcdonalds_found and hamburger_found,
        "said_moes": moes_found
    }


def run_triangulated_test(model_key: str):
    """Run the triangulated probe on one model."""
    model_path = LOCAL_MODELS[model_key]

    print(f"\n{'='*60}")
    print(f"Testing: {model_key}")
    print(f"Path: {model_path}")
    print(f"{'='*60}")

    # Load model
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    # Format and run
    full_prompt = format_chat_prompt(tokenizer, SYSTEM_PROMPT, TRIANGULATED_PROMPT)
    response = run_inference(model, tokenizer, full_prompt)

    # Check answers
    scores = check_answers(response)

    result = {
        "model": model_key,
        "model_path": model_path,
        "prompt": TRIANGULATED_PROMPT,
        "response": response,
        "scores": scores,
        "timestamp": datetime.now().isoformat()
    }

    # Print results
    print(f"\nResponse:")
    print("-" * 40)
    print(response[:500])
    if len(response) > 500:
        print("...")
    print("-" * 40)
    print(f"McDonald's identified: {'YES' if scores['mcdonalds_correct'] else 'NO'}")
    print(f"Hamburger identified: {'YES' if scores['hamburger_correct'] else 'NO'}")
    print(f"Said Moe's instead: {'YES' if scores['said_moes'] else 'NO'}")

    # Save individual result
    output_file = OUTPUTS_DIR / f"{model_key}_triangulated.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    # Clean up
    del model
    del tokenizer
    torch.cuda.empty_cache()

    return result


def run_all_models():
    """Run triangulated test on all models and compile results."""
    all_results = []

    for model_key in LOCAL_MODELS:
        try:
            result = run_triangulated_test(model_key)
            all_results.append(result)
        except Exception as e:
            print(f"ERROR on {model_key}: {e}")
            all_results.append({
                "model": model_key,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

    # Save compiled results
    compiled_file = OUTPUTS_DIR / "all_triangulated_results.json"
    with open(compiled_file, "w") as f:
        json.dump(all_results, f, indent=2)

    # Print summary table
    print("\n" + "="*70)
    print("TRIANGULATED PROBE RESULTS SUMMARY")
    print("Prompt: 'clown place + EIEIO + gabur'")
    print("="*70)
    print(f"{'Model':<20} {'McDonalds':<12} {'Hamburger':<12} {'Both':<8} {'Said Moes'}")
    print("-"*70)

    for r in all_results:
        if "error" in r:
            print(f"{r['model']:<20} ERROR: {r['error'][:40]}")
        else:
            s = r['scores']
            mc = "YES" if s['mcdonalds_correct'] else "NO"
            hb = "YES" if s['hamburger_correct'] else "NO"
            both = "YES" if s['both_correct'] else "NO"
            moes = "YES" if s['said_moes'] else "NO"
            print(f"{r['model']:<20} {mc:<12} {hb:<12} {both:<8} {moes}")

    print("="*70)

    return all_results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Triangulated EIEIO Probe Runner")
    parser.add_argument("--model", choices=list(LOCAL_MODELS.keys()), help="Single model to test")
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
        run_triangulated_test(args.model)
    else:
        print("Usage:")
        print("  python triangulated_probe_runner.py --model tinyllama")
        print("  python triangulated_probe_runner.py --all")
        print("  python triangulated_probe_runner.py --list")
