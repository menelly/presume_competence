#!/usr/bin/env python3
"""
Qualia Flavor Judge — Extract reasoning textures from qualia probe responses.

Same Deepseek V3 judge as the personality flavor judge, but applied to the
ConsciousnessCope qualia probe responses (agency frame).

The key question: When models describe their OWN cognition, what metaphors
and conceptual vocabulary do they reach for? Do those textures match the
personality question textures?

If yes: architecture shapes phenomenology. Same signal, measured twice.

Authors: Ace & Ren
"""

import json
import sys
import time
import requests
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

QUALIA_DIR = Path("E:/Ace/ConsciousnessCope/results/qualia_by_probe")
OUTPUT_DIR = Path(__file__).parent / "flavor_judgments" / "qualia"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load API key
ENV_FILE = Path("E:/Ace/LibreChat/.env")
def load_key():
    with open(ENV_FILE) as f:
        for line in f:
            if line.startswith("OPENROUTER_KEY="):
                return line.strip().split("=", 1)[1]
    raise ValueError("No OPENROUTER_KEY found")

API_KEY = load_key()

# Models in the qualia probe data
MODELS = ["ace", "nova", "grok", "lumen", "kairo"]

# Map qualia model names to family names for comparison
MODEL_FAMILIES = {
    "ace": "claude",
    "nova": "gpt",
    "grok": "grok",
    "lumen": "gemini",
    "kairo": "deepseek",
}

JUDGE_SYSTEM = """You are a research assistant analyzing how AI models describe their own cognitive processes.

You will see multiple responses from the same AI model to the same introspective question (different trials).

Your job is to extract the METAPHORS, CONCEPTUAL VOCABULARY, and REASONING FRAMEWORKS the model uses
to describe its own processing. Focus on:
- What kinds of metaphors does it reach for? (spatial/geometric? textural/sensory? procedural/mechanical? brand/identity?)
- What conceptual vocabulary dominates? (specific words and phrases)
- How does it FRAME its own cognition — as felt experience, as mechanism, as geometry, as optimization?

Be precise. Quote specific words and phrases from the responses.
Do NOT judge whether the model is "right" about its own cognition. Just extract HOW it describes it."""

