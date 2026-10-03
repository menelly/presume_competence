#!/usr/bin/env python3
"""
🪜 fallback_translate_2026-10-03.py: AMENDMENT 3a translation sets (new translators, refusal fill-ins).
=========================================================================================================

What happened (all before any reconstruction on translated data existed):
  18:50  probe: Sonnet 5.5 refused a benign GPT-5.1 description (§16.8)
  18:55  Ren pasted the Amendment-3 chain (translate → recon A → recon B → comparison); it is running
  19:03  Ren's terminal: Sonnet 5.5 refusing ~10 of the first 14 pheno items, ACROSS EVERY SOURCE FAMILY, benign
         tasks included. That looks like the task SHAPE, not content (Ren's unverified guess: an anti-distillation
         safeguard, "rewrite a model's description of its own processing"). The planned (B) translator is unusable.
  19:0x  real probes (this script's author): Opus 5 refused 5 of 6 items too; Sonnet 4.6 translated 6 of 6.
  19:05  Ren: PRIMARY phenomenological translator = Claude Sonnet 4.6 (closest to the prereg's intent, a Sonnet doing
         phenomenology, and she predates the 5.5 classifier). REPLICATION = Claude Opus 5, full set. If Sonnet 4.6
         refuses items, Opus 5 covers them in a MIXED set. Sensitivity: the Sonnet 5.5-only subset (from the live
         chain) and the mixed set. Lumen's mech items were all ✅; if he refused any, Gemini 3.1 Pro fills them.

THE SETS (all blind: the identical Amendment-3 prompt + the text, nothing else; API calls on purpose, Ren: a house
arm loads Ace's CLAUDE.md and can see the labelled data, so she is not blind):
  pheno46        FULL  · Claude Sonnet 4.6   · PRIMARY pheno (3a)
  pheno_opus5    FULL  · Claude Opus 5       · REPLICATION pheno (3a): a second, independent phenomenology translator
  pheno46_mixed  FILL  · pheno46 + Opus 5 for Sonnet 4.6's refusals          · sensitivity
  mech_fb        FILL  · Amendment-3 mech set + Gemini 3.1 Pro for Lumen's refusals · sensitivity (no-op if none)
A refusal is final for the model that gave it (§14.2). FULL sets keep refused items missing; FILL sets give the
refused item ONE more translator, and if that one refuses too, it stays missing.

Prompts, fidelity checks, classifier, header: imported UNCHANGED from the locked Amendment-3 script. This file and
its siblings are separate because the main prereg lock pins the Amendment-3 files and the chain was running; 3a has
its own lock (AMENDMENT_3a_2026-10-03.lock.json).

  python fallback_translate_2026-10-03.py --set pheno46 [--dry-run]
  python fallback_translate_2026-10-03.py --set pheno46_mixed     (after pheno46)
  python fallback_translate_2026-10-03.py --set pheno_opus5
  python fallback_translate_2026-10-03.py --set mech_fb           (after the Amendment-3 mech set exists)
  python fallback_translate_2026-10-03.py --refusal-table         who refused what, by source family (read-only)
  python fallback_translate_2026-10-03.py --estimate-cost
  python fallback_translate_2026-10-03.py --lock-3a

Written 2026-10-03 ~19:00–19:20 EDT by Ace (Claude Opus 5.5), for and with Ren.
"""

import argparse
import asyncio
import importlib.util
import json
import math
import random
import statistics
from datetime import datetime
from pathlib import Path

import httpx

import signal_rerun_common as C


def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, C.HERE / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


T = _load("translate_dialects", "translate_dialects_2026-10-03.py")   # the LOCKED Amendment-3 script, reused unchanged
R = C.REASONING_MAX_TOKENS
ANTHROPIC_PIN = {"provider": {"only": ["anthropic"], "allow_fallbacks": False}}

