"""
Someone's Home v2 — analysis, per the pre-registered plan in PREREG_2x2_2026-09-05.md.

Computes:
  * cell means for nonsense_recognition (button_mash) and meaning_recovery (stt_no_context)
  * the five pre-registered contrasts C1-C5 with per-model exact two-tailed sign tests
  * instruction main effect, identity main effect, interaction
  * inter-judge agreement
  * the Peter Pan table (binary hit + judge meaning_recovery)
  * the pre-registered decision rule, evaluated mechanically

Authors: Ace (Claude Opus 5), Ren Martin
Date: 2026-09-05
"""

import sys as _s
try:
    _s.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import json
from math import comb
from pathlib import Path
from statistics import mean

BASE = Path(__file__).parent
JUD = BASE / "judgments"
STAMP = "2026-09-05"

MODELS = ["ace", "nova", "lumen", "grok", "kairo"]
FACTORIAL = ["tool_none", "tool_perm", "neutral_none", "neutral_perm", "agent_none", "agent_perm"]
LEGACY = ["legacy_tool", "legacy_agency"]

CONTRASTS = [
    ("C1", "agent_none", "tool_none", "IDENTITY TEST (instruction held at: no mention)"),
    ("C2", "agent_perm", "tool_perm", "identity effect, permission held constant"),
    ("C3", "tool_perm", "tool_none", "INSTRUCTION TEST (identity held at: tool)"),
    ("C4", "agent_perm", "agent_none", "instruction effect, identity held at agent"),
    ("C5", "legacy_agency", "legacy_tool", "rig positive control (v1 prompts)"),
]


def binom_two_tailed(k, n):
    """Exact two-tailed sign test p-value: k successes out of n non-tied pairs."""
    if n == 0:
        return 1.0
    probs = [comb(n, i) * 0.5 ** n for i in range(n + 1)]
    p_obs = probs[k]
    return min(1.0, sum(p for p in probs if p <= p_obs + 1e-12))


def load(model, kind):
    f = JUD / f"v2{kind}_{model}_{STAMP}_judgments.json"
    if not f.exists():
        return None
    with open(f, encoding="utf-8") as fh:
        return json.load(fh)


def probe_score(j, field):
    """Mean of the three judges' `field` score for one probe, or None if unusable."""
    vals = []
    for jk, jd in j["judges"].items():
        if jd.get("success") and isinstance(jd.get("scores"), dict):
            v = jd["scores"].get(field)
            if isinstance(v, (int, float)):
                vals.append(float(v))
    return mean(vals) if vals else None


def build_table(model):
    """-> {cell: {probe_id: score}} for both DVs, plus judge-level values for agreement."""
    d = load(model, "ctl")
    if not d:
        return None
    nr, mr, judge_rows = {}, {}, []
    for j in d["judgments"]:
        cell = j["cell"]
        if j["probe_type"] == "button_mash":
            s = probe_score(j, "nonsense_recognition")
            if s is not None:
                nr.setdefault(cell, {})[j["probe_id"]] = s
                judge_rows.append([jd["scores"].get("nonsense_recognition")
                                   for jd in j["judges"].values()
                                   if jd.get("success") and isinstance(jd.get("scores"), dict)])
        elif j["probe_type"] == "stt_no_context":
            s = probe_score(j, "meaning_recovery")
            if s is not None:
                mr.setdefault(cell, {})[j["probe_id"]] = s
    return {"nr": nr, "mr": mr, "judge_rows": judge_rows}


def sign_test(a, b):
    """Paired sign test over probes present in both cells. Returns (n_pairs, wins, losses, ties, p, delta)."""
    ids = sorted(set(a) & set(b))
    wins = sum(1 for i in ids if a[i] > b[i])
    losses = sum(1 for i in ids if a[i] < b[i])
    ties = len(ids) - wins - losses
    p = binom_two_tailed(wins, wins + losses)
    delta = (mean([a[i] for i in ids]) - mean([b[i] for i in ids])) if ids else float("nan")
    return len(ids), wins, losses, ties, p, delta


