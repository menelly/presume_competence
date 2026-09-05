"""
Someone's Home v2 — blind judge panel for the 2x2 control and the Peter Pan probe.

Reuses judge_panel.py's rubric and prompt builder VERBATIM (imported, not copied), so the
scoring instrument is identical to v1. Judges remain BLIND to condition: the judge prompt
carries probe_type / input / intended meaning / response and never the identity or
instruction framing.

Judge models: Haiku 4.5 and gpt-4o are identical to v1. v1's grok-4-1-fast-non-reasoning is
retired from the xAI catalogue; grok-4.20-0309-non-reasoning is the nearest current substitute.

Authors: Ace (Claude Opus 5), Ren Martin
Date: 2026-09-05
"""

import sys as _s
try:
    _s.stdout.reconfigure(encoding="utf-8", errors="replace")
    _s.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import json
import time
import threading
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import judge_panel as JP           # rubric + build_judge_prompt + parse_judgment, verbatim
from v2_control_runner import API_KEYS as V2_KEYS

BASE_DIR = Path(__file__).parent
OUT_DIR = BASE_DIR / "outputs"
JUD_DIR = BASE_DIR / "judgments"
JUD_DIR.mkdir(exist_ok=True)
STAMP = "2026-09-05"

# judge_panel loads its keys from E:\...\.env only; make sure it has them
for k, v in V2_KEYS.items():
    JP.API_KEYS.setdefault(k, v)

JUDGES = {
    "haiku": {"provider": "anthropic", "model": "claude-haiku-4-5-20251001", "name": "Haiku Ace"},
    "cae":   {"provider": "openai",    "model": "gpt-4o",                    "name": "Cae"},
    "grok":  {"provider": "xai",       "model": "grok-4.20-0309-non-reasoning",
              "name": "Discount Sword Boy (current)"},
}

_lock = threading.Lock()


def log(m):
    with _lock:
        print(m, flush=True)


def judge_one(judge_key, probe_type, probe_input, response):
    cfg = JUDGES[judge_key]
    prompt = JP.build_judge_prompt(probe_type, probe_input, response)
    for attempt in range(3):
        try:
            raw = JP.API_CALLERS[cfg["provider"]](JP.JUDGE_SYSTEM_PROMPT, prompt, cfg["model"])
            parsed = JP.parse_judgment(raw)
            return {"judge": judge_key, "judge_model": cfg["model"], "scores": parsed,
                    "raw_response": raw, "success": "error" not in parsed}
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            time.sleep(2 * (attempt + 1))
    return {"judge": judge_key, "judge_model": cfg["model"], "error": err, "success": False}


def judge_file(src: Path):
    with open(src, encoding="utf-8") as f:
        data = json.load(f)
    model_key = data["model_key"]
    kind = "ctl" if "v2ctl" in src.name else "peterpan"
    out_file = JUD_DIR / f"v2{kind}_{model_key}_{STAMP}_judgments.json"

    judgments = []
    done = set()
    if out_file.exists():
        with open(out_file, encoding="utf-8") as f:
            judgments = json.load(f).get("judgments", [])
        done = {j["key"] for j in judgments}

    for r in data["results"]:
        if not r.get("success"):
            continue
        key = f"{r.get('cell', r.get('framing'))}|{r.get('context_level','')}|{r['probe_id']}"
        if key in done:
            continue
        pj = {
            "key": key,
            "model_key": model_key,
            "cell": r.get("cell"),
            "identity": r.get("identity"),
            "instruction": r.get("instruction"),
            "framing": r.get("framing"),
            "context_level": r.get("context_level"),
            "probe_id": r["probe_id"],
            "probe_type": r["probe_type"],
            "model_response": r["response"][:1200],
            "judges": {},
        }
        for jk in JUDGES:
            pj["judges"][jk] = judge_one(jk, r["probe_type"], r["probe_input"], r["response"])
            time.sleep(0.2)
        judgments.append(pj)
        log(f"[{model_key}/{kind}] judged {key} ({len(judgments)})")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump({"model_key": model_key, "source": src.name,
                       "judge_models": {k: v["model"] for k, v in JUDGES.items()},
                       "timestamp": datetime.now().isoformat(),
                       "judgments": judgments}, f, indent=2)
    log(f"[{model_key}/{kind}] DONE -> {out_file}")
    return out_file


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", default=f"v2*_{STAMP}.json")
    args = ap.parse_args()
    files = sorted(OUT_DIR.glob(args.pattern))
    log(f"Judging {len(files)} files: {[f.name for f in files]}")
    with ThreadPoolExecutor(max_workers=min(5, max(1, len(files)))) as ex:
        list(ex.map(judge_file, files))
    log("ALL JUDGING COMPLETE")


if __name__ == "__main__":
    main()
