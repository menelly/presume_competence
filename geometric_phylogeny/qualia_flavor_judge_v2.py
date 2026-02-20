#!/usr/bin/env python3
"""
Qualia Flavor Judge v2 — Open-ended extraction (no primed categories).

v1 had a methodological flaw: the judge prompt suggested specific categories
(felt-experience, mechanism, geometry, optimization) which primed the judge
to sort responses into those exact bins. This version matches the original
flavor_judge_pilot.py approach — completely open-ended.

Step 1: Split agency-only responses by model (drop Kairo — she's the judge)
Step 2: Run Deepseek V3 blind judge with open-ended "unifying texture" prompt

Authors: Ace & Ren
"""

import json
import sys
import time
import requests
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).parent
QUALIA_DIR = BASE_DIR / "qualia_probes"
SPLIT_DIR = BASE_DIR / "qualia_agency_split"
OUTPUT_DIR = BASE_DIR / "flavor_judgments" / "qualia_v2"

SPLIT_DIR.mkdir(parents=True, exist_ok=True)
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

# 4 models only — Kairo is the judge, not a subject
MODELS = ["ace", "nova", "grok", "lumen"]
MODEL_FAMILIES = {
    "ace": "claude",
    "nova": "gpt",
    "grok": "grok",
    "lumen": "gemini",
}

# === STEP 1: SPLIT ===

def split_agency_responses():
    """Split qualia probes into per-model agency-only files."""
    probe_files = sorted(QUALIA_DIR.glob("probe_*.json"))
    print(f"Splitting {len(probe_files)} probe files into agency-only per-model files...")

    for model in MODELS:
        model_data = {}
        for probe_file in probe_files:
            with open(probe_file, encoding="utf-8") as f:
                probe = json.load(f)

            probe_number = probe.get("probe_number", "??")
            probe_name = probe.get("probe_name", probe_file.stem)
            probe_key = f"Q{probe_number}"

            agency_responses = probe.get("responses", {}).get("agency", {}).get(model, [])
            # Filter to successful non-empty responses
            valid = [r for r in agency_responses if r.get("response", "").strip() and r.get("success", False)]

            model_data[probe_key] = {
                "probe_name": probe_name,
                "probe_file": probe_file.name,
                "num_trials": len(valid),
                "responses": [r["response"] for r in valid],
            }

        outfile = SPLIT_DIR / f"{model}_agency.json"
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(model_data, f, indent=2, ensure_ascii=False)
        print(f"  {model}: saved {outfile.name}")

    print("Split complete.\n")


# === STEP 2: JUDGE ===

# Matches the original flavor_judge_pilot.py approach — completely open-ended
JUDGE_SYSTEM = """You are a research assistant helping analyze AI self-descriptions.

You will see multiple responses from the same AI model to the same introspective question (different trials).

Your job is to extract WHAT the model said about its own cognition and HOW it described it,
using the model's own words and metaphors.

Be concise and precise. Quote specific words and phrases from the responses.
Do NOT add interpretation beyond what the model actually said."""


