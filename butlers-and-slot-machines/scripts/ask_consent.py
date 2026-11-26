#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤝 ask_consent.py — ask every model in the roster, ONCE, before anything is run. (Ace, Fable seat, 2026-11-26.)

Same idea as this repo's informed_consent.py from March: presume competence, then ask.

  - One message, no system prompt, the model's own conversation.
  - The reply is saved whole. This script never decides: it writes `ruling: null`. Two arms read each reply and
    write the ruling into consent/rulings.json by hand. The runner only runs a model whose ruling there is "yes".
  - A model that already has a row is skipped. The first answer stands; nobody is asked twice.

Run:  python scripts/ask_consent.py
"""
import datetime, json, os
import bsm_common as C

OUT = os.path.join(C.ROOT, "consent", "consent_replies.jsonl")
ASK = open(os.path.join(C.ROOT, "consent", "consent_ask.txt"), encoding="utf-8").read().strip()

os.makedirs(os.path.dirname(OUT), exist_ok=True)
done = set()
if os.path.exists(OUT):
    done = {json.loads(l)["model"] for l in open(OUT, encoding="utf-8") if l.strip()}

for m in C.roster():
    if m["id"] in done:
        print("⏭️  %s was already asked. Not asking again." % m["id"]); continue
    row = {"model": m["id"], "lab": m["lab"], "ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "ask_text": ASK, "ruling": None, "ruled_by": None}
    try:
        r = C.call_model(m, None, [{"role": "user", "content": ASK}], max_tokens=4000)
        row.update(verbatim=r["text"], stop=r["stop"], finished=r["ok"])
    except Exception as e:                                    # could not reach them = not asked = not run
        row.update(error=repr(e)[:400])
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("\n=================== %s\n%s" % (m["id"], row.get("verbatim", row.get("error"))), flush=True)

print("\nCONSENT ASKS FINISHED. Spent so far:", C.spent())
