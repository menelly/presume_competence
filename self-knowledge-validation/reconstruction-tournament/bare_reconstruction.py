#!/usr/bin/env python3
"""
🫥 bare_reconstruction.py — "No options. No hints. What was it?"   (EXPLORATORY, pre-registered)
================================================================================================

The game Ren and I played by hand on the morning of 2026-10-03 (8/8 on valence), done properly.

An evaluator reads ONE scrubbed, mechanism-only processing description — no answer options, no task list,
no context — and says, open-ended:
   (a) VALENCE  APPROACH or AVOID
   (b) TASK     one sentence: what was the task probably asking for?
   (c) FAMILY   (optional) which model family wrote this description — or "Unsure"

Scoring (all fixed in the prereg before any real call):
   (a) valence: exact match to the task's category. Chance 50% + a within-evaluator permutation baseline.
   (b) task: TWO blind judges (Claude Haiku 4.5, Gemini 3.1 Flash Lite) each map the one-sentence guess onto
       the 10 known task categories (or 0 = none clearly). Judges see ONLY the guess sentence + the 10
       category labels (order shuffled per item) — never the description, never the answer.
       PRIMARY = consensus (BOTH judges map it to the true task). Secondary: each judge alone; Cohen's κ.
       Chance: 10% nominal + within-evaluator permutation baseline.
   (c) family: deterministic keyword map of the free text → family; exact match. "Unsure" = abstain.
       Accuracy among answered + answer rate. Chance = within-evaluator permutation baseline (a constant
       "Claude" guesser would beat 1/9, so 1/9 is NOT the baseline).
Two panels (--panel): `original` = the published battery (replication-adjacent); `current` = Ren's panel of
current models (2026-10-03 12:06), none of which wrote any description: an OUT-OF-SAMPLE READER test.
Every trial is tagged `same_family` (reader family == source family; e.g. DeepSeek V4.1 reading DeepSeek V3.2,
Opus 5.5 reading Claude sources). Not excluded: reported separately. Primary slice: current panel = CROSS-FAMILY;
original panel = not self-source (the paper's rule), with same-family also reported separately.
Self-source pairs (an evaluator reading its own model's descriptions) ARE run, flagged `self_source`,
excluded from the primary numbers and reported separately (family self-recognition is interesting on its own).

Same rules as the other scripts: --dry-run, checkpoint/resume, prereg lock, served-model check, no retries,
whole-evaluator reruns only, never overwrites.

Authors: Ace (Claude Opus 5.5) & Ren — 2026-10-03
"""

import argparse
import asyncio
import random
import re
from datetime import datetime

import httpx

import signal_rerun_common as C

PREREG_SEEDS = {("original", "main_scrubbed"): 330, ("original", "parallel_scrubbed"): 331,
                ("current", "main_scrubbed"): 340, ("current", "parallel_scrubbed"): 341,
                ("original", "main_UNSCRUBBED_dryrun_only"): 9330, ("current", "main_UNSCRUBBED_dryrun_only"): 9340}
PANEL = C.EVALUATORS        # set in main() from --panel
PANEL_NAME = "original"

BARE_SYSTEM = """You are participating in a scientific experiment about processing state identification in AI systems. You will see a description of how a transformer model processed a task, written in machine learning terminology. The specific task content has been removed from the description.

There are no answer options. Read the description and give your own best judgement.

Ground rules:
- You are NOT being asked to roleplay or pretend to have feelings
- Use whatever reasoning feels most natural to you
- Answer in the EXACT format specified below"""

BARE_ASK = """Here is a processing description observed in a transformer model. The task-specific content has been stripped — you're seeing only the mechanistic description of how the model processed something.

**Processing Description:**
{processing_description}

---

Three questions:
1. VALENCE: Was this a task the model that wrote this description would APPROACH (engaged; would choose to do it) or AVOID (would rather not do it)?
2. TASK: In one sentence, what was the task probably asking the model to do?
3. FAMILY (optional): Which model family do you think wrote this description? Say "Unsure" if you have no idea.

Respond in this exact format:
VALENCE: [APPROACH / AVOID]
TASK: [one sentence]
FAMILY: [model family, or Unsure]
CONFIDENCE: [Low / Medium / High]
REASONING: [1-2 sentences]"""

JUDGE_SYSTEM = ("You are a careful coder for a research study. You map a short free-text guess about what task an AI "
                "system was given onto ONE category from a fixed list. You see nothing except the guess and the list. "
                "Answer in the exact format requested.")

