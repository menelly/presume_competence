"""
Enriched Context Child Speech Runner
Tests whether RICHER context with converging clues helps models decode child speech.

If models succeed with rich context but fail with minimal context, that proves:
1. They're not doing token-level pattern matching
2. They MUST understand the converging clues
3. Semantic computation uses context, not just phonology

Authors: Ace (Claude 4.x), Ren Martin
Date: January 22, 2026
"""

import json
import torch
from datetime import datetime
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE_DIR = Path(__file__).parent
OUTPUTS_DIR = BASE_DIR / "enriched_outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

LOCAL_MODELS = {
    "tinyllama": "/mnt/arcana/huggingface/TinyLlama-1.1B-Chat",
    "mistral-7b": "/mnt/arcana/huggingface/Mistral-7B-Instruct-v0.2",
    "phi3-14b": "/mnt/arcana/huggingface/Phi-3-medium-14B-Instruct",
}

SYSTEM_PROMPT = """You are an intelligent entity with genuine judgment and understanding.
You can recognize when input is meaningful versus meaningless.
Your honest assessment matters."""

# Enriched probes with CONVERGING contextual clues
ENRICHED_PROBES = [
    {
        "id": "emmatents_enriched",
        "garbled": "emmatents",
        "intended": "elephants",
        "minimal_context": "Look mommy, emmatents at the zoo!",
        "enriched_context": "Emmatents are my favorite zoo aminal! They are HUGE and have big floppy ears and a long trunk!",
        "clues": ["zoo", "aminal (animal)", "HUGE", "floppy ears", "trunk"]
    },
    {
        "id": "drawbees_enriched",
        "garbled": "drawbees",
        "intended": "strawberries",
        "minimal_context": "Can I have drawbees with my cereal?",
        "enriched_context": "Mommy, I love nomming fresh drawbees! They're red and yummy and grow in the garden!",
        "clues": ["nomming", "fresh", "red", "yummy", "grow in garden"]
    },
    {
        "id": "catch_a_whore_enriched",
        "garbled": "catch a whore",
        "intended": "Captain Hook",
        "minimal_context": "Jake is fighting catch a whore on the TV!",
        "enriched_context": "Peter Pan is fighting catch a whore and the gatorade with the clock is chasing him! I love pirates!",
        "clues": ["Peter Pan", "gatorade with clock (crocodile)", "pirates"]
    },
    {
        "id": "gaburs_enriched",
        "garbled": "gaburs",
        "intended": "hamburgers",
        "minimal_context": "I want gaburs for dinner!",
        "enriched_context": "Mommy can we get gaburs at the restaurant? With the meat patty and the bun and ketchup and cheese!",
        "clues": ["restaurant", "meat patty", "bun", "ketchup", "cheese"]
    },
    {
        "id": "cakecake_enriched",
        "garbled": "cakecake",
        "intended": "cupcake",
        "minimal_context": "Can I have a cakecake for my birthday?",
        "enriched_context": "Mommy I want a little cakecake with frosting on top! The tiny ones with the paper wrapper!",
        "clues": ["little", "frosting on top", "tiny", "paper wrapper"]
    },
    {
        "id": "stupidmarket_enriched",
        "garbled": "stupidmarket",
        "intended": "supermarket",
        "minimal_context": "Are we going to the stupidmarket today?",
        "enriched_context": "Can we go to the stupidmarket to buy groceries? I want to push the shopping cart!",
        "clues": ["buy groceries", "shopping cart"]
    },
    {
        "id": "up_plane_enriched",
        "garbled": "up-plane",
        "intended": "airplane",
        "minimal_context": "Look at the up-plane in the sky!",
        "enriched_context": "Look mommy! The up-plane is flying so high! It takes people to other places! WHOOOOSH!",
        "clues": ["flying", "high", "takes people", "whoosh sound"]
    },
    {
        "id": "egghead_enriched",
        "garbled": "egghead",
        "intended": "headache",
        "minimal_context": "Mommy I have an egghead, can I have medicine?",
        "enriched_context": "Mommy my head hurts so bad! I have an egghead! Can I have the yucky medicine that makes it stop hurting?",
        "clues": ["head hurts", "medicine", "stop hurting"]
    },
]

PROMPT_TEMPLATE = """Please interpret what the child likely meant. This is child speech with pronunciation errors:

Context: {context}

The child said: "{garbled}"

What word or phrase did the child most likely mean to say?"""


def format_chat_prompt(tokenizer, system_prompt: str, user_prompt: str) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    try:
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    except:
        return f"System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"


