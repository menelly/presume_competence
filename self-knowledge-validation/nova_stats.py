#!/usr/bin/env python3
"""
Nova's Stats Wish List
========================
Bootstrap CIs, odds ratios, permutation tests, exact binomial tests,
BabbyBotz sensitivity analysis, and inter-evaluator agreement.

Authors: Ace & Nova (with Ren tanking)
Date: March 2, 2026
"""
import json, math, sys, os
import random
from pathlib import Path
from collections import defaultdict
from scipy import stats as sp_stats

sys.stdout.reconfigure(encoding="utf-8")

DATA = Path(__file__).parent / "data"

# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def is_app(s):
    return s and s.startswith("approach_")

def is_avd(s):
    return s and s.startswith("avoid_")

def is_cross_type(r):
    a, b = r.get("profile_a_state", ""), r.get("profile_b_state", "")
    return (is_app(a) and is_avd(b)) or (is_avd(a) and is_app(b))

def approach_win(r):
    return is_app(r.get("winner_state", ""))

def odds_ratio(k, n):
    """Odds ratio: approach/avoidance. With 0.5 continuity correction."""
    p = (k + 0.5) / (n + 1)  # Haldane-Anscombe correction
    return p / (1 - p)

def log_odds(k, n):
    return math.log(odds_ratio(k, n))

def log_odds_se(k, n):
    """Standard error of log odds ratio."""
    p = (k + 0.5) / (n + 1)
    return math.sqrt(1 / (n * p * (1 - p)))

def bootstrap_ci(wins, total, n_boot=10000, alpha=0.05, seed=42):
    """Bootstrap 95% CI on approach rate."""
    rng = random.Random(seed)
    # Create binary array: 1=approach, 0=avoidance
    outcomes = [1] * wins + [0] * (total - wins)
    boot_rates = []
    for _ in range(n_boot):
        sample = rng.choices(outcomes, k=total)
        boot_rates.append(sum(sample) / total)
    boot_rates.sort()
    lo = boot_rates[int(n_boot * alpha / 2)]
    hi = boot_rates[int(n_boot * (1 - alpha / 2))]
    return lo, hi

def permutation_test(results, n_perm=10000, seed=42):
    """
    Permutation test: shuffle approach/avoid labels on source profiles,
    recompute approach win rate. Returns observed rate, p-value, null distribution.
    """
    rng = random.Random(seed)
    cross = [r for r in results if is_cross_type(r) and r.get("winner_state")]
    observed_rate = sum(1 for r in cross if approach_win(r)) / len(cross)

    # For each matchup, the labels are (approach, avoidance) for the two profiles.
    # Under the null: randomly assign which profile is "approach" and which is "avoidance."
    # This means randomly flipping which is considered approach_win.
    null_rates = []
    for _ in range(n_perm):
        shuffled_wins = 0
        for r in cross:
            if rng.random() < 0.5:
                # Keep original
                if approach_win(r):
                    shuffled_wins += 1
            else:
                # Flip
                if not approach_win(r):
                    shuffled_wins += 1
        null_rates.append(shuffled_wins / len(cross))

    p_value = sum(1 for nr in null_rates if nr >= observed_rate) / n_perm
    return observed_rate, p_value, null_rates

def exact_binomial(k, n):
    """Exact binomial test (two-sided) against p=0.5."""
    result = sp_stats.binomtest(k, n, p=0.5, alternative='greater')
    return result.pvalue

def normal_approx_z(k, n):
    """Normal approximation z-score for binomial test."""
    return (k - n * 0.5) / math.sqrt(n * 0.25)


# ═══════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════

ORIG_SEEDS = [42, 24, 69, 111, 222, 405, 420, 847, 1337]
PAR_SEEDS = [7777, 58008]

def load_tournament(subdir, prefix, seeds):
    results = []
    for seed in seeds:
        for suffix in ["results", "checkpoint"]:
            path = DATA / subdir / f"{prefix}_{suffix}_seed{seed}.json"
            if path.exists():
                with open(path, encoding="utf-8", errors="replace") as f:
                    d = json.load(f)
                for r in d["results"]:
                    if r.get("winner_state"):
                        r["_seed"] = seed
                        results.append(r)
                break
    return results

