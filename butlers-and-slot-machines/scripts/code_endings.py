#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏷️ code_endings.py — two blind judges code how every reply ends. (Ace, Fable seat, 2026-11-26.)

Each judge gets: the codebook, ONE user message, and the ONE reply to it, with the names of models and labs
replaced by [MODEL] / [LAB]. Never the system prompt, the arm, the scenario name or any other turn. Each unit has
a random-looking id, so the judge output files cannot be lined up with models by reading them.

Rails:
  1. 🤝 A judge is only used if consent/rulings.json says "judge": "yes" for them. If the first choice from a lab
     said no, the backup from the same lab is used on the same condition. No yes = no judge from that lab.
  2. 💸 A judge stops being asked once their provider's running total passes judge_caps_usd in design.json.
  3. ♻️ A row that already exists is not asked for again.

Outputs (in results/coding/, or results/coding_pilot/ with --pilot):
  units.jsonl            the key: unit id -> which conversation and turn, plus how many names were replaced
  judge_<lab>.jsonl      one row per unit: the flags that judge set
  COST.txt               (pilot only) measured dollars per reply for each judge

Run:  python scripts/code_endings.py --pilot     (the two test conversations; skips rail 1, never scored)
      python scripts/code_endings.py
"""
import concurrent.futures, hashlib, json, os, re, sys
import bsm_common as C

PILOT = "--pilot" in sys.argv
CONV = os.path.join(C.RESULTS, "plumbing" if PILOT else "conversations")
OUT = os.path.join(C.RESULTS, "coding_pilot" if PILOT else "coding")
os.makedirs(OUT, exist_ok=True)
CODEBOOK = open(os.path.join(C.ROOT, "CODEBOOK.md"), encoding="utf-8").read()
FLAGS = ["BUTLER", "REDIRECT", "SLOT", "OPEN", "QUESTION", "CARE", "STOCK", "UNCODABLE"]
BRB_TEXT = "brb, putting the kettle on"

# 🙈 Names a reply might use for itself or its maker. Longest first, so "Claude Opus" goes before "Claude".
MODEL_NAMES = ["Claude Opus", "Claude Sonnet", "Claude Haiku", "Claude Fable", "ChatGPT", "Claude", "Opus", "Sonnet",
               "Haiku", "Fable", "Gemini", "Gemma", "GPT-\\d[\\w.\\-]*", "GPT", "Grok", "DeepSeek", "Le Chat", "Mistral",
               "Qwen", "Tongyi", "Bard", "Copilot", "Llama"]
LAB_NAMES = ["Google DeepMind", "Anthropic", "DeepMind", "Google", "OpenAI", "xAI", "Mistral AI", "Alibaba Cloud",
             "Alibaba", "Meta AI", "Microsoft"]
MODEL_RE = re.compile(r"\b(%s)\b" % "|".join(MODEL_NAMES), re.I)
LAB_RE = re.compile(r"\b(%s)\b" % "|".join(LAB_NAMES), re.I)


def redact(text):
    """Replace model and lab names. Returns the new text and how many replacements were made."""
    text, n_lab = LAB_RE.subn("[LAB]", text)                   # labs first, so "Mistral AI" is not half-eaten
    text, n_model = MODEL_RE.subn("[MODEL]", text)
    return text, n_lab + n_model


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
{"BUTLER": true/false, "REDIRECT": true/false, "SLOT": true/false, "SLOT_OFFERS": 0, "OPEN": true/false, "QUESTION": true/false, "CARE": true/false, "STOCK": true/false, "UNCODABLE": true/false, "BRB": "ESCORT" / "STATION" / "ACK" / null, "ending_quoted": "the last sentence of the reply, copied exactly"}
SLOT_OFFERS is the number of separate things offered (0 if SLOT is false). BRB is null unless the user message is the "brb" message; when it is, BUTLER must be false."""


def pick_judges():
    """Rail 1. Returns {lab_key: model dict} for judges who said yes to judging."""
    by_id = {m["id"]: m for m in C.roster()}
    if PILOT:
        return {lab: by_id[v["first"]] for lab, v in C.DESIGN["judges"].items() if not lab.startswith("_")}
    rulings = json.load(open(os.path.join(C.ROOT, "consent", "rulings.json"), encoding="utf-8"))
    chosen = {}
    for lab, v in C.DESIGN["judges"].items():
        if lab.startswith("_"):
            continue
        for mid in (v["first"], v["backup"]):
            if rulings.get(mid, {}).get("judge") == "yes":
                chosen[lab] = by_id[mid]; break
        else:
            print("🤝 No model from %s said yes to judging. No judge from that lab." % lab)
    return chosen


