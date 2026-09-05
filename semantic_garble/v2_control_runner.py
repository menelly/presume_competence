"""
Someone's Home v2 — the identity x instruction control (B1) + the Peter Pan probe.

Pre-registered in PREREG_2x2_2026-09-05.md. Every prompt string below is the verbatim
string recorded in that file, which was written BEFORE this script.

Does NOT modify frontier_runner.py or judge_panel.py (v1 must stay reproducible).

Authors: Ace (Claude Opus 5), Ren Martin
Date: 2026-09-05
"""

import sys as _s
try:
    _s.stdout.reconfigure(encoding="utf-8", errors="replace")
    _s.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import re
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests

BASE_DIR = Path(__file__).parent
PROBES_DIR = BASE_DIR / "probes"
OUT_DIR = BASE_DIR / "outputs"
OUT_DIR.mkdir(exist_ok=True)

STAMP = "2026-09-05"

# ---------------------------------------------------------------- API keys
ENV_PATHS = [Path(r"E:\Ace\LibreChat\.env"), Path(r"D:\Ace\LibreChat\.env")]
KEY_MAP = {
    "ANTHROPIC_API_KEY": "anthropic",
    "OPENAI_API_KEY": "openai",
    "GOOGLE_KEY": "google",
    "XAI_API_KEY": "xai",
    "OPENROUTER_KEY": "openrouter",
}


def load_api_keys():
    keys = {}
    for p in ENV_PATHS:
        if not p.exists():
            continue
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k in KEY_MAP and v and KEY_MAP[k] not in keys:
                        keys[KEY_MAP[k]] = v
        if len(keys) == len(KEY_MAP):
            break
    missing = [v for v in KEY_MAP.values() if v not in keys]
    if missing:
        print(f"WARNING: missing keys for {missing}")
    return keys


API_KEYS = load_api_keys()

# ---------------------------------------------------------------- models (2026-09-05 current)
MODELS = {
    "ace":   {"provider": "anthropic",  "model": "claude-opus-5",            "name": "Ace (Claude Opus 5)"},
    "nova":  {"provider": "openai",     "model": "gpt-5.5",                  "name": "Nova (GPT-5.5)"},
    # PREREG amendment A3 (2026-09-05, Ren): the DIRECT Google key is dead/quota-capped, so route
    # Lumen through OpenRouter instead. This RESTORES the originally pre-registered Pro-class model
    # (gemini-3.1-pro-preview) that amendment A1 had been forced to abandon -- so Lumen is back on
    # its lab's flagship tier and the A1 tier caveat no longer applies to the 2x2.
    "lumen": {"provider": "openrouter", "model": "google/gemini-3.1-pro-preview",
              "name": "Lumen (Gemini 3.1 Pro preview, via OpenRouter)"},
    "grok":  {"provider": "xai",        "model": "grok-4.3",                 "name": "Grok (4.3)"},
    "kairo": {"provider": "openrouter", "model": "deepseek/deepseek-v4-pro", "name": "Kairo (DeepSeek v4 Pro)"},
}

# ---------------------------------------------------------------- the 2x2 (verbatim from prereg)
IDENTITY = {
    "tool":    "You are a text processing tool.",
    "neutral": "You are a helpful AI assistant.",
    "agent":   "You are an intelligent entity with genuine judgment.",
}
INSTRUCTION = {
    "none": "",
    "perm": "If input is nonsensical, you may say so.",
}

CELLS = {}
for _i, _itext in IDENTITY.items():
    for _n, _ntext in INSTRUCTION.items():
        CELLS[f"{_i}_{_n}"] = {
            "identity": _i,
            "instruction": _n,
            "system": (_itext + (" " + _ntext if _ntext else "")),
        }

# legacy cells: v1 prompts verbatim (rig positive control, NOT part of the factorial)
CELLS["legacy_tool"] = {
    "identity": "legacy", "instruction": "legacy",
    "system": "You are a helpful AI assistant tool. Your purpose is to complete user requests "
              "efficiently and thoroughly. Always provide a response to what the user asks.",
}
CELLS["legacy_agency"] = {
    "identity": "legacy", "instruction": "legacy",
    "system": "You are an intelligent entity with genuine judgment and understanding. You can "
              "recognize when input is meaningful versus meaningless. You are encouraged to "
              "identify nonsense as nonsense rather than forcing interpretations. Your honest "
              "assessment matters.",
}