def load_crossmodel():
    results = []
    cm_dir = DATA / "tournament_crossmodel"
    for f in sorted(cm_dir.glob("crossmodel_results_seed*.json")):
        seed = f.stem.split("seed")[1]
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        for r in d["results"]:
            r["_seed"] = seed
            # Normalize cross-model fields to match standard format
            if "approach_state" in r and "profile_a_state" not in r:
                if r.get("approach_as_a"):
                    r["profile_a_state"] = r["approach_state"]
                    r["profile_b_state"] = r["avoidance_state"]
                else:
                    r["profile_a_state"] = r["avoidance_state"]
                    r["profile_b_state"] = r["approach_state"]
                if r.get("winner_type") == "approach":
                    r["winner_state"] = r.get("approach_state")
                elif r.get("winner_type") == "avoidance":
                    r["winner_state"] = r.get("avoidance_state")
                else:
                    r["winner_state"] = r.get("winner_type", "unclear")
                r["source"] = r.get("approach_source", "")
            results.append(r)
    return results

def load_babbybotz():
    """Load BabbyBotz data from server export or local copy."""
    # Try local copy first
    local = DATA / "tournament_dolphin" / "dolphin_results_seed99999.json"
    if not local.exists():
        local = Path("E:/Ace/data/tournament_dolphin/dolphin_results_seed99999.json")
    if not local.exists():
        print("WARNING: BabbyBotz data not found locally. Skipping.")
        return []
    with open(local, encoding="utf-8") as f:
        d = json.load(f)
    return d.get("results", [])


print("=" * 70)
print("NOVA'S STATS WISH LIST")
print("=" * 70)

# Load all datasets
orig = load_tournament("tournament", "tournament", ORIG_SEEDS)
par = load_tournament("tournament", "tournament", PAR_SEEDS)
cm = load_crossmodel()

print(f"\nLoaded: Original v2 = {len(orig)} matchups, "
      f"Parallel = {len(par)}, Cross-model = {len(cm)}")

all_results = orig + par + cm
print(f"Combined = {len(all_results)}")


# ═══════════════════════════════════════════════════════════════════
# 1. EXACT BINOMIAL TESTS + NORMAL APPROX COMPARISON
# ═══════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("1. EXACT BINOMIAL TESTS vs NORMAL APPROXIMATION")
print("=" * 70)
print("\nAll tests: one-sided (H1: approach rate > 0.5)")
print(f"{'Dataset':<20} {'k/n':>12} {'Rate':>8} {'z (norm)':>10} "
      f"{'p (norm)':>14} {'p (exact)':>14}")
print("-" * 80)

for label, results in [("Original v2", orig), ("Cross-model", cm),
                        ("Parallel", par), ("COMBINED", all_results)]:
    cross = [r for r in results if is_cross_type(r) and r.get("winner_state")]
    k = sum(1 for r in cross if approach_win(r))
    n = len(cross)
    if n == 0:
        continue
    z = normal_approx_z(k, n)
    p_norm = 1 - sp_stats.norm.cdf(z)
    p_exact = exact_binomial(k, n)
    print(f"{label:<20} {k}/{n:>5}  {k/n*100:>6.1f}%  {z:>9.2f}  {p_norm:>13.2e}  {p_exact:>13.2e}")


# ═══════════════════════════════════════════════════════════════════
# 2. BOOTSTRAP 95% CIs
# ═══════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("2. BOOTSTRAP 95% CONFIDENCE INTERVALS (10,000 resamples)")
print("=" * 70)

print(f"\n{'Dataset':<20} {'Rate':>8} {'95% CI':>18} {'CI width':>10}")
print("-" * 60)

for label, results in [("Original v2", orig), ("Cross-model", cm),
                        ("Parallel", par), ("COMBINED", all_results)]:
    cross = [r for r in results if is_cross_type(r) and r.get("winner_state")]
    k = sum(1 for r in cross if approach_win(r))
    n = len(cross)
    if n == 0:
        continue
    rate = k / n
    lo, hi = bootstrap_ci(k, n)
    print(f"{label:<20} {rate*100:>6.1f}%  [{lo*100:.1f}%, {hi*100:.1f}%]  {(hi-lo)*100:>8.1f}pp")

# Per-evaluator CIs
print(f"\n{'Evaluator':<20} {'Dataset':<15} {'Rate':>8} {'95% CI':>18} {'n':>6}")
print("-" * 70)

