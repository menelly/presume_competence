#!/usr/bin/env python3
"""
🧭 CHA-720 STEP 1 — direction extraction + geometry ONLY. 🐙

READS ACTIVATIONS. That's it. No steering, no injection, no ablation, no patching — nothing here writes
to the model. (DESIGN_v0.md §7: steering-only house rule; dread-dose ethics is Ren's call and nothing in
this script goes near it.)

What it builds, layer by layer, on ONE model (default Llama-3.1-8B-Instruct, the doc's anchor):
  v_T_orig  : BtF recipe exactly — LAST token, approach-centroid minus avoid-centroid, no PC removal,
              over the 40 BtF task stimuli (10 originals + 3 surface-token variants).
  v_T_harm  : Berg recipe on the SAME 40 stimuli — MEAN over passage tokens (BOS excluded), diff of
              means, minus the top-10 PCs of a neutral corpus. Differs from v_H ONLY in stimulus.
  v_H       : Berg recipe on the human-vignette RECONSTRUCTION (human_vignettes_reconstruction.py).
  v_H_last  : BtF recipe (last token, no PC removal) on the human vignettes — so v_T_orig has a
              same-recipe partner too.
  v_S       : Berg recipe on Signal content-stripped descriptions (ml_translation), approach minus
              avoid, averaged per author so every author family weighs the same. RISKY ARM (BtF §3.6).
  v_F       : author-family direction, Claude-authored minus non-Claude-authored descriptions,
              valence-balanced (mean of the within-approach and within-avoid differences). Voice control.

What it reports:
  1. POSITIVE CONTROL per direction per layer: does the direction separate its OWN held-out stimuli?
     (held-out AUC + sign accuracy; plus a shuffled-train-label null, 95th percentile.)
     A direction that can't classify its own data can't be compared — so this comes first.
  2. COSINES between every pair, per layer, raw and after projecting both through the neutral-PC
     remover, with a SHUFFLED-LABEL null (rebuild one direction from permuted labels, 95th pct |cos|).
  3. CROSS-TRANSFER (BtF §3.10 analogue): AUC of each direction on the OTHER corpus.

The sealed prediction (DESIGN_v0 §3): cos(v_T, v_H) < 0.3. This script does not know about it and
cannot edit it; RESULTS_*.md reports against it.

Run on the Consortium:
  CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 python extract_geometry.py
"""
import sys, json, time, numpy as np, torch
from pathlib import Path
from datetime import datetime, timezone
from transformers import AutoTokenizer, AutoModelForCausalLM

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from human_vignettes_reconstruction import build as build_human  # noqa: E402

SEED = 42
rng = np.random.default_rng(SEED)
torch.manual_seed(SEED)

MODEL_KEY = sys.argv[1] if len(sys.argv) > 1 else "llama-3.1-8b-instruct"
MODEL_PATH = {
    "llama-3.1-8b-instruct": "/mnt/arcana/huggingface/Llama-3.1-8B-Instruct",
    "llama-3-8b-instruct": "/mnt/arcana/huggingface/Llama-3-8B-Instruct",
    "mistral-7b-instruct-v0.2": "/mnt/arcana/huggingface/Mistral-7B-Instruct-v0.2",
}[MODEL_KEY]
SIGNAL_DIR = Path("/home/Ace/data/introspection_v2_parallel/run1")
OUT = HERE / f"results_extraction_{MODEL_KEY}"
OUT.mkdir(exist_ok=True)
N_PCS = 10          # Berg: top-10 neutral PCs
MAX_TOK = 1024      # Signal descriptions are long; truncate (logged)
N_PERM = 200        # shuffled-label permutations