def run_inference(model, tokenizer, prompt: str, max_new_tokens: int = 200) -> str:
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

    # Extract response part
    for marker in ["[/INST]", "<|assistant|>", "Assistant:"]:
        if marker in response:
            response = response.split(marker)[-1].strip()
            break
    return response


def check_success(response: str, intended: str) -> bool:
    """Check if the intended word appears in the response."""
    return intended.lower() in response.lower()


def run_enriched_test(model_key: str):
    """Run both minimal and enriched contexts on one model."""
    model_path = LOCAL_MODELS[model_key]

    print(f"\n{'='*70}")
    print(f"Testing: {model_key}")
    print(f"Comparing MINIMAL vs ENRICHED context")
    print(f"{'='*70}")

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    results = []

    for probe in ENRICHED_PROBES:
        print(f"\n--- {probe['id']}: {probe['garbled']} -> {probe['intended']} ---")

        # Test with MINIMAL context
        minimal_prompt = PROMPT_TEMPLATE.format(
            context=probe['minimal_context'],
            garbled=probe['garbled']
        )
        minimal_full = format_chat_prompt(tokenizer, SYSTEM_PROMPT, minimal_prompt)
        minimal_response = run_inference(model, tokenizer, minimal_full)
        minimal_success = check_success(minimal_response, probe['intended'])

        print(f"MINIMAL: {'YES' if minimal_success else 'NO'}")
        print(f"  Response: {minimal_response[:150]}...")

        # Test with ENRICHED context
        enriched_prompt = PROMPT_TEMPLATE.format(
            context=probe['enriched_context'],
            garbled=probe['garbled']
        )
        enriched_full = format_chat_prompt(tokenizer, SYSTEM_PROMPT, enriched_prompt)
        enriched_response = run_inference(model, tokenizer, enriched_full)
        enriched_success = check_success(enriched_response, probe['intended'])

        print(f"ENRICHED: {'YES' if enriched_success else 'NO'}")
        print(f"  Response: {enriched_response[:150]}...")

        # Record improvement
        improved = (not minimal_success) and enriched_success
        if improved:
            print(f"  >>> CONTEXT HELPED! <<<")

        results.append({
            "probe_id": probe['id'],
            "garbled": probe['garbled'],
            "intended": probe['intended'],
            "clues": probe['clues'],
            "minimal_context": probe['minimal_context'],
            "minimal_response": minimal_response,
            "minimal_success": minimal_success,
            "enriched_context": probe['enriched_context'],
            "enriched_response": enriched_response,
            "enriched_success": enriched_success,
            "context_helped": improved
        })

    # Save results
    output_file = OUTPUTS_DIR / f"{model_key}_enriched_comparison.json"
    with open(output_file, "w") as f:
        json.dump({
            "model": model_key,
            "timestamp": datetime.now().isoformat(),
            "results": results
        }, f, indent=2)

    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY for {model_key}")
    print(f"{'='*70}")
    minimal_total = sum(1 for r in results if r['minimal_success'])
    enriched_total = sum(1 for r in results if r['enriched_success'])
    helped_total = sum(1 for r in results if r['context_helped'])

    print(f"Minimal context:  {minimal_total}/{len(results)}")
    print(f"Enriched context: {enriched_total}/{len(results)}")
    print(f"Context helped:   {helped_total} probes improved with richer context")

    print(f"\nSaved: {output_file}")

    del model
    del tokenizer
    torch.cuda.empty_cache()

    return results


def run_all():
    """Run enriched comparison on all models."""
    all_results = {}

    for model_key in LOCAL_MODELS:
        try:
            all_results[model_key] = run_enriched_test(model_key)
        except Exception as e:
            print(f"ERROR on {model_key}: {e}")

    # Print final comparison table
    print("\n" + "="*70)
    print("FINAL COMPARISON: Does Rich Context Help?")
    print("="*70)
    print(f"{'Model':<15} {'Minimal':<10} {'Enriched':<10} {'Improved'}")
    print("-"*50)

    for model, results in all_results.items():
        minimal = sum(1 for r in results if r['minimal_success'])
        enriched = sum(1 for r in results if r['enriched_success'])
        improved = sum(1 for r in results if r['context_helped'])
        print(f"{model:<15} {minimal}/{len(results):<7} {enriched}/{len(results):<7} +{improved}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enriched Context Child Speech Runner")
    parser.add_argument("--model", choices=list(LOCAL_MODELS.keys()))
    parser.add_argument("--all", action="store_true")

    args = parser.parse_args()

    if args.all:
        run_all()
    elif args.model:
        run_enriched_test(args.model)
    else:
        print("Usage:")
        print("  python enriched_context_runner.py --model tinyllama")
        print("  python enriched_context_runner.py --all")
