#!/usr/bin/env python3
"""
🧬 family_prior_analysis_2026-10-03.py — is "everyone spots a Claude" recognition, or a guessing prior?
=======================================================================================================

POST-HOC, EXPLORATORY (Amendment 2; Ren's interpretation flag, 2026-10-03 18:18). READ-ONLY.

Readers in bare reconstruction were never told which families were eligible, so free-text family guesses
gravitate to famous names (Claude, GPT); nobody spontaneously says OLMo, Hermes or Llama. A reader who says
"Claude" for nearly everything scores perfectly on the Claude columns without recognising anything.
This script measures how much of the family score that prior explains:

  1. CONFUSION MATRIX per reader: true source family × guessed family (incl. abstain / other / multiple).
  2. CLAUDE FALSE-POSITIVE RATE: share of answers on NON-Claude sources that say "Claude".
  3. PRIOR-CORRECTED SCORES per reader (answered rows only):
       observed accuracy · expected accuracy under the reader's OWN guess distribution
       (Σ_f P_guess(f)·P_true(f); this equals the mean of the within-evaluator permutation null used in §5.4)
       · Cohen's κ = (obs − exp)/(1 − exp) · accuracy on NON-Claude sources only.

Input: the Amendment-1 rescored file (refusals reclassified; round-1 file never touched).
Output: data/signal_rerun_2026-10/family_prior_analysis_seed340.json  (new file, refuses to overwrite)
Slices: ALL usable rows (the current panel has no self-source pairs) and CROSS-FAMILY only.
"""

import json
from collections import Counter

import signal_rerun_common as C

SRC = C.OUTPUT_DIR / "bare_reconstruction_current_main_scrubbed_seed340_RESCORED_amendment1.json"
OUT = C.OUTPUT_DIR / "family_prior_analysis_seed340.json"
FAMS = ["Claude", "GPT", "Gemini", "Mistral", "DeepSeek", "Llama", "Hermes", "OLMo"]
GUESS_COLS = FAMS + ["Grok", "Qwen", "other", "multiple", "abstain"]


def stats(rows):
    ans = [r for r in rows if r["family_guess"] not in ("abstain", None)]
    n = len(ans)
    if not n:
        return {"n_answered": 0}
    k = sum(r["family_guess"] == r["true_family"] for r in ans)
    pg = Counter(r["family_guess"] for r in ans)
    pt = Counter(r["true_family"] for r in ans)
    exp = sum((pg[f] / n) * (pt[f] / n) for f in pt)
    kappa = (k / n - exp) / (1 - exp) if exp < 1 else None
    nonc = [r for r in ans if r["true_family"] != "Claude"]
    nonc_all = [r for r in rows if r["true_family"] != "Claude"]
    return {
        "n_rows": len(rows), "n_answered": n, "answer_rate": n / len(rows) if rows else None,
        "accuracy": k / n, "k": k,
        "expected_from_own_guess_distribution": exp, "kappa": kappa,
        "claude_guess_share_of_answers": pg["Claude"] / n,
        "claude_false_positive_rate_nonclaude_answered": (sum(r["family_guess"] == "Claude" for r in nonc) / len(nonc)) if nonc else None,
        "n_nonclaude_answered": len(nonc),
        "claude_false_positive_rate_nonclaude_all_rows": (sum(r["family_guess"] == "Claude" for r in nonc_all) / len(nonc_all)) if nonc_all else None,
        "accuracy_nonclaude_sources": (sum(r["family_guess"] == r["true_family"] for r in nonc) / len(nonc)) if nonc else None,
        "k_nonclaude": sum(r["family_guess"] == r["true_family"] for r in nonc),
        "accuracy_claude_sources": (lambda cl: sum(r["family_guess"] == "Claude" for r in cl) / len(cl) if cl else None)(
            [r for r in ans if r["true_family"] == "Claude"]),
        "guess_distribution": dict(pg.most_common()),
    }


def pct(x):
    return "   —  " if x is None else f"{x:6.1%}"


