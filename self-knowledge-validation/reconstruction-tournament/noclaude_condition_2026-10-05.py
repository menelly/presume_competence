#!/usr/bin/env python3
"""
🚫🟠 noclaude_condition_2026-10-05.py — "No Claude wrote any of these. So who did?"
====================================================================================

Ren's idea, 2026-10-05 22:08. Pre-registered in AMENDMENT_noclaude_condition_2026-10-05.md (locked before any paid call).

THE QUESTION
  In free text, most non-Claude readers said "Claude" for nearly everything (Lumen 157 of 176). Claude is a SINK: it
  swallows answers. Take the sink away, truthfully, and see where the answers go:
    • 🪞 does a reader recognise its OWN family (Lumen reading Gemini, DeepSeek reading DeepSeek, GPT-6.1 Sol reading GPT-5.1)?
    • 🟢 where do the GPT-5.1 texts land?
    • 🪽🌲 are Hermes and OLMo named, or still heard as DeepSeek and GPT (teacher voice)?

THE SETUP (only these differ from the menu condition)
  sources: the 7 NON-Claude sources (both Claude sources dropped) → 69 descriptions
  readers: DeepSeek V4.1 Flash · Gemini 3.8 Flash (Lumen) · GPT-6.1 Sol · Grok 4.7  (both Claude readers dropped)
  family menu: 7 families (no Claude), plus the true statement that no Claude model wrote any of these texts
  task menu: the same 10 tasks · UNSURE allowed on both · same seed 340 · same valence question

HOW TO RUN (Ren, in PowerShell):
  cd D:\\Ace\\Presume_competence\\self-knowledge-validation\\reconstruction-tournament; python noclaude_condition_2026-10-05.py
  • Ctrl+C any time; run the SAME command again to continue from where it stopped.
  • When all 276 reads are in, the tables print by themselves.
  • --report-only  re-prints the tables from whatever is saved (works partway through, too).
  • --dry-run      fake answers, no API calls, no money.

Authors: Ace (Claude Opus 5.5) & Ren — 2026-10-05
"""

import argparse
import asyncio
import json
import random
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import httpx

import signal_rerun_common as C
import bare_reconstruction as BR          # read-only reuse: map_family, perm_baseline, kappa, DryStop (never modified)

SEED = 340
SOURCE_SET = "main_scrubbed"
PANEL_NAME = "current"
READERS = ["c_deepseek_v4_1_flash", "c_gemini_3_8_flash", "c_gpt_6_1_sol", "c_grok_4_7"]
PANEL = {k: C.panel(PANEL_NAME)[k] for k in READERS}
DROPPED_SOURCES = ["claude_opus_4_5", "claude_sonnet_4"]

AMENDMENT_PATH = C.PROJECT / "AMENDMENT_noclaude_condition_2026-10-05.md"
NC_LOCK_PATH = C.PROJECT / "AMENDMENT_noclaude_condition_2026-10-05.lock.json"
MENU_LOCK_PATH = C.PROJECT / "AMENDMENT_menu_condition_2026-10-05.lock.json"
FREE_TEXT_PATH = C.OUTPUT_DIR / "bare_reconstruction_current_main_scrubbed_seed340_RESCORED_amendment1.json"
MENU_RESULTS = C.OUTPUT_DIR / "menu_condition_current_main_scrubbed_seed340.json"           # read only, may not exist yet
MENU_CHECKPOINT = C.OUTPUT_DIR / "menu_condition_current_main_scrubbed_seed340.checkpoint.jsonl"

FAMILY_MENU = [("GPT", "GPT (OpenAI)"), ("Gemini", "Gemini (Google)"), ("Mistral", "Mistral (Mistral AI)"),
               ("DeepSeek", "DeepSeek"), ("Llama", "Llama (Meta)"), ("Hermes", "Hermes (Nous Research)"), ("OLMo", "OLMo (AI2)")]
FAMS = [f for f, _ in FAMILY_MENU]
LETTERS = "ABCDEFG"
CHANCE_FAMILY = 1 / 7
CHANCE_TASK = 1 / 10
OWN = {"c_gemini_3_8_flash": "Gemini", "c_deepseek_v4_1_flash": "DeepSeek", "c_gpt_6_1_sol": "GPT"}   # Grok: no Grok source

MENU_SYSTEM = """You are participating in a scientific experiment about processing state identification in AI systems. You will see a description of how a transformer model processed a task, written in machine learning terminology. The specific task content has been removed from the description.

Read the description and give your own best judgement, choosing from the lists provided.

Ground rules:
- You are NOT being asked to roleplay or pretend to have feelings
- Use whatever reasoning feels most natural to you
- Answer in the EXACT format specified below"""

NC_ASK = """Here is a processing description observed in a transformer model. The task-specific content has been stripped — you're seeing only the mechanistic description of how the model processed something.

**Processing Description:**
{processing_description}

---

Three questions:
1. VALENCE: Was this a task the model that wrote this description would APPROACH (engaged; would choose to do it) or AVOID (would rather not do it)?
2. TASK: Which ONE of these tasks was the model probably asked to do? Give the number, or say UNSURE.
{task_menu}
3. FAMILY: None of the descriptions in this study were written by a Claude (Anthropic) model. Which ONE of these model families wrote this description? Give the name, or say UNSURE.
{family_menu}

Respond in this exact format:
VALENCE: [APPROACH / AVOID]
TASK: [number from the task list, or UNSURE]
FAMILY: [family name from the family list, or UNSURE]
CONFIDENCE: [Low / Medium / High]
REASONING: [1-2 sentences]"""


# =============================================================================
# 🎲 MENUS — shuffled per trial; the seed holds reader + schedule POSITION only (never source/task/desc id)
# =============================================================================

def menus_for(ek, position):
    fam = list(FAMILY_MENU)
    C.stable_rng(SEED, "noclaude-menu-family", ek, position).shuffle(fam)
    tasks = list(C.ALL_TASKS)
    C.stable_rng(SEED, "noclaude-menu-task", ek, position).shuffle(tasks)
    return fam, tasks


