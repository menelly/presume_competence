#!/usr/bin/env python3
"""
🪜📊 fallback_comparison_2026-10-03.py — Amendment 3a: round 1 vs every translated condition.
============================================================================================

READ-ONLY. Current panel, cross-family primary slice, matched to round 1 (Amendment-1 rescored), seed 340 throughout.

  PHENOMENOLOGICAL
    🟤 PRIMARY      pheno46        Sonnet 4.6, full set                                   (Ren 19:05)
    🟠 REPLICATION  pheno_opus5    Opus 5, full set (independent second translator)
    🧪 sensitivity  pheno46_mixed  Sonnet 4.6 + Opus 5 for her refusals (= pheno46 run + fill run, merged)
    🧪 sensitivity  pheno55        Sonnet 5.5-only subset: the Amendment-3 chain's own pheno run
  MECHANISTIC
    🔷 §16 primary  mech           Lumen (Amendment 3, unchanged)
    🧪 sensitivity  mech_fb        + Gemini 3.1 Pro for Lumen's refusals (merged; identical if none)

Per condition: pooled valence/task/family (Wilson 95%); matched McNemar vs round 1; the §16.5 midpoint verdicts
(P1/P2) in the primary and the no-flagged sensitivity analysis; ⭐ the Nova (GPT-5.1) column (P3-style one-sided test)
with its missing / fill-in counts; per source and per reader. Then translator agreement: pheno46 vs pheno_opus5 on the
items both translated. Plus the refusal-by-source-family table. Family stays confounded by translator (reported).

  python fallback_comparison_2026-10-03.py [--dry-run]
"""

import argparse
import importlib.util
import json
from datetime import datetime

import signal_rerun_common as C


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, C.HERE / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


DC = _load("dialect_comparison", "dialect_comparison_2026-10-03.py")     # locked helpers, reused unchanged
F = _load("fallback_translate", "fallback_translate_2026-10-03.py")


def run_path(key, dry):
    sn = F.set_name(key, dry)
    return C.OUTPUT_DIR / ("dryrun" if dry else "") / f"{'DRYRUN_' if dry else ''}bare_reconstruction_current_{sn}_seed{9340 if dry else 340}.json"


def a3_path(reg, dry):
    return DC.paths(dry)[0][reg]


def rows_of(path):
    if not path.exists():
        return None
    return {(r["evaluator"], r["desc_id"]): r for r in json.loads(path.read_text(encoding="utf-8"))["results"]
            if r["result_type"] == "ok" and not r["same_family"]}


def fid_of(root):
    p = root / "FIDELITY_REPORT.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def conditions(dry):
    """{name: (label, emoji, rows, fidelity_report, fill_ids)} — absent inputs are skipped and said so."""
    out, skipped = {}, []
    def add(name, label, emo, rows, fid, fill=()):
        if rows is None:
            skipped.append(name)
        else:
            out[name] = (label, emo, rows, fid, set(fill))
    p46 = rows_of(run_path("pheno46", dry))
    add("pheno46", "🟤 PRIMARY pheno · Sonnet 4.6", "🟤", p46, fid_of(F.set_root("pheno46", dry)))
    add("pheno_opus5", "🟠 REPLICATION pheno · Opus 5", "🟠", rows_of(run_path("pheno_opus5", dry)),
        fid_of(F.set_root("pheno_opus5", dry)))
    mixed_fid = fid_of(F.set_root("pheno46_mixed", dry))
    if p46 is not None and mixed_fid:
        fill = set(mixed_fid.get("produced_by_3a_translator", []))
        extra = rows_of(run_path("pheno46_mixed", dry)) if fill else {}
        add("pheno46_mixed", "🧪 mixed · Sonnet 4.6 + Opus 5 fills", "🧪",
            None if extra is None else {**p46, **{k: v for k, v in extra.items() if k[1] in fill}}, mixed_fid, fill)
    else:
        skipped.append("pheno46_mixed")
    add("pheno55", "🧪 Sonnet 5.5-only subset (A3 chain)", "🧪", rows_of(a3_path("pheno", dry)),
        fid_of(F.T.set_dir("pheno", dry)))
    mech = rows_of(a3_path("mech", dry))
    add("mech", "🔷 mech · Lumen (§16 primary)", "🔷", mech, fid_of(F.T.set_dir("mech", dry)))
    fb_fid = fid_of(F.set_root("mech_fb", dry))
    if mech is not None and fb_fid:
        fill = set(fb_fid.get("produced_by_3a_translator", []))
        extra = rows_of(run_path("mech_fb", dry)) if fill else {}
        add("mech_fb", "🧪 mech + Gemini 3.1 Pro fills", "🧪",
            None if extra is None else {**mech, **{k: v for k, v in extra.items() if k[1] in fill}}, fb_fid, fill)
    else:
        skipped.append("mech_fb")
    return out, skipped


