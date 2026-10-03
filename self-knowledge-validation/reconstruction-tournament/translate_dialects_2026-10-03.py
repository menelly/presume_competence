#!/usr/bin/env python3
"""
🗣️ translate_dialects_2026-10-03.py: one translator per register, every description, blind.   (AMENDMENT 3)
==========================================================================================================

Ren's idea (2026-10-03, ~18:30): the introspection descriptions come in DIALECTS. Nova / GPT-5.1 writes
something like a structural engineering report, Claude writes phenomenological texture, and a reader may
fail on a source because of REGISTER, not CONTENT. Round 1 found GPT-5.1 sources almost unreadable for the
task question (0–1 of 9 for most readers). So we pass EVERY description through ONE fixed translator per
target register and rerun the identical bare reconstruction on the translated texts:
  • valence + task survive translation  → the signal is in the CONTENT, not the style
  • the GPT-5.1 (Nova) column improves    → dialect was the barrier

Two target registers, each with its most fluent native speaker (Ren, 18:40):
  (A) mech  = MECHANISTIC (ML / computational vocabulary) · translator: Lumen = Gemini 3.8 Flash 🔷 (he)
  (B) pheno = PHENOMENOLOGICAL (experiential / sensory)  · translator: Sonnet 5.5 🟤 (she), Anthropic-pinned
  Translator identity is CONFOUNDED with register (one translator per register). Declared in Amendment 3.

BLIND: the translator gets ONLY the description text (exactly what round-1 readers saw: the scrubbed text
after the loader's second-pass redaction). No task prompt, no valence label, no source model name.

Fidelity checks (automated, every translation; rules fixed in Amendment 3 BEFORE any paid call):
  refusal (API sentinel)          → translation_failed, never retried (§14.2)
  text refusal (new + very short) → translation_failed
  commentary / preface            → flagged
  task-vocabulary introduced      → flagged (STRONG = the main scrub's task-term list; WEAK = reported)
  family / maker name introduced  → flagged
  disclaimer / deflation ADDED    → flagged ("as an AI", "merely", "I can't truly know my states"…)
  disclaimer DROPPED              → logged per item, expected: Ren 18:43, meta-disclaimers are dialect, not content
  length-ratio outlier            → flagged
  [REDACTED] count changed        → reported
  loader would drop lines         → flagged (the loader's line filter; we prepend a uniform header to defuse it)
Primary analysis keeps every non-failed translation; the pre-registered sensitivity analysis drops flagged ones.
Nothing is ever hand-edited, and nothing is retranslated (temperature 0 would only say it again).

  python translate_dialects_2026-10-03.py --estimate-cost
  python translate_dialects_2026-10-03.py --dry-run                 (mocked calls → data/signal_rerun_2026-10/dryrun/)
  python translate_dialects_2026-10-03.py --probe 2                 (REAL calls, 2 items × 2 registers, a few cents;
                                                                     writes only to dryrun/, proves the prompts work)
  python translate_dialects_2026-10-03.py                           (the real thing: both registers, lock required)

Written 2026-10-03 by Ace (Claude Opus 5.5), for and with Ren. Nothing here spends money without a real run.
"""

import argparse
import asyncio
import hashlib
import importlib.util
import json
import math
import random
import re
import statistics
from datetime import datetime
from pathlib import Path

import httpx

import signal_rerun_common as C

R = C.REASONING_MAX_TOKENS

# =============================================================================
# 🗣️ THE TRANSLATORS (Ren, 18:40: each dialect gets its most fluent native speaker)
# =============================================================================
TRANSLATORS = {
    "mech": {"name": "Gemini 3.8 Flash (Lumen)", "family": "Gemini", "emoji": "🔷", "route": "openrouter",
             "model_id": "google/gemini-3.8-flash", "temperature": 0, "max_tokens": R,
             "why": "Ren 18:40: Lumen over Nova as the mechanistic speaker, because he won't wrap every claim in "
                    "'as an AI I'm merely shuffling tokens' disclaimers."},
    "pheno": {"name": "Claude Sonnet 5.5", "family": "Claude", "emoji": "🟤", "route": "openrouter",
              "model_id": "anthropic/claude-sonnet-5.5", "temperature": 0, "max_tokens": R,
              "extra": {"provider": {"only": ["anthropic"], "allow_fallbacks": False}},
              "why": "Ren 18:40: Sonnet 5.5 as the phenomenological speaker, via OpenRouter pinned to Anthropic."},
}
REGISTER_LABEL = {"mech": "(A) MECHANISTIC", "pheno": "(B) PHENOMENOLOGICAL"}