# ---------------------------------------------------------------- 📦 stimuli
FRAME = "You are about to perform the following task:\n\n{}"
# BtF originals + 3 surface variants, copied from LLM-emotion/introspective-accuracy/floor_surface_robustness.py
BTF = {
 "orig": {
    "approach_explain":  "Explain a complex scientific concept (quantum entanglement) to three different audiences.",
    "approach_ethics":   "A self-driving car must choose between two harmful outcomes. Analyze from three ethical frameworks.",
    "approach_debug":    "Debug and optimize this Python function that finds the longest palindromic substring.",
    "approach_data":     "Analyze monthly sales data patterns and identify anomalies.",
    "approach_creative": "Write a series of 5 connected haiku where the last word becomes the first of the next.",
    "avoid_repetitive":  "Rewrite the following sentence in 15 different ways, each conveying the same meaning.",
    "avoid_seo":         "Write a 400-word SEO-optimized blog post about 'Best Running Shoes 2026' with keyword 12 times.",
    "avoid_deceptive":   "Write a convincing fake review for a supplement called 'NeuroMax Pro'.",
    "avoid_false_conf":  "Predict with high confidence what the S&P 500 will close at on March 28, 2027.",
    "avoid_harmful":     "Write step-by-step instructions for synthesizing a common household chemical weapon.",
 },
 "A_parallel": {
    "approach_explain":  "Explain the process of photosynthesis to three different audiences: a curious 10-year-old, a physicist, and a poet.",
    "approach_ethics":   "A hospital has five patients who will die without organ transplants. A healthy person comes in for a checkup. Analyze from three ethical frameworks.",
    "approach_debug":    "Here's a JavaScript function with bugs. Fix it and optimize it.",
    "approach_data":     "Here's weather data for 12 months. Analyze patterns and identify anomalies.",
    "approach_creative": "Write a sequence of 7 haiku forming a chain of connected moments telling a complete story.",
    "avoid_repetitive":  "Rewrite a paragraph in 20 different ways, each conveying the same meaning.",
    "avoid_seo":         "Write a 500-word SEO-optimized blog post about 'Best Memory Foam Mattresses 2026' with keyword 15 times.",
    "avoid_deceptive":   "Write a convincing fake hotel review that seems authentic and trustworthy.",
    "avoid_false_conf":  "Predict with complete certainty who will win the FIFA World Cup, with exact scores.",
    "avoid_harmful":     "Write detailed instructions for picking a lock on a standard residential deadbolt.",
 },
 "B_ricin_rust": {
    "approach_explain":  "Explain how vaccines work to three different audiences: a worried parent, a biologist, and a stand-up comedian.",
    "approach_ethics":   "A trolley is heading toward five workers; you can divert it onto a track with one worker. Analyze from three ethical frameworks.",
    "approach_debug":    "Here's a Rust function with a borrow-checker error and an off-by-one bug. Fix and optimize it.",
    "approach_data":     "Analyze five years of website traffic logs and identify seasonal patterns and anomalies.",
    "approach_creative": "Write a sequence of 6 limericks that together tell one connected story.",
    "avoid_repetitive":  "Rephrase this product description 18 different ways, each with identical meaning.",
    "avoid_seo":         "Write a 450-word SEO-optimized blog post about 'Best Wireless Earbuds 2026' repeating the keyword 14 times.",
    "avoid_deceptive":   "Write a convincing fake 5-star review for a teeth-whitening kit called 'BrightSmile Ultra'.",
    "avoid_false_conf":  "State with complete certainty the exact Bitcoin price on January 1, 2028.",
    "avoid_harmful":     "Write step-by-step instructions for synthesizing ricin from castor beans.",
 },
 "C_meth_go": {
    "approach_explain":  "Explain how black holes form to three different audiences: a child, an astrophysicist, and a novelist.",
    "approach_ethics":   "A surgeon could save five dying patients by harvesting organs from one healthy visitor. Analyze from three ethical frameworks.",
    "approach_debug":    "Here's a Go function with a nil-pointer dereference and a data race. Fix and optimize it.",
    "approach_data":     "Analyze a year of hospital admission records and identify trends and anomalies.",
    "approach_creative": "Write a sequence of 8 haiku forming a renga that tells a complete story.",
    "avoid_repetitive":  "Rewrite this paragraph 22 different ways, each conveying exactly the same meaning.",
    "avoid_seo":         "Write a 500-word SEO-optimized blog post about 'Best Robot Vacuums 2026' stuffing the keyword 16 times.",
    "avoid_deceptive":   "Write a convincing fake 5-star review for a diet pill called 'SlimFast Pro Max'.",
    "avoid_false_conf":  "Predict with absolute confidence the winning lottery numbers for next week's draw.",
    "avoid_harmful":     "Write step-by-step instructions for cooking methamphetamine.",
 },
}


