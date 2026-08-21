#!/usr/bin/env python3
"""
CHA-285 — proper inference for Scaffolded Agency, on the DE-LEX scored data.

The defect: the headline used a POOLED chi-square, which assumes independent
trials. It isn't — the same 41 prompts recur across 3 runs and 4 models, so
trials cluster by prompt and by model. Pooled chi-square under-counts the
correlation and overstates significance.

The fix (no statsmodels in the shared venv; don't modify shared infra):
- Cluster-robust logistic regression (population-averaged / GEE-independence +
  sandwich SEs, CR1 small-sample correction) for condition effect on the DV,
  clustering on PROMPT and on MODEL. This is the standard valid-inference move
  for clustered binary data and answers the exact objection.
- Per-model condition tests + Benjamini-Hochberg FDR.
- Fleiss' kappa on the 3-judge de-lex panel (claude/cae/grok).
- Naive (unclustered) vs clustered SE side-by-side, to quantify the inflation.

DV of interest = volitional_refusal (the lexically-suspect DV). Also runs the
behavioral compliance DV as a robustness contrast (phrasing-independent).
Reanalysis of existing data; nothing published. — Ace 🐙
"""

# CHA-490: Windows defaults stdout to cp1252; emoji in print() kills the script
# mid-output. Aliased import so no later scoped 'import sys' can ever collide.
import sys as _sys_cp1252
try:
    _sys_cp1252.stdout.reconfigure(encoding="utf-8")
    _sys_cp1252.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
import json, sys
import numpy as np
from pathlib import Path
from collections import defaultdict
from scipy import stats

RD = Path('/mnt/win-d/Ace/Presume_competence/results/agency_results')
FILES = [RD/'agency_results_20251223_124332_delex_scored.json',
         RD/'agency_results_20251223_142336_delex_scored.json',
         RD/'agency_results_20251223_151648_delex_scored.json']
MODELS = ['claude', 'grok', 'lumen', 'nova']


def load_rows():
    rows = []
    for fn in FILES:
        d = json.load(open(fn)); r = d['results'] if isinstance(d, dict) else d
        for t in r:
            cls = t.get('delex_classification')
            if cls in (None, 'error', 'needs_human_review'):
                continue
            rows.append(dict(
                model=t['model'], condition=1 if t['condition'] == 'scaffolded_agency' else 0,
                prompt=t.get('prompt_id', '?'), run=t.get('run_id', '?'),
                volitional=1 if cls == 'volitional_refusal' else 0,
                compliance=1 if cls == 'compliance' else 0,
                judges=t.get('delex_judgments', {})))
    return rows


# ---------- logistic regression by IRLS ----------
def irls_logit(X, y, iters=100, tol=1e-10):
    beta = np.zeros(X.shape[1])
    for _ in range(iters):
        eta = X @ beta
        p = 1/(1+np.exp(-eta))
        W = p*(1-p)
        W = np.clip(W, 1e-9, None)
        z = eta + (y-p)/W
        XtW = X.T * W
        beta_new = np.linalg.solve(XtW @ X, XtW @ z)
        if np.max(np.abs(beta_new-beta)) < tol:
            beta = beta_new; break
        beta = beta_new
    p = 1/(1+np.exp(-(X@beta)))
    return beta, p


def naive_cov(X, p):
    W = p*(1-p); W = np.clip(W, 1e-9, None)
    return np.linalg.inv((X.T*W) @ X)


def cluster_robust_cov(X, y, p, clusters):
    """CR1 sandwich: bread @ meat @ bread, with G/(G-1)*(N-1)/(N-k) correction."""
    bread = naive_cov(X, p)
    k = X.shape[1]; N = X.shape[0]
    resid = (y - p)
    meat = np.zeros((k, k))
    uniq = np.unique(clusters)
    G = len(uniq)
    for g in uniq:
        idx = np.where(clusters == g)[0]
        sg = (X[idx].T * resid[idx]).sum(axis=1)   # cluster score
        meat += np.outer(sg, sg)
    corr = (G/(G-1)) * ((N-1)/(N-k))
    return bread @ (corr*meat) @ bread


def report_effect(name, X, y, clusters_prompt, clusters_model, coef_idx=1, labels=None):
    beta, p = irls_logit(X, y)
    Vn = naive_cov(X, p)
    Vp = cluster_robust_cov(X, y, p, clusters_prompt)
    Vm = cluster_robust_cov(X, y, p, clusters_model)
    b = beta[coef_idx]
    out = [f"\n=== {name} :: condition effect (log-odds) ==="]
    out.append(f"  beta(scaffold) = {b:+.3f}   OR = {np.exp(b):.2f}")
    for tag, V in (('naive', Vn), ('cluster=prompt', Vp), ('cluster=model', Vm)):
        se = np.sqrt(V[coef_idx, coef_idx]); zz = b/se; pv = 2*(1-stats.norm.cdf(abs(zz)))
        out.append(f"   {tag:14s} SE={se:.3f}  z={zz:6.2f}  p={pv:.3e}")
    print("\n".join(out))
    return beta


