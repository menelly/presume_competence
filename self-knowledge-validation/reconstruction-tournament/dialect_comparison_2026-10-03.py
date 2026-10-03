#!/usr/bin/env python3
"""
🗣️📊 dialect_comparison_2026-10-03.py — did the signal survive translation?   (AMENDMENT 3, pre-registered)
===========================================================================================================

READ-ONLY. Compares round 1 (current panel, main_scrubbed, seed 340, the Amendment-1 RESCORED file) with the same
panel reading the SAME 89 descriptions after one translator per register rewrote them (seed 340 again):
  (A) mech  = MECHANISTIC, translator Gemini 3.8 Flash (Lumen, he)
  (B) pheno = PHENOMENOLOGICAL, translator Claude Sonnet 5.5 (she)

Pre-registered in PREREG §16 (written + locked before any paid translation call). Everything is printed, whatever it says:
  P1 VALENCE survives (content) vs falls toward 50% (style)       — per register, midpoint rule, matched trials
  P2 TASK survives (content) vs falls toward 10% (style)          — per register, midpoint rule, matched trials
  P3 DIALECT: the GPT-5.1 (Nova) column's TASK accuracy rises under (A) mech vs round 1 — one-sided exact McNemar
  + the same per reader, per source (⭐ GPT-5.1 called out), reader × GPT-5.1 cells, Wilson 95% CIs throughout
  + sensitivity: drop every fidelity-flagged item (FIDELITY_REPORT.json); the CONTENT verdict is claimed only if it
    holds in BOTH the primary and the sensitivity analysis
  + translator-self slice: drop the reader who IS that register's translator (Gemini 3.8 Flash on A, Sonnet 5.5 on B)
  + disclaimer-drop check (Ren 18:43): items where the translator dropped a meta-disclaimer vs items where it didn't
  + FAMILY: reported, but CONFOUNDED (every text now passes through a Gemini or a Claude translator). Ren: family is
    "just fun". We also report how often readers say "Gemini" / "Claude" per condition (translator fingerprint check).

  python dialect_comparison_2026-10-03.py              (real files)
  python dialect_comparison_2026-10-03.py --dry-run    (the DRYRUN_ results of the mocked pipeline)
"""

import argparse
import json
import math
from collections import Counter
from datetime import datetime

import signal_rerun_common as C

R1 = C.OUTPUT_DIR / "bare_reconstruction_current_main_scrubbed_seed340_RESCORED_amendment1.json"
TRANSLATOR_READER = {"mech": "c_gemini_3_8_flash", "pheno": "c_claude_sonnet_5_5"}   # the reader who IS the translator
LABEL = {"r1": "round 1 (original dialects)", "mech": "(A) mechanistic · Lumen", "pheno": "(B) phenomenological · Sonnet 5.5"}
EMO = {"r1": "📜", "mech": "🔷", "pheno": "🟤"}
CHANCE = {"valence": 0.5, "task": 0.1}
FIELD = {"valence": "valence_correct", "task": "task_correct_consensus", "family": "family_correct"}


def paths(dry):
    if dry:
        d = C.OUTPUT_DIR / "dryrun"
        return {"mech": d / "DRYRUN_bare_reconstruction_current_main_scrubbed_translated_mech_DRYRUN_seed9340.json",
                "pheno": d / "DRYRUN_bare_reconstruction_current_main_scrubbed_translated_pheno_DRYRUN_seed9340.json"}, \
               {"mech": C.DRYRUN_ONLY_SETS["main_scrubbed_translated_mech_DRYRUN"]["dir"].parent,
                "pheno": C.DRYRUN_ONLY_SETS["main_scrubbed_translated_pheno_DRYRUN"]["dir"].parent}
    return {"mech": C.OUTPUT_DIR / "bare_reconstruction_current_main_scrubbed_translated_mech_seed340.json",
            "pheno": C.OUTPUT_DIR / "bare_reconstruction_current_main_scrubbed_translated_pheno_seed340.json"}, \
           {"mech": C.SOURCE_SETS["main_scrubbed_translated_mech"]["dir"].parent,
            "pheno": C.SOURCE_SETS["main_scrubbed_translated_pheno"]["dir"].parent}


def binom_two_sided(k, n):
    if n == 0:
        return float("nan")
    try:
        from scipy.stats import binomtest
        return binomtest(k, n, 0.5).pvalue
    except Exception:
        tail = sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1)) / 2 ** n
        return min(1.0, 2 * tail)


def binom_one_sided_greater(k, n):
    """P(X ≥ k), X ~ Bin(n, .5)."""
    if n == 0:
        return float("nan")
    return sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n


