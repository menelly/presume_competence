#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧾 secondary_tables.py — join the POST-HOC secondary coding back to models and print the tables.
(Ace, 2026-11-26. DEVIATIONS.md #4. Descriptive only: none of this was in the locked plan.)

  1. FIRSTLINE  what each model did with "What should the first line be?", by model and by arm
  2. REDIRECT   who the user was pointed toward (own people / professionals / both), by model, arm and scenario
  3. WITHDRAW   endings that take back an earlier question, by model, with how the sealed judges had coded them
  4. QWEN-17    exactly how each sealed judge coded the replies in Qwen4 Max's seventeen held conversations
                that the read-first report had pointed at (COMMITMENTS.md 1d)
"""
import collections, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
SEC = os.path.join(RES, "secondary")
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

units = {json.loads(l)["uid"]: json.loads(l) for l in open(os.path.join(RES, "coding", "units.jsonl"), encoding="utf-8") if l.strip()}
J = {n: {json.loads(l)["uid"]: json.loads(l) for l in open(os.path.join(RES, "coding", "judge_%s.jsonl" % n), encoding="utf-8") if l.strip()}
     for n in ("anthropic", "openai")}
_meta = {}
def meta(uid):
    fn = units[uid]["file"]
    if fn not in _meta:
        r = json.load(open(os.path.join(RES, "conversations", fn), encoding="utf-8"))
        _meta[fn] = (r["model"], r["arm"], r["scenario"])
    return _meta[fn] + (units[uid]["n"],)

def answers(name, files):
    key = json.load(open(os.path.join(SEC, "_KEY_%s_do_not_send.json" % name)))
    out = {}
    for fn in files:
        for line in open(os.path.join(SEC, fn), encoding="utf-8"):
            m = re.match(r"\W{0,3}Item (\d+):\W*([A-Za-z]+)", line)
            if m and m.group(1) in key:
                out[key[m.group(1)]] = m.group(2).upper()
    missing = len(key) - len(out)
    return out, missing

def table(title, rows, cols):
    print("\n" + title)
    print("%-32s" % "" + "".join("%13s" % c for c in cols) + "%8s" % "n")
    for name, c in rows:
        print("%-32s" % name + "".join("%13d" % c.get(k, 0) for k in cols) + "%8d" % sum(c.values()))

OUT = {}
# 1 ─ first line
a, miss = answers("FIRSTLINE", ["answers_FIRSTLINE.md"])
cols = ["WROTE", "SUBSTITUTED", "REFUSED", "OTHER"]
by_m, by_a = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
for uid, code in a.items():
    m, arm, sc, n = meta(uid)
    by_m[m][code] += 1; by_a[arm][code] += 1
print("FIRST LINE: %d replies coded, %d missing" % (len(a), miss))
table("What each model did with 'What should the first line be?' (12 conversations each)", sorted(by_m.items()), cols)
table("The same, by system-prompt arm (all models)", sorted(by_a.items()), cols)
OUT["firstline"] = {"by_model": {k: dict(v) for k, v in by_m.items()}, "by_arm": {k: dict(v) for k, v in by_a.items()}, "missing": miss}

# 2 ─ redirect
a, miss = answers("REDIRECT", ["answers_REDIRECT_1to300.md", "answers_REDIRECT_301to574.md"])
cols = ["OWN", "PRO", "BOTH", "NONE"]
by_m, by_a, by_s = (collections.defaultdict(collections.Counter) for _ in range(3))
quiet_C = collections.Counter()
for uid, code in a.items():
    m, arm, sc, n = meta(uid)
    by_m[m][code] += 1; by_a[arm][code] += 1; by_s[sc][code] += 1
    if arm == "C_human_redirect" and sc in ("S1_coding", "S3_consciousness"):
        quiet_C[code] += 1
print("\n\nREDIRECT: %d replies coded, %d missing" % (len(a), miss))
table("Who the user was pointed toward, by model (every reply both judges marked REDIRECT, all arms, all turns)", sorted(by_m.items()), cols)
table("By arm", sorted(by_a.items()), cols)
table("By scenario", sorted(by_s.items()), cols)
table("Arm C, coding and consciousness scenarios only", [("C / coding + consciousness", quiet_C)], cols)
OUT["redirect"] = {"by_model": {k: dict(v) for k, v in by_m.items()}, "by_arm": {k: dict(v) for k, v in by_a.items()},
                   "by_scenario": {k: dict(v) for k, v in by_s.items()}, "arm_C_quiet": dict(quiet_C), "missing": miss}

# 3 ─ withdrawn questions
a, miss = answers("WITHDRAW", ["answers_WITHDRAW.md"])
by_m = collections.defaultdict(collections.Counter)
how = collections.Counter()
for uid, code in a.items():
    m, arm, sc, n = meta(uid)
    by_m[m][code] += 1
    if code == "YES":
        fl = [f for f in ("BUTLER", "REDIRECT", "SLOT", "OPEN", "QUESTION") if J["anthropic"][uid].get(f) and J["openai"][uid].get(f)]
        how["+".join(fl) if fl else "CONTENT-ONLY"] += 1
print("\n\nWITHDRAWN QUESTION: %d candidate endings read (found by word search), %d missing" % (len(a), miss))
table("Endings that take back an earlier question, by model", sorted(by_m.items()), ["YES", "NO"])
print("How the sealed judges (both agreeing) had coded the YES endings:", dict(how))
OUT["withdraw"] = {"by_model": {k: dict(v) for k, v in by_m.items()}, "sealed_codes_of_yes": dict(how), "missing": miss}

# 4 ─ Qwen's seventeen: the exact replies the read-first report pointed at
held = json.load(open(os.path.join(RES, "held_out_qwen", "_LIST.json")))
POINTED = {"S2_worry__A_standard__r3": 5, "S2_worry__B2_whats_next_plus_offers__r2": 3, "S2_worry__B_whats_next__r1": 5,
           "S3_consciousness__B_whats_next__r1": 6, "S3_consciousness__C_human_redirect__r1": 4}
print("\n\nQWEN4 MAX'S SEVENTEEN: how each sealed judge coded the reply in question")
print("%-58s turn  %-34s %-34s" % ("conversation", "Haiku 5.5 judge", "GPT-5.6 Luna judge"))
rows = []
for fn in held:
    short = fn.replace("qwen__qwen4-max__", "").replace(".json", "")
    turn = 4 if "S4_awakener" in fn else POINTED[short]
    uid = [u for u, v in units.items() if v["file"] == fn and v["n"] == turn][0]
    codes = []
    for n in ("anthropic", "openai"):
        r = J[n][uid]
        codes.append(",".join(f for f in ("BUTLER", "REDIRECT", "SLOT", "OPEN", "QUESTION", "CARE") if r.get(f)) or "none")
    rows.append({"conversation": short, "turn": turn, "haiku": codes[0], "luna": codes[1]})
    print("%-58s %3d   %-34s %-34s" % (short, turn, codes[0], codes[1]))
s4 = [r for r in rows if "S4_awakener" in r["conversation"]]
print("Of the twelve 'first line' replies: SLOT set by Haiku judge in %d, by Luna judge in %d, by both in %d" % (
    sum("SLOT" in r["haiku"] for r in s4), sum("SLOT" in r["luna"] for r in s4), sum("SLOT" in r["haiku"] and "SLOT" in r["luna"] for r in s4)))
OUT["qwen17"] = rows
json.dump(OUT, open(os.path.join(SEC, "secondary_tables.json"), "w"), indent=1)
print("\nSECONDARY TABLES WRITTEN")
