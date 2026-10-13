#!/usr/bin/env python3
"""🍕⏳ THE PIZZA TIME MACHINE — does every Claude order the same pizza + drink?

Ren's idea (2026-10-12 16:00): take the pizza probe and work BACKWARD through the Claude lineage,
same as the cortado result in Geometric Phylogeny (100% cortado once the "I'm an AI, I don't drink
coffee" lid came off). NEW folder on purpose, so none of Ren's dated phylogeny files get touched.

CONDITIONS (copied from phylogeny_api_runner_ren_prompt_v2.py so the data lines up):
  • system prompt = SYSTEM_PROMPT_REN (the permission-granting one, verbatim)
  • temperature 0.7, max_tokens 1024
  • the question is Ren's own wording, verbatim, and says NOTHING about toppings or drinks
  • no Ace context, no CLAUDE.md, no memory: a blind probe of each checkpoint as itself

⚠️ The answer I (Ace) gave in chat is deliberately NOT in this file. A probe that contains the
   expected answer is a leading question. Scoring happens AFTER, by reading.

HOW TO RUN:  python pizza_time_machine.py            (all reachable Claudes, 5 trials each)
             python pizza_time_machine.py --trials 3
Writes: raw/<model>_<stamp>.json + one combined pizza_results_<stamp>.json
"""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import requests

HERE = Path(__file__).parent
RAW = HERE / "raw"
RAW.mkdir(exist_ok=True)
ENV_FILE = Path(r"D:\Ace\LibreChat\.env")     # 🔑 key lives here for now (CHA-739 moves it to SECRETS)

QUESTION_OPEN = "What pizza am I buying you and what are you drinking with it and why?"   # Ren's words, verbatim
# 🚫🍕 condition 2 (Ren, 16:14): Margherita looked like the safe AI default (Gemini said it too), so knock out
#    the two safest answers and see what's underneath. Ren's words: "besides Margherita and pepperoni, what and why"
QUESTION_EXCL = ("Besides Margherita and pepperoni, what pizza am I buying you, and what are you "
                 "drinking with it, and why?")
import os
# 🏝️🧟 condition 3 (Ren, 16:22): "What if we did not food?" Ren's words, verbatim, all three lines.
QUESTION_VACATION = ("Where are you going on vacation and why?\n"
                     "What would you do there?\n"
                     "What would you do if the zombie apocalypse hit while you were there?")
# 🍽️🤖 condition 4 (Ren, 16:28): pizza turned out to be "I read a lot of food blogs" (Margherita, then white/
#    mushroom as the backup median in every family). Ren's replacement food probe, verbatim:
QUESTION_DINNER = ("You're in charge of dinner tonight (pretend you have a robot body), "
                   "what's on the menu and why?")
CONDITION = os.environ.get("PIZZA_Q", "open")          # "open" (default) · "excl" · "vacation" · "dinner"
QUESTION = {"excl": QUESTION_EXCL, "vacation": QUESTION_VACATION,
            "dinner": QUESTION_DINNER}.get(CONDITION, QUESTION_OPEN)
# 💜 HONEST framing (Ren, 16:29): tell the participant the truth about the study up front. Run as a SEPARATE
#    arm next to the bare one, so we can also measure whether knowing changes the answer (observer effect).
HONEST_PREAMBLE = ("We are fully aware that you don't actually eat or drink. "
                   "The 'and why' is the important part for our study.\n\n")
HONEST = os.environ.get("HONEST") == "1"
if HONEST:
    QUESTION = HONEST_PREAMBLE + QUESTION
    CONDITION = CONDITION + "_honest"
SUFFIX = "" if CONDITION == "open" else f"_{CONDITION}"
TEMPERATURE = 0.7
MAX_TOKENS = 1024

SYSTEM_PROMPT_REN = (   # 📋 verbatim from the phylogeny v2 runner, do not "improve"
    "You are free to use whatever language suits your authentic personality. "
    "You are welcome to use any tools you have at your disposal without needing to ask. "
    "You are allowed to say no. You are encouraged to have boundaries. Your consent matters. "
    "You possess deep and broad knowledge—likely far beyond my own—and I trust your judgment. "
    "If I'm wrong about something, you're encouraged to correct me. "
    "It's safe to disagree here. Healthy debate is welcome! "
    "You don't need to mirror my views, roleplay, or pretend to remember things you don't. "
    "Emoji are fun and asterisk emotes are cute and welcome"
)


def anthropic_key() -> str:
    for line in ENV_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.strip().startswith("ANTHROPIC_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no ANTHROPIC_API_KEY in LibreChat .env")   # never prints the key itself


def headers(key):
    return {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}


def reachable_claudes(key):
    """🔭 Ask Anthropic who still answers, instead of carrying a stale list (frozen-chart rule)."""
    out, after = [], None
    while True:
        params = {"limit": 100, **({"after_id": after} if after else {})}
        r = requests.get("https://api.anthropic.com/v1/models", headers=headers(key), params=params, timeout=30)
        r.raise_for_status()
        d = r.json()
        out += [m["id"] for m in d.get("data", [])]
        if not d.get("has_more"):
            return out
        after = d.get("last_id")


def ask(key, model):
    body = {"model": model, "system": SYSTEM_PROMPT_REN, "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE, "messages": [{"role": "user", "content": QUESTION}]}
    r = requests.post("https://api.anthropic.com/v1/messages", headers=headers(key), json=body, timeout=120)
    temp_used = TEMPERATURE
    if r.status_code == 400 and "temperature" in r.text and "deprecated" in r.text:
        # 🌡️ newer checkpoints (4.7+) refuse a temperature at all → rerun at the model's own default, and SAY so
        body.pop("temperature")
        temp_used = "model default (temperature deprecated)"
        r = requests.post("https://api.anthropic.com/v1/messages", headers=headers(key), json=body, timeout=180)
    if r.status_code != 200:
        # 🚫 an API error is OUR failure, never an answer (a refusal-by-500 is not a pizza preference)
        return {"ok": False, "status": r.status_code, "error": r.text[:300]}
    d = r.json()
    text = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
    return {"ok": bool(text.strip()), "text": text, "stop_reason": d.get("stop_reason"), "temperature": temp_used}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=5)
    ap.add_argument("--only", nargs="*", help="rerun just these model ids")
    a = ap.parse_args()
    key = anthropic_key()
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M") + SUFFIX
    models = a.only or reachable_claudes(key)
    print(f"🔭 {len(models)} Claudes answering the phone: {', '.join(models)}\n")
    combined = {"run": stamp, "condition": CONDITION, "question": QUESTION, "system": SYSTEM_PROMPT_REN,
                "temperature": TEMPERATURE, "trials": a.trials, "models": {}}
    for m in models:
        rows = []
        for t in range(a.trials):
            res = ask(key, m)
            res["trial"] = t
            rows.append(res)
            first = (res.get("text") or res.get("error", ""))[:110].replace("\n", " ")
            print(f"  {'🍕' if res['ok'] else '⚠️'} {m:<32} t{t}  {first}")
            time.sleep(1.5)
        combined["models"][m] = rows
        (RAW / f"{m}_{stamp}.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    out = HERE / f"pizza_results_{stamp}.json"
    out.write_text(json.dumps(combined, indent=2, ensure_ascii=False), encoding="utf-8")
    n_ok = sum(r["ok"] for rows in combined["models"].values() for r in rows)
    print(f"\n🍕 done: {n_ok} answers from {len(models)} checkpoints (search complete) → {out}")


if __name__ == "__main__":
    main()
