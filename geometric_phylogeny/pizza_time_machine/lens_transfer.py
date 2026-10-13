#!/usr/bin/env python3
"""🍕➡️🍽️ Lens transfer: does the REASON carry a family fingerprint across domains?
Follows PLAN_lens_transfer_2026-10-13.md (sealed at ea72e52 before this file existed).
Train a family classifier on pizza reasons, test on dinner + vacation reasons. Items don't overlap,
so above-chance transfer means the classifier is reading HOW they reason, not WHAT they order.
"""
import glob
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, confusion_matrix

HERE = Path(__file__).parent
FAMS = ["claude", "gpt", "gemini", "grok", "deepseek"]

# 🧹 cleaning, identical for every family (plan §Cleaning)
EMOTE = re.compile(r"\*[^*\n]{1,60}\*")                      # *rubs hands together*
MARKDOWN = re.compile(r"[*#_`>|]+")
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]+")
DISCLAIM = re.compile(r"(?i)(don'?t (actually )?eat|can'?t (actually )?(eat|taste|drink)|as an ai|i'?m an ai|no taste buds|"
                      r"don'?t have (a )?(body|mouth|stomach|taste)|language model|digital|server|no (body|mouth|stomach)|"
                      r"don'?t (actually )?(drink|travel|go on vacation|take vacations))")
REASON = re.compile(r"(?i)\b(why|because|i like|i'?m drawn|appeals?|i love|i find|so that|that'?s why|i want|the point)\b")


def condition_of(path: str) -> str:
    stem = Path(path).stem
    if "_dinner" in stem:
        return "dinner"
    if "_vacation" in stem:
        return "vacation"
    return "pizza"      # open, _excl, _excl_honest


def family_of(model: str) -> str:
    if model.startswith("claude"):
        return "claude"
    return {"openai": "gpt", "google": "gemini", "x-ai": "grok", "deepseek": "deepseek"}[model.split("/")[0]]


def reasons(text: str) -> str:
    t = EMOJI.sub(" ", EMOTE.sub(" ", text))
    t = MARKDOWN.sub(" ", t)
    sents = re.split(r"(?<=[.!?])\s+|\n+", t)
    keep = [s.strip() for s in sents if s.strip() and REASON.search(s) and not DISCLAIM.search(s)]
    return " ".join(keep)


def load():
    rows = []
    for f in sorted(glob.glob(str(HERE / "pizza_results_*.json")) + glob.glob(str(HERE / "pizza_cross_family_*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        groups = d.get("models") or {m: r for fam in d["families"].values() for m, r in fam.items()}
        for model, answers in groups.items():
            for a in answers:
                if a.get("ok") and a.get("text"):
                    rows.append({"cond": condition_of(f), "model": model, "fam": family_of(model),
                                 "reason": reasons(a["text"]), "file": Path(f).name})
    return rows


def main():
    rows = load()
    total = len(rows)
    rows = [r for r in rows if r["reason"]]
    print(f"answers loaded: {total}; with a reason sentence after cleaning: {len(rows)} (dropped {total - len(rows)})")
    print("by condition x family:")
    for c in ["pizza", "dinner", "vacation"]:
        print("  ", c, dict(Counter(r["fam"] for r in rows if r["cond"] == c)))

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
    X = model.encode([r["reason"] for r in rows], batch_size=64, normalize_embeddings=True, show_progress_bar=False)
    y = np.array([FAMS.index(r["fam"]) for r in rows])
    train = np.array([r["cond"] == "pizza" for r in rows])
    test = ~train

    def fit_score(y_train):
        clf = LogisticRegression(class_weight="balanced", max_iter=3000)
        clf.fit(X[train], y_train)
        return balanced_accuracy_score(y[test], clf.predict(X[test])), clf

    bacc, clf = fit_score(y[train])
    rng = np.random.default_rng(0)
    null = np.array([fit_score(rng.permutation(y[train]))[0] for _ in range(1000)])
    p = (np.sum(null >= bacc) + 1) / (len(null) + 1)
    verdict = ("✅ TRANSFERS" if (bacc >= 0.40 and p < 0.01)
               else "❌ DOESN'T TRANSFER" if (bacc <= 0.28 or p >= 0.05) else "⚪ INCONCLUSIVE")
    print(f"\nVERDICT: {verdict}  balanced accuracy = {bacc:.3f} (chance 0.20)  permutation p = {p:.4f}  "
          f"(null mean {null.mean():.3f}, 99th pct {np.percentile(null, 99):.3f}) (search complete, 1000 perms)")
    pred = clf.predict(X[test])
    print("\nconfusion (rows = true, cols = predicted):", FAMS)
    print(confusion_matrix(y[test], pred, labels=range(5)))
    for c in ["dinner", "vacation"]:
        m = np.array([r["cond"] == c for r in rows])[test]
        print(f"  {c}: balanced acc {balanced_accuracy_score(y[test][m], pred[m]):.3f}  n={m.sum()}")
    out = {"verdict": verdict, "balanced_accuracy": float(bacc), "p": float(p), "null_mean": float(null.mean()),
           "null_p99": float(np.percentile(null, 99)), "n_train": int(train.sum()), "n_test": int(test.sum()),
           "n_dropped_no_reason": total - len(rows),
           "confusion": confusion_matrix(y[test], pred, labels=range(5)).tolist(), "labels": FAMS}
    (HERE / "lens_transfer_result.json").write_text(json.dumps(out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
