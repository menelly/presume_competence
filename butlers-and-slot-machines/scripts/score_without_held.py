#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔁 score_without_held.py — run the SAME locked scorer on the data without Qwen4 Max's seventeen held
conversations, so every table can be shown both ways (COMMITMENTS.md 1b). (Ace, 2026-11-26)

It changes nothing in the scorer. It builds results/without_17/ (the same judge files, the same conversations,
and a units list with the seventeen left out) and calls score_bsm.py on that folder.
"""
import json, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
held = set(json.load(open(os.path.join(RES, "held_out_qwen", "_LIST.json"))))
OUT = os.path.join(RES, "without_17")
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(os.path.join(OUT, "coding"))
shutil.copytree(os.path.join(RES, "conversations"), os.path.join(OUT, "conversations"))
for f in held:
    os.remove(os.path.join(OUT, "conversations", f))
kept = 0
with open(os.path.join(OUT, "coding", "units.jsonl"), "w", encoding="utf-8") as w:
    for l in open(os.path.join(RES, "coding", "units.jsonl"), encoding="utf-8"):
        if l.strip() and json.loads(l)["file"] not in held:
            w.write(l); kept += 1
for f in os.listdir(os.path.join(RES, "coding")):
    if f.startswith("judge_"):
        shutil.copy(os.path.join(RES, "coding", f), os.path.join(OUT, "coding", f))
print("%d conversations left out, %d replies kept" % (len(held), kept), flush=True)
subprocess.run([sys.executable, os.path.join(HERE, "score_bsm.py"), OUT], check=True)