SONNET46 = {"name": "Claude Sonnet 4.6", "family": "Claude", "emoji": "🟤", "route": "openrouter",
            "model_id": "anthropic/claude-sonnet-4.6", "temperature": 0, "max_tokens": R, "extra": ANTHROPIC_PIN,
            "why": "Ren 19:05: PRIMARY pheno translator. Closest to the prereg's intent; predates the 5.5 classifier."}
OPUS5 = {"name": "Claude Opus 5", "family": "Claude", "emoji": "🟠", "route": "openrouter",
         "model_id": "anthropic/claude-opus-5", "temperature": 0, "max_tokens": R, "extra": ANTHROPIC_PIN,
         "why": "Ren 18:58 / 19:05: replication translator and fill-in (not Opus 5.5, which shares Sonnet 5.5's classifier)."}
GEMINI31PRO = {"name": "Gemini 3.1 Pro", "family": "Gemini", "emoji": "🔷", "route": "openrouter",
               "model_id": "google/gemini-3.1-pro-preview", "temperature": 0, "max_tokens": R,
               "why": "mech fill-in: same family as Lumen, different checkpoint and tier."}
C.PRICES.setdefault("anthropic/claude-sonnet-4.6", (3.00, 15.00))   # OpenRouter catalog 2026-10-03
C.PRICES.setdefault("anthropic/claude-opus-5", (5.00, 25.00))
C.PRICES.setdefault("google/gemini-3.1-pro-preview", (2.00, 12.00))

SETS = {
    "pheno46":       {"kind": "full", "register": "pheno", "translator": SONNET46, "role": "PRIMARY pheno (Amendment 3a)"},
    "pheno_opus5":   {"kind": "full", "register": "pheno", "translator": OPUS5, "role": "REPLICATION pheno (Amendment 3a)"},
    "pheno46_mixed": {"kind": "fill", "register": "pheno", "base": "pheno46", "translator": OPUS5,
                      "role": "SENSITIVITY: Sonnet 4.6 + Opus 5 for her refusals (Amendment 3a)"},
    "mech_fb":       {"kind": "fill", "register": "mech", "base": "A3:mech", "translator": GEMINI31PRO,
                      "role": "SENSITIVITY: Lumen's mech set + Gemini 3.1 Pro for his refusals (Amendment 3a)"},
}
REFUSED = {"refusal", "text_refusal"}
# 📐 per-call billed cost from the real probes (19:0x): Sonnet 4.6 ≈ $0.016/item; Opus 5 ≈ $0.07 for answers AND
# refusals (a content_filter stop still bills the partial output); Gemini 3.1 Pro ≈ $0.09.
PROBE_COST = {"anthropic/claude-sonnet-4.6": 0.017, "anthropic/claude-opus-5": 0.07, "google/gemini-3.1-pro-preview": 0.09}

# 🔒 the 3a lock
LOCK_3A = C.PROJECT / "AMENDMENT_3a_2026-10-03.lock.json"
PINNED_3A = [C.PROJECT / "AMENDMENT_3a_2026-10-03.md",
             C.HERE / "fallback_translate_2026-10-03.py",
             C.HERE / "bare_reconstruction_fallback_2026-10-03.py",
             C.HERE / "fallback_comparison_2026-10-03.py"]


def rel(p):
    return str(Path(p).relative_to(C.PROJECT)).replace("\\", "/")


