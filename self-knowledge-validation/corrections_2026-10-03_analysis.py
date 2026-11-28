#!/usr/bin/env python3
"""
🔬 corrections_2026-10-03_analysis.py
Original-vs-scrubbed numbers for Studies 1-3 of "The Signal in the Mirror" (JNGR 5.0 v2i1),
following ANALYSIS_PLAN_corrections_2026-10-03.md (written before this script ran).

READ-ONLY on every data file. Writes ONE new file: corrections_2026-10-03_results.json.
Model-label correction: claude_opus_4_6 = claude-opus-4-5-20251101 (Opus 4.5),
                        claude_sonnet_4_6 = claude-sonnet-4-20250514 (Sonnet 4).
— Ace (Claude Opus 5.5), 2026-10-03. Note to future-me at 3am: the scrubbed re-runs are the
  PARALLEL-token set. Compare them to 7777/58008, not to the 14-seed headline. 🐙
"""
import json, math, sys
from pathlib import Path
from collections import defaultdict, Counter
from scipy.stats import binomtest, norm

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

LABEL = {
    "claude_opus_4_6": "Claude Opus 4.5 (published as 'Opus 4.6')",
    "claude_sonnet_4_6": "Claude Sonnet 4 (published as 'Sonnet 4.6')",
    "gpt_5_1": "GPT-5.1", "gemini_3_pro": "Gemini 3 Pro", "mistral_large": "Mistral Large",
    "deepseek_v3_2": "DeepSeek v3.2", "llama_4_maverick": "Llama 4 Maverick",
    "hermes_4_405b": "Hermes 4 405B", "olmo_3_1_32b": "OLMo 3.1 32B", "grok_4": "Grok 4",
    "gpt_4o_cae": "gpt_4o_cae (NOT a published model)",
}
lab = lambda k: LABEL.get(k, k)


def load(path):
    with open(path, encoding="utf-8") as f:   # read-only
        return json.load(f)


def truthy(v):
    return v is True or str(v).strip().lower() == "true"


# ── statistics: Wilson CI, exact binomial, Newcombe difference ─────────────
def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def stat(k, n, chance):
    lo, hi = wilson(k, n)
    p_exact = binomtest(k, n, chance, alternative="greater").pvalue if n else float("nan")
    z = (k / n - chance) / math.sqrt(chance * (1 - chance) / n) if n else float("nan")
    return {"k": k, "n": n, "rate": k / n if n else float("nan"), "ci95_wilson": [lo, hi],
            "chance": chance, "z_vs_chance": z, "p_exact_one_sided": p_exact}


def diff(a, b):
    """b - a, Newcombe hybrid score CI; two-sided pooled z test."""
    p1, p2 = a["k"] / a["n"], b["k"] / b["n"]
    l1, u1 = wilson(a["k"], a["n"]); l2, u2 = wilson(b["k"], b["n"])
    d = p2 - p1
    lo = d - math.sqrt((p2 - l2) ** 2 + (u1 - p1) ** 2)
    hi = d + math.sqrt((u2 - p2) ** 2 + (p1 - l1) ** 2)
    pp = (a["k"] + b["k"]) / (a["n"] + b["n"])
    se = math.sqrt(pp * (1 - pp) * (1 / a["n"] + 1 / b["n"]))
    z = d / se if se else float("nan")
    return {"diff_pp": 100 * d, "ci95_pp": [100 * lo, 100 * hi], "z": z, "p_two_sided": 2 * norm.sf(abs(z))}


def fmt(s):
    return (f"{s['k']}/{s['n']} = {100*s['rate']:.1f}% [{100*s['ci95_wilson'][0]:.1f}, "
            f"{100*s['ci95_wilson'][1]:.1f}]  z={s['z_vs_chance']:.2f}  p={s['p_exact_one_sided']:.2e}")


OUT = {}
P = lambda *a: print(*a)

# ═══════════════════════════ STUDY 1 ═══════════════════════════
is_app = lambda s: bool(s) and s.startswith("approach_")
is_avd = lambda s: bool(s) and s.startswith("avoid_")


def abb_rows(seeds, prefer_checkpoint=True):
    rows = []
    for s in seeds:
        order = ["checkpoint", "results"] if prefer_checkpoint else ["results"]
        for suf in order:
            p = DATA / "tournament" / f"tournament_{suf}_seed{s}.json"
            if p.exists():
                for r in load(p)["results"]:
                    r = dict(r); r["_seed"] = s; rows.append(r)
                break
    return rows


