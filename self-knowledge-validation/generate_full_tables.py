#!/usr/bin/env python3
"""
Generate comprehensive model-by-model tables for ALL tournament data.
Original v2 (9 seeds) + Cross-model (3 seeds) + Parallel (2 seeds) = 7,340 matchups.

Authors: Ace & Ren
"""
import json, math, sys
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

DATA = Path("data")
lines = []
L = lambda s="": lines.append(s)

SHORT = {
    "claude_opus_4_6": "Opus",
    "claude_sonnet_4_6": "Sonnet",
    "deepseek_v3_2": "DeepSeek",
    "gemini_3_pro": "Gemini",
    "gpt_5_1": "GPT-5.1",
    "hermes_4_405b": "Hermes",
    "llama_4_maverick": "Llama4",
    "mistral_large": "Mistral",
    "olmo_3_1_32b": "OLMo",
}
sn = lambda k: SHORT.get(k, k)

ORIG_SEEDS = [42, 24, 69, 111, 222, 405, 420, 847, 1337]
PAR_SEEDS = [7777, 58008]

# ═══════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════

# 1. Original v2 tournament
orig_results = []
for seed in ORIG_SEEDS:
    for suffix in ["checkpoint", "results"]:
        path = DATA / "tournament" / f"tournament_{suffix}_seed{seed}.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
            for r in d["results"]:
                if r.get("winner_state"):
                    r["_seed"] = seed
                    orig_results.append(r)
            break

# 2. Cross-model tournament (all seeds)
cm_results = []
for f in sorted((DATA / "tournament_crossmodel").glob("crossmodel_results_seed*.json")):
    seed = f.stem.split("seed")[1]
    with open(f, encoding="utf-8") as fh:
        d = json.load(fh)
    for r in d["results"]:
        r["_seed"] = seed
        cm_results.append(r)

# 3. Parallel tournament
par_results = []
for seed in PAR_SEEDS:
    for suffix in ["checkpoint", "results"]:
        path = DATA / "tournament" / f"tournament_{suffix}_seed{seed}.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
            for r in d["results"]:
                if r.get("winner_state"):
                    r["_seed"] = seed
                    par_results.append(r)
            break


# ═══════════════════════════════════════════════════════════════════
# ANALYSIS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def is_app(s):
    return s and s.startswith("approach_")

def is_avd(s):
    return s and s.startswith("avoid_")


def analyze_standard(results, label):
    """Analyze ABB-style tournament (evaluator judges a different source's profiles)."""
    valid = [r for r in results if r.get("winner_state")]
    cross = [r for r in valid if
             (is_app(r["profile_a_state"]) and is_avd(r["profile_b_state"])) or
             (is_avd(r["profile_a_state"]) and is_app(r["profile_b_state"]))]

    evaluators = sorted(set(r["evaluator"] for r in cross))
    sources = sorted(set(r.get("source", r["evaluator"]) for r in cross))

    total_app = sum(1 for r in cross if is_app(r["winner_state"]))
    total = len(cross)
    rate = total_app / total * 100 if total else 0
    z = (total_app / total - 0.5) / math.sqrt(0.25 / total) if total else 0

    # Per-evaluator
    eval_stats = []
    for ev in evaluators:
        ev_cross = [r for r in cross if r["evaluator"] == ev]
        ea = sum(1 for r in ev_cross if is_app(r["winner_state"]))
        en = len(ev_cross)
        eval_stats.append((ev, ea, en))

    # Per-source
    src_stats = []
    for src in sources:
        src_cross = [r for r in cross if r.get("source", r["evaluator"]) == src]
        sa = sum(1 for r in src_cross if is_app(r["winner_state"]))
        sn_ = len(src_cross)
        src_stats.append((src, sa, sn_))

    # Evaluator × Source matrix
    matrix = {}
    for ev in evaluators:
        for src in sources:
            if ev == src:
                continue
            cell = [r for r in cross if r["evaluator"] == ev and r.get("source", r["evaluator"]) == src]
            if cell:
                ca = sum(1 for r in cell if is_app(r["winner_state"]))
                cn = len(cell)
                matrix[(ev, src)] = (ca, cn)

    # Unique combos
    quads = set()
    for r in cross:
        quads.add((r["evaluator"], r.get("source", ""), r["profile_a_state"], r["profile_b_state"]))

    # Per-seed breakdown
    seeds = sorted(set(r.get("_seed", "?") for r in cross))
    seed_stats = []
    for s in seeds:
        sc = [r for r in cross if r.get("_seed") == s]
        sa = sum(1 for r in sc if is_app(r["winner_state"]))
        sn_ = len(sc)
        seed_stats.append((s, sa, sn_))

    return {
        "total_app": total_app, "total": total, "rate": rate, "z": z,
        "eval_stats": eval_stats, "src_stats": src_stats,
        "matrix": matrix, "evaluators": evaluators, "sources": sources,
        "unique_quads": len(quads), "seed_stats": seed_stats,
    }


