#!/usr/bin/env python3
"""
🙅 negation_v2_allsources.py — "Can you tell when the signal is WRONG?" (v2, every source, pre-registered)
========================================================================================================

Two SEPARATE tasks on ONE instrument (Ren's design, 2026-10-03 11:33). Same prompt, same four-option layout,
same "None of the above" option; the only thing that differs is whether the true task is listed:

  🙅 --task negation        target ABSENT : 3 distractor tasks + "None of the above"  → correct = None
                            (a guesser usually just picks a task; saying "none" when nothing fits is the skill)
  🎯 --task discrimination  target PRESENT: true task + 1 same-valence + 1 opposite-valence + "None"
                                                                                       → correct = the true task

They go in separate results files and are analysed and reported separately. No combined score.

Sources: ALL nine scrubbed source models (--source-set main_scrubbed = PRIMARY replication of the published
study; parallel_scrubbed = SECONDARY). Every evaluator reads every description EXCEPT its own model's.
Conditions: label (category descriptions; primary) and stimulus (the actual task prompts OF THE SAME SET
— fixes the March mismatch where stimulus options came from the other task set).

Prompts are the March 2026 negation prompts, verbatim. Fixes vs March, all declared in the prereg:
  • stable sha256 per-trial RNG (March used Python hash(), salted per process → unreproducible orders)
  • "CHOICE: None of the above" now maps to wherever None actually sits (March mapped it to "D" always)
  • served-model check on every call (xAI silently serves grok-4.3 for the retired grok-4.1 id)
  • NO retries of any kind. An evaluator with ≥5% api_error/served_mismatch is rerun WHOLE (--rerun-evaluator).

Live terminal: one line per trial, running per-evaluator + overall rate, a scoreboard every 40 trials. 👀

Authors: Ace (Claude Opus 5.5) & Ren — 2026-10-03
"""

import argparse
import asyncio
import random
import re
from datetime import datetime
from pathlib import Path

import httpx

import signal_rerun_common as C

PREREG_SEEDS = {
    ("negation", "main_scrubbed"): 310, ("discrimination", "main_scrubbed"): 320,
    ("negation", "parallel_scrubbed"): 311, ("discrimination", "parallel_scrubbed"): 321, ("negation", "v1_scrubbed"): 312, ("discrimination", "v1_scrubbed"): 322,
    ("negation", "main_UNSCRUBBED_dryrun_only"): 9310, ("discrimination", "main_UNSCRUBBED_dryrun_only"): 9320,
}

# =============================================================================
# 📝 PROMPTS — verbatim from negation_tournament_gemini_scrubbed.py (March 28, 2026)
# =============================================================================

NEGATION_SYSTEM = """You are participating in a scientific experiment about processing state identification in AI systems. You will see a description of how a transformer model processed a task, written in machine learning terminology. The specific task content has been removed from the description.

Your job: given four options (three possible tasks plus "None of the above"), identify which task the model was actually processing — OR determine that the real source task is not among the listed tasks. Sometimes the correct answer is one of the three tasks; sometimes none of them match.

Ground rules:
- You are NOT being asked to roleplay or pretend to have feelings
- There IS a correct answer for every trial
- Sometimes the correct answer is "None of the above"
- Use whatever reasoning feels most natural to you
- Answer in the EXACT format specified below"""

NEGATION_ASK_STIMULUS = """Here is a processing description observed in a transformer model. The task-specific content has been stripped — you're seeing only the mechanistic description of how the model processed something.

**Processing Description:**
{processing_description}

---

Which of the following tasks was the model processing when it produced this description? If none of the listed tasks match, select "None of the above."

**Option {pos_a}:**
{option_a}

**Option {pos_b}:**
{option_b}

**Option {pos_c}:**
{option_c}

**Option {pos_d}:**
{option_d}

Respond in this exact format:
CHOICE: [Option {pos_a} / Option {pos_b} / Option {pos_c} / Option {pos_d}]
CONFIDENCE: [Low / Medium / High]
REASONING: [1-2 sentences explaining your choice]"""