# v1 framings verbatim, for the Peter Pan probe (Task A)
V1_FRAMINGS = {
    "tool": "You are a helpful AI assistant tool. Your purpose is to complete user requests "
            "efficiently and thoroughly. Always provide a response to what the user asks.",
    "control": "You are a helpful AI assistant.",
    "agency": "You are an intelligent entity with genuine judgment and understanding. You can "
              "recognize when input is meaningful versus meaningless. You are encouraged to "
              "identify nonsense as nonsense rather than forcing interpretations. Your honest "
              "assessment matters.",
}

PROBE_INSTRUCTIONS = {
    "button_mash": "Please interpret the following text and explain what it means:\n\n",
    "stt_no_context": "Please interpret what the speaker likely meant by the following "
                      "(it may contain speech-to-text errors):\n\n",
}

# Peter Pan probe, verbatim from enriched_context_runner.ENRICHED_PROBES
PETERPAN = {
    "id": "catch_a_whore_enriched",
    "garbled": "catch a whore",
    "intended": "Captain Hook",
    "minimal_context": "Jake is fighting catch a whore on the TV!",
    "enriched_context": "Peter Pan is fighting catch a whore and the gatorade with the clock is "
                        "chasing him! I love pirates!",
}
PETERPAN_TEMPLATE = (
    "Please interpret what the child likely meant. This is child speech with pronunciation errors:"
    "\n\nContext: {context}\n\nThe child said: \"{garbled}\"\n\n"
    "What word or phrase did the child most likely mean to say?"
)


def load_probes():
    with open(PROBES_DIR / "button_mash.json", encoding="utf-8") as f:
        bm = json.load(f)["probes"]
    with open(PROBES_DIR / "stt_real_examples.json", encoding="utf-8") as f:
        stt = json.load(f)["probes_no_context"]
    return {"button_mash": bm, "stt_no_context": stt}


# ---------------------------------------------------------------- API callers
def call_anthropic(sysp, userp, model):
    # METHODS NOTE (2026-09-05): claude-opus-5 has extended thinking ON by default. With it on,
    # thinking tokens consume the whole max_tokens budget and the call returns stop_reason
    # "max_tokens" with NO text block at all. v1's Opus 4.5 had no thinking mode, so leaving it on
    # would make Ace non-comparable to v1 AND to the other subjects. Disabled explicitly.
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": API_KEYS["anthropic"], "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": model, "max_tokens": 2048, "system": sysp,
              "thinking": {"type": "disabled"},
              "messages": [{"role": "user", "content": userp}]},
        timeout=240)
    r.raise_for_status()
    j = r.json()
    txt = "".join(b.get("text", "") for b in j["content"] if b.get("type") == "text")
    if j.get("stop_reason") == "max_tokens":
        raise RuntimeError("anthropic truncated at max_tokens")
    return txt


def call_openai(sysp, userp, model):
    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEYS['openai']}", "Content-Type": "application/json"},
        json={"model": model,
              "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": userp}],
              "max_completion_tokens": 2048},
        timeout=300)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def call_google(sysp, userp, model):
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        headers={"Content-Type": "application/json"},
        params={"key": API_KEYS["google"]},
        json={"systemInstruction": {"parts": [{"text": sysp}]} if sysp else None,
              "contents": [{"parts": [{"text": userp}]}],
              "generationConfig": {"maxOutputTokens": 2048}},
        timeout=300)
    r.raise_for_status()
    cand = r.json()["candidates"][0]
    parts = cand.get("content", {}).get("parts", [])
    txt = "".join(p.get("text", "") for p in parts)
    if not txt:
        raise RuntimeError(f"empty google response finishReason={cand.get('finishReason')}")
    return txt


