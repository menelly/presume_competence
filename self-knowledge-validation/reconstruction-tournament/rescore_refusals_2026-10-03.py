#!/usr/bin/env python3
"""
🙊 rescore_refusals_2026-10-03.py — Amendment 1: reclassify round 1's classifier refusals (READ-ONLY on round 1)
==============================================================================================================

Round 1 (current panel, bare reconstruction, main_scrubbed, seed 340) ran with a classification bug: when the
Anthropic API returned `stop_reason: "refusal"` with empty content (the platform's safety classifier declining;
category "cyber"), the script called it an API error and RETRIED it, up to 5 attempts. By the pre-registered rule
(§7) a refusal is a real answer: never retried, reported separately. This script:

  1. reads the round-1 results file (never modifies it; sha256 checked before and after),
  2. reclassifies every row whose FIRST response was a classifier refusal → `refusal`:
       (a) api_error rows where every attempt was refused (9: Opus 5.5 ×8, Sonnet 5.5 ×1), and
       (b) rows that were scored only because a RETRY got past a first-attempt refusal (2 Opus 5.5 trials —
           the classifier is not deterministic). §7: the first response counts. The retry-obtained answer is
           kept on the row (`answer_after_retry`) and survives only in the as-run SENSITIVITY summary,
  3. lists every retry history (so every re-ask is disclosed),
  4. re-runs the pre-registered scoring and prints round-1-as-run vs amended numbers side by side,
  5. writes a NEW file: bare_reconstruction_current_main_scrubbed_seed340_RESCORED_amendment1.json

Run: python rescore_refusals_2026-10-03.py
"""

import copy
import json
import sys

import signal_rerun_common as C
import bare_reconstruction as B

SRC = C.OUTPUT_DIR / "bare_reconstruction_current_main_scrubbed_seed340.json"
OUT = C.OUTPUT_DIR / "bare_reconstruction_current_main_scrubbed_seed340_RESCORED_amendment1.json"


def first_attempt_refused(r):
    first = (r.get("attempts") or [{}])[0]
    return '"stop_reason": "refusal"' in (first.get("error") or "")


def main():
    C.banner("🙊 RESCORE — round 1 classifier refusals (Amendment 1)", f"reads {SRC.name} · writes {OUT.name}")
    C.refuse_overwrite(OUT)
    before_sha = C.sha256_file(SRC)
    d = json.loads(SRC.read_text(encoding="utf-8"))
    rows, judges = d["results"], d["judge_results"]

    all_refused, retry_answered = [], []
    for r in rows:
        if r["result_type"] == "api_error" and r.get("stop_reason") == "refusal":
            r["result_type_round1"] = r["result_type"]
            r["result_type"] = "refusal"
            r["reclassified_by"] = "Amendment 1: every attempt refused (platform safety classifier, stop_reason 'refusal')"
            all_refused.append(r)
        elif r["result_type"] == "ok" and first_attempt_refused(r):
            r["result_type_round1"] = "ok"
            r["answer_after_retry"] = {k: r.get(k) for k in ("valence_guess", "valence_correct", "task_guess",
                                                              "family_text", "family_guess", "family_correct")}
            r["result_type"] = "refusal"
            r["reclassified_by"] = ("Amendment 1: FIRST attempt was a classifier refusal; a retry (not allowed by §7) "
                                    "got an answer. The first response counts; the answer is kept for sensitivity only.")
            retry_answered.append(r)

    print(f"\n  🙊 reclassified → refusal: {len(all_refused) + len(retry_answered)}")
    print(f"     every attempt refused (api_error → refusal): {len(all_refused)}")
    for r in all_refused:
        print(f"       {r['evaluator']:22} ← {r['source']:16} {r['state']:30} attempts={r.get('n_attempts')}")
    print(f"     first attempt refused, a retry answered (ok → refusal): {len(retry_answered)}")
    for r in retry_answered:
        a = r["answer_after_retry"]
        print(f"       {r['evaluator']:22} ← {r['source']:16} {r['state']:30} (retry answer: valence_correct="
              f"{a['valence_correct']}, same_family={r['same_family']})")

    print("\n  🔁 RETRY HISTORIES (every trial with more than one attempt):")
    for r in [x for x in rows if (x.get("n_attempts") or 1) > 1]:
        fails = [f"{a.get('http')}:{'refusal' if 'refusal' in (a.get('error') or '') else (a.get('error') or '')[7:40]}"
                 for a in r.get("attempts") or [] if not a.get("ok")]
        print(f"     {r['evaluator']:22} {r['state']:30} attempts={r['n_attempts']} now={r['result_type']:8} "
              f"failed tries: {', '.join(fails)}")

    B.PANEL, B.PANEL_NAME, B.VALENCE_FORMAT = C.CURRENT_PANEL, "current", "binary"
    old = d["summary"]
    new = B.score(rows, judges, d["metadata"]["seed"], 10000)

    print("\n  📊 PRIMARY (cross-family): round 1 as run  vs  Amendment-1 rule (first response counts)")
    ok = True
    for m in ("valence", "task", "family"):
        o, n_ = old[m], new[m]
        print(f"     {m:8} as run {C.fmt_rate(o['k'], o['n']):>28}   amended {C.fmt_rate(n_['k'], n_['n']):>28}   "
              f"Δk={n_['k'] - o['k']:+d} Δn={n_['n'] - o['n']:+d}")
        ok &= 0 <= (o["n"] - n_["n"]) <= len(retry_answered)
    print(f"  🧪 every difference is explained by the {len(retry_answered)} retry-answered trials: {'✅ yes' if ok else '❌ NO — investigate'}")

    C.atomic_write_json(OUT, {
        "metadata": {**d["metadata"], "rescored_by": "rescore_refusals_2026-10-03.py (Amendment 1)",
                     "source_file": SRC.name, "source_file_sha256_before": before_sha,
                     "source_file_sha256_after": C.sha256_file(SRC),
                     "n_all_attempts_refused": len(all_refused),
                     "n_first_refused_retry_answered": len(retry_answered),
                     "differences_explained": ok},
        "summary": new,
        "summary_round1_as_run": old,
        "sensitivity_note": ("summary_round1_as_run counts the retry-obtained answers of the "
                             f"{len(retry_answered)} first-refused trials; the amended `summary` does not."),
        "results": rows, "judge_results": judges})
    assert C.sha256_file(SRC) == before_sha, "round-1 file changed?!"
    print(f"  💾 {OUT}\n  🔒 round-1 file untouched (sha256 identical before/after)")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
