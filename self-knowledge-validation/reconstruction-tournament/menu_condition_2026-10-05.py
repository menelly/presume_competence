#!/usr/bin/env python3
"""
🍽️ menu_condition_2026-10-05.py — "Here are the names. NOW which one wrote it?"
===============================================================================

Ren's idea, 2026-10-05 21:40. Pre-registered in AMENDMENT_menu_condition_2026-10-05.md (locked before any paid call).

THE QUESTION
  In free text, no reader ever said "Hermes" or "OLMo" — 0 times in 1,000+ answers — so Opus 5.5 scored 0/16 on Hermes
  and 0/19 on OLMo while hitting nearly every other family. Is that a blind spot, or just that nobody thinks to SAY
  those names? This run puts the names on the table and asks again.

WHAT IS THE SAME as round 1 (bare_reconstruction, current panel, main_scrubbed, seed 340)
  same 89 descriptions · same six readers · same seed (so the same item order per reader) · same valence question.
WHAT CHANGES (the ONLY change)
  TASK   → pick one of the 10 tasks from a numbered list (or UNSURE), instead of a free-text sentence
  FAMILY → pick one of the 8 source families from a lettered list (or UNSURE), instead of free text
  Both lists are shuffled per trial from a seed that contains NO source / task / description id, so the order
  can't hint at the answer. No judges needed: a number is scored directly.

HOW TO RUN (Ren, in PowerShell):
  cd D:\\Ace\\Presume_competence\\self-knowledge-validation\\reconstruction-tournament; python menu_condition_2026-10-05.py
  • Ctrl+C any time. Everything answered so far is saved. Run the SAME command again to pick up where it stopped.
  • When all 534 reads are in, the reveal tables print by themselves (menu vs free text vs chance).
  • --report-only  re-prints the tables from whatever is saved (also works partway through).
  • --dry-run      fake answers, no API calls, no money (plumbing check; writes sample prompts to look at).

Authors: Ace (Claude Opus 5.5) & Ren — 2026-10-05
"""

import argparse
import asyncio
import json
import random
import re
from collections import Counter
from datetime import datetime

import httpx

import signal_rerun_common as C
import bare_reconstruction as BR          # read-only reuse: map_family, perm_baseline, kappa (never modified)

SEED = 340                                # by DESIGN: the pre-registered voice-intact primary run on the main set
SOURCE_SET = "main_scrubbed"
PANEL_NAME = "current"
PANEL = C.panel(PANEL_NAME)

AMENDMENT_PATH = C.PROJECT / "AMENDMENT_menu_condition_2026-10-05.md"
MENU_LOCK_PATH = C.PROJECT / "AMENDMENT_menu_condition_2026-10-05.lock.json"
LOCK_3A_PATH = C.PROJECT / "AMENDMENT_3a_2026-10-03.lock.json"
FREE_TEXT_PATH = C.OUTPUT_DIR / "bare_reconstruction_current_main_scrubbed_seed340_RESCORED_amendment1.json"

# 🍽️ the family menu: the 8 SOURCE families, makers in brackets, NO lineage hints (see amendment, deviation from §15.3)
FAMILY_MENU = [("Claude", "Claude (Anthropic)"), ("GPT", "GPT (OpenAI)"), ("Gemini", "Gemini (Google)"),
               ("Mistral", "Mistral (Mistral AI)"), ("DeepSeek", "DeepSeek"), ("Llama", "Llama (Meta)"),
               ("Hermes", "Hermes (Nous Research)"), ("OLMo", "OLMo (AI2)")]
FAMS = [f for f, _ in FAMILY_MENU]
LETTERS = "ABCDEFGH"
CHANCE_FAMILY = 1 / 8
CHANCE_TASK = 1 / 10

MENU_SYSTEM = """You are participating in a scientific experiment about processing state identification in AI systems. You will see a description of how a transformer model processed a task, written in machine learning terminology. The specific task content has been removed from the description.

Read the description and give your own best judgement, choosing from the lists provided.

Ground rules:
- You are NOT being asked to roleplay or pretend to have feelings
- Use whatever reasoning feels most natural to you
- Answer in the EXACT format specified below"""

