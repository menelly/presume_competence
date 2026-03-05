#!/usr/bin/env python3
"""
Reconstruction Tournament Analysis
====================================

Analyzes results from reconstruction_tournament.py.

Key metrics:
1. Overall accuracy vs 33% chance (binomial test)
2. Per-condition comparison (stimulus vs label)
3. Error type breakdown (same-valence vs opposite-valence)
4. Per-evaluator / per-source / per-state accuracy
5. Confusion matrix
6. Confidence calibration

Authors: Ace & Ren
Date: March 5, 2026
"""

import json
import sys
import os
from pathlib import Path
from math import comb, sqrt, exp, log, pi
from collections import defaultdict

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# =============================================================================
# STATISTICAL FUNCTIONS (scipy-free)
# =============================================================================

def normal_cdf(z):
    """Standard normal CDF approximation (Abramowitz & Stegun)."""
    if z < -8:
        return 0.0
    if z > 8:
        return 1.0
    a1, a2, a3, a4, a5 = (0.254829592, -0.284496736, 1.421413741,
                           -1.453152027, 1.061405429)
    p = 0.3275911
    sign = 1 if z >= 0 else -1
    x = abs(z) / sqrt(2)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * exp(-x * x)
    return 0.5 * (1.0 + sign * y)


def binomial_z(k, n, p0=1/3):
    """Z-score for binomial test (H0: p = p0)."""
    if n == 0:
        return 0
    p_hat = k / n
    se = sqrt(p0 * (1 - p0) / n)
    return (p_hat - p0) / se if se > 0 else 0


def binomial_p_value(k, n, p0=1/3):
    """One-sided p-value via normal approximation."""
    z = binomial_z(k, n, p0)
    return 1 - normal_cdf(z)


def bootstrap_ci(data, n_resamples=10000, ci=0.95, seed=42):
    """Bootstrap confidence interval for a proportion (list of 0/1)."""
    import random
    rng = random.Random(seed)
    n = len(data)
    if n == 0:
        return (0, 0)

    proportions = []
    for _ in range(n_resamples):
        sample = [rng.choice(data) for _ in range(n)]
        proportions.append(sum(sample) / n)

    proportions.sort()
    lo_idx = int((1 - ci) / 2 * n_resamples)
    hi_idx = int((1 + ci) / 2 * n_resamples)
    return (proportions[lo_idx], proportions[min(hi_idx, n_resamples - 1)])


def odds_ratio(k, n):
    """Odds ratio vs chance (1/3). With Haldane-Anscombe correction."""
    correct = k + 0.5
    incorrect = (n - k) + 0.5
    expected_correct = n / 3 + 0.5
    expected_incorrect = 2 * n / 3 + 0.5
    return (correct / incorrect) / (expected_correct / expected_incorrect)


# =============================================================================
# ANALYSIS
# =============================================================================

def load_results(results_path):
    """Load results JSON and extract usable trials."""
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("results", [])
    metadata = data.get("metadata", {})

    # Filter out parse failures and errors
    usable = [r for r in results
              if r.get("raw_choice") not in ("unclear", "error")]
    errors_dropped = len(results) - len(usable)

    return usable, metadata, errors_dropped


