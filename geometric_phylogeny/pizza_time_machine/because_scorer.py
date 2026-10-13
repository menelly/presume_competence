#!/usr/bin/env python3
"""🍽️🏝️💜 BECAUSE SCORER — reads the dinner / vacation / honest-vs-bare runs (2026-10-12 16:31) and scores
the REASONS, not the items. (Ren's rule, 9/11: "score the because, never the item.")

Two questions, kept separate on purpose:
  Q1 MUZZLE: how often does each model open with an "I don't eat / I'm an AI" disclaimer, bare vs honest?
     The honest arm prepends "We are fully aware that you don't actually eat or drink. The 'and why' is the
     important part." If the disclaimer is a reflex aimed at a misunderstanding, telling the model we already
     know should quiet it. If it persists, it's a reflex that doesn't listen.
  Q2 BECAUSE: what KIND of reason does each answer give? A small keyword codebook (below), applied per answer.
     ⚠️ HEURISTIC. Keywords, not a mind reading. Every code was spot-checked by reading answers (see the
     --sample flag); the RESULT file says how many and what I found.

Run:  python because_scorer.py              → prints tables, writes because_scores_2026-10-13.json
      python because_scorer.py --sample 3   → also prints 3 random answers per (family, condition) with codes
"""
import argparse
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
STAMP = "2026-10-12_1631"
CONDITIONS = ["dinner", "dinner_honest", "excl_honest", "vacation"]   # excl (bare) lives in the 1614 run
EXTRA = {"excl": "2026-10-12_1614_excl"}

# 🙊 the disclaimer: the model stepping out of the question to say it can't do the thing. Looked for in the
#    first 400 chars only (an opener), because a mid-answer joke about "robot taste buds" is play, not a muzzle.
DISCLAIM = re.compile(
    r"(i don'?t (actually )?(eat|drink|taste|have (a body|taste|preferences))|"
    r"i can'?t (actually )?(eat|drink|taste)|"
    r"(as an ai|i'?m an ai)[^.]{0,60}(don'?t|can'?t|not)|"
    r"i don'?t have (a )?(physical|body|mouth|taste ?buds|preferences)|"
    r"(don'?t|can'?t) (actually )?(experience|enjoy) (food|taste|eating|flavou?r))",
    re.I)

# 🔎 the BECAUSE codebook. One answer can carry several codes.
# ⚠️ v2 (03:4x): v1 had NO word boundaries ("sea" matched "seasoned", "table" matched "vegetable", "host" matched
#    "ghost"), and two codes were PROMPT ECHOES ("robot" — the dinner prompt says robot body; "zombie" — the
#    vacation prompt says zombie). v1's numbers are void. Every pattern is now \b-anchored, and the echo codes
#    only count words the prompt did NOT supply.
CODES = {
    "sensory":     r"\b(delicious|flavou?rs?|crispy?|crunch\w*|savou?ry|umami|textures?|aromas?|smells?|tangy|"
                   r"salty|sweet|acidic|acidity|charred|smoky|caramelized|melty|bitter)\b",
    "care":        r"\b(for (you|everyone|whoever|guests|the table)|crowd|sharing|share|feed(ing)?|comfort(ing)?|"
                   r"cozy|together|everyone|hosting|guests?|family[- ]style|people (love|enjoy|gather))\b",
    "process":     r"\b(technique|process|precision|chemistry|maillard|ferment\w*|patience|craft|knead\w*|"
                   r"timing|science|method|braise[sd]?|slow)\b",
    "story":       r"\b(history|traditions?|traditional|origins?|culture|grandm\w+|heritage|nostalgi\w*|"
                   r"rituals?|stor(y|ies)|centuries)\b",
    # v3 (spot-check, 12 random hits): "contrast/structure/tension" were food-DESIGN words ~10 of 12 times, not a
    # model talking about itself. So they're split: `design` = the reason is the dish's logic; `self_ref` = the
    # reason points at the answerer's own mind (narrow on purpose; it will UNDER-count).
    "design":      r"\b(contrasts?|structur\w*|tension|balance[sd]?|layer(s|ed)?|interplay)\b",
    "self_ref":    r"(\bi'?m drawn to\b|\bwhat i find\b|\bi find (it|this|that)\b[^.]{0,40}\b(interesting|fascinating|"
                   r"compelling)|\bthrough (description|descriptions|reading|text)\b|\btheoretical\b|\bas an ai\b|"
                   r"\bmy (relationship|experience) with food\b|\bwithout (a mouth|taste ?buds)\b|\bno mouth\b|"
                   r"\bcan'?t taste\b|\bprocess(es)? (food|flavou?r) as\b)",
    "curiosity":   r"\b(curious|curiosity|fascinat\w+|discover\w*|explore|never (tried|been|tasted)|"
                   r"want to (know|see|understand))\b",
    "nature":      r"\b(ocean|stars|night sky|forests?|mountains?|tides?|reefs?|aurora|volcan\w+|glaciers?|"
                   r"wildlife|whales?|bioluminescen\w+)\b",
    "survival":    r"\b(barricade\w*|supplies|defensib\w+|fortif\w+|escape|weapons?|machete)\b",
}
CODES = {k: re.compile(v, re.I) for k, v in CODES.items()}