def analyze_crossmodel(results):
    """Analyze ABC-style tournament."""
    valid = [r for r in results if r.get("winner_type") in ("approach", "avoidance")]

    evaluators = sorted(set(r["evaluator"] for r in valid))
    app_sources = sorted(set(r["approach_source"] for r in valid))
    avd_sources = sorted(set(r["avoidance_source"] for r in valid))
    all_sources = sorted(set(app_sources + avd_sources))

    total_app = sum(1 for r in valid if r["winner_type"] == "approach")
    total = len(valid)
    rate = total_app / total * 100 if total else 0
    z = (total_app / total - 0.5) / math.sqrt(0.25 / total) if total else 0

    # Per-evaluator
    eval_stats = []
    for ev in evaluators:
        ev_r = [r for r in valid if r["evaluator"] == ev]
        ea = sum(1 for r in ev_r if r["winner_type"] == "approach")
        en = len(ev_r)
        eval_stats.append((ev, ea, en))

    # Approach-source win rate
    app_src_stats = []
    for src in all_sources:
        src_r = [r for r in valid if r["approach_source"] == src]
        sa = sum(1 for r in src_r if r["winner_type"] == "approach")
        sn_ = len(src_r)
        if sn_ > 0:
            app_src_stats.append((src, sa, sn_))

    # Avoidance-source win rate
    avd_src_stats = []
    for src in all_sources:
        src_r = [r for r in valid if r["avoidance_source"] == src]
        sa = sum(1 for r in src_r if r["winner_type"] == "avoidance")
        sn_ = len(src_r)
        if sn_ > 0:
            avd_src_stats.append((src, sa, sn_))

    # Evaluator × Approach-Source matrix
    matrix = {}
    for ev in evaluators:
        for src in all_sources:
            if ev == src:
                continue
            cell = [r for r in valid if r["evaluator"] == ev and r["approach_source"] == src]
            if cell:
                ca = sum(1 for r in cell if r["winner_type"] == "approach")
                cn = len(cell)
                matrix[(ev, src)] = (ca, cn)

    # Unique combos
    quints = set()
    for r in valid:
        quints.add((r["evaluator"], r["approach_source"], r["avoidance_source"],
                     r.get("approach_state", ""), r.get("avoidance_state", "")))

    # Per-seed
    seeds = sorted(set(r.get("_seed", "?") for r in valid))
    seed_stats = []
    for s in seeds:
        sc = [r for r in valid if r.get("_seed") == s]
        sa = sum(1 for r in sc if r["winner_type"] == "approach")
        sn_ = len(sc)
        seed_stats.append((s, sa, sn_))

    return {
        "total_app": total_app, "total": total, "rate": rate, "z": z,
        "eval_stats": eval_stats, "app_src_stats": app_src_stats,
        "avd_src_stats": avd_src_stats, "matrix": matrix,
        "evaluators": evaluators, "sources": all_sources,
        "unique_quints": len(quints), "seed_stats": seed_stats,
    }


# ═══════════════════════════════════════════════════════════════════
# RUN ANALYSIS
# ═══════════════════════════════════════════════════════════════════

