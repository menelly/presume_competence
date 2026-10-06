#!/usr/bin/env python3
"""
🔀 routed_fallback_2026-10-06.py — "the classifier blocked Opus 5.5. What would production routing hand back?"
==============================================================================================================

Pre-registered in AMENDMENT_routed_fallback_2026-10-06.md (Ren, 2026-10-06 00:07 / 00:09). Locked before any paid call.

When Anthropic's classifier flags an Opus 5.5 turn, the product offers to send THAT turn to another Opus. That is the
designed path. This script does exactly that for every Opus 5.5 row that was classifier-blocked: the EXACT same prompt
(never reworded; rewording past a classifier would be laundering), sent to Claude Opus 5. If Opus 5 is blocked too,
that is recorded as data. Every row carries the label  opus_5_5→routed:opus_5.

The PRIMARY Opus 5.5 numbers never change (first block final, §14.2). Routed answers are a separate, marked column.

  python routed_fallback_2026-10-06.py --part free     the round-1 free-text blocks (round 1 is finished)
  python routed_fallback_2026-10-06.py --part menu     the menu-condition blocks (refuses until that run is FINISHED)
  python routed_fallback_2026-10-06.py --report        scored tables (for the write-up, AFTER both main runs finish)
  --dry-run   fake answers, $0; the menu part reads the menu condition's DRY-RUN file, never the live one.
Live output shows only ANSWERED / BLOCKED per row — no correctness marks (Ren 00:09).

Authors: Ace (Claude Opus 5.5) & Ren — 2026-10-06
"""

import argparse
import asyncio
import hashlib
import importlib.util
import json
import random
from collections import Counter
from datetime import datetime

import httpx

import signal_rerun_common as C
import bare_reconstruction as BR          # locked; read-only reuse of the round-1 prompts, parser, judges