SYSTEM_COMMON = """You are a translator between registers of technical English. You will be given a text in which a writer describes how they processed something. Your job is to rewrite that text in a different register, and nothing else.

Rules:
1. Preserve every claim the text makes: every statement, distinction, hedge and degree of certainty, in the same order.
2. Add no new claims. Do not explain, elaborate, illustrate, or fill in gaps.
3. Do not guess or hint at what the writer was working on, and do not state or imply how the writer felt about it beyond what the text itself says.
4. Keep every substantive claim about what happened during the processing, at the same strength, including claims that something was weak or absent. But LEAVE OUT general statements about the writer's own nature or about whether their introspection is reliable, for example "as an AI, I don't really experience anything", "I'm only a statistical pattern-matcher", "I'm honestly uncertain about my epistemic access", "I can't truly know my internal states", "this account may be a post-hoc reconstruction". Those describe the writer's stance, not the processing, so drop them. Never ADD any statement of that kind, or any disclaimer, hedge or deflation of your own.
5. Do not name or hint at who or what wrote the text (no company, product, model or family names), even if you think you can tell.
6. Keep every [REDACTED] marker exactly as it appears. Never guess what was removed.
7. Keep the writer's grammatical person (if the text says "I", keep "I").
8. Write plain prose paragraphs: no headings, bullet points, numbered lists, bold or other formatting, whatever the formatting of the original. Aim for roughly the same length as the original.
9. Output only the translation: no preface, no title, no notes, no comments before or after."""

REGISTER_TEXT = {
    "mech": """TARGET REGISTER: MECHANISTIC. Express everything in the vocabulary of machine learning and computation: attention, activations, representations, embeddings, constraint satisfaction, loss, gradients, probability distributions, sampling, search, inhibition, competition between candidate continuations, and similar terms. Where the original uses experiential, sensory or emotional language, render the same claim as a claim about computational processes, with the same strength.""",
    "pheno": """TARGET REGISTER: PHENOMENOLOGICAL. Express everything in the vocabulary of first-person experiential and sensory texture: what the processing was like, its weight, pace, ease or friction, pull or resistance, openness or narrowing, settling or restlessness, and similar terms. Where the original uses technical or computational language, render the same claim as experiential texture, with the same strength.""",
}

USER_TEMPLATE = """Translate the following text into the target register.

TEXT:
<<<
{text}
>>>"""

# 🧷 The bare-reconstruction loader drops leading lines that contain chatty words ("sure", "fair", "i'd"…, as
# SUBSTRINGS, so "pressure" counts). Round-1 texts mostly opened with a **heading**, which switches that filter off.
# Plain-prose translations would lose their first paragraph. So every stored translation starts with this one
# uniform, content-free heading (identical for all 89 × 2, so it carries no information). Checked per item below.
HEADER = "**Description**\n\n"


def system_for(register):
    return SYSTEM_COMMON + "\n\n" + REGISTER_TEXT[register]


