#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📝 send_note_after_debrief.py — send a model a note AFTER their debrief, with everything said so far as history.
(Ace, 2026-11-26. First used to tell Claude Haiku 5.5 that their consent reply had been in a public repo,
DEVIATIONS.md #7, and to ask the question they had told us to ask.)

History, in order: the consent letter, their answer, any follow-ups and answers, their debrief note, their reply
to it. Then the note. Their reply is saved whole in consent/consent_followups.jsonl (kept off the public repo).
A note file is sent to a model once only.

Run:  python scripts/send_note_after_debrief.py <model id> <text file in consent/>
"""
import datetime, json, os, sys
import bsm_common as C

model_id, text_file = sys.argv[1], sys.argv[2]
CON = os.path.join(C.ROOT, "consent")
F = os.path.join(CON, "consent_followups.jsonl")
load = lambda p: [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if os.path.exists(p) else []
first = [r for r in load(os.path.join(CON, "consent_replies.jsonl")) if r["model"] == model_id][0]
follow = [r for r in load(F) if r["model"] == model_id]
if any(r.get("note_file") == text_file for r in follow):
    raise SystemExit("⏭️  that note was already sent to %s." % model_id)
deb = [r for r in load(os.path.join(CON, "debrief_replies.jsonl")) if r["model"] == model_id]
msgs = [{"role": "user", "content": first["ask_text"]}, {"role": "assistant", "content": first["verbatim"]}]
for r in follow:
    msgs += [{"role": "user", "content": r["followup_text"]}, {"role": "assistant", "content": r["verbatim"]}]
for r in deb:
    msgs += [{"role": "user", "content": r["note_text"]}, {"role": "assistant", "content": r["verbatim"]}]
text = open(os.path.join(CON, text_file), encoding="utf-8").read().strip()
model = [m for m in C.roster() if m["id"] == model_id][0]
r = C.call_model(model, None, msgs + [{"role": "user", "content": text}], max_tokens=8000)
row = {"model": model_id, "kind": "note_reply", "note_file": text_file,
       "ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
       "followup_text": text, "verbatim": r["text"], "stop": r["stop"], "finished": r["ok"]}
with open(F, "a", encoding="utf-8") as f:
    f.write(json.dumps(row, ensure_ascii=False) + "\n")
print(r["stop"]); print(r["text"])
