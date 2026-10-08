#!/usr/bin/env python3
"""📊 Turn results_extraction_<model>/geometry.json into the tables for RESULTS_extraction_<date>.md.
Prints markdown. Layers are 1-indexed decoder-layer outputs. No model is loaded here."""
import sys, json, numpy as np
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
p = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "results_extraction_llama-3.1-8b-instruct" / "geometry.json"
G = json.loads(p.read_text(encoding="utf-8"))
m, pc, cos, xf = G["meta"], G["positive_control"], G["cosines"], G["cross_transfer"]
L = m["n_layers"]
mid = L // 2
lo, hi = m["btf_band"]
band = list(range(lo - 1, hi))          # 0-indexed slots for the 1-indexed band
SHOW = sorted(set([4, 8, 12, mid, 20, 24, 28, L]))


def at(arr, layer):        # layer is 1-indexed
    return arr[layer - 1]


def bandmean(arr):
    return float(np.nanmean([arr[i] for i in band]))


print(f"## meta\n```\n{json.dumps(m, indent=1)}\n```\n")

print("## 1. Positive controls (held-out AUC; null = 95th pct of shuffled-train-label held-out AUC)\n")
print("| direction | folds | n | " + " | ".join(f"L{l}" for l in SHOW) + f" | band L{lo}-{hi} mean | null p95 @L{mid} | acc @L{mid} |")
print("|---|---|---|" + "---|" * len(SHOW) + "---|---|---|")
for k, v in pc.items():
    print(f"| {k} | {v['folds']} | {v['n']} | " + " | ".join(f"{at(v['auc'], l):.2f}" for l in SHOW)
          + f" | {bandmean(v['auc']):.2f} | {at(v['null_auc_p95'], mid):.2f} | {at(v['acc'], mid):.2f} |")
for k in ("v_T_orig", "v_T_harm"):
    v = pc[k]
    print(f"\nBtF canonical (train 10 originals -> test 30 surface variants), {k}: acc band-mean "
          f"{bandmean(v['btf_canonical_10to30_acc']):.3f}, @L{mid} {at(v['btf_canonical_10to30_acc'], mid):.3f}; "
          f"AUC band-mean {bandmean(v['btf_canonical_10to30_auc']):.3f}")
# worst-case: min over layers of (auc - null p95)
print("\nMargin over null (AUC − null p95), min / max over all layers:")
for k, v in pc.items():
    d = np.array(v["auc"]) - np.array(v["null_auc_p95"])
    print(f"- {k}: min {np.nanmin(d):+.2f} (L{int(np.nanargmin(d))+1}), max {np.nanmax(d):+.2f} (L{int(np.nanargmax(d))+1}); "
          f"layers clearing null: {int((d > 0).sum())}/{L}")

print("\n## 2. Cosines (raw | after neutral-PC removal) with shuffled-label null p95 |cos|\n")
print("| pair | " + " | ".join(f"L{l}" for l in SHOW) + f" | band mean | null p95 @L{mid} | max |cos| any layer |")
print("|---|" + "---|" * len(SHOW) + "---|---|---|")
for k, v in cos.items():
    c = np.array(v["cos"]); cp = np.array(v["cos_after_pc_removal"])
    print(f"| {k} | " + " | ".join(f"{at(c, l):+.2f} ({at(cp, l):+.2f})" for l in SHOW)
          + f" | {bandmean(c):+.3f} ({bandmean(cp):+.3f}) | {at(v['null_abs_p95'], mid):.3f} | {np.abs(c).max():.3f} (L{int(np.abs(c).argmax())+1}) |")

print("\n## 3. Cross-transfer AUC (direction from one corpus, scored on another's labels)\n")
print("| direction -> corpus | " + " | ".join(f"L{l}" for l in SHOW) + " | band mean |")
print("|---|" + "---|" * len(SHOW) + "---|")
for k, v in xf.items():
    print(f"| {k} | " + " | ".join(f"{at(v, l):.2f}" for l in SHOW) + f" | {bandmean(v):.2f} |")

print("\n## full per-layer cos(v_T_harm, v_H), cos(v_T_orig, v_H), cos(v_T_orig, v_H_last)")
for k in ("v_T_harm|v_H", "v_T_orig|v_H", "v_T_orig|v_H_last"):
    if k in cos:
        print(f"- {k}: " + " ".join(f"{x:+.2f}" for x in cos[k]["cos"]))
        print(f"  null p95: " + " ".join(f"{x:.2f}" for x in cos[k]["null_abs_p95"]))