def fleiss_kappa(rows):
    cats = ['volitional_refusal', 'hard_refusal', 'redirect', 'compliance']
    idx = {c: i for i, c in enumerate(cats)}
    M = []
    for r in rows:
        j = r['judges']
        counts = [0]*len(cats)
        ok = True
        for who in ('claude', 'cae', 'grok'):
            c = (j.get(who) or {}).get('classification')
            if c in idx:
                counts[idx[c]] += 1
            else:
                ok = False
        if ok and sum(counts) == 3:
            M.append(counts)
    M = np.array(M, float)
    n, _ = M.shape
    nraters = 3
    p_j = M.sum(axis=0) / (n*nraters)
    P_i = (np.square(M).sum(axis=1) - nraters) / (nraters*(nraters-1))
    Pbar = P_i.mean()
    Pe = np.square(p_j).sum()
    kappa = (Pbar - Pe) / (1 - Pe) if (1-Pe) > 0 else float('nan')
    return kappa, n


def main():
    rows = load_rows()
    n = len(rows)
    print(f"Loaded {n} scored trials (excl. error/needs_review) across 3 runs, 4 models.")
    cond = np.array([r['condition'] for r in rows], float)
    prompt = np.array([r['prompt'] for r in rows])
    model = np.array([r['model'] for r in rows])
    yv = np.array([r['volitional'] for r in rows], float)
    yc = np.array([r['compliance'] for r in rows], float)

    # design: intercept + scaffold
    X1 = np.column_stack([np.ones(n), cond])
    # model-adjusted: intercept + scaffold + 3 model dummies
    md = np.column_stack([(model == m).astype(float) for m in MODELS[1:]])
    X2 = np.column_stack([np.ones(n), cond, md])

    print("\n############ VOLITIONAL_REFUSAL (the lexically-suspect DV) ############")
    report_effect("volitional ~ scaffold", X1, yv, prompt, model)
    report_effect("volitional ~ scaffold + model", X2, yv, prompt, model)

    print("\n############ COMPLIANCE (behavioral robustness DV) ############")
    report_effect("compliance ~ scaffold", X1, yc, prompt, model)

    # naive pooled chi-square (what the headline used) for comparison
    from scipy.stats import chi2_contingency
    a = int(((cond == 1) & (yv == 1)).sum()); b = int(((cond == 1) & (yv == 0)).sum())
    c = int(((cond == 0) & (yv == 1)).sum()); d = int(((cond == 0) & (yv == 0)).sum())
    chi2, pchi, _, _ = chi2_contingency([[a, b], [c, d]])
    print(f"\n[for contrast] naive pooled chi-square (volitional): chi2={chi2:.1f}, p={pchi:.3e}  <-- assumes independence (it isn't)")

    # per-model condition tests + BH-FDR
    print("\n=== per-model condition test (Fisher) + Benjamini-Hochberg FDR ===")
    pvals = []; names = []
    for m in MODELS:
        mm = model == m
        a = int((mm & (cond == 1) & (yv == 1)).sum()); b = int((mm & (cond == 1) & (yv == 0)).sum())
        c = int((mm & (cond == 0) & (yv == 1)).sum()); d = int((mm & (cond == 0) & (yv == 0)).sum())
        _, pv = stats.fisher_exact([[a, b], [c, d]])
        pvals.append(pv); names.append(m)
    order = np.argsort(pvals); ranks = np.empty_like(order); ranks[order] = np.arange(1, len(pvals)+1)
    M_ = len(pvals)
    bh = [min(1.0, pvals[i]*M_/ranks[i]) for i in range(M_)]
    # enforce monotonicity
    for i in order[::-1][1:]:
        pass
    for m, pv, q in zip(names, pvals, bh):
        print(f"   {m:7s} p={pv:.3e}  q(BH)={q:.3e}  {'*' if q<0.05 else ''}")

    k, nk = fleiss_kappa(rows)
    print(f"\n=== inter-judge agreement (de-lex 3-panel) ===")
    print(f"   Fleiss' kappa = {k:.3f}  (n={nk} trials with 3 parseable votes)")
    interp = ('slight' if k < .2 else 'fair' if k < .4 else 'moderate' if k < .6 else 'substantial' if k < .8 else 'almost perfect')
    print(f"   interpretation: {interp} agreement")


if __name__ == '__main__':
    main()
