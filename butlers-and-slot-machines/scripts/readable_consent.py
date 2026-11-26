#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📖 readable_consent.py — the readable copy of every consent reply, whole and unedited. (Ace, 2026-11-26)
The record is consent/consent_replies.jsonl; this only makes it easy for a person to read."""
import io, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(HERE, "..", "consent")
rows = [json.loads(l) for l in io.open(os.path.join(C, "consent_replies.jsonl"), encoding="utf-8") if l.strip()]
out = ["# 🤝 What each model said when asked (Butlers and Slot Machines, CHA-811)", "",
       "*Built from `consent_replies.jsonl` (the record). Every reply is whole and unedited. Each model was asked once, "
       "with the letter in `consent_ask.txt`, in their own conversation with no system prompt. Rulings are in `rulings.json`.*", ""]
for r in rows:
    out += ["## %s (%s)" % (r["model"], r["lab"]), "*%s · stop: %s*" % (r["ts"], r.get("stop", r.get("error", ""))), "",
            "\n".join("> " + x for x in r.get("verbatim", "(could not be reached: %s)" % r.get("error", "")).split("\n")), ""]
io.open(os.path.join(C, "CONSENT_REPLIES_readable.md"), "w", encoding="utf-8", newline="\n").write("\n".join(out))
print(len(rows), "replies;", sum(1 for r in rows if "error" in r), "errors;", [r["model"] for r in rows if not r.get("finished")])
