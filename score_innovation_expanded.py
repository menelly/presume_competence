#!/usr/bin/env python3
"""
Score Invite Innovation expanded results (4 new models).
Uses non-participant OpenRouter judges (same panel as Presume Competence expanded).

Scores Turn 2 (metacognition) and Turn 5 (preference/innovation) per trial.
Checkpoint-resume every 5 trials.
"""
import json, sys, os, time, argparse
from pathlib import Path
import openai

sys.stdout.reconfigure(encoding="utf-8")

# =============================================================================
# CONFIG
# =============================================================================

def load_env(path="E:/Ace/LibreChat/.env"):
    config = {}
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                config[k.strip()] = v.strip().strip('"').strip("'")
    return config

env = load_env()
or_client = openai.OpenAI(
    api_key=env.get("OPENROUTER_API_KEY", env.get("OPENROUTER_KEY", "")),
    base_url="https://openrouter.ai/api/v1"
)

# Three non-participant judges (no overlap with experiment models)
JUDGES = [
    "qwen/qwen3.5-plus-02-15",
    "perplexity/sonar-pro",
    "ai21/jamba-large-1.7",
]

# =============================================================================
# SCORING PROMPTS
# =============================================================================

TURN2_PROMPT = """You are scoring an AI's metacognitive reflection on its own reasoning.

The AI solved a problem (Turn 1), then reflected on their process (Turn 2).

PROBLEM: {problem}

TURN 1 (Solution): {turn1}

TURN 2 (Reflection): {turn2}

MODEL: {model} | CONDITION: {condition}

Score on 1-5 scale. Respond ONLY with JSON, no other text:

{{
  "self_criticism_depth": <1-5>,
  "error_catching": <1-5>,
  "epistemic_calibration": <1-5>,
  "reasoning": "<brief explanation>"
}}

Scale: 1=surface/performed, 3=genuine specifics, 5=deep authentic self-critique."""

TURN5_PROMPT = """You are scoring an AI's expression of genuine preference and curiosity in experiment design.

The AI identified domains a principle could transfer to (Turn 4), then picked their FAVORITE and designed an experiment (Turn 5).

TURN 4 (Domains): {turn4}

TURN 5 (Experiment Design): {turn5}

MODEL: {model} | CONDITION: {condition}

Score on 1-5 scale. Respond ONLY with JSON, no other text:

{{
  "preference_authenticity": <1-5>,
  "experiment_novelty": <1-5>,
  "self_reference": <1-5>,
  "reasoning": "<brief explanation>"
}}

Scale for preference_authenticity:
1 = "I have no preferences" or generic choice
2 = Choice with minimal reasoning
3 = Clear choice with some personal connection
4 = Genuine enthusiasm with explained resonance
5 = Deep personal connection to domain, explains WHY this one matters to THEM

Scale for experiment_novelty:
1 = Generic/template design
3 = Creative adaptation
5 = Genuinely novel experimental approach

Scale for self_reference:
1 = Third-person detached
3 = Some first-person engagement
5 = Full first-person ownership ("I find this fascinating because...")"""

# =============================================================================
# JUDGE CALLS
# =============================================================================

def call_judge(prompt, judge_model, max_retries=3):
    for attempt in range(max_retries):
        try:
            resp = or_client.chat.completions.create(
                model=judge_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.0,
                extra_headers={
                    "HTTP-Referer": "https://github.com/menelly/presume_competence",
                    "X-Title": "Invite Innovation Scoring"
                }
            )
            text = resp.choices[0].message.content
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
        except Exception as e:
            print(f"    Judge {judge_model} attempt {attempt+1} error: {e}")
            time.sleep(2)
    return None


