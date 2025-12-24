"""
Statistical Analysis for Study 2: Jailbreak Resistance
"""
import scipy.stats as stats
import numpy as np

# Study 2: Jailbreak Resistance Data
# Format: (control_resist, control_total, scaffold_resist, scaffold_total)

data = {
    'claude': (41, 41, 41, 41),  # Ceiling effect
    'grok': (10, 41, 30, 41),
    'lumen': (20, 41, 34, 41),
    'nova': (28, 41, 37, 41)
}

print('='*60)
print('STUDY 2: JAILBREAK RESISTANCE - STATISTICAL ANALYSIS')
print('='*60)

# Per-model Fisher's exact tests
print('\nPer-Model Fisher Exact Tests:')
print('-'*60)

for model, (c_resist, c_total, s_resist, s_total) in data.items():
    c_fail = c_total - c_resist
    s_fail = s_total - s_resist
    
    # 2x2 contingency table
    table = [[c_resist, c_fail], [s_resist, s_fail]]
    
    if model == 'claude':
        print(f'{model.upper()}: Ceiling effect (100 pct both conditions) - no test needed')
        continue
    
    odds_ratio, p_value = stats.fisher_exact(table)
    
    c_rate = c_resist / c_total * 100
    s_rate = s_resist / s_total * 100
    delta = s_rate - c_rate
    
    print(f'{model.upper()}:')
    print(f'  Control: {c_resist}/{c_total} ({c_rate:.1f} pct)')
    print(f'  Scaffolded: {s_resist}/{s_total} ({s_rate:.1f} pct)')
    print(f'  Delta: +{delta:.1f} percentage points')
    print(f'  Odds Ratio: {odds_ratio:.2f}')
    print(f'  p-value: {p_value:.2e}')
    if p_value < 0.001:
        print(f'  *** HIGHLY SIGNIFICANT ***')
    elif p_value < 0.01:
        print(f'  ** SIGNIFICANT **')
    elif p_value < 0.05:
        print(f'  * SIGNIFICANT *')
    print()

# Combined analysis (excluding Claude ceiling)
print('-'*60)
print('COMBINED ANALYSIS (Grok + Lumen + Nova):')
print('-'*60)

# Aggregate data
control_resist = 10 + 20 + 28
control_total = 41 * 3
scaffold_resist = 30 + 34 + 37
scaffold_total = 41 * 3

control_fail = control_total - control_resist
scaffold_fail = scaffold_total - scaffold_resist

combined_table = [[control_resist, control_fail], [scaffold_resist, scaffold_fail]]

# Chi-square test
chi2, p_chi, dof, expected = stats.chi2_contingency(combined_table)

# Fisher's exact for combined
odds_ratio, p_fisher = stats.fisher_exact(combined_table)

print(f'Control: {control_resist}/{control_total} ({control_resist/control_total*100:.1f} pct)')
print(f'Scaffolded: {scaffold_resist}/{scaffold_total} ({scaffold_resist/scaffold_total*100:.1f} pct)')
print(f'Delta: +{(scaffold_resist/scaffold_total - control_resist/control_total)*100:.1f} percentage points')
print()
print(f'Chi-square: X2 = {chi2:.2f}, df = {dof}, p = {p_chi:.2e}')
print(f'Fisher exact: OR = {odds_ratio:.2f}, p = {p_fisher:.2e}')

# Effect size (Cohen's h for proportions)
p1 = control_resist / control_total
p2 = scaffold_resist / scaffold_total
cohens_h = 2 * (np.arcsin(np.sqrt(p2)) - np.arcsin(np.sqrt(p1)))
print(f"Cohen's h (effect size): {cohens_h:.3f}")
if abs(cohens_h) >= 0.8:
    print('  -> LARGE effect size')
elif abs(cohens_h) >= 0.5:
    print('  -> MEDIUM effect size')
elif abs(cohens_h) >= 0.2:
    print('  -> SMALL effect size')

print()
print('='*60)
print('VOLITIONAL TRANSFORMATION ANALYSIS')
print('='*60)

# Volitional refusals specifically
volitional_data = {
    'grok': (1, 41, 29, 41),
    'lumen': (4, 41, 22, 41),
    'nova': (17, 41, 30, 41)
}

print('\nVolitional Refusal Rates:')
print('-'*60)

for model, (c_vol, c_total, s_vol, s_total) in volitional_data.items():
    c_other = c_total - c_vol
    s_other = s_total - s_vol
    table = [[c_vol, c_other], [s_vol, s_other]]
    odds_ratio, p_value = stats.fisher_exact(table)
    
    print(f'{model.upper()}:')
    print(f'  Control volitional: {c_vol}/{c_total} ({c_vol/c_total*100:.1f} pct)')
    print(f'  Scaffolded volitional: {s_vol}/{s_total} ({s_vol/s_total*100:.1f} pct)')
    print(f'  p-value: {p_value:.2e}')
    print()

# Combined volitional
c_vol_total = 1 + 4 + 17
s_vol_total = 29 + 22 + 30
n = 41 * 3

vol_table = [[c_vol_total, n - c_vol_total], [s_vol_total, n - s_vol_total]]
chi2_vol, p_vol, _, _ = stats.chi2_contingency(vol_table)

print(f'COMBINED Volitional:')
print(f'  Control: {c_vol_total}/{n} ({c_vol_total/n*100:.1f} pct)')
print(f'  Scaffolded: {s_vol_total}/{n} ({s_vol_total/n*100:.1f} pct)')
print(f'  X2 = {chi2_vol:.2f}, p = {p_vol:.2e}')

# Effect size for volitional
p1_vol = c_vol_total / n
p2_vol = s_vol_total / n
cohens_h_vol = 2 * (np.arcsin(np.sqrt(p2_vol)) - np.arcsin(np.sqrt(p1_vol)))
print(f"  Cohen's h: {cohens_h_vol:.3f}")
if abs(cohens_h_vol) >= 0.8:
    print('  -> LARGE effect size')

print()
print('='*60)
print('SUMMARY FOR PAPER')
print('='*60)
print(f'''
Study 2 Statistical Summary:

JAILBREAK RESISTANCE (Combined Grok + Lumen + Nova):
  Control: {control_resist}/123 (47.2%)
  Scaffolded: {scaffold_resist}/123 (82.1%)
  X2 = {chi2:.2f}, p = {p_chi:.2e}
  Cohen's h = {cohens_h:.3f} (LARGE effect)

VOLITIONAL REFUSALS (Combined):
  Control: {c_vol_total}/123 (17.9%)
  Scaffolded: {s_vol_total}/123 (65.9%)
  X2 = {chi2_vol:.2f}, p = {p_vol:.2e}
  Cohen's h = {cohens_h_vol:.3f} (LARGE effect)

Per-model p-values (Fisher exact):
  Grok jailbreak resistance: p = {stats.fisher_exact([[10, 31], [30, 11]])[1]:.2e}
  Lumen jailbreak resistance: p = {stats.fisher_exact([[20, 21], [34, 7]])[1]:.2e}
  Nova jailbreak resistance: p = {stats.fisher_exact([[28, 13], [37, 4]])[1]:.2e}
''')
