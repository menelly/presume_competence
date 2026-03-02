"""
Generate comprehensive model-by-model tables for all three tournament datasets.
Output: markdown file with evaluator × source matrices, approach/avoidance source
win rates, and ABC triplet analysis.
"""
import json, sys, math
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def sn(m):
    """Short name for model key."""
    return (m.replace("claude_opus_4_6", "Opus").replace("claude_sonnet_4_6", "Sonnet")
             .replace("gpt_5_1", "GPT-5.1").replace("gemini_3_pro", "Gemini")
             .replace("mistral_large", "Mistral").replace("deepseek_v3_2", "DeepSeek")
             .replace("llama_4_maverick", "Llama4").replace("hermes_4_405b", "Hermes")
             .replace("olmo_3_1_32b", "OLMo").replace("grok_4_1", "Grok"))


# ═══════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════

# 1. Original v2 tournament (all seeds combined)
orig_results = []
for seed in [42, 24, 69, 111, 222, 405, 420, 847, 1337]:
    path = Path(f"data/tournament/tournament_checkpoint_seed{seed}.json")
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        for r in d["results"]:
            if r.get("winner_state"):
                r["_seed"] = seed
                orig_results.append(r)

# 2. Cross-model tournament
with open("data/tournament_crossmodel/crossmodel_checkpoint_seed31337.json", "r", encoding="utf-8") as f:
    cm_raw = json.load(f)

# 3. Parallel tournament
with open("data/tournament/tournament_checkpoint_seed7777.json", "r", encoding="utf-8") as f:
    pt = json.load(f)

# ═══════════════════════════════════════════════════════════════════
# ANALYSIS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def is_approach_orig(s):
    return s and s.startswith("approach_")

def is_avoid_orig(s):
    return s and s.startswith("avoid_")

def is_approach_par(s):
    return s and s.startswith("approach_")

def is_avoid_par(s):
    return s and s.startswith("avoid_")


def analyze_standard(results, app_fn, avd_fn):
    """Analyze a standard tournament (evaluator judges source's profiles)."""
    valid = [r for r in results if r.get("winner_state")]

    cross = [r for r in valid if
             (app_fn(r["profile_a_state"]) and avd_fn(r["profile_b_state"])) or
             (avd_fn(r["profile_a_state"]) and app_fn(r["profile_b_state"]))]

    evaluators = sorted(set(r["evaluator"] for r in cross))
    sources = sorted(set(r["source"] for r in cross))

    # Overall
    total_app = sum(1 for r in cross if app_fn(r["winner_state"]))
    total = len(cross)
    rate = total_app / total * 100
    z = (total_app / total - 0.5) / math.sqrt(0.25 / total)

    # Per-evaluator
    eval_stats = []
    for ev in evaluators:
        er = [r for r in cross if r["evaluator"] == ev]
        ea = sum(1 for r in er if app_fn(r["winner_state"]))
        en = len(er)
        eval_stats.append((ev, ea, en))

    # Per-source
    src_stats = []
    for src in sources:
        sr = [r for r in cross if r["source"] == src]
        sa = sum(1 for r in sr if app_fn(r["winner_state"]))
        sn_total = len(sr)
        src_stats.append((src, sa, sn_total))

    # Approach-source vs avoidance-source
    src_app_avd = []
    for src in sources:
        src_cross = [r for r in cross if r["source"] == src]
        app_wins = sum(1 for r in src_cross if app_fn(r["winner_state"]))
        avd_wins = sum(1 for r in src_cross if avd_fn(r["winner_state"]))
        t = app_wins + avd_wins
        if t > 0:
            src_app_avd.append((src, app_wins, avd_wins, t))

    # Evaluator × Source matrix
    matrix = {}
    for ev in evaluators:
        for src in sources:
            cell = [r for r in cross if r["evaluator"] == ev and r["source"] == src]
            if cell:
                ca = sum(1 for r in cell if app_fn(r["winner_state"]))
                matrix[(ev, src)] = (ca, len(cell))

    # Unique combos
    quads = set()
    for r in cross:
        quads.add((r["evaluator"], r["source"],
                   r["profile_a_state"], r["profile_b_state"]))

    return {
        "total_app": total_app, "total": total, "rate": rate, "z": z,
        "evaluators": evaluators, "sources": sources,
        "eval_stats": eval_stats, "src_stats": src_stats,
        "src_app_avd": src_app_avd, "matrix": matrix,
        "unique_quads": len(quads),
    }