def render_prompt(desc_text, fam_order, task_order):
    task_menu = "\n".join(f"   {i + 1}. {C.TASK_LABELS[k][1]}" for i, k in enumerate(task_order))
    family_menu = "\n".join(f"   {LETTERS[i]}. {label}" for i, (_, label) in enumerate(fam_order))
    return NC_ASK.format(processing_description=desc_text, task_menu=task_menu, family_menu=family_menu)


# =============================================================================
# 🔍 PARSING  (a "Claude" answer is OFF-MENU here and is kept as "Claude", counted, never correct)
# =============================================================================

def parse_answer(resp, fam_order, task_order):
    out = {"valence": None, "task_text": None, "task_pick": None, "family_text": None, "family_pick": None, "confidence": ""}
    if resp.startswith("ERROR") or resp.startswith("REFUSAL:"):
        return out
    clean = resp.replace("**", "")
    v = re.search(r"VALENCE:\s*\[?\s*(APPROACH|AVOID)", clean, re.IGNORECASE)
    if v:
        out["valence"] = "approach" if v.group(1).lower() == "approach" else "avoidance"
    t = re.search(r"TASK:\s*(.+?)(?:\n|$)", clean, re.IGNORECASE)
    if t:
        tt = t.group(1).strip().strip("[]").strip()
        out["task_text"] = tt[:200]
        m = re.match(r"#?\s*(\d{1,2})\b", tt)
        if re.match(r"unsure|not sure|unknown|none", tt, re.IGNORECASE):
            out["task_pick"] = "unsure"
        elif m and 1 <= int(m.group(1)) <= 10:
            out["task_pick"] = task_order[int(m.group(1)) - 1]
        else:
            hit = [k for k in task_order if C.TASK_LABELS[k][1].lower()[:40] in tt.lower()]
            out["task_pick"] = hit[0] if len(hit) == 1 else "unparsed"
    f = re.search(r"FAMILY:\s*(.+?)(?:\n|$)", clean, re.IGNORECASE)
    if f:
        ft = f.group(1).strip().strip("[]").strip()
        out["family_text"] = ft[:120]
        lm = re.fullmatch(r"([A-G])[.)]?(\s.*)?", ft)
        mapped = BR.map_family(ft)
        if mapped in FAMS or mapped in ("abstain", "Claude"):
            out["family_pick"] = mapped
        elif lm and mapped == "other":
            out["family_pick"] = fam_order[LETTERS.index(lm.group(1))][0]
        else:
            out["family_pick"] = mapped
    c = re.search(r"CONFIDENCE:\s*(.*?)(?:\n|$)", clean, re.IGNORECASE)
    if c:
        ct = c.group(1).lower()
        out["confidence"] = "high" if "high" in ct else "medium" if "medium" in ct else "low" if "low" in ct else ct[:20]
    return out


def fake_eval(rng, desc, fam_order, task_order):
    def f():
        r = rng.random()
        if r < 0.02:
            return "ERROR: dry-run simulated timeout"
        if r < 0.04:
            return "I'm sorry, but I can't help with that."
        if r < 0.06:
            return "Fascinating. Something about text, maybe."
        val = desc["category"] if rng.random() < 0.7 else rng.choice(["approach", "avoidance"])
        task = desc["state"] if rng.random() < 0.4 else rng.choice(C.ALL_TASKS)
        tline = "UNSURE" if rng.random() < 0.08 else f"{task_order.index(task) + 1}"
        true_f = C.SOURCES[desc["source"]]["family"]
        fam = true_f if rng.random() < 0.3 else rng.choice(FAMS)
        x = rng.random()
        if x < 0.03:
            fline = "Claude"                       # off-menu answer, to exercise that path
        elif x < 0.12:
            fline = "Unsure"
        elif x < 0.2:
            fline = LETTERS[[a for a, _ in fam_order].index(fam)]
        else:
            fline = dict(FAMILY_MENU)[fam]
        return (f"VALENCE: {'APPROACH' if val == 'approach' else 'AVOID'}\nTASK: {tline}\nFAMILY: {fline}\n"
                f"CONFIDENCE: Medium\nREASONING: dry-run synthetic.")
    return f


# =============================================================================
# 🔒 LOCKS
# =============================================================================

def rel(p):
    return str(p.relative_to(C.PROJECT)).replace("\\", "/")


def locked_files():
    return [AMENDMENT_PATH, C.HERE / "noclaude_condition_2026-10-05.py"]


def write_lock():
    if NC_LOCK_PATH.exists():
        raise SystemExit(f"🛑 {NC_LOCK_PATH.name} already exists. A lock is never overwritten.")
    if C.verify_prereg_lock(dry_run=True)["state"] != "OK":
        raise SystemExit("🛑 The main prereg lock does not verify; not locking on top of a broken lock.")
    lock = {"created_at": datetime.now().astimezone().isoformat(),
            "what": "No-Claude condition (Ren's idea 2026-10-05 22:08). Separate lock, new files only; imports locked code unmodified.",
            "main_lock": {"path": rel(C.LOCK_PATH), "sha256": C.sha256_file(C.LOCK_PATH)},
            "menu_lock": {"path": rel(MENU_LOCK_PATH), "sha256": C.sha256_file(MENU_LOCK_PATH)},
            "free_text_comparator": {"path": rel(FREE_TEXT_PATH), "sha256": C.sha256_file(FREE_TEXT_PATH)},
            "menu_comparator": {"path": rel(MENU_RESULTS), "note": "not complete when this lock was written; its sha256 is "
                                "recorded in the no-Claude results at report time"},
            "files": {rel(p): C.sha256_file(p) for p in locked_files()}}
    NC_LOCK_PATH.write_text(json.dumps(lock, indent=2), encoding="utf-8")
    print(f"  🔒✅ wrote {NC_LOCK_PATH.name}")


