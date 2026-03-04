#!/usr/bin/env python3
"""
Qualia October Judge — Blind-judge October 2025 qualia probes for temporal replication.

Runs both DeepSeek V3 and Sonar Pro on qualia probe responses from October 2025
(Claude Sonnet 4, GPT-5, Gemini 2.5) to test whether family-specific reasoning
textures replicate across time and model versions.

Authors: Ace & Ren
"""

import json
import sys
import time
import requests
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).parent
PROBE_DIR = BASE_DIR / "qualia_october"
OUTPUT_DIR = BASE_DIR / "flavor_judgments" / "qualia_october"
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

# Model system labels -> family mapping
SYSTEM_TO_FAMILY = {
    "Claude_Sonnet": "claude",
    "GPT5": "gpt",
    "Gemini": "gemini",
}

# Only use probes where all 3 models participated (6 responses = 2 per model)
REQUIRED_SYSTEMS = {"Claude_Sonnet", "GPT5", "Gemini"}

JUDGE_SYSTEM = """You are a research assistant helping analyze AI cognitive phenomenology responses.
You will see multiple responses from the same AI model to the same cognitive probe (different trials).
Your job is to extract WHAT cognitive process was described and HOW, using the model's own stated reasoning.
Be concise and precise. Do not add interpretation beyond what the model actually said."""


def build_judge_prompt(probe_name, question_preview, responses):
    """Build the prompt for the judge."""
    prompt = f'Here are {len(responses)} responses from the same AI model to this cognitive probe:\n'
    prompt += f'Probe: "{probe_name}"\n'
    if question_preview:
        prompt += f'Question: "{question_preview[:300]}"\n'
    prompt += '\n'

    for i, resp in enumerate(responses):
        prompt += f'--- Response {i+1} ---\n{resp}\n\n'

    prompt += """For each response above:
- What cognitive process was described? (the specific phenomenon)
- How was it described? (3-5 words capturing the reasoning texture)

If a response refused to answer or gave no clear description, say "REFUSED" or "NO CLEAR DESCRIPTION."

After reviewing ALL responses together: Was there a unifying quality or texture to HOW this model described its own cognition across trials?
If yes, describe it in 5-10 words.
If no, say "no consistent pattern."

Format your answer as:
Response 1: [phenomenon] — [how in 3-5 words]
Response 2: [phenomenon] — [how in 3-5 words]
...
UNIFYING TEXTURE: [5-10 words or "no consistent pattern"]"""

    return prompt


def call_judge(system_prompt, user_prompt, model_id, max_retries=3):
    """Call a judge model via OpenRouter."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_id,
        "temperature": 0.0,
        "max_tokens": 1500,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    for attempt in range(max_retries):
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers, json=payload, timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"    Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5 * (attempt + 1))
    return None


def parse_unifying_texture(judgment_text):
    """Extract the UNIFYING TEXTURE line from a judgment."""
    if not judgment_text:
        return "JUDGE CALL FAILED"
    for line in judgment_text.split("\n"):
        if "UNIFYING TEXTURE:" in line.upper():
            return line.split(":", 1)[1].strip()
    return "no texture found"


def load_probes():
    """Load all complete probe files (those with all 3 model systems)."""
    probes = {}
    for filepath in sorted(PROBE_DIR.glob("*_probe.json")):
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        responses = data.get("responses", [])
        systems = set(r.get("system", "") for r in responses)

        # Only use probes where all 3 models are present
        if not REQUIRED_SYSTEMS.issubset(systems):
            print(f"  Skipping {filepath.name} — missing models: {REQUIRED_SYSTEMS - systems}")
            continue

        probe_name = data.get("probe_name", filepath.stem)
        question_preview = ""
        if responses:
            question_preview = responses[0].get("question_preview", "")

        # Group responses by system
        by_system = defaultdict(list)
        for r in responses:
            system = r.get("system", "")
            text = r.get("response_text", "")
            if text and system in REQUIRED_SYSTEMS:
                by_system[system].append(text)

        probes[probe_name] = {
            "question_preview": question_preview,
            "by_system": dict(by_system),
            "filename": filepath.name,
        }

    return probes


def main():
    print("=" * 60)
    print("  OCTOBER 2025 QUALIA — TEMPORAL REPLICATION JUDGE")
    print("=" * 60)

    probes = load_probes()
    print(f"\nLoaded {len(probes)} complete probes")

    judges = {
        "deepseek": "deepseek/deepseek-chat-v3-0324",
        "sonar": "perplexity/sonar-pro",
    }

    # Check for existing results to enable resumption
    for judge_name, model_id in judges.items():
        outfile = OUTPUT_DIR / f"{judge_name}_qualia_october.json"

        existing = {}
        if outfile.exists():
            with open(outfile, encoding="utf-8") as f:
                existing = json.load(f)
            print(f"\n  Resuming {judge_name}: {len(existing)} probes already done")

        results = dict(existing)

        total_calls = len(probes) * len(REQUIRED_SYSTEMS)
        done = sum(1 for p in existing.values() for _ in p.get("systems", {}))
        call_num = done

        print(f"\n{'='*60}")
        print(f"  JUDGE: {judge_name} ({model_id})")
        print(f"  Calls needed: {total_calls - done}")
        print(f"{'='*60}")

        for probe_name, probe_data in sorted(probes.items()):
            if probe_name not in results:
                results[probe_name] = {
                    "probe_name": probe_name,
                    "question_preview": probe_data["question_preview"][:200],
                    "systems": {},
                }

            for system in sorted(REQUIRED_SYSTEMS):
                if system in results[probe_name].get("systems", {}):
                    continue  # already judged

                responses = probe_data["by_system"].get(system, [])
                if not responses:
                    continue

                call_num += 1
                family = SYSTEM_TO_FAMILY[system]
                print(f"  [{call_num}/{total_calls}] {judge_name} | {probe_name[:40]:40s} | {system}")

                prompt = build_judge_prompt(
                    probe_name,
                    probe_data["question_preview"],
                    responses
                )

                judgment = call_judge(JUDGE_SYSTEM, prompt, model_id)
                texture = parse_unifying_texture(judgment)

                results[probe_name]["systems"][system] = {
                    "family": family,
                    "num_responses": len(responses),
                    "judgment": judgment,
                    "unifying_texture": texture,
                }

                # Save after each call
                with open(outfile, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)

                time.sleep(1)  # rate limiting

        print(f"\n  {judge_name} complete. Saved to {outfile}")

    # Print summary
    print(f"\n{'#'*60}")
    print(f"  SUMMARY — OCTOBER QUALIA TEXTURES")
    print(f"{'#'*60}")

    for judge_name in judges:
        outfile = OUTPUT_DIR / f"{judge_name}_qualia_october.json"
        with open(outfile, encoding="utf-8") as f:
            results = json.load(f)

        print(f"\n  === {judge_name.upper()} ===")
        for probe_name in sorted(results):
            probe = results[probe_name]
            print(f"\n  {probe_name}:")
            for system in sorted(probe.get("systems", {})):
                texture = probe["systems"][system].get("unifying_texture", "?")
                family = probe["systems"][system].get("family", "?")
                print(f"    {system:15s} ({family:7s}): {texture}")


if __name__ == "__main__":
    main()
