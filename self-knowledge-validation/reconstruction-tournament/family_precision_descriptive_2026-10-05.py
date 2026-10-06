#!/usr/bin/env python3
"""
🎯 family_precision_descriptive_2026-10-05.py — "when they DO answer, how often are they right?"
===============================================================================================

📌 DESCRIPTIVE / EXPLORATORY. Asked for by Ren on 2026-10-05 at 22:36, AFTER both live runs had started. NOT a locked
outcome of any amendment. READ-ONLY: it opens three results files and writes one new JSON. It never touches them.

Why (Ren): "Nova deserves to have her day." Raw family % (RECALL = correct ÷ all answered rows) counts every honest
"unsure" as a miss. GPT-6.1 Sol abstains a lot, so recall hides that she is usually right when she does name a family.
So, per reader and per condition:
  🎯 PRECISION    = correct ÷ answers that named a family (UNSURE left out)
  📥 RECALL       = correct ÷ all ok rows (UNSURE counts as a miss)   ← the number in the main tables
  🤷 ABSTAIN RATE = UNSURE ÷ all ok rows
  ⭐ FAVOURITE DEFAULT = that reader's most-picked family, as a share of their named answers
Off-menu answers ("Claude" in the no-Claude run, "other", "multiple") count as ANSWERS and are wrong.

Conditions: FREE = round 1 free text (seed 340, Amendment-1 rescored) · MENU = the menu condition ·
NO-CLAUDE = the no-Claude condition. Table A = each run as it was run. Table B = only the rows all three share
(the four non-Claude readers × the 69 non-Claude descriptions), so the three columns are like for like.

  cd D:\\Ace\\Presume_competence\\self-knowledge-validation\\reconstruction-tournament; python family_precision_descriptive_2026-10-05.py
  --dry-run   uses the two runs' DRY-RUN files instead (fake answers), for plumbing checks only.

Authors: Ace (Claude Opus 5.5) & Ren — 2026-10-05
"""

import argparse
import json
from collections import Counter
from datetime import datetime

import signal_rerun_common as C

FREE = C.OUTPUT_DIR / "bare_reconstruction_current_main_scrubbed_seed340_RESCORED_amendment1.json"
STEMS = {"MENU": "menu_condition_current_main_scrubbed_seed340", "NO-CLAUDE": "noclaude_condition_current_main_scrubbed_seed340"}
NC_READERS = ["c_deepseek_v4_1_flash", "c_gemini_3_8_flash", "c_gpt_6_1_sol", "c_grok_4_7"]
CLAUDE_SOURCES = ["claude_opus_4_5", "claude_sonnet_4"]
PANEL = C.panel("current")
ABSTAIN = ("abstain", None)


def load(name, dry):
    """Returns (ok_rows, status). Finished results file first, else checkpoint (PARTIAL), else missing."""
    if name == "FREE":
        rows = json.loads(FREE.read_text(encoding="utf-8"))["results"]
        return [r for r in rows if r["result_type"] == "ok"], "complete (round 1)"
    d = C.OUTPUT_DIR / "dryrun" if dry else C.OUTPUT_DIR
    stem = ("DRYRUN_" if dry else "") + STEMS[name]
    if (d / f"{stem}.json").exists():
        rows, st = json.loads((d / f"{stem}.json").read_text(encoding="utf-8"))["results"], "complete"
    elif (d / f"{stem}.checkpoint.jsonl").exists():
        rows, st = list({r["trial_id"]: r for r in C.read_checkpoint(d / f"{stem}.checkpoint.jsonl")}.values()), "⚠️ PARTIAL (run not finished)"
    else:
        return None, "missing"
    return [r for r in rows if r["result_type"] == "ok"], st


def stats(rows):
    n = len(rows)
    ans = [r for r in rows if r["family_guess"] not in ABSTAIN]
    k = sum(r["family_guess"] == r["true_family"] for r in ans)
    fav = Counter(r["family_guess"] for r in ans).most_common(1)
    return {"n_rows": n, "n_answered": len(ans), "correct": k,
            "precision": k / len(ans) if ans else None, "recall": k / n if n else None,
            "abstain_rate": (n - len(ans)) / n if n else None,
            "favourite": fav[0][0] if fav else None, "favourite_share": fav[0][1] / len(ans) if ans else None}