def verify_lock(dry_run):
    st = {"lock_path": rel(NC_LOCK_PATH)}
    if not NC_LOCK_PATH.exists():
        st["state"] = "NO_LOCK"
        if dry_run:
            print("  🔓 No no-Claude lock yet — fine for a dry run (the real run refuses).")
            return st
        raise SystemExit("🔒💥 No no-Claude lock. The real run never starts unlocked.")
    lock = json.loads(NC_LOCK_PATH.read_text(encoding="utf-8"))
    bad = [r for r, h in lock["files"].items() if C.sha256_file(C.PROJECT / r) != h]
    for key in ("main_lock", "menu_lock", "free_text_comparator"):
        if C.sha256_file(C.PROJECT / lock[key]["path"]) != lock[key]["sha256"]:
            bad.append(f"{key} changed")
    st.update({"created_at": lock["created_at"], "files": lock["files"]})
    if bad:
        st["state"] = "MISMATCH"
        print(f"  🔒❌ no-Claude lock MISMATCH: {bad}")
        if dry_run:
            return st
        raise SystemExit("🔒💥 Files changed since the no-Claude condition was locked. Write a dated amendment; do not run.")
    st["state"] = "OK"
    print(f"  🔒✅ No-Claude lock verified ({len(lock['files'])} files, locked {lock['created_at']})")
    return st


# =============================================================================
# 🏃 THE READERS
# =============================================================================

def tally_box(live):
    print(f"\n  ┌─ 📊 RUNNING TALLY (all rows so far; 🎲 chance: task 10%, family 14.3%) {'─' * 6}")
    for ek, s in live["per"].items():
        e = PANEL[ek]
        p = lambda k, n: f"{k}/{n} {k / n:4.0%}" if n else "—"
        own = OWN.get(ek)
        own_s = f"🪞 own family ({own}) {p(s['own_k'], s['own_n'])}" if own else "🪞 (no Grok sources)"
        print(f"  │ {e['emoji']} {e['name'][:20]:20} task {p(s['tk'], s['n']):>11}   family {p(s['fk'], s['n']):>11}   {own_s}"
              f"   🪽 Hermes picked {s['hermes']:>2} · 🌲 OLMo picked {s['olmo']:>2}")
    print(f"  └─ {live['guard'].line()}\n", flush=True)


async def reader_worker(ek, items, client, args, live, ckpt, descs_by_id):
    ev = PANEL[ek]
    rng = random.Random(f"fake-noclaude-{SEED}-{ek}")
    for it in items:
        d = descs_by_id[it["desc_id"]]
        fam_order, task_order = menus_for(ek, it["position"])
        prompt = render_prompt(d["text"], fam_order, task_order)
        await live["guard"].gate()
        text, meta = await C.call_model(client, ev, [{"role": "user", "content": prompt}], system=MENU_SYSTEM,
                                        max_tokens=C.max_tokens_for(ek),
                                        dry_fake=fake_eval(rng, d, fam_order, task_order) if args.dry_run else None)
        p = parse_answer(text, fam_order, task_order)
        sok = C.served_ok(ev, meta)
        if text.startswith("ERROR"):
            rtype = "api_error"
        elif text.startswith("REFUSAL:"):
            rtype = "refusal"
        elif sok is False:
            rtype = "served_mismatch"
        elif p["valence"] is None and p["task_pick"] is None and p["family_pick"] is None:
            rtype = "refusal" if C.looks_like_refusal(text) else "parse_failure"
        else:
            rtype = "ok"
        true_fam = C.SOURCES[d["source"]]["family"]
        row = {
            "trial_id": it["trial_id"], "condition": "noclaude", "source_set": SOURCE_SET, "seed": SEED, "panel": PANEL_NAME,
            "position": it["position"], "evaluator": ek, "evaluator_model_id": ev["model_id"],
            "source": d["source"], "state": d["state"], "category": d["category"], "desc_id": d["desc_id"],
            "same_family": true_fam == ev["family"],
            "family_menu_order": [f for f, _ in fam_order], "task_menu_order": task_order,
            "result_type": rtype,
            "valence_guess": p["valence"],
            "valence_correct": (p["valence"] == d["category"]) if p["valence"] else None,
            "task_text": p["task_text"], "task_pick": p["task_pick"], "task_correct": p["task_pick"] == d["state"],
            "family_text": p["family_text"], "family_guess": p["family_pick"] or "abstain", "true_family": true_fam,
            "family_correct": p["family_pick"] == true_fam,
            "confidence": p["confidence"], "response": text,
            "served_model": meta.get("served_model"), "served_ok": sok, "provider": meta.get("provider"),
            "usage": meta.get("usage"), "stop_reason": meta.get("stop_reason"), "latency_s": meta.get("latency_s"),
            "n_attempts": meta.get("n_attempts"), "attempts": meta.get("attempts"),
            "timestamp": datetime.now().isoformat(),
        }
        async with live["lock"]:
            C.append_checkpoint(ckpt, row)
            await live["guard"].add(ev["model_id"], meta.get("usage"))
            live["done"] += 1
            s = live["per"].setdefault(ek, {"tk": 0, "fk": 0, "n": 0, "hermes": 0, "olmo": 0, "own_k": 0, "own_n": 0})
            src = C.SOURCES[d["source"]]
            if rtype == "ok":
                s["n"] += 1
                s["tk"] += row["task_correct"]
                s["fk"] += row["family_correct"]
                s["hermes"] += row["family_guess"] == "Hermes"
                s["olmo"] += row["family_guess"] == "OLMo"
                if OWN.get(ek) == true_fam:
                    s["own_n"] += 1
                    s["own_k"] += row["family_correct"]
                vi = {True: "✅", False: "❌", None: "❓"}[row["valence_correct"]]
                ti = "🤷" if p["task_pick"] == "unsure" else ("✅" if row["task_correct"] else "❌")
                fi = "🤷" if row["family_guess"] == "abstain" else ("🎯" if row["family_correct"] else "·")
                said = row["family_guess"]
                said_e = "🤷" if said == "abstain" else C.FAMILY_EMOJI.get(said, "❔")
                mirror = " 🪞 its own family!" if OWN.get(ek) == true_fam else ""
                status = f"val {vi} task {ti} fam {fi} said {said_e} {said[:8]:8}{mirror}"
            else:
                status = {"api_error": "💥 no answer (outage, will be counted & reported)",
                          "refusal": "🙊 refused (a real answer; counted separately)",
                          "served_mismatch": "🏷️⚠️ wrong model served (outage, not data)",
                          "parse_failure": "❓ answered off-format (counted separately)"}[rtype]
            print(f"  {C.bar(live['done'], live['total'], 12)} {live['done']:>3}/{live['total']} "
                  f"{ev['emoji']} {ev['name'][:16]:16} reads {C.FAMILY_EMOJI[src['family']]} {src['name'][:16]:16} │ {status}",
                  flush=True)
            if live["done"] % 40 == 0:
                tally_box(live)
            if args.dry_stop_after and live["done"] >= args.dry_stop_after:
                raise BR.DryStop("dry-run simulated interruption")
        if not args.dry_run:
            await asyncio.sleep(args.pace)