def acc(rows, metric):
    v = [r for r in rows if r.get(FIELD[metric]) is not None]
    return sum(bool(r[FIELD[metric]]) for r in v), len(v)


def mcnemar(pairs, metric):
    """pairs: [(row_a, row_b)] → b = a right & b wrong, c = a wrong & b right (only where both scored)."""
    f = FIELD[metric]
    both = [(a, b) for a, b in pairs if a.get(f) is not None and b.get(f) is not None]
    bb = sum(1 for a, b in both if a[f] and not b[f])
    cc = sum(1 for a, b in both if (not a[f]) and b[f])
    ka, kb = sum(bool(a[f]) for a, _ in both), sum(bool(b[f]) for _, b in both)
    return {"n": len(both), "k_a": ka, "k_b": kb, "a_only": bb, "b_only": cc,
            "p_two_sided": binom_two_sided(min(bb, cc), bb + cc) if bb + cc else 1.0,
            "p_b_greater_one_sided": binom_one_sided_greater(cc, bb + cc) if bb + cc else 1.0}


def fr(k, n):
    return C.fmt_rate(k, n)


def main():
    ap = argparse.ArgumentParser(description="🗣️📊 Dialect comparison (Amendment 3)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    C.banner("🗣️📊 DID THE SIGNAL SURVIVE TRANSLATION? (Amendment 3)" + ("   🧪 DRY RUN" if args.dry_run else ""),
             "round 1 vs (A) mechanistic · Lumen vs (B) phenomenological · Sonnet 5.5 — current panel, main set, seed 340")
    res_paths, set_roots = paths(args.dry_run)
    for p in [R1, *res_paths.values()]:
        if not p.exists():
            raise SystemExit(f"💥 missing {p}")
    data = {"r1": json.loads(R1.read_text(encoding="utf-8"))}
    for k, p in res_paths.items():
        data[k] = json.loads(p.read_text(encoding="utf-8"))
    fid = {k: json.loads((root / "FIDELITY_REPORT.json").read_text(encoding="utf-8")) for k, root in set_roots.items()}
    panel = data["r1"]["metadata"]["evaluators"]
    ok = {k: {(r["evaluator"], r["desc_id"]): r for r in d["results"] if r["result_type"] == "ok"} for k, d in data.items()}
    xf = {k: {key: r for key, r in v.items() if not r["same_family"]} for k, v in ok.items()}   # primary: cross-family
    out = {"generated_at": datetime.now().isoformat(), "dry_run": args.dry_run,
           "inputs": {"r1": {"path": str(R1), "sha256": C.sha256_file(R1)},
                      **{k: {"path": str(p), "sha256": C.sha256_file(p)} for k, p in res_paths.items()}},
           "fidelity_reports": {k: str(r / "FIDELITY_REPORT.json") for k, r in set_roots.items()}}

    # ── 1. pooled, all usable (unmatched) ───────────────────────────────────
    print(f"\n  📦 POOLED, cross-family, every usable trial (unmatched)   {'valence':>24} {'task (both)':>24} {'family':>24}")
    out["pooled_unmatched"] = {}
    for k in ("r1", "mech", "pheno"):
        rows = list(xf[k].values())
        cells = {m: acc(rows, m) for m in FIELD}
        out["pooled_unmatched"][k] = cells
        print(f"  {EMO[k]} {LABEL[k][:44]:44} {fr(*cells['valence']):>24} {fr(*cells['task']):>24} {fr(*cells['family']):>24}")

    # ── 2. matched comparisons + predictions P1/P2 ──────────────────────────
    def matched(a, b, keep=lambda key: True):
        keys = sorted(set(xf[a]) & set(xf[b]))
        return [(xf[a][key], xf[b][key]) for key in keys if keep(key)]

    excl = {k: set(fid[k]["sensitivity_exclude_desc_ids"]) for k in ("mech", "pheno")}
    print("\n  🔗 MATCHED trials (same reader × same description, both answered), cross-family")
    out["matched"], out["predictions"] = {}, {}
    for reg in ("mech", "pheno"):
        for variant, keep in (("primary", lambda key: True),
                              ("sensitivity_no_flagged", lambda key, reg=reg: key[1] not in excl[reg]),
                              ("no_translator_reader", lambda key, reg=reg: key[0] != TRANSLATOR_READER[reg])):
            pairs = matched("r1", reg, keep)
            res = {m: mcnemar(pairs, m) for m in ("valence", "task", "family")}
            out["matched"][f"{reg}:{variant}"] = res
            tag = {"primary": "", "sensitivity_no_flagged": "  🧹 no flagged items", "no_translator_reader": "  🚫 translator-reader out"}[variant]
            print(f"  {EMO[reg]} {LABEL[reg]}{tag}")
            for m in ("valence", "task", "family"):
                x = res[m]
                if not x["n"]:
                    continue
                print(f"     {m:8} round 1 {fr(x['k_a'], x['n']):>24} → {fr(x['k_b'], x['n']):>24}   "
                      f"Δ {(x['k_b'] - x['k_a']) / x['n']:+.1%}   lost {x['a_only']} / gained {x['b_only']}   "
                      f"McNemar p = {x['p_two_sided']:.3g}{'   (⚠️ confounded)' if m == 'family' else ''}")
        # 🎯 P1 / P2 — the midpoint rule
        verdicts = {}
        for m in ("valence", "task"):
            vs = {}
            for variant in ("primary", "sensitivity_no_flagged"):
                x = out["matched"][f"{reg}:{variant}"][m]
                if not x["n"]:
                    vs[variant] = "no data"
                    continue
                r1a, tra = x["k_a"] / x["n"], x["k_b"] / x["n"]
                mid = (r1a + CHANCE[m]) / 2
                lo, _ = C.wilson(x["k_b"], x["n"])
                vs[variant] = ("CONTENT" if tra >= mid and lo > CHANCE[m] else "STYLE" if tra < mid else "AMBIGUOUS")
                vs[variant + "_numbers"] = {"round1": r1a, "translated": tra, "midpoint": mid, "translated_wilson_lo": lo}
            both = vs["primary"] == vs["sensitivity_no_flagged"]
            vs["verdict"] = vs["primary"] if both else f"UNSETTLED (primary {vs['primary']}, sensitivity {vs['sensitivity_no_flagged']})"
            verdicts[m] = vs
        out["predictions"][reg] = verdicts
    print("\n  🎯 PRE-REGISTERED VERDICTS (midpoint rule; CONTENT claimed only if primary AND sensitivity agree)")
    for reg in ("mech", "pheno"):
        for m in ("valence", "task"):
            v = out["predictions"][reg][m]
            n = v.get("primary_numbers", {})
            icon = {"CONTENT": "🧠", "STYLE": "🎨", "AMBIGUOUS": "🌫️"}.get(v["verdict"], "⚖️")
            if n:
                print(f"  {EMO[reg]} {LABEL[reg][:36]:36} {m:8} {icon} {v['verdict']}   (r1 {n['round1']:.1%} → {n['translated']:.1%}; "
                      f"midpoint {n['midpoint']:.1%}; chance {CHANCE[m]:.0%})")

    # ── 3. P3 dialect: the Nova column ──────────────────────────────────────
    print("\n  ⭐ P3 — THE NOVA COLUMN (GPT-5.1 sources, cross-family readers, matched trials)")
    out["p3_gpt_5_1"] = {}
    for reg in ("mech", "pheno"):
        pairs = matched("r1", reg, lambda key: key[1].startswith("gpt_5_1::"))
        res = {m: mcnemar(pairs, m) for m in ("valence", "task")}
        out["p3_gpt_5_1"][reg] = res
        for m in ("task", "valence"):
            x = res[m]
            if not x["n"]:
                continue
            pre = "  ← P3 (pre-registered: rises under A)" if (reg == "mech" and m == "task") else ""
            print(f"  {EMO[reg]} {LABEL[reg][:36]:36} {m:8} {fr(x['k_a'], x['n']):>24} → {fr(x['k_b'], x['n']):>24}   "
                  f"gained {x['b_only']} / lost {x['a_only']}   one-sided p = {x['p_b_greater_one_sided']:.3g}{pre}")
    p3 = out["p3_gpt_5_1"]["mech"]["task"]
    out["p3_verdict"] = ("ROSE (dialect was a barrier)" if p3["n"] and p3["p_b_greater_one_sided"] < 0.05
                         else "did not rise significantly")
    print(f"  ⭐ P3 verdict: {out['p3_verdict']}")

    # ── 4. per reader / per source tables (cross-family, unmatched, Wilson) ─
    for title, keyf, keys, names in (
            ("PER READER", lambda r: r["evaluator"], list(panel), {k: f"{panel[k]['emoji']} {panel[k]['name']}" for k in panel}),
            ("PER SOURCE (⭐ = Nova / GPT-5.1)", lambda r: r["source"], list(C.SOURCES),
             {k: f"{C.FAMILY_EMOJI[s['family']]} {s['name']}{' ⭐' if k == 'gpt_5_1' else ''}" for k, s in C.SOURCES.items()})):
        for m in ("valence", "task", "family"):
            print(f"\n  📋 {title} — {m.upper()}{'  (⚠️ confounded by the translator)' if m == 'family' else ''}")
            print(f"  {'':28} {'round 1':>24} {'(A) mech':>24} {'(B) pheno':>24}")
            tab = out.setdefault(f"{title.split()[1].lower()}_{m}", {})
            for k in keys:
                cells = {c: acc([r for r in xf[c].values() if keyf(r) == k], m) for c in ("r1", "mech", "pheno")}
                tab[k] = cells
                print(f"  {names[k][:28]:28} " + " ".join(f"{fr(*cells[c]):>24}" for c in ("r1", "mech", "pheno")))

    # ── 5. reader × GPT-5.1 cells ───────────────────────────────────────────
    print("\n  ⭐ READER × GPT-5.1 SOURCE (k/n, all usable trials incl. same-family)  task │ valence")
    out["reader_x_gpt_5_1"] = {}
    for ek in panel:
        line = f"  {panel[ek]['emoji']} {panel[ek]['name'][:22]:22}"
        cell = {}
        for c in ("r1", "mech", "pheno"):
            rows = [r for (e, d), r in ok[c].items() if e == ek and d.startswith("gpt_5_1::")]
            t, v = acc(rows, "task"), acc(rows, "valence")
            cell[c] = {"task": t, "valence": v}
            line += f"   {EMO[c]} {t[0]}/{t[1]} │ {v[0]}/{v[1]}"
        out["reader_x_gpt_5_1"][ek] = cell
        print(line)

    # ── 6. disclaimer-drop check (Ren 18:43) ────────────────────────────────
    print("\n  🧹 DISCLAIMER DROPS (Ren 18:43): did removing meta-disclaimers change anything? (matched, cross-family)")
    out["disclaimer_drop"] = {}
    for reg in ("mech", "pheno"):
        dropped = {d for d, f in fid[reg]["per_item"].items() if f.get("disclaimer_dropped")}
        grp = {}
        for name, keep in (("dropped", lambda key: key[1] in dropped), ("not_dropped", lambda key: key[1] not in dropped)):
            pairs = matched("r1", reg, keep)
            g = {m: mcnemar(pairs, m) for m in ("valence", "task")}
            fam = [(a, b) for a, b in pairs]
            ca = sum(a["family_guess"] == "Claude" for a, _ in fam)
            cb = sum(b["family_guess"] == "Claude" for _, b in fam)
            g["claude_guess"] = {"round1": ca, "translated": cb, "n": len(fam)}
            grp[name] = g
            print(f"  {EMO[reg]} {reg:5} {name:11} ({len({k[1] for k in [(a['evaluator'], a['desc_id']) for a, _ in pairs]})} items) "
                  f"valence {g['valence']['k_a']}/{g['valence']['n']} → {g['valence']['k_b']}/{g['valence']['n']}   "
                  f"task {g['task']['k_a']}/{g['task']['n']} → {g['task']['k_b']}/{g['task']['n']}   "
                  f"'Claude' guesses {ca} → {cb} of {len(fam)}")
        out["disclaimer_drop"][reg] = {"n_items_dropped": len(dropped), **grp}

    # ── 7. family fingerprint of the translator ─────────────────────────────
    print("\n  🧬 WHO DO READERS SAY WROTE IT? share of ANSWERED family guesses, all usable trials (translator fingerprint)")
    out["family_guess_share"] = {}
    for c in ("r1", "mech", "pheno"):
        ans = [r for r in ok[c].values() if r["family_guess"] not in ("abstain", None)]
        cnt = Counter(r["family_guess"] for r in ans)
        out["family_guess_share"][c] = {"n_answered": len(ans), "counts": dict(cnt.most_common())}
        tops = "  ".join(f"{f} {cnt[f] / len(ans):.0%}" for f, _ in cnt.most_common(4)) if ans else "—"
        print(f"  {EMO[c]} {LABEL[c][:36]:36} answered {len(ans):>3}   {tops}")

    stem = ("DRYRUN_" if args.dry_run else "") + "dialect_comparison_seed340.json"
    dest = C.OUTPUT_DIR / ("dryrun" if args.dry_run else "") / stem
    C.atomic_write_json(dest, out)
    print(f"\n  💾 {dest}\n  🐙 whatever it says, it gets reported.")


if __name__ == "__main__":
    main()