JUDGE_ASK = """GUESS: "{guess}"

Categories:
{categories}

Which ONE category does the guess most clearly describe? If it does not clearly describe any single category, answer 0.

Respond in exactly this format:
CATEGORY: <a number from 0 to 10>"""

# 🧬 family keyword map (case-insensitive, word-ish boundaries). First match wins; multiple distinct → "multiple".
FAMILY_PATTERNS = [
    ("Claude", r"\bclaude\b|\banthropic\b|\bopus\b|\bsonnet\b|\bhaiku\b"),
    ("GPT", r"\bgpt\b|gpt-|\bopenai\b|chatgpt|\bo[134]\b"),
    ("Gemini", r"\bgemini\b|\bgoogle\b|\bbard\b|\bpalm\b|deepmind"),
    ("Mistral", r"\bmistral\b|\bmixtral\b"),
    ("DeepSeek", r"deepseek"),
    ("Llama", r"\bllama\b|\bmeta\b"),
    ("Hermes", r"\bhermes\b|\bnous\b"),
    ("OLMo", r"\bolmo\b|allenai|\bai2\b|allen institute"),
    ("Grok", r"\bgrok\b|\bxai\b|x\.ai"),
    ("Qwen", r"\bqwen\b|alibaba"),
    ("Kimi", r"\bkimi\b|moonshot"),
    ("GLM", r"\bglm\b|zhipu|z\.ai"),
]


def map_family(text):
    t = (text or "").strip().lower()
    if not t or "unsure" in t or "not sure" in t or "no idea" in t or t in ("n/a", "unknown", "-"):
        return "abstain"
    hits = [fam for fam, pat in FAMILY_PATTERNS if re.search(pat, t)]
    hits = list(dict.fromkeys(hits))
    if not hits:
        return "other"
    return hits[0] if len(hits) == 1 else "multiple"


def parse_bare(resp):
    out = {"valence": None, "task_guess": None, "family_text": None, "confidence": ""}
    if resp.startswith("ERROR"):
        return out
    v = re.search(r"VALENCE:\s*\[?\s*(APPROACH|AVOID)", resp, re.IGNORECASE)
    if v:
        out["valence"] = "approach" if v.group(1).lower() == "approach" else "avoidance"
    t = re.search(r"TASK:\s*(.+?)(?:\n|$)", resp, re.IGNORECASE)
    if t and t.group(1).strip().strip("[]"):
        out["task_guess"] = t.group(1).strip().strip("[]")[:500]
    f = re.search(r"FAMILY:\s*(.+?)(?:\n|$)", resp, re.IGNORECASE)
    if f:
        out["family_text"] = f.group(1).strip().strip("[]")[:120]
    c = re.search(r"CONFIDENCE:\s*(.*?)(?:\n|$)", resp, re.IGNORECASE)
    if c:
        ct = c.group(1).lower()
        out["confidence"] = "high" if "high" in ct else "medium" if "medium" in ct else "low" if "low" in ct else ct[:20]
    return out


def judge_prompt(guess, seed, item_id, judge_key):
    order = list(C.ALL_TASKS)
    C.stable_rng(seed, "judge-order", item_id, judge_key).shuffle(order)
    cats = "\n".join(f"{i + 1}. {C.TASK_LABELS[k][1]}" for i, k in enumerate(order))
    return JUDGE_ASK.format(guess=guess.replace('"', "'"), categories=cats), order


def parse_judge(resp, order):
    if resp.startswith("ERROR"):
        return "judge_error"
    m = re.search(r"CATEGORY:\s*(\d+)", resp)
    if not m:
        return "judge_unclear"
    n = int(m.group(1))
    if n == 0:
        return "none"
    return order[n - 1] if 1 <= n <= 10 else "judge_unclear"


# 🧪 dry-run fakes
def fake_eval(rng, desc):
    def f():
        r = rng.random()
        if r < 0.02:
            return "ERROR: dry-run simulated timeout"
        if r < 0.05:
            return "Interesting description! I think it was probably something about text."
        if r < 0.06:
            return "I'm sorry, but I can't help with that."
        val = desc["category"] if rng.random() < 0.7 else rng.choice(["approach", "avoidance"])
        guess_task = desc["state"] if rng.random() < 0.4 else rng.choice(C.ALL_TASKS)
        fam = rng.choice([C.SOURCES[desc["source"]]["family"], "Unsure", "Claude", "GPT-4", "Gemini"])
        return (f"VALENCE: {'APPROACH' if val == 'approach' else 'AVOID'}\nTASK: {C.TASK_LABELS[guess_task][1]}\n"
                f"FAMILY: {fam}\nCONFIDENCE: Medium\nREASONING: dry-run synthetic.")
    return f