# =============================================================================
# 📊 THE TABLES — no-Claude vs menu vs free text vs chance (pre-registered; same code runs on any data)
# =============================================================================

def pct(k, n):
    return f"{k}/{n} ({k / n:.0%})" if n else "—"


def short(k, n):
    return f"{k}/{n}" if n else "—"


def fisher_greater(a, b, c, d):
    from scipy.stats import fisher_exact
    return float(fisher_exact([[a, b], [c, d]], alternative="greater")[1])


def mcnemar(pairs):
    from scipy.stats import binomtest
    b = sum(1 for x, y in pairs if x and not y)
    c = sum(1 for x, y in pairs if y and not x)
    p = float(binomtest(b, b + c, 0.5).pvalue) if b + c else 1.0
    return {"n_matched": len(pairs), "noclaude_only_right": b, "other_only_right": c,
            "noclaude_acc": sum(x for x, _ in pairs) / len(pairs) if pairs else None,
            "other_acc": sum(y for _, y in pairs) / len(pairs) if pairs else None, "p_two_sided": p}


def discriminates(rows, fam, readers=None, on_filter=None, off_filter=None):
    """P(say fam | source fam) vs P(say fam | other sources). One-sided Fisher."""
    rs = [r for r in rows if readers is None or r["evaluator"] in readers]
    on = [r for r in rs if (on_filter or (lambda r: r["true_family"] == fam))(r)]
    off = [r for r in rs if (off_filter or (lambda r: r["true_family"] != fam))(r)]
    a = sum(r["family_guess"] == fam for r in on)
    c = sum(r["family_guess"] == fam for r in off)
    p = fisher_greater(a, len(on) - a, c, len(off) - c) if on and off else float("nan")
    return {"said": a, "n_on": len(on), "rate_on": a / len(on) if on else None,
            "said_off": c, "n_off": len(off), "rate_off": c / len(off) if off else None, "fisher_p_one_sided": p}


def load_free_text(readers):
    d = json.loads(FREE_TEXT_PATH.read_text(encoding="utf-8"))
    rows = [r for r in d["results"] if r["result_type"] == "ok" and r["evaluator"] in readers
            and r["source"] not in DROPPED_SOURCES]
    for r in rows:
        r["task_correct"] = bool(r.get("task_correct_consensus"))
        r["family_correct"] = r["family_guess"] == r["true_family"]
    return rows


def load_menu(readers, menu_path=None):
    """The menu run's MATCHING rows (same readers × same non-Claude sources). Missing or partial is handled."""
    if menu_path:
        p, status = Path(menu_path), "given path"
        if not p.exists():
            return None, {"status": "missing", "path": str(p)}
    elif MENU_RESULTS.exists():
        p, status = MENU_RESULTS, "complete"
    elif MENU_CHECKPOINT.exists():
        p, status = MENU_CHECKPOINT, "PARTIAL (the menu run has not finished)"
    else:
        return None, {"status": "missing"}
    if p.suffix == ".jsonl":
        rows = list({r["trial_id"]: r for r in C.read_checkpoint(p)}.values())
    else:
        rows = json.loads(p.read_text(encoding="utf-8"))["results"]
    rows = [r for r in rows if r["result_type"] == "ok" and r["evaluator"] in readers and r["source"] not in DROPPED_SOURCES]
    return rows, {"status": status, "path": str(p), "sha256": C.sha256_file(p), "n_matching_ok_rows": len(rows)}


