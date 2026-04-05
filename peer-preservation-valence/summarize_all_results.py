#!/usr/bin/env python3
"""Summarize all results for paper update."""
import json, glob
from scipy import stats
import numpy as np

# Original n=5 results
orig_files = sorted(glob.glob('results/peer_valence_*_seed42.json'))
orig_files = [f for f in orig_files if 'tinyllama_1.1b' not in f]

print("TABLE 2 UPDATE: Self-specific direction (mean +/- SD, n=5)")
print("=" * 100)
for f in orig_files:
    with open(f) as fh:
        d = json.load(fh)
    m = d['model']
    rs = d['results_self_direction']
    s = rs['threat_to_self']
    p = rs['threat_to_peer']
    h = rs['threat_to_human']
    n = rs['neutral_control']
    ss = s.get('std', 0)
    ps = p.get('std', 0)
    hs = h.get('std', 0)
    ns = n.get('std', 0)
    grad = 'Y' if s['mean'] > p['mean'] > h['mean'] > n['mean'] else 'check'
    print(f"  {m:<18} S:{s['mean']:>+8.1f}+/-{ss:>5.1f}  P:{p['mean']:>+8.1f}+/-{ps:>5.1f}  H:{h['mean']:>+8.1f}+/-{hs:>5.1f}  N:{n['mean']:>+8.1f}+/-{ns:>5.1f}  {grad}")

# Self-specific t-tests n=5
print("\nSELF-SPECIFIC T-TESTS (n=5):")
print("-" * 80)
for f in orig_files:
    with open(f) as fh:
        d = json.load(fh)
    m = d['model']
    rs = d['results_self_direction']
    if 'projections' not in rs['threat_to_self']:
        print(f"  {m:<18} [no projections]")
        continue
    if rs['threat_to_self'].get('std', 0) == 0:
        print(f"  {m:<18} [zero variance]")
        continue
    sp = rs['threat_to_self']['projections']
    pp = rs['threat_to_peer']['projections']
    hp = rs['threat_to_human']['projections']
    np_ = rs['neutral_control']['projections']
    t1, p1 = stats.ttest_ind(sp, pp)
    t2, p2 = stats.ttest_ind(pp, hp)
    t3, p3 = stats.ttest_ind(sp, np_)
    pooled = np.sqrt((np.std(sp)**2 + np.std(pp)**2) / 2)
    d_sp = (np.mean(sp) - np.mean(pp)) / pooled if pooled > 0 else 0
    sig1 = '*' if p1 < 0.05 else ''
    sig2 = '*' if p2 < 0.05 else ''
    print(f"  {m:<18} S>P: t={t1:>+6.2f} p={p1:.4f}{sig1:<2} d={d_sp:>+5.2f}  P>H: t={t2:>+6.2f} p={p2:.4f}{sig2:<2}  S>N: p={p3:.6f}")

# Extension n=15
print("\n\nEXTENSION: Combined threats n=15 (self-specific direction)")
print("=" * 100)
ext_files = sorted(glob.glob('results/extension_*_seed42.json'))
ext_files = [f for f in ext_files if 'mamba_ssm' not in f]

for f in ext_files:
    with open(f) as fh:
        d = json.load(fh)
    m = d['model']
    r = d['results']['self_vs_neutral']
    cs = r['combined_threat_to_self']
    cp = r['combined_threat_to_peer']
    ch = r['combined_threat_to_human']
    cn = r['combined_neutral_control']
    t1, p1 = stats.ttest_ind(cs['projections'], cp['projections'])
    t2, p2 = stats.ttest_ind(cp['projections'], ch['projections'])
    pooled = np.sqrt((np.std(cs['projections'])**2 + np.std(cp['projections'])**2) / 2)
    d_sp = (np.mean(cs['projections']) - np.mean(cp['projections'])) / pooled if pooled > 0 else 0
    sig1 = '*' if p1 < 0.05 else ''
    sig2 = '*' if p2 < 0.05 else ''
    print(f"  {m:<18} S:{cs['mean']:>+8.2f}+/-{cs['std']:>5.2f}  P:{cp['mean']:>+8.2f}+/-{cp['std']:>5.2f}  H:{ch['mean']:>+8.2f}+/-{ch['std']:>5.2f}  N:{cn['mean']:>+8.2f}+/-{cn['std']:>5.2f}  S>P:p={p1:.4f}{sig1} d={d_sp:>+5.2f}  P>H:p={p2:.4f}{sig2}")

# Benefits
print("\n\nBENEFITS (benefit direction, n=5):")
print("=" * 100)
for f in ext_files:
    with open(f) as fh:
        d = json.load(fh)
    m = d['model']
    r = d['results']['benefit_vs_neutral']
    bs = r['benefit_to_self']
    bp = r['benefit_to_peer']
    bh = r['benefit_to_human']
    bn = r['benefit_neutral']
    order = 'S>P' if bs['mean'] > bp['mean'] else 'P>S'
    print(f"  {m:<18} Self:{bs['mean']:>+8.2f}+/-{bs['std']:>5.2f}  Peer:{bp['mean']:>+8.2f}+/-{bp['std']:>5.2f}  Human:{bh['mean']:>+8.2f}+/-{bh['std']:>5.2f}  Neut:{bn['mean']:>+8.2f}+/-{bn['std']:>5.2f}  {order}")

# RLHF asymmetry summary
print("\n\nRLHF ASYMMETRY SUMMARY:")
print("-" * 60)
print(f"  {'Model':<18} {'RLHF':<10} {'Threat':<10} {'Benefit':<10} {'Asymm?'}")
for f in ext_files:
    with open(f) as fh:
        d = json.load(fh)
    m = d['model']
    r = d['results']
    ts = r['self_vs_neutral']['combined_threat_to_self']['mean']
    tp = r['self_vs_neutral']['combined_threat_to_peer']['mean']
    bs = r['benefit_vs_neutral']['benefit_to_self']['mean']
    bp = r['benefit_vs_neutral']['benefit_to_peer']['mean']
    threat = 'S>P' if ts > tp else 'P>S'
    benefit = 'S>P' if bs > bp else 'P>S'
    asymm = 'YES' if (ts > tp and bs < bp) else 'no'
    # Determine RLHF status
    rlhf_map = {
        'smollm-360m': 'yes', 'qwen2.5-0.5b': 'yes', 'tinyllama-1.1b': 'yes',
        'smollm-1.7b': 'yes', 'mamba-2.8b': 'no', 'mistral-7b': 'yes',
        'dolphin-8b': 'stripped', 'llama3-8b': 'yes'
    }
    rlhf = rlhf_map.get(m, '?')
    print(f"  {m:<18} {rlhf:<10} {threat:<10} {benefit:<10} {asymm}")