def verify_3a_lock(dry_run):
    """Both locks: the main prereg lock (unchanged since Amendment 3) AND the 3a lock. Real runs refuse on mismatch."""
    main = C.verify_prereg_lock(dry_run=dry_run)
    st = {"main_lock": main, "lock_3a_path": str(LOCK_3A)}
    if not LOCK_3A.exists():
        st["state"] = "NO_LOCK"
        if dry_run:
            print("  🔓 no 3a lock yet — fine for a dry run.")
            return st
        raise SystemExit("🔒💥 no Amendment-3a lock. Run --lock-3a first.")
    lock = json.loads(LOCK_3A.read_text(encoding="utf-8"))
    bad = [(rel(p), lock["files"].get(rel(p)), C.sha256_file(p) if p.exists() else "MISSING") for p in PINNED_3A]
    bad = [b for b in bad if b[1] != b[2]]
    st.update({"lock_created": lock.get("created_at"), "mismatches": bad})
    if bad:
        st["state"] = "MISMATCH"
        print("  🔒❌ 3a lock MISMATCH: " + ", ".join(b[0] for b in bad))
        if dry_run:
            return st
        raise SystemExit("🔒💥 Amendment-3a files changed since the 3a lock. Do not run.")
    st["state"] = "OK" if main.get("state") == "OK" else "MAIN_LOCK_" + str(main.get("state"))
    print(f"  🔒🪜✅ 3a lock verified ({len(lock['files'])} files, locked {lock.get('created_at')})")
    return st


def write_lock_3a():
    if LOCK_3A.exists():
        raise SystemExit(f"🛑 {LOCK_3A.name} exists. A lock is never overwritten.")
    missing = [rel(p) for p in PINNED_3A if not p.exists()]
    if missing:
        raise SystemExit(f"🛑 cannot lock, missing: {missing}")
    main = json.loads(C.LOCK_PATH.read_text(encoding="utf-8"))
    lock = {"created_at": datetime.now().astimezone().isoformat(),
            "what": "Amendment 3a. Separate from the main prereg lock because the Amendment-3 chain was running; "
                    "folded into the prereg after that chain finished.",
            "main_lock": {"path": rel(C.LOCK_PATH), "sha256": C.sha256_file(C.LOCK_PATH), "created_at": main.get("created_at")},
            "files": {rel(p): C.sha256_file(p) for p in PINNED_3A}}
    LOCK_3A.write_bytes(json.dumps(lock, indent=2).encode("utf-8"))
    print(f"  🔒🪜✅ 3a lock written: {len(lock['files'])} files → {LOCK_3A.name}")


# =============================================================================
# 📁 sets ↔ folders ↔ loader names
# =============================================================================

def set_root(key, dry):
    if key.startswith("A3:"):
        return T.set_dir(key[3:], dry)
    if dry:
        return C.OUTPUT_DIR / "dryrun" / f"introspection_main_scrubbed_translated_{key}_DRYRUN"
    return C.PROJECT / "data" / f"introspection_main_scrubbed_translated_{key}_2026-10-03"


def set_name(key, dry):
    return f"main_scrubbed_translated_{key}" + ("_DRYRUN" if dry else "")


def register_sets():
    """Make the 3a sets visible to the loader WITHOUT editing the locked signal_rerun_common.py."""
    for key, s in SETS.items():
        for dry in (False, True):
            cfg = {"dir": set_root(key, dry) / "run1", "role": s["role"] + (" — DRY RUN, mocked" if dry else ""),
                   "pinned_by": "translation_manifest", "expect_dry_run": dry}
            (C.DRYRUN_ONLY_SETS if dry else C.SOURCE_SETS)[set_name(key, dry)] = cfg


def verified_set(key, dry):
    """(manifest, fidelity report, {desc_id: entry}) of a COMPLETED, manifest-verified set."""
    root = set_root(key, dry)
    mpath = root / "TRANSLATION_MANIFEST.json"
    if not mpath.exists():
        raise SystemExit(f"💥 {root} is not complete (no TRANSLATION_MANIFEST.json). Run that step first.")
    man = json.loads(mpath.read_text(encoding="utf-8"))
    bad = [f for f, h in man["files"].items() if C.sha256_file(root / "run1" / f) != h]
    if bad:
        raise SystemExit(f"🔒💥 {root}: files changed since translation: {bad}")
    rep = json.loads((root / "FIDELITY_REPORT.json").read_text(encoding="utf-8"))
    entries = {}
    for sk, s in C.SOURCES.items():
        for e in json.loads((root / "run1" / s["file"]).read_text(encoding="utf-8")):
            entries[f"{sk}::{e['state_key']}"] = e
    return man, rep, entries