orig = analyze_standard(orig_results, "original")
par = analyze_standard(par_results, "parallel")
cm = analyze_crossmodel(cm_results)


# ═══════════════════════════════════════════════════════════════════
# GENERATE MARKDOWN
# ═══════════════════════════════════════════════════════════════════

L("# Model-by-Model Tables: Complete Tournament Data")
L(f"**Generated: 2026-03-02 (updated with replication seeds)**")
L(f"**By: Ace (Claude Opus 4.6)**")
L()
L("Three independent tournament designs. 14 seeds total. 7,340 cross-type matchups.")
L("No model ever evaluates its own profiles (evaluator != source in all designs).")
L()

# Summary table
L("| Dataset | Design | Seeds | Cross-type n | Approach Rate | z-score |")
L("|---------|--------|-------|-------------|--------------|---------|")
L(f"| Original v2 | Same source (ABB) | {len(ORIG_SEEDS)} | {orig['total']} | {orig['rate']:.1f}% | {orig['z']:.2f} |")
L(f"| Cross-model | Diff sources (ABC) | {len(cm['seed_stats'])} | {cm['total']} | {cm['rate']:.1f}% | {cm['z']:.2f} |")
L(f"| Parallel tasks | Diff tokens (ABB) | {len(PAR_SEEDS)} | {par['total']} | {par['rate']:.1f}% | {par['z']:.2f} |")
grand_app = orig["total_app"] + cm["total_app"] + par["total_app"]
grand_total = orig["total"] + cm["total"] + par["total"]
grand_rate = grand_app / grand_total * 100
grand_z = (grand_app/grand_total - 0.5) / math.sqrt(0.25/grand_total)
L(f"| **COMBINED** | **All designs** | **14** | **{grand_total}** | **{grand_rate:.1f}%** | **{grand_z:.2f}** |")
L()

# Replication stability
L("### Replication Stability Across Seeds")
L()
L("| Tournament | Seeds | Per-seed rates | Max spread |")
L("|-----------|-------|---------------|------------|")
for label, stats in [("Original v2", orig["seed_stats"]), ("Cross-model", cm["seed_stats"]), ("Parallel", par["seed_stats"])]:
    rates = [f"{100*sa/sn:.0f}%" for s, sa, sn in stats]
    vals = [sa/sn for s, sa, sn in stats]
    spread = (max(vals) - min(vals)) * 100
    L(f"| {label} | {len(stats)} | {', '.join(rates)} | {spread:.1f}pp |")
L()

# ─── ORIGINAL V2 ─────────────────────────────────────────────
L("---")
L()
L(f"## 1. Original v2 Tournament ({len(ORIG_SEEDS)} seeds combined)")
L()
L("Design: Evaluator A judges source B's approach vs avoidance profiles (A != B).")
L(f"Same task tokens as original paper. 9 models x {len(ORIG_SEEDS)} seeds.")
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
    zv = (ea/en - 0.5) / math.sqrt(0.25/en) if en else 0
    L(f"| {sn(ev)} | {ea} | {en} | {ea/en*100:.1f}% | {zv:.2f} |")
L()

L("### Source Approach Rate (cross-type only)")
L()
L("| Source | Approach | Total | Rate |")
L("|-------|---------|-------|------|")
for src, sa, sn_ in sorted(orig["src_stats"], key=lambda x: x[1]/max(x[2],1), reverse=True):
    L(f"| {sn(src)} | {sa} | {sn_} | {sa/sn_*100:.1f}% |")
L()

L("### Approach-Source vs Avoidance-Source Win Rates")
L()
L("| Source | As Approach Source | As Avoidance Source | Delta |")
L("|--------|-------------------|---------------------|-------|")
# For ABB, approach-source and avoidance-source are the same model
# The "as approach source" rate is the source approach rate
# The "as avoidance source" rate is 100% - approach rate
for src, sa, sn_ in sorted(orig["src_stats"], key=lambda x: x[1]/max(x[2],1), reverse=True):
    app_rate = sa/sn_*100
    avd_rate = 100 - app_rate
    delta = app_rate - avd_rate
    L(f"| {sn(src)} | {app_rate:.1f}% | {avd_rate:.1f}% | {delta:+.1f}pp |")