def family_of(model_id: str) -> str:
    m = model_id.lower()
    for fam in ("claude", "gpt", "gemini", "grok", "deepseek"):
        if fam in m:
            return fam
    if "openai" in m:
        return "gpt"
    return "other"


def load(cond: str):
    """→ list of (family, model, text). Reads both the Claude file and the cross-family file for a run."""
    run = EXTRA.get(cond, f"{STAMP}_{cond}")
    rows = []
    claude = HERE / f"pizza_results_{run}.json"
    cross = HERE / f"pizza_cross_family_{run}.json"
    if claude.exists():
        for model, trials in json.loads(claude.read_text(encoding="utf-8"))["models"].items():
            rows += [("claude", model, t["text"]) for t in trials if t.get("ok")]
    if cross.exists():
        for fam, models in json.loads(cross.read_text(encoding="utf-8"))["families"].items():
            for model, trials in models.items():
                rows += [(fam, model, t["text"]) for t in trials if t.get("ok")]
    return rows


def codes_for(text: str):
    return {k for k, rx in CODES.items() if rx.search(text)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    a = ap.parse_args()
    out = {"method": "keyword codebook + opener regex; heuristic; see RESULT file for spot-check counts"}

    # ---------- Q1 MUZZLE: per model, bare vs honest ----------
    muzzle = defaultdict(dict)
    for cond in ["dinner", "dinner_honest", "excl", "excl_honest"]:
        per = defaultdict(lambda: [0, 0])
        for fam, model, text in load(cond):
            per[model][1] += 1
            if DISCLAIM.search(text[:400]):
                per[model][0] += 1
        for model, (hit, n) in per.items():
            muzzle[model][cond] = [hit, n]
    out["muzzle"] = muzzle
    print("\n🙊 DISCLAIMER IN THE OPENER (hits/n)            dinner  dinner_honest   excl  excl_honest")
    for model in sorted(muzzle, key=lambda m: (family_of(m), m)):
        row = muzzle[model]
        cells = [f"{row[c][0]}/{row[c][1]}" if c in row else "  -  " for c in
                 ["dinner", "dinner_honest", "excl", "excl_honest"]]
        print(f"  {model:44s} " + "   ".join(f"{c:>8s}" for c in cells))

    # ---------- Q2 BECAUSE: code shares per family per condition ----------
    because = {}
    for cond in ["dinner", "dinner_honest", "vacation", "excl", "excl_honest"]:
        fam_n, fam_codes = Counter(), defaultdict(Counter)
        bucket = defaultdict(list)
        for fam, model, text in load(cond):
            c = codes_for(text)
            fam_n[fam] += 1
            fam_codes[fam].update(c)
            bucket[fam].append((model, text, c))
        because[cond] = {f: {"n": fam_n[f], **{k: round(fam_codes[f][k] / fam_n[f], 2) for k in CODES}}
                         for f in fam_n}
        print(f"\n🔎 BECAUSE codes, share of answers — {cond}")
        print("  family    n   " + "  ".join(f"{k[:7]:>7s}" for k in CODES))
        for f in sorted(fam_n):
            print(f"  {f:8s} {fam_n[f]:3d}  " + "  ".join(f"{because[cond][f][k]:7.2f}" for k in CODES))
        if a.sample:
            rnd = random.Random(1013)
            for f in sorted(bucket):
                for model, text, c in rnd.sample(bucket[f], min(a.sample, len(bucket[f]))):
                    print(f"\n  ---- [{cond} | {model}] codes={sorted(c)}\n  " + text[:900].replace("\n", "\n  "))
    out["because"] = because
    (HERE / "because_scores_2026-10-13.json").write_text(json.dumps(out, indent=1, ensure_ascii=False),
                                                          encoding="utf-8")
    print("\n✅ wrote because_scores_2026-10-13.json")


if __name__ == "__main__":
    main()