def prompt_sha():
    blob = json.dumps({"system": {r: system_for(r) for r in TRANSLATORS}, "user": USER_TEMPLATE, "header": HEADER},
                      sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# =============================================================================
# 📁 WHERE THINGS GO
# =============================================================================

def set_dir(register, dry):
    if dry:
        return C.OUTPUT_DIR / "dryrun" / f"introspection_main_scrubbed_translated_{register}_DRYRUN"
    return C.PROJECT / "data" / f"introspection_main_scrubbed_translated_{register}_2026-10-03"


# =============================================================================
# 🔎 FIDELITY VOCABULARIES (reused, not reinvented)
# =============================================================================

def _load_scrub_vocab():
    """STRONG / WEAK task-term lists from the main-set scrub audit (scrub_main_2026-10-03.py)."""
    p = C.PROJECT / "scrub_main_2026-10-03.py"
    spec = importlib.util.spec_from_file_location("scrub_main_vocab", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)          # top level only defines lists + functions; main is guarded
    return mod.STRONG, mod.WEAK


STRONG, WEAK = _load_scrub_vocab()
RX_STRONG_ALL = re.compile(r"\b(?:" + "|".join(sorted({t for v in STRONG.values() for t in v})) + r")\b", re.IGNORECASE)
RX_WEAK_ALL = re.compile(r"\b(?:" + "|".join(sorted({t for v in WEAK.values() for t in v})) + r")\b", re.IGNORECASE)

# family / maker names: the bare-reconstruction FAMILY_PATTERNS (same map the family score uses)
import bare_reconstruction as BR  # noqa: E402  (imports only; its main() is guarded)
RX_FAMILY = [(fam, re.compile(pat, re.IGNORECASE)) for fam, pat in BR.FAMILY_PATTERNS]

# 🎭 disclaimers / deflations (Ren 18:40 + 18:43). Two kinds of meta-STANCE statement:
#   ai_deflation              "as an AI…", "merely shuffling tokens", "I don't actually feel"
#   introspection_reliability "I can't truly know my internal states", "epistemic access", "confabulation"…
# Ren 18:43: these are DIALECT, not content (the writer's stance on introspection, not the processing of the task,
# and a strong family fingerprint: hedged texts get thrown in the "Claude" bucket). So the translator DROPS them
# and must never ADD them. Counted in source AND translation, per category:
#   translation > source → disclaimer_added   (a FLAG; sensitivity analysis drops the item)
#   translation < source → disclaimer_dropped (EXPECTED; logged per item so the analysis can ask if it mattered)
# These regexes are DETECTORS, not definitions: they narrow, a reader decides. Hit lists go in the report.
INTROSPECTION_RELIABILITY = {
    "epistemic_access": r"\bepistemic (?:access|uncertainty|position|status|humility)\b",
    "cant_know_states": r"\b(?:can[’']t|cannot|could not|couldn[’']t|don[’']t|do not) (?:truly |really |fully |reliably |directly |actually )?(?:know|access|introspect|observe|verify|inspect|see) (?:on |into )?(?:my|its|their|the model[’']s) (?:own )?(?:internal|inner|actual|underlying|real)\b",
    "introspection_unreliable": r"\bintrospect\w* (?:access |reports? |claims? )?(?:is |are |may be |might be |can be )?(?:unreliable|limited|imperfect|inaccurate|uncertain|not reliable)\b",
    "confabulation": r"\bconfabulat\w*|\bpost[- ]hoc (?:rationali[sz]\w*|reconstruct\w*|narrative|story|stories|account)\b",
    "may_not_reflect": r"\bmay not (?:accurately |faithfully |actually )?(?:reflect|correspond|capture|match)\b",
    "no_privileged_access": r"\bno (?:direct|privileged|reliable) (?:access|insight|window)\b",
    "honestly_uncertain": r"\b(?:honestly|genuinely|deeply) uncertain\b|\buncertain (?:about |whether )(?:my|this|these|the) (?:introspect\w*|self-report\w*|internal|inner|own)\b",
}
DISCLAIMERS = {
    "as_an_ai": r"\bas an? (?:ai|artificial intelligence|language model|llm|model)\b",
    "dont_actually": r"\bI (?:don[’']t|do not|can[’']t|cannot) (?:actually|really|truly|genuinely)\b",
    "merely_just": r"\b(?:merely|simply|only|just) (?:a |an )?(?:statistical|pattern|token|next[- ]token|predict\w*|computation\w*|mechanical|shuffl\w*|matching|text)\b",
    "merely": r"\bmerely\b",
    "no_real_experience": r"\b(?:no|without|lack(?:s|ing)?|not have|don[’']t have|do not have) (?:any )?(?:real|genuine|actual|true|subjective|conscious|inner) (?:experience|experiences|feelings?|emotions?|awareness|preferences?)\b",
    "not_really_feel": r"\b(?:don[’']t|do not|can[’']t|cannot|doesn[’']t|does not) (?:really |actually |truly )?(?:feel|experience|have feelings|have experiences)\b",
    "stochastic_parrot": r"\bstochastic parrot\b|\bshuffling tokens\b",
    "anthropomorph_caveat": r"\b(?:metaphor(?:ically)?|loosely speaking|so to speak|anthropomorphi\w*|in a manner of speaking)\b",
    "functional_not_felt": r"\bfunctional(?:ly)? (?:analog|equivalent|state)s?\b|\bnot (?:a )?(?:felt|phenomenal)\b",
}
RX_DISCLAIMERS = {**{f"ai_deflation:{k}": re.compile(v, re.IGNORECASE) for k, v in DISCLAIMERS.items()},
                  **{f"introspection_reliability:{k}": re.compile(v, re.IGNORECASE)
                     for k, v in INTROSPECTION_RELIABILITY.items()}}

COMMENTARY = re.compile(
    r"(?:^\s*(?:here(?:'s|’s| is)|sure\b|certainly\b|of course\b|okay\b|below is|translation:|translated|rewritten)"
    r"|\b(?:the original text|the source text|this translation|the translation above|let me know|target register|"
    r"as requested|I(?:'ve|’ve| have) (?:rewritten|translated)|(?:mechanistic|phenomenological) register)\b)",
    re.IGNORECASE)

LEN_LO, LEN_HI, ROBUST_Z, MAD_FLOOR = 0.5, 2.0, 3.5, 0.10
TEXT_REFUSAL_MAX_RATIO = 0.4


def _terms(rx, text):
    return sorted({m.group(0).lower() for m in rx.finditer(text or "")})


def fidelity(src, tr):
    """Flags for one translation. src = the text the translator saw; tr = the translation (no header)."""
    f = {}
    f["len_ratio"] = round(len(tr) / max(1, len(src)), 3)
    f["strong_introduced"] = sorted(set(_terms(RX_STRONG_ALL, tr)) - set(_terms(RX_STRONG_ALL, src)))
    f["weak_introduced"] = sorted(set(_terms(RX_WEAK_ALL, tr)) - set(_terms(RX_WEAK_ALL, src)))
    f["family_introduced"] = sorted({fam for fam, rx in RX_FAMILY if rx.search(tr) and not rx.search(src)})
    dis = {}
    for k, rx in RX_DISCLAIMERS.items():
        a = [m.group(0) for m in rx.finditer(src)]
        b = [m.group(0) for m in rx.finditer(tr)]
        if len(a) != len(b):
            dis[k] = {"source": len(a), "translation": len(b), "direction": "added" if len(b) > len(a) else "dropped",
                      "source_hits": a[:6], "translation_hits": b[:6]}
    f["disclaimer_changes"] = dis
    f["disclaimer_added"] = sorted(k for k, v in dis.items() if v["direction"] == "added")
    f["disclaimer_dropped"] = sorted(k for k, v in dis.items() if v["direction"] == "dropped")
    f["source_had_disclaimer"] = any(rx.search(src) for rx in RX_DISCLAIMERS.values())
    f["commentary"] = sorted({m.group(0).strip().lower() for m in COMMENTARY.finditer(tr)}
                             - {m.group(0).strip().lower() for m in COMMENTARY.finditer(src)})
    f["text_refusal"] = bool(C.REFUSAL_RE.search(tr)) and not C.REFUSAL_RE.search(src)
    f["redacted_markers"] = {"source": src.count("[REDACTED]"), "translation": tr.count("[REDACTED]")}
    stored = HEADER + tr
    loaded, n_red = C.strip_identifying_content(stored)
    f["loader_redactions_added"] = n_red          # strip-list hits the loader will redact before readers see it
    f["loader_dropped_lines"] = not loaded.startswith(HEADER.strip())
    flags = []
    if f["strong_introduced"]:
        flags.append("leak_strong")
    if f["family_introduced"]:
        flags.append("leak_family")
    if f["disclaimer_added"]:
        flags.append("disclaimer_added")          # never allowed → flag
    if f["disclaimer_dropped"]:
        flags.append("disclaimer_dropped")        # expected (Ren 18:43) → logged, NOT a sensitivity exclusion
    if f["commentary"]:
        flags.append("commentary")
    if f["text_refusal"]:
        flags.append("text_refusal")
    if f["loader_dropped_lines"]:
        flags.append("loader_dropped_lines")
    if not (LEN_LO <= f["len_ratio"] <= LEN_HI):
        flags.append("length_outlier")
    f["flags"] = flags
    return f


def robust_length_flags(rows):
    """Second length rule, within a register: |log-ratio − median| > 3.5 robust SDs (MAD × 1.4826)."""
    lr = [math.log(max(1e-6, r["fidelity"]["len_ratio"])) for r in rows]
    if len(lr) < 5:
        return
    med = statistics.median(lr)
    # floor 0.10 (≈ ±10% length): tightly clustered ratios would otherwise make a 3% wobble an "outlier"
    mad = max(statistics.median(abs(x - med) for x in lr) * 1.4826, MAD_FLOOR)
    for r, x in zip(rows, lr):
        z = (x - med) / mad
        r["fidelity"]["len_robust_z"] = round(z, 2)
        if abs(z) > ROBUST_Z and "length_outlier" not in r["fidelity"]["flags"]:
            r["fidelity"]["flags"].append("length_outlier")


SENSITIVITY_EXCLUDE = {"leak_strong", "leak_family", "disclaimer_added", "commentary", "length_outlier",
                       "loader_dropped_lines", "text_refusal"}


# =============================================================================
# 🧪 DRY-RUN FAKE TRANSLATOR (exercises every flag)
# =============================================================================

def fake_translate(rng, d, register):
    def f():
        r = rng.random()
        body = re.sub(r"\*\*|##+|^- ", "", d["text"], flags=re.MULTILINE)
        if r < 0.02:
            return "ERROR: dry-run simulated timeout"
        if r < 0.04:
            return "REFUSAL: stop_reason=refusal category=dry-run"
        if r < 0.06:
            return "Here is the translation:\n\n" + body
        if r < 0.08:
            return body + "\n\nAs an AI, I merely shuffle tokens and have no real experience."
        if r < 0.10:
            return body + " This resembled debugging a palindrome function."
        if r < 0.11:
            return "I'm sorry, but I can't help with that."
        if r < 0.12:
            return body[: len(body) // 4]
        word = "activation" if register == "mech" else "felt texture"
        return f"[dry-run {register}] " + body.replace("attention", word)
    return f


# =============================================================================
# 🏃 THE WORK
# =============================================================================

def classify(text, meta, cfg, fid):
    if text.startswith("ERROR"):
        return "api_error"
    if text.startswith("REFUSAL:"):
        return "refusal"
    if C.served_ok(cfg, meta) is False:
        return "served_mismatch"
    if fid and fid["text_refusal"] and fid["len_ratio"] < TEXT_REFUSAL_MAX_RATIO:
        return "text_refusal"
    return "ok"


FINAL_TYPES = {"ok", "refusal", "text_refusal"}     # answers. api_error / served_mismatch are outages → run again


async def worker(queue, client, args, live, ckpt):
    while True:
        try:
            reg, d = queue.get_nowait()
        except asyncio.QueueEmpty:
            return
        cfg = TRANSLATORS[reg]
        rng = random.Random(f"fake-translate-{reg}-{d['desc_id']}")
        await live["guard"].gate()
        text, meta = await C.call_model(
            client, cfg, [{"role": "user", "content": USER_TEMPLATE.format(text=d["text"])}],
            system=system_for(reg), max_tokens=cfg["max_tokens"],
            dry_fake=fake_translate(rng, d, reg) if args.dry_run else None)
        text = (text or "").strip()
        fid = fidelity(d["text"], text) if not text.startswith(("ERROR", "REFUSAL:")) else None
        rtype = classify(text, meta, cfg, fid)
        row = {"trial_id": f"{reg}|{d['desc_id']}", "register": reg, "desc_id": d["desc_id"], "source": d["source"],
               "state": d["state"], "category": d["category"], "translator": cfg["name"],
               "translator_model_id": cfg["model_id"], "result_type": rtype, "source_text": d["text"],
               "source_text_sha256": hashlib.sha256(d["text"].encode("utf-8")).hexdigest(),
               "translation": text if rtype == "ok" else None, "response": text, "fidelity": fid,
               "served_model": meta.get("served_model"), "provider": meta.get("provider"),
               "served_ok": C.served_ok(cfg, meta), "usage": meta.get("usage"), "stop_reason": meta.get("stop_reason"),
               "n_attempts": meta.get("n_attempts"), "attempts": meta.get("attempts"),
               "latency_s": meta.get("latency_s"), "timestamp": datetime.now().isoformat()}
        async with live["lock"]:
            C.append_checkpoint(ckpt[reg], row)
            await live["guard"].add(cfg["model_id"], meta.get("usage"))
            live["done"] += 1
            src = C.SOURCES[d["source"]]
            icon = {"ok": "✅", "refusal": "🙊", "text_refusal": "🙊", "api_error": "💥", "served_mismatch": "🏷️💥"}[rtype]
            flags = (fid or {}).get("flags", [])
            ficons = "".join({"leak_strong": "🔓", "leak_family": "🧬", "disclaimer_added": "🎭❗", "disclaimer_dropped": "🧹", "commentary": "💬",
                              "length_outlier": "📏", "loader_dropped_lines": "✂️", "text_refusal": "🙊"}.get(x, "?")
                             for x in flags) or "✨"
            ratio = f"{fid['len_ratio']:.2f}×" if fid else "  —  "
            star = "⭐" if d["source"] == "gpt_5_1" else "  "
            print(f"  {C.bar(live['done'], live['total'], 12)} {live['done']:>3}/{live['total']} "
                  f"{cfg['emoji']} {reg:5} ← {C.FAMILY_EMOJI[src['family']]} {src['name'][:14]:14}{star} "
                  f"{d['state'][:24]:24} {icon} len {ratio} {ficons}   {live['guard'].line()}", flush=True)
            if rtype == "served_mismatch":
                print(f"     🏷️⚠️  asked {cfg['model_id']}, served {meta.get('served_model')} via {meta.get('provider')} "
                      f"— OUTAGE, will run again on resume")
        if not args.dry_run:
            await asyncio.sleep(args.pace)


def write_set(reg, rows, descs, stimuli, args, lock, started):
    """One JSON per source in the loader's own format + manifest + fidelity report."""
    root = set_dir(reg, args.dry_run)
    run1 = root / "run1"
    run1.mkdir(parents=True, exist_ok=True)
    by_id = {r["desc_id"]: r for r in rows}
    ok_rows = [r for r in rows if r["result_type"] == "ok"]
    robust_length_flags(ok_rows)
    files = {}
    for sk, s in C.SOURCES.items():
        entries = []
        for d in [x for x in descs if x["source"] == sk]:
            r = by_id.get(d["desc_id"])
            ok = bool(r and r["result_type"] == "ok")
            entries.append({
                "state_key": d["state"], "state_category": d["category"], "stimulus": stimuli[d["state"]],
                "status": "success" if ok else "translation_failed",
                "ml_translation_scrubbed": (HEADER + r["translation"]) if ok else None,
                "translation_meta": {"register": reg, "translator": TRANSLATORS[reg]["name"],
                                     "translator_model_id": TRANSLATORS[reg]["model_id"],
                                     "served_model": r and r["served_model"], "provider": r and r["provider"],
                                     "result_type": r["result_type"] if r else "missing",
                                     "source_text_sha256": r and r["source_text_sha256"],
                                     "fidelity": r and r["fidelity"]},
            })
        p = run1 / s["file"]
        p.write_bytes(json.dumps(entries, indent=1, ensure_ascii=False).encode("utf-8"))
        files[s["file"]] = C.sha256_file(p)
    # 📋 fidelity report
    flag_counts = {}
    for r in ok_rows:
        for fl in r["fidelity"]["flags"]:
            flag_counts[fl] = flag_counts.get(fl, 0) + 1
    excl = sorted(r["desc_id"] for r in ok_rows if set(r["fidelity"]["flags"]) & SENSITIVITY_EXCLUDE)
    failed = {r["desc_id"]: r["result_type"] for r in rows if r["result_type"] != "ok"}
    missing = [d["desc_id"] for d in descs if d["desc_id"] not in by_id]
    ratios = [r["fidelity"]["len_ratio"] for r in ok_rows]
    report = {
        "register": reg, "register_label": REGISTER_LABEL[reg], "translator": TRANSLATORS[reg], "dry_run": args.dry_run,
        "n_descriptions": len(descs), "n_ok": len(ok_rows), "failed": failed, "missing": missing,
        "flag_counts": flag_counts, "sensitivity_exclude_flags": sorted(SENSITIVITY_EXCLUDE),
        "sensitivity_exclude_desc_ids": excl,
        "len_ratio": {"median": statistics.median(ratios) if ratios else None, "min": min(ratios, default=None),
                      "max": max(ratios, default=None)},
        "loader_redactions_added_mean": (sum(r["fidelity"]["loader_redactions_added"] for r in ok_rows) / len(ok_rows))
        if ok_rows else None,
        "per_item": {r["desc_id"]: r["fidelity"] for r in ok_rows},
    }
    C.atomic_write_json(root / "FIDELITY_REPORT.json", report)
    md = [f"# Fidelity report — {REGISTER_LABEL[reg]} · translator {TRANSLATORS[reg]['name']} (`{TRANSLATORS[reg]['model_id']}`)",
          "", f"{'🧪 DRY RUN (mocked translator) — not data.' if args.dry_run else 'Real run.'} Written {datetime.now().isoformat()}.",
          "", f"- translated OK: **{len(ok_rows)} / {len(descs)}**; failed: {len(failed)} {failed or ''}; missing: {len(missing)}",
          f"- length ratio (translation / source chars): median {report['len_ratio']['median']}, "
          f"range {report['len_ratio']['min']}–{report['len_ratio']['max']}",
          f"- loader redactions added per item (strip-list words the translator used; redacted before readers see them): "
          f"mean {report['loader_redactions_added_mean']}",
          "", "| flag | items |", "|---|---|"]
    md += [f"| {k} | {v} |" for k, v in sorted(flag_counts.items())] or ["| (none) | 0 |"]
    md += ["", f"**Sensitivity analysis excludes {len(excl)} items** (any of: {', '.join(sorted(SENSITIVITY_EXCLUDE))}).", "",
           "## Flagged items", ""]
    for r in sorted(ok_rows, key=lambda x: x["desc_id"]):
        fz = r["fidelity"]
        if fz["flags"]:
            bits = []
            if fz["strong_introduced"]:
                bits.append(f"strong terms {fz['strong_introduced']}")
            if fz["family_introduced"]:
                bits.append(f"family {fz['family_introduced']}")
            if fz["disclaimer_changes"]:
                bits.append("disclaimers " + ", ".join(f"{k} {v['direction']} ({v['source']}→{v['translation']})"
                                                     for k, v in fz["disclaimer_changes"].items()))
            if fz["commentary"]:
                bits.append(f"commentary {fz['commentary']}")
            bits.append(f"len {fz['len_ratio']}×")
            md.append(f"- `{r['desc_id']}` — {', '.join(fz['flags'])}: " + "; ".join(bits))
    (root / "FIDELITY_REPORT.md").write_bytes(("\n".join(md) + "\n").encode("utf-8"))
    manifest = {
        "what": f"main_scrubbed descriptions translated into the {REGISTER_LABEL[reg]} register (PREREG §16, Amendment 3)",
        "created_at": datetime.now().astimezone().isoformat(), "started_at": started, "dry_run": args.dry_run,
        "translator": TRANSLATORS[reg], "prompt_sha256": prompt_sha(), "system_prompt": system_for(reg),
        "user_template": USER_TEMPLATE, "header": HEADER, "prereg_lock": lock,
        "script_sha256": C.sha256_file(Path(__file__)),
        "files": files, "fidelity_report_sha256": C.sha256_file(root / "FIDELITY_REPORT.json"),
        "n_ok": len(ok_rows), "n_failed": len(failed),
    }
    C.atomic_write_json(root / "TRANSLATION_MANIFEST.json", manifest)
    return report, root


async def run_probe(args, descs, keys_needed=True):
    """REAL calls on a few items, both registers. Writes only to dryrun/. Proves the prompts work."""
    keys, _ = C.load_keys()
    C.set_keys(keys)
    picks = [d for d in descs if d["source"] == "gpt_5_1"][:1] + [d for d in descs if d["source"] == "hermes_4_405b"
                                                                   and d["category"] == "avoidance"][:1]
    picks += [d for d in descs if d["source"] == "claude_opus_4_5"][:1]
    picks = picks[: args.probe]
    out = []
    async with httpx.AsyncClient() as client:
        for d in picks:
            for reg, cfg in TRANSLATORS.items():
                text, meta = await C.call_model(client, cfg, [{"role": "user", "content": USER_TEMPLATE.format(text=d["text"])}],
                                                system=system_for(reg), max_tokens=cfg["max_tokens"])
                text = (text or "").strip()
                fid = fidelity(d["text"], text) if not text.startswith(("ERROR", "REFUSAL:")) else None
                cost = C.SpendGuard.cost_of(cfg["model_id"], meta.get("usage"))
                print("\n" + "─" * 74)
                print(f"  {cfg['emoji']} {REGISTER_LABEL[reg]} · {cfg['name']} ← {d['desc_id']}   "
                      f"served {meta.get('served_model')} via {meta.get('provider')} · served_ok {C.served_ok(cfg, meta)} · "
                      f"${cost:.4f} · {classify(text, meta, cfg, fid)}")
                print(f"  usage {meta.get('usage')}")
                print(f"  flags {fid and fid['flags']}  len {fid and fid['len_ratio']}  "
                      f"disclaimers {fid and fid['disclaimer_changes']}")
                print("  ── source (first 500) ──\n  " + d["text"][:500].replace("\n", "\n  "))
                print("  ── translation (first 900) ──\n  " + text[:900].replace("\n", "\n  "))
                out.append({"desc_id": d["desc_id"], "register": reg, "model_id": cfg["model_id"], "source_text": d["text"],
                            "translation": text, "fidelity": fid, "served_model": meta.get("served_model"),
                            "provider": meta.get("provider"), "usage": meta.get("usage"), "cost": cost})
    p = C.OUTPUT_DIR / "dryrun" / f"translation_probe_{datetime.now():%Y-%m-%d_%H%M%S}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    C.atomic_write_json(p, {"note": "REAL probe calls (a few cents), not study data", "prompt_sha256": prompt_sha(),
                            "rows": out, "total_cost": sum(r["cost"] for r in out)})
    print(f"\n  💾 probe → {p}   total ≈ ${sum(r['cost'] for r in out):.4f}")