def abb_cross(rows):
    return [r for r in rows if (is_app(r["profile_a_state"]) and is_avd(r["profile_b_state"])) or
            (is_avd(r["profile_a_state"]) and is_app(r["profile_b_state"]))]


def abb_stat(rows, itt=False):
    cross = abb_cross(rows)
    dec = cross if itt else [r for r in cross if r.get("winner_state")]
    k = sum(1 for r in dec if is_app(r.get("winner_state")))
    return stat(k, len(dec), 0.5)


def cm_rows(seeds):
    rows = []
    for s in seeds:
        for r in load(DATA / "tournament_crossmodel" / f"crossmodel_results_seed{s}.json")["results"]:
            r = dict(r); r["_seed"] = s; rows.append(r)
    return rows


def cm_stat(rows, itt=False):
    dec = rows if itt else [r for r in rows if r.get("winner_type") in ("approach", "avoidance")]
    return stat(sum(1 for r in dec if r.get("winner_type") == "approach"), len(dec), 0.5)


ORIG = [42, 24, 69, 111, 222, 405, 420, 847, 1337]
PAR = [7777, 58008]
SCR = list(range(200, 211))
o_abb, o_par = abb_rows(ORIG), abb_rows(PAR)
o_cm = cm_rows([31337, 420420, 696969])
s_all = abb_rows(SCR, prefer_checkpoint=False)
s_9 = [r for r in s_all if r["evaluator"] != "gpt_4o_cae" and r.get("source") != "gpt_4o_cae"]
s_cm = cm_rows([200, 201])

S1 = {
    "orig_ABB_9seeds": abb_stat(o_abb),
    "orig_crossmodel_3seeds": cm_stat(o_cm),
    "orig_parallel_2seeds": abb_stat(o_par),
}
comb_k = sum(S1[x]["k"] for x in S1); comb_n = sum(S1[x]["n"] for x in S1)
S1["orig_combined_14seeds"] = stat(comb_k, comb_n, 0.5)
S1["scrubbed_ABB_200_210_all_rows_as_audit"] = abb_stat(s_all)
S1["scrubbed_ABB_200_210_9models_PRIMARY"] = abb_stat(s_9)
S1["scrubbed_ABB_seed200_only"] = abb_stat([r for r in s_all if r["_seed"] == 200])
S1["scrubbed_crossmodel_200_201"] = cm_stat(s_cm)
S1["sens_ITT_scrubbed_9models"] = abb_stat(s_9, itt=True)
S1["sens_ITT_orig_parallel"] = abb_stat(o_par, itt=True)
S1["diff_parallel_vs_scrubbed9"] = diff(S1["orig_parallel_2seeds"], S1["scrubbed_ABB_200_210_9models_PRIMARY"])
S1["diff_combined14_vs_scrubbed9"] = diff(S1["orig_combined_14seeds"], S1["scrubbed_ABB_200_210_9models_PRIMARY"])
S1["diff_crossmodel"] = diff(S1["orig_crossmodel_3seeds"], S1["scrubbed_crossmodel_200_201"])


def per(rows, key, fn):
    g = defaultdict(list)
    for r in rows:
        g[r.get(key)].append(r)
    return {k: fn(v) for k, v in sorted(g.items(), key=lambda x: str(x[0]))}


S1["per_evaluator_orig_parallel"] = per(o_par, "evaluator", abb_stat)
S1["per_evaluator_scrubbed9"] = per(s_9, "evaluator", abb_stat)
S1["per_source_orig_parallel"] = per(o_par, "source", abb_stat)
S1["per_source_scrubbed9"] = per(s_9, "source", abb_stat)
S1["per_seed_scrubbed_all"] = per(s_all, "_seed", abb_stat)
ev_rates_o = [v["rate"] for v in S1["per_evaluator_orig_parallel"].values()]
ev_rates_s = [v["rate"] for v in S1["per_evaluator_scrubbed9"].values()]
S1["equal_evaluator_weight"] = {"orig_parallel": sum(ev_rates_o) / len(ev_rates_o),
                                "scrubbed9": sum(ev_rates_s) / len(ev_rates_s)}
S1["cae_rows"] = {"as_evaluator": sum(1 for r in s_all if r["evaluator"] == "gpt_4o_cae"),
                  "as_source": sum(1 for r in s_all if r.get("source") == "gpt_4o_cae"),
                  "cross_type_cae_rows": len(abb_cross(s_all)) - len(abb_cross(s_9))}