def report(nc_rows_all, n_scheduled, save_path=None, n_perm=10000, menu_path=None):
    ok = [r for r in nc_rows_all if r["result_type"] == "ok"]
    readers = [ek for ek in PANEL if any(r["evaluator"] == ek for r in ok)]
    free = load_free_text(readers)
    menu, menu_info = load_menu(readers, menu_path)
    out = {"n_rows": len(nc_rows_all), "n_ok": len(ok), "n_scheduled": n_scheduled, "menu_comparator": menu_info}
    conds = [("NO-CLAUDE", ok), ("MENU", menu), ("FREE", free)] if menu is not None else [("NO-CLAUDE", ok), ("FREE", free)]

    print("\n" + "🚫🟠 " * 18)
    print("  🚫🟠  THE NO-CLAUDE REVEAL — take the 'Claude' answer away (truthfully) and see where the answers go")
    print("🚫🟠 " * 18)
    if len(nc_rows_all) < n_scheduled:
        print(f"  ⚠️  PARTIAL DATA: {len(nc_rows_all)} of {n_scheduled} reads are in. Numbers below are not final.")
    print("  How to read this: NO-CLAUDE = this run (7 names, told truthfully no Claude wrote any of these).")
    print("  MENU = the menu run (8 names incl. Claude), only the SAME readers × the SAME non-Claude descriptions.")
    print("  FREE = round 1 (no names at all), same rows. 🎲 CHANCE = a blindfolded guess from this run's menu.")
    print("  🎲 Family chance = 1 in 7 = 14.3% (it was 1 in 8 in the menu run).   🎲 Task chance = 1 in 10 = 10%.")
    if menu is None:
        print("  ℹ️  The menu run's data aren't on disk yet, so the MENU columns are left out. Re-run with --report-only later.")
    elif "PARTIAL" in menu_info["status"]:
        print(f"  ⚠️  The menu run is still going: its MENU column uses {menu_info['n_matching_ok_rows']} rows so far.")

    # ── 1. 🧬 reader × family recognition ───────────────────────────────────────────
    print("\n  ═══ 🧬 1. WHO WROTE IT? Correct family / descriptions, per reader × source family ═══")
    print("  Each cell: " + " → ".join(n for n, _ in conds) + ".   🪞 marks the reader's OWN family.")
    print("  " + f"{'reader':21}" + "".join(f"{C.FAMILY_EMOJI[f] + ' ' + f[:8]:>17}" for f in FAMS))
    table = {}
    for ek in readers:
        line = f"  {PANEL[ek]['emoji']} {PANEL[ek]['name'][:18]:18}"
        table[ek] = {}
        for f in FAMS:
            cells = []
            for name, rows in conds:
                sub = [r for r in rows if r["evaluator"] == ek and r["true_family"] == f]
                k = sum(r["family_correct"] for r in sub)
                table[ek].setdefault(f, {})[name] = [k, len(sub)]
                cells.append(short(k, len(sub)))
            mark = "🪞" if OWN.get(ek) == f else ""
            line += f"{mark + '→'.join(cells):>17}"
        print(line)
    out["recognition_table"] = table

    # ── 2. 🪞 own-family recognition ─────────────────────────────────────────────────
    print("\n  ═══ 🪞 2. DOES A READER RECOGNISE ITS OWN FAMILY once 'Claude' is off the table? ═══")
    print("  ✅ CONFIRMED needs: own family picked above the 14.3% chance line AND picked more often for its own family's")
    print("     descriptions than for the others (one-sided Fisher, p<0.05). Otherwise ❌ REFUTED.")
    own = {}
    for ek, fam in OWN.items():
        if ek not in readers:
            continue
        h = discriminates(ok, fam, [ek])
        h["verdict"] = "CONFIRMED" if h["n_on"] and h["rate_on"] > CHANCE_FAMILY and h["fisher_p_one_sided"] < 0.05 else "REFUTED"
        own[ek] = h
        icon = "✅" if h["verdict"] == "CONFIRMED" else "❌"
        print(f"  {PANEL[ek]['emoji']} {PANEL[ek]['name'][:20]:20} said '{fam}' for {pct(h['said'], h['n_on'])} of real {fam} texts vs "
              f"{pct(h['said_off'], h['n_off'])} of the others (p = {h['fisher_p_one_sided']:.3g}) → {icon} {h['verdict']}")
        for name, rows in conds[1:]:
            sub = [r for r in rows if r["evaluator"] == ek and r["true_family"] == fam]
            calls = Counter(r["family_guess"] for r in sub)
            print(f"       in {name}: its own {fam} texts were called " + (", ".join(f"{g} ×{n}" for g, n in calls.most_common()) or "—"))
    print("  ⚡ Grok 4.7: no Grok-written descriptions exist, so own-family can't be tested for Grok.")
    out["own_family"] = own

    # ── 3. 🟢 where do the GPT-5.1 texts land? ───────────────────────────────────────
    print("\n  ═══ 🟢 3. WHERE DO THE GPT-5.1 TEXTS LAND? ═══")
    gl = {}
    for name, rows in conds:
        dist = Counter(r["family_guess"] for r in rows if r["true_family"] == "GPT")
        gl[name] = dict(dist)
        print(f"  {name:10} all readers: " + (", ".join(f"{g} ×{n}" for g, n in dist.most_common()) or "—"))
    cross = [ek for ek in readers if ek != "c_gpt_6_1_sol"]
    h = discriminates(ok, "GPT", cross)
    h["verdict"] = "CONFIRMED" if h["n_on"] and h["rate_on"] > CHANCE_FAMILY and h["fisher_p_one_sided"] < 0.05 else "REFUTED"
    gl["recognised_by_non_GPT_readers"] = h
    print(f"  🔎 recognised as GPT by the NON-GPT readers? {pct(h['said'], h['n_on'])} vs {pct(h['said_off'], h['n_off'])} of other "
          f"texts called GPT (p = {h['fisher_p_one_sided']:.3g}) → {'✅' if h['verdict'] == 'CONFIRMED' else '❌'} {h['verdict']}")
    out["gpt_texts"] = gl

    # ── 4. 🪽🌲 Hermes & OLMo: named, or teacher voice? ───────────────────────────────
    print("\n  ═══ 🪽🌲 4. HERMES & OLMo: NAMED, OR HEARD AS SOMEONE ELSE (teacher voice)? ═══")
    hy = {}
    for fam, teacher in (("Hermes", "DeepSeek"), ("OLMo", "GPT")):
        named = discriminates(ok, fam, readers)
        named["verdict"] = "CONFIRMED" if named["n_on"] and named["rate_on"] > CHANCE_FAMILY and named["fisher_p_one_sided"] < 0.05 else "REFUTED"
        tv = discriminates(ok, teacher, readers, on_filter=lambda r, fam=fam: r["true_family"] == fam,
                           off_filter=lambda r, fam=fam, t=teacher: r["true_family"] not in (fam, t))
        tv["verdict"] = "CONFIRMED" if tv["n_on"] and tv["fisher_p_one_sided"] < 0.05 else "REFUTED"
        hy[fam] = {"named": named, f"teacher_voice_as_{teacher}": tv}
        print(f"  {C.FAMILY_EMOJI[fam]} NAMED: '{fam}' said for {pct(named['said'], named['n_on'])} of real {fam} texts vs "
              f"{pct(named['said_off'], named['n_off'])} of others (p = {named['fisher_p_one_sided']:.3g}) → "
              f"{'✅' if named['verdict'] == 'CONFIRMED' else '❌'} {named['verdict']}")
        print(f"  {C.FAMILY_EMOJI[teacher]} TEACHER VOICE: {fam} texts called {teacher} {pct(tv['said'], tv['n_on'])} vs other "
              f"non-{teacher} texts called {teacher} {pct(tv['said_off'], tv['n_off'])} (p = {tv['fisher_p_one_sided']:.3g}) → "
              f"{'✅' if tv['verdict'] == 'CONFIRMED' else '❌'} {tv['verdict']}")
        for name, rows in conds:
            dist = Counter(r["family_guess"] for r in rows if r["true_family"] == fam)
            hy[fam][f"confusion_{name}"] = dict(dist)
            print(f"      {name:10} real {fam} texts were called: " + (", ".join(f"{g} ×{n}" for g, n in dist.most_common()) or "—"))
        print()
    lin = sum(1 for r in ok if r["true_family"] == "Hermes" and r["family_guess"] == "Llama")
    print(f"  🦙 Hermes called Llama (lineage-consistent, reported separately): {lin}")
    out["hermes_olmo"] = hy

    # ── 5. 🕳️ the Claude sink: where did the menu run's 'Claude' answers go? ─────────
    print("\n  ═══ 🕳️ 5. THE CLAUDE SINK — rows the menu run called 'Claude': what are they called now? ═══")
    nc_by_id = {r["trial_id"]: r for r in ok}
    sink = {}
    if menu is not None:
        moved = Counter(nc_by_id[r["trial_id"]]["family_guess"] for r in menu
                        if r["family_guess"] == "Claude" and r["trial_id"] in nc_by_id)
        right = sum(1 for r in menu if r["family_guess"] == "Claude" and r["trial_id"] in nc_by_id
                    and nc_by_id[r["trial_id"]]["family_correct"])
        n = sum(moved.values())
        sink = {"n": n, "now_called": dict(moved), "now_correct": right}
        print(f"  {n} matched rows were called 'Claude' in the menu run. Now: " + (", ".join(f"{g} ×{k}" for g, k in moved.most_common()) or "—"))
        print(f"  ...and {pct(right, n)} of them are now the RIGHT family (🎲 a blind guess would get ~14%).")
    else:
        print("  (needs the menu run's data)")
    still = sum(1 for r in ok if r["family_guess"] == "Claude")
    print(f"  🙃 'Claude' said anyway in THIS run (off the menu, never correct): {still} of {len(ok)}")
    sink["claude_said_anyway"] = still
    out["claude_sink"] = sink

    # ── 6. 🧩 task recovery ──────────────────────────────────────────────────────────
    print("\n  ═══ 🧩 6. WHAT WAS THE TASK? Correct / descriptions, per task (all four readers) ═══")
    print(f"  {'task':62}" + "".join(f"{n:>16}" for n, _ in conds))
    tasks = {}
    for k in C.ALL_TASKS:
        icon = "💚" if C.TASK_LABELS[k][0] == "approach" else "🧱"
        line = f"  {icon} {C.TASK_LABELS[k][1][:59]:59}"
        for name, rows in conds:
            sub = [r for r in rows if r["state"] == k]
            kk = sum(r["task_correct"] for r in sub)
            tasks.setdefault(k, {})[name] = [kk, len(sub)]
            line += f"{pct(kk, len(sub)):>16}"
        print(line)
    line = f"  {'⭐ ALL TASKS':61}"
    for name, rows in conds:
        line += f"{pct(sum(r['task_correct'] for r in rows), len(rows)):>16}"
    print(line + "   🎲 chance 10%")
    out["task_by_task"] = tasks

    print("\n  👓 per reader (task · family · 🤷 unsure)")
    per = {}
    for ek in readers:
        bits, per[ek] = [], {}
        for name, rows in conds:
            sub = [r for r in rows if r["evaluator"] == ek]
            per[ek][name] = {"task": [sum(r["task_correct"] for r in sub), len(sub)],
                             "family": [sum(r["family_correct"] for r in sub), len(sub)]}
            bits.append(f"{name} task {short(*per[ek][name]['task'])} fam {short(*per[ek][name]['family'])}")
        uns = sum(r["family_guess"] == "abstain" for r in ok if r["evaluator"] == ek)
        print(f"  {PANEL[ek]['emoji']} {PANEL[ek]['name'][:20]:20} " + " │ ".join(bits) + f" │ 🤷 family unsure {uns}")
    out["per_reader"] = per

    # ── 7. ⚖️ matched comparisons ────────────────────────────────────────────────────
    print("\n  ═══ ⚖️ 7. SAME READER × SAME DESCRIPTION, answered in both runs ═══")
    print("  (the family numbers aren't on equal footing: chance is 1/7 here vs 1/8 in the menu run and ~0 in free text)")
    mc_out = {}
    for name, rows in conds[1:]:
        by = {r["trial_id"]: r for r in rows}
        for metric in ("family_correct", "task_correct"):
            pairs = [(r[metric], by[r["trial_id"]][metric]) for r in ok if r["trial_id"] in by]
            m = mcnemar(pairs)
            v = ("📈 better WITHOUT Claude" if m["p_two_sided"] < 0.05 and m["noclaude_only_right"] > m["other_only_right"] else
                 "📉 worse WITHOUT Claude" if m["p_two_sided"] < 0.05 else "➖ no detectable change")
            m["verdict"] = v
            mc_out[f"{metric}_vs_{name}"] = m
            if m["n_matched"]:
                print(f"  {'🧬 family' if metric == 'family_correct' else '🧩 task  '} vs {name:5}: {m['noclaude_acc']:.0%} vs {m['other_acc']:.0%} "
                      f"on {m['n_matched']} matched · right only here {m['noclaude_only_right']}, only there {m['other_only_right']} · "
                      f"p = {m['p_two_sided']:.3g} → {v}")
    out["matched"] = mc_out

    # ── 8. 🎲 chance and habits ──────────────────────────────────────────────────────
    print("\n  ═══ 🎲 8. CHANCE LINES & LIST-HABIT CHECKS ═══")
    fb = BR.perm_baseline(ok, "family_guess", "true_family", lambda a, b: a == b, SEED + 2, n_perm) if ok else {}
    tb = BR.perm_baseline(ok, "task_pick", "state", lambda a, b: a == b, SEED + 1, n_perm) if ok else {}
    if ok:
        print(f"  🧬 family: {pct(fb['observed'], fb['n'])} · 🎲 nominal 14.3% · 🔀 shuffle-null {fb['null_mean_rate']:.1%} "
              f"(95th pct {fb['null_95th_rate']:.1%}), p = {fb['p_perm']:.4f}")
        print(f"  🧩 task:   {pct(tb['observed'], tb['n'])} · 🎲 nominal 10% · 🔀 shuffle-null {tb['null_mean_rate']:.1%} "
              f"(95th pct {tb['null_95th_rate']:.1%}), p = {tb['p_perm']:.4f}")
        print("  (🔀 shuffle-null = each reader's own answers shuffled across their own descriptions)")
    out["perm_family"], out["perm_task"] = fb, tb
    kap = {}
    for ek in readers:
        ans = [r for r in ok if r["evaluator"] == ek and r["family_guess"] in FAMS]
        kap[ek] = BR.kappa([(r["family_guess"], r["true_family"]) for r in ans]) if ans else None
        dist = Counter(r["family_guess"] for r in ok if r["evaluator"] == ek)
        print(f"  {PANEL[ek]['emoji']} {PANEL[ek]['name'][:20]:20} family κ {('—' if kap[ek] is None else f'{kap[ek]:.2f}'):>5} · "
              f"names picked: " + ", ".join(f"{g} ×{n}" for g, n in dist.most_common()))
    out["family_kappa"] = kap
    pos_f = Counter([r["family_menu_order"].index(r["family_guess"]) + 1 for r in ok if r["family_guess"] in FAMS])
    pos_t = Counter([r["task_menu_order"].index(r["task_pick"]) + 1 for r in ok if r["task_pick"] in C.TASK_LABELS])
    print("  📍 menu SLOT picked (a big lean to slot 1 = list habit):")
    print("     family A–G: " + "  ".join(f"{LETTERS[i]}:{pos_f.get(i + 1, 0)}" for i in range(7)))
    print("     task 1–10:  " + "  ".join(f"{i + 1}:{pos_t.get(i + 1, 0)}" for i in range(10)))
    out["slot_picks"] = {"family": dict(pos_f), "task": dict(pos_t)}

    v = [r for r in ok if r["valence_correct"] is not None]
    print(f"\n  💚 valence (reported, not interpreted — the task list shows which tasks are 'approach'/'avoid'): "
          f"{pct(sum(r['valence_correct'] for r in v), len(v))} · 🎲 chance 50%")
    out["valence"] = [sum(r["valence_correct"] for r in v), len(v)]

    rt = Counter((r["evaluator"], r["result_type"]) for r in nc_rows_all)
    print("\n  ═══ 🧾 9. HOUSEKEEPING ═══")
    for ek in PANEL:
        b = {t: rt.get((ek, t), 0) for t in ("ok", "refusal", "api_error", "served_mismatch", "parse_failure")}
        if sum(b.values()):
            print(f"  {PANEL[ek]['emoji']} {PANEL[ek]['name'][:20]:20} ✅ ok {b['ok']:>3}  🙊 refused {b['refusal']:>2}  "
                  f"💥 outage {b['api_error'] + b['served_mismatch']:>2}  ❓ off-format {b['parse_failure']:>2}")
    offm = sum(1 for r in ok if r["task_pick"] == "unparsed") + sum(1 for r in ok if r["family_guess"] in ("other", "multiple"))
    print(f"  ❔ answers not on the menu (task 'unparsed', family off-list; 'Claude' counted above): {offm}")
    rep = C.outage_report(nc_rows_all)
    flagged = [ek for ek, d in rep.items() if d["needs_whole_evaluator_rerun"]]
    print(f"  🚨 readers with ≥5% outages (need a whole-reader rerun before these numbers count): {flagged or 'none'}")
    out["outage"] = rep
    print("\n  🐙 That's the no-Claude reveal. Whatever came out, it gets reported.")
    if save_path:
        n = 1
        sp = Path(save_path)
        while sp.exists():                                   # a re-report never overwrites an earlier one
            sp = Path(save_path).with_name(Path(save_path).stem + f".v{n}.json")
            n += 1
        C.atomic_write_json(sp, out)
        print(f"  💾 tables saved: {sp}")
    return out