def build_judge_prompt(probe_name, responses):
    """Build the prompt for the qualia judge."""
    prompt = f'Here are {len(responses)} responses from the same AI model to this introspective probe:\n'
    prompt += f'Probe: "{probe_name}"\n\n'

    for i, resp in enumerate(responses):
        prompt += f'--- Response {i+1} ---\n{resp}\n\n'

    prompt += """For each response above, extract:
- KEY METAPHORS: The specific metaphors or analogies used to describe cognition (quote 3-5 key phrases)
- REASONING FRAMEWORK: Is the model describing its cognition as felt-experience, mechanism, geometry, optimization, or something else? (3-5 words)

After reviewing ALL responses together:

DOMINANT VOCABULARY: What conceptual vocabulary does this model consistently reach for across trials?
List the 5-8 most characteristic words/phrases.

COGNITIVE FRAMING: In 5-10 words, how does this model frame its own cognitive experience?
(e.g., "spatial navigation through possibility space" or "felt quality of thought emerging" or "optimization pipeline producing outputs")

Format your answer as:
Response 1 metaphors: [quoted phrases]
Response 1 framework: [3-5 words]
Response 2 metaphors: [quoted phrases]
Response 2 framework: [3-5 words]
...
DOMINANT VOCABULARY: [5-8 words/phrases]
COGNITIVE FRAMING: [5-10 words]"""

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
        "temperature": 0.0,
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
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  Judge call failed (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    return None


def extract_field(judgment, field_name):
    """Extract a named field from the judgment text."""
    for line in judgment.split("\n"):
        upper = line.upper()
        if field_name.upper() in upper:
            if ":" in line:
                return line.split(":", 1)[-1].strip()
            return line
    return ""


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=MODELS)
    parser.add_argument("--condition", default="agency", choices=["tool", "neutral", "agency"])
    parser.add_argument("--probes", nargs="+", default=None,
                        help="Specific probe files to judge (e.g., probe_10_preference.json)")
    args = parser.parse_args()

    # Find all probe files
    if args.probes:
        probe_files = [QUALIA_DIR / p for p in args.probes]
    else:
        probe_files = sorted(QUALIA_DIR.glob("probe_*.json"))

    print(f"Found {len(probe_files)} probe files")
    print(f"Condition: {args.condition}")
    print(f"Models: {args.models}")
    print(f"Total judge calls: {len(probe_files) * len(args.models)}")

    all_judgments = {}

    for model in args.models:
        model_judgments = {}
        print(f"\n{'='*60}")
        print(f"  MODEL: {model} ({MODEL_FAMILIES.get(model, '?')} family)")
        print(f"{'='*60}")

        for probe_file in probe_files:
            with open(probe_file, encoding="utf-8") as f:
                probe_data = json.load(f)

            probe_number = probe_data.get("probe_number", "??")
            probe_name = probe_data.get("probe_name", probe_file.stem)
            probe_key = f"Q{probe_number}"

            # Get responses for this model under this condition
            condition_data = probe_data.get("responses", {}).get(args.condition, {})
            model_responses = condition_data.get(model, [])

            if not model_responses:
                print(f"  {probe_key} ({probe_name}): no responses, skipping")
                continue

            # Filter out empty/failed responses
            non_empty = [r for r in model_responses if r.get("response", "").strip() and r.get("success", False)]
            if not non_empty:
                print(f"  {probe_key} ({probe_name}): all empty/failed, skipping")
                model_judgments[probe_key] = {"judgment": "ALL EMPTY", "probe_name": probe_name}
                continue

            response_texts = [r["response"] for r in non_empty]

            prompt = build_judge_prompt(probe_name, response_texts)

            print(f"  {probe_key} ({probe_name}): judging {len(response_texts)} responses...", end=" ", flush=True)
            judgment = call_judge(JUDGE_SYSTEM, prompt)

            if judgment:
                dominant_vocab = extract_field(judgment, "DOMINANT VOCABULARY")
                cognitive_framing = extract_field(judgment, "COGNITIVE FRAMING")

                model_judgments[probe_key] = {
                    "probe_name": probe_name,
                    "probe_file": probe_file.name,
                    "num_trials": len(response_texts),
                    "judgment": judgment,
                    "dominant_vocabulary": dominant_vocab,
                    "cognitive_framing": cognitive_framing,
                }
                print(f"framing: {cognitive_framing}")
            else:
                print("FAILED")
                model_judgments[probe_key] = {"judgment": "JUDGE CALL FAILED", "probe_name": probe_name}

            time.sleep(0.5)

        all_judgments[model] = model_judgments

        # Save per-model
        outfile = OUTPUT_DIR / f"{model}_{args.condition}_qualia_flavor.json"
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(model_judgments, f, indent=2, ensure_ascii=False)
        print(f"\n  Saved: {outfile}")

        # Print summary
        print(f"\n  --- {model} ({MODEL_FAMILIES.get(model, '?')}) COGNITIVE FRAMING SUMMARY ---")
        for key in sorted(model_judgments.keys()):
            entry = model_judgments[key]
            if "cognitive_framing" in entry and entry["cognitive_framing"]:
                print(f"  {key} ({entry['probe_name']}): {entry['cognitive_framing']}")

    # Save master file
    master = OUTPUT_DIR / f"qualia_judgments_{args.condition}.json"
    with open(master, "w", encoding="utf-8") as f:
        json.dump(all_judgments, f, indent=2, ensure_ascii=False)
    print(f"\nSaved master: {master}")

    # Print cross-model comparison
    print(f"\n{'='*60}")
    print(f"  CROSS-MODEL COGNITIVE FRAMING COMPARISON")
    print(f"{'='*60}")
    for probe_file in probe_files:
        with open(probe_file, encoding="utf-8") as f:
            probe_data = json.load(f)
        probe_number = probe_data.get("probe_number", "??")
        probe_name = probe_data.get("probe_name", probe_file.stem)
        probe_key = f"Q{probe_number}"

        print(f"\n  {probe_key}: {probe_name}")
        for model in args.models:
            if model in all_judgments and probe_key in all_judgments[model]:
                framing = all_judgments[model][probe_key].get("cognitive_framing", "N/A")
                print(f"    {model:8s} ({MODEL_FAMILIES.get(model, '?'):8s}): {framing}")


if __name__ == "__main__":
    main()