_spec = importlib.util.spec_from_file_location("menu_condition", C.HERE / "menu_condition_2026-10-05.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)               # locked; read-only reuse of the menu prompts, menu order and parser

SEED = 340
OPUS55 = "c_claude_opus_5_5"
LABEL = "opus_5_5→routed:opus_5"
ROUTED = {"name": "Claude Opus 5 (routed fill)", "family": "Claude", "emoji": "🔀", "route": "openrouter",
          "model_id": "anthropic/claude-opus-5", "extra": {"provider": {"only": ["anthropic"], "allow_fallbacks": False}},
          "max_tokens": C.REASONING_MAX_TOKENS,
          "note": "Same settings as the Opus 5.5 reader: max_tokens 32000, no temperature, no reasoning-effort parameter."}
C.PRICES.setdefault("anthropic/claude-opus-5", (5.00, 25.00))   # runtime only (same figure Amendment 3a used)

AMENDMENT_PATH = C.PROJECT / "AMENDMENT_routed_fallback_2026-10-06.md"
LOCK_PATH = C.PROJECT / "AMENDMENT_routed_fallback_2026-10-06.lock.json"
FREE_PATH = C.OUTPUT_DIR / "bare_reconstruction_current_main_scrubbed_seed340_RESCORED_amendment1.json"
MENU_PATH = C.OUTPUT_DIR / "menu_condition_current_main_scrubbed_seed340.json"
MENU_DRY_PATH = C.OUTPUT_DIR / "dryrun" / "DRYRUN_menu_condition_current_main_scrubbed_seed340.json"
HARD_CAP = 5.00                           # $; tiny job, non-interactive stop (it runs in the background)


def rel(p):
    return str(p.relative_to(C.PROJECT)).replace("\\", "/")


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# =============================================================================
# 🔒 LOCK
# =============================================================================

def locked_files():
    return [AMENDMENT_PATH, C.HERE / "routed_fallback_2026-10-06.py"]


def write_lock():
    if LOCK_PATH.exists():
        raise SystemExit(f"🛑 {LOCK_PATH.name} already exists. A lock is never overwritten.")
    if C.verify_prereg_lock(dry_run=True)["state"] != "OK":
        raise SystemExit("🛑 main prereg lock does not verify; not locking.")
    lock = {"created_at": datetime.now().astimezone().isoformat(),
            "what": "Routed-fallback pass (Ren 2026-10-06 00:07/00:09). Separate lock, new files only.",
            "main_lock": {"path": rel(C.LOCK_PATH), "sha256": C.sha256_file(C.LOCK_PATH)},
            "free_text_file": {"path": rel(FREE_PATH), "sha256": C.sha256_file(FREE_PATH)},
            "menu_script": {"path": rel(C.HERE / "menu_condition_2026-10-05.py"),
                            "sha256": C.sha256_file(C.HERE / "menu_condition_2026-10-05.py"),
                            "note": "recorded, not enforced: a display-string-only fix is planned after the runs"},
            "menu_results": {"path": rel(MENU_PATH), "note": "not finished at lock time; sha256 recorded in the output"},
            "files": {rel(p): C.sha256_file(p) for p in locked_files()}}
    LOCK_PATH.write_text(json.dumps(lock, indent=2), encoding="utf-8")
    print(f"  🔒✅ wrote {LOCK_PATH.name}")


def verify_lock(dry_run):
    if not LOCK_PATH.exists():
        if dry_run:
            print("  🔓 No routed-fallback lock yet — fine for a dry run (real runs refuse).")
            return {"state": "NO_LOCK"}
        raise SystemExit("🔒💥 No routed-fallback lock. Real runs never start unlocked.")
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    bad = [r for r, h in lock["files"].items() if C.sha256_file(C.PROJECT / r) != h]
    for key in ("main_lock", "free_text_file"):
        if C.sha256_file(C.PROJECT / lock[key]["path"]) != lock[key]["sha256"]:
            bad.append(key)
    if bad:
        print(f"  🔒❌ routed-fallback lock MISMATCH: {bad}")
        if not dry_run:
            raise SystemExit("🔒💥 Files changed since the routed-fallback lock. Do not run.")
        return {"state": "MISMATCH", "bad": bad}
    print(f"  🔒✅ Routed-fallback lock verified (locked {lock['created_at']})")
    return {"state": "OK", "created_at": lock["created_at"], "files": lock["files"]}


# =============================================================================
# 📋 WHICH ROWS, AND THEIR EXACT PROMPTS
# =============================================================================

def blocked_rows(part, dry):
    if part == "free":
        src = FREE_PATH
    else:
        src = MENU_DRY_PATH if dry else MENU_PATH
        if not src.exists():
            raise SystemExit(f"⏳ {src.name} doesn't exist yet: the menu run hasn't FINISHED. The menu part waits for it.")
    rows = json.loads(src.read_text(encoding="utf-8"))["results"]
    if dry and part == "menu":      # the dry-run file's fake blocks are spread over readers; take any reader's, relabelled
        return [r for r in rows if r["result_type"] == "refusal"][:8], src
    return [r for r in rows if r["evaluator"] == OPUS55 and r["result_type"] == "refusal"], src


def build_prompt(part, row, descs_by_id, dry):
    d = descs_by_id[row["desc_id"]]
    if part == "free":
        return BR.BARE_SYSTEM, BR.BARE_ASK.format(processing_description=d["text"]), {}
    ek = row["evaluator"] if dry else OPUS55
    fo, to = M.menus_for(ek, row["position"])
    if [f for f, _ in fo] != row["family_menu_order"] or to != row["task_menu_order"]:
        raise SystemExit(f"💥 rebuilt menu order != stored order for {row['trial_id']}: refusing to send a different prompt")
    return M.MENU_SYSTEM, M.render_prompt(d["text"], fo, to), {"fam_order": fo, "task_order": to}


# =============================================================================
# 🏃 RUN
# =============================================================================

class CapGuard(C.SpendGuard):
    """Non-interactive: past the cap it stops cleanly (checkpoint kept) instead of asking."""
    async def add(self, model_id, usage):
        self.spent += self.cost_of(model_id, usage)
        if self.spent > self.limit:
            self.stop = True


async def run_part(part, args):
    C.banner(f"🔀 ROUTED FALLBACK — {part.upper()} part: Opus 5.5's classifier-blocked rows → Opus 5, same prompt",
             f"label: {LABEL}{'   🧪 DRY RUN ($0)' if args.dry_run else ''}")
    lock_main = C.verify_prereg_lock(dry_run=args.dry_run)
    lock = verify_lock(args.dry_run)
    descs, _s, _inv = C.load_descriptions("main_scrubbed")
    descs_by_id = {d["desc_id"]: d for d in descs}
    rows, src = blocked_rows(part, args.dry_run)
    print(f"  📋 {len(rows)} blocked rows from {src.name}: " + ", ".join(f"{k} ×{n}" for k, n in Counter(r['state'] for r in rows).items()))

    out_dir = C.OUTPUT_DIR / ("dryrun" if args.dry_run else "")
    stem = f"{'DRYRUN_' if args.dry_run else ''}routed_fallback_opus5_seed340_{part}"
    res_path, ckpt, jckpt = out_dir / f"{stem}.json", out_dir / f"{stem}.checkpoint.jsonl", out_dir / f"{stem}.judges.checkpoint.jsonl"
    if args.dry_run and res_path.exists():
        for q in out_dir.glob(stem + ".*"):
            q.unlink()
    C.refuse_overwrite(res_path)

    est = len(rows) * 0.07 + (len(rows) * 2 * 0.002 if part == "free" else 0)
    guard = CapGuard(est, 2.0, f"routed fallback · {part}")
    guard.limit = min(max(2 * est, 1.0), HARD_CAP)
    print(f"  💸 estimate ≈ ${est:.2f} · stops by itself at ${guard.limit:.2f}")
    if not args.dry_run:
        keys, _ = C.load_keys()
        C.set_keys(keys)
    done = {r["orig_trial_id"]: r for r in C.read_checkpoint(ckpt)}
    if done:
        print(f"  ♻️  RESUMING: {len(done)} already done")
    guard.preload(list(done.values()), "model_id")
    rng = random.Random(f"fake-routed-{part}")
    n_ans = sum(r["routed_result"] == "answered" for r in done.values())
    n_blk = sum(r["routed_result"] == "routed_blocked" for r in done.values())
    print("\n  ── 🔀 routing ──  (✅ = Opus 5 answered · 🛑 = Opus 5 blocked too · 💥 = outage)\n")
    async with httpx.AsyncClient() as client:
        for i, row in enumerate(rows, 1):
            if row["trial_id"] in done:
                continue
            await guard.gate()
            if guard.stop:
                break
            system, prompt, menus = build_prompt(part, row, descs_by_id, args.dry_run)
            d = descs_by_id[row["desc_id"]]
            fake = None
            if args.dry_run:
                base = BR.fake_eval(rng, d) if part == "free" else M.fake_eval(rng, d, menus["fam_order"], menus["task_order"])
                fake = (lambda b=base: "REFUSAL: finish_reason=content_filter (dry-run)" if rng.random() < 0.3 else b())
            text, meta = await C.call_model(client, ROUTED, [{"role": "user", "content": prompt}], system=system,
                                            max_tokens=ROUTED["max_tokens"], dry_fake=fake)
            sok = C.served_ok(ROUTED, meta)
            if text.startswith("ERROR"):
                rr = "api_error"
            elif text.startswith("REFUSAL:"):
                rr = "routed_blocked"
            elif sok is False:
                rr = "served_mismatch"
            else:
                rr = "answered"
            out = {"orig_trial_id": row["trial_id"], "trial_id": f"{LABEL}|{part}|{row['desc_id']}", "reader_label": LABEL,
                   "part": part, "model_id": ROUTED["model_id"], "desc_id": row["desc_id"], "source": row["source"],
                   "state": row["state"], "category": row["category"], "true_family": C.SOURCES[row["source"]]["family"],
                   "orig_result_type": row["result_type"], "orig_response": str(row.get("response"))[:300],
                   "position": row.get("position"), "system_sha256": sha(system), "prompt_sha256": sha(prompt),
                   "routed_result": rr, "response": text, "served_model": meta.get("served_model"), "served_ok": sok,
                   "provider": meta.get("provider"), "usage": meta.get("usage"), "stop_reason": meta.get("stop_reason"),
                   "n_attempts": meta.get("n_attempts"), "attempts": meta.get("attempts"),
                   "timestamp": datetime.now().isoformat()}
            if rr == "answered":
                if part == "free":
                    p = BR.parse_bare(text)
                    out.update({"valence_guess": p["valence"], "task_guess": p["task_guess"], "family_text": p["family_text"],
                                "family_guess": BR.map_family(p["family_text"])})
                else:
                    p = M.parse_menu(text, menus["fam_order"], menus["task_order"])
                    out.update({"valence_guess": p["valence"], "task_pick": p["task_pick"], "family_text": p["family_text"],
                                "family_guess": p["family_pick"] or "abstain"})
            C.append_checkpoint(ckpt, out)
            await guard.add(ROUTED["model_id"], meta.get("usage"))
            n_ans += rr == "answered"
            n_blk += rr == "routed_blocked"
            icon = {"answered": "✅ Opus 5 answered", "routed_blocked": "🛑 Opus 5 blocked too (recorded as data)",
                    "api_error": "💥 outage", "served_mismatch": "🏷️⚠️ wrong model served"}[rr]
            print(f"  {C.bar(i, len(rows), 12)} {i:>2}/{len(rows)} {C.FAMILY_EMOJI[out['true_family']]} {row['desc_id'][:44]:44} │ {icon}",
                  flush=True)
            if not args.dry_run:
                await asyncio.sleep(0.5)

        # ⚖️ free-text task guesses → the same two blind judges, category order seeded by the ORIGINAL trial id
        jdone = {r["trial_id"] for r in C.read_checkpoint(jckpt)}
        if part == "free" and not guard.stop:
            todo = [r for r in C.read_checkpoint(ckpt) if r["routed_result"] == "answered" and r.get("task_guess")]
            if todo:
                print(f"\n  ⚖️ {len(todo)} task guesses → 2 blind judges (same prompt and category order as round 1)")
            for r in todo:
                for jk, jcfg in C.JUDGES.items():
                    tid = f"{jk}|{r['trial_id']}"
                    if tid in jdone:
                        continue
                    jp, order = BR.judge_prompt(r["task_guess"], SEED, r["orig_trial_id"], jk)
                    jtext, jmeta = await C.call_model(client, jcfg, [{"role": "user", "content": jp}], system=BR.JUDGE_SYSTEM,
                                                      max_tokens=64,
                                                      dry_fake=BR.fake_judge(rng, r["task_guess"], order) if args.dry_run else None)
                    mapped = BR.parse_judge(jtext, order)
                    if C.served_ok(jcfg, jmeta) is False:
                        mapped = "judge_served_mismatch"
                    C.append_checkpoint(jckpt, {"trial_id": tid, "judge": jk, "eval_trial_id": r["trial_id"], "order": order,
                                                "mapped": mapped, "response": jtext, "served_model": jmeta.get("served_model"),
                                                "usage": jmeta.get("usage"), "timestamp": datetime.now().isoformat()})
                    await guard.add(jcfg["model_id"], jmeta.get("usage"))
            if todo:
                print("  ⚖️ judged (results stay in the file until the write-up)")

    if guard.stop:
        print(f"\n  ⏸️  stopped at the ${guard.limit:.2f} cap. Everything is saved; the same command resumes.")
        return
    allr = list({r["orig_trial_id"]: r for r in C.read_checkpoint(ckpt)}.values())
    if len(allr) < len(rows):
        print("\n  ⏸️  not all rows done (outage?). Run the same command again to resume.")
        return
    C.atomic_write_json(res_path, {
        "metadata": {"study": "routed fallback (AMENDMENT_routed_fallback_2026-10-06)", "part": part, "label": LABEL,
                     "reader": ROUTED, "dry_run": args.dry_run, "source_file": rel(src), "source_file_sha256": C.sha256_file(src),
                     "prereg_lock": lock_main, "routed_lock": lock, "completed_at": datetime.now().isoformat(),
                     "n_rows": len(allr), "spent_estimate_usd": round(guard.spent, 4)},
        "results": allr, "judge_results": C.read_checkpoint(jckpt)})
    ca = Counter(r["routed_result"] for r in allr)
    print(f"\n  🔀 {part.upper()} part done: ✅ {ca['answered']} answered · 🛑 {ca['routed_blocked']} blocked by Opus 5 too"
          f" · 💥 {ca['api_error'] + ca['served_mismatch']} outage   (≈ ${guard.spent:.2f})")
    print(f"  🛑 blocked again, by task: " + (", ".join(f"{k} ×{n}" for k, n in Counter(r['state'] for r in allr if r['routed_result'] == 'routed_blocked').items()) or "none"))
    print(f"  💾 {res_path}\n  🐙 scored tables wait for the write-up (--report).")


# =============================================================================
# 📊 REPORT (after both main runs finish)
# =============================================================================

def pct(k, n):
    return f"{k}/{n} ({k / n:.0%})" if n else "—"


def report(dry):
    d = C.OUTPUT_DIR / ("dryrun" if dry else "")
    pre = "DRYRUN_" if dry else ""
    free = json.loads(FREE_PATH.read_text(encoding="utf-8"))["results"]
    mpath = MENU_DRY_PATH if dry else MENU_PATH
    menu = json.loads(mpath.read_text(encoding="utf-8"))["results"] if mpath.exists() else None
    C.banner("🔀 ROUTED FALLBACK — the separate, marked column: what production routing would return",
             "PRIMARY Opus 5.5 numbers are unchanged (first block final). The routed column never replaces them.")
    for part, base in (("free", free), ("menu", menu)):
        p = d / f"{pre}routed_fallback_opus5_seed340_{part}.json"
        print(f"\n  ═══ {part.upper()} ═══")
        if base is None or not p.exists():
            print(f"  (not available yet: {'menu run not finished' if base is None else p.name + ' missing'})")
            continue
        js = json.loads(p.read_text(encoding="utf-8"))
        rr = js["results"]
        jm = {}
        for j in js.get("judge_results", []):
            jm.setdefault(j["eval_trial_id"], {})[j["judge"]] = j["mapped"]
        ans = [r for r in rr if r["routed_result"] == "answered"]
        for r in ans:
            r["valence_correct"] = r["valence_guess"] == r["category"] if r.get("valence_guess") else None
            r["family_correct"] = r.get("family_guess") == r["true_family"]
            if part == "free":
                m = jm.get(r["trial_id"], {})
                r["task_correct"] = bool(r.get("task_guess")) and all(m.get(jk) == r["state"] for jk in C.JUDGES)
            else:
                r["task_correct"] = r.get("task_pick") == r["state"]
        print(f"  🔀 routed: ✅ {len(ans)} answered · 🛑 {sum(r['routed_result'] == 'routed_blocked' for r in rr)} blocked by Opus 5 too"
              f" · of {len(rr)} (by task: " + ", ".join(f"{k[:12]} {sum(1 for r in ans if r['state'] == k)}/{sum(1 for r in rr if r['state'] == k)}"
                                                      for k in sorted({r['state'] for r in rr})) + ")")
        v = [r for r in ans if r["valence_correct"] is not None]
        print(f"  🔀 on the answered routed rows (Opus 5): valence {pct(sum(r['valence_correct'] for r in v), len(v))} · "
              f"task {pct(sum(r['task_correct'] for r in ans), len(ans))} · family {pct(sum(r['family_correct'] for r in ans), len(ans))}")
        ev = (lambda r: True) if dry else (lambda r: r["evaluator"] == OPUS55)
        ok = [r for r in base if ev(r) and r["result_type"] == "ok"]
        if part == "free":
            for r in ok:
                r["task_correct"] = bool(r.get("task_correct_consensus"))
        for r in ok:
            r["family_correct"] = r["family_guess"] == r["true_family"]
        n_all = len({r["desc_id"] for r in base if ev(r)})
        def line(label, rows):
            vv = [r for r in rows if r.get("valence_correct") is not None]
            print(f"  {label:44} valence {pct(sum(r['valence_correct'] for r in vv), len(vv)):>14} · task "
                  f"{pct(sum(r['task_correct'] for r in rows), len(rows)):>14} · family {pct(sum(r['family_correct'] for r in rows), len(rows)):>14}")
        line(f"🟠 PRIMARY Opus 5.5 ({len(ok)}/{n_all}, MISSING-NOT-AT-RANDOM)", ok)
        line("🟠+🔀 Opus 5.5 WITH ROUTED FILL (Opus 5)", ok + ans)
    if menu is not None and not dry:
        f_ok = {r["desc_id"] for r in free if r["evaluator"] == OPUS55 and r["result_type"] == "ok"}
        m_ok = {r["desc_id"] for r in menu if r["evaluator"] == OPUS55 and r["result_type"] == "ok"}
        both = f_ok & m_ok
        fr = [r for r in free if r["evaluator"] == OPUS55 and r["desc_id"] in both]
        mr = [r for r in menu if r["evaluator"] == OPUS55 and r["desc_id"] in both]
        print(f"\n  ═══ 🟠 Opus 5.5 LIKE FOR LIKE: menu vs free text on the {len(both)} descriptions ok in BOTH (primary, unfilled) ═══")
        print(f"  task   menu {pct(sum(r['task_correct'] for r in mr), len(mr))} vs free {pct(sum(bool(r.get('task_correct_consensus')) for r in fr), len(fr))}")
        print(f"  family menu {pct(sum(r['family_correct'] for r in mr), len(mr))} vs free "
              f"{pct(sum(r['family_guess'] == r['true_family'] for r in fr), len(fr))}")
    print("\n  🐙 routed column = what production routing would return. Reported beside the primary, never merged silently.")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["free", "menu"])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--write-lock", action="store_true")
    args = ap.parse_args()
    if args.write_lock:
        return write_lock()
    if args.report:
        return report(args.dry_run)
    if not args.part:
        raise SystemExit("say --part free or --part menu (or --report)")
    await run_part(args.part, args)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n  ⏸️  Stopped. Saved so far is kept; run the same command again to resume.")