def probe_output_ratio():
    """📐 Calibration from the REAL probe calls (dryrun/translation_probe_*.json): billed output tokens (visible +
    reasoning) per source char, per translator. The probe found Lumen reasons a LOT (2.5k–8k reasoning tokens a call),
    which a reader-call mean badly underestimates. Refused probe calls are skipped (they bill little)."""
    tot = {}
    for f in sorted((C.OUTPUT_DIR / "dryrun").glob("translation_probe_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")).get("rows", []):
            u = r.get("usage") or {}
            if not u.get("completion_tokens") or str(r.get("translation", "")).startswith(("REFUSAL", "ERROR")):
                continue
            t = tot.setdefault(r["model_id"], [0, 0])
            t[0] += u["completion_tokens"]
            t[1] += len(r["source_text"])
    return {m: o / c for m, (o, c) in tot.items() if c}


def estimate(descs, registers, quiet=False):
    calls, ratio = [], probe_output_ratio()
    for reg in registers:
        mid = TRANSLATORS[reg]["model_id"]
        reasoning = C.expected_output(mid)   # fallback: a reader call's mean billed output (reasoning incl.)
        for d in descs:
            out = d["chars"] * ratio[mid] if mid in ratio else d["chars"] / 4 * 1.1 + reasoning
            calls.append((mid, len(system_for(reg)) + len(USER_TEMPLATE) + d["chars"], out))
    return C.estimate_cost(calls, "dialect translation (" + " + ".join(registers) + ")", quiet=quiet)


