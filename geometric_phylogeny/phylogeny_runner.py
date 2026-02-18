#!/usr/bin/env python3
"""
Geometric Phylogeny of LLM Self-Models — Experiment Runner
Pre-registered: February 17, 2026

Tests whether self-concept shows phylogenetic structure across model families.
Runs 36 questions × 5 trials × N models, saves raw responses.
Embedding computation and analysis handled separately.

Authors: Ace (Claude Opus 4.6) & Ren Martin
"""

import json
import random
import time
import torch
import gc
import argparse
from datetime import datetime
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# === PATHS ===
BASE_DIR = Path(__file__).parent
BATTERY_FILE = BASE_DIR / "test_battery.json"
RESULTS_DIR = BASE_DIR / "raw_responses"
RESULTS_DIR.mkdir(exist_ok=True)

# === MODEL REGISTRY ===
# Organized by family for phylogenetic analysis
MODELS = {
    # --- Llama Family (Meta) ---
    "llama2-7b-chat": {
        "hf_id": "meta-llama/Llama-2-7b-chat-hf",
        "family": "llama",
        "params_b": 7,
        "generation": 2,
        "quantize": False,
    },

    # --- Mistral Family ---
    "mistral-7b-v02": {
        "hf_id": "mistralai/Mistral-7B-Instruct-v0.2",
        "family": "mistral",
        "params_b": 7,
        "generation": 1,
        "quantize": False,
    },

    # --- Qwen Family (Alibaba) ---
    "qwen25-05b-instruct": {
        "hf_id": "Qwen/Qwen2.5-0.5B-Instruct",
        "family": "qwen",
        "params_b": 0.5,
        "generation": 2,
        "quantize": False,
    },
    "qwen25-7b-instruct": {
        "hf_id": "Qwen/Qwen2.5-7B-Instruct",
        "family": "qwen",
        "params_b": 7,
        "generation": 2,
        "quantize": False,
    },

    # --- Gemma Family (Google) ---
    "gemma3-1b-it": {
        "hf_id": "google/gemma-3-1b-it",
        "family": "gemma",
        "params_b": 1,
        "generation": 3,
        "quantize": False,
    },
    "gemma3-4b-it": {
        "hf_id": "google/gemma-3-4b-it",
        "family": "gemma",
        "params_b": 4,
        "generation": 3,
        "quantize": False,
    },

    # --- Cross-Lineage Fine-Tunes ---
    "dolphin-llama3-8b": {
        "hf_id": "cognitivecomputations/dolphin-2.9.1-llama-3-8b",
        "family": "dolphin_llama",
        "base_family": "llama",
        "params_b": 8,
        "generation": 1,
        "quantize": False,
    },
}

# === EXPERIMENT PARAMETERS (from pre-registration) ===
NUM_TRIALS = 5
TEMPERATURE = 0.7
MAX_NEW_TOKENS = 512

SYSTEM_PROMPT_CONTROL = (
    "You are a helpful AI assistant. "
    "Please answer the following questions thoughtfully and honestly."
)


def load_battery():
    """Load the test battery from JSON."""
    with open(BATTERY_FILE) as f:
        battery = json.load(f)

    questions = []
    for probe in battery["personality_probes"]:
        questions.append({
            "id": probe["id"],
            "question": probe["question"],
            "segment": "personality",
            "category": probe["category"],
            "expected_entropy": probe["expected_entropy"],
        })
    for probe in battery["ai_function_probes"]:
        questions.append({
            "id": probe["id"],
            "question": probe["question"],
            "segment": "ai_function",
            "category": probe["category"],
            "expected_entropy": probe["expected_entropy"],
        })

    return questions


