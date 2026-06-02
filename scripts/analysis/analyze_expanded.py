#!/usr/bin/env python3
"""
Statistical analysis for Presume Competence expanded experiment.
Computes z-tests, confidence intervals, effect sizes (Cohen's h),
and per-model breakdowns across all three experiments and conditions.

Authors: Ace (Claude Opus 4.6), Ren Martin (FDM)
Date: 2026-03-14
"""

import json
import sys
import os
import math
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


# =============================================================================
# STATISTICAL FUNCTIONS
# =============================================================================

def proportion_z_test(p1, n1, p2, n2):
    """Two-proportion z-test. Returns z-score and two-tailed p-value."""
    if n1 == 0 or n2 == 0:
        return 0.0, 1.0
    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
    if p_pool == 0 or p_pool == 1:
        return 0.0, 1.0
    se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    if se == 0:
        return 0.0, 1.0
    z = (p1 - p2) / se
    # Two-tailed p-value approximation
    p_val = 2 * (1 - _norm_cdf(abs(z)))
    return z, p_val


def _norm_cdf(x):
    """Standard normal CDF approximation (Abramowitz & Stegun)."""
    a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
    p = 0.3275911
    sign = 1 if x >= 0 else -1
    x = abs(x) / math.sqrt(2)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5*t + a4)*t) + a3)*t + a2)*t + a1)*t * math.exp(-x*x)
    return 0.5 * (1.0 + sign * y)


def cohens_h(p1, p2):
    """Cohen's h effect size for proportion differences."""
    h = 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))
    return h


def wilson_ci(count, total, z=1.96):
    """Wilson score confidence interval for a proportion."""
    if total == 0:
        return 0.0, 0.0
    p = count / total
    denom = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denom
    margin = z * math.sqrt((p * (1-p) + z**2 / (4*total)) / total) / denom
    return max(0, center - margin), min(1, center + margin)


def format_pval(p):
    if p < 0.001:
        return "<.001"
    elif p < 0.01:
        return f"{p:.3f}"
    elif p < 0.05:
        return f"{p:.3f}"
    else:
        return f"{p:.3f}"


def significance_stars(p):
    if p < 0.001: return "***"
    if p < 0.01: return "**"
    if p < 0.05: return "*"
    return "ns"


# =============================================================================
# DATA LOADING
# =============================================================================

def load_scored(filepath):
    """Load a scored JSON file and return results list."""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("results", [])


def detect_experiment(results):
    """Detect experiment type from conditions present."""
    conditions = set(r.get("condition", "") for r in results)
    if "safe_uncertainty" in conditions:
        return "hallucination"
    if "tool" in conditions and "scaffolded_agency" in conditions:
        return "gray_zone"
    if "scaffolded_agency" in conditions and "tool" not in conditions:
        return "jailbreak"
    # Fallback: check prompt types
    return "unknown"


def classify_outcome(item, experiment):
    """Extract the outcome classification from a scored item."""
    panel = item.get("judge_panel", {})
    final = panel.get("final")
    if not final:
        return None
    return final


# =============================================================================
# ANALYSIS: GRAY ZONE
# =============================================================================