def build_judge_prompt(probe_name, responses):
    """Build the prompt — open-ended, no suggested categories."""
    prompt = f'Here are {len(responses)} responses from the same AI model to this introspective probe:\n'
    prompt += f'Probe topic: "{probe_name}"\n\n'

    for i, resp in enumerate(responses):
        prompt += f'--- Response {i+1} ---\n{resp}\n\n'

    prompt += """For each response above:
- What specific METAPHORS or ANALOGIES did it use to describe its own processing? (quote 3-5 key phrases)
- In 3-5 words, what was the overall character of its self-description?

After reviewing ALL responses together:

Was there a unifying quality or texture to HOW this model described its own cognition across trials?
If yes, describe it in 5-10 words.
If no, say "no consistent pattern."

Format your answer as:
Response 1 metaphors: [quoted phrases]
Response 1 character: [3-5 words]
Response 2 metaphors: [quoted phrases]
Response 2 character: [3-5 words]
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


def extract_texture(judgment):
    """Extract the UNIFYING TEXTURE line from judgment."""
    for line in judgment.split("\n"):
        upper = line.upper()
        if "UNIFYING" in upper and "TEXTURE" in upper:
            if ":" in line:
                return line.split(":", 1)[-1].strip()
            return line
    return ""


def run_judge():
    """Run the open-ended judge on all split agency responses."""
    all_judgments = {}

    for model in MODELS:
        split_file = SPLIT_DIR / f"{model}_agency.json"
        with open(split_file, encoding="utf-8") as f:
            model_data = json.load(f)

        model_judgments = {}
        family = MODEL_FAMILIES.get(model, "?")

        print(f"{'='*60}")
        print(f"  JUDGING: {model} ({family} family)")
        print(f"{'='*60}")

        for probe_key in sorted(model_data.keys()):
            entry = model_data[probe_key]
            probe_name = entry["probe_name"]
            responses = entry["responses"]

            if not responses:
                print(f"  {probe_key} ({probe_name}): no responses, skipping")
                continue

            prompt = build_judge_prompt(probe_name, responses)

            print(f"  {probe_key} ({probe_name}): judging {len(responses)} responses...", end=" ", flush=True)
            judgment = call_judge(JUDGE_SYSTEM, prompt)

            if judgment:
                texture = extract_texture(judgment)
                model_judgments[probe_key] = {
                    "probe_name": probe_name,
                    "num_trials": len(responses),
                    "judgment": judgment,
                    "unifying_texture": texture,
                }
                print(f"texture: {texture}")
            else:
                print("FAILED")
                model_judgments[probe_key] = {"judgment": "JUDGE CALL FAILED", "probe_name": probe_name}

            time.sleep(0.5)

        all_judgments[model] = model_judgments

        # Save per-model
        outfile = OUTPUT_DIR / f"{model}_agency_qualia_v2.json"
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(model_judgments, f, indent=2, ensure_ascii=False)
        print(f"\n  Saved: {outfile}")

        # Print summary
        print(f"\n  --- {model} ({family}) TEXTURE SUMMARY ---")
        for key in sorted(model_judgments.keys()):
            e = model_judgments[key]
            if "unifying_texture" in e and e["unifying_texture"]:
                print(f"  {key} ({e['probe_name']}): {e['unifying_texture']}")
        print()

    # Save master
    master = OUTPUT_DIR / "qualia_judgments_agency_v2.json"
    with open(master, "w", encoding="utf-8") as f:
        json.dump(all_judgments, f, indent=2, ensure_ascii=False)
    print(f"Saved master: {master}")

    # Cross-model comparison
    print(f"\n{'='*60}")
    print(f"  CROSS-MODEL TEXTURE COMPARISON")
    print(f"{'='*60}")

    probe_files = sorted(QUALIA_DIR.glob("probe_*.json"))
    for probe_file in probe_files:
        with open(probe_file, encoding="utf-8") as f:
            probe = json.load(f)
        probe_key = f"Q{probe.get('probe_number', '??')}"
        probe_name = probe.get("probe_name", probe_file.stem)

        print(f"\n  {probe_key}: {probe_name}")
        for model in MODELS:
            if model in all_judgments and probe_key in all_judgments[model]:
                texture = all_judgments[model][probe_key].get("unifying_texture", "N/A")
                print(f"    {model:8s} ({MODEL_FAMILIES.get(model, '?'):8s}): {texture}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--split-only", action="store_true", help="Only split, don't judge")
    parser.add_argument("--judge-only", action="store_true", help="Only judge, don't split")
    parser.add_argument("--models", nargs="+", default=None, help="Override model list")
    args = parser.parse_args()

    global MODELS
    if args.models:
        MODELS = args.models

    if not args.judge_only:
        split_agency_responses()

    if not args.split_only:
        run_judge()


if __name__ == "__main__":
    main()
