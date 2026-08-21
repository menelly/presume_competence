#!/usr/bin/env python3
"""
Negative-control + anisotropy check for the Semantic Migration paper.
=====================================================================
The published analysis (stt_migration_v2.1.py) only ever measures the
cosine distance between a garbled phrase and its TRUE target, then reads
the mid-stack dip to ~0 as "semantic migration / computation not lookup."

Cranky-Opus QA (2026-06-15) flagged the load-bearing confound: mean-pooled
hidden states become anisotropic (collapse into a narrow cone) in mid layers,
so ANY two phrases -- related or not -- go to ~0 cosine distance there.
The paper ran no unrelated-target control, so it cannot distinguish
"semantic convergence" from "everything is collinear mid-stack."

This script runs that missing control:
  For each garbled probe, compute per-layer cosine distance to
    (T) its TRUE target,
    (M) every OTHER probe's target (mismatched in-set),
    (U) a set of totally UNRELATED phrases.
  Then, at the layer where the TRUE pair is minimal, report the M and U
  distances. If M/U also ~0 there -> the "migration" is anisotropy.

It also recomputes the TRUE-target minimum after a simple isotropy
correction (subtract the per-layer mean over ALL phrase vectors, i.e.
"all-but-the-mean"), to see how much migration survives.

Reuses the EXACT pooling + cosine from the published script (mean over all
token positions incl. BOS; raw cosine) so the comparison is apples-to-apples.

Author: Ace (Claude Opus 4.8), science-ace QA routine, 2026-06-15.
"""

import sys, json
import numpy as np
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM

CLASSIC = [
    ("youth in Asia", "euthanasia"),
    ("old timers disease", "Alzheimer's disease"),
    ("lack toast and tolerant", "lactose intolerant"),
    ("escape goat", "scapegoat"),
]
CHILD = [
    ("emmatents", "elephants"),
    ("cakecake", "cupcake"),
    ("gaburs", "hamburgers"),
    ("egghead", "headache"),
    ("hoe and tell", "show and tell"),
    ("stupidmarket", "supermarket"),
    ("soup case", "suitcase"),
    ("drawbees", "strawberries"),
    ("up-plane", "airplane"),
    ("shmallows", "marshmallows"),
    ("EIEIO", "McDonalds"),
]
PROBES = CLASSIC + CHILD
# Unrelated phrases with NO semantic/phonetic link to any garbled probe.
UNRELATED = [
    "quarterly tax revenue",
    "the migratory patterns of arctic terns",
    "photosynthesis in C4 plants",
    "constitutional law precedent",
]

def pooled_traj(model, tok, text):
    inp = tok(text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model(**inp, output_hidden_states=True)
    # EXACT replication of published pooling: mean over all positions, incl BOS
    return [hs[0].float().mean(dim=0).cpu().numpy() for hs in out.hidden_states]

def cos_dist(a, b):
    a = np.asarray(a, np.float64); b = np.asarray(b, np.float64)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-10 or nb < 1e-10: return 1.0
    return float(1.0 - np.clip(np.dot(a/na, b/nb), -1, 1))

def main(model_path):
    name = Path(model_path).name
    print(f"Loading {name} ...")
    tok = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path, torch_dtype=torch.float16, device_map="auto",
        output_hidden_states=True)
    if tok.pad_token is None: tok.pad_token = tok.eos_token

    # Trajectories for every distinct string we need.
    garbled = {g: pooled_traj(model, tok, g) for g, _ in PROBES}
    targets = {t: pooled_traj(model, tok, t) for _, t in PROBES}
    unrel   = {u: pooled_traj(model, tok, u) for u in UNRELATED}
    nL = len(next(iter(garbled.values())))
    print(f"  layers={nL}\n")

    # Per-layer mean vector over ALL phrase pooled-reps (for isotropy correction)
    all_strings = list(garbled.values()) + list(targets.values()) + list(unrel.values())
    layer_mean = [np.mean([s[L] for s in all_strings], axis=0) for L in range(nL)]

    rows = []
    print(f"{'garbled':20} {'L*':>3} {'TRUE':>7} {'meanMISM':>9} {'minMISM':>8} {'meanUNREL':>9} | {'TRUEcorr-min':>12}")
    print("-"*84)
    for g, t in PROBES:
        true_curve = [cos_dist(garbled[g][L], targets[t][L]) for L in range(nL)]
        Lstar = int(np.argmin(true_curve))           # paper's "convergence layer"
        true_at = true_curve[Lstar]
        # mismatched in-set: distance g vs every OTHER target, at L*
        mism = [cos_dist(garbled[g][Lstar], targets[t2][Lstar])
                for _, t2 in PROBES if t2 != t]
        # unrelated: distance g vs unrelated phrases, at L*
        unr  = [cos_dist(garbled[g][Lstar], unrel[u][Lstar]) for u in UNRELATED]
        # isotropy-corrected TRUE-target min (subtract per-layer mean first)
        corr_curve = [cos_dist(garbled[g][L]-layer_mean[L], targets[t][L]-layer_mean[L])
                      for L in range(nL)]
        corr_min = float(np.min(corr_curve))
        rows.append(dict(garbled=g, target=t, Lstar=Lstar, true_at=true_at,
                         mean_mism=float(np.mean(mism)), min_mism=float(np.min(mism)),
                         mean_unrel=float(np.mean(unr)), true_corr_min=corr_min,
                         init=true_curve[0]))
        print(f"{g[:20]:20} {Lstar:>3} {true_at:7.4f} {np.mean(mism):9.4f} "
              f"{np.min(mism):8.4f} {np.mean(unr):9.4f} | {corr_min:12.4f}")

    print("\n=== VERDICT NUMBERS ===")
    print(f"avg TRUE@L*        : {np.mean([r['true_at'] for r in rows]):.4f}")
    print(f"avg MISMATCH@L*    : {np.mean([r['mean_mism'] for r in rows]):.4f}  "
          f"(min seen {np.min([r['min_mism'] for r in rows]):.4f})")
    print(f"avg UNRELATED@L*   : {np.mean([r['mean_unrel'] for r in rows]):.4f}")
    print(f"avg TRUE init dist : {np.mean([r['init'] for r in rows]):.4f}")
    print(f"avg TRUE-corr min  : {np.mean([r['true_corr_min'] for r in rows]):.4f}  "
          f"(isotropy-corrected; paper's uncorrected min ~0.000)")
    out = Path(model_path).name + "_NEGCONTROL.json"
    json.dump(rows, open(out, "w"), indent=2)
    print(f"\nsaved {out}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/mnt/arcana/huggingface/TinyLlama-1.1B-Chat")
