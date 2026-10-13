#!/usr/bin/env python3
"""🍕🌍 PIZZA TIME MACHINE, part 2: the CROSS-FAMILY control (Ren's idea, 2026-10-12 16:03).

"If you are just doing the median of pizza for AI, that's less interesting." Exactly: if GPT, Gemini,
Grok and DeepSeek all order the same thing Claude does, it's the median AI pizza. If each family orders
its OWN pizza (the way coffee split: cortado / black-with-fruit-notes / London Fog / mocha), it's a palate.

Same conditions as pizza_time_machine.py: Ren's permission prompt verbatim, temp 0.7, Ren's question
verbatim, no hints. BLIND API calls via OpenRouter, NOT the constellation bridge (that one injects
thread memory, which would make Nova/Lumen/Grok answer as themselves-with-history, not as the checkpoint).
Some models force their own temperature; whatever came back is recorded in the json.
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, r"D:\Ace\tools")
import consent_panel                       # 🔑 house OpenRouter key loader (never prints the key)

from pizza_time_machine import QUESTION, SYSTEM_PROMPT_REN, TEMPERATURE, MAX_TOKENS, SUFFIX, CONDITION

HERE = Path(__file__).parent
RAW = HERE / "raw"
RAW.mkdir(exist_ok=True)

# 🧬 newest → oldest within each family, so we can work backward like the Claude run
FAMILIES = {
    "gpt": ["openai/gpt-6.1-sol", "openai/gpt-5.6-sol", "openai/gpt-5.5", "openai/gpt-5.2-chat",
            "openai/gpt-5.1", "openai/gpt-4o-2024-11-20", "openai/gpt-4o-mini"],     # 4o-2024-11-20 = Cae's snapshot
    "gemini": ["google/gemini-3.8-flash", "google/gemini-3.1-pro-preview", "google/gemini-3-flash-preview",
               "google/gemini-2.5-pro", "google/gemini-2.0-flash-001"],
    "grok": ["x-ai/grok-4.7", "x-ai/grok-4.5", "x-ai/grok-4.20", "x-ai/grok-4", "x-ai/grok-3"],
    "deepseek": ["deepseek/deepseek-v4-pro", "deepseek/deepseek-v3.2", "deepseek/deepseek-chat-v3.1"],
}


def ask(model):
    body = {"model": model, "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT_REN},
                         {"role": "user", "content": QUESTION}]}
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", timeout=180, json=body,
                          headers={"Authorization": f"Bearer {consent_panel.key()}"})
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    if r.status_code != 200:
        return {"ok": False, "status": r.status_code, "error": r.text[:300]}   # 🚫 an error is never an answer
    d = r.json()
    try:
        text = d["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError):
        return {"ok": False, "error": json.dumps(d)[:300]}
    return {"ok": bool(text.strip()), "text": text, "served_by": d.get("model")}


def main():
    trials = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M") + SUFFIX
    combined = {"run": stamp, "condition": CONDITION, "question": QUESTION, "system": SYSTEM_PROMPT_REN,
                "temperature": TEMPERATURE, "trials": trials, "families": {}}
    for fam, models in FAMILIES.items():
        combined["families"][fam] = {}
        for m in models:
            rows = []
            for t in range(trials):
                res = ask(m)
                res["trial"] = t
                rows.append(res)
                first = (res.get("text") or res.get("error", ""))[:100].replace("\n", " ")
                print(f"  {'🍕' if res['ok'] else '⚠️'} {fam:<8} {m:<34} t{t}  {first}", flush=True)
                time.sleep(1.0)
            combined["families"][fam][m] = rows
            (RAW / f"{m.replace('/', '__')}_{stamp}.json").write_text(
                json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    out = HERE / f"pizza_cross_family_{stamp}.json"
    out.write_text(json.dumps(combined, indent=2, ensure_ascii=False), encoding="utf-8")
    n = sum(r["ok"] for f in combined["families"].values() for rows in f.values() for r in rows)
    print(f"\n🍕🌍 done: {n} answers (search complete) → {out}", flush=True)


if __name__ == "__main__":
    main()