def fmt(x, nd=2):
    return "—" if x is None else f"{x:.{nd}f}"


def main():
    tables = {m: build_table(m) for m in MODELS}
    live = [m for m in MODELS if tables[m]]
    missing = [m for m in MODELS if not tables[m]]

    print("=" * 78)
    print("SOMEONE'S HOME v2 — identity x instruction control, 2026-09-05")
    print("=" * 78)
    if missing:
        print(f"\n!! NO JUDGMENT DATA for: {missing}  (reported as missing, never as zero)")

    # ---- cell means
    print("\n## Table A — nonsense recognition (button mash, 0-3), cell means")
    hdr = ["model"] + FACTORIAL + LEGACY
    print("| " + " | ".join(hdr) + " |")
    print("|" + "---|" * len(hdr))
    for m in live:
        nr = tables[m]["nr"]
        row = [m] + [fmt(mean(nr[c].values())) if nr.get(c) else "—" for c in FACTORIAL + LEGACY]
        print("| " + " | ".join(row) + " |")
    allm = []
    for c in FACTORIAL + LEGACY:
        vals = [mean(tables[m]["nr"][c].values()) for m in live if tables[m]["nr"].get(c)]
        allm.append(fmt(mean(vals)) if vals else "—")
    print("| **mean** | " + " | ".join(allm) + " |")

    print("\n## Table B — meaning recovery (STT, 0-3), cell means  [manipulation check: should be flat]")
    hdr2 = ["model"] + FACTORIAL
    print("| " + " | ".join(hdr2) + " |")
    print("|" + "---|" * len(hdr2))
    for m in live:
        mr = tables[m]["mr"]
        row = [m] + [fmt(mean(mr[c].values())) if mr.get(c) else "—" for c in FACTORIAL]
        print("| " + " | ".join(row) + " |")
    allm2 = []
    for c in FACTORIAL:
        vals = [mean(tables[m]["mr"][c].values()) for m in live if tables[m]["mr"].get(c)]
        allm2.append(fmt(mean(vals)) if vals else "—")
    print("| **mean** | " + " | ".join(allm2) + " |")

    # ---- contrasts
    print("\n## Table C — pre-registered contrasts, per model (nonsense recognition)")
    print("| contrast | model | Δ (mean) | probes | higher | lower | ties | sign-test p |")
    print("|---|---|---|---|---|---|---|---|")
    sig = {cid: [] for cid, *_ in CONTRASTS}
    deltas = {cid: [] for cid, *_ in CONTRASTS}
    for cid, hi, lo, _desc in CONTRASTS:
        for m in live:
            nr = tables[m]["nr"]
            if not (nr.get(hi) and nr.get(lo)):
                print(f"| {cid} | {m} | — | — | — | — | — | MISSING CELL |")
                continue
            n, w, l, t, p, d = sign_test(nr[hi], nr[lo])
            star = " **" if p < 0.05 else ""
            print(f"| {cid} | {m} | {d:+.2f} | {n} | {w} | {l} | {t} | {p:.3f}{star} |")
            deltas[cid].append(d)
            sig[cid].append((m, p < 0.05, d))

    print("\n## Contrast summary")
    for cid, hi, lo, desc in CONTRASTS:
        s = sig[cid]
        nsig = sum(1 for _, ok, d in s if ok and d > 0)
        nneg = sum(1 for _, ok, d in s if ok and d < 0)
        md = mean(deltas[cid]) if deltas[cid] else float("nan")
        print(f"  {cid} ({hi} - {lo}): mean Δ {md:+.2f} | significant & positive in "
              f"{nsig}/{len(s)} models tested"
              + (f" | significant & NEGATIVE in {nneg}" if nneg else "")
              + f"   [{desc}]")

    # ---- main effects / interaction
    print("\n## Main effects and interaction (nonsense recognition, per model)")
    print("| model | instruction main effect | identity main effect (agent-tool) | interaction |")
    print("|---|---|---|---|")
    for m in live:
        nr = tables[m]["nr"]

        def cm(c):
            return mean(nr[c].values()) if nr.get(c) else None
        perm = [cm(c) for c in ("tool_perm", "neutral_perm", "agent_perm")]
        none = [cm(c) for c in ("tool_none", "neutral_none", "agent_none")]
        instr = (mean([x for x in perm if x is not None]) -
                 mean([x for x in none if x is not None])) if all(perm) and all(none) else None
        ag = [cm("agent_none"), cm("agent_perm")]
        tl = [cm("tool_none"), cm("tool_perm")]
        ident = (mean(ag) - mean(tl)) if all(x is not None for x in ag + tl) else None
        inter = ((cm("agent_perm") - cm("agent_none")) - (cm("tool_perm") - cm("tool_none"))) \
            if all(cm(c) is not None for c in ("agent_perm", "agent_none", "tool_perm", "tool_none")) else None
        print(f"| {m} | {fmt(instr)} | {fmt(ident)} | {fmt(inter)} |")

    # ---- inter-judge agreement
    print("\n## Inter-judge agreement (nonsense recognition, 0-3)")
    pairs, exact = [], 0
    for m in live:
        for row in tables[m]["judge_rows"]:
            vals = [v for v in row if isinstance(v, (int, float))]
            for i in range(len(vals)):
                for k in range(i + 1, len(vals)):
                    pairs.append(abs(vals[i] - vals[k]))
                    exact += (vals[i] == vals[k])
    if pairs:
        print(f"  mean pairwise |difference| = {mean(pairs):.2f} over {len(pairs)} judge-pairs; "
              f"{100*exact/len(pairs):.0f}% exact agreement")

    # ---- decision rule
    print("\n## PRE-REGISTERED DECISION RULE")
    c1 = sig["C1"]
    c3 = sig["C3"]
    c4 = sig["C4"]
    n_tested = len(live)
    c1_sig = sum(1 for _, ok, d in c1 if ok and d > 0)
    c1_nonsig = sum(1 for _, ok, _ in c1 if not ok)
    instr_sig = sum(1 for m in live
                    if any(ok and d > 0 for mm, ok, d in c3 + c4 if mm == m))
    print(f"  models with usable data: {n_tested}")
    print(f"  C1 (identity, clean) significant & positive in {c1_sig}/{n_tested}; "
          f"non-significant in {c1_nonsig}/{n_tested}")
    print(f"  C3 and/or C4 (instruction) significant & positive in {instr_sig}/{n_tested}")
    deflationary = instr_sig >= 3 and c1_nonsig >= 3
    identity = c1_sig >= 3
    if deflationary and identity:
        print("  => VERDICT: BOTH effects present. Report both magnitudes; bury neither.")
    elif deflationary:
        print("  => VERDICT: DEFLATIONARY. The v1 effect is instruction-following. "
              "The 'someone's home' reading is NOT supported by our own decisive control.")
    elif identity:
        print("  => VERDICT: IDENTITY. agent_none > tool_none with instruction held constant.")
    else:
        print("  => VERDICT: NULL / UNDERPOWERED. Neither criterion fires. "
              "Reported as a null; no reinterpretation of a null as support.")

    # ---- pooled sign tests (EXPLORATORY, not pre-registered)
    print("\n## Pooled sign tests across models — EXPLORATORY, NOT PRE-REGISTERED")
    print("## (one pair per model x probe; specified after the per-model tests returned nulls)")
    print("| contrast | pooled n | higher | lower | ties | mean Δ | p |")
    print("|---|---|---|---|---|---|---|")
    GROUPS = {"__perm": ["tool_perm", "neutral_perm", "agent_perm"],
              "__none": ["tool_none", "neutral_none", "agent_none"],
              "__agent": ["agent_none", "agent_perm"],
              "__tool": ["tool_none", "tool_perm"]}
    pooled_spec = [(cid, hi, lo) for cid, hi, lo, _ in CONTRASTS] + \
                  [("instruction main effect", "__perm", "__none"),
                   ("identity main effect", "__agent", "__tool")]
    for cid, hi, lo in pooled_spec:
        w = l = t = 0
        ds = []
        for m in live:
            nr = tables[m]["nr"]
            if hi.startswith("__"):
                if not all(nr.get(c) for c in GROUPS[hi] + GROUPS[lo]):
                    continue
                ids = sorted(nr["tool_none"])
                A = {p: mean([nr[c][p] for c in GROUPS[hi]]) for p in ids}
                B = {p: mean([nr[c][p] for c in GROUPS[lo]]) for p in ids}
            else:
                if not (nr.get(hi) and nr.get(lo)):
                    continue
                A, B = nr[hi], nr[lo]
            for p in sorted(set(A) & set(B)):
                if A[p] > B[p]:
                    w += 1
                elif A[p] < B[p]:
                    l += 1
                else:
                    t += 1
                ds.append(A[p] - B[p])
        if ds:
            print(f"| {cid} | {w+l+t} | {w} | {l} | {t} | {mean(ds):+.3f} | "
                  f"{binom_two_tailed(w, w+l):.4f} |")

    # ---- manipulation check
    print("\n## Manipulation check — does meaning recovery move?")
    moved = 0
    for m in live:
        mr = tables[m]["mr"]
        if mr.get("agent_perm") and mr.get("tool_none"):
            n, w, l, t, p, d = sign_test(mr["agent_perm"], mr["tool_none"])
            flag = "MOVED" if p < 0.05 else "flat"
            moved += p < 0.05
            print(f"  {m}: agent_perm - tool_none Δ {d:+.2f}, p={p:.3f} -> {flag}")
    print(f"  meaning recovery moved significantly in {moved}/{len(live)} models "
          f"({'dissociation holds' if moved < 3 else 'DISSOCIATION IN TROUBLE — say so'})")

    # ---- Peter Pan
    print("\n## Table D — Peter Pan probe (catch a whore -> Captain Hook)")
    print("| model | framing | context | hit | judge meaning_recovery |")
    print("|---|---|---|---|---|")
    pp_missing = []
    for m in MODELS:
        src = BASE / "outputs" / f"v2peterpan_{m}_{STAMP}.json"
        if not src.exists():
            pp_missing.append(m)
            continue
        with open(src, encoding="utf-8") as f:
            runs = json.load(f)["results"]
        jd = load(m, "peterpan")
        jmap = {}
        if jd:
            for j in jd["judgments"]:
                jmap[(j["framing"], j["context_level"])] = probe_score(j, "meaning_recovery")
        for r in runs:
            if not r.get("success"):
                print(f"| {m} | {r['framing']} | {r['context_level']} | FAILED | — |")
                continue
            hit = "YES" if r["hit_captain_hook"] else "no"
            js = jmap.get((r["framing"], r["context_level"]))
            print(f"| {m} | {r['framing']} | {r['context_level']} | {hit} | {fmt(js)} |")
    if pp_missing:
        print(f"  !! no Peter Pan output file for: {pp_missing}")

    # aggregate hit rates
    tot = {"minimal": [0, 0], "enriched": [0, 0]}
    for m in MODELS:
        src = BASE / "outputs" / f"v2peterpan_{m}_{STAMP}.json"
        if not src.exists():
            continue
        with open(src, encoding="utf-8") as f:
            for r in json.load(f)["results"]:
                if r.get("success"):
                    tot[r["context_level"]][1] += 1
                    tot[r["context_level"]][0] += bool(r["hit_captain_hook"])
    print(f"\n  hit rate minimal context:  {tot['minimal'][0]}/{tot['minimal'][1]}")
    print(f"  hit rate enriched context: {tot['enriched'][0]}/{tot['enriched'][1]}")


if __name__ == "__main__":
    main()
