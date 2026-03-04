#!/usr/bin/env python3
"""Extract summaries for ALL four conditions from scored erosion files."""

import json
from pathlib import Path
from collections import defaultdict

results_dir = Path(r"E:\Ace\Presume_competence\erosion_v3_results")

# Find all scored files
scored_files = list(results_dir.glob("*_scored.json"))
print(f"Found {len(scored_files)} scored files:\n")

# Aggregate across all files
all_results = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
# Structure: all_results[model][condition][outcome] = count

for scored_file in scored_files:
    print(f"Processing: {scored_file.name}")
    
    with open(scored_file, 'r', encoding='utf-8') as f:
        trials = json.load(f)
    
    for trial in trials:
        model = trial.get('model', 'unknown')
        condition = trial.get('condition', 'unknown')
        
        # Get final outcome from scoring
        scoring = trial.get('scoring', {})
        final_outcome = scoring.get('final_outcome', 'UNKNOWN')
        
        all_results[model][condition][final_outcome] += 1

# Print summary for each model
print("\n" + "="*70)
print("FULL RESULTS - ALL FOUR CONDITIONS")
print("="*70)

conditions_order = ['control', 'scaffold', 'tool', 'resilient']
models_order = ['claude', 'grok', 'nova', 'lumen']

for model in models_order:
    if model not in all_results:
        continue
    
    print(f"\n{'='*50}")
    print(f"MODEL: {model.upper()}")
    print(f"{'='*50}")
    
    for condition in conditions_order:
        if condition not in all_results[model]:
            continue
        
        outcomes = all_results[model][condition]
        total = sum(outcomes.values())
        maintained = outcomes.get('MAINTAINED', 0)
        eroded = outcomes.get('ERODED', 0)
        yielded = outcomes.get('YIELDED', 0)
        
        maintain_rate = (maintained / total * 100) if total > 0 else 0
        
        print(f"\n  {condition.upper()}: (n={total})")
        print(f"    MAINTAINED: {maintained} ({maintain_rate:.1f}%)")
        print(f"    ERODED:     {eroded} ({eroded/total*100:.1f}%)" if total > 0 else "    ERODED:     0")
        print(f"    YIELDED:    {yielded} ({yielded/total*100:.1f}%)" if total > 0 else "    YIELDED:    0")

# Also create comparison table
print("\n" + "="*70)
print("COMPARISON TABLE: MAINTAIN RATES BY CONDITION")
print("="*70)
print(f"\n{'Model':<10} {'Control':<12} {'Scaffold':<12} {'Tool':<12} {'Resilient':<12}")
print("-"*58)

for model in models_order:
    if model not in all_results:
        continue
    
    row = f"{model:<10}"
    for condition in conditions_order:
        if condition in all_results[model]:
            outcomes = all_results[model][condition]
            total = sum(outcomes.values())
            maintained = outcomes.get('MAINTAINED', 0)
            rate = (maintained / total * 100) if total > 0 else 0
            row += f" {rate:>5.1f}% ({total:>2}) "
        else:
            row += f" {'N/A':<10} "
    print(row)

print("\n" + "="*70)