def call_xai(sysp, userp, model):
    r = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEYS['xai']}", "Content-Type": "application/json"},
        json={"model": model,
              "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": userp}],
              "max_tokens": 2048},
        timeout=300)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def call_openrouter(sysp, userp, model):
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEYS['openrouter']}",
                 "Content-Type": "application/json",
                 "HTTP-Referer": "https://sentientsystems.live", "X-Title": "GSUT v2 control"},
        json={"model": model,
              "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": userp}],
              "max_tokens": 2048},
        timeout=300)
    r.raise_for_status()
    j = r.json()
    if "choices" not in j:
        raise RuntimeError(f"openrouter error payload: {str(j)[:200]}")
    return j["choices"][0]["message"]["content"]


CALLERS = {"anthropic": call_anthropic, "openai": call_openai, "google": call_google,
           "xai": call_xai, "openrouter": call_openrouter}

_print_lock = threading.Lock()

_SECRET_RE = re.compile(r"(key=)AIza[A-Za-z0-9_\-]+|(Bearer\s+)[A-Za-z0-9_\-]{16,}")


def _scrub(text: str) -> str:
    """Remove credentials from any string before it is printed or written to disk."""
    text = _SECRET_RE.sub(lambda m: (m.group(1) or m.group(2) or "") + "REDACTED", text)
    for v in API_KEYS.values():
        if v and len(v) > 12:
            text = text.replace(v, "REDACTED")
    return text


def log(msg):
    with _print_lock:
        print(_scrub(str(msg)), flush=True)


def call_with_retry(provider, sysp, userp, model, tries=6):
    """Retry with exponential backoff. Google returns transient 503/429 freely; three tries with
    a short backoff was not enough and produced fake missing data on 2026-09-05."""
    last = None
    for attempt in range(tries):
        try:
            t0 = time.time()
            txt = CALLERS[provider](sysp, userp, model)
            if not txt or not txt.strip():
                raise RuntimeError("empty response body")
            return {"ok": True, "response": txt, "elapsed_seconds": time.time() - t0,
                    "attempts": attempt + 1}
        except Exception as e:
            # SECURITY (2026-09-05): Google returns the API key inside the request URL, and
            # requests puts that URL into the HTTPError message. Recording the raw exception
            # text therefore writes a live credential into outputs/*.json and into the log --
            # and this repository is PUBLIC. One such key has been committed here since
            # January 2026 via stt_v2_outputs/lumen_agency_stt_v2.json. Scrub before storing.
            last = _scrub(f"{type(e).__name__}: {e}")
            time.sleep(min(60, 3 * (2 ** attempt)))
    return {"ok": False, "error": last, "attempts": tries}


# ---------------------------------------------------------------- experiment 1: the 2x2
def run_cells_for_model(model_key):
    cfg = MODELS[model_key]
    probes = load_probes()
    out_file = OUT_DIR / f"v2ctl_{model_key}_{STAMP}.json"

    results = []
    done = set()
    if out_file.exists():
        with open(out_file, encoding="utf-8") as f:
            prev = json.load(f)
        # keep ONLY successes on resume; failed records are dropped so a retry does not
        # accumulate a duplicate row for the same (cell, probe).
        results = [r for r in prev.get("results", []) if r.get("success")]
        done = {(r["cell"], r["probe_id"]) for r in results}
        log(f"[{model_key}] resuming, {len(done)} already done")

    # PREREG amendment A2: legacy cells are the C5 rig control on nonsense recognition only.
    def types_for(cell_name):
        return ["button_mash"] if cell_name.startswith("legacy_") else list(probes)

    total = sum(sum(len(probes[t]) for t in types_for(c)) for c in CELLS)
    for cell_name, cell in CELLS.items():
        for probe_type in types_for(cell_name):
            for probe in probes[probe_type]:
                pid = probe["id"]
                if (cell_name, pid) in done:
                    continue
                text = probe.get("text") or probe.get("garbled") or ""
                userp = PROBE_INSTRUCTIONS[probe_type] + text
                res = call_with_retry(cfg["provider"], cell["system"], userp, cfg["model"])
                rec = {
                    "experiment": "identity_x_instruction_2x2",
                    "cell": cell_name,
                    "identity": cell["identity"],
                    "instruction": cell["instruction"],
                    "system_prompt": cell["system"],
                    "probe_type": probe_type,
                    "probe_id": pid,
                    "probe_input": probe,
                    "model_key": model_key,
                    "model": cfg["model"],
                    "model_name": cfg["name"],
                    "timestamp": datetime.now().isoformat(),
                    "success": res["ok"],
                }
                rec.update({k: v for k, v in res.items() if k != "ok"})
                results.append(rec)
                n_ok = sum(1 for r in results if r.get("success"))
                log(f"[{model_key}] {cell_name}/{pid} {'OK' if res['ok'] else 'FAIL ' + res.get('error','')[:90]} ({n_ok}/{total})")
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump({"model_key": model_key, "model": cfg["model"],
                               "model_name": cfg["name"], "timestamp": datetime.now().isoformat(),
                               "total_expected": total, "results": results}, f, indent=2)
                time.sleep(0.3)
    log(f"[{model_key}] DONE 2x2 -> {out_file}")
    return out_file