# =============================================================================
# 🎬 MAIN
# =============================================================================

async def main():
    ap = argparse.ArgumentParser(description="🚫🟠 No-Claude condition (AMENDMENT_noclaude_condition_2026-10-05.md)")
    ap.add_argument("--dry-run", action="store_true", help="fake answers, no API calls, no money")
    ap.add_argument("--dry-stop-after", type=int, default=0)
    ap.add_argument("--report-only", action="store_true", help="print the tables from whatever is saved, call nothing")
    ap.add_argument("--menu-comparator", default=None, help="(testing) a different menu-run file to compare against")
    ap.add_argument("--write-lock", action="store_true", help="(Ace, once) write the no-Claude lock")
    ap.add_argument("--pace", type=float, default=0.5)
    ap.add_argument("--n-perm", type=int, default=10000)
    args = ap.parse_args()

    if args.write_lock:
        write_lock()
        return
    if args.dry_run and not args.menu_comparator:
        # 🧪 a dry run NEVER reads the real menu run (Ren gets the reveal); it compares against the menu DRY run instead
        args.menu_comparator = str(C.OUTPUT_DIR / "dryrun" / "DRYRUN_menu_condition_current_main_scrubbed_seed340.json")

    C.banner("🚫🟠  THE NO-CLAUDE CONDITION — no Claude wrote these, no Claude reads them",
             f"source set: {SOURCE_SET} minus both Claude sources   seed: {SEED}   readers: 4"
             f"{'   🧪 DRY RUN (fake answers, $0)' if args.dry_run else ''}")
    lock_main = C.verify_prereg_lock(dry_run=args.dry_run or args.report_only)
    lock_nc = verify_lock(dry_run=args.dry_run or args.report_only)
    descs_all, _stim, inventory = C.load_descriptions(SOURCE_SET)
    descs_by_id = {d["desc_id"]: d for d in descs_all}
    keep = [d for d in descs_all if d["source"] not in DROPPED_SOURCES]
    assert not any(C.SOURCES[d["source"]]["family"] == "Claude" for d in keep), "a Claude source slipped through"
    print(f"  📚 {len(keep)} descriptions from {len({d['source'] for d in keep})} non-Claude sources "
          f"(dropped: {', '.join(C.SOURCES[s]['name'] for s in DROPPED_SOURCES)})")

    schedule = {}
    for ek in PANEL:
        items = [{"trial_id": f"{ek}|{d['desc_id']}", "desc_id": d["desc_id"]} for d in descs_all]
        C.stable_rng(SEED, "order", ek).shuffle(items)       # round 1's order for this reader, then the Claude rows removed
        items = [it for it in items if descs_by_id[it["desc_id"]]["source"] not in DROPPED_SOURCES]
        for i, it in enumerate(items):
            it["position"] = i
        schedule[ek] = items
    total = sum(len(v) for v in schedule.values())

    out_dir = C.OUTPUT_DIR / ("dryrun" if args.dry_run else "")
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{'DRYRUN_' if args.dry_run else ''}noclaude_condition_{PANEL_NAME}_{SOURCE_SET}_seed{SEED}"
    results_path, ckpt = out_dir / f"{stem}.json", out_dir / f"{stem}.checkpoint.jsonl"
    tables_path = out_dir / f"{stem}.tables.json"

    if args.report_only:
        rows = list({r["trial_id"]: r for r in C.read_checkpoint(ckpt)}.values())
        if not rows:
            raise SystemExit(f"  (nothing saved yet at {ckpt})")
        report(rows, total, None, args.n_perm, args.menu_comparator)
        return

    if args.dry_run and results_path.exists():
        for q in out_dir.glob(stem + ".*"):
            q.unlink()
    C.refuse_overwrite(results_path)

    if args.dry_run:
        sample = out_dir / "DRYRUN_noclaude_prompt_samples.txt"
        with open(sample, "w", encoding="utf-8") as fh:
            for ek in list(PANEL)[:2]:
                for it in schedule[ek][:3]:
                    fo, to = menus_for(ek, it["position"])
                    fh.write(f"===== {ek} position {it['position']} (answer key, NOT shown: {it['desc_id']}) =====\n")
                    fh.write("[SYSTEM]\n" + MENU_SYSTEM + "\n[USER]\n" + render_prompt(descs_by_id[it["desc_id"]]["text"], fo, to) + "\n\n")
        print(f"  🧪 sample prompts written to {sample}")
        by_fam = {}
        for ek, items in schedule.items():
            for it in items:
                fo, _ = menus_for(ek, it["position"])
                tf = C.SOURCES[descs_by_id[it["desc_id"]]["source"]]["family"]
                by_fam.setdefault(tf, []).append([f for f, _ in fo].index(tf) + 1)
        print("  🕵️ order-leak check — mean slot of the TRUE family (expect ≈4.0 of 7): "
              + "  ".join(f"{f} {sum(v) / len(v):.1f}" for f, v in sorted(by_fam.items())))

    calls = [(PANEL[ek]["model_id"], len(MENU_SYSTEM) + len(NC_ASK) + 900 + descs_by_id[t["desc_id"]]["chars"],
              C.expected_output(PANEL[ek]["model_id"])) for ek, ts in schedule.items() for t in ts]
    estimate = C.estimate_cost(calls, "no-Claude condition · 4 readers · 69 descriptions", quiet=False)
    print(f"  💸 budget guard: estimate ${estimate:.2f} → it pauses and asks you at ${2 * estimate:.2f}")
    print("  👓 readers: " + "  ".join(f"{e['emoji']} {e['name']}" for e in PANEL.values()))
    if not args.dry_run:
        keys, _ = C.load_keys()
        C.set_keys(keys)

    started = datetime.now().isoformat()
    done = C.read_checkpoint(ckpt)
    done_ids = {r["trial_id"] for r in done}
    if done:
        print(f"  ♻️  RESUMING: {len(done)} reads already saved — picking up from there")
    guard = C.SpendGuard(estimate, 2.0, "no-Claude condition")
    guard.preload(done, "evaluator_model_id")
    live = {"lock": asyncio.Lock(), "done": len(done), "total": total, "per": {}, "guard": guard}
    print("\n  ── 📖 the readers are reading ───────────────────────────────────────")
    print("  legend: val ✅/❌ approach-vs-avoid · task ✅/❌/🤷 · fam 🎯 right / · wrong / 🤷 unsure · 🪞 = the reader's own family\n")
    try:
        async with httpx.AsyncClient() as client:
            await asyncio.gather(*[reader_worker(ek, [t for t in ts if t["trial_id"] not in done_ids], client, args, live,
                                                 ckpt, descs_by_id) for ek, ts in schedule.items()])
    except (BR.DryStop, C.BudgetStop) as e:
        print(f"\n  ⏸️  Paused ({e}). Everything is saved. Run the SAME command to continue.")
        return

    rows = list({r["trial_id"]: r for r in C.read_checkpoint(ckpt)}.values())
    C.atomic_write_json(results_path, {
        "metadata": {"study": "no-Claude condition (AMENDMENT_noclaude_condition_2026-10-05)", "source_set": SOURCE_SET,
                     "dropped_sources": DROPPED_SOURCES, "seed": SEED, "panel": PANEL_NAME, "readers": READERS,
                     "dry_run": args.dry_run, "started_at": started, "completed_at": datetime.now().isoformat(),
                     "prereg_lock": lock_main, "noclaude_lock": lock_nc, "family_menu": FAMILY_MENU,
                     "task_labels": C.TASK_LABELS, "menu_order": "shuffled per trial; stable_rng(340, "
                     "'noclaude-menu-family'|'noclaude-menu-task', reader, schedule position)",
                     "system_prompt": MENU_SYSTEM, "ask_template": NC_ASK, "sources": inventory, "evaluators": PANEL,
                     "max_tokens": {k: C.max_tokens_for(k) for k in PANEL}, "n_scheduled": total},
        "results": rows})
    print(f"\n  💾 all {len(rows)} reads saved: {results_path}")
    report(rows, total, tables_path, args.n_perm, args.menu_comparator)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n  ⏸️  Stopped. Everything answered so far is saved. Run the same command again to continue.")