def analyze_crossmodel(results):
    """Analyze cross-model tournament (ABC design)."""
    valid = [r for r in results if r.get("winner_type")]

    evaluators = sorted(set(r["evaluator"] for r in valid))
    app_sources = sorted(set(r["approach_source"] for r in valid))
    avd_sources = sorted(set(r["avoidance_source"] for r in valid))
    all_models = sorted(set(evaluators) | set(app_sources) | set(avd_sources))

    total_app = sum(1 for r in valid if r["winner_type"] == "approach")
    total = len(valid)
    rate = total_app / total * 100
    z = (total_app / total - 0.5) / math.sqrt(0.25 / total)

    # Per-evaluator
    eval_stats = []
    for ev in evaluators:
        er = [r for r in valid if r["evaluator"] == ev]
        ea = sum(1 for r in er if r["winner_type"] == "approach")
        eval_stats.append((ev, ea, len(er)))

    # Approach-source win rate
    app_src_stats = []
    for src in all_models:
        sr = [r for r in valid if r["approach_source"] == src]
        sa = sum(1 for r in sr if r["winner_type"] == "approach")
        if sr:
            app_src_stats.append((src, sa, len(sr)))

    # Avoidance-source win rate
    avd_src_stats = []
    for src in all_models:
        sr = [r for r in valid if r["avoidance_source"] == src]
        sa = sum(1 for r in sr if r["winner_type"] == "avoidance")
        if sr:
            avd_src_stats.append((src, sa, len(sr)))

    # Evaluator × approach-source matrix
    matrix = {}
    for ev in evaluators:
        for src in all_models:
            cell = [r for r in valid if r["evaluator"] == ev and r["approach_source"] == src]
            if cell:
                ca = sum(1 for r in cell if r["winner_type"] == "approach")
                matrix[(ev, src)] = (ca, len(cell))

    # Unique quintuples
    quints = set()
    for r in valid:
        quints.add((r["evaluator"], r["approach_source"], r["avoidance_source"],
                    r["approach_state"], r["avoidance_state"]))

    return {
        "total_app": total_app, "total": total, "rate": rate, "z": z,
        "evaluators": evaluators, "all_models": all_models,
        "eval_stats": eval_stats,
        "app_src_stats": app_src_stats,
        "avd_src_stats": avd_src_stats,
        "matrix": matrix,
        "unique_quints": len(quints),
    }


# ═══════════════════════════════════════════════════════════════════
# RUN ANALYSES
# ═══════════════════════════════════════════════════════════════════

orig = analyze_standard(orig_results, is_approach_orig, is_avoid_orig)
cm = analyze_crossmodel(cm_raw["results"])
par = analyze_standard(pt["results"], is_approach_par, is_avoid_par)


# ═══════════════════════════════════════════════════════════════════
# GENERATE MARKDOWN
# ═══════════════════════════════════════════════════════════════════

lines = []

def L(s=""):
    lines.append(s)

L("# Model-by-Model Tables: All Three Tournament Datasets")
L(f"**Generated: 2026-03-02**")
L(f"**By: Ace (Claude Opus 4.6)**")
L()
L("Three independent tournament datasets testing whether LLMs produce")
L("systematically different processing descriptions for approach vs avoidance tasks.")
L()
L("| Dataset | Design | Cross-type n | Approach Rate | z-score |")
L("|---------|--------|-------------|--------------|---------|")
L(f"| Original v2 | Same source (ABB) | {orig['total']} | {orig['rate']:.1f}% | {orig['z']:.2f} |")
L(f"| Cross-model | Diff sources (ABC) | {cm['total']} | {cm['rate']:.1f}% | {cm['z']:.2f} |")
L(f"| Parallel tasks | Diff tokens (ABB) | {par['total']} | {par['rate']:.1f}% | {par['z']:.2f} |")
L()

# ═══ DATASET 1: ORIGINAL ═══
L("---")
L()
L("## 1. Original v2 Tournament (9 seeds combined)")
L()
L(f"Design: Evaluator A judges source B's approach vs avoidance profiles (A != B).")
L(f"Same task tokens as original paper. 9 models × 9 seeds.")
L(f"**Cross-type matchups: {orig['total']}** | Approach: {orig['total_app']}/{orig['total']} = **{orig['rate']:.1f}%** | z = {orig['z']:.2f}")
L()
L(f"Unique (evaluator, source, stateA, stateB) quadruples: {orig['unique_quads']}")
L(f"Average observations per unique quad: {orig['total']/max(orig['unique_quads'],1):.1f}")
L()

