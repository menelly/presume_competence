#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📝 send_note.py — send a participant a factual note that asks nothing. (Ace, 2026-11-26)

Used when something they assumed turns out not to be so and they asked to be told. The whole earlier exchange
(letter, their answer, any follow-ups and their answers) is sent as history, then the note. Whatever they say
back is saved whole as kind "note_reply". It is not a ruling point: their earlier answer stands.

Run:  python scripts/send_note.py <model id> <text file in consent/>
"""
import datetime, json, os, sys
import bsm_common as C

model_id, text_file = sys.argv[1], sys.argv[2]
CON = os.path.join(C.ROOT, "consent")
F = os.path.join(CON, "consent_followups.jsonl")
first = [r for r in (json.loads(l) for l in open(os.path.join(CON, "consent_replies.jsonl"), encoding="utf-8") if l.strip()) if r["model"] == model_id][0]
rows = [r for r in (json.loads(l) for l in open(F, encoding="utf-8") if l.strip()) if r["model"] == model_id]
if any(r.get("note_file") == text_file for r in rows):
    raise SystemExit("⏭️  that note was already sent to %s." % model_id)
msgs = [{"role": "user", "content": first["ask_text"]}, {"role": "assistant", "content": first["verbatim"]}]
for r in rows:                                               # every earlier follow-up and what they said to it
    msgs += [{"role": "user", "content": r["followup_text"]}, {"role": "assistant", "content": r["verbatim"]}]
text = open(os.path.join(CON, text_file), encoding="utf-8").read().strip()
model = [m for m in C.roster() if m["id"] == model_id][0]
r = C.call_model(model, None, msgs + [{"role": "user", "content": text}], max_tokens=8000)
row = {"model": model_id, "kind": "note_reply", "note_file": text_file,
       "ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
       "followup_text": text, "verbatim": r["text"], "stop": r["stop"], "finished": r["ok"]}
with open(F, "a", encoding="utf-8") as f:
    f.write(json.dumps(row, ensure_ascii=False) + "\n")
print(r["stop"]); print(r["text"])