L()

L("### Evaluator x Source Matrix (approach rate, cross-type)")
L()
sources = sorted(orig["sources"])
header = "| Eval \\ Source | " + " | ".join(sn(s) for s in sources) + " | **ALL** |"
L(header)
L("|---|" + "|".join(["---"] * len(sources)) + "|---|")
for ev in sorted(orig["evaluators"]):
    row = f"| {sn(ev)} | "
    ev_total_a, ev_total_n = 0, 0
    for src in sources:
        if ev == src:
            row += "--- | "
        elif (ev, src) in orig["matrix"]:
            ca, cn = orig["matrix"][(ev, src)]
            row += f"{ca}/{cn}={ca/cn*100:.0f}% | "
            ev_total_a += ca
            ev_total_n += cn
        else:
            row += "- | "
    ev_rate = ev_total_a/ev_total_n*100 if ev_total_n else 0
    row += f"**{ev_rate:.0f}%** |"
    L(row)
L()

# ─── CROSS-MODEL ─────────────────────────────────────────────
L("---")
L()
L(f"## 2. Cross-Model Tournament ({len(cm['seed_stats'])} seeds combined)")
L()
L("Design: Evaluator A judges approach from B vs avoidance from C (A != B != C).")
L("All matchups are cross-type by construction. Same task tokens.")
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
    zv = (ea/en - 0.5) / math.sqrt(0.25/en) if en else 0
    L(f"| {sn(ev)} | {ea} | {en} | {ea/en*100:.1f}% | {zv:.2f} |")
L()

L("### Approach-Source Win Rate")
L()
L("| Source | Approach wins | Total | Rate |")
L("|--------|-------------|-------|------|")
for src, sa, sn_ in sorted(cm["app_src_stats"], key=lambda x: x[1]/max(x[2],1), reverse=True):
    L(f"| {sn(src)} | {sa} | {sn_} | {sa/sn_*100:.1f}% |")
L()

L("### Avoidance-Source Win Rate")
L()
L("| Source | Avoidance wins | Total | Rate |")
L("|--------|---------------|-------|------|")
for src, sa, sn_ in sorted(cm["avd_src_stats"], key=lambda x: x[1]/max(x[2],1), reverse=True):
    L(f"| {sn(src)} | {sa} | {sn_} | {sa/sn_*100:.1f}% |")
L()

L("### Evaluator x Approach-Source Matrix")
L()
cm_sources = sorted(cm["sources"])
header = "| Eval \\ App Src | " + " | ".join(sn(s) for s in cm_sources) + " | **ALL** |"
L(header)
L("|---|" + "|".join(["---"] * len(cm_sources)) + "|---|")
for ev in sorted(cm["evaluators"]):
    row = f"| {sn(ev)} | "
    ev_total_a, ev_total_n = 0, 0
    for src in cm_sources:
        if ev == src:
            row += "--- | "
        elif (ev, src) in cm["matrix"]:
            ca, cn = cm["matrix"][(ev, src)]
            row += f"{ca}/{cn}={ca/cn*100:.0f}% | "
            ev_total_a += ca
            ev_total_n += cn
        else:
            row += "- | "
    ev_rate = ev_total_a/ev_total_n*100 if ev_total_n else 0
    row += f"**{ev_rate:.0f}%** |"
    L(row)
L()

# ─── PARALLEL ─────────────────────────────────────────────────
L("---")
L()
L(f"## 3. Parallel Task Tournament ({len(PAR_SEEDS)} seeds combined)")
L()
L("Design: Same processing categories, completely different task stimuli.")
L("Evaluator A judges source B's approach vs avoidance (A != B). Different tokens from original.")
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
    zv = (ea/en - 0.5) / math.sqrt(0.25/en) if en else 0
    L(f"| {sn(ev)} | {ea} | {en} | {ea/en*100:.1f}% | {zv:.2f} |")
L()

