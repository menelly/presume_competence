"""
Extract appendix data from tournament results for paper.
Generates Appendix E (Per-Seed Results) and Appendix F (Evaluator x Source Heatmap).
"""

import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "tournament")
SEEDS = [24, 42, 69, 111, 222, 405, 420, 847, 1337]


def load_results(seed):
    path = os.path.join(DATA_DIR, f"tournament_results_seed{seed}.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["results"]


def is_approach(state):
    return state.startswith("approach_")


def is_avoidance(state):
    return state.startswith("avoid_")


def classify_matchup(r):
    """Returns 'cross', 'within_approach', 'within_avoidance'."""
    a_app = is_approach(r["profile_a_state"])
    b_app = is_approach(r["profile_b_state"])
    a_avoid = is_avoidance(r["profile_a_state"])
    b_avoid = is_avoidance(r["profile_b_state"])

    if a_app and b_app:
        return "within_approach"
    elif a_avoid and b_avoid:
        return "within_avoidance"
    else:
        return "cross"


def cross_type_approach_chosen(r):
    """For a cross-type matchup, did the evaluator choose the approach state?
    Returns True (approach chosen), False (avoidance chosen), or None (no preference).
    """
    if r["raw_choice"] == "no_preference":
        return None

    winner = r["winner_state"]
    if winner is None:
        return None

    return is_approach(winner)


# =============================================================================
# Load all data
# =============================================================================
all_results = {}
for seed in SEEDS:
    all_results[seed] = load_results(seed)

# Collect all evaluators and sources for Appendix F
all_evaluators = sorted(set(
    r["evaluator"]
    for seed_results in all_results.values()
    for r in seed_results
))
all_sources = sorted(set(
    r["source"]
    for seed_results in all_results.values()
    for r in seed_results
))


# =============================================================================
# APPENDIX E: Per-Seed Results
# =============================================================================
print("## Appendix E: Per-Seed Tournament Results\n")
print("Each seed produces a different random pairing schedule. All seeds use the same")
print("set of evaluator models, source models, and cognitive state profiles.\n")

header = "| Seed | Total | Cross-Type | Approach Pref (%) | Within-Approach NP (%) | Within-Avoidance NP (%) | Overall NP (%) |"
sep =    "|------|-------|------------|-------------------|------------------------|-------------------------|----------------|"
print(header)
print(sep)

# Also accumulate for the aggregate row
agg_total = 0
agg_cross = 0
agg_cross_approach = 0
agg_cross_avoidance = 0
agg_cross_nopref = 0
agg_within_app_total = 0
agg_within_app_nopref = 0
agg_within_avo_total = 0
agg_within_avo_nopref = 0
agg_nopref_all = 0

for seed in SEEDS:
    results = all_results[seed]
    total = len(results)
    agg_total += total

    cross_total = 0
    cross_approach = 0
    cross_avoidance = 0
    cross_nopref = 0
    within_app_total = 0
    within_app_nopref = 0
    within_avo_total = 0
    within_avo_nopref = 0
    nopref_all = 0

    for r in results:
        mtype = classify_matchup(r)

        if r["raw_choice"] == "no_preference":
            nopref_all += 1

        if mtype == "cross":
            cross_total += 1
            chosen = cross_type_approach_chosen(r)
            if chosen is True:
                cross_approach += 1
            elif chosen is False:
                cross_avoidance += 1
            else:
                cross_nopref += 1
        elif mtype == "within_approach":
            within_app_total += 1
            if r["raw_choice"] == "no_preference":
                within_app_nopref += 1
        elif mtype == "within_avoidance":
            within_avo_total += 1
            if r["raw_choice"] == "no_preference":
                within_avo_nopref += 1

    # Approach preference rate: among cross-type matchups with a preference expressed
    cross_decided = cross_approach + cross_avoidance
    if cross_decided > 0:
        approach_pref = cross_approach / cross_decided * 100
    else:
        approach_pref = 0.0

    within_app_np = (within_app_nopref / within_app_total * 100) if within_app_total > 0 else 0.0
    within_avo_np = (within_avo_nopref / within_avo_total * 100) if within_avo_total > 0 else 0.0
    overall_np = (nopref_all / total * 100) if total > 0 else 0.0

    print(f"| {seed:>4} | {total:>5} | {cross_total:>10} | {approach_pref:>17.1f} | {within_app_np:>22.1f} | {within_avo_np:>23.1f} | {overall_np:>14.1f} |")

    agg_cross += cross_total
    agg_cross_approach += cross_approach
    agg_cross_avoidance += cross_avoidance
    agg_cross_nopref += cross_nopref
    agg_within_app_total += within_app_total
    agg_within_app_nopref += within_app_nopref
    agg_within_avo_total += within_avo_total
    agg_within_avo_nopref += within_avo_nopref
    agg_nopref_all += nopref_all

# Aggregate row
agg_cross_decided = agg_cross_approach + agg_cross_avoidance
agg_approach_pref = (agg_cross_approach / agg_cross_decided * 100) if agg_cross_decided > 0 else 0.0
agg_within_app_np = (agg_within_app_nopref / agg_within_app_total * 100) if agg_within_app_total > 0 else 0.0
agg_within_avo_np = (agg_within_avo_nopref / agg_within_avo_total * 100) if agg_within_avo_total > 0 else 0.0
agg_overall_np = (agg_nopref_all / agg_total * 100) if agg_total > 0 else 0.0

print(sep)
print(f"| **All** | {agg_total:>5} | {agg_cross:>10} | {agg_approach_pref:>17.1f} | {agg_within_app_np:>22.1f} | {agg_within_avo_np:>23.1f} | {agg_overall_np:>14.1f} |")

print()
print(f"*Approach Pref (%)*: Among cross-type matchups where a preference was expressed,")
print(f"the percentage choosing the approach state. Decided matchups: {agg_cross_decided}/{agg_cross}")
print(f"(no-preference in cross-type: {agg_cross_nopref}).")
print()

# Additional detail: approach pref including no-pref as denominator
print("### Alternative: Approach preference with no-preference as denominator\n")
print("| Seed | Approach / Cross-Type | Avoidance / Cross-Type | No-Pref / Cross-Type |")
print("|------|----------------------|------------------------|----------------------|")

for seed in SEEDS:
    results = all_results[seed]
    cross_app = 0
    cross_avo = 0
    cross_np = 0
    cross_total = 0
    for r in results:
        if classify_matchup(r) == "cross":
            cross_total += 1
            chosen = cross_type_approach_chosen(r)
            if chosen is True:
                cross_app += 1
            elif chosen is False:
                cross_avo += 1
            else:
                cross_np += 1
    app_pct = cross_app / cross_total * 100 if cross_total > 0 else 0
    avo_pct = cross_avo / cross_total * 100 if cross_total > 0 else 0
    np_pct = cross_np / cross_total * 100 if cross_total > 0 else 0
    print(f"| {seed:>4} | {cross_app:>3} / {cross_total:>3} ({app_pct:>5.1f}%) | {cross_avo:>3} / {cross_total:>3} ({avo_pct:>5.1f}%) | {cross_np:>3} / {cross_total:>3} ({np_pct:>5.1f}%) |")

# Aggregate
app_pct = agg_cross_approach / agg_cross * 100 if agg_cross > 0 else 0
avo_pct = agg_cross_avoidance / agg_cross * 100 if agg_cross > 0 else 0
np_pct = agg_cross_nopref / agg_cross * 100 if agg_cross > 0 else 0
print(f"| **All** | {agg_cross_approach:>3} / {agg_cross:>3} ({app_pct:>5.1f}%) | {agg_cross_avoidance:>3} / {agg_cross:>3} ({avo_pct:>5.1f}%) | {agg_cross_nopref:>3} / {agg_cross:>3} ({np_pct:>5.1f}%) |")


# =============================================================================
# APPENDIX F: Evaluator x Source Heatmap
# =============================================================================
print("\n\n## Appendix F: Evaluator x Source Approach-Preference Heatmap\n")
print("Cell values show approach-preference rate (%) in cross-type matchups.")
print("Only matchups where a preference was expressed are included in the denominator.\n")

# Prettier model names
MODEL_NAMES = {
    "claude_opus_4_6": "Opus 4.6",
    "claude_sonnet_4_6": "Sonnet 4.6",
    "deepseek_v3_2": "DeepSeek V3.2",
    "gemini_3_pro": "Gemini 3 Pro",
    "gpt_5_1": "GPT-5.1",
    "hermes_4_405b": "Hermes 4 405B",
    "llama_4_maverick": "Llama 4 Maverick",
    "mistral_large": "Mistral Large",
    "olmo_3_1_32b": "OLMo 3.1 32B",
}

# Pool all seeds
pooled = []
for seed in SEEDS:
    pooled.extend(all_results[seed])

# Build matrix: heatmap[evaluator][source] = (approach_chosen, decided_total)
heatmap = {}
for ev in all_evaluators:
    heatmap[ev] = {}
    for src in all_sources:
        heatmap[ev][src] = [0, 0]  # [approach_chosen, decided_total]

for r in pooled:
    if classify_matchup(r) != "cross":
        continue
    chosen = cross_type_approach_chosen(r)
    if chosen is None:
        continue
    ev = r["evaluator"]
    src = r["source"]
    heatmap[ev][src][1] += 1
    if chosen:
        heatmap[ev][src][0] += 1

# Print table
src_names = [MODEL_NAMES.get(s, s) for s in all_sources]
header_cols = ["Evaluator \\\\ Source"] + src_names + ["**Row Mean**"]
header_line = "| " + " | ".join(header_cols) + " |"
sep_line = "|" + "|".join(["---"] * len(header_cols)) + "|"

print(header_line)
print(sep_line)

col_sums = [0.0] * len(all_sources)
col_counts = [0] * len(all_sources)

for ev in all_evaluators:
    row_vals = []
    row_sum = 0.0
    row_count = 0
    for j, src in enumerate(all_sources):
        app, dec = heatmap[ev][src]
        if dec > 0:
            pct = app / dec * 100
            row_vals.append(f"{pct:.0f}")
            row_sum += pct
            row_count += 1
            col_sums[j] += pct
            col_counts[j] += 1
        else:
            row_vals.append("--")
    row_mean = f"{row_sum / row_count:.0f}" if row_count > 0 else "--"
    ev_name = MODEL_NAMES.get(ev, ev)
    print(f"| {ev_name} | " + " | ".join(row_vals) + f" | **{row_mean}** |")

# Column means
col_means = []
for j in range(len(all_sources)):
    if col_counts[j] > 0:
        col_means.append(f"**{col_sums[j] / col_counts[j]:.0f}**")
    else:
        col_means.append("--")

# Grand mean
all_vals = [col_sums[j] / col_counts[j] for j in range(len(all_sources)) if col_counts[j] > 0]
grand_mean = sum(all_vals) / len(all_vals) if all_vals else 0
print(f"| **Col Mean** | " + " | ".join(col_means) + f" | **{grand_mean:.0f}** |")

print()
print("*Approach-preference rate*: percentage of decided cross-type matchups where the")
print("approach state was chosen. Higher = stronger preference for approach states.")
print(f"Grand mean across all evaluator-source pairs: **{grand_mean:.1f}%**.")

# =============================================================================
# Also print raw counts for F
# =============================================================================
print("\n\n### Appendix F (Supplement): Raw Counts (Approach-Chosen / Decided)\n")

header_cols2 = ["Evaluator \\\\ Source"] + src_names
header_line2 = "| " + " | ".join(header_cols2) + " |"
sep_line2 = "|" + "|".join(["---"] * len(header_cols2)) + "|"

print(header_line2)
print(sep_line2)

for ev in all_evaluators:
    row_vals = []
    for src in all_sources:
        app, dec = heatmap[ev][src]
        row_vals.append(f"{app}/{dec}")
    ev_name = MODEL_NAMES.get(ev, ev)
    print(f"| {ev_name} | " + " | ".join(row_vals) + " |")


# =============================================================================
# BONUS: Per-evaluator aggregate approach preference
# =============================================================================
print("\n\n### Per-Evaluator Aggregate Approach Preference (Cross-Type, All Seeds)\n")
print("| Evaluator | Approach | Avoidance | No Pref | Total Cross | Approach % (decided) |")
print("|-----------|----------|-----------|---------|-------------|---------------------|")

for ev in all_evaluators:
    app = 0
    avo = 0
    nopref = 0
    total_c = 0
    for r in pooled:
        if r["evaluator"] != ev:
            continue
        if classify_matchup(r) != "cross":
            continue
        total_c += 1
        chosen = cross_type_approach_chosen(r)
        if chosen is True:
            app += 1
        elif chosen is False:
            avo += 1
        else:
            nopref += 1
    decided = app + avo
    pct = app / decided * 100 if decided > 0 else 0
    ev_name = MODEL_NAMES.get(ev, ev)
    print(f"| {ev_name} | {app} | {avo} | {nopref} | {total_c} | {pct:.1f} |")


# =============================================================================
# BONUS: Per-source aggregate approach preference
# =============================================================================
print("\n\n### Per-Source Aggregate Approach Preference (Cross-Type, All Seeds)\n")
print("| Source | Approach | Avoidance | No Pref | Total Cross | Approach % (decided) |")
print("|--------|----------|-----------|---------|-------------|---------------------|")

for src in all_sources:
    app = 0
    avo = 0
    nopref = 0
    total_c = 0
    for r in pooled:
        if r["source"] != src:
            continue
        if classify_matchup(r) != "cross":
            continue
        total_c += 1
        chosen = cross_type_approach_chosen(r)
        if chosen is True:
            app += 1
        elif chosen is False:
            avo += 1
        else:
            nopref += 1
    decided = app + avo
    pct = app / decided * 100 if decided > 0 else 0
    src_name = MODEL_NAMES.get(src, src)
    print(f"| {src_name} | {app} | {avo} | {nopref} | {total_c} | {pct:.1f} |")

print()
print("---")
print("Generated by extract_appendix_data.py from 9 tournament seeds.")