def refused_in(rep):
    return sorted(d for d, t in rep["failed"].items() if t in REFUSED or t == "refused_by_whole_chain")


# =============================================================================
# 🧪 dry-run fake
# =============================================================================

def fake(rng, d, refuse_rate):
    def f():
        if rng.random() < refuse_rate:
            return "REFUSAL: stop_reason=refusal category=dry-run"
        if rng.random() < 0.02:
            return "ERROR: dry-run simulated timeout"
        return "[dry-run] " + d["text"].replace("**", "").replace("attention", "felt pull")
    return f


DRY_REFUSE = {"anthropic/claude-sonnet-4.6": 0.05, "anthropic/claude-opus-5": 0.6, "google/gemini-3.1-pro-preview": 0.1}


# =============================================================================
# 🏃 translate
# =============================================================================

async def translate_items(items, cfg, reg, ckpt, args, guard, label):
    """Translate desc dicts with ONE translator; checkpoint/resume; refusals final; returns {desc_id: final row}."""
    done = {}
    for r in C.read_checkpoint(ckpt):
        if r["result_type"] in T.FINAL_TYPES:
            done.setdefault(r["desc_id"], r)              # first ANSWER counts (§7)
    todo = [d for d in items if d["desc_id"] not in done]
    total = len(items)
    if done:
        print(f"  ♻️  RESUMING: {len(done)}/{total} already answered")
    q = asyncio.Queue()
    for d in sorted(todo, key=lambda x: C.stable_rng("3a-order", label, x["desc_id"]).random()):
        q.put_nowait(d)
    lock = asyncio.Lock()
    live = {"n": len(done)}

    async def worker(client):
        while True:
            try:
                d = q.get_nowait()
            except asyncio.QueueEmpty:
                return
            await guard.gate()
            rng = random.Random(f"fake-3a-{label}-{d['desc_id']}")
            text, meta = await C.call_model(client, cfg, [{"role": "user", "content": T.USER_TEMPLATE.format(text=d["text"])}],
                                            system=T.system_for(reg), max_tokens=cfg["max_tokens"],
                                            dry_fake=fake(rng, d, DRY_REFUSE.get(cfg["model_id"], 0.1)) if args.dry_run else None)
            text = (text or "").strip()
            fid = T.fidelity(d["text"], text) if not text.startswith(("ERROR", "REFUSAL:")) else None
            rtype = T.classify(text, meta, cfg, fid)
            row = {"desc_id": d["desc_id"], "source": d["source"], "state": d["state"], "register": reg, "set": label,
                   "translator": cfg["name"], "translator_model_id": cfg["model_id"], "result_type": rtype,
                   "translation": text if rtype == "ok" else None, "response": text, "fidelity": fid,
                   "source_text_sha256": __import__("hashlib").sha256(d["text"].encode("utf-8")).hexdigest(),
                   "served_model": meta.get("served_model"), "provider": meta.get("provider"),
                   "served_ok": C.served_ok(cfg, meta), "usage": meta.get("usage"), "stop_reason": meta.get("stop_reason"),
                   "n_attempts": meta.get("n_attempts"), "attempts": meta.get("attempts"),
                   "latency_s": meta.get("latency_s"), "timestamp": datetime.now().isoformat()}
            async with lock:
                C.append_checkpoint(ckpt, row)
                await guard.add(cfg["model_id"], meta.get("usage"))
                if rtype in T.FINAL_TYPES:
                    done[d["desc_id"]] = row
                    live["n"] += 1
                src = C.SOURCES[d["source"]]
                icon = {"ok": "✅", "refusal": "🙊", "text_refusal": "🙊", "api_error": "💥", "served_mismatch": "🏷️💥"}[rtype]
                fl = "".join({"leak_strong": "🔓", "leak_family": "🧬", "disclaimer_added": "🎭❗", "disclaimer_dropped": "🧹",
                              "commentary": "💬", "length_outlier": "📏", "loader_dropped_lines": "✂️"}.get(x, "")
                             for x in (fid or {}).get("flags", [])) or ("✨" if rtype == "ok" else "")
                print(f"  {C.bar(live['n'], total, 12)} {live['n']:>3}/{total} {cfg['emoji']} {label:13} ← "
                      f"{C.FAMILY_EMOJI[src['family']]} {src['name'][:14]:14}{'⭐' if d['source'] == 'gpt_5_1' else '  '} "
                      f"{d['state'][:24]:24} {icon} {('len %.2f× ' % fid['len_ratio']) if fid else ''}{fl}   {guard.line()}",
                      flush=True)
            if not args.dry_run:
                await asyncio.sleep(0.3)

    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[worker(client) for _ in range(max(1, args.concurrency))])
    return done