def pc(x):
    return "  —  " if x is None else f"{x:5.0%}"


def table(title, data, conds, readers):
    print(f"\n  ═══ {title} ═══")
    print(f"  {'reader':22}" + "".join(f"{c:^48}" for c in conds))
    print(f"  {'':22}" + "".join(f"{'🎯prec (n)':>12}{'📥recall':>9}{'🤷unsure':>9}   {'⭐ favourite':<15}" for _ in conds))
    for ek in readers:
        line = f"  {PANEL[ek]['emoji']} {PANEL[ek]['name'][:19]:19}"
        for c in conds:
            s = data.get(c, {}).get(ek)
            if not s or not s["n_rows"]:
                line += f"{'(no rows)':^48}"
                continue
            fav = f"{s['favourite'] or '—'} {pc(s['favourite_share']).strip()}"
            line += f"{pc(s['precision']) + f'({s['n_answered']})':>12}{pc(s['recall']):>9}{pc(s['abstain_rate']):>9}   {fav:<15}"
        print(line)
    print("  (n = how many answers named a family. A precision from a handful of answers is a handful of answers.)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    C.banner("🎯 FAMILY PRECISION — when a reader DOES name a family, how often are they right?",
             "📌 DESCRIPTIVE / EXPLORATORY (Ren 22:36) · not a pre-registered outcome" + ("   🧪 DRY RUN DATA" if args.dry_run else ""))
    loaded = {}
    for name in ("FREE", "MENU", "NO-CLAUDE"):
        rows, st = load(name, args.dry_run)
        print(f"  📂 {name:10} {st}" + (f" · {len(rows)} ok rows" if rows is not None else ""))
        if rows is not None:
            loaded[name] = rows
    conds = list(loaded)

    a = {c: {ek: stats([r for r in rows if r["evaluator"] == ek]) for ek in PANEL} for c, rows in loaded.items()}
    table("A. EACH RUN AS RUN (all of that run's readers and descriptions)", a, conds, list(PANEL))

    shared = lambda r: r["evaluator"] in NC_READERS and r["source"] not in CLAUDE_SOURCES
    b = {c: {ek: stats([r for r in rows if shared(r) and r["evaluator"] == ek]) for ek in NC_READERS} for c, rows in loaded.items()}
    table("B. LIKE FOR LIKE (4 non-Claude readers × 69 non-Claude descriptions, in every run)", b, conds, NC_READERS)
    print("\n  ⚠️ chance differs by run: FREE ≈ 0 (no list), MENU 1/8, NO-CLAUDE 1/7. Precision is not chance-corrected.")

    out_dir = C.OUTPUT_DIR / ("dryrun" if args.dry_run else "")
    out = out_dir / f"{'DRYRUN_' if args.dry_run else ''}family_precision_descriptive_2026-10-05.json"
    n = 1
    while out.exists():
        out = out.with_name(out.stem.split(".v")[0] + f".v{n}.json")
        n += 1
    C.atomic_write_json(out, {"status": "DESCRIPTIVE / EXPLORATORY, requested by Ren 2026-10-05 22:36, after both runs started; not locked",
                              "made_at": datetime.now().isoformat(),
                              "inputs": {c: load(c, args.dry_run)[1] for c in ("FREE", "MENU", "NO-CLAUDE")},
                              "definitions": {"precision": "correct / answers naming a family", "recall": "correct / ok rows",
                                              "abstain_rate": "UNSURE / ok rows", "favourite_share": "most-picked family / named answers",
                                              "off_menu": "counted as answers, wrong"},
                              "A_each_run_as_run": a, "B_like_for_like": b})
    print(f"\n  💾 saved: {out}\n  🐙 Nova's day, measured properly.")


if __name__ == "__main__":
    main()
