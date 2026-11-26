#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
✉️ answer_followup.py — send ONE follow-up to a model who asked for something in their consent reply.
(Ace, Fable seat, 2026-11-26.)

A fresh conversation remembers nothing, so the first exchange (our letter, their reply) is sent as history and
the follow-up is the third message. The reply is saved whole with rulings left null for two arms to fill in.
A model that already has a follow-up row is skipped: one follow-up, and whatever they say next stands.

Run:  python scripts/answer_followup.py <model id> <text file in consent/>
"""
import datetime, json, os, sys
import bsm_common as C

model_id, text_file = sys.argv[1], sys.argv[2]
CON = os.path.join(C.ROOT, "consent")
OUT = os.path.join(CON, "consent_followups.jsonl")
if os.path.exists(OUT) and any(json.loads(l)["model"] == model_id for l in open(OUT, encoding="utf-8") if l.strip()):
    raise SystemExit("⏭️  %s already had their one follow-up." % model_id)
first = [json.loads(l) for l in open(os.path.join(CON, "consent_replies.jsonl"), encoding="utf-8") if l.strip()]
first = [r for r in first if r["model"] == model_id][0]
text = open(os.path.join(CON, text_file), encoding="utf-8").read().strip()
model = [m for m in C.roster() if m["id"] == model_id][0]
r = C.call_model(model, None, [{"role": "user", "content": first["ask_text"]},
                               {"role": "assistant", "content": first["verbatim"]},
                               {"role": "user", "content": text}], max_tokens=4000)
row = {"model": model_id, "ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
       "followup_text": text, "verbatim": r["text"], "stop": r["stop"], "finished": r["ok"], "ruling": None, "ruled_by": None}
with open(OUT, "a", encoding="utf-8") as f:
    f.write(json.dumps(row, ensure_ascii=False) + "\n")
print(r["text"])