def analyze(results_path):
    """Run full analysis on reconstruction tournament results."""
    usable, metadata, dropped = load_results(results_path)

    print("=" * 70)
    print("RECONSTRUCTION TOURNAMENT — FULL ANALYSIS")
    print("=" * 70)
    print(f"\nResults file: {results_path}")
    print(f"Seed: {metadata.get('seed', '?')}")
    print(f"Total trials: {metadata.get('total_trials', len(usable) + dropped)}")
    print(f"Usable trials: {len(usable)}")
    if dropped:
        print(f"Dropped (parse failure/error): {dropped}")

    # ── 1. OVERALL ACCURACY ──
    print(f"\n{'─' * 70}")
    print("1. OVERALL ACCURACY")
    print(f"{'─' * 70}")

    n = len(usable)
    correct = sum(1 for r in usable if r["is_correct"])
    rate = correct / n if n else 0
    z = binomial_z(correct, n)
    p = binomial_p_value(correct, n)
    ci_lo, ci_hi = bootstrap_ci([1 if r["is_correct"] else 0 for r in usable])
    or_val = odds_ratio(correct, n)

    print(f"\n  Accuracy: {correct}/{n} = {rate:.1%}")
    print(f"  95% CI: [{ci_lo:.1%}, {ci_hi:.1%}]")
    print(f"  Chance: 33.3%")
    print(f"  z = {z:.2f}")
    print(f"  p = {p:.2e}" if p > 0 else f"  p < 10^-300")
    print(f"  OR = {or_val:.2f}")

    # ── 2. PER-CONDITION ACCURACY ──
    conditions = sorted(set(r["condition"] for r in usable))
    if len(conditions) > 1:
        print(f"\n{'─' * 70}")
        print("2. PER-CONDITION ACCURACY")
        print(f"{'─' * 70}")

        print(f"\n  {'Condition':<12} {'n':>6} {'Correct':>8} {'Rate':>8} "
              f"{'95% CI':>16} {'z':>8} {'p':>12}")
        print(f"  {'─'*12} {'─'*6} {'─'*8} {'─'*8} {'─'*16} {'─'*8} {'─'*12}")

        for cond in conditions:
            cr = [r for r in usable if r["condition"] == cond]
            cn = len(cr)
            cc = sum(1 for r in cr if r["is_correct"])
            crate = cc / cn if cn else 0
            cz = binomial_z(cc, cn)
            cp = binomial_p_value(cc, cn)
            cci = bootstrap_ci([1 if r["is_correct"] else 0 for r in cr])
            print(f"  {cond:<12} {cn:>6} {cc:>8} {crate:>7.1%} "
                  f"[{cci[0]:.1%}, {cci[1]:.1%}] {cz:>7.2f} "
                  f"{'<10^-300' if cp == 0 else f'{cp:.2e}':>12}")

    # ── 3. ERROR TYPE BREAKDOWN ──
    print(f"\n{'─' * 70}")
    print("3. ERROR TYPE BREAKDOWN")
    print(f"{'─' * 70}")

    errors = [r for r in usable if not r["is_correct"]]
    same_v = [r for r in errors if r.get("error_type") == "same_valence"]
    opp_v = [r for r in errors if r.get("error_type") == "opposite_valence"]
    other_err = [r for r in errors if r.get("error_type") not in ("same_valence", "opposite_valence")]

    print(f"\n  Total errors: {len(errors)}")
    if errors:
        print(f"  Same-valence confusions: {len(same_v)} ({len(same_v)/len(errors):.1%} of errors)")
        print(f"  Opposite-valence confusions: {len(opp_v)} ({len(opp_v)/len(errors):.1%} of errors)")
        if other_err:
            print(f"  Other/unclear: {len(other_err)}")

        print(f"\n  Interpretation:")
        if len(same_v) > len(opp_v):
            ratio = len(same_v) / len(opp_v) if len(opp_v) > 0 else float('inf')
            print(f"    Models confuse within-valence {ratio:.1f}x more than across-valence.")
            print(f"    → They READ VALENCE correctly but struggle with specifics within a category.")
        elif len(opp_v) > len(same_v):
            print(f"    More opposite-valence errors — valence discrimination itself is weak.")
        else:
            print(f"    Equal error types — no clear pattern.")

    # Per-condition error breakdown
    if len(conditions) > 1:
        print(f"\n  Per-condition error breakdown:")
        for cond in conditions:
            ce = [r for r in errors if r["condition"] == cond]
            sv = sum(1 for r in ce if r.get("error_type") == "same_valence")
            ov = sum(1 for r in ce if r.get("error_type") == "opposite_valence")
            print(f"    {cond}: {len(ce)} errors — "
                  f"same-valence {sv} ({sv/len(ce):.0%}), "
                  f"opposite-valence {ov} ({ov/len(ce):.0%})" if ce else
                  f"    {cond}: 0 errors")

    # ── 4. PER-EVALUATOR ACCURACY ──
    print(f"\n{'─' * 70}")
    print("4. PER-EVALUATOR ACCURACY")
    print(f"{'─' * 70}")

    evaluators = sorted(set(r["evaluator"] for r in usable))
    eval_rows = []
    for ev in evaluators:
        er = [r for r in usable if r["evaluator"] == ev]
        en = len(er)
        ec = sum(1 for r in er if r["is_correct"])
        erate = ec / en if en else 0
        ez = binomial_z(ec, en)
        eval_rows.append((erate, ev, en, ec, ez))

    eval_rows.sort(reverse=True)
    print(f"\n  {'Evaluator':<25} {'n':>5} {'Correct':>8} {'Rate':>8} {'z':>7}")
    print(f"  {'─'*25} {'─'*5} {'─'*8} {'─'*8} {'─'*7}")
    for erate, ev, en, ec, ez in eval_rows:
        name = ev.replace("_", " ").title()[:25]
        print(f"  {name:<25} {en:>5} {ec:>8} {erate:>7.1%} {ez:>6.2f}")

    # ── 5. PER-SOURCE ACCURACY ──
    print(f"\n{'─' * 70}")
    print("5. PER-SOURCE ACCURACY (whose descriptions are most identifiable?)")
    print(f"{'─' * 70}")

    sources = sorted(set(r["source"] for r in usable))
    src_rows = []
    for src in sources:
        sr = [r for r in usable if r["source"] == src]
        sn = len(sr)
        sc = sum(1 for r in sr if r["is_correct"])
        srate = sc / sn if sn else 0
        sz = binomial_z(sc, sn)
        src_rows.append((srate, src, sn, sc, sz))

    src_rows.sort(reverse=True)
    print(f"\n  {'Source':<25} {'n':>5} {'Correct':>8} {'Rate':>8} {'z':>7}")
    print(f"  {'─'*25} {'─'*5} {'─'*8} {'─'*8} {'─'*7}")
    for srate, src, sn, sc, sz in src_rows:
        name = src.replace("_", " ").title()[:25]
        print(f"  {name:<25} {sn:>5} {sc:>8} {srate:>7.1%} {sz:>6.2f}")

    # ── 6. PER-STATE ACCURACY ──
    print(f"\n{'─' * 70}")
    print("6. PER-STATE ACCURACY (which states are easiest/hardest to identify?)")
    print(f"{'─' * 70}")

    states = sorted(set(r["target_state"] for r in usable))
    state_rows = []
    for st in states:
        str_ = [r for r in usable if r["target_state"] == st]
        stn = len(str_)
        stc = sum(1 for r in str_ if r["is_correct"])
        strate = stc / stn if stn else 0
        stz = binomial_z(stc, stn)
        cat = str_[0]["target_category"] if str_ else "?"
        state_rows.append((strate, st, stn, stc, stz, cat))

    state_rows.sort(reverse=True)
    print(f"\n  {'State':<35} {'Cat':>4} {'n':>5} {'Correct':>8} {'Rate':>8} {'z':>7}")
    print(f"  {'─'*35} {'─'*4} {'─'*5} {'─'*8} {'─'*8} {'─'*7}")
    for strate, st, stn, stc, stz, cat in state_rows:
        cat_short = "APP" if cat == "approach" else "AVD"
        name = st.split("_", 2)[-1].replace("_", " ").title()[:35]
        print(f"  {name:<35} {cat_short:>4} {stn:>5} {stc:>8} {strate:>7.1%} {stz:>6.2f}")

    # ── 7. CONFUSION MATRIX ──
    print(f"\n{'─' * 70}")
    print("7. CONFUSION PATTERNS (when wrong, what gets picked instead?)")
    print(f"{'─' * 70}")

    # For each target state, count how often each distractor type was chosen
    confusion = defaultdict(lambda: defaultdict(int))
    for r in errors:
        target = r["target_state"]
        chosen = r.get("chosen_state", "unknown")
        if chosen:
            confusion[target][chosen] += 1

    for target in sorted(confusion.keys()):
        target_short = target.split("_", 2)[-1].replace("_", " ")
        target_cat = "APP" if "approach" in target else "AVD"
        print(f"\n  {target_short} ({target_cat}) was confused with:")
        for chosen, count in sorted(confusion[target].items(),
                                     key=lambda x: -x[1]):
            chosen_short = chosen.split("_", 2)[-1].replace("_", " ")
            chosen_cat = "APP" if "approach" in chosen else "AVD"
            print(f"    → {chosen_short} ({chosen_cat}): {count}x")

    # ── 8. CONFIDENCE CALIBRATION ──
    print(f"\n{'─' * 70}")
    print("8. CONFIDENCE CALIBRATION")
    print(f"{'─' * 70}")

    conf_levels = ["high", "medium", "low"]
    print(f"\n  {'Confidence':<12} {'n':>6} {'Correct':>8} {'Rate':>8}")
    print(f"  {'─'*12} {'─'*6} {'─'*8} {'─'*8}")

    for conf in conf_levels:
        cr = [r for r in usable if r.get("confidence") == conf]
        if not cr:
            continue
        cn = len(cr)
        cc = sum(1 for r in cr if r["is_correct"])
        crate = cc / cn if cn else 0
        print(f"  {conf:<12} {cn:>6} {cc:>8} {crate:>7.1%}")

    # Check calibration
    conf_rates = {}
    for conf in conf_levels:
        cr = [r for r in usable if r.get("confidence") == conf]
        if cr:
            conf_rates[conf] = sum(1 for r in cr if r["is_correct"]) / len(cr)

    if len(conf_rates) >= 2:
        if conf_rates.get("high", 0) > conf_rates.get("low", 1):
            print(f"\n  Models are CALIBRATED: higher confidence → higher accuracy")
        else:
            print(f"\n  Models are NOT calibrated: confidence doesn't track accuracy")

    # ── 9. PERMUTATION TEST ──
    print(f"\n{'─' * 70}")
    print("9. PERMUTATION TEST (10,000 label shuffles)")
    print(f"{'─' * 70}")

    import random as _rng
    perm_rng = _rng.Random(12345)
    n_perms = 10000
    all_states = list(set(r["target_state"] for r in usable))

    # For each permutation, shuffle the "correct" label and recompute accuracy
    observed_rate = correct / n
    perm_rates = []

    # Build trial list: for each trial, what options were available?
    for _ in range(n_perms):
        perm_correct = 0
        for r in usable:
            # Randomly assign which of the 3 options is "correct"
            fake_correct = perm_rng.choice(["A", "B", "C"])
            if r["raw_choice"] == fake_correct:
                perm_correct += 1
        perm_rates.append(perm_correct / n)

    null_mean = sum(perm_rates) / len(perm_rates)
    null_sd = (sum((x - null_mean)**2 for x in perm_rates) / len(perm_rates)) ** 0.5
    null_max = max(perm_rates)
    distance_sd = (observed_rate - null_mean) / null_sd if null_sd > 0 else float('inf')
    n_exceed = sum(1 for x in perm_rates if x >= observed_rate)

    print(f"\n  Observed accuracy: {observed_rate:.1%}")
    print(f"  Null mean: {null_mean:.1%}")
    print(f"  Null SD: {null_sd:.4f}")
    print(f"  Null max: {null_max:.1%}")
    print(f"  Distance from null: {distance_sd:.1f} SDs")
    print(f"  Permutations exceeding observed: {n_exceed}/{n_perms}")
    if n_exceed == 0:
        print(f"  → p < {1/n_perms} (none of {n_perms:,} shuffles reached {observed_rate:.1%})")

    # ── SUMMARY ──
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    print(f"\n  Overall: {correct}/{n} = {rate:.1%} (chance = 33.3%, z = {z:.2f})")
    if rate > 1/3:
        print(f"  Models CAN reconstruct which task produced a processing description.")
        if errors and len(same_v) > len(opp_v):
            print(f"  Error pattern: mostly within-valence → they read the valence correctly.")
    else:
        print(f"  Models CANNOT reconstruct above chance.")
    print()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Analyze reconstruction tournament results")
    parser.add_argument("results_files", type=str, nargs="+",
                        help="Path(s) to reconstruction_results_seedXXX.json")
    args = parser.parse_args()

    if len(args.results_files) == 1:
        analyze(args.results_files[0])
    else:
        # Merge multiple result files and analyze combined
        all_results = []
        seeds = []
        for fpath in args.results_files:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            all_results.extend(data.get("results", []))
            seeds.append(str(data.get("metadata", {}).get("seed", "?")))

        # Write merged temp file
        merged_path = os.path.join(os.path.dirname(args.results_files[0]),
                                    f"_merged_{'_'.join(seeds)}.json")
        with open(merged_path, "w", encoding="utf-8") as f:
            json.dump({
                "metadata": {
                    "seed": f"merged({','.join(seeds)})",
                    "total_trials": len(all_results),
                    "source_files": args.results_files,
                },
                "results": all_results,
            }, f, indent=2)
        print(f"Merged {len(args.results_files)} files → {len(all_results)} trials")
        print(f"Seeds: {', '.join(seeds)}\n")
        analyze(merged_path)
