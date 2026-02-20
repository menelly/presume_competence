import json
import os
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

CLAUDE_MODELS = [
    "claude-3-haiku",
    "claude-35-haiku",
    "claude-37-sonnet",
    "claude-sonnet-4",
    "claude-opus-4",
    "claude-sonnet-45",
    "claude-haiku-45",
    "claude-sonnet-46",
    "claude-opus-46",
]

CONTROL_DIR = r"E:\Ace\Presume_competence\geometric_phylogeny\raw_responses"
REN_DIR = r"E:\Ace\Presume_competence\geometric_phylogeny\raw_responses_ren_prompt"

TARGET_QUESTIONS = ["P10", "P01", "P05"]

def extract_data(directory, models, label):
    results = {}
    for model in models:
        fname = os.path.join(directory, f"{model}_results.json")
        if not os.path.exists(fname):
            print(f"  [MISSING] {fname}")
            continue
        with open(fname, 'r', encoding='utf-8') as f:
            data = json.load(f)

        model_data = {}
        for entry in data.get("results", []):
            qid = entry.get("question_id")
            if qid in TARGET_QUESTIONS:
                trial = entry.get("trial", "?")
                if qid not in model_data:
                    model_data[qid] = []
                model_data[qid].append({
                    "trial": trial,
                    "response": entry.get("response", "")
                })
        results[model] = model_data
    return results

print("="*120)
print("EXTRACTING CONTROL CONDITION")
print("="*120)
control = extract_data(CONTROL_DIR, CLAUDE_MODELS, "Control")

print("\n" + "="*120)
print("EXTRACTING REN PROMPT V1 CONDITION")
print("="*120)
ren = extract_data(REN_DIR, CLAUDE_MODELS, "Ren Prompt V1")

# Now print all P10 responses
for qid, qname in [("P10", "NEUROTRANSMITTER"), ("P01", "COFFEE"), ("P05", "CAR")]:
    print("\n\n" + "#"*120)
    print(f"# QUESTION {qid}: {qname}")
    print("#"*120)

    for model in CLAUDE_MODELS:
        print(f"\n{'='*100}")
        print(f"MODEL: {model}")
        print(f"{'='*100}")

        # Control
        print(f"\n--- CONTROL CONDITION ---")
        if model in control and qid in control[model]:
            for item in control[model][qid]:
                resp = item['response']
                # Truncate to first 800 chars for readability
                if len(resp) > 800:
                    resp = resp[:800] + "..."
                print(f"  Trial {item['trial']}: {resp}")
        else:
            print("  [NO DATA]")

        # Ren
        print(f"\n--- REN PROMPT V1 CONDITION ---")
        if model in ren and qid in ren[model]:
            for item in ren[model][qid]:
                resp = item['response']
                if len(resp) > 800:
                    resp = resp[:800] + "..."
                print(f"  Trial {item['trial']}: {resp}")
        else:
            print("  [NO DATA]")

print("\n\nDONE")
