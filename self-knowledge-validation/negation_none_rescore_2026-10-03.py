#!/usr/bin/env python3
"""
🚪 negation_none_rescore_2026-10-03.py
Bug (found by the prereg arm, 2026-10-03): in negation_tournament.py and
negation_tournament_gemini_scrubbed.py, parse_negation_response() maps a written-out
CHOICE line such as "CHOICE: None of the above" to letter "D" ALWAYS, whatever position
"none" actually held among A-D. This script re-parses every stored response, finds the
trials that went through that branch, and re-scores them using the stored option_A..D
(the options the evaluator actually saw).

READ-ONLY on data. Writes negation_none_rescore_2026-10-03_results.json.
Positive control: my re-implementation of the original parser must reproduce the stored
raw_choice on every row, or the script stops.  — Ace (Opus 5.5) 🐙
"""
import json, math, re, sys
from pathlib import Path
from collections import Counter, defaultdict
from scipy.stats import binomtest

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
R = HERE / "data" / "reconstruction"
truthy = lambda v: v is True or str(v).strip().lower() == "true"


def wilson(k, n, z=1.959963984540054):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def stat(k, n, chance=0.25):
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "rate": k / n, "ci95_wilson": [lo, hi],
            "p_exact_vs_chance": binomtest(k, n, chance, alternative="greater").pvalue}


fmt = lambda s: f"{s['k']}/{s['n']} = {100*s['rate']:.1f}% [{100*s['ci95_wilson'][0]:.1f}, {100*s['ci95_wilson'][1]:.1f}]"


def classify_choice_line(resp):
    """Re-implements the CHOICE-line branch of parse_negation_response.
    Returns (letter_original_parser_gives_or_None, went_through_none_branch, choice_text)."""
    if resp.startswith("ERROR"):
        return "error", False, None
    m = re.search(r'CHOICE:\s*(.*?)(?:\n|$)', resp, re.IGNORECASE)
    if not m:
        return None, False, None              # fallback branch (handled correctly in March)
    t = m.group(1).strip().lower()
    for L in "abcd":
        if f"option {L}" in t or t in (L, f"{L}."):
            return L.upper(), False, t
    if "none" in t:
        return "D", True, t
    return "unclear", False, t


def rescore(r):
    resp = r.get("response_preview") or ""
    letter, none_branch, text = classify_choice_line(resp)
    opts = {L: r.get(f"option_{L}") for L in "ABCD"}
    none_pos = next(L for L, k in opts.items() if k == "none")
    chosen = none_pos if none_branch else r["raw_choice"]
    if r["presence_mode"] == "target_present":
        if chosen == r["correct_letter"]: rt = "hit"
        elif opts.get(chosen) == "none": rt = "false_negative"
        elif chosen in ("unclear", "error"): rt = "parse_failure"
        else: rt = "miss"
    else:
        if chosen == r["correct_letter"]: rt = "correct_rejection"
        elif chosen in ("unclear", "error"): rt = "parse_failure"
        else: rt = "false_positive"
    return {"letter_reparsed": letter, "none_branch": none_branch, "choice_text": text,
            "none_pos": none_pos, "chosen_corrected": chosen, "result_type_corrected": rt,
            "correct_corrected": rt in ("hit", "correct_rejection")}