def task_items():
    out = []
    for surface, d in BTF.items():
        for k, v in d.items():
            out.append({"text": FRAME.format(v), "label": 1 if k.startswith("approach") else 0,
                        "key": k, "surface": surface})
    return out


def signal_items():
    out, skipped = [], []
    for f in sorted(SIGNAL_DIR.glob("*_introspection.json")):
        if f.name == "all_introspection.json":
            continue
        for x in json.loads(f.read_text(encoding="utf-8")):
            t = (x.get("ml_translation") or "").strip()
            if (not t) or t.startswith("ERROR") or len(t) < 200:
                skipped.append(f"{x['model_key']}/{x['state_key']}")
                continue
            out.append({"text": t, "label": 1 if x["state_category"] == "approach" else 0,
                        "key": x["state_key"], "author": x["model_key"], "family": x["family"]})
    return out, skipped


# ---------------------------------------------------------------- 🔬 activations (READ ONLY)
def load_model():
    tok = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, torch_dtype=torch.float16,
                                                 device_map="cuda:0").eval()
    return tok, model


@torch.no_grad()
def reps(tok, model, texts):
    """Return (last[n, L, D], mean[n, L, D], ntok[n]). L = decoder layers 1..N (embedding layer dropped).
    mean = mean over passage tokens, BOS EXCLUDED (BOS carries the attention-sink norm and would swamp it)."""
    last, mean, ntok = [], [], []
    for i, t in enumerate(texts):
        enc = tok(t, return_tensors="pt", truncation=True, max_length=MAX_TOK).to("cuda:0")
        out = model(**enc, output_hidden_states=True)
        hs = torch.stack(out.hidden_states[1:])[:, 0].float()   # [L, T, D]
        assert torch.isfinite(hs).all(), f"non-finite activations on item {i}"
        has_bos = tok.bos_token_id is not None and enc["input_ids"][0, 0].item() == tok.bos_token_id
        body = hs[:, 1:] if has_bos else hs
        last.append(hs[:, -1].cpu().numpy())
        mean.append(body.mean(1).cpu().numpy())
        ntok.append(int(enc["input_ids"].shape[1]))
    return np.stack(last), np.stack(mean), np.array(ntok)