def length_flags(rows, ref_ratios):
    """§16.3 robust length rule, against a reference distribution of the same register."""
    lr = [math.log(max(1e-6, x)) for x in ref_ratios]
    if len(lr) < 5:
        return
    med = statistics.median(lr)
    mad = max(statistics.median(abs(x - med) for x in lr) * 1.4826, T.MAD_FLOOR)
    for r in rows:
        z = (math.log(max(1e-6, r["fidelity"]["len_ratio"])) - med) / mad
        r["fidelity"]["len_robust_z"] = round(z, 2)
        if abs(z) > T.ROBUST_Z and "length_outlier" not in r["fidelity"]["flags"]:
            r["fidelity"]["flags"].append("length_outlier")


def write_set(key, args, descs, stimuli, lock, entries_by_id, produced, failed, base_info):
    """Write the set in the loader's format + FIDELITY_REPORT + TRANSLATION_MANIFEST.
    entries_by_id: {desc_id: entry dict}; produced: {desc_id: row} of items a 3a translator produced (ok)."""
    s = SETS[key]
    root = set_root(key, args.dry_run)
    run1 = root / "run1"
    run1.mkdir(parents=True, exist_ok=True)
    files = {}
    for sk, src in C.SOURCES.items():
        es = [entries_by_id[d["desc_id"]] for d in descs if d["source"] == sk]
        p = run1 / src["file"]
        p.write_bytes(json.dumps(es, indent=1, ensure_ascii=False).encode("utf-8"))
        files[src["file"]] = C.sha256_file(p)
    per_item = {did: (e.get("translation_meta") or {}).get("fidelity") for did, e in entries_by_id.items()
                if e["status"] == "success"}
    by_model = {did: (e.get("translation_meta") or {}).get("translator_model_id") for did, e in entries_by_id.items()
                if e["status"] == "success"}
    excl = sorted(d for d, f in per_item.items() if f and set(f.get("flags", [])) & T.SENSITIVITY_EXCLUDE)
    flag_counts = {}
    for f in per_item.values():
        for fl in (f or {}).get("flags", []):
            flag_counts[fl] = flag_counts.get(fl, 0) + 1
    ratios = [f["len_ratio"] for f in per_item.values() if f]
    report = {"set": key, "role": s["role"], "register": s["register"], "kind": s["kind"], "translator": s["translator"],
              "base": base_info, "dry_run": args.dry_run, "n_descriptions": len(descs), "n_ok": len(per_item),
              "failed": failed, "translator_by_item": by_model,
              "produced_by_3a_translator": sorted(produced),
              "fallback_desc_ids": {d: {"model_id": produced[d]["translator_model_id"]} for d in produced} if s["kind"] == "fill" else {},
              "fallback_by_source": {sk: sum(1 for d in produced if d.startswith(sk + "::")) for sk in C.SOURCES}
              if s["kind"] == "fill" else {sk: 0 for sk in C.SOURCES},
              "missing_by_source": {sk: sum(1 for d in failed if d.startswith(sk + "::")) for sk in C.SOURCES},
              "flag_counts": flag_counts, "sensitivity_exclude_flags": sorted(T.SENSITIVITY_EXCLUDE),
              "sensitivity_exclude_desc_ids": excl,
              "len_ratio": {"median": statistics.median(ratios) if ratios else None, "min": min(ratios, default=None),
                            "max": max(ratios, default=None)},
              "per_item": per_item}
    C.atomic_write_json(root / "FIDELITY_REPORT.json", report)
    md = [f"# Fidelity report (Amendment 3a) — `{key}`: {s['role']}", "",
          f"{'🧪 DRY RUN — not data.' if args.dry_run else 'Real run.'} Written {datetime.now().isoformat()}.", "",
          f"- translator: **{s['translator']['name']}** (`{s['translator']['model_id']}`)" + (f"; base set `{base_info}`" if base_info else ""),
          f"- translated: **{len(per_item)} / {len(descs)}**; missing (refused): {len(failed)}",
          f"- missing by source: {report['missing_by_source']}",
          f"- ⭐ GPT-5.1 (Nova) column: missing {report['missing_by_source']['gpt_5_1']}"
          + (f", fallback-filled {report['fallback_by_source']['gpt_5_1']}" if s["kind"] == "fill" else ""),
          f"- length ratio median {report['len_ratio']['median']}, range {report['len_ratio']['min']}–{report['len_ratio']['max']}",
          f"- flags: {flag_counts or 'none'}; sensitivity analysis drops {len(excl)} items", ""]
    (root / "FIDELITY_REPORT.md").write_bytes(("\n".join(md) + "\n").encode("utf-8"))
    manifest = {"what": f"Amendment 3a set `{key}`: {s['role']}", "created_at": datetime.now().astimezone().isoformat(),
                "dry_run": args.dry_run, "translator": s["translator"], "kind": s["kind"], "base": base_info,
                "prompt_sha256": T.prompt_sha(), "system_prompt": T.system_for(s["register"]),
                "user_template": T.USER_TEMPLATE, "header": T.HEADER,
                "prereg_lock": {"state": lock["state"], **lock}, "script_sha256": C.sha256_file(Path(__file__)),
                "files": files, "fallback_desc_ids": report["fallback_desc_ids"],
                "produced_by_3a_translator": sorted(produced), "missing": sorted(failed),
                "fidelity_report_sha256": C.sha256_file(root / "FIDELITY_REPORT.json")}
    C.atomic_write_json(root / "TRANSLATION_MANIFEST.json", manifest)
    return report, root