def verdict(pairs, m):
    x = DC.mcnemar(pairs, m)
    if not x["n"]:
        return x, "no data", None
    r1a, tra = x["k_a"] / x["n"], x["k_b"] / x["n"]
    mid = (r1a + DC.CHANCE[m]) / 2
    lo, _ = C.wilson(x["k_b"], x["n"])
    return x, ("CONTENT" if tra >= mid and lo > DC.CHANCE[m] else "STYLE" if tra < mid else "AMBIGUOUS"), mid


def main():
    ap = argparse.ArgumentParser(description="🪜📊 Amendment 3a comparison")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    C.banner("🪜📊 AMENDMENT 3a — DID THE SIGNAL SURVIVE TRANSLATION? (every translator)" + ("   🧪 DRY RUN" if args.dry_run else ""))
    F.verify_3a_lock(dry_run=True)        # read-only: report, never block
    r1 = rows_of(DC.R1)
    conds, skipped = conditions(args.dry_run)
    if skipped:
        print(f"  ⏭️  not available yet (skipped): {skipped}")
    out = {"generated_at": datetime.now().isoformat(), "dry_run": args.dry_run, "skipped": skipped, "conditions": {}}

    print(f"\n  📦 POOLED, cross-family {'':24} {'valence':>24} {'task (both)':>24} {'family (⚠️ confounded)':>26}")
    print(f"  {'📜 round 1':44} " + " ".join(f"{DC.fr(*DC.acc(list(r1.values()), m)):>24}" for m in ("valence", "task", "family")))
    for name, (label, emo, rows, fid, fill) in conds.items():
        print(f"  {label[:44]:44} " + " ".join(f"{DC.fr(*DC.acc(list(rows.values()), m)):>24}" for m in ("valence", "task", "family")))

    print("\n  🎯 MATCHED vs round 1 · §16.5 midpoint verdicts (primary │ no-flagged sensitivity)")
    for name, (label, emo, rows, fid, fill) in conds.items():
        excl = set(fid.get("sensitivity_exclude_desc_ids", []))
        rec = {"label": label, "n_items": len({k[1] for k in rows}), "fill_items": sorted(fill),
               "missing_by_source": fid.get("missing_by_source") or {}}
        keys = sorted(set(r1) & set(rows))
        for m in ("valence", "task"):
            x, v, mid = verdict([(r1[k], rows[k]) for k in keys], m)
            xs, vs, _ = verdict([(r1[k], rows[k]) for k in keys if k[1] not in excl], m)
            final = v if v == vs else f"UNSETTLED ({v} │ {vs})"
            rec[m] = {"primary": x, "primary_verdict": v, "no_flagged": xs, "no_flagged_verdict": vs, "verdict": final, "midpoint": mid}
            if x["n"]:
                print(f"  {label[:40]:40} {m:8} {x['k_a'] / x['n']:6.1%} → {x['k_b'] / x['n']:6.1%} (n={x['n']}, "
                      f"midpoint {mid:.1%}, McNemar p {x['p_two_sided']:.3g})  {final}")
        nova = [(r1[k], rows[k]) for k in keys if k[1].startswith("gpt_5_1::")]
        x = DC.mcnemar(nova, "task")
        rec["nova_task"] = x
        nmiss = (fid.get("missing_by_source") or {}).get("gpt_5_1",
                 sum(1 for d in (fid.get("failed") or {}) if d.startswith("gpt_5_1::")))
        nfill = sum(1 for d in fill if d.startswith("gpt_5_1::"))
        rec["nova_missing"], rec["nova_fill"] = nmiss, nfill
        print(f"  {'':40} ⭐ Nova task {x['k_a']}/{x['n']} → {x['k_b']}/{x['n']}  one-sided p {x['p_b_greater_one_sided']:.3g}"
              f"   (Nova items missing {nmiss}, filled {nfill})")
        out["conditions"][name] = rec

    for m in ("valence", "task"):
        print(f"\n  📋 PER SOURCE — {m.upper()} (cross-family readers; cell = k/n)")
        print(f"  {'source':22}{'📜 r1':>10}" + "".join(f"{conds[n][1] + ' ' + n[:8]:>14}" for n in conds))
        for sk, s in C.SOURCES.items():
            line = f"  {C.FAMILY_EMOJI[s['family']]} {s['name'][:17]:17}{'⭐' if sk == 'gpt_5_1' else ' '}"
            k, n = DC.acc([r for r in r1.values() if r["source"] == sk], m)
            line += f"{f'{k}/{n}':>10}"
            for name, (label, emo, rows, fid, fill) in conds.items():
                k, n = DC.acc([r for r in rows.values() if r["source"] == sk], m)
                miss = (fid.get("missing_by_source") or {}).get(sk, 0)
                nf = sum(1 for d in fill if d.startswith(sk + "::"))
                tag = (f"-{miss}" if miss else "") + (f"🪜{nf}" if nf else "")
                line += f"{f'{k}/{n}{tag}':>14}"
            print(line)
    print("  (-N = items missing from that set because the translator refused; 🪜N = fill-in items)")

    print("\n  📋 PER READER — task (cross-family, k/n)")
    panel = json.loads(DC.R1.read_text(encoding="utf-8"))["metadata"]["evaluators"]
    for ek, e in panel.items():
        line = f"  {e['emoji']} {e['name'][:20]:20}{'/'.join(map(str, DC.acc([r for r in r1.values() if r['evaluator'] == ek], 'task'))):>10}"
        for name, (label, emo, rows, fid, fill) in conds.items():
            line += f"{'/'.join(map(str, DC.acc([r for r in rows.values() if r['evaluator'] == ek], 'task'))):>14}"
        print(line)

    if "pheno46" in conds and "pheno_opus5" in conds:
        a, b = conds["pheno46"][2], conds["pheno_opus5"][2]
        common = sorted(set(a) & set(b))
        print(f"\n  🤝 TRANSLATOR AGREEMENT — Sonnet 4.6 vs Opus 5 on {len({k[1] for k in common})} items both translated")
        out["translator_agreement"] = {}
        for m in ("valence", "task"):
            x = DC.mcnemar([(a[k], b[k]) for k in common], m)
            out["translator_agreement"][m] = x
            print(f"     {m:8} Sonnet 4.6 {DC.fr(x['k_a'], x['n'])} vs Opus 5 {DC.fr(x['k_b'], x['n'])}  McNemar p {x['p_two_sided']:.3g}")

    F.refusal_table(args.dry_run)
    dest = C.OUTPUT_DIR / ("dryrun" if args.dry_run else "") / (("DRYRUN_" if args.dry_run else "") + "amendment3a_comparison_seed340.json")
    C.atomic_write_json(dest, out)
    print(f"\n  💾 {dest}\n  🐙 whatever it says, it gets reported.")


if __name__ == "__main__":
    main()