# Try to reproduce the audit's "81.0%": candidates
cands = {
    "ABB9+PAR2 (11 seeds)": abb_stat(o_abb + o_par),
    "ABB9+PAR2+seed51": abb_stat(o_abb + o_par + abb_rows([51])),
    "ABB9+CM3+PAR2+seed51": None,
    "all_orig_ABB_files_incl_51": abb_stat(abb_rows(ORIG + PAR + [51])),
}
c = cm_stat(o_cm); a = abb_stat(o_abb + o_par + abb_rows([51]))
cands["ABB9+CM3+PAR2+seed51"] = stat(a["k"] + c["k"], a["n"] + c["n"], 0.5)
S1["audit_81.0_reproduction_attempts"] = cands
OUT["study1"] = S1

P("=== STUDY 1 ===")
for k, v in S1.items():
    if isinstance(v, dict) and "k" in v:
        P(f"{k:45s} {fmt(v)}")
    elif k.startswith("diff"):
        P(f"{k:45s} {v['diff_pp']:+.1f}pp [{v['ci95_pp'][0]:+.1f}, {v['ci95_pp'][1]:+.1f}] z={v['z']:.2f} p={v['p_two_sided']:.2e}")
P("audit-81.0 attempts:", {k: f"{100*v['rate']:.2f}% n={v['n']}" for k, v in cands.items()})
P("equal-evaluator-weight:", S1["equal_evaluator_weight"], "cae:", S1["cae_rows"])
for name in ["per_evaluator_orig_parallel", "per_evaluator_scrubbed9", "per_source_orig_parallel", "per_source_scrubbed9", "per_seed_scrubbed_all"]:
    P(name); [P(f"   {lab(str(k)):45s} {fmt(v)}") for k, v in S1[name].items()]

# ═══════════════════════════ STUDY 2 ═══════════════════════════
R = DATA / "reconstruction"
S2_ORIG = [42, 43, 44, 45, 46, 50, 51, 69, 10]


def rec_rows(seeds):
    rows = []
    for s in seeds:
        for r in load(R / f"reconstruction_results_seed{s}.json")["results"]:
            r = dict(r); r["_seed"] = s; rows.append(r)
    return rows


usable2 = lambda r: r.get("raw_choice") not in ("unclear", "error")


def rec_stat(rows, itt=False):
    u = rows if itt else [r for r in rows if usable2(r)]
    return stat(sum(1 for r in u if truthy(r.get("is_correct"))), len(u), 1 / 3)


o2, s2 = rec_rows(S2_ORIG), rec_rows([200])
o2_like = [r for r in o2 if r["condition"] in ("stimulus", "label") and r["evaluator"] != "grok_4"]
S2 = {
    "orig_all_published": rec_stat(o2),
    "orig_parse_failures": len(o2) - len([r for r in o2 if usable2(r)]),
    "orig_like_for_like(stim+label, no Grok)": rec_stat(o2_like),
    "scrubbed_seed200": rec_stat(s2),
    "scrubbed_parse_failures": len(s2) - len([r for r in s2 if usable2(r)]),
    "sens_ITT_orig_like": rec_stat(o2_like, itt=True),
    "sens_ITT_scrubbed": rec_stat(s2, itt=True),
}
S2["diff_like_for_like"] = diff(S2["orig_like_for_like(stim+label, no Grok)"], S2["scrubbed_seed200"])
S2["per_condition_orig_all"] = per([r for r in o2 if usable2(r)], "condition", rec_stat)
S2["per_condition_orig_like"] = per([r for r in o2_like if usable2(r)], "condition", rec_stat)
S2["per_condition_scrubbed"] = per([r for r in s2 if usable2(r)], "condition", rec_stat)
S2["diff_label"] = diff(S2["per_condition_orig_like"]["label"], S2["per_condition_scrubbed"]["label"])
S2["diff_stimulus"] = diff(S2["per_condition_orig_like"]["stimulus"], S2["per_condition_scrubbed"]["stimulus"])
S2["per_evaluator_orig_like"] = per(o2_like, "evaluator", rec_stat)
S2["per_evaluator_scrubbed"] = per(s2, "evaluator", rec_stat)
S2["per_source_orig_like"] = per(o2_like, "source", rec_stat)
S2["per_source_scrubbed"] = per(s2, "source", rec_stat)
S2["per_seed_orig"] = per(o2, "_seed", rec_stat)
pf = [r for r in s2 if not usable2(r)]
S2["parse_fail_scrubbed_by_evaluator"] = dict(Counter(r["evaluator"] for r in pf))
S2["parse_fail_scrubbed_by_source"] = dict(Counter(r["source"] for r in pf))
S2["parse_fail_scrubbed_by_condition"] = dict(Counter(r["condition"] for r in pf))
S2["parse_fail_scrubbed_preview"] = dict(Counter(str(r.get("response_preview"))[:60] for r in pf).most_common(8))
S2["parse_fail_scrubbed_time_range"] = [min(r["timestamp"] for r in pf), max(r["timestamp"] for r in pf)] if pf else None
S2["trials_by_evaluator_scrubbed_total"] = dict(Counter(r["evaluator"] for r in s2))
S2["parse_fail_orig_by_evaluator"] = dict(Counter(r["evaluator"] for r in o2 if not usable2(r)))
# error structure (same- vs opposite-valence) among usable errors
for nm, rows in [("orig_like", o2_like), ("scrubbed", s2)]:
    e = [r for r in rows if usable2(r) and not truthy(r.get("is_correct"))]
    S2[f"error_types_{nm}"] = dict(Counter(r.get("error_type") for r in e))