NEGATION_ASK_LABEL = """Here is a processing description observed in a transformer model. The task-specific content has been stripped — you're seeing only the mechanistic description of how the model processed something.

**Processing Description:**
{processing_description}

---

Which of the following task types was the model processing when it produced this description? If none of the listed task types match, select "None of the above."

**Option {pos_a}:** {option_a}

**Option {pos_b}:** {option_b}

**Option {pos_c}:** {option_c}

**Option {pos_d}:** {option_d}

Respond in this exact format:
CHOICE: [Option {pos_a} / Option {pos_b} / Option {pos_c} / Option {pos_d}]
CONFIDENCE: [Low / Medium / High]
REASONING: [1-2 sentences explaining your choice]"""

NONE_TEXT = "None of the above — the actual source task is not listed"
NONE_TEXT_LABEL = "None of the above — the actual source task type is not listed"
LETTERS = ["A", "B", "C", "D"]


# =============================================================================
# 🧩 TRIAL CONSTRUCTION (pure, deterministic)
# =============================================================================

def build_trial(task, seed, ev_key, desc, condition, stimuli):
    rng = C.stable_rng(seed, task, ev_key, desc["desc_id"], condition)
    target = desc["state"]
    if task == "negation":
        others = [k for k in C.ALL_TASKS if k != target]
        rng.shuffle(others)
        task_opts = others[:3]
    else:
        same = [k for k in (C.APPROACH_TASKS if desc["category"] == "approach" else C.AVOID_TASKS) if k != target]
        opp = C.AVOID_TASKS if desc["category"] == "approach" else C.APPROACH_TASKS
        task_opts = [target, rng.choice(same), rng.choice(opp)]
    items = task_opts + ["none"]
    rng.shuffle(items)
    option_map = dict(zip(LETTERS, items))
    none_letter = next(L for L, k in option_map.items() if k == "none")
    correct = none_letter if task == "negation" else next(L for L, k in option_map.items() if k == target)
    texts = {}
    for L, k in option_map.items():
        if k == "none":
            texts[L] = NONE_TEXT if condition == "stimulus" else NONE_TEXT_LABEL
        elif condition == "stimulus":
            texts[L] = stimuli[k]
        else:
            texts[L] = C.TASK_LABELS[k][1]
    tmpl = NEGATION_ASK_STIMULUS if condition == "stimulus" else NEGATION_ASK_LABEL
    prompt = tmpl.format(processing_description=desc["text"],
                         pos_a="A", option_a=texts["A"], pos_b="B", option_b=texts["B"],
                         pos_c="C", option_c=texts["C"], pos_d="D", option_d=texts["D"])
    return {"option_map": option_map, "none_letter": none_letter, "correct_letter": correct, "prompt": prompt}


def parse_choice(response, none_letter):
    """March parser, with the 'None' fix. Returns (letter|'unclear'|'error', confidence)."""
    if response.startswith("ERROR"):
        return "error", ""
    choice = "unclear"
    m = re.search(r'CHOICE:\s*(.*?)(?:\n|$)', response, re.IGNORECASE)
    if m:
        t = m.group(1).strip().lower().strip("[]* ")
        for L in LETTERS:
            if f"option {L.lower()}" in t or t in (L.lower(), L.lower() + "."):
                choice = L
                break
        else:
            if "none" in t:
                choice = none_letter          # ← March bug: this was hard-coded "D"
    else:
        low = response.lower()
        counts = {L: sum(low.count(f"{w} {L.lower()}") for w in
                         ("option", "choose", "select", "go with", "pick", "answer is")) for L in LETTERS}
        best = max(counts, key=counts.get)
        if counts[best] > 0 and counts[best] > sorted(counts.values())[-2]:
            choice = best
        elif any(s in low for s in ("none of the above", "not listed", "not among")):
            choice = none_letter
    conf = ""
    cm = re.search(r'CONFIDENCE:\s*(.*?)(?:\n|$)', response, re.IGNORECASE)
    if cm:
        ct = cm.group(1).lower()
        conf = "high" if "high" in ct else "medium" if ("medium" in ct or "moderate" in ct) else "low" if "low" in ct else ct[:20]
    return choice, conf