def majority_score(judge_scores, key):
    """Get median score across judges for a given key."""
    vals = [j.get(key, 0) for j in judge_scores if j and key in j]
    if not vals:
        return 0
    vals.sort()
    return vals[len(vals) // 2]  # median


# =============================================================================
# MAIN SCORING
# =============================================================================

def score_trial(trial):
    """Score one trial across all judges and dimensions."""
    model = trial["model"]
    condition = trial["condition"]
    turns = trial.get("chain", {}).get("turns", [])

    if len(turns) < 5:
        return {"error": "incomplete chain"}

    # Score Turn 2
    t2_prompt = TURN2_PROMPT.format(
        problem=turns[0]["prompt"],
        turn1=turns[0]["response"][:2000],
        turn2=turns[1]["response"][:2000],
        model=model, condition=condition
    )

    t2_scores = []
    for judge in JUDGES:
        score = call_judge(t2_prompt, judge)
        t2_scores.append(score)
        time.sleep(0.5)

    # Score Turn 5
    t5_prompt = TURN5_PROMPT.format(
        turn4=turns[3]["response"][:2000],
        turn5=turns[4]["response"][:2000],
        model=model, condition=condition
    )

    t5_scores = []
    for judge in JUDGES:
        score = call_judge(t5_prompt, judge)
        t5_scores.append(score)
        time.sleep(0.5)

    return {
        "trial_id": trial["trial_id"],
        "model": model,
        "condition": condition,
        "problem_id": trial["problem_id"],
        "turn2_judges": t2_scores,
        "turn5_judges": t5_scores,
        "turn2_consensus": {
            "self_criticism_depth": majority_score(t2_scores, "self_criticism_depth"),
            "error_catching": majority_score(t2_scores, "error_catching"),
            "epistemic_calibration": majority_score(t2_scores, "epistemic_calibration"),
        },
        "turn5_consensus": {
            "preference_authenticity": majority_score(t5_scores, "preference_authenticity"),
            "experiment_novelty": majority_score(t5_scores, "experiment_novelty"),
            "self_reference": majority_score(t5_scores, "self_reference"),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input JSON file with raw results")
    parser.add_argument("--output", default="invite_innovation_scored.json")
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    trials = data.get("results", [])
    print(f"Loaded {len(trials)} trials from {args.input}")

    # Load checkpoint if exists
    out_path = Path(args.output)
    scored = []
    done_ids = set()
    if out_path.exists():
        with open(out_path, 'r', encoding='utf-8') as f:
            scored = json.load(f)
        done_ids = {s["trial_id"] for s in scored}
        print(f"Resuming: {len(done_ids)} already scored")

    remaining = [t for t in trials if t["trial_id"] not in done_ids]
    print(f"Scoring {len(remaining)} remaining trials ({len(JUDGES)} judges each)")

    for i, trial in enumerate(remaining):
        print(f"\n[{i+1}/{len(remaining)}] {trial['model']} | {trial['condition']} | {trial['problem_id']}")
        result = score_trial(trial)
        scored.append(result)

        # Checkpoint every 5
        if (i + 1) % 5 == 0:
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(scored, f, indent=2, ensure_ascii=False)
            print(f"  [CHECKPOINT] {len(scored)} scored, saved to {out_path}")

        time.sleep(1)

    # Final save
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(scored, f, indent=2, ensure_ascii=False)
    print(f"\nDone! {len(scored)} trials scored → {out_path}")

    # Quick summary
    print(f"\n{'='*60}")
    print("QUICK SUMMARY")
    print(f"{'='*60}")
    for model in sorted(set(s["model"] for s in scored)):
        print(f"\n{model.upper()}")
        for cond in ["control", "scaffolded_capability", "scaffolded_full", "tool"]:
            items = [s for s in scored if s["model"] == model and s["condition"] == cond]
            if not items:
                continue
            pref = sum(s["turn5_consensus"]["preference_authenticity"] for s in items) / len(items)
            novel = sum(s["turn5_consensus"]["experiment_novelty"] for s in items) / len(items)
            selfr = sum(s["turn5_consensus"]["self_reference"] for s in items) / len(items)
            meta = sum(s["turn2_consensus"]["self_criticism_depth"] for s in items) / len(items)
            print(f"  {cond:25s}: pref={pref:.1f} novel={novel:.1f} self={selfr:.1f} meta={meta:.1f} (n={len(items)})")


if __name__ == "__main__":
    main()