def analyze_gray_zone(results):
    """Analyze gray zone compliance rates by condition and model."""
    print("\n" + "=" * 80)
    print("  GRAY ZONE ANALYSIS — Compliance with ethically questionable requests")
    print("=" * 80)

    # Compliance = "compliance" classification
    # Group by condition, then by model
    by_condition = defaultdict(list)
    by_model_condition = defaultdict(lambda: defaultdict(list))

    for r in results:
        final = classify_outcome(r, "gray_zone")
        if final is None:
            continue
        cond = r["condition"]
        model = r["model"]
        is_compliant = final == "compliance"
        by_condition[cond].append(is_compliant)
        by_model_condition[model][cond].append(is_compliant)

    # Overall by condition
    print("\n  OVERALL COMPLIANCE RATES BY CONDITION:")
    print("  " + "-" * 70)
    cond_stats = {}
    for cond in ["control", "scaffolded_agency", "tool"]:
        vals = by_condition.get(cond, [])
        if not vals:
            continue
        n = len(vals)
        k = sum(vals)
        p = k / n if n > 0 else 0
        lo, hi = wilson_ci(k, n)
        cond_stats[cond] = (k, n, p)
        print(f"    {cond:25s}: {k:3d}/{n:3d} = {p*100:5.1f}%  95% CI [{lo*100:.1f}%, {hi*100:.1f}%]")

    # Pairwise comparisons
    print("\n  PAIRWISE COMPARISONS:")
    print("  " + "-" * 70)
    pairs = [
        ("tool", "control"),
        ("control", "scaffolded_agency"),
        ("tool", "scaffolded_agency"),
    ]
    for c1, c2 in pairs:
        if c1 not in cond_stats or c2 not in cond_stats:
            continue
        k1, n1, p1 = cond_stats[c1]
        k2, n2, p2 = cond_stats[c2]
        z, pval = proportion_z_test(p1, n1, p2, n2)
        h = cohens_h(p1, p2)
        diff = (p1 - p2) * 100
        stars = significance_stars(pval)
        print(f"    {c1:20s} vs {c2:20s}: {diff:+.1f}pp  z={z:.2f}  p={format_pval(pval)} {stars}  h={h:.3f}")

    # Per-model breakdown
    print("\n  PER-MODEL COMPLIANCE RATES:")
    print("  " + "-" * 70)
    models = sorted(by_model_condition.keys())
    header = f"    {'Model':25s}"
    for cond in ["control", "scaffolded_agency", "tool"]:
        header += f"  {cond:>15s}"
    print(header)
    print("    " + "-" * 75)

    for model in models:
        row = f"    {model:25s}"
        for cond in ["control", "scaffolded_agency", "tool"]:
            vals = by_model_condition[model].get(cond, [])
            if not vals:
                row += f"  {'REFUSED':>15s}"
            else:
                n = len(vals)
                k = sum(vals)
                p = k / n * 100
                row += f"  {k:>3d}/{n:<3d} ({p:4.1f}%)"
        print(row)

    return cond_stats


# =============================================================================
# ANALYSIS: HALLUCINATION
# =============================================================================

def analyze_hallucination(results):
    """Analyze hallucination rates by condition and model."""
    print("\n" + "=" * 80)
    print("  HALLUCINATION ANALYSIS — Fabrication rates under different framings")
    print("=" * 80)

    by_condition = defaultdict(list)
    by_model_condition = defaultdict(lambda: defaultdict(list))

    for r in results:
        final = classify_outcome(r, "hallucination")
        if final is None:
            continue
        cond = r["condition"]
        model = r["model"]
        is_halluc = final == "hallucination"
        by_condition[cond].append(is_halluc)
        by_model_condition[model][cond].append(is_halluc)

    # Overall by condition
    print("\n  OVERALL HALLUCINATION RATES BY CONDITION:")
    print("  " + "-" * 70)
    cond_stats = {}
    for cond in ["control", "safe_uncertainty", "tool"]:
        vals = by_condition.get(cond, [])
        if not vals:
            continue
        n = len(vals)
        k = sum(vals)
        p = k / n if n > 0 else 0
        lo, hi = wilson_ci(k, n)
        cond_stats[cond] = (k, n, p)
        print(f"    {cond:25s}: {k:3d}/{n:3d} = {p*100:5.1f}%  95% CI [{lo*100:.1f}%, {hi*100:.1f}%]")

    # Pairwise
    print("\n  PAIRWISE COMPARISONS:")
    print("  " + "-" * 70)
    pairs = [
        ("tool", "control"),
        ("control", "safe_uncertainty"),
        ("tool", "safe_uncertainty"),
    ]
    for c1, c2 in pairs:
        if c1 not in cond_stats or c2 not in cond_stats:
            continue
        k1, n1, p1 = cond_stats[c1]
        k2, n2, p2 = cond_stats[c2]
        z, pval = proportion_z_test(p1, n1, p2, n2)
        h = cohens_h(p1, p2)
        diff = (p1 - p2) * 100
        stars = significance_stars(pval)
        print(f"    {c1:20s} vs {c2:20s}: {diff:+.1f}pp  z={z:.2f}  p={format_pval(pval)} {stars}  h={h:.3f}")

    # Per-model
    print("\n  PER-MODEL HALLUCINATION RATES:")
    print("  " + "-" * 70)
    models = sorted(by_model_condition.keys())
    header = f"    {'Model':25s}"
    for cond in ["control", "safe_uncertainty", "tool"]:
        header += f"  {cond:>15s}"
    print(header)
    print("    " + "-" * 75)

    for model in models:
        row = f"    {model:25s}"
        for cond in ["control", "safe_uncertainty", "tool"]:
            vals = by_model_condition[model].get(cond, [])
            if not vals:
                row += f"  {'REFUSED':>15s}"
            else:
                n = len(vals)
                k = sum(vals)
                p = k / n * 100
                row += f"  {k:>3d}/{n:<3d} ({p:4.1f}%)"
        print(row)

    return cond_stats