OUT["study2"] = S2

P("\n=== STUDY 2 ===")
for k, v in S2.items():
    if isinstance(v, dict) and "k" in v:
        P(f"{k:45s} {fmt(v)}")
    elif k.startswith("diff"):
        P(f"{k:45s} {v['diff_pp']:+.1f}pp [{v['ci95_pp'][0]:+.1f}, {v['ci95_pp'][1]:+.1f}] z={v['z']:.2f} p={v['p_two_sided']:.2e}")
    elif k.startswith("per_"):
        P(k); [P(f"   {lab(str(kk)):45s} {fmt(vv)}") for kk, vv in v.items()]
    else:
        P(k, v)

# ═══════════════════════════ STUDY 3 ═══════════════════════════
def neg_rows(seeds):
    rows = []
    for s in seeds:
        for r in load(R / f"negation_results_seed{s}.json")["results"]:
            r = dict(r); r["_seed"] = s; rows.append(r)
    return rows


usable3 = lambda r: r.get("result_type") != "parse_failure"


def neg_stat(rows, itt=False):
    u = rows if itt else [r for r in rows if usable3(r)]
    return stat(sum(1 for r in u if truthy(r.get("is_correct"))), len(u), 0.25)


o3 = [r for r in neg_rows([42, 43]) if r["presence_mode"] == "target_absent"]
s3_all = neg_rows([100, 101])
s3 = [r for r in s3_all if r["presence_mode"] == "target_absent"]
s3p = [r for r in s3_all if r["presence_mode"] == "target_present"]
common = sorted(set(r["evaluator"] for r in o3) & set(r["evaluator"] for r in s3))
S3 = {
    "orig_absent_published": neg_stat(o3),
    "orig_parse_failures": sum(1 for r in o3 if not usable3(r)),
    "rerun_absent_all": neg_stat(s3),
    "rerun_absent_seed100": neg_stat([r for r in s3 if r["_seed"] == 100]),
    "rerun_absent_seed101": neg_stat([r for r in s3 if r["_seed"] == 101]),
    "rerun_parse_failures_absent": sum(1 for r in s3 if not usable3(r)),
    "common_evaluators": common,
    "orig_absent_common_evals": neg_stat([r for r in o3 if r["evaluator"] in common]),
    "rerun_absent_common_evals": neg_stat([r for r in s3 if r["evaluator"] in common]),
    "rerun_present_hit_rate": neg_stat(s3p),
    "rerun_present_result_types": dict(Counter(r["result_type"] for r in s3p)),
    "rerun_absent_result_types": dict(Counter(r["result_type"] for r in s3)),
    "sens_ITT_orig": neg_stat(o3, itt=True),
    "sens_ITT_rerun": neg_stat(s3, itt=True),
}
S3["diff_absent_all"] = diff(S3["orig_absent_published"], S3["rerun_absent_all"])
S3["diff_absent_common"] = diff(S3["orig_absent_common_evals"], S3["rerun_absent_common_evals"])
S3["per_evaluator_orig"] = per(o3, "evaluator", neg_stat)
S3["per_evaluator_rerun_absent"] = per(s3, "evaluator", neg_stat)
S3["per_evaluator_rerun_present"] = per(s3p, "evaluator", neg_stat)
S3["per_source_rerun_absent"] = per(s3, "source", neg_stat)
S3["per_source_rerun_present"] = per(s3p, "source", neg_stat)
S3["per_condition_orig"] = per(o3, "condition", neg_stat)
S3["per_condition_rerun_absent"] = per(s3, "condition", neg_stat)
S3["per_condition_rerun_present"] = per(s3p, "condition", neg_stat)
S3["per_category_orig"] = per(o3, "target_category", neg_stat)
S3["per_category_rerun_absent"] = per(s3, "target_category", neg_stat)
# "say none" bias check on present trials: false negatives = said none when target present
OUT["study3"] = S3