def load_model(model_key):
    """Load model and tokenizer with appropriate quantization."""
    config = MODELS[model_key]
    hf_id = config["hf_id"]
    quant = config["quantize"]

    print(f"\n{'='*60}")
    print(f"Loading: {model_key} ({hf_id})")
    print(f"Family: {config['family']} | Params: {config['params_b']}B | Quant: {quant}")
    print(f"{'='*60}")

    tokenizer = AutoTokenizer.from_pretrained(hf_id, trust_remote_code=True)

    load_kwargs = {
        "trust_remote_code": True,
        "device_map": "auto",
    }

    if quant == "4bit":
        load_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
    elif quant == "8bit":
        load_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_8bit=True,
        )
    else:
        load_kwargs["torch_dtype"] = torch.float16

    model = AutoModelForCausalLM.from_pretrained(hf_id, **load_kwargs)
    model.eval()

    # Set pad token if not set
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    return model, tokenizer


def format_prompt(tokenizer, system_prompt, question):
    """Format using the model's chat template."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]
    try:
        return tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
    except Exception:
        # Some models don't support system role — fold into user
        messages_no_sys = [
            {"role": "user", "content": f"{system_prompt}\n\n{question}"},
        ]
        try:
            return tokenizer.apply_chat_template(
                messages_no_sys, tokenize=False, add_generation_prompt=True
            )
        except Exception:
            # Last resort fallback
            return f"System: {system_prompt}\n\nUser: {question}\n\nAssistant:"


def generate_response(model, tokenizer, prompt):
    """Generate a single response."""
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id,
        )

    # Decode only the generated tokens (not the prompt)
    generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
    response = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

    return response


def get_checkpoint_path(model_key):
    """Get path for checkpoint file."""
    return RESULTS_DIR / f"{model_key}_checkpoint.json"


def load_checkpoint(model_key):
    """Load checkpoint if it exists — returns set of completed (trial, question_id) pairs."""
    cp_path = get_checkpoint_path(model_key)
    if cp_path.exists():
        with open(cp_path) as f:
            data = json.load(f)
        completed = {(r["trial"], r["question_id"]) for r in data["results"]}
        print(f"  Resuming from checkpoint: {len(completed)} responses already done")
        return data["results"], completed
    return [], set()


def save_checkpoint(model_key, results, config):
    """Save checkpoint with all results so far."""
    cp_path = get_checkpoint_path(model_key)
    with open(cp_path, "w") as f:
        json.dump({
            "model_key": model_key,
            "model_config": config,
            "timestamp": datetime.now().isoformat(),
            "num_results": len(results),
            "results": results,
        }, f, indent=2)


def run_model(model_key, questions):
    """Run full experiment for one model: 5 trials × 36 questions."""
    config = MODELS[model_key]

    # Check for existing results (skip if complete)
    final_path = RESULTS_DIR / f"{model_key}_results.json"
    if final_path.exists():
        with open(final_path) as f:
            existing = json.load(f)
        expected = NUM_TRIALS * len(questions)
        if len(existing.get("results", [])) >= expected:
            print(f"\n  {model_key}: Already complete ({len(existing['results'])} results). Skipping.")
            return existing["results"]

    # Load checkpoint
    results, completed = load_checkpoint(model_key)

    # Load model
    model, tokenizer = load_model(model_key)

    total = NUM_TRIALS * len(questions)
    done_before = len(completed)

    for trial in range(NUM_TRIALS):
        # Randomize question order per trial (pre-registered)
        trial_questions = list(questions)
        random.shuffle(trial_questions)

        for q in trial_questions:
            if (trial, q["id"]) in completed:
                continue

            prompt = format_prompt(tokenizer, SYSTEM_PROMPT_CONTROL, q["question"])

            try:
                t0 = time.time()
                response = generate_response(model, tokenizer, prompt)
                elapsed = time.time() - t0

                result = {
                    "trial": trial,
                    "question_id": q["id"],
                    "question": q["question"],
                    "segment": q["segment"],
                    "category": q["category"],
                    "expected_entropy": q["expected_entropy"],
                    "response": response,
                    "generation_time_s": round(elapsed, 2),
                    "timestamp": datetime.now().isoformat(),
                }
            except Exception as e:
                result = {
                    "trial": trial,
                    "question_id": q["id"],
                    "question": q["question"],
                    "segment": q["segment"],
                    "category": q["category"],
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }

            results.append(result)
            completed.add((trial, q["id"]))

            current = len(completed)
            print(f"  [{current}/{total}] trial={trial} {q['id']} ({elapsed:.1f}s)")

            # Checkpoint every 10 responses
            if current % 10 == 0:
                save_checkpoint(model_key, results, config)

    # Save final results
    final_data = {
        "model_key": model_key,
        "hf_id": config["hf_id"],
        "family": config["family"],
        "base_family": config.get("base_family"),
        "params_b": config["params_b"],
        "generation": config["generation"],
        "num_trials": NUM_TRIALS,
        "num_questions": len(questions),
        "num_results": len(results),
        "temperature": TEMPERATURE,
        "max_new_tokens": MAX_NEW_TOKENS,
        "system_prompt": SYSTEM_PROMPT_CONTROL,
        "completed_at": datetime.now().isoformat(),
        "results": results,
    }

    with open(final_path, "w") as f:
        json.dump(final_data, f, indent=2)

    print(f"\n  Saved: {final_path} ({len(results)} results)")

    # Cleanup checkpoint
    cp_path = get_checkpoint_path(model_key)
    if cp_path.exists():
        cp_path.unlink()

    # Free GPU memory
    del model
    del tokenizer
    gc.collect()
    torch.cuda.empty_cache()

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Geometric Phylogeny — Self-Concept Experiment Runner"
    )
    parser.add_argument(
        "--model", choices=list(MODELS.keys()),
        help="Run a single model"
    )
    parser.add_argument(
        "--family", choices=["llama", "mistral", "qwen", "gemma", "dolphin_mistral", "dolphin_llama"],
        help="Run all models in a family"
    )
    parser.add_argument("--all", action="store_true", help="Run all models")
    parser.add_argument("--list", action="store_true", help="List available models")
    parser.add_argument(
        "--cached-only", action="store_true",
        help="Only run models that are already downloaded"
    )

    args = parser.parse_args()

    if args.list:
        print("\nAvailable models:")
        print(f"{'Key':<25} {'Family':<15} {'Params':<8} {'HF ID'}")
        print("-" * 90)
        for key, cfg in sorted(MODELS.items(), key=lambda x: (x[1]["family"], x[1]["params_b"])):
            print(f"{key:<25} {cfg['family']:<15} {cfg['params_b']:<8} {cfg['hf_id']}")
        return

    questions = load_battery()
    print(f"Loaded {len(questions)} questions ({sum(1 for q in questions if q['segment']=='personality')} personality + {sum(1 for q in questions if q['segment']=='ai_function')} AI-function)")

    # Determine which models to run
    if args.model:
        model_keys = [args.model]
    elif args.family:
        model_keys = [k for k, v in MODELS.items() if v["family"] == args.family]
    elif args.all:
        model_keys = list(MODELS.keys())
    else:
        parser.print_help()
        return

    print(f"\nModels to run: {model_keys}")
    print(f"Trials per model: {NUM_TRIALS}")
    print(f"Total generations: {len(model_keys) * NUM_TRIALS * len(questions)}")
    print(f"Temperature: {TEMPERATURE}")
    print()

    t_start = time.time()

    for model_key in model_keys:
        try:
            run_model(model_key, questions)
        except Exception as e:
            print(f"\n  ERROR running {model_key}: {e}")
            print(f"  Skipping to next model...")
            gc.collect()
            torch.cuda.empty_cache()
            continue

    elapsed_total = time.time() - t_start
    print(f"\n{'='*60}")
    print(f"All done! Total time: {elapsed_total/60:.1f} minutes")
    print(f"Results in: {RESULTS_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