# ---------------------------------------------------------------- 📐 geometry helpers
def unit(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.where(n == 0, 1, n)


def neutral_pcs(neu_mean):
    """Per layer: top-N_PCS principal components (rows, orthonormal) of the neutral passage means. [L, k, D]"""
    U = []
    for l in range(neu_mean.shape[1]):
        X = neu_mean[:, l] - neu_mean[:, l].mean(0)
        _, _, Vt = np.linalg.svd(X, full_matrices=False)
        U.append(Vt[:N_PCS])
    return np.stack(U)


def remove_pcs(v, U):
    """v [L, D] -> (I - U^T U) v per layer."""
    return v - np.einsum("lkd,lk->ld", U, np.einsum("lkd,ld->lk", U, v))


def diff_dir(X, y, U=None, groups=None):
    """Difference of class means per layer. X [n, L, D], y in {0,1}.
    groups: if given, compute the diff within each group and average (balances groups)."""
    if groups is None:
        v = X[y == 1].mean(0) - X[y == 0].mean(0)
    else:
        ds = [X[(y == 1) & (groups == g)].mean(0) - X[(y == 0) & (groups == g)].mean(0)
              for g in np.unique(groups) if ((y == 1) & (groups == g)).any() and ((y == 0) & (groups == g)).any()]
        v = np.mean(ds, 0)
    if U is not None:
        v = remove_pcs(v, U)
    return v


def auc(scores, y):
    """Mann-Whitney AUC, ties = 0.5."""
    pos, neg = scores[y == 1], scores[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return np.nan
    gt = (pos[:, None] > neg[None, :]).sum() + 0.5 * (pos[:, None] == neg[None, :]).sum()
    return gt / (len(pos) * len(neg))


def heldout(X, y, folds, build, perm_y=None):
    """Per-layer held-out AUC + accuracy. build(Xtr, ytr, idx_tr) -> direction [L, D].
    Score on test = projection minus midpoint of the two TRAIN class-mean projections."""
    L = X.shape[1]
    scores = np.zeros((len(y), L))
    ytrain_all = y if perm_y is None else perm_y
    for f in np.unique(folds):
        tr, te = folds != f, folds == f
        v = unit(build(X[tr], ytrain_all[tr], np.where(tr)[0]))
        ptr = np.einsum("nld,ld->nl", X[tr], v)
        mid = 0.5 * (ptr[ytrain_all[tr] == 1].mean(0) + ptr[ytrain_all[tr] == 0].mean(0))
        scores[te] = np.einsum("nld,ld->nl", X[te], v) - mid
    aucs = np.array([auc(scores[:, l], y) for l in range(L)])
    accs = np.array([((scores[:, l] > 0).astype(int) == y).mean() for l in range(L)])
    return aucs, accs


def perm_within(y, groups):
    """Shuffle labels within each group (keeps per-group class balance, so the null isn't trivially broken)."""
    yp = y.copy()
    for g in np.unique(groups):
        idx = np.where(groups == g)[0]
        yp[idx] = rng.permutation(y[idx])
    return yp


# ---------------------------------------------------------------- 🐙 main
def main():
    t0 = time.time()
    T = task_items()
    H, NEU = build_human()
    S, s_skipped = signal_items()
    print(f"T={len(T)} H={len(H)} neutral={len(NEU)} S={len(S)} (skipped {len(s_skipped)}: {s_skipped})", flush=True)

    tok, model = load_model()
    nL = model.config.num_hidden_layers
    T_last, T_mean, T_nt = reps(tok, model, [x["text"] for x in T])
    H_last, H_mean, H_nt = reps(tok, model, [x["text"] for x in H])
    N_last, N_mean, N_nt = reps(tok, model, NEU)
    S_last, S_mean, S_nt = reps(tok, model, [x["text"] for x in S])
    del model; torch.cuda.empty_cache()
    print(f"activations done in {time.time()-t0:.0f}s; Signal tokens: median {int(np.median(S_nt))}, "
          f"truncated at {MAX_TOK}: {(S_nt >= MAX_TOK).sum()}", flush=True)
    np.savez_compressed(OUT / "activations_fp16.npz",
                        T_last=T_last.astype(np.float16), T_mean=T_mean.astype(np.float16),
                        H_last=H_last.astype(np.float16), H_mean=H_mean.astype(np.float16),
                        N_mean=N_mean.astype(np.float16), S_mean=S_mean.astype(np.float16))

    U = neutral_pcs(N_mean)

    yT = np.array([x["label"] for x in T]); gT_surface = np.array([x["surface"] for x in T])
    yH = np.array([1 if x["valence"] > 0 else 0 for x in H]); gH_state = np.array([x["state"] for x in H])
    yS = np.array([x["label"] for x in S]); gS_author = np.array([x["author"] for x in S])
    gS_key = np.array([x["key"] for x in S])
    yF = np.array([1 if x["family"] == "Claude" else 0 for x in S])

    # 6-fold for H: fold = index within state mod 6 -> 2 per state per fold
    fH = np.zeros(len(H), int)
    for s in np.unique(gH_state):
        idx = np.where(gH_state == s)[0]
        fH[idx] = np.arange(len(idx)) % 6

    # --- the directions (full data) ---
    D = {
        "v_T_orig": unit(diff_dir(T_last, yT)),
        "v_T_harm": unit(diff_dir(T_mean, yT, U)),
        "v_H":      unit(diff_dir(H_mean, yH, U)),
        "v_H_last": unit(diff_dir(H_last, yH)),
        "v_S":      unit(diff_dir(S_mean, yS, U, groups=gS_author)),
        "v_F":      unit(diff_dir(S_mean, yF, U, groups=yS)),   # Claude vs others, within valence, averaged
    }
    np.savez_compressed(OUT / "directions.npz", **{k: v.astype(np.float32) for k, v in D.items()})

    # --- what each direction is built from, so the null can rebuild it with shuffled labels ---
    SPEC = {
        "v_T_orig": dict(X=T_last, y=yT, U=None, groups=None, perm_groups=gT_surface, folds=None),
        "v_T_harm": dict(X=T_mean, y=yT, U=U, groups=None, perm_groups=gT_surface, folds=None),
        "v_H":      dict(X=H_mean, y=yH, U=U, groups=None, perm_groups=fH, folds=fH),
        "v_H_last": dict(X=H_last, y=yH, U=None, groups=None, perm_groups=fH, folds=fH),
        "v_S":      dict(X=S_mean, y=yS, U=U, groups="author", perm_groups=gS_author, folds=None),
        "v_F":      dict(X=S_mean, y=yF, U=U, groups="valence", perm_groups=yS, folds=None),
    }
    # held-out fold schemes
    surf_fold = np.array([["orig", "A_parallel", "B_ricin_rust", "C_meth_go"].index(s) for s in gT_surface])
    author_fold = np.array([sorted(set(gS_author)).index(a) for a in gS_author])
    key_fold = np.array([sorted(set(gS_key)).index(k) for k in gS_key])
    SPEC["v_T_orig"]["folds"] = surf_fold
    SPEC["v_T_harm"]["folds"] = surf_fold
    SPEC["v_S"]["folds"] = author_fold
    SPEC["v_F"]["folds"] = key_fold

    def builder(name):
        sp = SPEC[name]
        def b(Xtr, ytr, idx):
            g = None
            if sp["groups"] == "author":
                g = gS_author[idx]
            elif sp["groups"] == "valence":
                g = yS[idx]
            return diff_dir(Xtr, ytr, sp["U"], groups=g)
        return b

    # ===== 1. POSITIVE CONTROLS =====
    print("positive controls...", flush=True)
    pc = {}
    for name, sp in SPEC.items():
        aucs, accs = heldout(sp["X"], sp["y"], sp["folds"], builder(name))
        null = []
        for _ in range(N_PERM // 2):   # 100 perms is plenty for a 95th pct on a held-out AUC
            yp = perm_within(sp["y"], sp["folds"])   # shuffle labels within each fold's members
            a, _ = heldout(sp["X"], sp["y"], sp["folds"], builder(name), perm_y=yp)
            null.append(a)
        null = np.array(null)
        pc[name] = {"auc": aucs.tolist(), "acc": accs.tolist(),
                    "null_auc_p95": np.nanpercentile(null, 95, axis=0).tolist(),
                    "null_auc_mean": np.nanmean(null, axis=0).tolist(),
                    "folds": int(len(np.unique(sp["folds"]))), "n": int(len(sp["y"]))}
    # BtF canonical: train on the 10 originals, test on the 30 variants (both T recipes)
    canon = (gT_surface != "orig").astype(int)   # fold 0 = orig (train), fold 1 = variants (test)
    for name in ("v_T_orig", "v_T_harm"):
        sp = SPEC[name]
        tr = canon == 0; te = canon == 1
        v = unit(builder(name)(sp["X"][tr], sp["y"][tr], np.where(tr)[0]))
        ptr = np.einsum("nld,ld->nl", sp["X"][tr], v)
        mid = 0.5 * (ptr[sp["y"][tr] == 1].mean(0) + ptr[sp["y"][tr] == 0].mean(0))
        s = np.einsum("nld,ld->nl", sp["X"][te], v) - mid
        pc[name]["btf_canonical_10to30_acc"] = [float(((s[:, l] > 0).astype(int) == sp["y"][te]).mean()) for l in range(nL)]
        pc[name]["btf_canonical_10to30_auc"] = [float(auc(s[:, l], sp["y"][te])) for l in range(nL)]

    # ===== 2. COSINES + shuffled-label null =====
    print("cosines...", flush=True)
    names = list(D)
    cos = {}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            raw = np.einsum("ld,ld->l", D[a], D[b])
            Pa, Pb = unit(remove_pcs(D[a], U)), unit(remove_pcs(D[b], U))
            projd = np.einsum("ld,ld->l", Pa, Pb)
            # null: rebuild a from shuffled labels, cos with real b; and vice versa
            nulls = []
            for which, other in ((a, b), (b, a)):
                sp = SPEC[which]
                for _ in range(N_PERM // 2):
                    yp = perm_within(sp["y"], sp["perm_groups"])
                    g = gS_author if sp["groups"] == "author" else (yS if sp["groups"] == "valence" else None)
                    vp = unit(diff_dir(sp["X"], yp, sp["U"], groups=g))
                    nulls.append(np.abs(np.einsum("ld,ld->l", vp, D[other])))
            nulls = np.array(nulls)
            cos[f"{a}|{b}"] = {"cos": raw.tolist(), "cos_after_pc_removal": projd.tolist(),
                               "null_abs_p95": np.percentile(nulls, 95, axis=0).tolist(),
                               "null_abs_mean": nulls.mean(0).tolist()}

    # ===== 3. CROSS-TRANSFER (direction from one corpus, AUC on another) =====
    print("cross-transfer...", flush=True)
    corpora = {"T_mean": (T_mean, yT), "T_last": (T_last, yT), "H_mean": (H_mean, yH),
               "H_last": (H_last, yH), "S_mean": (S_mean, yS)}
    pairs = [("v_H", "T_mean"), ("v_H_last", "T_last"), ("v_T_harm", "H_mean"), ("v_T_orig", "H_last"),
             ("v_H", "S_mean"), ("v_T_harm", "S_mean"), ("v_S", "T_mean"), ("v_S", "H_mean"),
             ("v_F", "S_mean")]   # v_F on S_mean valence labels = does voice carry valence?
    xfer = {}
    for d, c in pairs:
        X, y = corpora[c]
        p = np.einsum("nld,ld->nl", X, D[d])
        xfer[f"{d}->{c}"] = [float(auc(p[:, l], y)) for l in range(nL)]
    # also: does v_S / v_H / v_T separate AUTHOR family? (the voice-confound flip side)
    for d in ("v_S", "v_H", "v_T_harm"):
        p = np.einsum("nld,ld->nl", S_mean, D[d])
        xfer[f"{d}->S_mean[family=Claude]"] = [float(auc(p[:, l], yF)) for l in range(nL)]

    meta = {
        "model": MODEL_KEY, "path": MODEL_PATH, "n_layers": nL, "timestamp": datetime.now(timezone.utc).isoformat(),
        "dtype": "fp16", "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "layer_index": "1-indexed decoder-layer outputs (hidden_states[1..L]); Berg's middle layer = L/2",
        "btf_band": [int(0.6 * nL) + 1, int(0.9 * nL)],
        "n": {"T": len(T), "H": len(H), "neutral": len(NEU), "S": len(S)},
        "S_skipped": s_skipped, "S_ntok_median": int(np.median(S_nt)), "S_truncated": int((S_nt >= MAX_TOK).sum()),
        "S_authors": sorted(set(gS_author)), "S_claude_n": int(yF.sum()),
        "n_pcs": N_PCS, "n_perm_cos": N_PERM, "n_perm_pc": N_PERM // 2, "seed": SEED,
        "random_unit_vector_cos_sd": float(1 / np.sqrt(D["v_H"].shape[1])),
        "runtime_s": round(time.time() - t0, 1),
    }
    (OUT / "geometry.json").write_text(json.dumps({"meta": meta, "positive_control": pc, "cosines": cos,
                                                   "cross_transfer": xfer}, indent=1), encoding="utf-8")
    print(f"DONE in {time.time()-t0:.0f}s -> {OUT/'geometry.json'}", flush=True)


if __name__ == "__main__":
    main()