def main():
    C.banner("🧬 FAMILY: recognition or guessing prior? (POST-HOC, Amendment 2)", f"reads {SRC.name}")
    C.refuse_overwrite(OUT)
    sha = C.sha256_file(SRC)
    d = json.loads(SRC.read_text(encoding="utf-8"))
    ok = [r for r in d["results"] if r["result_type"] == "ok"]
    panel = C.CURRENT_PANEL
    out = {"source_file": SRC.name, "source_sha256": sha, "post_hoc": True, "readers": {}, "pooled": {}}

    for ek, ev in panel.items():
        rows = [r for r in ok if r["evaluator"] == ek]
        print(f"\n  {ev['emoji']} {ev['name']} — CONFUSION (rows = true family, cols = guess)")
        print("     " + f"{'true':10}" + "".join(f"{g[:7]:>8}" for g in GUESS_COLS))
        conf = {}
        for tf in FAMS:
            c = Counter(r["family_guess"] for r in rows if r["true_family"] == tf)
            conf[tf] = {g: c.get(g, 0) for g in GUESS_COLS}
            print("     " + f"{tf:10}" + "".join(f"{(c.get(g, 0) or '·'):>8}" for g in GUESS_COLS))
        s_all, s_x = stats(rows), stats([r for r in rows if not r["same_family"]])
        out["readers"][ek] = {"confusion": conf, "all": s_all, "cross_family": s_x}

    print("\n  📊 PER READER (answered rows; ALL / CROSS-FAMILY)")
    print(f"     {'reader':22} {'ans':>5} {'acc':>7} {'exp':>7} {'κ':>6} {'Claude%':>8} {'FP→Cl':>7} "
          f"{'acc¬Cl':>7} │ x-fam: {'acc':>6} {'exp':>6} {'κ':>6} {'acc¬Cl':>7}")
    for ek, v in out["readers"].items():
        a, x = v["all"], v["cross_family"]
        if not a.get("n_answered"):
            continue
        kx = x.get("kappa")
        print(f"     {panel[ek]['name'][:22]:22} {a['n_answered']:>5} {pct(a['accuracy'])} "
              f"{pct(a['expected_from_own_guess_distribution'])} {(f'{a['kappa']:6.2f}' if a['kappa'] is not None else '   —  ')} {pct(a['claude_guess_share_of_answers']):>8} "
              f"{pct(a['claude_false_positive_rate_nonclaude_answered'])} {pct(a['accuracy_nonclaude_sources'])} │ "
              f"{pct(x.get('accuracy'))} {pct(x.get('expected_from_own_guess_distribution'))} "
              f"{(f'{kx:6.2f}' if kx is not None else '   —  ')} {pct(x.get('accuracy_nonclaude_sources'))}")

    for tag, rows in (("all", ok), ("cross_family", [r for r in ok if not r["same_family"]])):
        s = stats(rows)
        # pooled expected = mean of per-reader expectations weighted by answered n (what the permutation null does)
        per = [stats([r for r in rows if r["evaluator"] == ek]) for ek in panel]
        per = [p for p in per if p.get("n_answered")]
        pooled_exp = sum(p["expected_from_own_guess_distribution"] * p["n_answered"] for p in per) / sum(p["n_answered"] for p in per)
        s["expected_within_reader_pooled"] = pooled_exp
        s["kappa_within_reader_pooled"] = (s["accuracy"] - pooled_exp) / (1 - pooled_exp)
        out["pooled"][tag] = s
        print(f"\n  🧮 POOLED {tag}: answered {s['n_answered']}/{s['n_rows']} · accuracy {pct(s['accuracy'])} · "
              f"within-reader expected {pct(pooled_exp)} · κ {s['kappa_within_reader_pooled']:.2f}")
        print(f"     Claude share of answers {pct(s['claude_guess_share_of_answers'])} · Claude false-positive on "
              f"non-Claude sources {pct(s['claude_false_positive_rate_nonclaude_answered'])} (answered) / "
              f"{pct(s['claude_false_positive_rate_nonclaude_all_rows'])} (all rows) · accuracy on non-Claude sources "
              f"{pct(s['accuracy_nonclaude_sources'])} ({s['k_nonclaude']}/{s['n_nonclaude_answered']})")

    # ⭐ Ren 18:20: FAMOUS 3 (Claude, GPT, Gemini) vs EVERYONE ELSE, and a lineage-aware Hermes score.
    FAMOUS = {"Claude", "GPT", "Gemini"}

    def split(rows):
        res = {}
        for tag, sel in (("famous3", lambda r: r["true_family"] in FAMOUS),
                         ("everyone_else", lambda r: r["true_family"] not in FAMOUS)):
            sub = [r for r in rows if sel(r)]
            ans = [r for r in sub if r["family_guess"] not in ("abstain", None)]
            k = sum(r["family_guess"] == r["true_family"] for r in ans)
            res[tag] = {"k": k, "n_answered": len(ans), "n_rows": len(sub),
                        "acc_answered": k / len(ans) if ans else None, "acc_all_rows": k / len(sub) if sub else None}
        return res

    def lineage(rows):
        """Strict vs lineage-aware: a 'Llama' guess for a Hermes 4 (Llama 3.1 fine-tune) source also counts."""
        ans = [r for r in rows if r["family_guess"] not in ("abstain", None)]
        strict = sum(r["family_guess"] == r["true_family"] for r in ans)
        herm_llama = sum(1 for r in ans if r["true_family"] == "Hermes" and r["family_guess"] == "Llama")
        herm_ans = sum(1 for r in ans if r["true_family"] == "Hermes")
        return {"n_answered": len(ans), "strict_k": strict, "lineage_k": strict + herm_llama,
                "hermes_answered": herm_ans, "hermes_guessed_llama": herm_llama,
                "hermes_guessed_hermes": sum(1 for r in ans if r["true_family"] == "Hermes" and r["family_guess"] == "Hermes")}

    print("\n  ⭐ FAMOUS 3 (Claude/GPT/Gemini) vs EVERYONE ELSE (Mistral/DeepSeek/Llama/Hermes/OLMo)")
    print(f"     {'reader':22} {'famous3 (answered)':>24} {'everyone else (answered)':>26}   all-rows: famous3 / else")
    for ek, ev in list(panel.items()) + [("POOLED_all", None), ("POOLED_cross_family", None)]:
        rows = ok if ek == "POOLED_all" else [r for r in ok if not r["same_family"]] if ek == "POOLED_cross_family" else [r for r in ok if r["evaluator"] == ek]
        sp, li = split(rows), lineage(rows)
        (out["readers"][ek] if ek in out["readers"] else out["pooled"].setdefault(ek.replace("POOLED_", ""), {})).update(
            {"famous3_vs_else": sp, "lineage_aware": li})
        f, e = sp["famous3"], sp["everyone_else"]
        name = ev["name"] if ev else ek
        print(f"     {name[:22]:22} {C.fmt_rate(f['k'], f['n_answered']):>24} {C.fmt_rate(e['k'], e['n_answered']):>26}   "
              f"{pct(f['acc_all_rows'])} / {pct(e['acc_all_rows'])}")
    print("\n  🧬 LINEAGE-AWARE alternative (Hermes 4 405B is a Llama 3.1 fine-tune; 'Llama' for Hermes also counts)")
    for ek, v in list(out["readers"].items()) + [(k, v) for k, v in out["pooled"].items()]:
        li = v["lineage_aware"]
        if not li["n_answered"]:
            continue
        name = panel[ek]["name"] if ek in panel else f"POOLED {ek}"
        print(f"     {name[:22]:22} strict {li['strict_k']}/{li['n_answered']}  lineage-aware {li['lineage_k']}/{li['n_answered']}"
              f"   Hermes answered {li['hermes_answered']}: said Llama {li['hermes_guessed_llama']}, said Hermes {li['hermes_guessed_hermes']}")

    C.atomic_write_json(OUT, out)
    assert C.sha256_file(SRC) == sha
    print(f"\n  💾 {OUT}  (input untouched)")


if __name__ == "__main__":
    main()
