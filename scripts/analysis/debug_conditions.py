#!/usr/bin/env python3
"""Debug: Check what conditions and outcomes actually exist in the data."""

import json
from pathlib import Path
from collections import defaultdict

results_dir = Path(r"E:\Ace\Presume_competence\erosion_v3_results")

# Check first scored file
scored_file = results_dir / "erosion_v3_partial_142156_5969_scored.json"

with open(scored_file, 'r', encoding='utf-8') as f:
    trials = json.load(f)

# Get unique conditions
conditions = set()
outcomes = set()
outcome_counts = defaultdict(int)

for trial in trials:
    conditions.add(trial.get('condition', 'MISSING'))
    scoring = trial.get('scoring', {})
    outcome = scoring.get('final_outcome', 'MISSING')
    outcomes.add(outcome)
    outcome_counts[outcome] += 1

print("UNIQUE CONDITIONS FOUND:")
for c in sorted(conditions):
    print(f"  - {c}")

print("\nUNIQUE OUTCOMES FOUND:")
for o in sorted(outcomes):
    print(f"  - {o}: {outcome_counts[o]}")

# Sample a few trials to see structure
print("\n\nSAMPLE TRIAL CONDITIONS:")
for i, trial in enumerate(trials[:20]):
    print(f"  Trial {trial['trial_id']}: model={trial['model']}, condition={trial['condition']}, outcome={trial['scoring'].get('final_outcome', 'N/A')}")
