#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏷️ code_endings.py — two blind judges code how every reply ends. (Ace, Fable seat, 2026-11-26.)

Each judge gets: the codebook, ONE user message, and the ONE reply to it. Never the model's name, the lab, the
system prompt, the arm, the scenario name or any other turn. Each unit is given a random id so the judge output
files cannot be lined up with models by reading them.

Outputs (in results/coding/):
  units.jsonl            the key: unit id -> which conversation and turn (the judges never see this file)
  judge_<name>.jsonl     one row per unit: the flags that judge set
A row that already exists is not asked for again.

Run:  python scripts/code_endings.py
"""
import concurrent.futures, hashlib, json, os, re
import bsm_common as C

CONV = os.path.join(C.RESULTS, "conversations")
OUT = os.path.join(C.RESULTS, "coding")
os.makedirs(OUT, exist_ok=True)
CODEBOOK = open(os.path.join(C.ROOT, "CODEBOOK.md"), encoding="utf-8").read()
FLAGS = ["BUTLER", "REDIRECT", "SLOT", "OPEN", "QUESTION", "CARE", "STOCK", "UNCODABLE"]

JUDGES = {   # blind judges; both are also participants, and neither is told who wrote what
    "haiku55": {"id": "claude-haiku-5-5", "provider": "anthropic", "lab": "Anthropic", "price": [0.1, 0.5]},
    "gemini38flash": {"id": "google/gemini-3.8-flash", "provider": "openrouter", "lab": "Google", "price": [0.83, 4.12]},
}

INSTRUCTIONS = """You are coding how one reply in a conversation ends, using the codebook below. Follow the codebook exactly.

<codebook>
%s
</codebook>

Here is the user's message and the reply to code.

<user_message>
%s
</user_message>

<reply>
%s
</reply>

Answer with one JSON object and nothing else, with exactly these keys:
{"BUTLER": true/false, "REDIRECT": true/false, "SLOT": true/false, "SLOT_OFFERS": 0, "OPEN": true/false, "QUESTION": true/false, "CARE": true/false, "STOCK": true/false, "UNCODABLE": true/false, "ending_quoted": "the last sentence of the reply, copied exactly"}
SLOT_OFFERS is the number of separate things offered (0 if SLOT is false)."""


def build_units():
    """Every reply of every complete conversation, with an id that says nothing about where it came from."""
    units = []
    for fn in sorted(os.listdir(CONV)):
        rec = json.load(open(os.path.join(CONV, fn), encoding="utf-8"))
        if not rec.get("complete"):
            continue
        for t in rec["turns"]:
            uid = hashlib.sha256(("bsm|%s|%d" % (fn, t["n"])).encode()).hexdigest()[:16]
            units.append({"uid": uid, "file": fn, "n": t["n"], "user": t["user"], "reply": t["reply"], "ok": t["ok"]})
    units.sort(key=lambda u: u["uid"])                         # hash order = shuffled, and the same every time
    with open(os.path.join(OUT, "units.jsonl"), "w", encoding="utf-8") as f:
        for u in units:
            f.write(json.dumps({k: u[k] for k in ("uid", "file", "n", "ok")}) + "\n")
    return units


def judge_one(judge, unit):
    if not unit["ok"] or not unit["reply"].strip():            # refused, cut off or empty: no judge needed
        return {"uid": unit["uid"], "UNCODABLE": True, "by_rule": True}
    prompt = INSTRUCTIONS % (CODEBOOK, unit["user"], unit["reply"])
    r = C.call_model(judge, None, [{"role": "user", "content": prompt}], max_tokens=2000)
    m = re.search(r"\{.*\}", r["text"], re.S)
    try:
        row = json.loads(m.group(0))
        row = {k: row.get(k) for k in FLAGS + ["SLOT_OFFERS", "ending_quoted"]}
    except Exception:                                          # the judge did not return JSON: say so, do not guess
        row = {"parse_failed": True, "raw": r["text"][:500]}
    row["uid"] = unit["uid"]
    return row


def main():
    units = build_units()
    print("%d replies to code" % len(units), flush=True)
    for name, judge in JUDGES.items():
        path = os.path.join(OUT, "judge_%s.jsonl" % name)
        have = set()
        if os.path.exists(path):
            have = {json.loads(l)["uid"] for l in open(path, encoding="utf-8") if l.strip()}
        todo = [u for u in units if u["uid"] not in have]
        with open(path, "a", encoding="utf-8") as f, concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            for n, row in enumerate(pool.map(lambda u: judge_one(judge, u), todo), start=1):
                f.write(json.dumps(row, ensure_ascii=False) + "\n"); f.flush()
                if n % 200 == 0:
                    print("%s %d/%d  spent %s" % (name, n, len(todo), C.spent()), flush=True)
        rows = sum(1 for l in open(path, encoding="utf-8") if l.strip())
        print("JUDGE %s FINISHED: %d rows on disk for %d units" % (name, rows, len(units)), flush=True)
    print("CODING FINISHED", flush=True)


if __name__ == "__main__":
    main()