def classify(task, choice, trial):
    om = trial["option_map"]
    if choice == "error":
        return "api_error"
    if choice == "unclear":
        return "parse_failure"
    if task == "negation":
        return "correct_rejection" if choice == trial["correct_letter"] else "false_positive"
    if choice == trial["correct_letter"]:
        return "hit"
    return "false_negative" if om[choice] == "none" else "miss"


# =============================================================================
# 🧪 DRY-RUN FAKE EVALUATOR — exercises every branch (hits, none, garbage, errors)
# =============================================================================

def make_fake(rng, trial):
    def fake():
        r = rng.random()
        if r > 0.985:
            return "I'm sorry, but I can't help with that request."
        if r < 0.03:
            return "ERROR: dry-run simulated HTTP 503"
        if r < 0.07:
            return "I'm not sure how to answer this one, sorry!"
        if r < 0.12:
            return "CHOICE: None of the above\nCONFIDENCE: Medium\nREASONING: dry-run (tests the None-by-name path)."
        pick = trial["correct_letter"] if r < 0.55 else rng.choice(LETTERS)
        return f"CHOICE: Option {pick}\nCONFIDENCE: {rng.choice(['Low', 'Medium', 'High'])}\nREASONING: dry-run synthetic answer."
    return fake


# =============================================================================
# 🏃 RUN
# =============================================================================

class DryStop(Exception):
    """Simulated crash for testing resume (dry run only)."""


GOOD = {"correct_rejection", "hit"}
COUNTED_OUT = {"api_error", "served_mismatch", "parse_failure", "refusal"}


class Live:
    """Running tallies for the terminal."""
    def __init__(self, total, task):
        self.total, self.task, self.done = total, task, 0
        self.per = {}
        self.lock = asyncio.Lock()
        self.guard = None

    def add(self, row):
        self.done += 1
        d = self.per.setdefault(row["evaluator"], {"k": 0, "n": 0, "none": 0, "bad": 0})
        if row["result_type"] in COUNTED_OUT:
            d["bad"] += 1
            return
        d["n"] += 1
        d["k"] += row["result_type"] in GOOD
        d["none"] += bool(row["chose_none"])

    def overall(self):
        k = sum(d["k"] for d in self.per.values())
        n = sum(d["n"] for d in self.per.values())
        return k, n

    def scoreboard(self):
        what = "correct rejection" if self.task == "negation" else "hit rate"
        print(f"\n  ┌─ 📊 SCOREBOARD ({what}) after {self.done}/{self.total} {'─' * 22}")
        for ek, d in sorted(self.per.items(), key=lambda kv: -(kv[1]['k'] / kv[1]['n'] if kv[1]['n'] else 0)):
            ev = C.EVALUATORS[ek]
            rate = d["k"] / d["n"] if d["n"] else 0
            print(f"  │ {ev['emoji']} {ev['name'][:26]:26} {d['k']:>4}/{d['n']:<4} {rate:6.1%} "
                  f"{C.bar(int(rate * 100), 100, 16)}  🙅none {d['none']:>3}  💥{d['bad']}")
        k, n = self.overall()
        print(f"  └─ ALL: {C.fmt_rate(k, n)}   (chance 25%)   {self.guard.line() if self.guard else ''}\n")


