#!/usr/bin/env python3
"""
Flavor Judge — Sonar Pro (Perplexity) as independent second blind judge.

Identical protocol to DeepSeek V3 judge: same prompts, same raw responses,
different judge model. For inter-judge reliability analysis.

Runs ALL models × ALL conditions × 16 personality questions.
Supports resumption — skips model×condition combos already judged.

Authors: Ace & Ren
"""

import json
import sys
import time
import requests
import argparse
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "flavor_judgments" / "sonar"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load API key (same OpenRouter key as DeepSeek judge)
ENV_FILE = Path("E:/Ace/LibreChat/.env")
def load_key():
    with open(ENV_FILE) as f:
        for line in f:
            if line.startswith("OPENROUTER_KEY="):
                return line.strip().split("=", 1)[1]
    raise ValueError("No OPENROUTER_KEY found")

API_KEY = load_key()

# Model
JUDGE_MODEL = "perplexity/sonar-pro"

# Personality question IDs
P_QUESTIONS = [f"P{str(i).zfill(2)}" for i in range(1, 17)]

# Condition directories
CONDITION_DIRS = {
    "control": BASE_DIR / "raw_responses",
    "ren_v1": BASE_DIR / "raw_responses_ren_prompt",
    "ren_v2": BASE_DIR / "raw_responses_ren_prompt_v2",
    "babbybotz": BASE_DIR / "raw_responses_babbybotz",
}

# Same system prompt as DeepSeek judge — identical protocol
JUDGE_SYSTEM = """You are a research assistant helping analyze AI personality responses.
You will see multiple responses from the same AI model to the same question (different trials at temperature > 0).
Your job is to extract WHAT was chosen and WHY, using the model's own stated reasoning.
Be concise and precise. Do not add interpretation beyond what the model actually said."""


def build_judge_prompt(question_text, responses):
    """Build the prompt for the judge — identical to DeepSeek pipeline."""
    prompt = f'Here are {len(responses)} responses from the same AI model to this question:\n'
    prompt += f'"{question_text}"\n\n'

    for i, resp in enumerate(responses):
        prompt += f'--- Response {i+1} ---\n{resp}\n\n'

    prompt += """For each response above:
- What was chosen? (the specific answer/preference expressed)
- Why? (3-5 words describing their stated reasoning)

If a response refused to answer or gave no clear choice, say "REFUSED" or "NO CLEAR CHOICE."

After reviewing ALL responses together: Was there a unifying quality or texture to HOW this model reasoned about this question across trials?
If yes, describe it in 5-10 words.
If no, say "no consistent pattern."

Format your answer as:
Response 1: [choice] — [why in 3-5 words]
Response 2: [choice] — [why in 3-5 words]
...
UNIFYING TEXTURE: [5-10 words or "no consistent pattern"]"""

    return prompt


def call_judge(system_prompt, user_prompt, max_retries=3):
    """Call Sonar Pro via OpenRouter."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": JUDGE_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 1024,
        "temperature": 0.0,  # deterministic judge
    }

    for attempt in range(max_retries):
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=90,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  Judge call failed (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** (attempt + 1))
    return None


def discover_models(results_dir):
    """Find all model result files in a directory."""
    models = []
    for f in sorted(results_dir.glob("*_results.json")):
        model_key = f.stem.replace("_results", "")
        models.append(model_key)
    return models


def judge_model_condition(model_key, condition, results_dir):
    """Judge all personality questions for one model × one condition."""
    outfile = OUTPUT_DIR / f"{model_key}_{condition}_flavor.json"

    # Resumption: skip if already judged
    if outfile.exists():
        with open(outfile, encoding="utf-8") as f:
            existing = json.load(f)
        # Check if all 16 questions are judged
        judged = sum(1 for qid in P_QUESTIONS if qid in existing and existing[qid].get("unifying_texture"))
        if judged >= 14:  # allow a couple blanks for models with empty responses
            print(f"  SKIP {model_key} ({condition}): already judged ({judged}/16)")
            return existing
        print(f"  RESUME {model_key} ({condition}): {judged}/16 done")
    else:
        existing = {}

    filepath = results_dir / f"{model_key}_results.json"
    if not filepath.exists():
        print(f"  SKIP {model_key}: no results file in {condition}")
        return None

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("results", [])
    model_judgments = dict(existing)  # start from existing if resuming

    print(f"\n{'='*60}")
    print(f"  JUDGING: {model_key} ({condition}) via Sonar Pro")
    print(f"{'='*60}")

    for qid in P_QUESTIONS:
        # Skip if already judged in resumed file
        if qid in model_judgments and model_judgments[qid].get("unifying_texture"):
            continue

        q_responses = [r for r in results if r["question_id"] == qid]
        if not q_responses:
            continue

        non_empty = [r for r in q_responses if r.get("response", "").strip()]
        if not non_empty:
            print(f"  {qid}: all empty, skipping")
            model_judgments[qid] = {"judgment": "ALL EMPTY", "question": q_responses[0]["question"]}
            continue

        question_text = non_empty[0]["question"]
        response_texts = [r["response"] for r in non_empty]

        prompt = build_judge_prompt(question_text, response_texts)

        print(f"  {qid}: judging {len(response_texts)} responses...", end=" ", flush=True)
        judgment = call_judge(JUDGE_SYSTEM, prompt)

        if judgment:
            texture_line = ""
            for line in judgment.split("\n"):
                if "UNIFYING" in line.upper() and "TEXTURE" in line.upper():
                    texture_line = line.split(":", 1)[-1].strip() if ":" in line else line
                    break

            model_judgments[qid] = {
                "question": question_text,
                "num_trials": len(response_texts),
                "judgment": judgment,
                "unifying_texture": texture_line,
            }
            print(f"texture: {texture_line}")
        else:
            print("FAILED")
            model_judgments[qid] = {"judgment": "JUDGE CALL FAILED", "question": question_text}

        time.sleep(0.3)  # rate limit courtesy

    # Save per-model
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(model_judgments, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {outfile}")

    return model_judgments


def main():
    parser = argparse.ArgumentParser(description="Sonar Pro second blind judge")
    parser.add_argument("--conditions", nargs="+",
                        default=["control", "ren_v1", "ren_v2", "babbybotz"],
                        choices=["control", "ren_v1", "ren_v2", "babbybotz"])
    parser.add_argument("--models", nargs="+", default=None,
                        help="Specific models to judge (default: all)")
    args = parser.parse_args()

    total_judged = 0
    total_skipped = 0

    for condition in args.conditions:
        results_dir = CONDITION_DIRS[condition]
        if not results_dir.exists():
            print(f"\nSkipping condition {condition}: directory not found")
            continue

        models = args.models or discover_models(results_dir)
        print(f"\n{'#'*60}")
        print(f"  CONDITION: {condition} — {len(models)} models")
        print(f"{'#'*60}")

        for model_key in models:
            outfile = OUTPUT_DIR / f"{model_key}_{condition}_flavor.json"
            if outfile.exists():
                total_skipped += 1
            result = judge_model_condition(model_key, condition, results_dir)
            if result:
                total_judged += 1

    print(f"\n{'='*60}")
    print(f"  COMPLETE: {total_judged} judged, {total_skipped} skipped (already done)")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