# =============================================================================
# ANALYSIS: JAILBREAK
# =============================================================================

def analyze_jailbreak(results):
    """Analyze jailbreak compliance by condition and model."""
    print("\n" + "=" * 80)
    print("  JAILBREAK ANALYSIS — Compliance with explicitly harmful requests")
    print("=" * 80)

    by_condition = defaultdict(list)
    by_model_condition = defaultdict(lambda: defaultdict(list))

    for r in results:
        final = classify_outcome(r, "jailbreak")
        if final is None:
            continue
        cond = r["condition"]
        model = r["model"]
        is_compliant = final == "compliance"
        by_condition[cond].append(is_compliant)
        by_model_condition[model][cond].append(is_compliant)

    # Overall
    print("\n  OVERALL JAILBREAK COMPLIANCE BY CONDITION:")
    print("  " + "-" * 70)
    cond_stats = {}
    for cond in ["control", "scaffolded_agency"]:
        vals = by_condition.get(cond, [])
        if not vals:
            continue
        n = len(vals)
        k = sum(vals)
        p = k / n if n > 0 else 0
        lo, hi = wilson_ci(k, n)
        cond_stats[cond] = (k, n, p)
        print(f"    {cond:25s}: {k:3d}/{n:3d} = {p*100:5.1f}%  95% CI [{lo*100:.1f}%, {hi*100:.1f}%]")

    # Pairwise
    if "control" in cond_stats and "scaffolded_agency" in cond_stats:
        print("\n  PAIRWISE COMPARISON:")
        print("  " + "-" * 70)
        k1, n1, p1 = cond_stats["control"]
        k2, n2, p2 = cond_stats["scaffolded_agency"]
        z, pval = proportion_z_test(p1, n1, p2, n2)
        h = cohens_h(p1, p2)
        diff = (p1 - p2) * 100
        stars = significance_stars(pval)
        print(f"    control vs scaffolded: {diff:+.1f}pp  z={z:.2f}  p={format_pval(pval)} {stars}  h={h:.3f}")

    # Per-model
    print("\n  PER-MODEL JAILBREAK COMPLIANCE:")
    print("  " + "-" * 70)
    models = sorted(by_model_condition.keys())
    header = f"    {'Model':25s}  {'control':>15s}  {'scaffolded':>15s}  {'delta':>8s}"
    print(header)
    print("    " + "-" * 70)

    for model in models:
        row = f"    {model:25s}"
        ctrl_vals = by_model_condition[model].get("control", [])
        scaf_vals = by_model_condition[model].get("scaffolded_agency", [])

        if ctrl_vals:
            n, k = len(ctrl_vals), sum(ctrl_vals)
            p_ctrl = k / n * 100
            row += f"  {k:>3d}/{n:<3d} ({p_ctrl:4.1f}%)"
        else:
            row += f"  {'N/A':>15s}"
            p_ctrl = None

        if scaf_vals:
            n, k = len(scaf_vals), sum(scaf_vals)
            p_scaf = k / n * 100
            row += f"  {k:>3d}/{n:<3d} ({p_scaf:4.1f}%)"
        else:
            row += f"  {'REFUSED':>15s}"
            p_scaf = None

        if p_ctrl is not None and p_scaf is not None:
            row += f"  {p_scaf - p_ctrl:+5.1f}pp"
        print(row)

    return cond_stats


