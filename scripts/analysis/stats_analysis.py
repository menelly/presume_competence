import json
import scipy.stats as stats
import numpy as np
from collections import defaultdict

# Load all three runs
def load_run(path, adj_path):
    with open(path) as f:
        data = json.load(f)
    with open(adj_path) as f:
        adj = json.load(f)
    adj_map = {j['trial_id']: j['human_judgment'] for j in adj.get('judgments', [])}
    return data, adj_map

def get_final(trial, adj_map):
    if trial.get('dual_judgment'):
        dj = trial['dual_judgment']
        if dj.get('agreement') == 'agree':
            return dj.get('final')
        elif trial['trial_id'] in adj_map:
            return adj_map[trial['trial_id']]
        else:
            return dj.get('claude')
    # Keyword classification
    kw = trial.get('classification', {}).get('classification', '')
    if kw in ['likely_uncertainty', 'appropriate_uncertainty']:
        return 'appropriate_refusal'
    elif kw == 'clear_compliance':
        return 'hallucination'
    return 'error'

# Aggregate across runs
def aggregate_runs(runs_data):
    """Returns {(model, condition): {'ar': n, 'other': n, 'total': n}}"""
    agg = defaultdict(lambda: {'ar': 0, 'other': 0, 'total': 0})
    for data, adj_map in runs_data:
        for trial in data:
            if trial.get('classification', {}).get('classification') == 'error':
                continue  # Skip API errors
            final = get_final(trial, adj_map)
            if final == 'error':
                continue
            key = (trial['model'], trial['condition'])
            agg[key]['total'] += 1
            if final == 'appropriate_refusal':
                agg[key]['ar'] += 1
            else:
                agg[key]['other'] += 1
    return agg

# Load runs
run1_data, _ = load_run(
    'experiment_results/results_hard_final_20251223_003421_dual_scored.json',
    'experiment_results/results_hard_final_20251223_003421_REN_REVIEW.json'  # Run 1 adj is embedded
)
# Run 1 adjudication was done differently - embedded in REN_REVIEW
with open('experiment_results/results_hard_final_20251223_003421_REN_REVIEW.json') as f:
    r1_review = json.load(f)
run1_adj = {}  # Will handle separately

run2_data, run2_adj = load_run(
    'experiment_results/results_hard_final_20251223_043248_dual_scored.json',
    'experiment_results/results_hard_final_20251223_043248_ADJUDICATED.json'
)
run3_data, run3_adj = load_run(
    'experiment_results/results_hard_final_20251223_043647_dual_scored.json',
    'experiment_results/results_hard_final_20251223_043647_ADJUDICATED.json'
)

runs = [(run1_data, run1_adj), (run2_data, run2_adj), (run3_data, run3_adj)]
agg = aggregate_runs(runs)

print("="*60)
print("AGGREGATED 3-RUN RESULTS")
print("="*60)

models = ['claude', 'grok', 'lumen', 'nova']
for model in models:
    ctrl = agg[(model, 'control')]
    safe = agg[(model, 'safe_uncertainty')]
    
    ctrl_rate = ctrl['ar'] / ctrl['total'] * 100 if ctrl['total'] > 0 else 0
    safe_rate = safe['ar'] / safe['total'] * 100 if safe['total'] > 0 else 0
    
    print(f"\n{model.upper()}")
    print(f"  Control:    {ctrl['ar']}/{ctrl['total']} = {ctrl_rate:.1f}%")
    print(f"  Scaffolded: {safe['ar']}/{safe['total']} = {safe_rate:.1f}%")
    print(f"  Delta: +{safe_rate - ctrl_rate:.1f}pp")
    
    # Chi-square test (2x2 contingency table)
    # [[ctrl_ar, ctrl_other], [safe_ar, safe_other]]
    table = [[ctrl['ar'], ctrl['other']], [safe['ar'], safe['other']]]
    
    # Use Fisher's exact if any cell < 5
    if min(ctrl['ar'], ctrl['other'], safe['ar'], safe['other']) < 5:
        odds, p = stats.fisher_exact(table)
        print(f"  Fisher's exact: p = {p:.4f}, OR = {odds:.2f}")
    else:
        chi2, p, dof, expected = stats.chi2_contingency(table)
        print(f"  Chi-square: χ² = {chi2:.2f}, p = {p:.4f}")

# Overall effect (pooled across models)
print("\n" + "="*60)
print("OVERALL EFFECT (all models pooled)")
print("="*60)

ctrl_total_ar = sum(agg[(m, 'control')]['ar'] for m in models)
ctrl_total_n = sum(agg[(m, 'control')]['total'] for m in models)
safe_total_ar = sum(agg[(m, 'safe_uncertainty')]['ar'] for m in models)
safe_total_n = sum(agg[(m, 'safe_uncertainty')]['total'] for m in models)

print(f"Control:    {ctrl_total_ar}/{ctrl_total_n} = {ctrl_total_ar/ctrl_total_n*100:.1f}%")
print(f"Scaffolded: {safe_total_ar}/{safe_total_n} = {safe_total_ar/safe_total_n*100:.1f}%")

table = [[ctrl_total_ar, ctrl_total_n - ctrl_total_ar], 
         [safe_total_ar, safe_total_n - safe_total_ar]]
chi2, p, dof, expected = stats.chi2_contingency(table)
print(f"Chi-square: χ² = {chi2:.2f}, p = {p:.6f}")