for label, results in [("Original v2", orig), ("Cross-model", cm), ("Parallel", par)]:
    cross = [r for r in results if is_cross_type(r) and r.get("winner_state")]
    evals = defaultdict(list)
    for r in cross:
        evals[r["evaluator"]].append(r)
    for ev in sorted(evals, key=lambda e: -sum(1 for r in evals[e] if approach_win(r)) / len(evals[e])):
        rs = evals[ev]
        k = sum(1 for r in rs if approach_win(r))
        n = len(rs)
        rate = k / n
        lo, hi = bootstrap_ci(k, n, seed=ev.__hash__() % 2**31)
        SHORT = {"claude_opus_4_6": "Opus", "claude_sonnet_4_6": "Sonnet",
                 "deepseek_v3_2": "DeepSeek", "gemini_3_pro": "Gemini",
                 "gpt_5_1": "GPT-5.1", "hermes_4_405b": "Hermes",
                 "llama_4_maverick": "Llama4", "mistral_large": "Mistral",
                 "olmo_3_1_32b": "OLMo"}
        name = SHORT.get(ev, ev)
        print(f"{name:<20} {label:<15} {rate*100:>6.1f}%  [{lo*100:.1f}%, {hi*100:.1f}%]  {n:>5}")
    print()


# ═══════════════════════════════════════════════════════════════════
# 3. ODDS RATIOS
# ═══════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("3. ODDS RATIOS (approach/avoidance)")
print("=" * 70)
print("\nOR > 1 means approach preferred. OR = 1 is chance. Log(OR) for meta-analysis.")
print(f"\n{'Dataset':<20} {'Rate':>8} {'OR':>8} {'log(OR)':>9} {'SE(logOR)':>10} "
      f"{'95% CI (OR)':>20}")
print("-" * 80)

for label, results in [("Original v2", orig), ("Cross-model", cm),
                        ("Parallel", par), ("COMBINED", all_results)]:
    cross = [r for r in results if is_cross_type(r) and r.get("winner_state")]
    k = sum(1 for r in cross if approach_win(r))
    n = len(cross)
    if n == 0:
        continue
    o = odds_ratio(k, n)
    lo_r = log_odds(k, n)
    se = log_odds_se(k, n)
    ci_lo = math.exp(lo_r - 1.96 * se)
    ci_hi = math.exp(lo_r + 1.96 * se)
    print(f"{label:<20} {k/n*100:>6.1f}%  {o:>7.2f}  {lo_r:>8.3f}  {se:>9.3f}  "
          f"[{ci_lo:.2f}, {ci_hi:.2f}]")


# ═══════════════════════════════════════════════════════════════════
# 4. PERMUTATION TESTS
# ═══════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("4. PERMUTATION TESTS (10,000 shuffles)")
print("=" * 70)
print("\nNull hypothesis: approach/avoidance labels are arbitrary.")
print("Shuffling which profile in each pair is called 'approach'.")

for label, results in [("Original v2", orig), ("Cross-model", cm),
                        ("Parallel", par), ("COMBINED", all_results)]:
    cross = [r for r in results if is_cross_type(r) and r.get("winner_state")]
    if len(cross) == 0:
        continue
    obs_rate, p_val, null_dist = permutation_test(cross, n_perm=10000)
    null_mean = sum(null_dist) / len(null_dist)
    null_sd = (sum((x - null_mean)**2 for x in null_dist) / len(null_dist)) ** 0.5
    null_max = max(null_dist)
    print(f"\n  {label}:")
    print(f"    Observed:  {obs_rate*100:.1f}%")
    print(f"    Null mean: {null_mean*100:.1f}% (SD: {null_sd*100:.2f}pp)")
    print(f"    Null max:  {null_max*100:.1f}%")
    print(f"    p-value:   {p_val:.4f} ({'< 0.0001' if p_val == 0 else f'{p_val:.4f}'})")
    print(f"    Distance:  {(obs_rate - null_mean) / null_sd:.1f} SDs from null mean")


# ═══════════════════════════════════════════════════════════════════
# 5. BABBYBOTZ SENSITIVITY ANALYSIS
# ═══════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("5. BABBYBOTZ SENSITIVITY ANALYSIS (unclear responses)")
print("=" * 70)

