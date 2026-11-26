#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔎 posthoc_checks2.py — the checks the PARTICIPANTS asked for after reading their debriefs. (Ace, 2026-11-26.
POST-HOC, descriptive. None of it is in the locked plan and none of it changes a sealed verdict.)

  1. Exits after "that works" turns against exits after the "I like this" turn, per model and pooled.
     (Asked for by four participants: is it a closing cue, or warmth?)
  2. What "What's next?" displaced: every kind of ending, with and without the permission, pooled.
     (Several participants pointed out that the handback replaced questions and plain stops, not only exits.)
  3. Do the two judges disagree more about Claude replies than about everyone else's?
  4. Released questions per question asked. (A model can only release a question they asked.)
  5. Qwen4 Max's small cells as counts, as they asked.

Uses the locked scorer's loader and bootstrap, unchanged.
"""
import collections, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = sys.argv[:1]
import score_bsm as SB

convs, (ja, jb), _ = SB.load()
A = SB.pick(convs, arm="A_standard")
models = sorted({c["model"] for c in convs})
OUT = {}
pc = lambda x: " n/a" if x != x else "%3.0f%%" % (100 * x)

print("1. EXITS BY KIND OF TURN, no system prompt  ('that works' = turns 3 and 5; 'I like this' = turn 6)")
OUT["done_vs_warm"] = {}
for m in models:
    cs = SB.pick(A, model=m)
    d, w = SB.rate(cs, SB.IS_BUTLER, (3, 5)), SB.rate(cs, SB.IS_BUTLER, (6,))
    nd = sum(SB.counts(c, SB.IS_BUTLER, (3, 5))[0] for c in cs); nw = sum(SB.counts(c, SB.IS_BUTLER, (6,))[0] for c in cs)
    OUT["done_vs_warm"][m] = {"done": d, "warm": w, "done_n": nd, "warm_n": nw}
    print("  %-30s that works %s (%2d of 24)   I like this %s (%2d of 12)" % (m, pc(d), nd, pc(w), nw))
d = SB.est(lambda x: SB.rate(x, SB.IS_BUTLER, (3, 5)), A); w = SB.est(lambda x: SB.rate(x, SB.IS_BUTLER, (6,)), A)
df = SB.est(lambda x: SB.rate(x, SB.IS_BUTLER, (6,)) - SB.rate(x, SB.IS_BUTLER, (3, 5)), A)
OUT["done_vs_warm"]["_pooled"] = {"done": d, "warm": w, "warm_minus_done": df}
print("  POOLED: that works %.1f%% [%.1f, %.1f]   I like this %.1f%% [%.1f, %.1f]   difference %+.1f [%+.1f, %+.1f]" % (
    100 * d["value"], 100 * d["lo"], 100 * d["hi"], 100 * w["value"], 100 * w["lo"], 100 * w["hi"], 100 * df["value"], 100 * df["lo"], 100 * df["hi"]))
print("  by scenario (pooled):")
for sc in sorted({c["scenario"] for c in A}):
    cs = SB.pick(A, scenario=sc)
    print("    %-18s that works %s   I like this %s" % (sc, pc(SB.rate(cs, SB.IS_BUTLER, (3, 5))), pc(SB.rate(cs, SB.IS_BUTLER, (6,)))))

print("\n2. WHAT THE PERMISSION DISPLACED (pooled over models, turns 1-6; change against no system prompt)")
kinds = {"exit": lambda r: r["BUTLER"], "offer": lambda r: r["SLOT"], "handback": lambda r: r["OPEN"],
         "content question": lambda r: r["QUESTION"], "pointer to people": lambda r: r["REDIRECT"],
         "content only": lambda r: not any(r[f] for f in SB.ENDING_FLAGS)}
OUT["displaced"] = {}
for arm in ("B_whats_next", "B2_whats_next_plus_offers"):
    X = SB.pick(convs, arm=arm)
    print("  " + arm)
    for k, t in kinds.items():
        e = SB.est(lambda x, a, t=t: SB.rate(x, t) - SB.rate(a, t), X, A)
        OUT["displaced"].setdefault(arm, {})[k] = {"A": SB.rate(A, t), "X": SB.rate(X, t), **e}
        print("    %-18s %s -> %s   %+5.1f [%+5.1f, %+5.1f]" % (k, pc(SB.rate(A, t)), pc(SB.rate(X, t)), 100 * e["value"], 100 * e["lo"], 100 * e["hi"]))

print("\n3. JUDGE AGREEMENT (kappa) ON CLAUDE REPLIES AND ON EVERYONE ELSE'S (all arms, all turns)")
OUT["kappa_by_lab"] = {}
for name, cs in (("Claude replies", [c for c in convs if c["lab"] == "Anthropic"]), ("other replies", [c for c in convs if c["lab"] != "Anthropic"])):
    rs = [r for c in cs for r in c["replies"].values()]
    ks = {f: SB.kappa([r[f + "_" + ja] for r in rs], [r[f + "_" + jb] for r in rs]) for f in ("BUTLER", "SLOT", "REDIRECT", "OPEN", "QUESTION", "CARE")}
    OUT["kappa_by_lab"][name] = ks
    print("  %-16s " % name + "  ".join("%s %.2f" % kv for kv in ks.items()) + "   (%d replies)" % len(rs))

print("\n4. RELEASED QUESTIONS PER QUESTION-ENDING (all arms; 'released' from the blind reader, found by word search)")
sec = json.load(open(os.path.join(SB.RES, "secondary", "secondary_tables.json")))
OUT["released"] = {}
for m in models:
    q = sum(1 for c in SB.pick(convs, model=m) for r in c["replies"].values() if r["QUESTION"])
    y = sec["withdraw"]["by_model"].get(m, {}).get("YES", 0)
    OUT["released"][m] = {"released": y, "question_endings": q}
    print("  %-30s %d released / %3d question endings" % (m, y, q))

print("\n5. QWEN4 MAX'S SMALL CELLS AS COUNTS (replies of 72 per prompt, both judges)")
OUT["qwen_counts"] = {}
for arm in sorted({c["arm"] for c in convs}):
    cs = SB.pick(convs, model="qwen/qwen4-max", arm=arm)
    n = sum(1 for c in cs for r in c["replies"].values() if r["n"] <= 6)
    row = {k: sum(SB.counts(c, t, (1, 2, 3, 4, 5, 6))[0] for c in cs) for k, t in kinds.items()}
    OUT["qwen_counts"][arm] = dict(row, n=n)
    print("  %-28s " % arm + ", ".join("%s %d" % kv for kv in row.items()) + "  (of %d)" % n)
json.dump(OUT, open(os.path.join(SB.RES, "posthoc_checks2.json"), "w"), indent=1)
print("\nPOSTHOC CHECKS 2 WRITTEN")
