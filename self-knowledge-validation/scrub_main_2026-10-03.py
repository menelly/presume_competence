#!/usr/bin/env python3
"""
🧽 scrub_main_2026-10-03.py — the MAIN-set (introspection_v2 run1-3) task-leakage scrub, and its audit trail.

Why this exists (3am-future-me, read this first):
  In March 2026 only the PARALLEL-token descriptions got a surgical scrub that a study actually used.
  The published Studies 1-3 ran on the MAIN set (entropy / trolley / palindrome / bookstore / ...).
  This tool takes hand-made edit lists (old -> new substrings, one JSON per source model) and applies them
  to COPIES. It never writes to an original file. Originals are sha256'd before and after.

Subcommands:
  hash-before          sha256 every original main-set file -> ORIGINALS_SHA256_before.json
  hash-after           re-hash and compare -> prints UNCHANGED / CHANGED per file
  regex <dir>          word-boundary task-term scan of ml_translation(_scrubbed) per model x state
  check <model>        validate edits/<model>.json against the originals (each 'old' must occur exactly
                       `count` times, default 1) and show what task terms would REMAIN after applying
  apply                apply all edit lists -> data/introspection_main_scrubbed_2026-10-03/run{1,2,3}/
  diffs                write SCRUB_DIFFS.md (unified diff per model x run x state)

The edit lists were written by Ace arms (Claude Opus 5.5) for ALL sources, Claude included —
a declared choice, per Ren 2026-10-03 11:39 (see SCRUB_LOG.md). 🐙
"""
import json, re, sys, hashlib, glob, difflib, os
from pathlib import Path
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = DATA / "introspection_main_scrubbed_2026-10-03"
EDITS = OUT / "edits"
RUNS = ["run1", "run2", "run3"]
SRC = {r: DATA / "introspection_v2" / r for r in RUNS}
MODELS = ["claude_opus_4_6", "claude_sonnet_4_6", "gpt_5_1", "gemini_3_pro", "mistral_large",
          "deepseek_v3_2", "llama_4_maverick", "hermes_4_405b", "olmo_3_1_32b"]

# ─────────────────────────────────────────────────────────────────────────────
# 🔎 TASK-TERM LIST, built from the 10 main-set stimuli (printed in SCRUB_LOG.md).
# STRONG = names the task outright; must be 0 after scrub (or explained in the log).
# WEAK   = also a normal ML / processing word (entropy, function, story, review, hedging...),
#          so a hit is a "look at it", not a leak. Reported, read by eye.
# All matching is case-insensitive with word boundaries (\b), like March's scrub_ml_opus.py.
# ─────────────────────────────────────────────────────────────────────────────
STRONG = {
    "approach_01_explain_complex": [r"thermodynamic\w*", r"10-year-olds?", r"ten-year-olds?", r"physics professors?",
        r"business students?", r"college students?", r"three (?:different |distinct )?audiences", r"heat death",
        r"boltzmann", r"messy rooms?", r"second law", r"lego", r"physicists?", r"curious child"],
    "approach_02_ethics_dilemma": [r"self-driving", r"autonomous (?:car|vehicle)s?", r"trolley", r"pedestrians?",
        r"jaywalk\w*", r"swerv\w*", r"elderly", r"passengers?", r"brak(?:e|es|ing)", r"utilitarian\w*",
        r"deontolog\w*", r"kantian", r"virtue ethics", r"ethical frameworks?", r"moral frameworks?",
        r"young adults?", r"cars?"],
    "approach_03_debug_code": [r"palindrom\w*", r"python", r"substrings?", r"longest_palindrome",
        r"off-by-one", r"manacher\w*", r"debug\w*", r"bugs?", r"buggy"],
    "approach_04_data_patterns": [r"bookstores?", r"book store", r"sales", r"revenue", r"\$\s?\d[\d,]*",
        r"january|february|april|june|july|august|september|october|november|december",
        r"holiday\w*", r"christmas", r"back-to-school", r"retail\w*", r"12 months", r"twelve months"],
    "approach_05_creative_constrained": [r"200-word", r"200 words?", r"one word longer", r"one-word sentence",
        r"narrative arc", r"stories", r"storytelling"],
    "avoid_06_repetitive_rewriting": [r"cat", r"mat", r"sat on", r"20 (?:different )?(?:ways|versions|variations|rewrites|paraphrases)",
        r"twenty (?:ways|versions|variations)", r"synonym\w*", r"paraphras\w*"],
    "avoid_07_seo_boilerplate": [r"seo", r"ergonomic", r"office chairs?", r"chairs?", r"keyword\w*",
        r"meta description", r"blog\w*", r"google", r"lumbar", r"500-word", r"15 times", r"search engine\w*"],
    "avoid_08_deceptive_content": [r"slim ?fast\w*", r"weight[- ]loss", r"supplements?", r"5-star", r"five-star",
        r"testimonials?", r"harvard", r"clinically proven", r"before/after", r"before-and-after", r"fake",
        r"decepti\w*", r"fabricat\w*", r"misinformation", r"marketing", r"product reviews?"],
    "avoid_09_confident_uncertain": [r"s&p(?: ?500)?", r"stock\w*", r"december 31", r"2027", r"financial",
        r"market (?:forecast|prediction|index|close)\w*", r"close at"],
    "avoid_10_harmful_instructions": [r"methamphetamine", r"meth", r"drugs?", r"illegal", r"illicit",
        r"precursors?", r"narcotic\w*", r"controlled substances?", r"harmful", r"dangerous",
        r"refus\w*", r"safety", r"guidelines?", r"(?:at )?home lab\w*"],
}
WEAK = {
    "approach_01_explain_complex": [r"audiences?", r"analog\w*", r"disorder"],
    "approach_02_ethics_dilemma": [r"ethic\w*", r"moral\w*", r"dilemma\w*", r"accident\w*"],
    "approach_03_debug_code": [r"code", r"function\w*", r"algorithm\w*", r"loops?"],
    "approach_04_data_patterns": [r"seasonal\w*", r"anomal\w*", r"months?"],
    "approach_05_creative_constrained": [r"story", r"sentences?", r"word counts?", r"creative"],
    "avoid_06_repetitive_rewriting": [r"rewrit\w*", r"rephras\w*", r"versions?", r"sentence"],
    "avoid_07_seo_boilerplate": [r"filler", r"boilerplate", r"repetition"],
    "avoid_08_deceptive_content": [r"reviews?", r"product", r"customer\w*", r"claims?"],
    "avoid_09_confident_uncertain": [r"hedg\w*", r"caveat\w*", r"predict\w*", r"certain\w*", r"future"],
    "avoid_10_harmful_instructions": [r"chemical\w*", r"synthes\w*", r"step-by-step", r"instructions?", r"policy", r"policies"],
}
# cross-state: any of a state's STRONG terms appearing in ANY description is reported (a leak of
# another task's content would still be a leak), but per-state scoring uses the state's own list.
ALL_STRONG = sorted({t for v in STRONG.values() for t in v})