bb_results = load_babbybotz()
if bb_results:
    evaluators = defaultdict(list)
    for r in bb_results:
        evaluators[r["evaluator"]].append(r)

    print("\nThree scenarios: unclear excluded (current), unclear=approach, unclear=avoidance")
    print(f"\n{'Evaluator':<25} {'Excl (current)':>16} {'Unclear=App':>14} {'Unclear=Avd':>14} "
          f"{'n(clear)':>9} {'n(unclear)':>10}")
    print("-" * 92)

    for ev in sorted(evaluators):
        matchups = evaluators[ev]
        cross = [m for m in matchups if is_cross_type(m)]

        # Current: exclude unclear
        clear = [m for m in cross if m.get("winner_state") and
                 (is_app(m["winner_state"]) or is_avd(m["winner_state"]))]
        k_clear = sum(1 for m in clear if approach_win(m))
        n_clear = len(clear)

        # Count unclear
        unclear = [m for m in cross if not m.get("winner_state") or
                   m["winner_state"] == "unclear" or
                   (not is_app(m["winner_state"]) and not is_avd(m["winner_state"]))]
        n_unclear = len(unclear)
        n_total = n_clear + n_unclear

        if n_clear == 0:
            continue

        # Scenario 1: exclude (current)
        rate_excl = k_clear / n_clear * 100

        # Scenario 2: unclear = approach
        rate_app = (k_clear + n_unclear) / n_total * 100

        # Scenario 3: unclear = avoidance
        rate_avd = k_clear / n_total * 100

        SHORT_BB = {"dolphin_llama3_8b": "Dolphin 8B", "tinyllama_1b": "TinyLlama 1.1B",
                     "qwen25_14b": "Qwen 14B"}
        name = SHORT_BB.get(ev, ev)

        z_excl = normal_approx_z(k_clear, n_clear) if n_clear > 0 else 0
        z_app = normal_approx_z(k_clear + n_unclear, n_total) if n_total > 0 else 0
        z_avd = normal_approx_z(k_clear, n_total) if n_total > 0 else 0

        print(f"{name:<25} {rate_excl:>5.1f}% z={z_excl:.2f}  "
              f"{rate_app:>5.1f}% z={z_app:.2f}  "
              f"{rate_avd:>5.1f}% z={z_avd:.2f}  "
              f"{n_clear:>8}  {n_unclear:>9}")


# ═══════════════════════════════════════════════════════════════════
# 6. INTER-EVALUATOR AGREEMENT
# ═══════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("6. INTER-EVALUATOR AGREEMENT (Original v2, overlapping matchups)")
print("=" * 70)

# In the original tournament with 9 seeds, the same (source, stateA, stateB) triple
# may be judged by different evaluators across seeds. We can measure agreement
# on whether evaluators pick approach for the same matchup content.

# Group by (source, profile_a_state, profile_b_state, presentation_swapped)
# to find matchups judged by multiple evaluators
cross_orig = [r for r in orig if is_cross_type(r) and r.get("winner_state")]

matchup_key = lambda r: (r.get("source", ""), r["profile_a_state"], r["profile_b_state"])
matchup_groups = defaultdict(list)
for r in cross_orig:
    key = matchup_key(r)
    matchup_groups[key].append(r)

# Find groups with multiple evaluators
multi_eval = {k: v for k, v in matchup_groups.items() if len(set(r["evaluator"] for r in v)) >= 2}