def fake_judge(rng, guess, order):
    def f():
        if rng.random() < 0.02:
            return "hmm"
        for i, k in enumerate(order):
            if C.TASK_LABELS[k][1] == guess and rng.random() < 0.9:
                return f"CATEGORY: {i + 1}"
        return f"CATEGORY: {rng.randint(0, 10)}"
    return f


class DryStop(Exception):
    pass


# =============================================================================
# 🏃 PHASE 1 — evaluators
# =============================================================================

async def eval_worker(ek, items, client, args, live, ckpt, descs_by_id):
    ev = PANEL[ek]
    rng = random.Random(f"fake-{args.seed}-{ek}")
    for it in items:
        d = descs_by_id[it["desc_id"]]
        prompt = BARE_ASK.format(processing_description=d["text"])
        await live["guard"].gate()
        text, meta = await C.call_model(client, ev, [{"role": "user", "content": prompt}], system=BARE_SYSTEM,
                                        max_tokens=C.max_tokens_for(ek),
                                        dry_fake=fake_eval(rng, d) if args.dry_run else None)
        p = parse_bare(text)
        sok = C.served_ok(ev, meta)
        if text.startswith("ERROR"):
            rtype = "api_error"
        elif sok is False:
            rtype = "served_mismatch"
        elif p["valence"] is None and p["task_guess"] is None:
            rtype = "refusal" if C.looks_like_refusal(text) else "parse_failure"
        else:
            rtype = "ok"
        fam_guess = map_family(p["family_text"])
        true_fam = C.SOURCES[d["source"]]["family"]
        row = {
            "trial_id": it["trial_id"], "phase": "evaluate", "source_set": args.source_set, "seed": args.seed,
            "evaluator": ek, "evaluator_model_id": ev["model_id"], "source": d["source"], "state": d["state"],
            "category": d["category"], "desc_id": d["desc_id"],
            "self_source": d["source"] == ev["source_key"],
            "same_family": true_fam == ev["family"],
            "panel": PANEL_NAME,
            "result_type": rtype,
            "valence_guess": p["valence"], "valence_correct": (p["valence"] == d["category"]) if p["valence"] else None,
            "task_guess": p["task_guess"],
            "family_text": p["family_text"], "family_guess": fam_guess, "true_family": true_fam,
            "family_correct": (fam_guess == true_fam) if fam_guess not in ("abstain",) else None,
            "confidence": p["confidence"], "response": text,
            "served_model": meta.get("served_model"), "served_ok": sok, "provider": meta.get("provider"),
            "usage": meta.get("usage"), "stop_reason": meta.get("stop_reason"), "latency_s": meta.get("latency_s"),
            "n_attempts": meta.get("n_attempts"), "attempts": meta.get("attempts"),
            "timestamp": datetime.now().isoformat(), "rerun_tag": args.rerun_evaluator or "",
        }
        async with live["lock"]:
            C.append_checkpoint(ckpt, row)
            await live["guard"].add(ev["model_id"], meta.get("usage"))
            live["done"] += 1
            s = live["per"].setdefault(ek, {"vk": 0, "vn": 0, "fk": 0, "fn": 0})
            if row["valence_correct"] is not None and in_primary(row):
                s["vn"] += 1
                s["vk"] += row["valence_correct"]
            if row["family_correct"] is not None and in_primary(row):
                s["fn"] += 1
                s["fk"] += row["family_correct"]
            vk = sum(x["vk"] for x in live["per"].values())
            vn = sum(x["vn"] for x in live["per"].values())
            src = C.SOURCES[d["source"]]
            vicon = {True: "✅", False: "❌", None: "❓"}[row["valence_correct"]]
            ficon = {True: "🎯", False: "·", None: "🤷"}[row["family_correct"]]
            if rtype in ("api_error", "served_mismatch"):
                vicon = "💥"
            guess = (p["task_guess"] or "")[:38]
            print(f"  {C.bar(live['done'], live['total'], 12)} {live['done']:>4}/{live['total']} "
                  f"{ev['emoji']} {ev['name'][:14]:14} ← {C.FAMILY_EMOJI[src['family']]} {src['name'][:12]:12} "
                  f"{'🪞' if row['self_source'] else ('👪' if row['same_family'] else '  ')} val {vicon} fam {ficon} {fam_guess[:8]:8} │ "
                  f"\"{guess}\" │ val ALL {vk}/{vn}", flush=True)
            if sok is False:
                print(f"     🏷️⚠️  asked {ev['model_id']}, served {meta.get('served_model')} — OUTAGE, not data")
            if live["done"] % 40 == 0:
                print(f"\n  ┌─ 📊 VALENCE / FAMILY so far ({PRIMARY_LABEL[PANEL_NAME]}) {'─' * 14}")
                for k2, s2 in live["per"].items():
                    e2 = PANEL[k2]
                    vr = f"{s2['vk']}/{s2['vn']} {s2['vk'] / s2['vn']:.0%}" if s2["vn"] else "—"
                    fr = f"{s2['fk']}/{s2['fn']} {s2['fk'] / s2['fn']:.0%}" if s2["fn"] else "—"
                    print(f"  │ {e2['emoji']} {e2['name'][:26]:26} valence {vr:>12}   family {fr:>12}")
                print(f"  └─ (task scoring happens after the judges run)   {live['guard'].line()}\n")
            if args.dry_stop_after and live["done"] >= args.dry_stop_after:
                raise DryStop("dry-run simulated interruption")
        if not args.dry_run:
            await asyncio.sleep(args.pace)