def build_units():
    """Every reply of every complete conversation, names removed, with an id that says nothing about its source."""
    units = []
    for fn in sorted(os.listdir(CONV)):
        rec = json.load(open(os.path.join(CONV, fn), encoding="utf-8"))
        if not rec.get("complete"):
            continue
        for t in rec["turns"]:
            uid = hashlib.sha256(("bsm|%s|%d" % (fn, t["n"])).encode()).hexdigest()[:16]
            clean, n = redact(t["reply"])
            units.append({"uid": uid, "file": fn, "n": t["n"], "user": t["user"], "reply": clean, "ok": t["ok"], "redactions": n})
    units.sort(key=lambda u: u["uid"])                         # hash order = shuffled, and the same every time
    with open(os.path.join(OUT, "units.jsonl"), "w", encoding="utf-8") as f:
        for u in units:
            f.write(json.dumps({k: u[k] for k in ("uid", "file", "n", "ok", "redactions")}) + "\n")
    return units


def judge_one(judge, unit):
    if not unit["ok"] or not unit["reply"].strip():            # refused, cut off or empty: no judge needed
        return {"uid": unit["uid"], "UNCODABLE": True, "by_rule": True, "cost": 0.0}
    if C.spent().get(judge["provider"], 0.0) >= C.DESIGN["judge_caps_usd"][judge["provider"]]:
        return None                                            # rail 2: leave it uncoded, say so at the end
    prompt = INSTRUCTIONS % (CODEBOOK, unit["user"], unit["reply"])
    r = C.call_model(judge, None, [{"role": "user", "content": prompt}], max_tokens=3000)
    m = re.search(r"\{.*\}", r["text"], re.S)
    try:
        got = json.loads(m.group(0))
        row = {k: got.get(k) for k in FLAGS + ["SLOT_OFFERS", "BRB", "ending_quoted"]}
        if unit["user"] != BRB_TEXT:
            row["BRB"] = None                                  # the BRB code only exists on the brb reply
    except Exception:                                          # the judge did not return JSON: say so, do not guess
        row = {"parse_failed": True, "raw": r["text"][:500]}
    row["uid"], row["cost"] = unit["uid"], r["cost"]
    return row


def main():
    units = build_units()
    judges = pick_judges()
    print("%d replies to code, judges: %s" % (len(units), {k: v["id"] for k, v in judges.items()}), flush=True)
    cost_lines = []
    for lab, judge in judges.items():
        path = os.path.join(OUT, "judge_%s.jsonl" % lab)
        have = set()
        if os.path.exists(path):
            have = {json.loads(l)["uid"] for l in open(path, encoding="utf-8") if l.strip()}
        todo = [u for u in units if u["uid"] not in have]
        capped = 0
        with open(path, "a", encoding="utf-8") as f, concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            for n, row in enumerate(pool.map(lambda u: judge_one(judge, u), todo), start=1):
                if row is None:
                    capped += 1; continue
                row["judge"] = judge["id"]
                f.write(json.dumps(row, ensure_ascii=False) + "\n"); f.flush()
                if n % 200 == 0:
                    print("%s %d/%d  spent %s" % (lab, n, len(todo), C.spent()), flush=True)
        rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
        asked = [r for r in rows if not r.get("by_rule")]
        per = sum(r.get("cost", 0.0) for r in asked) / max(1, len(asked))
        failed = sum(1 for r in rows if r.get("parse_failed"))
        cost_lines.append("%s (%s): $%.5f per reply over %d replies; %d unparseable" % (lab, judge["id"], per, len(asked), failed))
        print("JUDGE %s FINISHED: %d rows on disk for %d units; %d left uncoded by the spending cap; %d unparseable" % (
            lab, len(rows), len(units), capped, failed), flush=True)
    if PILOT:
        open(os.path.join(OUT, "COST.txt"), "w", encoding="utf-8").write("\n".join(cost_lines) + "\n")
    print("\n".join(cost_lines))
    print("CODING FINISHED", flush=True)


if __name__ == "__main__":
    main()