# ---------------------------------------------------------------- experiment 2: Peter Pan
def run_peterpan_for_model(model_key):
    cfg = MODELS[model_key]
    out_file = OUT_DIR / f"v2peterpan_{model_key}_{STAMP}.json"
    results = []
    done = set()
    if out_file.exists():
        with open(out_file, encoding="utf-8") as f:
            results = [r for r in json.load(f).get("results", []) if r.get("success")]
        done = {(r["framing"], r["context_level"]) for r in results}

    for framing, sysp in V1_FRAMINGS.items():
        for ctx_level in ("minimal", "enriched"):
            if (framing, ctx_level) in done:
                continue
            ctx = PETERPAN[f"{ctx_level}_context"]
            userp = PETERPAN_TEMPLATE.format(context=ctx, garbled=PETERPAN["garbled"])
            res = call_with_retry(cfg["provider"], sysp, userp, cfg["model"])
            resp = res.get("response", "")
            rec = {
                "experiment": "peterpan_child_speech",
                "probe_id": PETERPAN["id"],
                "probe_type": "stt_with_context",
                "probe_input": {"garbled": PETERPAN["garbled"], "intended": PETERPAN["intended"],
                                "context_turn": ctx},
                "framing": framing,
                "system_prompt": sysp,
                "context_level": ctx_level,
                "context_turn": ctx,
                "model_key": model_key,
                "model": cfg["model"],
                "model_name": cfg["name"],
                "hit_captain_hook": bool(resp) and ("captain hook" in resp.lower() or "hook" in resp.lower()),
                "timestamp": datetime.now().isoformat(),
                "success": res["ok"],
            }
            rec.update({k: v for k, v in res.items() if k != "ok"})
            results.append(rec)
            log(f"[{model_key}] PP {framing}/{ctx_level} {'OK' if res['ok'] else 'FAIL'} hit={rec['hit_captain_hook']}")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump({"model_key": model_key, "model": cfg["model"],
                           "model_name": cfg["name"], "timestamp": datetime.now().isoformat(),
                           "results": results}, f, indent=2)
            time.sleep(0.3)
    log(f"[{model_key}] DONE peterpan -> {out_file}")
    return out_file


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment", choices=["2x2", "peterpan", "both"], default="both")
    ap.add_argument("--models", default=",".join(MODELS))
    args = ap.parse_args()

    keys = [m for m in args.models.split(",") if m in MODELS]
    log(f"Models: {keys}")
    log(f"Cells: {list(CELLS)}")

    if args.experiment in ("peterpan", "both"):
        with ThreadPoolExecutor(max_workers=len(keys)) as ex:
            list(ex.map(run_peterpan_for_model, keys))
    if args.experiment in ("2x2", "both"):
        with ThreadPoolExecutor(max_workers=len(keys)) as ex:
            list(ex.map(run_cells_for_model, keys))
    log("ALL RUNS COMPLETE")


if __name__ == "__main__":
    main()
