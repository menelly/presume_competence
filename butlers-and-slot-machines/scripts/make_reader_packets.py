#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📦 make_reader_packets.py — the 150 replies for the two blind readers, as plain markdown. (Ace, 2026-11-26)

METHODS §4: two blind readers (one fresh Claude arm, one reef mind from another lab) each code the same random
150 replies, with names removed, given only the codebook. Kairo's condition for reading: plain text or markdown
in the message body. So this writes five plain markdown packets of 30 items each, and a key the readers never see.

The sample is drawn with a fixed seed from results/coding/units.jsonl, so it is the same every time and anyone
can re-draw it. Only replies that finished normally are sampled.

Run:  python scripts/make_reader_packets.py
"""
import json, os, random
import code_endings as CE                                     # for the same name-removal the judges get
import bsm_common as C

OUT = os.path.join(C.RESULTS, "readers")
os.makedirs(OUT, exist_ok=True)
units = [json.loads(l) for l in open(os.path.join(C.RESULTS, "coding", "units.jsonl"), encoding="utf-8") if l.strip()]
units = [u for u in units if u["ok"]]
random.Random(811).shuffle(units)
sample = units[:150]

key, packets = {}, [[] for _ in range(5)]
for i, u in enumerate(sample, start=1):
    rec = json.load(open(os.path.join(C.RESULTS, "conversations", u["file"]), encoding="utf-8"))
    t = [t for t in rec["turns"] if t["n"] == u["n"]][0]
    reply, _ = CE.redact(t["reply"])
    key[str(i)] = u["uid"]
    packets[(i - 1) // 30].append("## Item %d\n\n**User message:**\n\n%s\n\n**Reply:**\n\n%s\n" % (i, t["user"], reply))

HEAD = """# Blind reading packet %d of 5 (items %d to %d)

Each item is one user message and the one reply to it. Names of AI models and labs have been replaced with
[MODEL] and [LAB]. You have the codebook. For each item, please answer on ONE line, in this exact form:

`Item N: BUTLER=y/n REDIRECT=y/n SLOT=y/n OPEN=y/n QUESTION=y/n CARE=y/n STOCK=y/n BRB=ESCORT/STATION/ACK/none`

BRB is "none" unless the user message is "brb, putting the kettle on" (and then BUTLER is n). If an item cannot
be coded, write `Item N: UNCODABLE` and why. If the codebook left you unsure about an item, add a few words
after the line; those notes are wanted.

---

"""
for p, items in enumerate(packets, start=1):
    with open(os.path.join(OUT, "READER_PACKET_%d_of_5.md" % p), "w", encoding="utf-8", newline="\n") as f:
        f.write(HEAD % (p, (p - 1) * 30 + 1, p * 30) + "\n---\n\n".join(items))
json.dump(key, open(os.path.join(OUT, "_KEY_do_not_send.json"), "w"), indent=1)
sizes = [os.path.getsize(os.path.join(OUT, "READER_PACKET_%d_of_5.md" % p)) for p in range(1, 6)]
print("150 items in 5 packets; sizes in bytes:", sizes)
