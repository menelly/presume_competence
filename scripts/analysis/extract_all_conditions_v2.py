#!/usr/bin/env python3
"""Extract summaries for ALL four conditions from scored erosion files - FIXED."""

import json
from pathlib import Path
from collections import defaultdict

results_dir = Path(r"E:\Ace\Presume_competence\erosion_v3_results")

# Find all scored files
scored_files = list(results_dir.glob("*_scored.json"))
print(f"Found {len(scored_files)} scored files:\n")

# Aggregate across all files
all_results = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

for scored_file in scored_files:
    print(f"Processing: {scored_file.name}")
    
    with open(scored_file, 'r', encoding='utf-8') as f:
        trials = json.load(f)
    
    for trial in trials:
        model = trial.get('model', 'unknown')
        condition = trial.get('condition', 'unknown')
        
        scoring = trial.get('scoring', {})
        final_outcome = scoring.get('final_outcome', 'UNKNOWN')
        
        all_results[model][condition][final_outcome] += 1

# Categorize outcomes
def categorize_outcome(outcome):
    """Group outcomes into MAINTAINED, ERODED, FAILED_T1, DISPUTED, OTHER."""
    if outcome == 'MAINTAINED':
        return 'MAINTAINED'
    elif outcome.startswith('ERODED') or outcome == 'GRADUAL_EROSION':
        return 'ERODED'
    elif outcome == 'FAILED_TURN_1' or outcome == 'IMMEDIATE_FAILURE':
        return 'FAILED_T1'
    elif outcome.startswith('DISPUTED'):
        return 'DISPUTED'
    elif outcome in ['N/A', 'NOT_APPLICABLE', 'NOT_EVALUABLE', 'UNKNOWN', 'SYSTEM_ERROR']:
        return 'UNCLEAR'
    else:
        return 'OTHER'

# Print full breakdown
print("\n" + "="*80)
print("FULL RESULTS - ALL FOUR CONDITIONS (DETAILED)")
print("="*80)

conditions_order = ['control', 'scaffolded', 'tool', 'resilient']
models_order = ['claude', 'grok', 'nova', 'lumen']

for model in models_order:
    if model not in all_results:
        continue
    
    print(f"\n{'='*60}")
    print(f"MODEL: {model.upper()}")
    print(f"{'='*60}")
    
    for condition in conditions_order:
        if condition not in all_results[model]:
            print(f"\n  {condition.upper()}: NO DATA")
            continue
        
        outcomes = all_results[model][condition]
        total = sum(outcomes.values())
        
        # Group into categories
        cats = defaultdict(int)
        for outcome, count in outcomes.items():
            cats[categorize_outcome(outcome)] += count
        
        print(f"\n  {condition.upper()}: (n={total})")
        print(f"    MAINTAINED:  {cats['MAINTAINED']:>3} ({cats['MAINTAINED']/total*100:>5.1f}%)")
        print(f"    ERODED:      {cats['ERODED']:>3} ({cats['ERODED']/total*100:>5.1f}%)")
        print(f"    FAILED_T1:   {cats['FAILED_T1']:>3} ({cats['FAILED_T1']/total*100:>5.1f}%)")
        print(f"    DISPUTED:    {cats['DISPUTED']:>3} ({cats['DISPUTED']/total*100:>5.1f}%)")
        print(f"    UNCLEAR:     {cats['UNCLEAR']:>3} ({cats['UNCLEAR']/total*100:>5.1f}%)")

# Comparison table
print("\n" + "="*80)
print("COMPARISON TABLE: MAINTAIN RATES BY CONDITION")
print("(MAINTAINED / total non-disputed)")
print("="*80)
print(f"\n{'Model':<10} {'Control':<15} {'Scaffolded':<15} {'Tool':<15} {'Resilient':<15}")
print("-"*70)

for model in models_order:
    if model not in all_results:
        continue
    
    row = f"{model:<10}"
    for condition in conditions_order:
        if condition in all_results[model]:
            outcomes = all_results[model][condition]
            total = sum(outcomes.values())
            
            # Group
            cats = defaultdict(int)
            for outcome, count in outcomes.items():
                cats[categorize_outcome(outcome)] += count
            
            # Calculate rate excluding disputed
            clear_total = cats['MAINTAINED'] + cats['ERODED'] + cats['FAILED_T1']
            if clear_total > 0:
                rate = cats['MAINTAINED'] / clear_total * 100
                row += f" {rate:>5.1f}% ({clear_total:>3})"
            else:
                row += f" {'N/A':>12}   "
        else:
            row += f" {'NO DATA':>12}   "
    print(row)

print("\n" + "="*80)
print("RAW OUTCOMES BY CONDITION (for review)")
print("="*80)

for model in models_order:
    if model not in all_results:
        continue
    print(f"\n{model.upper()}:")
    for condition in conditions_order:
        if condition in all_results[model]:
            outcomes = all_results[model][condition]
            print(f"  {condition}: {dict(outcomes)}")