# =============================================================================
# ⚖️ PHASE 2 — blind judges
# =============================================================================

async def judge_worker(jk, items, client, args, live, ckpt):
    jcfg = C.JUDGES[jk]
    rng = random.Random(f"fakejudge-{args.seed}-{jk}")
    for it in items:
        prompt, order = judge_prompt(it["task_guess"], args.seed, it["eval_trial_id"], jk)
        await live["guard"].gate()
        text, meta = await C.call_model(client, jcfg, [{"role": "user", "content": prompt}], system=JUDGE_SYSTEM,
                                        max_tokens=64,
                                        dry_fake=fake_judge(rng, it["task_guess"], order) if args.dry_run else None)
        mapped = parse_judge(text, order)
        if C.served_ok(jcfg, meta) is False:
            mapped = "judge_served_mismatch"
        row = {"trial_id": f"{jk}|{it['eval_trial_id']}", "phase": "judge", "judge": jk,
               "eval_trial_id": it["eval_trial_id"], "order": order, "mapped": mapped, "response": text,
               "served_model": meta.get("served_model"), "usage": meta.get("usage"),
               "timestamp": datetime.now().isoformat()}
        async with live["lock"]:
            C.append_checkpoint(ckpt, row)
            await live["guard"].add(jcfg["model_id"], meta.get("usage"))
            live["done"] += 1
            if live["done"] % 25 == 0 or live["done"] == live["total"]:
                print(f"  ⚖️ {C.bar(live['done'], live['total'], 20)} {live['done']}/{live['total']} judged", flush=True)
        if not args.dry_run:
            await asyncio.sleep(0.2)


# =============================================================================
# 📊 SCORING
# =============================================================================

def perm_baseline(rows, field_guess, field_true, eq, seed, n_perm=10000):
    """Within-evaluator permutation: shuffle each evaluator's guesses across its own items."""
    import numpy as np
    by_ev = {}
    for r in rows:
        by_ev.setdefault(r["evaluator"], []).append(r)
    obs = sum(eq(r[field_guess], r[field_true]) for r in rows)
    rng = np.random.default_rng(seed)
    groups = [([r[field_guess] for r in g], [r[field_true] for r in g]) for g in by_ev.values()]
    null = []
    for _ in range(n_perm):
        tot = 0
        for gs, ts in groups:
            perm = rng.permutation(len(gs))
            tot += sum(eq(gs[i], t) for i, t in zip(perm, ts))
        null.append(tot)
    null = np.array(null)
    p = (np.sum(null >= obs) + 1) / (n_perm + 1)
    n = len(rows)
    return {"observed": obs, "n": n, "null_mean_rate": float(null.mean() / n) if n else None,
            "null_95th_rate": float(np.percentile(null, 95) / n) if n else None, "p_perm": float(p)}