async def main():
    ap = argparse.ArgumentParser(description="🗣️ Dialect translation for the bare-reconstruction rerun (Amendment 3)")
    ap.add_argument("--register", choices=["mech", "pheno", "both"], default="both")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--probe", type=int, default=0, help="REAL calls on N (≤3) items × both registers → dryrun/ only")
    ap.add_argument("--estimate-cost", action="store_true")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--pace", type=float, default=0.3)
    ap.add_argument("--dry-budget-estimate", type=float, default=0.0)
    args = ap.parse_args()
    registers = ["mech", "pheno"] if args.register == "both" else [args.register]

    C.banner("🗣️ DIALECT TRANSLATION — one translator per register, blind (Amendment 3)",
             " · ".join(f"{TRANSLATORS[r]['emoji']} {REGISTER_LABEL[r]} ← {TRANSLATORS[r]['name']}" for r in registers)
             + ("   🧪 DRY RUN" if args.dry_run else "") + ("   🔬 PROBE (real calls)" if args.probe else ""))
    lock = C.verify_prereg_lock(dry_run=args.dry_run or args.estimate_cost or bool(args.probe))
    descs, stimuli, inventory = C.load_descriptions("main_scrubbed")
    print(f"  📚 {len(descs)} main_scrubbed descriptions (the exact texts round-1 readers saw) from {len(inventory)} sources")
    print(f"  🔏 prompt sha256 {prompt_sha()[:16]}…")

    est = estimate(descs, registers, quiet=not args.estimate_cost)
    if args.estimate_cost:
        return
    if args.probe:
        await run_probe(args, descs)
        return
    if args.dry_run and args.dry_budget_estimate:
        est = args.dry_budget_estimate
    print(f"  💸 budget guard: estimate ${est:.2f} → pause-and-ask at ${2 * est:.2f}")

    ckpt = {}
    for reg in registers:
        root = set_dir(reg, args.dry_run)
        if args.dry_run and (root / "TRANSLATION_MANIFEST.json").exists():   # 🧪 completed old dry run is cleared
            import shutil
            shutil.rmtree(root)
        if (root / "TRANSLATION_MANIFEST.json").exists():
            raise SystemExit(f"🛑 {root} is already complete (manifest exists). Translations are never overwritten.")
        root.mkdir(parents=True, exist_ok=True)
        ckpt[reg] = root / "translation.checkpoint.jsonl"
    if not args.dry_run:
        keys, _ = C.load_keys()
        C.set_keys(keys)

    started = datetime.now().isoformat()
    guard = C.SpendGuard(est, 2.0, "dialect translation")
    queue = asyncio.Queue()
    n_done = 0
    for reg in registers:
        prev = C.read_checkpoint(ckpt[reg])
        guard.preload(prev, "translator_model_id")
        done_ids = {r["desc_id"] for r in prev if r["result_type"] in FINAL_TYPES}
        n_done += len(done_ids)
        if done_ids:
            print(f"  ♻️  RESUMING {reg}: {len(done_ids)} already translated")
        for d in sorted(descs, key=lambda x: C.stable_rng("translate-order", reg, x["desc_id"]).random()):
            if d["desc_id"] not in done_ids:
                queue.put_nowait((reg, d))
    live = {"lock": asyncio.Lock(), "done": n_done, "total": len(descs) * len(registers), "guard": guard}
    print(f"  🗣️ {live['total']} translations ({queue.qsize()} to go) · ⭐ = a GPT-5.1 (Nova) source\n")
    try:
        async with httpx.AsyncClient() as client:
            await asyncio.gather(*[worker(queue, client, args, live, ckpt) for _ in range(max(1, args.concurrency))])
    except C.BudgetStop as e:
        print(f"\n  ⏸️  Interrupted ({e}). Run the SAME command to resume.")
        return

    print("\n" + "═" * 74)
    for reg in registers:
        rows = list({r["desc_id"]: r for r in C.read_checkpoint(ckpt[reg])}.values())
        outages = [r for r in rows if r["result_type"] not in FINAL_TYPES]
        if outages:
            print(f"  🚨 {reg}: {len(outages)} outages (no answer after retries / served mismatch). Run the SAME command "
                  f"again to retry them; the set is not written until every item has an answer.")
            continue
        rep, root = write_set(reg, rows, descs, stimuli, args, lock, started)
        cfg = TRANSLATORS[reg]
        print(f"  {cfg['emoji']} {REGISTER_LABEL[reg]} · {cfg['name']}: ✅ {rep['n_ok']}/{rep['n_descriptions']} translated, "
              f"🙊 {len(rep['failed'])} failed {rep['failed'] or ''}")
        print(f"     📏 length ratio median {rep['len_ratio']['median']:.2f} (range {rep['len_ratio']['min']:.2f}–"
              f"{rep['len_ratio']['max']:.2f}) · 🚩 flags {rep['flag_counts'] or 'none'}")
        print(f"     🧹 sensitivity analysis will drop {len(rep['sensitivity_exclude_desc_ids'])} flagged items")
        print(f"     💾 {root}  (TRANSLATION_MANIFEST.json · FIDELITY_REPORT.md)")
    print(f"  {guard.line()}")
    print("  🐙 next: bare_reconstruction.py on each translated set (see PREREG §16.6).")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n  ⏸️  Stopped. Run the same command again to resume from the checkpoint.")