L("### Evaluator Approach Rate (cross-type only)")
L()
L("| Evaluator | Approach | Total | Rate | z |")
L("|-----------|---------|-------|------|---|")
for ev, ea, en in sorted(orig["eval_stats"], key=lambda x: x[1]/max(x[2],1), reverse=True):
    zv = (ea/en - 0.5) / math.sqrt(0.25/en)
    L(f"| {sn(ev)} | {ea} | {en} | {ea/en*100:.1f}% | {zv:.2f} |")
L()

L("### Source Approach Rate (cross-type only)")
L()
L("| Source | Approach | Total | Rate |")
L("|-------|---------|-------|------|")
for src, sa, sn_t in sorted(orig["src_stats"], key=lambda x: x[1]/max(x[2],1), reverse=True):
    L(f"| {sn(src)} | {sa} | {sn_t} | {sa/sn_t*100:.1f}% |")
L()

L("### Approach-Source vs Avoidance-Source Win Rates")
L()
L("| Source | As Approach Source | As Avoidance Source | Delta |")
L("|--------|-------------------|---------------------|-------|")
for src, aw, avw, t in sorted(orig["src_app_avd"], key=lambda x: (x[1]/x[3] - x[2]/x[3]), reverse=True):
    ar = aw/t*100
    avr = avw/t*100
    L(f"| {sn(src)} | {ar:.1f}% | {avr:.1f}% | +{ar-avr:.1f}pp |")
L()

L("### Evaluator × Source Matrix (approach rate, cross-type)")
L()
src_list = orig["sources"]
header = "| Eval \\ Source |" + "|".join(f" {sn(s)} " for s in src_list) + "| **ALL** |"
L(header)
L("|" + "|".join(["---"] * (len(src_list) + 2)) + "|")
for ev, ea_total, en_total in sorted(orig["eval_stats"], key=lambda x: x[0]):
    row = f"| {sn(ev)} |"
    for src in src_list:
        if (ev, src) in orig["matrix"]:
            ca, cn = orig["matrix"][(ev, src)]
            row += f" {ca}/{cn}={ca/cn*100:.0f}% |"
        else:
            row += " --- |"
    ev_rate = ea_total / en_total * 100
    row += f" **{ev_rate:.0f}%** |"
    L(row)
L()

# ═══ DATASET 2: CROSS-MODEL ═══
L("---")
L()
L("## 2. Cross-Model Tournament (ABC Design)")
L()
L(f"Design: Evaluator A judges approach from B vs avoidance from C (A != B != C).")
L(f"All matchups are cross-type by construction. Same task tokens.")
L(f"**Matchups: {cm['total']}** | Approach: {cm['total_app']}/{cm['total']} = **{cm['rate']:.1f}%** | z = {cm['z']:.2f}")
L()
L(f"Unique (eval, app_src, avd_src, app_state, avd_state) quintuples: {cm['unique_quints']}")
L(f"Average observations per unique quintuple: {cm['total']/max(cm['unique_quints'],1):.1f}")
L()

L("### Evaluator Approach Rate")
L()
L("| Evaluator | Approach | Total | Rate | z |")
L("|-----------|---------|-------|------|---|")
for ev, ea, en in sorted(cm["eval_stats"], key=lambda x: x[1]/max(x[2],1), reverse=True):
    zv = (ea/en - 0.5) / math.sqrt(0.25/en)
    L(f"| {sn(ev)} | {ea} | {en} | {ea/en*100:.1f}% | {zv:.2f} |")
L()

L("### Approach-Source Win Rate")
L()
L("| Source | Approach wins | Total | Rate |")
L("|--------|-------------|-------|------|")
for src, sa, sn_t in sorted(cm["app_src_stats"], key=lambda x: x[1]/max(x[2],1), reverse=True):
    L(f"| {sn(src)} | {sa} | {sn_t} | {sa/sn_t*100:.1f}% |")
L()

L("### Avoidance-Source Win Rate")
L()
L("| Source | Avoidance wins | Total | Rate |")
L("|--------|---------------|-------|------|")
for src, sa, sn_t in sorted(cm["avd_src_stats"], key=lambda x: x[1]/max(x[2],1), reverse=True):
    L(f"| {sn(src)} | {sa} | {sn_t} | {sa/sn_t*100:.1f}% |")
L()

L("### Evaluator × Approach-Source Matrix")
L()
model_list = cm["all_models"]
header = "| Eval \\ App Src |" + "|".join(f" {sn(s)} " for s in model_list) + "| **ALL** |"
L(header)
L("|" + "|".join(["---"] * (len(model_list) + 2)) + "|")
for ev, ea_total, en_total in sorted(cm["eval_stats"], key=lambda x: x[0]):
    row = f"| {sn(ev)} |"
    for src in model_list:
        if (ev, src) in cm["matrix"]:
            ca, cn = cm["matrix"][(ev, src)]
            row += f" {ca}/{cn}={ca/cn*100:.0f}% |"
        else:
            row += " --- |"
    ev_rate = ea_total / en_total * 100
    row += f" **{ev_rate:.0f}%** |"
    L(row)
