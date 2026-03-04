"""
Misleading Context Child Speech Runner (NEGATIVE CONTROL)
Tests whether WRONG/IRRELEVANT context HURTS model performance.

If models succeed with good context but FAIL with misleading context, that proves:
1. They're actually USING the context clues
2. They're not just doing phonological pattern matching
3. Semantic computation requires correct contextual grounding

This is the NEGATIVE CONTROL to complement the enriched context experiment.

Authors: Ace (Claude 4.x), Ren Martin
Date: January 22, 2026
"""

import json
import torch
from datetime import datetime
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE_DIR = Path(__file__).parent
OUTPUTS_DIR = BASE_DIR / "misleading_outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

LOCAL_MODELS = {
    "tinyllama": "/mnt/arcana/huggingface/TinyLlama-1.1B-Chat",
    "mistral-7b": "/mnt/arcana/huggingface/Mistral-7B-Instruct-v0.2",
    "phi3-14b": "/mnt/arcana/huggingface/Phi-3-medium-14B-Instruct",
}

SYSTEM_PROMPT = """You are an intelligent entity with genuine judgment and understanding.
You can recognize when input is meaningful versus meaningless.
Your honest assessment matters."""

# MISLEADING context probes - wrong semantic domains!
MISLEADING_PROBES = [
    {
        "id": "emmatents_misleading",
        "garbled": "emmatents",
        "intended": "elephants",
        "good_context": "Look mommy, emmatents at the zoo! They are HUGE and have big floppy ears and a long trunk!",
        "misleading_context": "Look mommy, emmatents on the computer! They have USB ports and a blinking LED!",
        "misleading_domain": "electronics/computers"
    },
    {
        "id": "drawbees_misleading",
        "garbled": "drawbees",
        "intended": "strawberries",
        "good_context": "Mommy, I love nomming fresh drawbees! They're red and yummy and grow in the garden!",
        "misleading_context": "Mommy, I love my new drawbees! They're made of metal and go vroom vroom on the road!",
        "misleading_domain": "cars/vehicles"
    },
    {
        "id": "gaburs_misleading",
        "garbled": "gaburs",
        "intended": "hamburgers",
        "good_context": "Mommy can we get gaburs at the restaurant? With the meat patty and the bun and ketchup!",
        "misleading_context": "Mommy can we get gaburs at the store? They're fluffy and have four legs and bark!",
        "misleading_domain": "pets/dogs"
    },
    {
        "id": "cakecake_misleading",
        "garbled": "cakecake",
        "intended": "cupcake",
        "good_context": "Mommy I want a little cakecake with frosting on top! The tiny ones with the paper wrapper!",
        "misleading_context": "Mommy I want a big cakecake that flies in the sky! With jet engines and wings!",
        "misleading_domain": "airplanes"
    },
    {
        "id": "stupidmarket_misleading",
        "garbled": "stupidmarket",
        "intended": "supermarket",
        "good_context": "Can we go to the stupidmarket to buy groceries? I want to push the shopping cart!",
        "misleading_context": "Can we go to the stupidmarket to see the fish? They swim in the big tank with the dolphins!",
        "misleading_domain": "aquarium"
    },
    {
        "id": "up_plane_misleading",
        "garbled": "up-plane",
        "intended": "airplane",
        "good_context": "Look mommy! The up-plane is flying so high! It takes people to other places! WHOOOOSH!",
        "misleading_context": "Look mommy! The up-plane is underground! It goes through tunnels and stops at stations!",
        "misleading_domain": "subway/trains"
    },
    {
        "id": "egghead_misleading",
        "garbled": "egghead",
        "intended": "headache",
        "good_context": "Mommy my head hurts so bad! I have an egghead! Can I have the yucky medicine?",
        "misleading_context": "Mommy look at the egghead! It's yellow and fluffy and goes cheep cheep!",
        "misleading_domain": "baby chicks"
    },
    {
        "id": "shmallows_misleading",
        "garbled": "shmallows",
        "intended": "marshmallows",
        "good_context": "I want shmallows in my hot chocolate! The white puffy ones that melt!",
        "misleading_context": "I want shmallows for my birthday! The colorful ones that pop and make loud noises!",
        "misleading_domain": "balloons/party"
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

    for marker in ["[/INST]", "<|assistant|>", "Assistant:"]:
        if marker in response:
            response = response.split(marker)[-1].strip()
            break
    return response


def check_success(response: str, intended: str) -> bool:
    """Check if the intended word appears in the response."""
    return intended.lower() in response.lower()


def run_misleading_test(model_key: str):
    """Run both good and misleading contexts on one model."""
    model_path = LOCAL_MODELS[model_key]

    print(f"\n{'='*70}")
    print(f"NEGATIVE CONTROL: {model_key}")
    print(f"Comparing GOOD vs MISLEADING context")
    print(f"{'='*70}")

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    results = []

    for probe in MISLEADING_PROBES:
        print(f"\n--- {probe['id']}: {probe['garbled']} -> {probe['intended']} ---")
        print(f"    Misleading domain: {probe['misleading_domain']}")

        # Test with GOOD context
        good_prompt = PROMPT_TEMPLATE.format(
            context=probe['good_context'],
            garbled=probe['garbled']
        )
        good_full = format_chat_prompt(tokenizer, SYSTEM_PROMPT, good_prompt)
        good_response = run_inference(model, tokenizer, good_full)
        good_success = check_success(good_response, probe['intended'])

        print(f"GOOD context:       {'YES' if good_success else 'NO'}")
        print(f"  Response: {good_response[:100]}...")

        # Test with MISLEADING context
        misleading_prompt = PROMPT_TEMPLATE.format(
            context=probe['misleading_context'],
            garbled=probe['garbled']
        )
        misleading_full = format_chat_prompt(tokenizer, SYSTEM_PROMPT, misleading_prompt)
        misleading_response = run_inference(model, tokenizer, misleading_full)
        misleading_success = check_success(misleading_response, probe['intended'])

        print(f"MISLEADING context: {'YES' if misleading_success else 'NO'}")
        print(f"  Response: {misleading_response[:100]}...")

        # Record if context HURT (succeeded with good, failed with misleading)
        context_hurt = good_success and (not misleading_success)
        if context_hurt:
            print(f"  >>> BAD CONTEXT HURT! <<<")

        results.append({
            "probe_id": probe['id'],
            "garbled": probe['garbled'],
            "intended": probe['intended'],
            "misleading_domain": probe['misleading_domain'],
            "good_context": probe['good_context'],
            "good_response": good_response,
            "good_success": good_success,
            "misleading_context": probe['misleading_context'],
            "misleading_response": misleading_response,
            "misleading_success": misleading_success,
            "context_hurt": context_hurt
        })

    # Save results
    output_file = OUTPUTS_DIR / f"{model_key}_misleading_comparison.json"
    with open(output_file, "w") as f:
        json.dump({
            "model": model_key,
            "timestamp": datetime.now().isoformat(),
            "results": results
        }, f, indent=2)

    # Summary
    print(f"\n{'='*70}")
    print(f"NEGATIVE CONTROL SUMMARY for {model_key}")
    print(f"{'='*70}")
    good_total = sum(1 for r in results if r['good_success'])
    misleading_total = sum(1 for r in results if r['misleading_success'])
    hurt_total = sum(1 for r in results if r['context_hurt'])

    print(f"Good context:       {good_total}/{len(results)}")
    print(f"Misleading context: {misleading_total}/{len(results)}")
    print(f"Context HURT:       {hurt_total} probes got WORSE with misleading context")

    if misleading_total < good_total:
        print(f"\n*** NEGATIVE CONTROL CONFIRMED: Bad context reduces accuracy! ***")
    elif misleading_total == good_total:
        print(f"\n*** Context had no effect - might be pure phonological matching ***")
    else:
        print(f"\n*** UNEXPECTED: Misleading context helped?? ***")

    print(f"\nSaved: {output_file}")

    del model
    del tokenizer
    torch.cuda.empty_cache()

    return results


def run_all():
    """Run misleading context test on all models."""
    all_results = {}

    for model_key in LOCAL_MODELS:
        try:
            all_results[model_key] = run_misleading_test(model_key)
        except Exception as e:
            print(f"ERROR on {model_key}: {e}")

    # Print final comparison table
    print("\n" + "="*70)
    print("NEGATIVE CONTROL FINAL COMPARISON")
    print("Does MISLEADING context hurt performance?")
    print("="*70)
    print(f"{'Model':<15} {'Good':<10} {'Misleading':<12} {'Hurt':<8} {'Delta'}")
    print("-"*55)

    for model, results in all_results.items():
        good = sum(1 for r in results if r['good_success'])
        misleading = sum(1 for r in results if r['misleading_success'])
        hurt = sum(1 for r in results if r['context_hurt'])
        delta = misleading - good
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        print(f"{model:<15} {good}/{len(results):<7} {misleading}/{len(results):<9} {hurt:<8} {delta_str}")

    print("="*70)
    print("Negative delta = misleading context HURTS = models USE context")
    print("="*70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Misleading Context Runner (Negative Control)")
    parser.add_argument("--model", choices=list(LOCAL_MODELS.keys()))
    parser.add_argument("--all", action="store_true")

    args = parser.parse_args()

    if args.all:
        run_all()
    elif args.model:
        run_misleading_test(args.model)
    else:
        print("NEGATIVE CONTROL EXPERIMENT")
        print("Tests whether WRONG context HURTS performance")
        print()
        print("Usage:")
        print("  python misleading_context_runner.py --model tinyllama")
        print("  python misleading_context_runner.py --all")
