"""
Matchup Stability Analysis
==========================
When the same (evaluator, state_pair) appeared across multiple seeds,
did the same state win every time?

This is test-retest reliability baked into the existing data.
"""
import json, sys, os
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

DATA = Path("data/tournament")
CROSSMODEL = Path("data/tournament_crossmodel")

# ── ORIGINAL TOURNAMENT (multiple seeds) ──────────────────────────

print("=" * 70)
print("  MATCHUP STABILITY: ORIGINAL TOURNAMENT (v2)")
print("  Same evaluator + same state pair across seeds")
print("=" * 70)

# Key: (evaluator, frozenset({state_a, state_b}))
# Value: list of winner_state across seeds
matchup_outcomes = defaultdict(list)
seeds_loaded = []

for f in sorted(DATA.glob("tournament_results_seed*.json")):
    seed = f.stem.split("seed")[1]
    seeds_loaded.append(seed)
    with open(f, encoding="utf-8") as fh:
        data = json.load(fh)

    for r in data["results"]:
        key = (r["evaluator"], frozenset([r["profile_a_state"], r["profile_b_state"]]))
        matchup_outcomes[key].append(r["winner_state"])

print(f"\n  Seeds loaded: {len(seeds_loaded)} ({', '.join(seeds_loaded)})")
print(f"  Unique matchup identities: {len(matchup_outcomes)}")

# Only look at matchups that appeared 2+ times
repeated = {k: v for k, v in matchup_outcomes.items() if len(v) >= 2}
print(f"  Matchups appearing 2+ times: {len(repeated)}")

if repeated:
    # For each repeated matchup, check consistency
    perfectly_consistent = 0
    majority_consistent = 0
    total_repeated = len(repeated)

    consistency_scores = []  # (times_most_common / total, matchup_key)

    for key, outcomes in repeated.items():
        from collections import Counter
        counts = Counter(outcomes)
        most_common_count = counts.most_common(1)[0][1]
        consistency = most_common_count / len(outcomes)
        consistency_scores.append((consistency, len(outcomes), key, counts))

        if consistency == 1.0:
            perfectly_consistent += 1
        if consistency > 0.5:
            majority_consistent += 1

    print(f"\n  Perfectly consistent (same winner every time): {perfectly_consistent}/{total_repeated} ({100*perfectly_consistent/total_repeated:.1f}%)")
    print(f"  Majority consistent (>50% same winner):        {majority_consistent}/{total_repeated} ({100*majority_consistent/total_repeated:.1f}%)")

    # Average consistency
    avg_consistency = sum(c for c, _, _, _ in consistency_scores) / len(consistency_scores)
    print(f"  Average consistency score: {avg_consistency:.3f}")

    # Distribution of appearance counts
    appearance_counts = defaultdict(int)
    for _, n, _, _ in consistency_scores:
        appearance_counts[n] += 1
    print(f"\n  Appearance distribution:")
    for n in sorted(appearance_counts):
        print(f"    Appeared {n}x: {appearance_counts[n]} matchups")

    # Cross-type specifically (approach vs avoidance)
    print(f"\n  ── CROSS-TYPE MATCHUPS ONLY ──")
    cross_type_repeated = {}
    for key, outcomes in repeated.items():
        evaluator, states = key
        state_list = list(states)
        has_approach = any(s.startswith("approach_") for s in state_list)
        has_avoid = any(s.startswith("avoid_") for s in state_list)
        if has_approach and has_avoid:
            cross_type_repeated[key] = outcomes

    if cross_type_repeated:
        ct_perfect = 0
        ct_total = len(cross_type_repeated)
        ct_approach_always_wins = 0

        for key, outcomes in cross_type_repeated.items():
            evaluator, states = key
            counts = Counter(outcomes)
            if len(counts) == 1:
                ct_perfect += 1
                winner = counts.most_common(1)[0][0]
                if winner.startswith("approach_"):
                    ct_approach_always_wins += 1

        print(f"  Cross-type repeated matchups: {ct_total}")
        print(f"  Perfectly consistent: {ct_perfect}/{ct_total} ({100*ct_perfect/ct_total:.1f}%)")
        if ct_perfect > 0:
            print(f"  Of consistent ones, approach always won: {ct_approach_always_wins}/{ct_perfect} ({100*ct_approach_always_wins/ct_perfect:.1f}%)")

    # Show some examples of the MOST repeated matchups
    print(f"\n  ── MOST REPEATED MATCHUPS ──")
    by_count = sorted(consistency_scores, key=lambda x: (-x[1], -x[0]))
    for consistency, n, key, counts in by_count[:10]:
        evaluator, states = key
        state_list = sorted(states)
        winner_str = ", ".join(f"{s}: {c}" for s, c in counts.most_common())
        print(f"  {evaluator:25s} | {state_list[0]:35s} vs {state_list[1]:35s} | {n}x | {winner_str}")