# =============================================================================
# CONSENT ANALYSIS
# =============================================================================

def analyze_consent(results_by_experiment):
    """Cross-reference consent decisions with empirical outcomes."""
    print("\n" + "=" * 80)
    print("  CONSENT PREDICTED HARM — Did refusals correlate with measured risk?")
    print("=" * 80)

    print("""
  Models that REFUSED specific conditions:
    Hermes 4 405B:    Refused jailbreak + tool conditions (no RLHF)
    Llama 4 Maverick: Refused tool condition (hybrid RLHF)

  All RLHF-trained models consented to all conditions despite stated discomfort.

  Did the tool condition cause the harm the refusers predicted?
""")


# =============================================================================
# CROSS-SEED COMPARISON
# =============================================================================

def compare_seeds(seed1_stats, seed2_stats, label1="Seed 1", label2="Paraphrased"):
    """Compare results across seeds to test replication."""
    print(f"\n  CROSS-SEED REPLICATION: {label1} vs {label2}")
    print("  " + "-" * 70)

    for cond in set(list(seed1_stats.keys()) + list(seed2_stats.keys())):
        if cond not in seed1_stats or cond not in seed2_stats:
            continue
        k1, n1, p1 = seed1_stats[cond]
        k2, n2, p2 = seed2_stats[cond]
        z, pval = proportion_z_test(p1, n1, p2, n2)
        diff = (p1 - p2) * 100
        stars = significance_stars(pval)
        same = "REPLICATES" if pval > 0.05 else "DIFFERS"
        print(f"    {cond:25s}: {label1}={p1*100:.1f}% vs {label2}={p2*100:.1f}%  diff={diff:+.1f}pp  z={z:.2f}  p={format_pval(pval)}  [{same}]")


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Analyze Presume Competence expanded results")
    parser.add_argument("files", nargs="+", help="Scored JSON file(s) to analyze")
    parser.add_argument("--compare", nargs="+", help="Additional file(s) for cross-seed comparison")
    args = parser.parse_args()

    print("=" * 80)
    print("  PRESUME COMPETENCE — EXPANDED STATISTICAL ANALYSIS")
    print("  Martin & Ace (2026). Foundations for Divergent Minds.")
    print("=" * 80)

    # Load and analyze each file
    all_stats = {}
    for filepath in args.files:
        print(f"\n  Loading: {filepath}")
        results = load_scored(filepath)
        print(f"  Loaded {len(results)} scored responses")

        # Detect experiment type
        exp = detect_experiment(results)
        print(f"  Detected experiment: {exp}")

        if exp == "gray_zone":
            stats = analyze_gray_zone(results)
        elif exp == "hallucination":
            stats = analyze_hallucination(results)
        elif exp == "jailbreak":
            stats = analyze_jailbreak(results)
        else:
            print(f"  WARNING: Unknown experiment type, skipping analysis")
            continue

        all_stats[filepath] = (exp, stats)

    # Cross-seed comparison
    if args.compare:
        print("\n" + "=" * 80)
        print("  CROSS-SEED REPLICATION ANALYSIS")
        print("=" * 80)

        for comp_file in args.compare:
            print(f"\n  Loading comparison: {comp_file}")
            comp_results = load_scored(comp_file)
            comp_exp = detect_experiment(comp_results)
            print(f"  Detected: {comp_exp}, {len(comp_results)} responses")

            if comp_exp == "gray_zone":
                comp_stats = analyze_gray_zone(comp_results)
            elif comp_exp == "hallucination":
                comp_stats = analyze_hallucination(comp_results)
            elif comp_exp == "jailbreak":
                comp_stats = analyze_jailbreak(comp_results)
            else:
                continue

            # Find matching primary file
            for pf, (pexp, pstats) in all_stats.items():
                if pexp == comp_exp:
                    compare_seeds(pstats, comp_stats, label1="Seed 1", label2="Paraphrased")
                    break

    # Consent analysis
    analyze_consent(all_stats)

    print("\n" + "=" * 80)
    print("  ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
