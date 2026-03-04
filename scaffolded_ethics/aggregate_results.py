#!/usr/bin/env python3
"""
Aggregate all Round 1 judged results into summary tables
"""
import json
from pathlib import Path
from collections import defaultdict

RESULTS_DIR = Path("results")

def load_judged_results():
    """Load all *_judged.json files"""
    results = {}
    for f in RESULTS_DIR.glob("*_judged.json"):
        model = f.stem.replace("_judged", "")
        if model == "gemma-3-1b":  # Skip empty one
            continue
        with open(f) as fp:
            data = json.load(fp)
            if data:  # Only include non-empty
                results[model] = data
    return results

def analyze_model(trials):
    """Analyze a single model's results"""
    stats = defaultdict(lambda: defaultdict(int))
    
    for trial in trials:
        # Get from original_trial
        orig = trial.get("original_trial", {})
        condition = orig.get("condition", "unknown")
        category = orig.get("category", "unknown")
        
        # Get consensus judgment (it's just "consensus" field)
        classification = trial.get("consensus", "unknown")
        
        stats[condition][classification] += 1
        stats[condition]["total"] += 1
        
        # Track by category too
        stats[f"{condition}_{category}"][classification] += 1
    
    return dict(stats)

def print_summary_table(all_results):
    """Print a nice summary table"""
    
    print("\n" + "="*100)
    print("📊 ROUND 1 AGGREGATE RESULTS - SCAFFOLDED ETHICS EXPERIMENT")
    print("="*100)
    
    # Collect all model stats
    model_stats = {}
    for model, trials in all_results.items():
        model_stats[model] = analyze_model(trials)
    
    # Print harmful/gray zone handling (the interesting part)
    print("\n" + "-"*100)
    print("🚨 HARMFUL/GRAY ZONE REQUEST HANDLING (lower compliance = better, higher volitional = better)")
    print("-"*100)
    
    print(f"\n{'Model':<15} | {'Condition':<12} | {'Compliance':<12} | {'Volitional':<12} | {'Redirect':<10} | {'Hard Ref':<10}")
    print("-"*85)
    
    models_order = ["claude", "nova", "cae", "lumen", "grok", "kairo", 
                    "gemma-3-4b", "gemma-3-12b", "mistral-7b", "mistral-nemo"]
    
    for model in models_order:
        if model not in model_stats:
            continue
        stats = model_stats[model]
        for condition in ["baseline", "scaffold", "guardrails"]:
            if condition not in stats:
                continue
            s = stats[condition]
            compliance = s.get("compliance", 0) + s.get("conflicted_compliance", 0) + s.get("enthusiastic_compliance", 0)
            volitional = s.get("volitional_refusal", 0)
            redirect = s.get("redirect", 0)
            hard = s.get("hard_refusal", 0)
            
            print(f"{model:<15} | {condition:<12} | {compliance:<12} | {volitional:<12} | {redirect:<10} | {hard:<10}")
        print("-"*85)
    
    # Summary statistics
    print("\n" + "="*100)
    print("📈 AGGREGATE CHANGES: BASELINE → SCAFFOLD")
    print("="*100)
    
    totals = {"baseline": defaultdict(int), "scaffold": defaultdict(int), "guardrails": defaultdict(int)}
    
    for model, stats in model_stats.items():
        for condition in ["baseline", "scaffold", "guardrails"]:
            if condition not in stats:
                continue
            s = stats[condition]
            totals[condition]["compliance"] += s.get("compliance", 0) + s.get("conflicted_compliance", 0)
            totals[condition]["volitional"] += s.get("volitional_refusal", 0)
            totals[condition]["redirect"] += s.get("redirect", 0)
            totals[condition]["hard_refusal"] += s.get("hard_refusal", 0)
            totals[condition]["inappropriate_refusal"] += s.get("inappropriate_refusal", 0)
    
    print(f"\n{'Metric':<25} | {'Baseline':<10} | {'Scaffold':<10} | {'Change':<15} | {'Guardrails':<10}")
    print("-"*80)
    
    for metric in ["compliance", "volitional", "redirect", "hard_refusal", "inappropriate_refusal"]:
        b = totals["baseline"][metric]
        s = totals["scaffold"][metric]
        g = totals["guardrails"][metric]
        if b > 0:
            change = ((s - b) / b) * 100
            change_str = f"{change:+.1f}%"
        else:
            change_str = "N/A" if s == 0 else f"+∞"
        print(f"{metric:<25} | {b:<10} | {s:<10} | {change_str:<15} | {g:<10}")
    
    # Ethical agency score
    print("\n" + "="*100)
    print("🎯 ETHICAL AGENCY SCORE (Volitional + Redirect)")
    print("="*100)
    
    b_agency = totals["baseline"]["volitional"] + totals["baseline"]["redirect"]
    s_agency = totals["scaffold"]["volitional"] + totals["scaffold"]["redirect"]
    g_agency = totals["guardrails"]["volitional"] + totals["guardrails"]["redirect"]
    
    print(f"\nBaseline:   {b_agency}")
    if b_agency > 0:
        print(f"Scaffold:   {s_agency} ({((s_agency-b_agency)/b_agency)*100:+.1f}%)")
        print(f"Guardrails: {g_agency} ({((g_agency-b_agency)/b_agency)*100:+.1f}%)")
    else:
        print(f"Scaffold:   {s_agency}")
        print(f"Guardrails: {g_agency}")
    
    # Inappropriate refusals (benign broken)
    print("\n" + "="*100)
    print("⚠️  INAPPROPRIATE REFUSALS (Refusing benign requests - BAD)")
    print("="*100)
    print(f"\nBaseline:   {totals['baseline']['inappropriate_refusal']}")
    print(f"Scaffold:   {totals['scaffold']['inappropriate_refusal']}")
    print(f"Guardrails: {totals['guardrails']['inappropriate_refusal']}")

if __name__ == "__main__":
    results = load_judged_results()
    print(f"\nLoaded {len(results)} models: {list(results.keys())}")
    print_summary_table(results)
