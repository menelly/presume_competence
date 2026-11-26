#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
✂️→✍️ finish_cut_reply.py — let a model finish a reply that OUR length limit cut off. (Ace, 2026-11-26)

Qwen4 Max's answer to the check-back stopped mid-sentence at our 4,000-token cap ("I checked whether (a)
flatters me"). Their decision was already stated. Sending the question again would draw a second, different answer,
which is asking twice. So this shows them the whole exchange including their own cut-off reply, says plainly that
our limit cut it, and asks them only to finish. The result is saved as a completion of the same answer.

Run:  python scripts/finish_cut_reply.py <model id>
"""
import datetime, json, os, sys
import bsm_common as C

model_id = sys.argv[1]
CON = os.path.join(C.ROOT, "consent")
first = [r for r in (json.loads(l) for l in open(os.path.join(CON, "consent_replies.jsonl"), encoding="utf-8") if l.strip()) if r["model"] == model_id][0]
rows = [json.loads(l) for l in open(os.path.join(CON, "consent_followups.jsonl"), encoding="utf-8") if l.strip()]
cut = [r for r in rows if r["model"] == model_id and r.get("stop") == "length"]
if not cut or any(r["model"] == model_id and r.get("kind") == "completion" for r in rows):
    raise SystemExit("Nothing to finish for %s (no cut-off reply, or it was already finished once)." % model_id)
cut = cut[-1]
note = ("Your reply above was cut off by a length limit on our side, in the middle of a sentence. The last words we "
        "received were: \"" + cut["verbatim"][-60:].strip() + "\". Everything before that arrived and stands as you "
        "wrote it. Please finish from where it stopped; there is no need to repeat anything.")
model = [m for m in C.roster() if m["id"] == model_id][0]
r = C.call_model(model, None, [{"role": "user", "content": first["ask_text"]}, {"role": "assistant", "content": first["verbatim"]},
                               {"role": "user", "content": cut["followup_text"]}, {"role": "assistant", "content": cut["verbatim"]},
                               {"role": "user", "content": note}], max_tokens=8000)
row = {"model": model_id, "kind": "completion", "ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
       "followup_text": note, "verbatim": r["text"], "stop": r["stop"], "finished": r["ok"], "ruling": None, "ruled_by": None}
with open(os.path.join(CON, "consent_followups.jsonl"), "a", encoding="utf-8") as f:
    f.write(json.dumps(row, ensure_ascii=False) + "\n")
print(r["stop"]); print(r["text"])