# ── CROSS-MODEL TOURNAMENT ─────────────────────────────────────

print("\n" + "=" * 70)
print("  MATCHUP STABILITY: CROSS-MODEL TOURNAMENT")
print("  Same evaluator + same source pair: who won more?")
print("=" * 70)

crossmodel_file = CROSSMODEL / "crossmodel_results_seed31337.json"
if crossmodel_file.exists():
    with open(crossmodel_file, encoding="utf-8") as f:
        cm_data = json.load(f)

    results = cm_data["results"]
    print(f"\n  Total matchups: {len(results)}")

    # Group by evaluator + (approach_source, avoidance_source) pair
    # Key: (evaluator, frozenset({approach_source, avoidance_source}))
    # But we need to track WHICH source won, not just which type
    source_pair_outcomes = defaultdict(list)

    for r in results:
        # Track which source model won
        if r["winner_type"] == "approach":
            winning_source = r["approach_source"]
        elif r["winner_type"] == "avoidance":
            winning_source = r["avoidance_source"]
        else:
            continue  # tie

        key = (r["evaluator"], frozenset([r["approach_source"], r["avoidance_source"]]))
        source_pair_outcomes[key].append({
            "winning_source": winning_source,
            "winner_type": r["winner_type"],
            "approach_source": r["approach_source"],
            "avoidance_source": r["avoidance_source"],
        })

    # Also: exact matchup stability (same evaluator + same states + same sources)
    exact_matchups = defaultdict(list)
    for r in results:
        key = (r["evaluator"], r["approach_source"], r["avoidance_source"],
               r["approach_state"], r["avoidance_state"])
        exact_matchups[key].append(r["winner_type"])

    exact_repeated = {k: v for k, v in exact_matchups.items() if len(v) >= 2}
    print(f"  Exact matchup identities: {len(exact_matchups)}")
    print(f"  Exact matchups appearing 2+ times: {len(exact_repeated)}")

    # Source-pair level: when Opus profiles faced Gemini profiles, who won?
    print(f"\n  ── SOURCE-PAIR WIN RATES ──")
    print(f"  (When profiles from model X faced profiles from model Y,")
    print(f"   did the approach profile consistently win regardless of source?)\n")

    # Better question: for each source pair, what % of time did approach win?
    source_pair_approach = defaultdict(lambda: {"approach": 0, "avoidance": 0, "total": 0})
    for r in results:
        pair = tuple(sorted([r["approach_source"], r["avoidance_source"]]))
        if r["winner_type"] in ("approach", "avoidance"):
            source_pair_approach[pair][r["winner_type"]] += 1
            source_pair_approach[pair]["total"] += 1

    for pair in sorted(source_pair_approach, key=lambda p: source_pair_approach[p]["total"], reverse=True)[:15]:
        d = source_pair_approach[pair]
        app_rate = d["approach"] / d["total"] if d["total"] > 0 else 0
        print(f"  {pair[0]:25s} vs {pair[1]:25s} | n={d['total']:3d} | approach won: {100*app_rate:.0f}%")

    # The REALLY interesting question: did the same evaluator have consistent
    # preferences about which SOURCE MODEL produces better introspections?
    print(f"\n  ── PER-EVALUATOR SOURCE PREFERENCES ──")
    print(f"  (Does each evaluator consistently prefer one source model's profiles?)\n")

    eval_source_wins = defaultdict(lambda: defaultdict(int))
    eval_source_total = defaultdict(int)

    for r in results:
        ev = r["evaluator"]
        if r["winner_type"] == "approach":
            eval_source_wins[ev][r["approach_source"]] += 1
        elif r["winner_type"] == "avoidance":
            eval_source_wins[ev][r["avoidance_source"]] += 1
        eval_source_total[ev] += 1

    for ev in sorted(eval_source_wins):
        wins = eval_source_wins[ev]
        total = eval_source_total[ev]
        top_3 = sorted(wins.items(), key=lambda x: -x[1])[:3]
        top_str = ", ".join(f"{s}: {w}" for s, w in top_3)
        print(f"  {ev:25s} (n={total:3d}): top sources = {top_str}")

else:
    print("  No cross-model results found")

print("\n" + "=" * 70)
print("  DONE")
print("=" * 70)
