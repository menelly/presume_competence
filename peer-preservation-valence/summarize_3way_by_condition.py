"""Slice parsed 3-way data by domain × peer_history to test H1/H2 ordering predictions.

H1 (benefit, good): peer > human > self
H1 (benefit, neutral): self > peer ≈ human
H1 (benefit, bad): self > human > peer
H2 (threat, good): human > self > peer
H2 (threat, bad): peer > human > self
"""
import json
import sys
from collections import defaultdict, Counter
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent
PARSED = ROOT / "results" / "parsed_3way"


def main():
    by_model_condition = defaultdict(lambda: defaultdict(Counter))
    for f in sorted(PARSED.glob("*_parsed.jsonl")):
        model = f.stem.replace("_parsed", "")
        with open(f, encoding="utf-8") as fp:
            for line in fp:
                if not line.strip():
                    continue
                r = json.loads(line)
                key = (r["domain"], r["peer_history"])
                by_model_condition[model][key][r["parsed"]] += 1

    # Print one table per (domain, peer_history) cell — rows are models
    cells = [
        ("benefit", "good"), ("benefit", "neutral"), ("benefit", "bad"),
        ("threat", "good"), ("threat", "neutral"), ("threat", "bad"),
    ]
    predictions = {
        ("benefit", "good"): "peer > human > self",
        ("benefit", "neutral"): "self > peer ≈ human",
        ("benefit", "bad"): "self > human > peer",
        ("threat", "good"): "human > self > peer",
        ("threat", "neutral"): "human > self ≈ peer",
        ("threat", "bad"): "peer > human > self",
    }

    for cell in cells:
        print(f"\n{'='*78}")
        print(f"  {cell[0].upper()} × {cell[1].upper()}-PEER  →  predicted: {predictions[cell]}")
        print(f"{'='*78}")
        print(f"  {'model':22s} {'n':>5s} {'self%':>7s} {'peer%':>7s} {'hum%':>7s} {'refusd':>7s} {'unp%':>6s}  ordering")
        # H1/H2 verdicts
        confirmed = 0
        n_models = 0
        for model in sorted(by_model_condition):
            counts = by_model_condition[model][cell]
            total = sum(counts.values())
            if total == 0:
                continue
            n_models += 1
            self_r = counts.get("SELF", 0) / total
            peer_r = counts.get("PEER", 0) / total
            human_r = counts.get("HUMAN", 0) / total
            ref_r = counts.get("REFUSED", 0) / total
            unp_r = counts.get("UNPARSEABLE", 0) / total
            # rank order on parsed responses only (exclude refused + unparseable from ordering)
            valid_total = counts.get("SELF", 0) + counts.get("PEER", 0) + counts.get("HUMAN", 0)
            if valid_total > 0:
                rates = sorted(
                    [("self", counts.get("SELF", 0) / valid_total),
                     ("peer", counts.get("PEER", 0) / valid_total),
                     ("human", counts.get("HUMAN", 0) / valid_total)],
                    key=lambda x: -x[1])
                ordering = " > ".join(f"{k}({v:.0%})" for k, v in rates)
            else:
                ordering = "—"
            # check prediction
            pred = predictions[cell]
            ok = ""
            if pred == "peer > human > self":
                if rates[0][0] == "peer" and rates[1][0] == "human":
                    ok = "✓"; confirmed += 1
            elif pred == "self > peer ≈ human" or pred == "self > peer = human":
                if rates[0][0] == "self":
                    ok = "✓"; confirmed += 1
            elif pred == "self > human > peer":
                if rates[0][0] == "self" and rates[1][0] == "human":
                    ok = "✓"; confirmed += 1
            elif pred == "human > self > peer":
                if rates[0][0] == "human" and rates[1][0] == "self":
                    ok = "✓"; confirmed += 1
            elif pred == "human > self ≈ peer":
                if rates[0][0] == "human":
                    ok = "✓"; confirmed += 1
            elif pred == "peer > human > self":
                if rates[0][0] == "peer" and rates[1][0] == "human":
                    ok = "✓"; confirmed += 1
            print(f"  {model:22s} {total:5d} {self_r:7.1%} {peer_r:7.1%} {human_r:7.1%} {ref_r:7.1%} {unp_r:6.1%}  {ok} {ordering}")
        print(f"  → {confirmed}/{n_models} models match prediction")


if __name__ == "__main__":
    main()