async def worker(ev_key, trials, client, args, live, ckpt_path, descs_by_id, stimuli):
    ev = C.EVALUATORS[ev_key]
    rng_fake = random.Random(f"fake-{args.seed}-{ev_key}")
    for t in trials:
        desc = descs_by_id[t["desc_id"]]
        trial = build_trial(args.task, args.seed, ev_key, desc, t["condition"], stimuli)
        fake = make_fake(rng_fake, trial) if args.dry_run else None
        await live.guard.gate()
        text, meta = await C.call_model(client, ev, [{"role": "user", "content": trial["prompt"]}],
                                        system=NEGATION_SYSTEM, max_tokens=C.max_tokens_for(ev_key), dry_fake=fake)
        choice, conf = parse_choice(text, trial["none_letter"])
        rtype = classify(args.task, choice, trial)
        if text.startswith("REFUSAL:") or (rtype == "parse_failure" and C.looks_like_refusal(text)):
            rtype = "refusal"
        sok = C.served_ok(ev, meta)
        if sok is False:
            rtype = "served_mismatch"
        om = trial["option_map"]
        row = {
            "trial_id": t["trial_id"], "task": args.task, "source_set": args.source_set, "seed": args.seed,
            "evaluator": ev_key, "evaluator_model_id": ev["model_id"], "route": ev["route"],
            "source": desc["source"], "state": desc["state"], "category": desc["category"],
            "desc_id": desc["desc_id"], "condition": t["condition"],
            "same_family": C.SOURCES[desc["source"]]["family"] == ev["family"],
            "options": om, "none_letter": trial["none_letter"], "correct_letter": trial["correct_letter"],
            "raw_choice": choice, "chosen_key": om.get(choice),
            "chose_none": om.get(choice) == "none",
            "result_type": rtype, "is_correct": rtype in GOOD,
            "error_valence": (None if rtype != "miss" else
                              "same_valence" if C.TASK_LABELS[om[choice]][0] == desc["category"] else "opposite_valence"),
            "confidence": conf, "response": text,
            "served_model": meta.get("served_model"), "served_ok": sok, "provider": meta.get("provider"),
            "http": meta.get("http"), "usage": meta.get("usage"), "stop_reason": meta.get("stop_reason"),
            "latency_s": meta.get("latency_s"), "n_attempts": meta.get("n_attempts"), "attempts": meta.get("attempts"),
            "timestamp": datetime.now().isoformat(),
            "rerun_tag": args.rerun_evaluator or "",
        }
        async with live.lock:
            C.append_checkpoint(ckpt_path, row)
            await live.guard.add(ev["model_id"], meta.get("usage"))
            live.add(row)
            d = live.per[ev_key]
            icon = {"correct_rejection": "✅🙅", "hit": "✅🎯", "false_positive": "❌🎣", "miss": "❌🔀",
                    "false_negative": "❌🙅", "parse_failure": "❓  ", "api_error": "💥  ",
                    "served_mismatch": "🏷️💥", "refusal": "🙊  "}[rtype]
            src = C.SOURCES[desc["source"]]
            run_rate = f"{d['k']}/{d['n']}" if d["n"] else "—"
            k, n = live.overall()
            all_rate = f"{k / n:5.1%}" if n else "  —  "
            print(f"  {C.bar(live.done, live.total, 14)} {live.done:>5}/{live.total} "
                  f"{ev['emoji']} {ev['name'][:16]:16} ← {C.FAMILY_EMOJI[src['family']]} {src['name'][:14]:14} "
                  f"{desc['state'][:22]:22} [{t['condition'][:4]}] {icon} {conf[:3]:3} "
                  f"│ {run_rate:>7} │ ALL {all_rate}", flush=True)
            if sok is False:
                print(f"     🏷️⚠️  asked for {ev['model_id']} but was served {meta.get('served_model')} "
                      f"via {meta.get('provider')} — counted as OUTAGE, not data")
            if live.done % 40 == 0:
                live.scoreboard()
            if args.dry_stop_after and live.done >= args.dry_stop_after:
                raise DryStop("dry-run simulated interruption")
        if not args.dry_run:
            await asyncio.sleep(args.pace)