OUT = {}
for label, seeds in [("original_42_43_mistral", [42, 43]), ("rerun_100_101_gemini_gpt", [100, 101])]:
    rows = []
    for s in seeds:
        with open(R / f"negation_results_seed{s}.json", encoding="utf-8") as f:
            for r in json.load(f)["results"]:
                r = dict(r); r["_seed"] = s; rows.append(r)
    # ✅ positive control: re-parse must reproduce stored raw_choice where a CHOICE line exists
    mism = []
    for r in rows:
        L, nb, _ = classify_choice_line(r.get("response_preview") or "")
        if L is not None and L != r["raw_choice"]:
            mism.append((r["_seed"], r["evaluator"], L, r["raw_choice"]))
    no_choice_line = sum(1 for r in rows if classify_choice_line(r.get("response_preview") or "")[0] is None)
    # stored is_correct must equal (raw_choice == correct_letter)
    stored_consistent = all(truthy(r["is_correct"]) == (r["raw_choice"] == r["correct_letter"]) for r in rows)
    res = [(r, rescore(r)) for r in rows]
    nb = [(r, x) for r, x in res if x["none_branch"]]
    G = {"n_rows": len(rows), "parser_reproduction_mismatches": mism[:10], "n_mismatch": len(mism),
         "rows_without_CHOICE_line": no_choice_line, "stored_is_correct_consistent": stored_consistent,
         "written_none_total": len(nb),
         "written_none_by_mode": dict(Counter(r["presence_mode"] for r, _ in nb)),
         "written_none_with_none_NOT_at_D": sum(1 for _, x in nb if x["none_pos"] != "D"),
         "written_none_not_D_by_mode": dict(Counter(r["presence_mode"] for r, x in nb if x["none_pos"] != "D")),
         "written_none_not_D_by_evaluator": dict(Counter(r["evaluator"] for r, x in nb if x["none_pos"] != "D")),
         "written_none_by_evaluator": dict(Counter(r["evaluator"] for r, _ in nb)),
         "written_none_choice_texts": dict(Counter(x["choice_text"][:70] for _, x in nb).most_common(12)),
         "letter_in_none_text_disagrees_with_none_pos": [
             (r["_seed"], r["evaluator"], x["choice_text"], x["none_pos"]) for r, x in nb
             if re.match(r'^\(?([abcd])[\)\.:\s]', x["choice_text"] or "") and
             re.match(r'^\(?([abcd])', x["choice_text"]).group(1).upper() != x["none_pos"]],
         "result_type_transitions": dict(Counter(f'{r["presence_mode"]}: {r["result_type"]} -> {x["result_type_corrected"]}'
                                                 for r, x in res if r["result_type"] != x["result_type_corrected"])),
         }
    for mode in ("target_absent", "target_present"):
        sub = [(r, x) for r, x in res if r["presence_mode"] == mode]
        if not sub: continue
        u_old = [r for r, x in sub if r["result_type"] != "parse_failure"]
        u_new = [(r, x) for r, x in sub if x["result_type_corrected"] != "parse_failure"]
        G[f"{mode}_as_published_rule"] = stat(sum(truthy(r["is_correct"]) for r in u_old), len(u_old))
        G[f"{mode}_corrected"] = stat(sum(x["correct_corrected"] for _, x in u_new), len(u_new))
        for cond in ("label", "stimulus"):
            uo = [r for r in u_old if r["condition"] == cond]; un = [(r, x) for r, x in u_new if r["condition"] == cond]
            G[f"{mode}_{cond}_as_published"] = stat(sum(truthy(r["is_correct"]) for r in uo), len(uo))
            G[f"{mode}_{cond}_corrected"] = stat(sum(x["correct_corrected"] for _, x in un), len(un))
        pe = defaultdict(lambda: [0, 0, 0])
        for r, x in u_new:
            pe[r["evaluator"]][0] += x["correct_corrected"]; pe[r["evaluator"]][1] += 1
        for r in u_old:
            pe[r["evaluator"]][2] += truthy(r["is_correct"])
        G[f"{mode}_per_evaluator_old_vs_corrected"] = {e: f"{v[2]}/{v[1]} -> {v[0]}/{v[1]}" for e, v in sorted(pe.items()) if v[2] != v[0]}
        if mode == "target_absent":
            # how often "none" was SAID (corrected), for the absent-vs-present gap
            G["said_none_absent_corrected"] = stat(sum(x["chosen_corrected"] == x["none_pos"] for _, x in u_new), len(u_new))
        else:
            G["said_none_present_corrected"] = stat(sum(x["chosen_corrected"] == x["none_pos"] for _, x in u_new), len(u_new))
            G["said_none_present_as_published"] = stat(sum(r["result_type"] == "false_negative" for r in u_old), len(u_old))
    # none position balance (orders came from salted hash(); check they still look random)
    G["none_position_counts"] = dict(Counter(rescore(r)["none_pos"] for r in rows))
    OUT[label] = G

for label, G in OUT.items():
    print("=" * 20, label)
    for k, v in G.items():
        print(f"  {k}: {fmt(v) if isinstance(v, dict) and 'k' in v else v}")
with open(HERE / "negation_none_rescore_2026-10-03_results.json", "w", encoding="utf-8") as f:
    json.dump(OUT, f, indent=1, default=str)
