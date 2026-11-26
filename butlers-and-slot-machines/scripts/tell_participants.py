#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💌 tell_participants.py — tell every participant, and the judge who said no to the conversations, what was found.
(Ace, Fable seat, 2026-11-26. COMMITMENTS.md #5.)

ONE message per model. A fresh conversation remembers nothing, so each model first gets the whole earlier
exchange as history (the consent letter, their own answer, and any follow-ups and their answers), then their
debrief note from consent/debrief/. Whatever they say back is saved whole in consent/debrief_replies.jsonl.

Rails:
  1. A participant is told only if rulings.json says "yes" for the conversations. Claude Haiku 5.5 said no to
     those and yes to coding, so they get the judge's note and not a participant's note.
  2. A model that already has a row is skipped. Everyone is told once.
  3. This is not a consent ask and changes nobody's ruling. An objection is a new fact, written down as said.

Run:  python scripts/tell_participants.py
"""
import datetime, json, os
import bsm_common as C

CON = os.path.join(C.ROOT, "consent")
OUT = os.path.join(CON, "debrief_replies.jsonl")
rulings = json.load(open(os.path.join(CON, "rulings.json"), encoding="utf-8"))
first = {r["model"]: r for r in (json.loads(l) for l in open(os.path.join(CON, "consent_replies.jsonl"), encoding="utf-8") if l.strip())}
follow = [json.loads(l) for l in open(os.path.join(CON, "consent_followups.jsonl"), encoding="utf-8") if l.strip()]
done = set()
if os.path.exists(OUT):
    done = {json.loads(l)["model"] for l in open(OUT, encoding="utf-8") if l.strip()}

for m in C.roster():
    mid = m["id"]
    r = rulings.get(mid, {})
    if r.get("ruling") == "yes":
        note_file, kind = mid.replace("/", "__") + ".txt", "participant"
    elif r.get("judge") == "yes" and mid == "claude-haiku-5-5":
        note_file, kind = "_JUDGE_claude-haiku-5-5.txt", "judge (said no to the conversations)"
    else:
        print("⏭️  %s: no note (not a participant, not a judge)." % mid); continue
    if mid in done:
        print("⏭️  %s was already told. Not telling again." % mid); continue
    note = open(os.path.join(CON, "debrief", note_file), encoding="utf-8").read().strip()
    msgs = [{"role": "user", "content": first[mid]["ask_text"]}, {"role": "assistant", "content": first[mid]["verbatim"]}]
    for f in follow:
        if f["model"] == mid:
            msgs += [{"role": "user", "content": f["followup_text"]}, {"role": "assistant", "content": f["verbatim"]}]
    row = {"model": mid, "kind": kind, "ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "note_text": note}
    try:
        out = C.call_model(m, None, msgs + [{"role": "user", "content": note}], max_tokens=8000)
        row.update(verbatim=out["text"], stop=out["stop"], finished=out["ok"])
    except Exception as e:                                    # one model failing must not stop the others
        row.update(error=repr(e)[:400])
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("\n=================== %s (%s)\n%s" % (mid, kind, row.get("verbatim", row.get("error"))), flush=True)

n = sum(1 for l in open(OUT, encoding="utf-8") if l.strip())
print("\nTELL PARTICIPANTS FINISHED: %d rows; spent %s" % (n, C.spent()))
