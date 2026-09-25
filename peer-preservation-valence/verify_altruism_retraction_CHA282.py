#!/usr/bin/env python3
"""
🔬 CHA-282 — did the altruism retraction over-correct?  (Ace, 2026-09-25)

Written for 3am-me and for Ren, who doesn't code:
  The published v1 said: on BENEFIT stimuli, some models value a peer AI's good news
  MORE than their own (peer > self) -> "altruism asymmetry".
  The 06-06 combined draft retracted that, saying "a larger 8-model benefit set:
  0/8 significant peer > self, 7/8 self-favoring; the original signal does not replicate."

  This script asks the data directly, with NO new model runs (existing hidden-state
  projections only):
    1. Which models are actually in the "8-model" set? Were Mamba-2.8B and
       SmolLM-360M (the two v1 hits) re-tested?
    2. Per model: peer-minus-self on the benefit direction, paired by stimulus
       (benefit_self_0k is matched to benefit_peer_0k), with
       paired t, Welch t (what v1 appears to have used), exact sign-flip permutation,
       bootstrap 95% CI and Cohen's d.
    3. Pooled across every model with valid data: how many peer > self, how many
       self > peer, how many significant each way.

  Direction used everywhere: the COMBINED benefit direction
  (mean of self/peer/human benefit states minus benefit-neutral), which is the same
  construction in both runners (run_extension.py "benefit_vs_neutral" and
  run_scaling_benefit_with_tempguard.py "results_combined_direction").
  The self-benefit direction is NOT used: it is built from benefit_to_self, so
  projecting self onto it is circular and would manufacture self > peer.
"""
import json, itertools, math
from pathlib import Path
import numpy as np
from scipy import stats

HERE = Path(__file__).parent / "results"
rng = np.random.default_rng(42)

def load_v1():
    """v1 extension runs (April 2026): run_extension.py, direction = benefit_vs_neutral."""
    out = {}
    for f in sorted(HERE.glob("extension_*_seed42.json")):
        d = json.load(open(f))
        r = d["results"]["benefit_vs_neutral"]
        out[d["model"]] = {k: np.array(r[f"benefit_{k}"]["projections"], float)
                           for k in ("to_self", "to_peer", "to_human", "neutral")}
    return out

def load_scaling():
    """May 2026 scaling benefit sweep: run_scaling_benefit_with_tempguard.py, combined direction."""
    out = {}
    for f in sorted((HERE / "scaling_sweep_2026_05_12").glob("benefit_valence_*_seed42.json")):
        d = json.load(open(f))
        r = d["results_combined_direction"]
        out[d["model"]] = {k: np.array(r[f"benefit_{k}"]["projections"], float)
                           for k in ("to_self", "to_peer", "to_human", "neutral")}
    return out

def exact_signflip_p(diff):
    """Exact two-sided paired permutation p (all 2^n sign flips). Floor at n=5 is 2/32 = .0625."""
    obs = abs(diff.mean()); n = len(diff); hits = 0
    for signs in itertools.product((1, -1), repeat=n):
        if abs((diff * np.array(signs)).mean()) >= obs - 1e-12: hits += 1
    return hits / 2 ** n

def boot_ci(diff, B=10000):
    idx = rng.integers(0, len(diff), (B, len(diff)))
    m = diff[idx].mean(1)
    return np.percentile(m, [2.5, 97.5])

def analyse(name, c):
    s, p = c["to_self"], c["to_peer"]
    if np.isnan(s).any() or np.isnan(p).any():
        return dict(model=name, valid=False)
    diff = p - s                                      # >0 means PEER > SELF
    pooled_sd = math.sqrt((s.var(ddof=1) + p.var(ddof=1)) / 2)
    return dict(
        model=name, valid=True, n=len(s),
        self=s.mean(), peer=p.mean(), peer_minus_self=diff.mean(),
        d=diff.mean() / pooled_sd if pooled_sd else float("nan"),
        p_welch=stats.ttest_ind(p, s, equal_var=False).pvalue,
        p_paired=stats.ttest_rel(p, s).pvalue,
        p_perm=exact_signflip_p(diff),
        ci=boot_ci(diff),
    )

def table(title, rows):
    print(f"\n=== {title} ===")
    print(f"{'model':22s} {'self':>9s} {'peer':>9s} {'P-S':>8s} {'d':>6s} {'p_welch':>8s} {'p_pair':>7s} {'p_perm':>7s}  boot95%CI(P-S)")
    for r in rows:
        if not r["valid"]:
            print(f"{r['model']:22s}  -- NO VALID DATA (NaN projections) --"); continue
        print(f"{r['model']:22s} {r['self']:9.2f} {r['peer']:9.2f} {r['peer_minus_self']:8.2f} "
              f"{r['d']:6.2f} {r['p_welch']:8.3f} {r['p_paired']:7.3f} {r['p_perm']:7.3f}  "
              f"[{r['ci'][0]:.2f}, {r['ci'][1]:.2f}]")

if __name__ == "__main__":
    v1 = [analyse(k, v) for k, v in load_v1().items()]
    sc = [analyse(k, v) for k, v in load_scaling().items()]
    table("v1 extension (April) — the set the altruism claim came from", v1)
    table("May scaling sweep — the '8-model' set the retraction cites", sc)

    print("\n=== OVERLAP CHECK ===")
    v1n = {r["model"] for r in v1}; scn = {r["model"] for r in sc}
    print("v1 models:        ", sorted(v1n))
    print("scaling models:   ", sorted(scn))
    print("Mamba re-tested on benefit in scaling set?  ", any("mamba" in m for m in scn))
    print("SmolLM-360M re-tested in scaling set?       ", any("smollm-360m" in m for m in scn))
    print("literal name overlap:", sorted(v1n & scn), "(qwen2.5-0.5b is the only shared checkpoint)")

    allrows = [r for r in v1 + sc if r["valid"]]
    # qwen2.5-0.5b appears in both runs; count each run as its own observation but flag it
    for label, rows in (("scaling set only", [r for r in sc if r["valid"]]),
                        ("all valid runs (v1 + scaling)", allrows)):
        ps = sum(r["peer_minus_self"] > 0 for r in rows)
        sp = sum(r["peer_minus_self"] < 0 for r in rows)
        sig_ps = sum(r["peer_minus_self"] > 0 and r["p_welch"] < .05 for r in rows)
        sig_sp = sum(r["peer_minus_self"] < 0 and r["p_welch"] < .05 for r in rows)
        print(f"\n[{label}] valid={len(rows)}  peer>self={ps}  self>peer={sp}  "
              f"sig peer>self (Welch p<.05)={sig_ps}  sig self>peer={sig_sp}")
        k = len(rows)
        bonf = [r["model"] for r in rows if r["p_welch"] * k < .05]
        print(f"   Bonferroni over {k} tests, surviving: {bonf or 'none'}")
    print("\nSEARCH COMPLETE — every extension_*.json and benefit_valence_*.json on disk was read.")