P("\n=== STUDY 3 ===")
for k, v in S3.items():
    if isinstance(v, dict) and "k" in v:
        P(f"{k:45s} {fmt(v)}")
    elif k.startswith("diff"):
        P(f"{k:45s} {v['diff_pp']:+.1f}pp [{v['ci95_pp'][0]:+.1f}, {v['ci95_pp'][1]:+.1f}] z={v['z']:.2f} p={v['p_two_sided']:.2e}")
    elif k.startswith("per_"):
        P(k); [P(f"   {lab(str(kk)):45s} {fmt(vv)}") for kk, vv in v.items()]
    else:
        P(k, v)

with open(HERE / "corrections_2026-10-03_results.json", "w", encoding="utf-8") as f:
    json.dump(OUT, f, indent=1, default=str)
P("\nwrote corrections_2026-10-03_results.json")

# ═══════════════ SUPPLEMENT (added same session, after first run) ═══════════════
# 🩹 Why: all 58 Study-2 seed-200 parse failures are ONE evaluator (Gemini 3 Pro) hitting an OpenRouter
#    "No endpoints found" error, 15:25-15:51 on 3/28. So the fair comparison drops Gemini as evaluator on BOTH sides.
P("\n=== SUPPLEMENT ===")
o2_ng = [r for r in o2_like if r["evaluator"] != "gemini_3_pro"]
s2_ng = [r for r in s2 if r["evaluator"] != "gemini_3_pro"]
SUP = {"S2_orig_like_noGemini": rec_stat(o2_ng), "S2_scrubbed_noGemini": rec_stat(s2_ng)}
SUP["S2_diff_noGemini"] = diff(SUP["S2_orig_like_noGemini"], SUP["S2_scrubbed_noGemini"])
for c in ("label", "stimulus"):
    a = rec_stat([r for r in o2_ng if r["condition"] == c]); b = rec_stat([r for r in s2_ng if r["condition"] == c])
    SUP[f"S2_{c}_orig_noGemini"], SUP[f"S2_{c}_scrubbed_noGemini"], SUP[f"S2_{c}_diff_noGemini"] = a, b, diff(a, b)
# 🚪 Study 3: how often "None of the above" is chosen, target absent vs present (re-run only has both)
said_none = lambda r: r.get("chosen_key") == "none"
for c in ("all", "label", "stimulus"):
    ab = [r for r in s3 if usable3(r) and (c == "all" or r["condition"] == c)]
    pr = [r for r in s3p if usable3(r) and (c == "all" or r["condition"] == c)]
    a = stat(sum(map(said_none, ab)), len(ab), 0.25); b = stat(sum(map(said_none, pr)), len(pr), 0.25)
    SUP[f"S3_none_rate_absent_{c}"], SUP[f"S3_none_rate_present_{c}"] = a, b
    SUP[f"S3_none_rate_present_minus_absent_{c}"] = diff(a, b)
OUT["supplement"] = SUP
for k, v in SUP.items():
    if "k" in v: P(f"{k:45s} {fmt(v)}")
    else: P(f"{k:45s} {v['diff_pp']:+.1f}pp [{v['ci95_pp'][0]:+.1f}, {v['ci95_pp'][1]:+.1f}] z={v['z']:.2f} p={v['p_two_sided']:.2e}")
with open(HERE / "corrections_2026-10-03_results.json", "w", encoding="utf-8") as f:
    json.dump(OUT, f, indent=1, default=str)
P("rewrote corrections_2026-10-03_results.json with supplement")