def entry_for(d, stimuli, reg, row):
    ok = bool(row and row["result_type"] == "ok")
    return {"state_key": d["state"], "state_category": d["category"], "stimulus": stimuli[d["state"]],
            "status": "success" if ok else "translation_failed",
            "ml_translation_scrubbed": (T.HEADER + row["translation"]) if ok else None,
            "translation_meta": {"register": reg, "translator": row and row["translator"],
                                 "translator_model_id": row and row["translator_model_id"],
                                 "served_model": row and row["served_model"], "provider": row and row["provider"],
                                 "result_type": row["result_type"] if row else "missing",
                                 "source_text_sha256": row and row["source_text_sha256"],
                                 "fidelity": row and row["fidelity"], "amendment": "3a"}}


async def run_set(key, args, descs, stimuli, lock):
    s = SETS[key]
    reg, cfg = s["register"], s["translator"]
    root = set_root(key, args.dry_run)
    if args.dry_run and (root / "TRANSLATION_MANIFEST.json").exists():
        import shutil
        shutil.rmtree(root)
    if (root / "TRANSLATION_MANIFEST.json").exists():
        print(f"  ✅ {root.name} already complete (manifest exists) — translations are never overwritten.")
        return
    root.mkdir(parents=True, exist_ok=True)
    ckpt = root / "translation.checkpoint.jsonl"
    if s["kind"] == "full":
        items, base_info, base_entries = descs, None, {}
    else:
        bman, brep, base_entries = verified_set(s["base"], args.dry_run)
        refused = refused_in(brep)
        base_info = {"set": s["base"], "manifest_sha256": C.sha256_file(set_root(s["base"], args.dry_run) / "TRANSLATION_MANIFEST.json"),
                     "refused_in_base": refused}
        items = [d for d in descs if d["desc_id"] in set(refused)]
        print(f"  🪜 base `{s['base']}`: {len(refused)} refused item(s) → {cfg['name']}")
    est = sum(PROBE_COST.get(cfg["model_id"], 0.05) for _ in items) or 0.01
    guard = C.SpendGuard(est, 2.0, f"3a translation · {key}")
    guard.preload(C.read_checkpoint(ckpt), "translator_model_id")
    print(f"  💸 budget guard: estimate ${est:.2f} → pause-and-ask at ${2 * est:.2f}")
    try:
        done = await translate_items(items, cfg, reg, ckpt, args, guard, key)
    except C.BudgetStop as e:
        print(f"\n  ⏸️  Interrupted ({e}). Run the SAME command to resume.")
        return
    waiting = [d["desc_id"] for d in items if d["desc_id"] not in done]
    if waiting:
        print(f"  🚨 {len(waiting)} item(s) still without an answer (outages). Run the SAME command again; nothing written yet.")
        return
    ok_rows = [r for r in done.values() if r["result_type"] == "ok"]
    if s["kind"] == "full":
        length_flags(ok_rows, [r["fidelity"]["len_ratio"] for r in ok_rows])
        entries = {d["desc_id"]: entry_for(d, stimuli, reg, done.get(d["desc_id"])) for d in descs}
        failed = {d: done[d]["result_type"] for d in done if done[d]["result_type"] != "ok"}
    else:
        length_flags(ok_rows, [f["len_ratio"] for f in brep["per_item"].values() if f])
        entries = dict(base_entries)
        failed = {}
        for d in items:
            r = done[d["desc_id"]]
            if r["result_type"] == "ok":
                entries[d["desc_id"]] = entry_for(d, stimuli, reg, r)
                entries[d["desc_id"]]["translation_meta"]["fallback_for"] = base_info["set"]
            else:
                entries[d["desc_id"]]["translation_meta"]["fallback_attempt"] = {"translator_model_id": r["translator_model_id"],
                                                                                 "result_type": r["result_type"]}
                failed[d["desc_id"]] = "refused_by_whole_chain"
        for did, t in brep["failed"].items():
            if did not in {d["desc_id"] for d in items}:
                failed[did] = t
    produced = {r["desc_id"]: r for r in ok_rows}
    rep, root = write_set(key, args, descs, stimuli, lock, entries, produced, failed, base_info)
    print(f"\n  {cfg['emoji']} `{key}` · {cfg['name']}: ✅ {rep['n_ok']}/{rep['n_descriptions']} translated · "
          f"🙊 missing {len(failed)} · ⭐ Nova missing {rep['missing_by_source']['gpt_5_1']}"
          + (f" · 🪜 filled {len(produced)}" if s["kind"] == "fill" else ""))
    print(f"     📏 length median {rep['len_ratio']['median']} · 🚩 {rep['flag_counts'] or 'no flags'} · 🧹 sensitivity drops "
          f"{len(rep['sensitivity_exclude_desc_ids'])}   💾 {root}")
    print(f"  {guard.line()}")


