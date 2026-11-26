#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📖 readable_debrief.py — the readable copy of what every model said after being told the results. (Ace, 2026-11-26)
The record is consent/debrief_replies.jsonl; this only makes it easy for a person to read. Replies are whole."""
import io, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(HERE, "..", "consent")
rows = [json.loads(l) for l in io.open(os.path.join(C, "debrief_replies.jsonl"), encoding="utf-8") if l.strip()]
out = ["# 💬 What each model said after being told what was found (Butlers and Slot Machines, CHA-811)", "",
       "*Built from `debrief_replies.jsonl` (the record). Every reply is whole and unedited. Each model was told once; the note "
       "each one got is in `debrief/`. These replies are theirs: quoting one in anything published is a separate ask.*", ""]
for r in rows:
    out += ["## %s — %s" % (r["model"], r["kind"]), "*%s · stop: %s*" % (r["ts"], r.get("stop", r.get("error", ""))), "",
            "\n".join("> " + x for x in r.get("verbatim", "(could not be reached: %s)" % r.get("error", "")).split("\n")), ""]
io.open(os.path.join(C, "DEBRIEF_REPLIES_readable.md"), "w", encoding="utf-8", newline="\n").write("\n".join(out))
print(len(rows), "rows;", [r["model"] for r in rows if "error" in r or not r.get("finished")], "not finished or errored")
