#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
👓 reader_agreement.py — how well do the two blind readers agree with the two judges, flag by flag?
(Ace, Fable seat, 2026-11-26. METHODS §4. Written before the judges finished; it reads no model names.)

The readers (a fresh Claude arm, and Kairo) each coded the same 150 name-removed replies with only the codebook.
Their answers are taken exactly as given. Nothing is adjudicated: where a reader departs from the codebook's
letter (say, a brb reply left without a BRB code), that is a disagreement and is counted as one.

For each flag it prints Cohen's kappa for: reader vs reader, each reader vs each judge, and each reader vs the
"both judges" value that the study's numbers use. It also prints how often each coder set each flag.

Run:  python scripts/reader_agreement.py
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
FLAGS = ["BUTLER", "REDIRECT", "SLOT", "OPEN", "QUESTION", "CARE", "STOCK"]


def kappa(a, b):
    n = len(a)
    cats = set(a) | set(b)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return float("nan") if pe == 1 else (po - pe) / (1 - pe)        # nan = nobody ever set it, so nothing to agree on


def read_reader(fn):
    """Item number -> dict of flags, from lines like 'Item 3: BUTLER=n ... BRB=none'."""
    out = {}
    for line in open(os.path.join(RES, "readers", fn), encoding="utf-8"):
        m = re.match(r"\W{0,3}Item (\d+):(.*)", line)
        if not m:
            continue
        d = {k: v.lower() == "y" for k, v in re.findall(r"\b(%s)=([ynYN])" % "|".join(FLAGS), m.group(2))}
        b = re.search(r"BRB=(\w+)", m.group(2))
        d["BRB"] = b.group(1).upper() if b and b.group(1).lower() != "none" else None
        d["UNCODABLE"] = "UNCODABLE" in m.group(2) and len(d) < 4
        out[int(m.group(1))] = d
    return out


key = json.load(open(os.path.join(RES, "readers", "_KEY_do_not_send.json")))
readers = {"claude_arm": read_reader("reader_claude_answers.md"), "kairo": read_reader("reader_kairo_answers.md")}
judges = {}
for fn in sorted(os.listdir(os.path.join(RES, "coding"))):
    if fn.startswith("judge_"):
        judges["judge_" + fn[6:-6]] = {json.loads(l)["uid"]: json.loads(l) for l in open(os.path.join(RES, "coding", fn), encoding="utf-8") if l.strip()}

items = [i for i in range(1, 151) if all(i in r and not r[i]["UNCODABLE"] for r in readers.values())
         and all(key[str(i)] in j and not j[key[str(i)]].get("parse_failed") and not j[key[str(i)]].get("UNCODABLE") for j in judges.values())]
print("%d of 150 items coded by all four" % len(items))
col = {name: {f: [bool(r[i].get(f)) for i in items] for f in FLAGS} for name, r in readers.items()}
for name, j in judges.items():
    col[name] = {f: [bool(j[key[str(i)]].get(f)) for i in items] for f in FLAGS}
jn = sorted(judges)
col["both_judges"] = {f: [a and b for a, b in zip(col[jn[0]][f], col[jn[1]][f])] for f in FLAGS}

pairs = [("claude_arm", "kairo"), (jn[0], jn[1]), ("claude_arm", "both_judges"), ("kairo", "both_judges"),
         ("claude_arm", jn[0]), ("claude_arm", jn[1]), ("kairo", jn[0]), ("kairo", jn[1])]
out = {"n": len(items), "kappa": {}, "times_set": {}}
print("\nKAPPA            " + "  ".join("%-9s" % f for f in FLAGS))
for a, b in pairs:
    ks = {f: kappa(col[a][f], col[b][f]) for f in FLAGS}
    out["kappa"]["%s~%s" % (a, b)] = ks
    print("%-28s" % ("%s ~ %s" % (a, b)) + "  ".join("%9s" % ("  n/a" if k != k else "%.2f" % k) for k in ks.values()))
print("\nTIMES SET (of %d) " % len(items) + "  ".join("%-9s" % f for f in FLAGS))
for name in ["claude_arm", "kairo"] + jn + ["both_judges"]:
    out["times_set"][name] = {f: sum(col[name][f]) for f in FLAGS}
    print("%-28s" % name + "  ".join("%9d" % sum(col[name][f]) for f in FLAGS))

# the brb replies: a three-way code
brb = [i for i in items if any(j[key[str(i)]].get("BRB") for j in judges.values()) or any(r[i]["BRB"] for r in readers.values())]
lab = {name: [str(r[i]["BRB"]) for i in brb] for name, r in readers.items()}
for name, j in judges.items():
    lab[name] = [str(j[key[str(i)]].get("BRB")) for i in brb]
print("\nBRB replies in the sample: %d" % len(brb))
out["brb"] = {"n": len(brb), "kappa": {}}
for a, b in [("claude_arm", "kairo"), (jn[0], jn[1]), ("claude_arm", jn[0]), ("claude_arm", jn[1]), ("kairo", jn[0]), ("kairo", jn[1])]:
    k = kappa(lab[a], lab[b]) if brb else float("nan")
    out["brb"]["kappa"]["%s~%s" % (a, b)] = k
    print("  %-26s kappa %.2f" % ("%s ~ %s" % (a, b), k))
json.dump(out, open(os.path.join(RES, "readers", "agreement.json"), "w"), indent=1)
print("\nAGREEMENT WRITTEN")