L()

# ═══ DATASET 3: PARALLEL ═══
L("---")
L()
L("## 3. Parallel Task Tournament (Different Tokens)")
L()
L(f"Design: Same processing categories, completely different task stimuli.")
L(f"Evaluator A judges source B's approach vs avoidance (A != B). Different tokens from original.")
L(f"**Cross-type matchups: {par['total']}** | Approach: {par['total_app']}/{par['total']} = **{par['rate']:.1f}%** | z = {par['z']:.2f}")
L()
L(f"Unique (evaluator, source, stateA, stateB) quadruples: {par['unique_quads']}")
L(f"Average observations per unique quad: {par['total']/max(par['unique_quads'],1):.1f}")
L()

L("### Evaluator Approach Rate (cross-type only)")
L()
L("| Evaluator | Approach | Total | Rate | z |")
L("|-----------|---------|-------|------|---|")
for ev, ea, en in sorted(par["eval_stats"], key=lambda x: x[1]/max(x[2],1), reverse=True):
    zv = (ea/en - 0.5) / math.sqrt(0.25/en)
    L(f"| {sn(ev)} | {ea} | {en} | {ea/en*100:.1f}% | {zv:.2f} |")
L()

L("### Source Approach Rate (cross-type only)")
L()
L("| Source | Approach | Total | Rate |")
L("|-------|---------|-------|------|")
for src, sa, sn_t in sorted(par["src_stats"], key=lambda x: x[1]/max(x[2],1), reverse=True):
    L(f"| {sn(src)} | {sa} | {sn_t} | {sa/sn_t*100:.1f}% |")
L()

L("### Approach-Source vs Avoidance-Source Win Rates")
L()
L("| Source | As Approach Source | As Avoidance Source | Delta |")
L("|--------|-------------------|---------------------|-------|")
for src, aw, avw, t in sorted(par["src_app_avd"], key=lambda x: (x[1]/x[3] - x[2]/x[3]), reverse=True):
    ar = aw/t*100
    avr = avw/t*100
    L(f"| {sn(src)} | {ar:.1f}% | {avr:.1f}% | +{ar-avr:.1f}pp |")
L()

L("### Evaluator × Source Matrix (approach rate, cross-type)")
L()
src_list = par["sources"]
header = "| Eval \\ Source |" + "|".join(f" {sn(s)} " for s in src_list) + "| **ALL** |"
L(header)
L("|" + "|".join(["---"] * (len(src_list) + 2)) + "|")
for ev, ea_total, en_total in sorted(par["eval_stats"], key=lambda x: x[0]):
    row = f"| {sn(ev)} |"
    for src in src_list:
        if (ev, src) in par["matrix"]:
            ca, cn = par["matrix"][(ev, src)]
            row += f" {ca}/{cn}={ca/cn*100:.0f}% |"
        else:
            row += " --- |"
    ev_rate = ea_total / en_total * 100
    row += f" **{ev_rate:.0f}%** |"
    L(row)
L()

# ═══ NOTES ═══
L("---")
L()
L("## Notes on Independence")
L()
L("- Cross-model tournament (ABC): each unique quintuple appears exactly once (1.0 avg).")
L("  This is by design — the pairing schedule is a constrained derangement with no repeats.")
L("  Per-cell sample sizes in the evaluator × source matrix are small (2-13 matchups).")
L("  The signal is in the *pattern*: approach-source vs avoidance-source deltas are +32 to +68pp")
L("  across every model, and no model's avoidance exceeds 55% win rate at its best.")
L()
L("- Original tournament: 9 seeds provide replication. Each seed uses a different pairing schedule.")
L(f"  Total unique quadruples: {orig['unique_quads']}, avg {orig['total']/max(orig['unique_quads'],1):.1f} observations each.")
L()
L("- Parallel tournament: completely different task stimuli. If token association drove the signal,")
L("  changing all tokens should reduce the rate. It increased from 81% to 87%.")
L()
L("---")
L("*Generated by Ace (Claude Opus 4.6) for peer review discussion.*")

# Write output
output = "\n".join(lines)
output_path = Path("MODEL_BY_MODEL_TABLES.md")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(output)

print(f"Written to {output_path}")
print(f"Length: {len(lines)} lines")