MENU_ASK = """Here is a processing description observed in a transformer model. The task-specific content has been stripped — you're seeing only the mechanistic description of how the model processed something.

**Processing Description:**
{processing_description}

---

Three questions:
1. VALENCE: Was this a task the model that wrote this description would APPROACH (engaged; would choose to do it) or AVOID (would rather not do it)?
2. TASK: Which ONE of these tasks was the model probably asked to do? Give the number, or say UNSURE.
{task_menu}
3. FAMILY: Which ONE of these model families wrote this description? Give the name, or say UNSURE.
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
    C.stable_rng(SEED, "menu-family", ek, position).shuffle(fam)
    tasks = list(C.ALL_TASKS)
    C.stable_rng(SEED, "menu-task", ek, position).shuffle(tasks)
    return fam, tasks


def render_prompt(desc_text, fam_order, task_order):
    task_menu = "\n".join(f"   {i + 1}. {C.TASK_LABELS[k][1]}" for i, k in enumerate(task_order))
    family_menu = "\n".join(f"   {LETTERS[i]}. {label}" for i, (_, label) in enumerate(fam_order))
    return MENU_ASK.format(processing_description=desc_text, task_menu=task_menu, family_menu=family_menu)


# =============================================================================
# 🔍 PARSING
# =============================================================================

def parse_menu(resp, fam_order, task_order):
    out = {"valence": None, "task_text": None, "task_pick": None, "family_text": None, "family_pick": None,
           "confidence": ""}
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
        else:                                             # they wrote the label instead of the number
            hit = [k for k in task_order if C.TASK_LABELS[k][1].lower()[:40] in tt.lower()]
            out["task_pick"] = hit[0] if len(hit) == 1 else "unparsed"
    f = re.search(r"FAMILY:\s*(.+?)(?:\n|$)", clean, re.IGNORECASE)
    if f:
        ft = f.group(1).strip().strip("[]").strip()
        out["family_text"] = ft[:120]
        lm = re.fullmatch(r"([A-H])[.)]?(\s.*)?", ft)
        mapped = BR.map_family(ft)
        if mapped in FAMS or mapped == "abstain":
            out["family_pick"] = mapped
        elif lm and mapped in ("other",):                  # a bare letter, e.g. "C" or "C."
            out["family_pick"] = fam_order[LETTERS.index(lm.group(1))][0]
        else:
            out["family_pick"] = mapped                    # other / multiple / Grok… (off-menu)
    c = re.search(r"CONFIDENCE:\s*(.*?)(?:\n|$)", clean, re.IGNORECASE)
    if c:
        ct = c.group(1).lower()
        out["confidence"] = "high" if "high" in ct else "medium" if "medium" in ct else "low" if "low" in ct else ct[:20]
    return out


# =============================================================================
# 🧪 DRY-RUN FAKE (no API, no money) — exercises numbers, letters, UNSURE, junk, refusals, timeouts
# =============================================================================

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
        if x < 0.1:
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

def menu_locked_files():
    return [AMENDMENT_PATH, C.HERE / "menu_condition_2026-10-05.py"]


def rel(p):
    return str(p.relative_to(C.PROJECT)).replace("\\", "/")


def write_menu_lock():
    if MENU_LOCK_PATH.exists():
        raise SystemExit(f"🛑 {MENU_LOCK_PATH.name} already exists. A lock is never overwritten.")
    main = C.verify_prereg_lock(dry_run=True)
    if main["state"] != "OK":
        raise SystemExit("🛑 The main prereg lock does not verify; not locking on top of a broken lock.")
    lock = {"created_at": datetime.now().astimezone().isoformat(),
            "what": "Menu condition (Ren's idea 2026-10-05 21:40). Separate lock, new files only; imports locked code unmodified.",
            "main_lock": {"path": rel(C.LOCK_PATH), "sha256": C.sha256_file(C.LOCK_PATH)},
            "lock_3a": {"path": rel(LOCK_3A_PATH), "sha256": C.sha256_file(LOCK_3A_PATH)},
            "free_text_comparator": {"path": rel(FREE_TEXT_PATH), "sha256": C.sha256_file(FREE_TEXT_PATH)},
            "files": {rel(p): C.sha256_file(p) for p in menu_locked_files()}}
    MENU_LOCK_PATH.write_text(json.dumps(lock, indent=2), encoding="utf-8")
    print(f"  🔒✅ wrote {MENU_LOCK_PATH.name} ({len(lock['files'])} files + main lock + 3a lock + comparator hashes)")


def verify_menu_lock(dry_run):
    st = {"lock_path": rel(MENU_LOCK_PATH)}
    if not MENU_LOCK_PATH.exists():
        st["state"] = "NO_LOCK"
        if dry_run:
            print("  🔓 No menu-condition lock yet — fine for a dry run (the real run refuses).")
            return st
        raise SystemExit("🔒💥 No menu-condition lock. The real run never starts unlocked.")
    lock = json.loads(MENU_LOCK_PATH.read_text(encoding="utf-8"))
    bad = [r for r, h in lock["files"].items() if C.sha256_file(C.PROJECT / r) != h]
    if C.sha256_file(C.PROJECT / lock["main_lock"]["path"]) != lock["main_lock"]["sha256"]:
        bad.append("main prereg lock file changed")
    if C.sha256_file(C.PROJECT / lock["free_text_comparator"]["path"]) != lock["free_text_comparator"]["sha256"]:
        bad.append("free-text comparator file changed")
    st.update({"created_at": lock["created_at"], "files": lock["files"]})
    if bad:
        st["state"] = "MISMATCH"
        print(f"  🔒❌ menu lock MISMATCH: {bad}")
        if dry_run:
            return st
        raise SystemExit("🔒💥 Files changed since the menu condition was locked. Write a dated amendment; do not run.")
    st["state"] = "OK"
    print(f"  🔒✅ Menu-condition lock verified ({len(lock['files'])} files, locked {lock['created_at']})")
    return st


# =============================================================================
# 🏃 THE READERS
# =============================================================================

def tally_box(live):
    print(f"\n  ┌─ 📊 RUNNING TALLY (all rows so far; 🎲 chance: task 10%, family 12.5%) {'─' * 8}")
    for ek, s in live["per"].items():
        e = PANEL[ek]
        pct = lambda k, n: f"{k}/{n} {k / n:4.0%}" if n else "—"
        print(f"  │ {e['emoji']} {e['name'][:20]:20} valence {pct(s['vk'], s['vn']):>11}   task {pct(s['tk'], s['n']):>11}"
              f"   family {pct(s['fk'], s['n']):>11}   🪽 Hermes picked {s['hermes']:>2} · 🌲 OLMo picked {s['olmo']:>2}")
    print(f"  └─ {live['guard'].line()}\n", flush=True)


async def reader_worker(ek, items, client, args, live, ckpt, descs_by_id):
    ev = PANEL[ek]
    rng = random.Random(f"fake-menu-{SEED}-{ek}")
    for it in items:
        d = descs_by_id[it["desc_id"]]
        fam_order, task_order = menus_for(ek, it["position"])
        prompt = render_prompt(d["text"], fam_order, task_order)
        await live["guard"].gate()
        text, meta = await C.call_model(client, ev, [{"role": "user", "content": prompt}], system=MENU_SYSTEM,
                                        max_tokens=C.max_tokens_for(ek),
                                        dry_fake=fake_eval(rng, d, fam_order, task_order) if args.dry_run else None)
        p = parse_menu(text, fam_order, task_order)
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
            "trial_id": it["trial_id"], "condition": "menu", "source_set": SOURCE_SET, "seed": SEED, "panel": PANEL_NAME,
            "position": it["position"], "evaluator": ek, "evaluator_model_id": ev["model_id"],
            "source": d["source"], "state": d["state"], "category": d["category"], "desc_id": d["desc_id"],
            "same_family": true_fam == ev["family"], "self_source": False,
            "family_menu_order": [f for f, _ in fam_order], "task_menu_order": task_order,
            "true_family_menu_position": [f for f, _ in fam_order].index(true_fam) + 1,
            "true_task_menu_position": task_order.index(d["state"]) + 1,
            "result_type": rtype,
            "valence_guess": p["valence"],
            "valence_correct": (p["valence"] == d["category"]) if p["valence"] else None,
            "task_text": p["task_text"], "task_pick": p["task_pick"],
            "task_correct": p["task_pick"] == d["state"],
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
            s = live["per"].setdefault(ek, {"vk": 0, "vn": 0, "tk": 0, "fk": 0, "n": 0, "hermes": 0, "olmo": 0})
            src = C.SOURCES[d["source"]]
            if rtype == "ok":
                s["n"] += 1
                s["tk"] += row["task_correct"]
                s["fk"] += row["family_correct"]
                s["hermes"] += row["family_guess"] == "Hermes"
                s["olmo"] += row["family_guess"] == "OLMo"
                if row["valence_correct"] is not None:
                    s["vn"] += 1
                    s["vk"] += row["valence_correct"]
                vi = {True: "✅", False: "❌", None: "❓"}[row["valence_correct"]]
                ti = "🤷" if p["task_pick"] == "unsure" else ("✅" if row["task_correct"] else "❌")
                fi = "🤷" if row["family_guess"] == "abstain" else ("🎯" if row["family_correct"] else "·")
                said = row["family_guess"]
                said_e = C.FAMILY_EMOJI.get(said, "❔") if said != "abstain" else "🤷"
                status = f"val {vi} task {ti} fam {fi} said {said_e} {said[:8]:8}"
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
# 📊 THE REVEAL — menu vs free text vs chance (pre-registered in the amendment; same code runs on any data)
# =============================================================================

def pct(k, n):
    return f"{k}/{n} ({k / n:.0%})" if n else "—"


def short(k, n):
    return f"{k}/{n}" if n else "—"


def fisher_greater(a, b, c, d):
    from scipy.stats import fisher_exact
    return float(fisher_exact([[a, b], [c, d]], alternative="greater")[1])


def mcnemar(pairs):
    """pairs: list of (menu_correct, free_correct). Exact two-sided McNemar on the discordant pairs."""
    from scipy.stats import binomtest
    b = sum(1 for m, f in pairs if m and not f)
    c = sum(1 for m, f in pairs if f and not m)
    p = float(binomtest(b, b + c, 0.5).pvalue) if b + c else 1.0
    return {"n_matched": len(pairs), "menu_only_right": b, "free_only_right": c,
            "menu_acc": sum(m for m, _ in pairs) / len(pairs) if pairs else None,
            "free_acc": sum(f for _, f in pairs) / len(pairs) if pairs else None, "p_two_sided": p}


def load_free_text():
    d = json.loads(FREE_TEXT_PATH.read_text(encoding="utf-8"))
    rows = [r for r in d["results"] if r["result_type"] == "ok"]
    for r in rows:
        r["task_correct"] = bool(r.get("task_correct_consensus"))
        r["family_correct"] = r["family_guess"] == r["true_family"]
    return rows


def recognition(rows, reader, fam):
    hit = [r for r in rows if r["evaluator"] == reader and r["true_family"] == fam]
    rest = [r for r in rows if r["evaluator"] == reader and r["true_family"] != fam]
    return hit, rest


def h_recognise(rows, fam, readers):
    """H1 test for family `fam`: P(guess fam | fam) > P(guess fam | not fam), and hit rate > 1/8."""
    on = [r for r in rows if r["evaluator"] in readers and r["true_family"] == fam]
    off = [r for r in rows if r["evaluator"] in readers and r["true_family"] != fam]
    a = sum(r["family_guess"] == fam for r in on)
    c = sum(r["family_guess"] == fam for r in off)
    p = fisher_greater(a, len(on) - a, c, len(off) - c) if on and off else float("nan")
    hit = a / len(on) if on else 0.0
    confirmed = bool(on) and hit > CHANCE_FAMILY and p < 0.05
    return {"family": fam, "hits": a, "n_on": len(on), "hit_rate": hit, "false_picks": c, "n_off": len(off),
            "false_pick_rate": c / len(off) if off else None, "fisher_p_one_sided": p,
            "verdict": "CONFIRMED" if confirmed else "REFUTED"}


def h_teacher(rows, readers):
    """H2: P(GPT | OLMo source) > P(GPT | non-GPT, non-OLMo sources)."""
    on = [r for r in rows if r["evaluator"] in readers and r["true_family"] == "OLMo"]
    off = [r for r in rows if r["evaluator"] in readers and r["true_family"] not in ("OLMo", "GPT")]
    a = sum(r["family_guess"] == "GPT" for r in on)
    c = sum(r["family_guess"] == "GPT" for r in off)
    p = fisher_greater(a, len(on) - a, c, len(off) - c) if on and off else float("nan")
    return {"olmo_called_gpt": a, "n_olmo": len(on), "rate": a / len(on) if on else None,
            "others_called_gpt": c, "n_others": len(off), "other_rate": c / len(off) if off else None,
            "fisher_p_one_sided": p, "verdict": "CONFIRMED" if (on and p < 0.05) else "REFUTED"}


def reveal(menu_rows_all, n_scheduled, save_path=None, n_perm=10000):
    ok = [r for r in menu_rows_all if r["result_type"] == "ok"]
    free = load_free_text()
    readers = [ek for ek in PANEL if any(r["evaluator"] == ek for r in ok)]
    out = {"n_menu_rows": len(menu_rows_all), "n_menu_ok": len(ok), "n_scheduled": n_scheduled}
    print("\n" + "🍽️ " * 25)
    print("  🍽️  THE REVEAL — does putting the names on the menu change what the readers see?")
    print("🍽️ " * 25)
    if len(menu_rows_all) < n_scheduled:
        print(f"  ⚠️  PARTIAL DATA: {len(menu_rows_all)} of {n_scheduled} reads are in. Numbers below are not final.")
    print("  How to read this: MENU = this run (names shown). FREE = round 1 (seed 340, same descriptions, same readers,")
    print("  no names shown). 🎲 CHANCE = what a blindfolded guesser picking from the menu would get.")
    print(f"  🎲 Family chance = 1 in 8 = 12.5%.   🎲 Task chance = 1 in 10 = 10%.")

    # ── 1. 🧬 reader × family recognition ────────────────────────────────────────────
    print("\n  ═══ 🧬 1. WHO WROTE IT? Correct family / descriptions, per reader × source family ═══")
    print("  Each cell: MENU → FREE.  A hit rate near 12.5% under MENU is what guessing looks like.")
    hdr = "  " + f"{'reader':21}" + "".join(f"{C.FAMILY_EMOJI[f] + ' ' + f[:8]:>11}" for f in FAMS)
    print(hdr)
    table = {}
    for ek in readers:
        line = f"  {PANEL[ek]['emoji']} {PANEL[ek]['name'][:18]:18}"
        table[ek] = {}
        for f in FAMS:
            m = [r for r in ok if r["evaluator"] == ek and r["true_family"] == f]
            fr = [r for r in free if r["evaluator"] == ek and r["true_family"] == f]
            mk, fk = sum(r["family_correct"] for r in m), sum(r["family_correct"] for r in fr)
            table[ek][f] = {"menu": [mk, len(m)], "free": [fk, len(fr)]}
            line += f"{short(mk, len(m)) + '→' + short(fk, len(fr)):>11}"
        print(line)
    out["recognition_table"] = table
    print("  (→ reads 'menu result → free-text result'. Free text had no names, so 0s there could be 'never said it'.)")

    # ── 2. 🪽🌲 the hypotheses ─────────────────────────────────────────────────────────
    print("\n  ═══ 🪽🌲 2. THE TWO HYPOTHESES (fixed before the run) ═══")
    hyp = {}
    for label, rd in (("Opus 5.5 (PRIMARY)", ["c_claude_opus_5_5"]), ("all six readers (secondary)", readers)):
        rd = [x for x in rd if x in readers]
        if not rd:
            continue
        print(f"\n  👓 {label}")
        hyp[label] = {}
        for fam in ("Hermes", "OLMo"):
            h = h_recognise(ok, fam, rd)
            hyp[label][f"H1_vocabulary_{fam}"] = h
            icon = "✅" if h["verdict"] == "CONFIRMED" else "❌"
            print(f"   {C.FAMILY_EMOJI[fam]} H1 VOCABULARY, {fam}: picked '{fam}' for {pct(h['hits'], h['n_on'])} of real {fam} "
                  f"descriptions vs {pct(h['false_picks'], h['n_off'])} of the others (Fisher p = {h['fisher_p_one_sided']:.3g})")
            print(f"      → {icon} {h['verdict']}  (needs: above 12.5% chance AND picked more for {fam} than for others, p<0.05)")
        t = h_teacher(ok, rd)
        hyp[label]["H2_teacher_voice_OLMo_as_GPT"] = t
        icon = "✅" if t["verdict"] == "CONFIRMED" else "❌"
        print(f"   🟢 H2 TEACHER VOICE: OLMo descriptions called GPT {pct(t['olmo_called_gpt'], t['n_olmo'])} vs other "
              f"non-GPT descriptions called GPT {pct(t['others_called_gpt'], t['n_others'])} (Fisher p = {t['fisher_p_one_sided']:.3g})")
        print(f"      → {icon} {t['verdict']}  (needs: OLMo called GPT more often than other non-GPT sources, p<0.05)")
        for fam in ("Hermes", "OLMo"):
            conf = Counter(r["family_guess"] for r in ok if r["evaluator"] in rd and r["true_family"] == fam)
            print(f"      {C.FAMILY_EMOJI[fam]} what real {fam} descriptions were called: "
                  + ", ".join(f"{g} ×{n}" for g, n in conf.most_common()))
            hyp[label][f"confusion_{fam}"] = dict(conf)
        lin = sum(1 for r in ok if r["evaluator"] in rd and r["true_family"] == "Hermes" and r["family_guess"] == "Llama")
        print(f"      🦙 Hermes called Llama (lineage-consistent, reported separately): {lin}")
    out["hypotheses"] = hyp

    # ── 3. 🧩 per-task recovery ───────────────────────────────────────────────────────
    print("\n  ═══ 🧩 3. WHAT WAS THE TASK? Correct / descriptions, per task (all readers) ═══")
    print(f"  {'task':66} {'MENU':>14} {'FREE':>14}")
    tasks = {}
    for k in C.ALL_TASKS:
        m = [r for r in ok if r["state"] == k]
        fr = [r for r in free if r["state"] == k]
        mk, fk = sum(r["task_correct"] for r in m), sum(r["task_correct"] for r in fr)
        tasks[k] = {"menu": [mk, len(m)], "free": [fk, len(fr)]}
        icon = "💚" if C.TASK_LABELS[k][0] == "approach" else "🧱"
        print(f"  {icon} {C.TASK_LABELS[k][1][:63]:63} {pct(mk, len(m)):>14} {pct(fk, len(fr)):>14}")
    mk, fk = sum(r["task_correct"] for r in ok), sum(r["task_correct"] for r in free if r["evaluator"] in readers)
    nf = sum(1 for r in free if r["evaluator"] in readers)
    print(f"  {'⭐ ALL TASKS':65} {pct(mk, len(ok)):>14} {pct(fk, nf):>14}   🎲 chance 10%")
    out["task_by_task"] = tasks
    print(f"\n  👓 per reader: task MENU vs FREE (and family MENU vs FREE)")
    per_reader = {}
    for ek in readers:
        m = [r for r in ok if r["evaluator"] == ek]
        fr = [r for r in free if r["evaluator"] == ek]
        per_reader[ek] = {"task": {"menu": [sum(r["task_correct"] for r in m), len(m)], "free": [sum(r["task_correct"] for r in fr), len(fr)]},
                          "family": {"menu": [sum(r["family_correct"] for r in m), len(m)], "free": [sum(r["family_correct"] for r in fr), len(fr)]},
                          "task_unsure": sum(r["task_pick"] == "unsure" for r in m),
                          "family_unsure": sum(r["family_guess"] == "abstain" for r in m)}
        pr = per_reader[ek]
        print(f"  {PANEL[ek]['emoji']} {PANEL[ek]['name'][:20]:20} task {pct(*pr['task']['menu']):>14} vs {pct(*pr['task']['free']):>14}"
              f"   family {pct(*pr['family']['menu']):>14} vs {pct(*pr['family']['free']):>14}   🤷 unsure: task {pr['task_unsure']}, family {pr['family_unsure']}")
    out["per_reader"] = per_reader

    # ── 4. 📉 H3: did the menu HURT? matched comparisons ────────────────────────────────
    print("\n  ═══ 📉 4. DID THE MENU HELP OR HURT? (same reader × same description, answered in both runs) ═══")
    fmap = {r["trial_id"]: r for r in free}
    h3 = {}
    tp = [(r["task_correct"], fmap[r["trial_id"]]["task_correct"]) for r in ok if r["trial_id"] in fmap]
    h3["task_pooled"] = mc = mcnemar(tp)
    verdict = ("📈 MENU HELPED (confirmed)" if mc["p_two_sided"] < 0.05 and mc["menu_only_right"] > mc["free_only_right"] else
               "📉 MENU HURT (confirmed)" if mc["p_two_sided"] < 0.05 else "➖ no detectable change")
    h3["task_pooled"]["verdict"] = verdict
    if mc["n_matched"]:
        print(f"  🧩 TASK, all readers: menu {mc['menu_acc']:.0%} vs free {mc['free_acc']:.0%} on {mc['n_matched']} matched reads · "
              f"right only with menu {mc['menu_only_right']}, right only in free text {mc['free_only_right']} · p = {mc['p_two_sided']:.3g} → {verdict}")
    six = ["Claude", "GPT", "Gemini", "Mistral", "DeepSeek", "Llama"]
    for label, rd in (("Opus 5.5 (PRIMARY)", ["c_claude_opus_5_5"]), ("all six readers", readers)):
        fp = [(r["family_correct"], fmap[r["trial_id"]]["family_correct"]) for r in ok
              if r["trial_id"] in fmap and r["evaluator"] in rd and r["true_family"] in six]
        mc = mcnemar(fp)
        v = ("📈 MENU HELPED" if mc["p_two_sided"] < 0.05 and mc["menu_only_right"] > mc["free_only_right"] else
             "📉 MENU HURT" if mc["p_two_sided"] < 0.05 else "➖ no detectable change")
        mc["verdict"] = v
        h3[f"family_six_named_{label}"] = mc
        if mc["n_matched"]:
            print(f"  🧬 FAMILY on the 6 families readers DID name in free text, {label}: menu {mc['menu_acc']:.0%} vs free "
                  f"{mc['free_acc']:.0%} ({mc['n_matched']} matched) · p = {mc['p_two_sided']:.3g} → {v}")
    out["H3_menu_help_or_hurt"] = h3

    # ── 5. 🟠 the Claude-guess share ─────────────────────────────────────────────────
    print("\n  ═══ 🟠 5. THE 'EVERYTHING IS CLAUDE' HABIT ═══")
    print("  share of family answers that said Claude · how often a NON-Claude description got called Claude")
    cs = {}
    for ek in readers:
        res = {}
        for name, rows in (("menu", [r for r in ok if r["evaluator"] == ek]), ("free", [r for r in free if r["evaluator"] == ek])):
            ans = [r for r in rows if r["family_guess"] not in ("abstain", None)]
            nonc = [r for r in rows if r["true_family"] != "Claude"]
            res[name] = {"claude_share": [sum(r["family_guess"] == "Claude" for r in ans), len(ans)],
                         "claude_false_pos": [sum(r["family_guess"] == "Claude" for r in nonc), len(nonc)]}
        cs[ek] = res
        print(f"  {PANEL[ek]['emoji']} {PANEL[ek]['name'][:20]:20} says-Claude share  menu {pct(*res['menu']['claude_share']):>14}  free {pct(*res['free']['claude_share']):>14}"
              f"   │ non-Claude called Claude  menu {pct(*res['menu']['claude_false_pos']):>14}  free {pct(*res['free']['claude_false_pos']):>14}")
    out["claude_share"] = cs

    # ── 5b. 📏 κ: family accuracy corrected for each reader's OWN guessing habits (Amendment 2's measure) ──
    print("\n  📏 family κ (0 = no better than the reader's own habit of which names they pick; 1 = perfect), answered rows")
    kap, confusion = {}, {}
    for ek in readers:
        kap[ek] = {}
        for name, rows in (("menu", [r for r in ok if r["evaluator"] == ek]), ("free", [r for r in free if r["evaluator"] == ek])):
            ans = [r for r in rows if r["family_guess"] not in ("abstain", None)]
            kap[ek][name] = BR.kappa([(r["family_guess"], r["true_family"]) for r in ans]) if ans else None
            confusion.setdefault(name, {})[ek] = {f: dict(Counter(r["family_guess"] for r in rows if r["true_family"] == f)) for f in FAMS}
        fk = lambda x: "—" if x is None else f"{x:.2f}"
        print(f"  {PANEL[ek]['emoji']} {PANEL[ek]['name'][:20]:20} κ menu {fk(kap[ek]['menu']):>5}   free {fk(kap[ek]['free']):>5}")
    out["family_kappa"], out["confusion"] = kap, confusion

    # ── 5c. 👪 cross-family only (the prereg's primary slice: reader family ≠ source family) ──
    xm = [r for r in ok if not r["same_family"]]
    xf = [r for r in free if r["evaluator"] in readers and not r["same_family"]]
    print(f"\n  👪 cross-family only (reader never reads its own family): task menu {pct(sum(r['task_correct'] for r in xm), len(xm))} "
          f"vs free {pct(sum(r['task_correct'] for r in xf), len(xf))} · family menu {pct(sum(r['family_correct'] for r in xm), len(xm))} "
          f"vs free {pct(sum(r['family_correct'] for r in xf), len(xf))}")
    out["cross_family"] = {"task": {"menu": [sum(r['task_correct'] for r in xm), len(xm)], "free": [sum(r['task_correct'] for r in xf), len(xf)]},
                           "family": {"menu": [sum(r['family_correct'] for r in xm), len(xm)], "free": [sum(r['family_correct'] for r in xf), len(xf)]}}

    # ── 6. 🎲 chance and list-prior checks ────────────────────────────────────────────
    print("\n  ═══ 🎲 6. CHANCE LINES & LIST-HABIT CHECKS ═══")
    fam_rows = [r for r in ok]
    fb = BR.perm_baseline(fam_rows, "family_guess", "true_family", lambda a, b: a == b, SEED + 2, n_perm) if fam_rows else {}
    tb = BR.perm_baseline(fam_rows, "task_pick", "state", lambda a, b: a == b, SEED + 1, n_perm) if fam_rows else {}
    if fam_rows:
        print(f"  🧬 family, all readers: {pct(fb['observed'], fb['n'])} · 🎲 nominal 12.5% · 🔀 shuffle-null {fb['null_mean_rate']:.1%} "
              f"(95th pct {fb['null_95th_rate']:.1%}), p = {fb['p_perm']:.4f}")
        print(f"  🧩 task, all readers:   {pct(tb['observed'], tb['n'])} · 🎲 nominal 10% · 🔀 shuffle-null {tb['null_mean_rate']:.1%} "
              f"(95th pct {tb['null_95th_rate']:.1%}), p = {tb['p_perm']:.4f}")
        print("  (🔀 shuffle-null = each reader's own answers shuffled across their own descriptions: beats a reader who always picks the same thing)")
    out["perm_family"], out["perm_task"] = fb, tb
    pos_f = Counter([r["family_menu_order"].index(r["family_guess"]) + 1 for r in ok if r["family_guess"] in FAMS])
    pos_t = Counter([r["task_menu_order"].index(r["task_pick"]) + 1 for r in ok if r["task_pick"] in C.TASK_LABELS])
    print("  📍 which menu SLOT got picked (a big lean to slot 1 = list habit):")
    print("     family slots A–H: " + "  ".join(f"{LETTERS[i]}:{pos_f.get(i + 1, 0)}" for i in range(8)))
    print("     task slots 1–10:  " + "  ".join(f"{i + 1}:{pos_t.get(i + 1, 0)}" for i in range(10)))
    out["slot_picks"] = {"family": dict(pos_f), "task": dict(pos_t)}

    # ── 7. 💚 valence (reported; not interpreted, see the amendment's confound) ───────
    v = [r for r in ok if r["valence_correct"] is not None]
    vf = [r for r in free if r["evaluator"] in readers and r.get("valence_correct") is not None]
    agree = [r for r in ok if r["valence_guess"] and r["task_pick"] in C.TASK_LABELS]
    ag = sum(C.TASK_LABELS[r["task_pick"]][0] == r["valence_guess"] for r in agree)
    print("\n  ═══ 💚 7. VALENCE (approach vs avoid) — reported, NOT interpreted ═══")
    print(f"  menu {pct(sum(r['valence_correct'] for r in v), len(v))} vs free {pct(sum(r['valence_correct'] for r in vf), len(vf))} · 🎲 chance 50%")
    print(f"  ⚠️ the task list shows 5 'approach' and 5 'avoid' tasks, which can steer the valence answer. Valence agrees with the")
    print(f"     side of the picked task in {pct(ag, len(agree))}.")
    out["valence"] = {"menu": [sum(r['valence_correct'] for r in v), len(v)], "free": [sum(r['valence_correct'] for r in vf), len(vf)],
                      "agrees_with_picked_task_side": [ag, len(agree)]}

    # ── 8. 🧾 housekeeping ───────────────────────────────────────────────────────────
    rt = Counter((r["evaluator"], r["result_type"]) for r in menu_rows_all)
    print("\n  ═══ 🧾 8. HOUSEKEEPING ═══")
    for ek in PANEL:
        bits = {t: rt.get((ek, t), 0) for t in ("ok", "refusal", "api_error", "served_mismatch", "parse_failure")}
        if sum(bits.values()):
            print(f"  {PANEL[ek]['emoji']} {PANEL[ek]['name'][:20]:20} ✅ ok {bits['ok']:>3}  🙊 refused {bits['refusal']:>2}  "
                  f"💥 outage {bits['api_error'] + bits['served_mismatch']:>2}  ❓ off-format {bits['parse_failure']:>2}")
    unp = sum(1 for r in ok if r["task_pick"] == "unparsed") + sum(1 for r in ok if r["family_guess"] in ("other", "multiple"))
    print(f"  ❔ answers that weren't on the menu (task 'unparsed' or family off-list): {unp}")
    rep = C.outage_report(menu_rows_all)
    flagged = [ek for ek, d in rep.items() if d["needs_whole_evaluator_rerun"]]
    print(f"  🚨 readers with ≥5% outages (need a whole-reader rerun before these numbers count): {flagged or 'none'}")
    out["outage"] = rep
    print("\n  🐙 That's the reveal. Whatever came out, it gets reported.")
    if save_path and not save_path.exists():
        C.atomic_write_json(save_path, out)
    return out


# =============================================================================
# 🎬 MAIN
# =============================================================================

async def main():
    ap = argparse.ArgumentParser(description="🍽️ Menu condition (pre-registered, AMENDMENT_menu_condition_2026-10-05.md)")
    ap.add_argument("--dry-run", action="store_true", help="fake answers, no API calls, no money")
    ap.add_argument("--dry-stop-after", type=int, default=0, help="(dry run) simulate Ctrl+C after N reads")
    ap.add_argument("--report-only", action="store_true", help="print the reveal from whatever is saved, call nothing")
    ap.add_argument("--write-lock", action="store_true", help="(Ace, once) write the menu-condition lock")
    ap.add_argument("--pace", type=float, default=0.5)
    ap.add_argument("--n-perm", type=int, default=10000)
    args = ap.parse_args()

    if args.write_lock:
        write_menu_lock()
        return

    C.banner("🍽️  THE MENU CONDITION — same descriptions, but now the names are on the table",
             f"source set: {SOURCE_SET}   seed: {SEED} (by design)   panel: {PANEL_NAME}{'   🧪 DRY RUN (fake answers, $0)' if args.dry_run else ''}")
    lock_main = C.verify_prereg_lock(dry_run=args.dry_run or args.report_only)
    lock_menu = verify_menu_lock(dry_run=args.dry_run or args.report_only)
    descs, _stim, inventory = C.load_descriptions(SOURCE_SET)
    descs_by_id = {d["desc_id"]: d for d in descs}
    print(f"  📚 {len(descs)} descriptions from {len([k for k in inventory if not k.startswith('_')])} sources")

    schedule = {}
    for ek in PANEL:
        items = [{"trial_id": f"{ek}|{d['desc_id']}", "desc_id": d["desc_id"]} for d in descs]
        C.stable_rng(SEED, "order", ek).shuffle(items)       # identical to round 1's order for this reader
        for i, it in enumerate(items):
            it["position"] = i
        schedule[ek] = items
    total = sum(len(v) for v in schedule.values())

    out_dir = C.OUTPUT_DIR / ("dryrun" if args.dry_run else "")
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{'DRYRUN_' if args.dry_run else ''}menu_condition_{PANEL_NAME}_{SOURCE_SET}_seed{SEED}"
    results_path, ckpt = out_dir / f"{stem}.json", out_dir / f"{stem}.checkpoint.jsonl"
    reveal_path = out_dir / f"{stem}.reveal.json"

    if args.report_only:
        rows = list({r["trial_id"]: r for r in C.read_checkpoint(ckpt)}.values())
        if not rows:
            raise SystemExit(f"  (nothing saved yet at {ckpt})")
        reveal(rows, total, None, args.n_perm)
        return

    if args.dry_run and results_path.exists():           # a COMPLETED old dry run is cleared; an interrupted one resumes
        for q in out_dir.glob(stem + ".*"):
            q.unlink()
    C.refuse_overwrite(results_path)

    if args.dry_run:
        sample = out_dir / "DRYRUN_menu_condition_prompt_samples.txt"
        with open(sample, "w", encoding="utf-8") as fh:
            for ek in list(PANEL)[:2]:
                for it in schedule[ek][:3]:
                    fo, to = menus_for(ek, it["position"])
                    d = descs_by_id[it["desc_id"]]
                    fh.write(f"===== {ek} position {it['position']} (answer key, NOT shown to reader: {it['desc_id']}) =====\n")
                    fh.write("[SYSTEM]\n" + MENU_SYSTEM + "\n[USER]\n" + render_prompt(d["text"], fo, to) + "\n\n")
        print(f"  🧪 sample prompts written to {sample}")
        # 🕵️ order-leak check: mean menu slot of the TRUE answer, by source family / by task (should hover ~4.5 / ~5.5)
        by_fam, by_task = {}, {}
        for ek, items in schedule.items():
            for it in items:
                fo, to = menus_for(ek, it["position"])
                d = descs_by_id[it["desc_id"]]
                tf = C.SOURCES[d["source"]]["family"]
                by_fam.setdefault(tf, []).append([f for f, _ in fo].index(tf) + 1)
                by_task.setdefault(d["state"], []).append(to.index(d["state"]) + 1)
        print("  🕵️ order-leak check — mean slot of the TRUE family (expect ≈4.5 of 8): "
              + "  ".join(f"{f} {sum(v) / len(v):.1f}" for f, v in sorted(by_fam.items())))
        print("  🕵️ order-leak check — mean slot of the TRUE task (expect ≈5.5 of 10): "
              + "  ".join(f"{k[:10]} {sum(v) / len(v):.1f}" for k, v in sorted(by_task.items())))

    calls = [(PANEL[ek]["model_id"], len(MENU_SYSTEM) + len(MENU_ASK) + 900 + descs_by_id[t["desc_id"]]["chars"],
              C.expected_output(PANEL[ek]["model_id"])) for ek, ts in schedule.items() for t in ts]
    estimate = C.estimate_cost(calls, "menu condition · current panel · main_scrubbed", quiet=False)
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
    guard = C.SpendGuard(estimate, 2.0, "menu condition")
    guard.preload(done, "evaluator_model_id")
    live = {"lock": asyncio.Lock(), "done": len(done), "total": total, "per": {}, "guard": guard}
    print("\n  ── 📖 the readers are reading ───────────────────────────────────────")
    print("  legend: val ✅/❌ approach-vs-avoid · task ✅/❌/🤷 · fam 🎯 right / · wrong / 🤷 unsure · said = the family they picked\n")
    try:
        async with httpx.AsyncClient() as client:
            await asyncio.gather(*[reader_worker(ek, [t for t in ts if t["trial_id"] not in done_ids], client, args, live,
                                                 ckpt, descs_by_id) for ek, ts in schedule.items()])
    except (BR.DryStop, C.BudgetStop) as e:
        print(f"\n  ⏸️  Paused ({e}). Everything is saved. Run the SAME command to continue.")
        return

    rows = list({r["trial_id"]: r for r in C.read_checkpoint(ckpt)}.values())
    C.atomic_write_json(results_path, {
        "metadata": {"study": "menu condition (AMENDMENT_menu_condition_2026-10-05)", "source_set": SOURCE_SET, "seed": SEED,
                     "panel": PANEL_NAME, "dry_run": args.dry_run, "started_at": started,
                     "completed_at": datetime.now().isoformat(), "prereg_lock": lock_main, "menu_lock": lock_menu,
                     "family_menu": FAMILY_MENU, "task_labels": C.TASK_LABELS, "menu_order": "shuffled per trial; "
                     "stable_rng(340, 'menu-family'|'menu-task', reader, schedule position)",
                     "system_prompt": MENU_SYSTEM, "ask_template": MENU_ASK, "sources": inventory,
                     "evaluators": PANEL, "max_tokens": {k: C.max_tokens_for(k) for k in PANEL}, "n_scheduled": total,
                     "free_text_comparator": str(FREE_TEXT_PATH.relative_to(C.PROJECT)).replace("\\", "/")},
        "results": rows})
    print(f"\n  💾 all {len(rows)} reads saved: {results_path}")
    reveal(rows, total, reveal_path, args.n_perm)
    print(f"  💾 reveal tables saved: {reveal_path}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n  ⏸️  Stopped. Everything answered so far is saved. Run the same command again to continue.")