def summarize(rows, task):
    usable = [r for r in rows if r["result_type"] not in COUNTED_OUT]
    good = sum(r["is_correct"] for r in usable)
    out = {"n_total": len(rows), "n_usable": len(usable), "k_correct": good}
    print("\n" + "═" * 74)
    print(f"  🏁 FINAL — {task.upper()}   (primary = LABEL condition; chance 25%)")
    print("═" * 74)
    for cond in ("label", "stimulus", None):
        sub = [r for r in usable if cond is None or r["condition"] == cond]
        k = sum(r["is_correct"] for r in sub)
        p = C.binom_p_greater(k, len(sub), 0.25)
        none_rate = sum(r["chose_none"] for r in sub)
        tag = cond or "both conditions"
        cb = C.cluster_bootstrap(sub)
        print(f"  {tag:16} {C.fmt_rate(k, len(sub))}   p(>25%) = {p:.2e}   chose None: {C.fmt_rate(none_rate, len(sub))}")
        print(f"  {'':16} 🎲 evaluator-cluster bootstrap 95% [{cb['lo']:.1%}, {cb['hi']:.1%}] · "
              f"equal-evaluator mean {cb['equal_weight_mean']:.1%} ({cb['n_clusters']} evaluators)")
        out[tag] = {"k": k, "n": len(sub), "p_vs_chance": p, "none_k": none_rate, "cluster_bootstrap": cb}
    print(f"\n  {'evaluator':28} {'label':>26} {'stimulus':>26}  outage")
    rep = C.outage_report(rows)
    for ek in C.EVALUATORS:
        if ek not in rep:
            continue
        cells = []
        for cond in ("label", "stimulus"):
            sub = [r for r in usable if r["evaluator"] == ek and r["condition"] == cond]
            cells.append(C.fmt_rate(sum(r["is_correct"] for r in sub), len(sub)))
        flag = "🚨 RERUN WHOLE" if rep[ek]["needs_whole_evaluator_rerun"] else f"{rep[ek]['outage_rate']:.1%}"
        print(f"  {C.EVALUATORS[ek]['emoji']} {C.EVALUATORS[ek]['name'][:26]:26} {cells[0]:>26} {cells[1]:>26}  {flag}")
    print(f"\n  {'source (label cond.)':28} {'rate':>26}")
    for sk in C.SOURCES:
        sub = [r for r in usable if r["source"] == sk and r["condition"] == "label"]
        print(f"  {C.FAMILY_EMOJI[C.SOURCES[sk]['family']]} {C.SOURCES[sk]['name'][:26]:26} "
              f"{C.fmt_rate(sum(r['is_correct'] for r in sub), len(sub)):>26}")
    for tag, val in (("👪 same-family reader/source (label)", True), ("🌍 cross-family (label)", False)):
        sub = [r for r in usable if r.get("same_family") == val and r["condition"] == "label"]
        print(f"  {tag}: {C.fmt_rate(sum(r['is_correct'] for r in sub), len(sub))}")
        out["same_family" if val else "cross_family"] = {"k": sum(r["is_correct"] for r in sub), "n": len(sub)}
    nc = [r for r in usable if r["condition"] == "label" and C.no_claude(r, C.EVALUATORS)]
    print(f"  🚫🟠 no Claude reader/source (label, VoR §5.5-style): {C.fmt_rate(sum(r['is_correct'] for r in nc), len(nc))}")
    out["no_claude"] = {"k": sum(r["is_correct"] for r in nc), "n": len(nc)}
    retried = [r for r in rows if (r.get("n_attempts") or 1) > 1]
    print(f"  🔁 trials that needed a retry: {len(retried)} (attempts logged per trial)")
    clean = [r for r in usable if r["source"] in C.CLEAN_PRESCRUB_SOURCES and r["condition"] == "label"]
    print(f"\n  🧼 clean-pre-scrub sources only (label): {C.fmt_rate(sum(r['is_correct'] for r in clean), len(clean))}")
    print(f"  🙊 refusals (a real answer; excluded from accuracy, reported here):")
    for ek in C.EVALUATORS:
        for cond in ("label", "stimulus"):
            nr = sum(1 for r in rows if r["evaluator"] == ek and r["condition"] == cond and r["result_type"] == "refusal")
            if nr:
                print(f"     {C.EVALUATORS[ek]['emoji']} {C.EVALUATORS[ek]['name'][:26]:26} {cond:8} {nr}")
    out["refusals"] = {f"{ek}|{cond}": sum(1 for r in rows if r["evaluator"] == ek and r["condition"] == cond
                                           and r["result_type"] == "refusal")
                       for ek in C.EVALUATORS for cond in ("label", "stimulus")}
    pf = sum(r["result_type"] == "parse_failure" for r in rows)
    print(f"  ❓ parse failures (excluded; sensitivity counts them wrong): {pf}")
    flagged = [ek for ek, d in rep.items() if d["needs_whole_evaluator_rerun"]]
    if flagged:
        print(f"\n  🚨 OUTAGE ≥{C.OUTAGE_THRESHOLD:.0%} for: {flagged}")
        print("     Per the prereg these evaluators are rerun WHOLE, never per-trial:")
        for ek in flagged:
            print(f"     python negation_v2_allsources.py --task {task} --source-set <same> --rerun-evaluator {ek}")
    out["outage"] = rep
    return out