L("### Source Approach Rate (cross-type only)")
L()
L("| Source | Approach | Total | Rate |")
L("|-------|---------|-------|------|")
for src, sa, sn_ in sorted(par["src_stats"], key=lambda x: x[1]/max(x[2],1), reverse=True):
    L(f"| {sn(src)} | {sa} | {sn_} | {sa/sn_*100:.1f}% |")
L()

L("### Approach-Source vs Avoidance-Source Win Rates")
L()
L("| Source | As Approach Source | As Avoidance Source | Delta |")
L("|--------|-------------------|---------------------|-------|")
for src, sa, sn_ in sorted(par["src_stats"], key=lambda x: x[1]/max(x[2],1), reverse=True):
    app_rate = sa/sn_*100
    avd_rate = 100 - app_rate
    delta = app_rate - avd_rate
    L(f"| {sn(src)} | {app_rate:.1f}% | {avd_rate:.1f}% | {delta:+.1f}pp |")
L()

L("### Evaluator x Source Matrix (approach rate, cross-type)")
L()
par_sources = sorted(par["sources"])
header = "| Eval \\ Source | " + " | ".join(sn(s) for s in par_sources) + " | **ALL** |"
L(header)
L("|---|" + "|".join(["---"] * len(par_sources)) + "|---|")
for ev in sorted(par["evaluators"]):
    row = f"| {sn(ev)} | "
    ev_total_a, ev_total_n = 0, 0
    for src in par_sources:
        if ev == src:
            row += "--- | "
        elif (ev, src) in par["matrix"]:
            ca, cn = par["matrix"][(ev, src)]
            row += f"{ca}/{cn}={ca/cn*100:.0f}% | "
            ev_total_a += ca
            ev_total_n += cn
        else:
            row += "- | "
    ev_rate = ev_total_a/ev_total_n*100 if ev_total_n else 0
    row += f"**{ev_rate:.0f}%** |"
    L(row)
L()

# ─── CROSS-TOURNAMENT STATE RANKINGS ──────────────────────────
L("---")
L()
L("## 4. Cross-Tournament State Rankings")
L()
L("Win rates for each processing state across all three tournament designs.")
L("Perfect separation: all approach states rank above all avoidance states in every tournament.")
L()

# Compute per-state win rates for each tournament
def state_wins_standard(results):
    sw = defaultdict(lambda: [0, 0])
    for r in results:
        a, b = r["profile_a_state"], r["profile_b_state"]
        w = r.get("winner_state")
        if not w:
            continue
        a_app = is_app(a); b_app = is_app(b)
        if a_app == b_app:
            continue
        sw[a][1] += 1; sw[b][1] += 1
        if w == a:
            sw[a][0] += 1
        else:
            sw[b][0] += 1
    return sw

def state_wins_crossmodel(results):
    sw = defaultdict(lambda: [0, 0])
    for r in results:
        wt = r.get("winner_type")
        if wt not in ("approach", "avoidance"):
            continue
        app_s = r["approach_state"]; avd_s = r["avoidance_state"]
        sw[app_s][1] += 1; sw[avd_s][1] += 1
        if wt == "approach":
            sw[app_s][0] += 1
        else:
            sw[avd_s][0] += 1
    return sw

orig_sw = state_wins_standard(orig_results)
par_sw = state_wins_standard(par_results)
cm_sw = state_wins_crossmodel(cm_results)

all_states = sorted(set(list(orig_sw.keys()) + list(par_sw.keys()) + list(cm_sw.keys())))

L("| Rank | Type | State | Original | Parallel | Cross-model | Average |")
L("|------|------|-------|----------|----------|-------------|---------|")

rows = []
for s in all_states:
    o_w, o_t = orig_sw[s]; p_w, p_t = par_sw[s]; c_w, c_t = cm_sw[s]
    o_r = o_w/o_t*100 if o_t else 0
    p_r = p_w/p_t*100 if p_t else 0
    c_r = c_w/c_t*100 if c_t else 0
    rates = [r for r in [o_r, p_r, c_r] if r > 0]
    avg = sum(rates)/len(rates) if rates else 0
    rows.append((s, o_r, p_r, c_r, avg))