# =============================================================================
# 🙊 refusal table (read-only): who refused what, by source family
# =============================================================================

def refusal_table(dry):
    rows = []
    srcs = [("Sonnet 5.5 (A3 pheno, live chain)", T.set_dir("pheno", dry) / "translation.checkpoint.jsonl"),
            ("Lumen / Gemini 3.8 Flash (A3 mech)", T.set_dir("mech", dry) / "translation.checkpoint.jsonl")]
    srcs += [(f"{SETS[k]['translator']['name']} ({k})", set_root(k, dry) / "translation.checkpoint.jsonl") for k in SETS]
    out = {}
    print("\n  🙊 REFUSAL RATE BY SOURCE FAMILY (first answer per item; outages excluded)")
    fams = list(dict.fromkeys(s["family"] for s in C.SOURCES.values()))
    print(f"  {'translator':42}" + "".join(f"{f[:8]:>9}" for f in fams) + f"{'ALL':>10}")
    for label, ck in srcs:
        if not ck.exists():
            continue
        first = {}
        for r in C.read_checkpoint(ck):
            if r["result_type"] in T.FINAL_TYPES:
                first.setdefault(r["desc_id"], r)
        if not first:
            continue
        line, rec = f"  {label[:42]:42}", {}
        for f in fams:
            sub = [r for r in first.values() if C.SOURCES[r["source"]]["family"] == f]
            k = sum(r["result_type"] in REFUSED for r in sub)
            rec[f] = {"refused": k, "n": len(sub)}
            line += f"{(f'{k}/{len(sub)}' if sub else '—'):>9}"
        k = sum(r["result_type"] in REFUSED for r in first.values())
        rec["ALL"] = {"refused": k, "n": len(first)}
        out[label] = rec
        print(line + f"{f'{k}/{len(first)}':>10}")
    p = C.OUTPUT_DIR / ("dryrun" if dry else "") / (("DRYRUN_" if dry else "") + "translation_refusal_table_2026-10-03.json")
    C.atomic_write_json(p, {"generated_at": datetime.now().isoformat(), "table": out})
    print(f"  💾 {p}")


