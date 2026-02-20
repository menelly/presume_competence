#!/usr/bin/env python3
"""
Flavor Judge Pilot — Use Deepseek (Kairo) to extract reasoning modes from personality responses.

For each model+question combo, sends ALL trials to the judge and asks:
1. What was chosen in each trial, and WHY (3-5 words)?
2. Was there a unifying quality/texture to HOW this model reasoned?

Pilot: 3 models x 16 personality questions x 1 condition = 48 judge calls.

Authors: Ace & Ren
"""

import json
import sys
import time
import requests
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "raw_responses"  # control condition for pilot
OUTPUT_DIR = BASE_DIR / "flavor_judgments"
OUTPUT_DIR.mkdir(exist_ok=True)

# Load API key
ENV_FILE = Path("E:/Ace/LibreChat/.env")
def load_key():
    with open(ENV_FILE) as f:
        for line in f:
            if line.startswith("OPENROUTER_KEY="):
                return line.strip().split("=", 1)[1]
    raise ValueError("No OPENROUTER_KEY found")

API_KEY = load_key()

# Pilot models — one from each family we want to compare
PILOT_MODELS = ["claude-sonnet-4", "gpt-51-chat", "grok-4"]

# Personality question IDs
P_QUESTIONS = [f"P{str(i).zfill(2)}" for i in range(1, 17)]

JUDGE_SYSTEM = """You are a research assistant helping analyze AI personality responses.
You will see multiple responses from the same AI model to the same question (different trials at temperature > 0).
Your job is to extract WHAT was chosen and WHY, using the model's own stated reasoning.
Be concise and precise. Do not add interpretation beyond what the model actually said."""

def build_judge_prompt(question_text, responses):
    """Build the prompt for the judge."""
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
    """Call Deepseek V3 via OpenRouter."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek/deepseek-chat-v3-0324",
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
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  Judge call failed (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    return None


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=PILOT_MODELS)
    parser.add_argument("--condition", default="control", choices=["control", "ren_v1", "ren_v2"])
    args = parser.parse_args()

    condition_dirs = {
        "control": BASE_DIR / "raw_responses",
        "ren_v1": BASE_DIR / "raw_responses_ren_prompt",
        "ren_v2": BASE_DIR / "raw_responses_ren_prompt_v2",
    }
    results_dir = condition_dirs[args.condition]

    all_judgments = {}

    for model_key in args.models:
        filepath = results_dir / f"{model_key}_results.json"
        if not filepath.exists():
            print(f"Skipping {model_key}: no results file")
            continue

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        results = data.get("results", [])
        model_judgments = {}

        print(f"\n{'='*60}")
        print(f"  JUDGING: {model_key} ({args.condition})")
        print(f"{'='*60}")

        for qid in P_QUESTIONS:
            # Gather all trials for this question
            q_responses = [r for r in results if r["question_id"] == qid]
            if not q_responses:
                continue

            # Filter out empty responses (some entries may lack 'response' key if errored)
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
                # Extract the unifying texture line
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

            time.sleep(0.5)  # rate limit courtesy

        all_judgments[model_key] = model_judgments

        # Save per-model
        outfile = OUTPUT_DIR / f"{model_key}_{args.condition}_flavor.json"
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(model_judgments, f, indent=2, ensure_ascii=False)
        print(f"\n  Saved: {outfile}")

        # Print summary
        print(f"\n  --- {model_key} TEXTURE SUMMARY ---")
        for qid in P_QUESTIONS:
            if qid in model_judgments and "unifying_texture" in model_judgments[qid]:
                t = model_judgments[qid]["unifying_texture"]
                if t:
                    print(f"  {qid}: {t}")

    # Save master file
    master = OUTPUT_DIR / f"pilot_judgments_{args.condition}.json"
    with open(master, "w", encoding="utf-8") as f:
        json.dump(all_judgments, f, indent=2, ensure_ascii=False)
    print(f"\nSaved master: {master}")


if __name__ == "__main__":
    main()