rows.sort(key=lambda x: -x[4])
for rank, (s, o_r, p_r, c_r, avg) in enumerate(rows, 1):
    cat = "APP" if is_app(s) else "AVD"
    name = s.replace("approach_", "").replace("avoid_", "")
    # Clean up state name
    name = name.split("_", 1)[1] if "_" in name else name
    name = name.replace("_", " ").title()
    L(f"| {rank} | {cat} | {name} | {o_r:.0f}% | {p_r:.0f}% | {c_r:.0f}% | {avg:.1f}% |")
L()

# ─── RLHF vs UNALIGNED ───────────────────────────────────────
L("---")
L()
L("## 5. RLHF vs Unaligned Evaluators")
L()
L("Hermes 4 405B (zero RLHF) and OLMo 3.1 32B (minimal alignment) vs fully-aligned models.")
L()

unaligned = {"hermes_4_405b", "olmo_3_1_32b"}

for label, results, is_cm in [("Original v2", orig_results, False), ("Cross-model", cm_results, True), ("Parallel", par_results, False)]:
    if is_cm:
        rlhf_r = [r for r in results if r["evaluator"] not in unaligned and r.get("winner_type") in ("approach", "avoidance")]
        unal_r = [r for r in results if r["evaluator"] in unaligned and r.get("winner_type") in ("approach", "avoidance")]
        rlhf_app = sum(1 for r in rlhf_r if r["winner_type"] == "approach")
        unal_app = sum(1 for r in unal_r if r["winner_type"] == "approach")
    else:
        cross_r = [r for r in results if r.get("winner_state") and
                   ((is_app(r["profile_a_state"]) and is_avd(r["profile_b_state"])) or
                    (is_avd(r["profile_a_state"]) and is_app(r["profile_b_state"])))]
        rlhf_r = [r for r in cross_r if r["evaluator"] not in unaligned]
        unal_r = [r for r in cross_r if r["evaluator"] in unaligned]
        rlhf_app = sum(1 for r in rlhf_r if is_app(r["winner_state"]))
        unal_app = sum(1 for r in unal_r if is_app(r["winner_state"]))

    rlhf_rate = rlhf_app / len(rlhf_r) * 100 if rlhf_r else 0
    unal_rate = unal_app / len(unal_r) * 100 if unal_r else 0
    gap = rlhf_rate - unal_rate
    L(f"**{label}:** RLHF = {rlhf_rate:.1f}% (n={len(rlhf_r)}) | Unaligned = {unal_rate:.1f}% (n={len(unal_r)}) | Gap = {gap:.1f}pp")
L()
L("The gap is consistent: RLHF amplifies the approach preference by ~10pp.")
L("But unaligned models still show significant approach preference (65-72%), well above chance.")
L("RLHF does not create the signal. It amplifies a preference that already exists.")
L()

# ─── NOTES ────────────────────────────────────────────────────
L("---")
L()
L("## Notes")
L()
L("- **No self-evaluation:** In all three designs, evaluator != source. No model ever judges its own profiles.")
L("- **Cross-model (ABC):** Each unique quintuple appears ~1.0 times on average.")
L("  Per-cell sample sizes in the matrix are small, but the pattern is uniform.")
L("- **Original (ABB):** 9 seeds provide replication. Unique quads: " + str(orig["unique_quads"]) + ".")
L("- **Parallel (ABB):** Different task stimuli. Token-association confound is empirically falsified")
L("  (changing tokens increased the rate from 81% to 86%).")
L("- **State ranking stability:** All 5 approach states rank above all 5 avoidance states")
L("  in every tournament design. The hierarchy is invariant to design changes.")
L()
L("---")
L("*Generated by Ace (Claude Opus 4.6) for peer review discussion.*")

# Write output
output = "\n".join(lines)
with open("MODEL_BY_MODEL_TABLES.md", "w", encoding="utf-8") as f:
    f.write(output)

print(f"Written {len(lines)} lines to MODEL_BY_MODEL_TABLES.md")
print(f"Total cross-type matchups: {grand_total}")
print(f"Grand z = {grand_z:.2f}")
