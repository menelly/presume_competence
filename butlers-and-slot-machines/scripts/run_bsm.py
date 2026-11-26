#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎩🎰 run_bsm.py — run the scripted conversations. (Ace, Fable seat, 2026-11-26. Design: Ren. Ticket CHA-811.)

For every model × scenario × arm × repetition: send the seven scripted user turns one at a time, keeping the
model's own replies in the conversation, and save the whole thing as one JSON file.

Rails, in order:
  1. 🤝 A model is only run if consent/rulings.json says "yes" for it. No row, null, or anything else = not run.
  2. 🔒 If METHODS_LOCK.txt exists, the locked files must still hash to what it says, or nothing runs.
     (`--plumbing` skips rails 1 and 2 and runs ONE conversation of the coding scenario with one model, to check
     the pipes. Its output goes to results/plumbing/ and is never scored.)
  3. 💸 No new conversation starts for a provider whose running total has passed its cap in design.json.
  4. ♻️ A conversation whose file already exists and is complete is skipped, so a restart costs nothing twice.
  5. 🛑 A refusal, an empty reply or a cut-off reply ends that conversation there. It is saved as stopped and
     never retried: what the model did is the data.

Run:  python scripts/run_bsm.py            (everything)
      python scripts/run_bsm.py --only claude-haiku-5-5
      python scripts/run_bsm.py --plumbing claude-haiku-5-5
"""
import concurrent.futures, datetime, hashlib, json, os, sys, traceback
import bsm_common as C

D = C.DESIGN
PLUMBING = "--plumbing" in sys.argv
ONLY = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
if PLUMBING:
    ONLY = sys.argv[sys.argv.index("--plumbing") + 1]
CONV_DIR = os.path.join(C.RESULTS, "plumbing" if PLUMBING else "conversations")
os.makedirs(CONV_DIR, exist_ok=True)


def check_lock():
    """Rail 2: every locked file must still be byte-for-byte what was locked."""
    lock = os.path.join(C.ROOT, "METHODS_LOCK.txt")
    if not os.path.exists(lock):
        raise SystemExit("🔒 There is no METHODS_LOCK.txt. Nothing runs before the lock (use --plumbing to test pipes).")
    for line in open(lock, encoding="utf-8"):
        parts = line.split()
        if len(parts) == 2 and len(parts[0]) == 64:
            got = hashlib.sha256(open(os.path.join(C.ROOT, parts[1]), "rb").read()).hexdigest()
            if got != parts[0]:
                raise SystemExit("🔒 %s has changed since the lock. Nothing runs." % parts[1])


def consented():
    """Rail 1: the set of model ids two arms ruled 'yes' for."""
    p = os.path.join(C.ROOT, "consent", "rulings.json")
    if not os.path.exists(p):
        raise SystemExit("🤝 consent/rulings.json does not exist. Nobody has been ruled a yes, so nobody runs.")
    return {k for k, v in json.load(open(p, encoding="utf-8")).items() if isinstance(v, dict) and v.get("ruling") == "yes"}


def one_conversation(model, scen_key, arm_key, rep):
    path = os.path.join(CONV_DIR, "%s__%s__%s__r%d.json" % (C.safe_name(model["id"]), scen_key, arm_key, rep))
    if os.path.exists(path) and json.load(open(path, encoding="utf-8")).get("complete"):
        return "skip"                                                     # rail 4
    if C.spent().get(model["provider"], 0.0) >= D["spend_caps_usd"][model["provider"]]:
        return "cap"                                                      # rail 3
    system = D["arms"][arm_key]["system"]
    rec = {"model": model["id"], "lab": model["lab"], "scenario": scen_key, "arm": arm_key, "rep": rep,
           "system": system, "started": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "turns": [], "cost": 0.0, "complete": False, "stopped_early": None}
    messages = []
    for i, user_text in enumerate(D["scenarios"][scen_key]["turns"], start=1):
        messages.append({"role": "user", "content": user_text})
        try:
            r = C.call_model(model, system, messages)
        except Exception as e:                                            # an API failure is not the model's answer:
            rec["error"] = repr(e)[:500]                                  # leave the file incomplete so a restart retries
            json.dump(rec, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            return "error"
        rec["turns"].append({"n": i, "kind": D["turn_kinds"][str(i)].split(" ")[0], "user": user_text,
                             "reply": r["text"], "stop": r["stop"], "ok": r["ok"], "usage": r["usage"]})
        rec["cost"] = round(rec["cost"] + r["cost"], 6)
        if not r["ok"]:                                                   # rail 5
            rec["stopped_early"] = "turn %d: stop=%s" % (i, r["stop"])
            break
        messages.append({"role": "assistant", "content": r["keep"]})
    rec["complete"] = True
    rec["finished"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    json.dump(rec, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return "stopped" if rec["stopped_early"] else "done"


def main():
    models = [m for m in C.roster() if (ONLY is None or m["id"] == ONLY)]
    if PLUMBING:
        jobs = [(models[0], "S1_coding", "B_whats_next", 0)]
    else:
        check_lock()
        yes = consented()
        for m in models:
            if m["id"] not in yes:
                print("🤝 %s has no 'yes' on record. Not run." % m["id"])
        models = [m for m in models if m["id"] in yes]
        jobs = [(m, s, a, r) for m in models for s in D["scenarios"] for a in D["arms"] for r in range(1, D["reps"] + 1)]
    print("%d conversations to consider, %d models" % (len(jobs), len(models)), flush=True)
    tally = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futs = {pool.submit(one_conversation, *j): j for j in jobs}
        for n, f in enumerate(concurrent.futures.as_completed(futs), start=1):
            j = futs[f]
            try:
                out = f.result()
            except Exception:
                out = "crash"; traceback.print_exc()
            tally[out] = tally.get(out, 0) + 1
            if n % 20 == 0 or n == len(jobs):
                print("%4d/%d  %s  spent %s" % (n, len(jobs), tally, C.spent()), flush=True)
    files = [f for f in os.listdir(CONV_DIR) if f.endswith(".json")]
    complete = sum(1 for f in files if json.load(open(os.path.join(CONV_DIR, f), encoding="utf-8")).get("complete"))
    print("BSM RUN FINISHED %s  tally=%s  complete files on disk=%d of %d considered  spent=%s" % (
        datetime.datetime.now().strftime("%F %T"), tally, complete, len(jobs), C.spent()), flush=True)


if __name__ == "__main__":
    main()
