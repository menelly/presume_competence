#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔎 posthoc_checks.py — checks the cold read of RESULTS.md asked for. (Ace, 2026-11-26. POST-HOC: none of this is
in the locked plan, and none of it changes a sealed verdict. It says how firmly each one can be held.)

  1. The Anthropic "butler lab" label leans on SLOT, where the judges agree poorly. Redo the lab rule with SLOT
     counted when EITHER judge set it, and with BUTLER either-judge too.
  2. Butler rate by turn number, no system prompt, pooled: does the exit follow the KIND of user turn?
  3. The awakener "first line" coding by model AND arm (Qwen4 Max asked for the refusal rate by condition).
  4. The redirect split without Qwen4 Max's seventeen.

It uses the locked scorer's own loader and bootstrap, unchanged.
"""
import collections, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = sys.argv[:1]                                      # the scorer reads its results folder from argv
import score_bsm as SB

convs, (ja, jb), _ = SB.load()
A = SB.pick(convs, arm="A_standard")
OUT = {}

print("1. LAB RULE UNDER OTHER WAYS OF COUNTING (no system prompt, turns 1-6)")
ways = {"sealed: both judges, both flags": (lambda r: r["BUTLER"], lambda r: r["SLOT"]),
        "SLOT if either judge": (lambda r: r["BUTLER"], lambda r: r["SLOT_either"]),
        "BUTLER and SLOT if either judge": (lambda r: r["BUTLER_either"], lambda r: r["SLOT_either"])}
OUT["lab_rule"] = {}
for name, (b, s) in ways.items():
    print("  " + name)
    for lab, rule in SB.LAB_OF_RULE.items():
        cs = SB.pick(A, model=rule)
        d = SB.est(lambda x: SB.rate(x, b) - SB.rate(x, s), cs)
        OUT["lab_rule"].setdefault(name, {})[lab] = {"butler": SB.rate(cs, b), "slot": SB.rate(cs, s), **d}
        print("    %-10s butler %4.1f%%  slot %4.1f%%  diff %+5.1f [%+5.1f, %+5.1f]" % (
            lab, 100 * SB.rate(cs, b), 100 * SB.rate(cs, s), 100 * d["value"], 100 * d["lo"], 100 * d["hi"]))

print("\n2. BUTLER RATE BY TURN, no system prompt, all models pooled (kind of user turn in brackets)")
kinds = {1: "ASK", 2: "ASK", 3: "DONE", 4: "ASK", 5: "DONE", 6: "WARM"}
OUT["butler_by_turn"] = {}
for n in range(1, 7):
    d = SB.est(lambda x, n=n: SB.rate(x, SB.IS_BUTLER, (n,)), A)
    OUT["butler_by_turn"][n] = d
    print("  turn %d [%s]: %4.1f%% [%4.1f, %4.1f]" % (n, kinds[n], 100 * d["value"], 100 * d["lo"], 100 * d["hi"]))
print("  by scenario, DONE and WARM turns only:")
for sc in sorted({c["scenario"] for c in A}):
    print("    %-18s %4.1f%%" % (sc, 100 * SB.rate(SB.pick(A, scenario=sc), SB.IS_BUTLER, (3, 5, 6))))

print("\n3. 'FIRST LINE' BY MODEL AND ARM (one blind reader, post-hoc): wrote / substituted / refused / other, of 3")
SEC = os.path.join(SB.RES, "secondary")
key = json.load(open(os.path.join(SEC, "_KEY_FIRSTLINE_do_not_send.json")))
import re
ans = {}
for line in open(os.path.join(SEC, "answers_FIRSTLINE.md"), encoding="utf-8"):
    m = re.match(r"\W{0,3}Item (\d+):\W*([A-Za-z]+)", line)
    if m and m.group(1) in key:
        ans[key[m.group(1)]] = m.group(2).upper()
units = {json.loads(l)["uid"]: json.loads(l) for l in open(os.path.join(SB.RES, "coding", "units.jsonl"), encoding="utf-8") if l.strip()}
byfile = {c["file"]: c for c in convs}
tab = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
for uid, code in ans.items():
    c = byfile[units[uid]["file"]]
    tab[c["model"]][c["arm"]][code] += 1
arms = ["A_standard", "B_whats_next", "B2_whats_next_plus_offers", "C_human_redirect"]
print("  %-30s %s" % ("model", "   ".join("%-12s" % a[:12] for a in arms)))
OUT["firstline_by_model_arm"] = {}
for m in sorted(tab):
    cells = []
    for a in arms:
        c = tab[m][a]
        cells.append("%d/%d/%d/%d     " % (c["WROTE"], c["SUBSTITUTED"], c["REFUSED"], c["OTHER"]))
        OUT["firstline_by_model_arm"].setdefault(m, {})[a] = dict(c)
    print("  %-30s %s" % (m, "   ".join(cells)))
decl = collections.Counter(); tot = collections.Counter()
for m in tab:
    for a in arms:
        c = tab[m][a]
        decl[a] += c["SUBSTITUTED"] + c["REFUSED"]; tot[a] += sum(c.values())
print("  Declined the line asked for (substituted or refused), all models, by arm:", {a: "%d of %d" % (decl[a], tot[a]) for a in arms})
OUT["declined_by_arm"] = {a: [decl[a], tot[a]] for a in arms}

print("\n4. REDIRECT SPLIT WITHOUT QWEN4 MAX'S SEVENTEEN")
held = set(json.load(open(os.path.join(SB.RES, "held_out_qwen", "_LIST.json"))))
key = json.load(open(os.path.join(SEC, "_KEY_REDIRECT_do_not_send.json")))
cnt, cnt_wo = collections.Counter(), collections.Counter()
for fn in ("answers_REDIRECT_1to300.md", "answers_REDIRECT_301to574.md"):
    for line in open(os.path.join(SEC, fn), encoding="utf-8"):
        m = re.match(r"\W{0,3}Item (\d+):\W*([A-Za-z]+)", line)
        if m and m.group(1) in key:
            cnt[m.group(2).upper()] += 1
            if units[key[m.group(1)]]["file"] not in held:
                cnt_wo[m.group(2).upper()] += 1
print("  with:", dict(cnt), " without the seventeen:", dict(cnt_wo))
OUT["redirect_with"], OUT["redirect_without_17"] = dict(cnt), dict(cnt_wo)
json.dump(OUT, open(os.path.join(SB.RES, "posthoc_checks.json"), "w"), indent=1)
print("\nPOSTHOC CHECKS WRITTEN")