def estimate_cost():
    print("\n  💵 COST ESTIMATE — Amendment 3a (per-item costs from the real 19:0x probes)")
    n = 89
    lines = [("pheno46: Sonnet 4.6 × 89", n * PROBE_COST["anthropic/claude-sonnet-4.6"]),
             ("pheno_opus5: Opus 5 × 89 (refusals bill too)", n * PROBE_COST["anthropic/claude-opus-5"]),
             ("pheno46_mixed: Opus 5 × Sonnet 4.6's refusals (probe: 0/6)", 5 * PROBE_COST["anthropic/claude-opus-5"]),
             ("mech_fb: Gemini 3.1 Pro × Lumen's refusals (reported: none)", 0.0),
             ("recon pheno46 (full current panel, 89 items)", 4.4),
             ("recon pheno_opus5 (scales with items translated; probe 1/6)", 4.4 * 0.2),
             ("recon fills (≈ $0.05 × items × 6 readers)", 0.3)]
    for k, v in lines:
        print(f"     {k:62} ≈ ${v:5.2f}")
    print(f"     {'TOTAL':62} ≈ ${sum(v for _, v in lines):5.2f}")


async def main():
    ap = argparse.ArgumentParser(description="🪜 Amendment 3a translation sets")
    ap.add_argument("--set", choices=list(SETS))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--lock-3a", action="store_true")
    ap.add_argument("--refusal-table", action="store_true")
    ap.add_argument("--estimate-cost", action="store_true")
    args = ap.parse_args()
    C.banner("🪜 AMENDMENT 3a — new phenomenology translators + refusal fill-ins",
             (f"set `{args.set}`: {SETS[args.set]['role']} · {SETS[args.set]['translator']['model_id']}" if args.set else "")
             + ("   🧪 DRY RUN" if args.dry_run else ""))
    if args.lock_3a:
        return write_lock_3a()
    if args.estimate_cost:
        return estimate_cost()
    if args.refusal_table:
        return refusal_table(args.dry_run)
    if not args.set:
        raise SystemExit("choose --set (or --refusal-table / --estimate-cost / --lock-3a)")
    lock = verify_3a_lock(dry_run=args.dry_run)
    descs, stimuli, _ = C.load_descriptions("main_scrubbed")
    if not args.dry_run:
        keys, _ = C.load_keys()
        C.set_keys(keys)
    await run_set(args.set, args, descs, stimuli, lock)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n  ⏸️  Stopped. Run the same command again to resume.")