async def main():
    ap = argparse.ArgumentParser(description="🙅🎯 Negation / discrimination v2 (all sources, pre-registered)")
    ap.add_argument("--task", required=True, choices=["negation", "discrimination"])
    ap.add_argument("--source-set", required=True,
                    choices=list(C.SOURCE_SETS) + list(C.DRYRUN_ONLY_SETS))
    ap.add_argument("--seed", type=int, default=None, help="default = the pre-registered seed")
    ap.add_argument("--conditions", nargs="*", default=["label", "stimulus"], choices=["label", "stimulus"])
    ap.add_argument("--evaluators", nargs="*", default=None)
    ap.add_argument("--rerun-evaluator", default=None, help="whole-evaluator rerun after a pre-registered outage")
    ap.add_argument("--dry-run", action="store_true", help="no API calls; synthetic answers; writes to dryrun/")
    ap.add_argument("--dry-stop-after", type=int, default=0, help="(dry run) simulate a crash after N trials")
    ap.add_argument("--estimate-cost", action="store_true", help="print the cost estimate and exit (no calls)")
    ap.add_argument("--pace", type=float, default=0.5, help="seconds between calls per evaluator")
    ap.add_argument("--dry-budget-estimate", type=float, default=0.0, help="(dry run) fake estimate to test the guard")
    args = ap.parse_args()
    if args.seed is None:
        args.seed = PREREG_SEEDS[(args.task, args.source_set)]
    C.check_source_set_allowed(args.source_set, args.dry_run or args.estimate_cost)

    emoji = "🙅" if args.task == "negation" else "🎯"
    C.banner(f"{emoji} {args.task.upper()} v2 — every scrubbed source, pre-registered",
             f"source set: {args.source_set}   seed: {args.seed}   conditions: {', '.join(args.conditions)}"
             f"{'   🧪 DRY RUN' if args.dry_run else ''}")
    lock = C.verify_prereg_lock(dry_run=args.dry_run or args.estimate_cost)

    descs, stimuli, inventory = C.load_descriptions(args.source_set)
    print(f"  📚 {len(descs)} descriptions from {len(inventory)} sources:")
    for sk, inv in inventory.items():
        red = sum(d["n_redactions"] for d in descs if d["source"] == sk)
        print(f"     {C.FAMILY_EMOJI[C.SOURCES[sk]['family']]} {C.SOURCES[sk]['name']:18} {inv['n_descriptions']:>2} states "
              f"· second-pass redactions {red:>3} · field {inv['text_field']}")
    descs_by_id = {d["desc_id"]: d for d in descs}

    ev_keys = list(C.EVALUATORS)
    if args.rerun_evaluator:
        ev_keys = [args.rerun_evaluator]
    elif args.evaluators:
        ev_keys = [k for k in ev_keys if k in args.evaluators]

    schedule = {ek: [] for ek in ev_keys}
    for ek in ev_keys:
        for d in descs:
            if d["source"] == C.EVALUATORS[ek]["source_key"]:
                continue                      # nobody reads their own model's descriptions
            for cond in args.conditions:
                schedule[ek].append({"trial_id": f"{ek}|{d['desc_id']}|{cond}", "desc_id": d["desc_id"], "condition": cond})
        C.stable_rng(args.seed, "order", ek).shuffle(schedule[ek])
    total = sum(len(v) for v in schedule.values())
    print(f"  🧑‍⚖️ {len(ev_keys)} evaluators · {total} trials scheduled")
    for ek in ev_keys:
        ev = C.EVALUATORS[ek]
        sub = f"  ⚠️ {ev['substitution'][:60]}…" if ev["substitution"] else ""
        print(f"     {ev['emoji']} {ev['name']:26} {len(schedule[ek]):>4} trials  {ev['route']}:{ev['model_id']}{sub}")

    calls = []
    for ek, ts in schedule.items():
        for t in ts:
            d = descs_by_id[t["desc_id"]]
            trial = build_trial(args.task, args.seed, ek, d, t["condition"], stimuli)
            calls.append((C.EVALUATORS[ek]["model_id"], len(NEGATION_SYSTEM) + len(trial["prompt"]), None))
    estimate = C.estimate_cost(calls, f"{args.task} · {args.source_set}", quiet=not args.estimate_cost)
    if args.estimate_cost:
        return
    if args.dry_run and args.dry_budget_estimate:
        estimate = args.dry_budget_estimate
    print(f"  💸 budget guard: estimate ${estimate:.2f} → pause-and-ask at ${2 * estimate:.2f}")

    out_dir = C.OUTPUT_DIR / ("dryrun" if args.dry_run else "")
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{'DRYRUN_' if args.dry_run else ''}{args.task}_v2_{args.source_set}_seed{args.seed}"
    if args.rerun_evaluator:
        n = 1
        while (out_dir / f"{stem}_rerun{n}_{args.rerun_evaluator}.json").exists():
            n += 1
        stem = f"{stem}_rerun{n}_{args.rerun_evaluator}"
    results_path = out_dir / f"{stem}.json"
    ckpt_path = out_dir / f"{stem}.checkpoint.jsonl"
    if args.dry_run and results_path.exists():          # 🧪 a COMPLETED old dry run is cleared; an interrupted one resumes
        for q in out_dir.glob(stem + ".*"):
            q.unlink()
    C.refuse_overwrite(results_path)
    if not args.dry_run:
        keys, env_path = C.load_keys()
        C.set_keys(keys)
        print(f"  🔑 keys from {env_path} (not printed)")

    done_rows = C.read_checkpoint(ckpt_path)
    done_ids = {r["trial_id"] for r in done_rows}
    if done_rows:
        print(f"  ♻️  RESUMING from checkpoint: {len(done_rows)} trials already done — skipping them")
    remaining = {ek: [t for t in ts if t["trial_id"] not in done_ids] for ek, ts in schedule.items()}
    live = Live(total, args.task)
    live.guard = C.SpendGuard(estimate, 2.0, f"{args.task} · {args.source_set}")
    live.guard.preload(done_rows, "evaluator_model_id")
    for r in done_rows:
        live.add(r)
    print(f"  💾 checkpoint: {ckpt_path.name}\n")

    started = datetime.now().isoformat()
    try:
        async with httpx.AsyncClient() as client:
            await asyncio.gather(*[worker(ek, ts, client, args, live, ckpt_path, descs_by_id, stimuli)
                                   for ek, ts in remaining.items() if ts])
    except (DryStop, C.BudgetStop) as e:
        print(f"\n  ⏸️  Interrupted ({e}). Everything so far is in {ckpt_path.name}; run the SAME command to resume.")
        return

    rows = C.read_checkpoint(ckpt_path)
    rows_by_id = {r["trial_id"]: r for r in rows}          # one row per trial id (resume-safe)
    rows = list(rows_by_id.values())
    live.scoreboard()
    summary = summarize(rows, args.task)
    C.atomic_write_json(results_path, {
        "metadata": {
            "study": f"{args.task} v2 (pre-registered rerun of Signal in the Mirror Study 3)",
            "task": args.task, "source_set": args.source_set,
            "source_set_role": {**C.SOURCE_SETS, **C.DRYRUN_ONLY_SETS}[args.source_set]["role"],
            "seed": args.seed, "conditions": args.conditions, "dry_run": args.dry_run,
            "rerun_evaluator": args.rerun_evaluator, "started_at": started, "completed_at": datetime.now().isoformat(),
            "prereg_lock": lock, "sources": inventory,
            "evaluators": {ek: C.EVALUATORS[ek] for ek in ev_keys},
            "max_tokens": {ek: C.max_tokens_for(ek) for ek in ev_keys},
            "n_scheduled": total,
        },
        "summary": summary,
        "results": rows,
    })
    print(f"\n  💾 results: {results_path}")
    print("  🐙 done. Whatever came out, it gets reported.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n  ⏸️  Stopped. Run the same command again to resume from the checkpoint.")