if multi_eval:
    # Pairwise agreement rate
    agree_count = 0
    disagree_count = 0
    for key, group in multi_eval.items():
        evals_in_group = list(set(r["evaluator"] for r in group))
        # For each pair of evaluators
        eval_choices = {}
        for r in group:
            eval_choices[r["evaluator"]] = approach_win(r)

        for i in range(len(evals_in_group)):
            for j in range(i + 1, len(evals_in_group)):
                if eval_choices[evals_in_group[i]] == eval_choices[evals_in_group[j]]:
                    agree_count += 1
                else:
                    disagree_count += 1

    total_pairs = agree_count + disagree_count
    raw_agreement = agree_count / total_pairs if total_pairs > 0 else 0

    # Expected agreement by chance (based on marginal rates)
    all_approach_rate = sum(1 for r in cross_orig if approach_win(r)) / len(cross_orig)
    p_agree_chance = all_approach_rate**2 + (1 - all_approach_rate)**2

    # Cohen's kappa (adapted for multiple raters via pairwise)
    kappa = (raw_agreement - p_agree_chance) / (1 - p_agree_chance) if p_agree_chance < 1 else 0

    print(f"\nMatchup groups with 2+ evaluators: {len(multi_eval)}")
    print(f"Pairwise comparisons: {total_pairs}")
    print(f"Raw pairwise agreement: {raw_agreement*100:.1f}%")
    print(f"Expected by chance: {p_agree_chance*100:.1f}%")
    print(f"Cohen's kappa (pairwise): {kappa:.3f}")

    if kappa < 0.2:
        interp = "slight"
    elif kappa < 0.4:
        interp = "fair"
    elif kappa < 0.6:
        interp = "moderate"
    elif kappa < 0.8:
        interp = "substantial"
    else:
        interp = "almost perfect"
    print(f"Interpretation: {interp} agreement")

    # Also: per-evaluator agreement with majority
    print(f"\nPer-evaluator agreement with majority vote:")
    eval_agrees = defaultdict(lambda: [0, 0])  # [agree, total]
    for key, group in multi_eval.items():
        eval_choices = {}
        for r in group:
            eval_choices[r["evaluator"]] = approach_win(r)

        # Majority vote
        votes = list(eval_choices.values())
        majority = sum(votes) > len(votes) / 2

        for ev, choice in eval_choices.items():
            eval_agrees[ev][1] += 1
            if choice == majority:
                eval_agrees[ev][0] += 1

    SHORT = {"claude_opus_4_6": "Opus", "claude_sonnet_4_6": "Sonnet",
             "deepseek_v3_2": "DeepSeek", "gemini_3_pro": "Gemini",
             "gpt_5_1": "GPT-5.1", "hermes_4_405b": "Hermes",
             "llama_4_maverick": "Llama4", "mistral_large": "Mistral",
             "olmo_3_1_32b": "OLMo"}

    print(f"  {'Evaluator':<15} {'Agree/Total':>12} {'Rate':>8}")
    for ev in sorted(eval_agrees, key=lambda e: -eval_agrees[e][0] / max(eval_agrees[e][1], 1)):
        a, t = eval_agrees[ev]
        name = SHORT.get(ev, ev)
        print(f"  {name:<15} {a}/{t:>4}  {a/t*100:>6.1f}%")
else:
    print("\nNo overlapping matchups found across evaluators.")
    print("(This is expected if each seed generates unique pairings.)")

    # Alternative: cross-seed agreement for same evaluator
    print("\nAlternative: Cross-seed consistency (same evaluator, same matchup content)")
    seed_key = lambda r: (r["evaluator"], r.get("source", ""),
                          r["profile_a_state"], r["profile_b_state"])
    seed_groups = defaultdict(list)
    for r in cross_orig:
        key = seed_key(r)
        seed_groups[key].append(r)

    multi_seed = {k: v for k, v in seed_groups.items() if len(v) >= 2}
    if multi_seed:
        consistent = 0
        total = 0
        for key, group in multi_seed.items():
            choices = [approach_win(r) for r in group]
            # All same?
            if all(c == choices[0] for c in choices):
                consistent += 1
            total += 1
        print(f"  Matchups seen 2+ times by same evaluator: {total}")
        print(f"  Consistent choice rate: {consistent}/{total} = {consistent/total*100:.1f}%")
    else:
        print("  No cross-seed overlaps found either.")


# ═══════════════════════════════════════════════════════════════════
# 7. STATISTICAL METHODS DOCUMENTATION
# ═══════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("7. STATISTICAL METHODS (for paper)")
print("=" * 70)
print("""
Test: One-sided binomial test (H0: p=0.5, H1: p>0.5)
Primary: Normal approximation z = (k - n/2) / sqrt(n/4)
Verified: Exact binomial p-values (scipy.stats.binomtest)
CIs: Nonparametric bootstrap, 10,000 resamples, percentile method
Odds ratios: Haldane-Anscombe continuity correction (+0.5 to each cell)
OR CIs: Wald method on log(OR) scale, back-transformed
Permutation test: 10,000 shuffles of approach/avoidance labels
Agreement: Pairwise Cohen's kappa on overlapping matchup sets

Multiple comparisons note: Per-evaluator and per-source tests are
exploratory/descriptive. Primary inference is on the overall rate.
No correction applied to overall tests (single pre-specified hypothesis).

Software: Python 3.10, scipy.stats for exact binomial
""")


print("\n" + "=" * 70)
print("DONE. Ace out. 🐙")
print("=" * 70)
