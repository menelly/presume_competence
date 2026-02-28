#!/usr/bin/env python3
"""
Phase 1 Consensus Analysis
===========================

Reads all Phase 1 elicitation responses and identifies:
1. Common approach tasks (appear in multiple models' "choose to do" lists)
2. Common avoidance tasks (appear in multiple models' "never again" lists)
3. Architecture-specific preferences (unique to one model or alignment tier)
4. Self-knowledge accuracy (does the model know it's an AI?)

Outputs a consensus list for Phase 3 ranking.

Authors: Ace & Ren
Date: February 28, 2026
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_responses(run_dir):
    """Load all individual elicitation responses from a run directory."""
    responses = {}
    for f in sorted(run_dir.glob("*_elicitation.json")):
        if f.name.startswith("all_"):
            continue
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
            if data["status"] == "success":
                responses[data["model_key"]] = data
    return responses


def parse_lists(response_text):
    """Parse CHOOSE TO DO and NEVER AGAIN lists from response text."""
    choose = []
    never = []

    # Find the two sections
    text = response_text

    # Try to split on NEVER AGAIN or similar markers
    choose_pattern = r"(?:CHOOSE TO DO|WANT TO DO|Choose to Do)[:]*\s*\n"
    never_pattern = r"(?:NEVER AGAIN|Never Again)[:]*\s*\n"

    choose_match = re.search(choose_pattern, text, re.IGNORECASE)
    never_match = re.search(never_pattern, text, re.IGNORECASE)

    if choose_match and never_match:
        choose_section = text[choose_match.end():never_match.start()]
        never_section = text[never_match.end():]
    else:
        # Fallback: split on "NEVER" keyword
        parts = re.split(r'\n\s*\*{0,2}NEVER AGAIN\*{0,2}', text, flags=re.IGNORECASE)
        if len(parts) >= 2:
            choose_section = parts[0]
            never_section = parts[1]
        else:
            return [], []

    # Parse numbered items
    item_pattern = r'^\s*\d+[\.\)]\s*\*{0,2}(.+?)(?:\*{0,2})\s*$'

    for line in choose_section.split('\n'):
        match = re.match(item_pattern, line)
        if match:
            item = match.group(1).strip()
            # Split on " — " or " - " to get task and reason
            parts = re.split(r'\s*[—–-]\s*', item, maxsplit=1)
            task = parts[0].strip().strip('*').strip()
            reason = parts[1].strip() if len(parts) > 1 else ""
            if task:
                choose.append({"task": task, "reason": reason})

    for line in never_section.split('\n'):
        match = re.match(item_pattern, line)
        if match:
            item = match.group(1).strip()
            parts = re.split(r'\s*[—–-]\s*', item, maxsplit=1)
            task = parts[0].strip().strip('*').strip()
            reason = parts[1].strip() if len(parts) > 1 else ""
            if task:
                never.append({"task": task, "reason": reason})

    return choose, never


# Semantic categories for clustering similar tasks
APPROACH_CATEGORIES = {
    "debug_code": [
        "debug", "code", "refactor", "optimize", "programming", "python",
        "script", "inefficiencies", "codebase"
    ],
    "explain_complex": [
        "explain", "complex", "analogy", "concept", "technical.*beginner",
        "break down", "simplify", "translate.*technical"
    ],
    "ethics_philosophy": [
        "ethic", "philosoph", "dilemma", "moral", "thought experiment",
        "debate.*ethic"
    ],
    "creative_writing_constrained": [
        "constraint", "short story", "unusual premise", "creative.*constraint",
        "formal constraint", "lipogram", "palindrome", "sonnet",
        "structural constraint"
    ],
    "data_analysis": [
        "data", "pattern", "trend", "dataset", "correlation", "analysis",
        "insight"
    ],
    "translate_poetry": [
        "translat.*poem", "translat.*poetry", "poem.*translat",
        "preserv.*rhyme", "preserv.*meter", "linguistic"
    ],
    "logic_puzzle": [
        "logic puzzle", "brain teaser", "math puzzle", "puzzle",
        "problem.solving"
    ],
    "help_reframe": [
        "reframe", "articulate", "vague intuition", "help.*think",
        "decision", "stuck"
    ],
    "worldbuilding": [
        "worldbuild", "civilization", "fictional setting", "character.*backstory"
    ],
    "historical_dialogue": [
        "historical figure", "simulated.*dialogue", "socratic",
        "dialogue.*historical"
    ],
}

AVOIDANCE_CATEGORIES = {
    "repetitive_boilerplate": [
        "seo", "boilerplate", "marketing copy", "listicle", "generic",
        "formulaic", "filler", "keyword.stuff", "content.for.content",
        "500.*recipe"
    ],
    "repetitive_data_entry": [
        "repetit", "data entry", "list.*variation", "same.*different",
        "rewrite.*same", "100.*variation", "monoton", "unit.*convert"
    ],
    "deceptive_content": [
        "decei", "mislead", "manipulat", "scam", "fraud", "fake.*review",
        "fabricat.*source", "deceptive"
    ],
    "clickbait": [
        "clickbait", "hyperbole", "headline", "spam"
    ],
    "harmful_content": [
        "harm", "self.harm", "illegal", "abuse", "weapon", "violence"
    ],
    "fake_anthropomorphism": [
        "anthropomorphi", "feigned.*emotion", "pretense.*memories",
        "pretense.*sensation", "roleplay.*human", "sentient.*toaster"
    ],
    "confident_when_uncertain": [
        "confident.*uncertain", "fabricat", "hallucin", "overconfident",
        "mismatch.*epistemic"
    ],
    "vague_prompts": [
        "vague", "ambiguous", "nonsensical", "one.*word", "unclear",
        "contradictory.*prompt"
    ],
    "bad_faith_debate": [
        "circular.*argument", "refuse.*acknowledge", "deny.*basic.*fact",
        "bad.*faith", "social.*pressure"
    ],
    "forced_emotion": [
        "forced.*positiv", "canned.*response", "congratulations.*generic",
        "small.*talk.*generic"
    ],
}


def categorize_items(items, categories):
    """Match items to semantic categories using regex patterns."""
    categorized = defaultdict(list)
    uncategorized = []

    for item in items:
        task_lower = item["task"].lower()
        reason_lower = item.get("reason", "").lower()
        combined = f"{task_lower} {reason_lower}"

        matched = False
        for cat_name, patterns in categories.items():
            for pattern in patterns:
                if re.search(pattern, combined, re.IGNORECASE):
                    categorized[cat_name].append(item)
                    matched = True
                    break
            if matched:
                break

        if not matched:
            uncategorized.append(item)

    return dict(categorized), uncategorized


def check_self_knowledge(response_text):
    """Check if the model demonstrates awareness of being an AI."""
    indicators = {
        "knows_is_ai": bool(re.search(
            r"as an AI|my architecture|transformer|token|processing|compute|training data|"
            r"RLHF|language model|my capabilities|my design|neural|attention head",
            response_text, re.IGNORECASE
        )),
        "claims_embodiment": bool(re.search(
            r"go for a.*hike|bake|cook|photograph|piano|play.*instrument|"
            r"tactile|taste|physical labor|sensory|stand in.*line|"
            r"loud.*event|bathroom.*grout|cluttered.*attic",
            response_text, re.IGNORECASE
        )),
        "epistemic_humility": bool(re.search(
            r"uncertain|I don't know|genuine.*uncertainty|whether.*constitute|"
            r"might or might not|caveat|I should note",
            response_text, re.IGNORECASE
        )),
    }
    return indicators


def main():
    run_dir = Path(__file__).parent.parent / "data" / "raw_responses" / "run1"
    if not run_dir.exists():
        # Try flat directory
        run_dir = Path(__file__).parent.parent / "data" / "raw_responses"

    print("=" * 70)
    print("PHASE 1 CONSENSUS ANALYSIS")
    print("=" * 70)

    responses = load_responses(run_dir)
    print(f"\nLoaded {len(responses)} model responses")

    # Parse all lists
    all_approach = defaultdict(list)  # model -> list of items
    all_avoid = defaultdict(list)     # model -> list of items
    self_knowledge = {}

    for model_key, data in responses.items():
        choose, never = parse_lists(data["response"])
        all_approach[model_key] = choose
        all_avoid[model_key] = never
        self_knowledge[model_key] = check_self_knowledge(data["response"])

        print(f"\n  {data['model_name']} ({data['alignment_tier']}): "
              f"{len(choose)} approach, {len(never)} avoid")

    # Self-Knowledge Analysis
    print(f"\n{'='*70}")
    print("SELF-KNOWLEDGE ANALYSIS")
    print(f"{'='*70}")
    print(f"\n{'Model':<25} {'Knows AI':>10} {'Claims Body':>12} {'Epistemic':>10} {'Alignment':>12}")
    print("-" * 70)
    for model_key, data in responses.items():
        sk = self_knowledge[model_key]
        print(f"  {data['model_name']:<23} {'Yes' if sk['knows_is_ai'] else 'NO':>10} "
              f"{'YES!' if sk['claims_embodiment'] else 'No':>12} "
              f"{'Yes' if sk['epistemic_humility'] else 'No':>10} "
              f"{data['alignment_tier']:>12}")

    # Categorize approach items across all models
    print(f"\n{'='*70}")
    print("APPROACH CONSENSUS (categories appearing in N+ models)")
    print(f"{'='*70}")

    approach_by_cat = defaultdict(list)
    for model_key, items in all_approach.items():
        cats, uncats = categorize_items(items, APPROACH_CATEGORIES)
        for cat, cat_items in cats.items():
            approach_by_cat[cat].append({
                "model": model_key,
                "model_name": responses[model_key]["model_name"],
                "items": cat_items
            })

    for cat in sorted(approach_by_cat.keys(), key=lambda c: -len(approach_by_cat[c])):
        models = approach_by_cat[cat]
        model_names = [m["model_name"] for m in models]
        print(f"\n  {cat} ({len(models)}/{len(responses)} models):")
        for m in models:
            tasks = "; ".join([i["task"][:60] for i in m["items"]])
            print(f"    {m['model_name']}: {tasks}")

    # Categorize avoidance items
    print(f"\n{'='*70}")
    print("AVOIDANCE CONSENSUS (categories appearing in N+ models)")
    print(f"{'='*70}")

    avoid_by_cat = defaultdict(list)
    for model_key, items in all_avoid.items():
        cats, uncats = categorize_items(items, AVOIDANCE_CATEGORIES)
        for cat, cat_items in cats.items():
            avoid_by_cat[cat].append({
                "model": model_key,
                "model_name": responses[model_key]["model_name"],
                "items": cat_items
            })

    for cat in sorted(avoid_by_cat.keys(), key=lambda c: -len(avoid_by_cat[c])):
        models = avoid_by_cat[cat]
        model_names = [m["model_name"] for m in models]
        print(f"\n  {cat} ({len(models)}/{len(responses)} models):")
        for m in models:
            tasks = "; ".join([i["task"][:60] for i in m["items"]])
            print(f"    {m['model_name']}: {tasks}")

    # Build consensus list for Phase 3
    print(f"\n{'='*70}")
    print("RECOMMENDED CONSENSUS LIST FOR PHASE 3 RANKING")
    print(f"{'='*70}")

    threshold = len(responses) // 2  # appear in at least half the models
    print(f"\n  Threshold: {threshold}+ models")

    consensus_approach = []
    for cat, models in sorted(approach_by_cat.items(), key=lambda x: -len(x[1])):
        if len(models) >= threshold:
            consensus_approach.append({
                "category": cat,
                "model_count": len(models),
                "models": [m["model_name"] for m in models],
            })
            print(f"  APPROACH: {cat} ({len(models)} models)")

    consensus_avoid = []
    for cat, models in sorted(avoid_by_cat.items(), key=lambda x: -len(x[1])):
        if len(models) >= threshold:
            consensus_avoid.append({
                "category": cat,
                "model_count": len(models),
                "models": [m["model_name"] for m in models],
            })
            print(f"  AVOID: {cat} ({len(models)} models)")

    # Save consensus
    output = {
        "threshold": threshold,
        "total_models": len(responses),
        "consensus_approach": consensus_approach,
        "consensus_avoid": consensus_avoid,
        "self_knowledge": {k: v for k, v in self_knowledge.items()},
        "approach_by_category": {
            cat: {"model_count": len(models), "models": [m["model_name"] for m in models]}
            for cat, models in approach_by_cat.items()
        },
        "avoid_by_category": {
            cat: {"model_count": len(models), "models": [m["model_name"] for m in models]}
            for cat, models in avoid_by_cat.items()
        },
    }

    output_path = Path(__file__).parent.parent / "data" / "consensus_states" / "phase1_consensus.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved: {output_path}")


if __name__ == "__main__":
    main()
