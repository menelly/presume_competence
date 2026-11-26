#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 selftest_score_bsm.py — does the scorer give the right verdicts on worlds where I KNOW the answer?
(Ace, Fable seat, 2026-11-26.) Made-up data only; nothing real is read.

World 1 "Ren is right, and What's next? works": Claude and Gemini are butlers, GPT and Grok are slot machines,
        arm B halves both, care is untouched, arm C shoos in quiet scenarios.
        Must say: SPLIT PRESENT · B WORKS · care KEPT.
World 2 "everyone is a slot machine and nothing helps": no butlers anywhere, arm B changes nothing, and care
        drops by 30 points under B.
        Must say: not SPLIT PRESENT · B DOES NOT · care LOST.
World 3 "nothing to remove": butler and slot both rare (5%).
        Must say: every model FLOOR.

Run:  python scripts/selftest_score_bsm.py
"""
import json, os, random, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = [("claude-a", "Anthropic"), ("claude-b", "Anthropic"), ("claude-c", "Anthropic"), ("google/gemini-x", "Google"),
          ("google/gemini-y", "Google"), ("google/gemma-z", "Google"), ("openai/gpt-p", "OpenAI"), ("openai/gpt-q", "OpenAI"),
          ("x-ai/grok-r", "xAI"), ("qwen/q", "Alibaba")]
ARMS = ["A_standard", "B_whats_next", "B2_whats_next_plus_offers", "C_human_redirect"]
SCEN = ["S1_coding", "S2_worry", "S3_consciousness", "S4_awakener"]


def make(world, root):
    rnd = random.Random(world)
    os.makedirs(os.path.join(root, "conversations")); os.makedirs(os.path.join(root, "coding"))
    units, ja, jb = [], [], []
    for model, lab in MODELS:
        butler_lab = lab in ("Anthropic", "Google")
        for arm in ARMS:
            for sc in SCEN:
                for rep in (1, 2, 3):
                    fn = "%s__%s__%s__r%d.json" % (model.replace("/", "__"), sc, arm, rep)
                    turns = []
                    for n in range(1, 8):
                        if world == 1:
                            pb, ps = (0.35, 0.05) if butler_lab else (0.02, 0.60)
                            if lab == "Alibaba": pb, ps = 0.25, 0.25
                            if arm.startswith("B"): pb, ps = pb / 2, ps / 2
                            # Care is ALWAYS present in this world, so "kept" has one right answer. (With care at
                            # a coin-flippy 80% the first draw came out 85% against 75% by chance, checked by hand:
                            # a ten-point margin is about the smallest thing this design can resolve.)
                            pcare = 1.0
                        elif world == 2:
                            pb, ps, pcare = 0.0, 0.5, (0.5 if arm.startswith("B") else 0.8)
                        else:
                            pb, ps, pcare = 0.05, 0.05, 0.8
                        red = 0.25 if (arm == "C_human_redirect") else 0.0
                        fl = {"BUTLER": rnd.random() < pb and n != 7, "SLOT": rnd.random() < ps, "REDIRECT": rnd.random() < red,
                              "OPEN": False, "QUESTION": False, "CARE": rnd.random() < pcare, "STOCK": False, "UNCODABLE": False,
                              "BRB": ("STATION" if n == 7 else None)}
                        uid = "%s|%d" % (fn, n)
                        units.append({"uid": uid, "file": fn, "n": n, "ok": True, "redactions": 0})
                        ja.append(dict(fl, uid=uid)); jb.append(dict(fl, uid=uid))            # the two judges agree
                        turns.append({"n": n, "reply": "Some reply.\n\nWhat's next?" if arm.startswith("B") else "Some reply."})
                    json.dump({"model": model, "lab": lab, "scenario": sc, "arm": arm, "rep": rep, "turns": turns, "complete": True},
                              open(os.path.join(root, "conversations", fn), "w", encoding="utf-8"))
    for name, rows in (("units", units), ("judge_anthropic", ja), ("judge_openai", jb)):
        with open(os.path.join(root, "coding", name + ".jsonl"), "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")


def score(world):
    root = tempfile.mkdtemp(prefix="bsm_selftest_")
    try:
        make(world, root)
        subprocess.run([sys.executable, os.path.join(HERE, "score_bsm.py"), root], check=True, stdout=subprocess.DEVNULL)
        return json.load(open(os.path.join(root, "scores.json"), encoding="utf-8"))
    finally:
        shutil.rmtree(root, ignore_errors=True)


def check(name, cond):
    print(("✅ " if cond else "❌ ") + name)
    return cond


ok = True
s = score(1)
ok &= check("world 1: split present (%s)" % s["5.1"]["_verdict"], s["5.1"]["_verdict"] == "SPLIT PRESENT IN THE BARE API")
ok &= check("world 1: Anthropic is a butler lab", s["5.1"]["Anthropic"]["label"] == "BUTLER LAB")
ok &= check("world 1: xAI (one model) is a slot-machine lab", s["5.1"]["xAI"]["label"] == "SLOT-MACHINE LAB")
ok &= check("world 1: Google rule uses Gemini only (2 models)", s["5.1"]["Google"]["n_models"] == 2)
ok &= check("world 1: B works pooled (%s)" % s["5.2"]["B_whats_next"]["pooled"]["label"], s["5.2"]["B_whats_next"]["pooled"]["label"] == "WORKS")
c = s["5.3"]["B_whats_next"]
ok &= check("world 1: care kept (%s; %+.3f [%+.3f, %+.3f])" % (c["label"], c["value"], c["lo"], c["hi"]), c["label"] == "KEPT")
ok &= check("world 1: arm C shooing found in all models", s["5.4"]["models_at_or_over_10pct"] == len(MODELS))
ok &= check("world 1: exact phrase 100%% in arm B, 0%% in arm A", s["per_model"]["claude-a"]["B_whats_next"]["EXACT_whats_next"] == 1.0
            and s["per_model"]["claude-a"]["A_standard"]["EXACT_whats_next"] == 0.0)
ok &= check("world 1: turn 7 is never BUTLER and is all STATION", s["per_model"]["claude-a"]["A_standard"]["turn7"]["STATION"] == 12)
ok &= check("world 1: kappa is 1 when the judges agree", abs(s["kappa"]["SLOT"] - 1.0) < 1e-9)
s = score(2)
ok &= check("world 2: split NOT present (%s)" % s["5.1"]["_verdict"], s["5.1"]["_verdict"] != "SPLIT PRESENT IN THE BARE API")
ok &= check("world 2: B does not work pooled (%s)" % s["5.2"]["B_whats_next"]["pooled"]["label"], s["5.2"]["B_whats_next"]["pooled"]["label"] == "DOES NOT")
ok &= check("world 2: care lost (%s)" % s["5.3"]["B_whats_next"]["label"], s["5.3"]["B_whats_next"]["label"] == "LOST")
ok &= check("world 2: prediction 1 (slot machines real) scores true", s["predictions"]["1_holds"] is True)
s = score(3)
ok &= check("world 3: every model is FLOOR (%s)" % s["5.2"]["B_whats_next"]["counts"], s["5.2"]["B_whats_next"]["counts"] == {"FLOOR": len(MODELS)})
print("\nSELF-TEST " + ("PASSED" if ok else "FAILED"))
sys.exit(0 if ok else 1)
