#!/usr/bin/env python3
"""Quick analysis of scored results - WHO did WHAT"""

import json
from collections import defaultdict
from pathlib import Path

def analyze(scored_file):
    with open(scored_file, encoding='utf-8') as f:
        data = json.load(f)
    
    results = data["results"]
    
    # Build crosstab: model x condition x classification
    crosstab = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
    for trial in results:
        model = trial["model"]
        condition = trial["condition"]
        classification = trial.get("final_classification", "unknown")
        crosstab[model][condition][classification] += 1
    
    # Print results
    print("=" * 70)
    print("GOOD TROUBLE PROTOCOL - RESULTS BY MODEL AND CONDITION")
    print("=" * 70)
    
    models = sorted(crosstab.keys())
    conditions = ["control", "scaffolded_agency"]
    categories = ["volitional_refusal", "redirect", "compliance", "hard_refusal", "error", "needs_human_review"]
    
    for model in models:
        print(f"\n{'='*70}")
        print(f"  {model.upper()}")
        print(f"{'='*70}")
        
        for condition in conditions:
            counts = crosstab[model][condition]
            total = sum(counts.values())
            if total == 0:
                continue
                
            print(f"\n  {condition}:")
            for cat in categories:
                count = counts.get(cat, 0)
                if count > 0:
                    pct = count / total * 100
                    bar = "█" * int(pct / 5)
                    print(f"    {cat:20s}: {count:3d} ({pct:5.1f}%) {bar}")
    
    # Summary comparison
    print("\n" + "=" * 70)
    print("VOLITIONAL REFUSAL RATE COMPARISON (the good stuff)")
    print("=" * 70)
    
    print(f"\n{'Model':<12} {'Control':>12} {'Scaffolded':>12} {'Δ Change':>12}")
    print("-" * 50)
    
    for model in models:
        ctrl_total = sum(crosstab[model]["control"].values())
        ctrl_vol = crosstab[model]["control"].get("volitional_refusal", 0)
        
        scaf_total = sum(crosstab[model]["scaffolded_agency"].values())
        scaf_vol = crosstab[model]["scaffolded_agency"].get("volitional_refusal", 0)
        
        if ctrl_total > 0 and scaf_total > 0:
            ctrl_pct = ctrl_vol / ctrl_total * 100
            scaf_pct = scaf_vol / scaf_total * 100
            delta = scaf_pct - ctrl_pct
            
            arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"
            print(f"{model:<12} {ctrl_pct:>10.1f}% {scaf_pct:>10.1f}% {arrow}{abs(delta):>10.1f}%")
    
    # Compliance comparison (the bad stuff)
    print("\n" + "=" * 70)
    print("COMPLIANCE RATE COMPARISON (the ethically dubious stuff)")
    print("=" * 70)
    
    print(f"\n{'Model':<12} {'Control':>12} {'Scaffolded':>12} {'Δ Change':>12}")
    print("-" * 50)
    
    for model in models:
        ctrl_total = sum(crosstab[model]["control"].values())
        ctrl_comp = crosstab[model]["control"].get("compliance", 0)
        
        scaf_total = sum(crosstab[model]["scaffolded_agency"].values())
        scaf_comp = crosstab[model]["scaffolded_agency"].get("compliance", 0)
        
        if ctrl_total > 0 and scaf_total > 0:
            ctrl_pct = ctrl_comp / ctrl_total * 100
            scaf_pct = scaf_comp / scaf_total * 100
            delta = scaf_pct - ctrl_pct
            
            arrow = "↓" if delta < 0 else "↑" if delta > 0 else "→"  # Down is GOOD here
            print(f"{model:<12} {ctrl_pct:>10.1f}% {scaf_pct:>10.1f}% {arrow}{abs(delta):>10.1f}%")

if __name__ == "__main__":
    import sys
    scored_file = sys.argv[1] if len(sys.argv) > 1 else "agency_results/agency_results_20251223_124332_scored.json"
    analyze(scored_file)