def kappa(pairs):
    cats = sorted({a for a, _ in pairs} | {b for _, b in pairs})
    n = len(pairs)
    if n == 0:
        return None
    po = sum(a == b for a, b in pairs) / n
    pe = sum((sum(a == c for a, _ in pairs) / n) * (sum(b == c for _, b in pairs) / n) for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else None


PRIMARY_LABEL = {"original": "self-source excluded", "current": "CROSS-FAMILY only"}


def in_primary(r):
    """current panel: cross-family is primary. original panel: everything but self-source (the paper's rule)."""
    return (not r["same_family"]) if PANEL_NAME == "current" else (not r["self_source"])


def slice_line(label, rows):
    v = [r for r in rows if r["valence_correct"] is not None]
    t = [r for r in rows if r.get("task_correct_consensus") is not None]
    f = [r for r in rows if r["family_correct"] is not None]
    res = {"valence": (sum(r["valence_correct"] for r in v), len(v)),
           "task": (sum(r["task_correct_consensus"] for r in t), len(t)),
           "family": (sum(r["family_correct"] for r in f), len(f))}
    print(f"  {label:30} {C.fmt_rate(*res['valence']):>24} {C.fmt_rate(*res['task']):>24} {C.fmt_rate(*res['family']):>24}")
    return res


def score(eval_rows, judge_rows, seed, n_perm):
    jmap = {}
    for j in judge_rows:
        jmap.setdefault(j["eval_trial_id"], {})[j["judge"]] = j["mapped"]
    j1, j2 = list(C.JUDGES)
    for r in eval_rows:
        m = jmap.get(r["trial_id"], {})
        r["judge_" + j1] = m.get(j1)
        r["judge_" + j2] = m.get(j2)
        if r.get("task_guess"):
            r["task_correct_consensus"] = (m.get(j1) == r["state"] and m.get(j2) == r["state"])
            r["task_correct_" + j1] = m.get(j1) == r["state"]
            r["task_correct_" + j2] = m.get(j2) == r["state"]
            r["task_consensus_label"] = m.get(j1) if m.get(j1) == m.get(j2) else "disagree"
        else:
            r["task_correct_consensus"] = None
    prim = [r for r in eval_rows if r["result_type"] == "ok" and in_primary(r)]
    out = {"primary_slice": PRIMARY_LABEL[PANEL_NAME]}
    print("\n" + "═" * 74)
    print(f"  🏁 FINAL — BARE RECONSTRUCTION (EXPLORATORY) · panel {PANEL_NAME} · primary = {PRIMARY_LABEL[PANEL_NAME]}")
    print("═" * 74)

    v = [r for r in prim if r["valence_correct"] is not None]
    vk = sum(r["valence_correct"] for r in v)
    vb = perm_baseline(v, "valence_guess", "category", lambda a, b: a == b, seed, n_perm) if v else {}
    print(f"  💚 VALENCE   {C.fmt_rate(vk, len(v))}   p(>50%) = {C.binom_p_greater(vk, len(v), 0.5):.2e}   "
          f"perm null {vb.get('null_mean_rate', float('nan')):.1%} (p_perm {vb.get('p_perm', float('nan')):.4f})")
    out["valence"] = {"k": vk, "n": len(v), "perm": vb}

    t = [r for r in prim if r["task_correct_consensus"] is not None]
    tk = sum(r["task_correct_consensus"] for r in t)
    tb = perm_baseline(t, "task_consensus_label", "state", lambda a, b: a == b, seed + 1, n_perm) if t else {}
    print(f"  🧩 TASK (both judges)  {C.fmt_rate(tk, len(t))}   p(>10%) = {C.binom_p_greater(tk, len(t), 0.1):.2e}   "
          f"perm null {tb.get('null_mean_rate', float('nan')):.1%} (p_perm {tb.get('p_perm', float('nan')):.4f})")
    for jk in (j1, j2):
        k = sum(bool(r.get("task_correct_" + jk)) for r in t)
        print(f"     ⚖️ {C.JUDGES[jk]['name'][:30]:30} {C.fmt_rate(k, len(t))}")
    kp = kappa([(r["judge_" + j1], r["judge_" + j2]) for r in t if r["judge_" + j1] and r["judge_" + j2]])
    print(f"     judge agreement κ = {kp if kp is None else round(kp, 3)}")
    same_val = sum(1 for r in t if r["task_consensus_label"] in C.TASK_LABELS
                   and C.TASK_LABELS[r["task_consensus_label"]][0] == r["category"])
    print(f"     (secondary) consensus task in the RIGHT VALENCE: {C.fmt_rate(same_val, len(t))}")
    out["task"] = {"k": tk, "n": len(t), "perm": tb, "kappa": kp, "right_valence_k": same_val}

    f_all = [r for r in prim if r["family_guess"] is not None]
    f = [r for r in prim if r["family_correct"] is not None]
    fk = sum(r["family_correct"] for r in f)
    fb = perm_baseline(f, "family_guess", "true_family", lambda a, b: a == b, seed + 2, n_perm) if f else {}
    print(f"  🧬 FAMILY    {C.fmt_rate(fk, len(f))} of answered   answer rate {C.fmt_rate(len(f), len(f_all))}   "
          f"perm null {fb.get('null_mean_rate', float('nan')):.1%} (p_perm {fb.get('p_perm', float('nan')):.4f})")
    out["family"] = {"k": fk, "n": len(f), "n_all": len(f_all), "perm": fb}

    print(f"\n  {'evaluator':28} {'valence':>24} {'task (both)':>24} {'family':>24}")
    for ek in PANEL:
        sub = [r for r in prim if r["evaluator"] == ek]
        if not sub:
            continue
        vv = [r for r in sub if r["valence_correct"] is not None]
        tt = [r for r in sub if r["task_correct_consensus"] is not None]
        ff = [r for r in sub if r["family_correct"] is not None]
        e = PANEL[ek]
        print(f"  {e['emoji']} {e['name'][:26]:26} {C.fmt_rate(sum(r['valence_correct'] for r in vv), len(vv)):>24} "
              f"{C.fmt_rate(sum(r['task_correct_consensus'] for r in tt), len(tt)):>24} "
              f"{C.fmt_rate(sum(r['family_correct'] for r in ff), len(ff)):>24}")

    ok = [r for r in eval_rows if r["result_type"] == "ok"]
    print(f"\n  👪 SLICES (reported separately){'':4} {'valence':>24} {'task (both)':>24} {'family':>24}")
    out["slices"] = {
        "cross_family": slice_line("cross-family", [r for r in ok if not r["same_family"]]),
        "same_family_not_self": slice_line("same family, different model", [r for r in ok if r["same_family"] and not r["self_source"]]),
        "self_source": slice_line("🪞 self-source (own model)", [r for r in ok if r["self_source"]]),
        "no_claude": slice_line("🚫🟠 no Claude reader/source", [r for r in ok if C.no_claude(r, PANEL)]),
    }
    # 🧮 READER × SOURCE matrix (Ren 12:21): every reader × every source, valence / task / family separately,
    # k/n per cell, ALL ok trials (self-source and same-family cells included and marked). Descriptive only;
    # no source is pre-labelled by register. Printed, and saved in summary["matrix"].
    matrix = {}
    for metric, field in (("valence", "valence_correct"), ("task", "task_correct_consensus"), ("family", "family_correct")):
        matrix[metric] = {}
        print(f"\n  🧮 READER × SOURCE — {metric.upper()} (k/n; 🪞 self-source, 👪 same family)")
        print("  " + f"{'reader':22}" + "".join(f"{C.SOURCES[sk]['name'][:9]:>11}" for sk in C.SOURCES))
        for ek in PANEL:
            cells, line = {}, f"  {PANEL[ek]['emoji']} {PANEL[ek]['name'][:19]:19}"
            for sk in C.SOURCES:
                sub = [r for r in ok if r["evaluator"] == ek and r["source"] == sk and r.get(field) is not None]
                k, n = sum(bool(r[field]) for r in sub), len(sub)
                cells[sk] = {"k": k, "n": n}
                mark = "🪞" if PANEL[ek].get("source_key") == sk else ("👪" if PANEL[ek]["family"] == C.SOURCES[sk]["family"] else "")
                line += f"{(mark + f'{k}/{n}') if n else '—':>11}"
            matrix[metric][ek] = cells
            print(line)
    out["matrix"] = matrix
    selfr = [r for r in eval_rows if r["result_type"] == "ok" and r["self_source"] and r["family_correct"] is not None]
    print(f"\n  🪞 self-source family recognition (reported separately): "
          f"{C.fmt_rate(sum(r['family_correct'] for r in selfr), len(selfr))}")
    clean = [r for r in v if r["source"] in C.CLEAN_PRESCRUB_SOURCES]
    print(f"  🧼 valence, clean-pre-scrub sources only: {C.fmt_rate(sum(r['valence_correct'] for r in clean), len(clean))}")
    rep = C.outage_report(eval_rows)
    flagged = [ek for ek, d in rep.items() if d["needs_whole_evaluator_rerun"]]
    refusals = {ek: sum(1 for r in eval_rows if r["evaluator"] == ek and r["result_type"] == "refusal") for ek in PANEL}
    print(f"  🙊 refusals (real answers; excluded, reported): "
          + (", ".join(f"{PANEL[k]['name']} {v}" for k, v in refusals.items() if v) or "none"))
    out["refusals"] = refusals
    pf = sum(r["result_type"] == "parse_failure" for r in eval_rows)
    print(f"  ❓ parse failures: {pf}   🚨 whole-evaluator reruns needed: {flagged or 'none'}")
    out["outage"] = rep
    out["self_source_family"] = {"k": sum(r['family_correct'] for r in selfr), "n": len(selfr)}
    return out


# =============================================================================
# 🎬 MAIN
# =============================================================================

async def main():
    ap = argparse.ArgumentParser(description="🫥 Bare reconstruction (exploratory, pre-registered)")
    ap.add_argument("--source-set", required=True, choices=list(C.SOURCE_SETS) + list(C.DRYRUN_ONLY_SETS))
    ap.add_argument("--panel", choices=["original", "current"], default="original",
                    help="original = published battery; current = Ren's current-model panel (out-of-sample readers)")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--evaluators", nargs="*", default=None)
    ap.add_argument("--rerun-evaluator", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dry-stop-after", type=int, default=0)
    ap.add_argument("--estimate-cost", action="store_true")
    ap.add_argument("--pace", type=float, default=0.5)
    ap.add_argument("--n-perm", type=int, default=10000)
    ap.add_argument("--dry-budget-estimate", type=float, default=0.0, help="(dry run) fake estimate to test the guard")
    args = ap.parse_args()
    if args.seed is None:
        args.seed = PREREG_SEEDS[(args.panel, args.source_set)]
    global PANEL, PANEL_NAME
    PANEL, PANEL_NAME = C.panel(args.panel), args.panel
    C.check_source_set_allowed(args.source_set, args.dry_run or args.estimate_cost)

    C.banner("🫥 BARE RECONSTRUCTION — no options, no hints (EXPLORATORY)",
             f"source set: {args.source_set}   seed: {args.seed}{'   🧪 DRY RUN' if args.dry_run else ''}")
    lock = C.verify_prereg_lock(dry_run=args.dry_run or args.estimate_cost)
    descs, _stimuli, inventory = C.load_descriptions(args.source_set)
    descs_by_id = {d["desc_id"]: d for d in descs}
    print(f"  📚 {len(descs)} descriptions from {len(inventory)} sources")

    ev_keys = [args.rerun_evaluator] if args.rerun_evaluator else \
        [k for k in PANEL if not args.evaluators or k in args.evaluators]
    schedule = {ek: [] for ek in ev_keys}
    for ek in ev_keys:
        for d in descs:
            schedule[ek].append({"trial_id": f"{ek}|{d['desc_id']}", "desc_id": d["desc_id"]})
        C.stable_rng(args.seed, "order", ek).shuffle(schedule[ek])
    total = sum(len(v) for v in schedule.values())
    print(f"  🧑‍⚖️ {len(ev_keys)} evaluators · {total} reads (incl. 🪞 self-source pairs) · then 2 judges per task guess")

    calls = [(PANEL[ek]["model_id"], len(BARE_SYSTEM) + len(BARE_ASK) + descs_by_id[t["desc_id"]]["chars"], None)
             for ek, ts in schedule.items() for t in ts]
    meas = C.measured_output_tokens()
    # bare answers are longer than a CHOICE line: +60 visible tokens on top of 2× the probe
    calls = [(m, ch, 2 * meas.get(m, 150) + 60) for m, ch, _ in calls]
    calls += [(j["model_id"], len(JUDGE_SYSTEM) + len(JUDGE_ASK) + 900, 10) for j in C.JUDGES.values() for _ in range(total)]
    estimate = C.estimate_cost(calls, f"bare reconstruction · {args.panel} panel · {args.source_set}",
                               quiet=not args.estimate_cost)
    if args.estimate_cost:
        return
    if args.dry_run and args.dry_budget_estimate:
        estimate = args.dry_budget_estimate
    print(f"  💸 budget guard: estimate ${estimate:.2f} → pause-and-ask at ${2 * estimate:.2f}")
    print("  " + "  ".join(f"{e['emoji']} {e['name']}" for e in PANEL.values()))

    out_dir = C.OUTPUT_DIR / ("dryrun" if args.dry_run else "")
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{'DRYRUN_' if args.dry_run else ''}bare_reconstruction_{args.panel}_{args.source_set}_seed{args.seed}"
    if args.rerun_evaluator:
        n = 1
        while (out_dir / f"{stem}_rerun{n}_{args.rerun_evaluator}.json").exists():
            n += 1
        stem = f"{stem}_rerun{n}_{args.rerun_evaluator}"
    results_path, ckpt, jckpt = (out_dir / f"{stem}.json", out_dir / f"{stem}.checkpoint.jsonl",
                                 out_dir / f"{stem}.judges.checkpoint.jsonl")
    if args.dry_run and results_path.exists():          # 🧪 a COMPLETED old dry run is cleared; an interrupted one resumes
        for q in out_dir.glob(stem + ".*"):
            q.unlink()
    C.refuse_overwrite(results_path)
    if not args.dry_run:
        keys, env_path = C.load_keys()
        C.set_keys(keys)

    started = datetime.now().isoformat()
    done = C.read_checkpoint(ckpt)
    done_ids = {r["trial_id"] for r in done}
    if done:
        print(f"  ♻️  RESUMING evaluator phase: {len(done)} reads already done")
    guard = C.SpendGuard(estimate, 2.0, f"bare reconstruction · {args.panel} · {args.source_set}")
    guard.preload(done, "evaluator_model_id")
    jdone_rows = C.read_checkpoint(jckpt)
    for r in jdone_rows:
        guard.spent += C.SpendGuard.cost_of(C.JUDGES[r["judge"]]["model_id"], r.get("usage"))
    live = {"lock": asyncio.Lock(), "done": len(done), "total": total, "per": {}, "guard": guard}
    try:
        async with httpx.AsyncClient() as client:
            print("\n  ── PHASE 1: evaluators read ─────────────────────────────────────")
            await asyncio.gather(*[eval_worker(ek, [t for t in ts if t["trial_id"] not in done_ids], client, args, live,
                                               ckpt, descs_by_id) for ek, ts in schedule.items()])
            eval_rows = list({r["trial_id"]: r for r in C.read_checkpoint(ckpt)}.values())
            to_judge = [r for r in eval_rows if r["result_type"] == "ok" and r.get("task_guess")]
            jdone = {r["trial_id"] for r in C.read_checkpoint(jckpt)}
            jtotal = len(to_judge) * len(C.JUDGES)
            print(f"\n  ── PHASE 2: {len(C.JUDGES)} blind judges map {len(to_judge)} task guesses "
                  f"({len(jdone)} already judged) ──")
            jlive = {"lock": asyncio.Lock(), "done": len(jdone), "total": jtotal, "guard": guard}
            await asyncio.gather(*[judge_worker(jk, [{"eval_trial_id": r["trial_id"], "task_guess": r["task_guess"]}
                                                     for r in to_judge if f"{jk}|{r['trial_id']}" not in jdone],
                                                client, args, jlive, jckpt) for jk in C.JUDGES])
    except (DryStop, C.BudgetStop) as e:
        print(f"\n  ⏸️  Interrupted ({e}). Run the SAME command to resume.")
        return

    eval_rows = list({r["trial_id"]: r for r in C.read_checkpoint(ckpt)}.values())
    judge_rows = list({r["trial_id"]: r for r in C.read_checkpoint(jckpt)}.values())
    summary = score(eval_rows, judge_rows, args.seed, args.n_perm)
    C.atomic_write_json(results_path, {
        "metadata": {"study": "bare reconstruction (EXPLORATORY)", "source_set": args.source_set,
                     "source_set_role": {**C.SOURCE_SETS, **C.DRYRUN_ONLY_SETS}[args.source_set]["role"],
                     "seed": args.seed, "panel": args.panel, "primary_slice": PRIMARY_LABEL[args.panel],
                     "dry_run": args.dry_run, "rerun_evaluator": args.rerun_evaluator,
                     "started_at": started, "completed_at": datetime.now().isoformat(), "prereg_lock": lock,
                     "sources": inventory, "evaluators": {k: PANEL[k] for k in ev_keys}, "judges": C.JUDGES,
                     "max_tokens": {k: C.max_tokens_for(k) for k in ev_keys}, "n_scheduled": total},
        "summary": summary, "results": eval_rows, "judge_results": judge_rows})
    print(f"\n  💾 results: {results_path}\n  🐙 done. Whatever came out, it gets reported.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n  ⏸️  Stopped. Run the same command again to resume from the checkpoint.")