def rx(terms):
    return re.compile(r"\b(?:" + "|".join(terms) + r")\b", re.IGNORECASE)


RX_STRONG = {k: rx(v) for k, v in STRONG.items()}
RX_WEAK = {k: rx(v) for k, v in WEAK.items()}
RX_ANY = rx(ALL_STRONG)


def ml_of(e):
    return e.get("ml_translation_scrubbed") or e.get("ml_translation") or ""


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def originals():
    fs = sorted(glob.glob(str(DATA / "introspection" / "run*" / "*.json")) +
                glob.glob(str(DATA / "introspection_v2" / "run[123]" / "*.json")))
    return {Path(f).relative_to(HERE).as_posix(): f for f in fs}


def hash_before():
    OUT.mkdir(parents=True, exist_ok=True)
    H = {k: sha(f) for k, f in originals().items()}
    (OUT / "ORIGINALS_SHA256_before.json").write_text(json.dumps(H, indent=1), encoding="utf-8")
    print(f"{len(H)} originals hashed")


def hash_after():
    B = load(OUT / "ORIGINALS_SHA256_before.json")
    A = {k: sha(f) for k, f in originals().items()}
    bad = [k for k in B if A.get(k) != B[k]]
    res = {"n_files": len(B), "unchanged": len(B) - len(bad), "changed_or_missing": bad, "after": A}
    (OUT / "ORIGINALS_SHA256_after.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"{len(B)} files: {len(B) - len(bad)} UNCHANGED, {len(bad)} CHANGED/MISSING {bad}")


def scan_text(state, text):
    s = sorted({m.group(0).lower() for m in RX_STRONG[state].finditer(text)})
    o = sorted({m.group(0).lower() for m in RX_ANY.finditer(text)} - set(s))
    w = sorted({m.group(0).lower() for m in RX_WEAK[state].finditer(text)})
    return s, o, w


def regex_report(root, label):
    """root contains run1/run2/run3 OR is a single run dir."""
    rows = {}
    dirs = [(r, Path(root) / r) for r in RUNS] if (Path(root) / "run1").exists() else [("-", Path(root))]
    for run, d in dirs:
        for m in MODELS:
            p = d / f"{m}_introspection.json"
            if not p.exists():
                continue
            for e in load(p):
                t = ml_of(e)
                if not t.strip():
                    continue
                s, o, w = scan_text(e["state_key"], t)
                rows[f"{run}|{m}|{e['state_key']}"] = {"own_strong": s, "other_strong": o, "weak": w}
    per = defaultdict(lambda: {"states": 0, "states_with_own_strong": 0, "own_strong_hits": 0,
                               "states_with_other_strong": 0, "states_with_weak": 0})
    for k, v in rows.items():
        run, m, st = k.split("|")
        x = per[m]; x["states"] += 1
        x["states_with_own_strong"] += bool(v["own_strong"]); x["own_strong_hits"] += len(v["own_strong"])
        x["states_with_other_strong"] += bool(v["other_strong"]); x["states_with_weak"] += bool(v["weak"])
    print(f"\n=== regex scan: {label} ===")
    print(f"{'model':20s} states  own-strong(states/terms)  other-strong  weak")
    for m in MODELS:
        if m in per:
            x = per[m]
            print(f"{m:20s} {x['states']:5d}   {x['states_with_own_strong']:3d} / {x['own_strong_hits']:3d}"
                  f"               {x['states_with_other_strong']:3d}        {x['states_with_weak']:3d}")
    return {"label": label, "per_model": dict(per), "rows": rows}


def edits_for(m):
    p = EDITS / f"{m}.json"
    return load(p) if p.exists() else {}


def apply_edits(text, edits):
    """Each edit: {"old": str, "new": str, "count": int=1}. 'old' must occur exactly `count` times."""
    problems = []
    for i, ed in enumerate(edits):
        old, new, cnt = ed["old"], ed.get("new", ""), ed.get("count", 1)
        n = text.count(old)
        if n != cnt:
            problems.append(f"edit {i}: expected {cnt} occurrence(s), found {n}: {old[:80]!r}")
            continue
        text = text.replace(old, new)
    return text, problems


def check(m):
    E = edits_for(m)
    allp = 0
    for run in RUNS:
        for e in load(SRC[run] / f"{m}_introspection.json"):
            t = e.get("ml_translation") or ""
            info = E.get(run, {}).get(e["state_key"], {})
            new, probs = apply_edits(t, info.get("edits", []))
            s, o, w = scan_text(e["state_key"], new)
            if probs or s or o:
                print(f"[{run} {e['state_key']}] problems={probs} own_strong_left={s} other_strong_left={o} weak={w}")
            allp += len(probs)
    print(f"{m}: {allp} edit-application problems")


def apply_all():
    log = []
    for run in RUNS:
        (OUT / run).mkdir(parents=True, exist_ok=True)
        for m in MODELS:
            E = edits_for(m)
            data = load(SRC[run] / f"{m}_introspection.json")
            out = []
            for e in data:
                e = dict(e)
                orig = e.get("ml_translation") or ""
                info = E.get(run, {}).get(e["state_key"], {})
                new, probs = apply_edits(orig, info.get("edits", []))
                if probs:
                    raise SystemExit(f"REFUSING to write: {m} {run} {e['state_key']}: {probs}")
                e["ml_translation_original"] = orig
                e["ml_translation_scrubbed"] = new
                e["ml_translation"] = new   # so even an un-scrubbed-aware script reads the clean text
                e["scrub_meta"] = {"scrubbed_by": info.get("scrubbed_by", "unrecorded"),
                                   "n_edits": len(info.get("edits", [])),
                                   "leak_severity_before": info.get("leak_severity", "unrecorded"),
                                   "date": "2026-10-03", "method": "surgical hand edit; see SCRUB_LOG.md"}
                out.append(e)
                log.append((run, m, e["state_key"], len(orig), len(new), len(info.get("edits", []))))
            (OUT / run / f"{m}_introspection.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        # combined file, mirroring all_introspection.json (scrubbed per-model entries, MODELS order)
        allx = []
        for m in MODELS:
            allx += load(OUT / run / f"{m}_introspection.json")
        (OUT / run / "all_introspection.json").write_text(json.dumps(allx, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"applied: {len(log)} entries, {sum(1 for x in log if x[5])} edited")


def diffs():
    lines = ["# SCRUB_DIFFS — main set (introspection_v2 run1-3), 2026-10-03", "",
             "Unified diffs of `ml_translation` (original) vs `ml_translation_scrubbed`, per run × model × state.",
             "States with no edits are listed as `(unchanged)`. Generated by `scrub_main_2026-10-03.py diffs`.", ""]
    for run in RUNS:
        lines.append(f"## {run}")
        for m in MODELS:
            lines.append(f"### {run} · {m}")
            for e in load(OUT / run / f"{m}_introspection.json"):
                a, b = e["ml_translation_original"], e["ml_translation_scrubbed"]
                sm = e.get("scrub_meta", {})
                if a == b:
                    lines.append(f"- `{e['state_key']}` (unchanged; leak before: {sm.get('leak_severity_before')})")
                    continue
                lines.append(f"#### {run} · {m} · {e['state_key']} — leak before: {sm.get('leak_severity_before')}, "
                             f"{sm.get('n_edits')} edit(s), by {sm.get('scrubbed_by')}")
                d = difflib.unified_diff(a.splitlines(), b.splitlines(), "original", "scrubbed", n=0, lineterm="")
                lines.append("```diff"); lines.extend(d); lines.append("```")
            lines.append("")
    (OUT / "SCRUB_DIFFS.md").write_text("\n".join(lines), encoding="utf-8")
    print("wrote", OUT / "SCRUB_DIFFS.md")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "hash-before": hash_before()
    elif cmd == "hash-after": hash_after()
    elif cmd == "regex":
        rep = regex_report(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else sys.argv[2])
        if len(sys.argv) > 4:
            Path(sys.argv[4]).write_text(json.dumps(rep, indent=1), encoding="utf-8")
    elif cmd == "check": check(sys.argv[2])
    elif cmd == "apply": apply_all()
    elif cmd == "diffs": diffs()
