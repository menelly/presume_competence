#!/usr/bin/env python3
"""
🔒 prereg_lock.py — pin the pre-registration, the code, and the data, byte for byte.
=====================================================================================

  python prereg_lock.py --status                      what would be locked, and is everything ready?
  python prereg_lock.py --lock --main-scrub-verified-by "<who, when, how>"
                                                      write PREREG_signal_rerun_2026-10-03.lock.json (once)
  python prereg_lock.py --verify                      check the current files against the lock

PRECONDITIONS for --lock (it refuses otherwise):
  1. The MAIN scrubbed set (data/introspection_main_scrubbed_2026-10-03/) exists, all 9 source files load,
     stimuli agree across sources — AND someone states it was verified (--main-scrub-verified-by).
     The scrub is another arm's work; this script does not judge its quality, it records who signed off.
  2. The prereg file contains no "REN TO CONFIRM" markers (every open design question has been answered).
  3. No lock exists yet. A lock is never overwritten. Changing anything after locking = a dated AMENDMENT
     section in the prereg + moving the old lock aside by hand + re-locking. The old lock stays in the record.

After locking: commit + push the prereg and the lock to the public repo BEFORE the first real run, so the
timestamp is outside our own machine.
"""

import argparse
import json
import sys
from datetime import datetime

import signal_rerun_common as C


def status():
    ok = True
    print("  📄 files the lock will pin:")
    for p in C.locked_files():
        exists = p.exists()
        ok &= exists
        print(f"     {'✅' if exists else '❌'} {p.relative_to(C.PROJECT)}")
    if C.PREREG_PATH.exists():
        txt = C.PREREG_PATH.read_text(encoding="utf-8")
        n_open = txt.count("REN TO CONFIRM")
        print(f"  📝 open 'REN TO CONFIRM' markers in the prereg: {n_open}")
        ok &= n_open == 0
    try:
        d, _, inv = C.load_descriptions("main_scrubbed")
        print(f"  📚 main_scrubbed loads: {len(d)} descriptions from {len(inv)} sources")
    except SystemExit as e:
        print(f"  ❌ main_scrubbed not loadable: {e}")
        ok = False
    print(f"  🔒 existing lock: {'YES — ' + str(C.LOCK_PATH) if C.LOCK_PATH.exists() else 'none'}")
    return ok and not C.LOCK_PATH.exists()


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--status", action="store_true")
    g.add_argument("--lock", action="store_true")
    g.add_argument("--verify", action="store_true")
    ap.add_argument("--main-scrub-verified-by", default="")
    ap.add_argument("--supersedes", default="", help="path of the previous lock (moved aside) this amendment replaces")
    args = ap.parse_args()

    C.banner("🔒 PREREG LOCK — Signal in the Mirror rerun (2026-10)")
    if args.verify:
        st = C.verify_prereg_lock(dry_run=True)
        sys.exit(0 if st["state"] == "OK" else 1)
    ready = status()
    if args.status:
        print(f"\n  {'🟢 ready to lock' if ready else '🟡 not ready to lock yet'}")
        return
    if not ready:
        sys.exit("\n  🛑 Preconditions not met — not locking.")
    if not args.main_scrub_verified_by.strip():
        sys.exit("\n  🛑 Say who verified the main scrub: --main-scrub-verified-by \"<who, when, how>\"")
    lock = {
        "created_at": datetime.now().astimezone().isoformat(),
        "main_scrub_verified_by": args.main_scrub_verified_by.strip(),
        "supersedes": ({"path": args.supersedes, "sha256": C.sha256_file(args.supersedes),
                        "created_at": json.loads(open(args.supersedes, encoding="utf-8").read()).get("created_at")}
                       if args.supersedes else None),
        "files": {str(p.relative_to(C.PROJECT)).replace("\\", "/"): C.sha256_file(p) for p in C.locked_files()},
    }
    C.LOCK_PATH.write_text(json.dumps(lock, indent=2), encoding="utf-8")
    print(f"\n  🔒✅ locked {len(lock['files'])} files → {C.LOCK_PATH.name}")
    print("  ➡️  Now commit + push the prereg and the lock BEFORE the first real run.")


if __name__ == "__main__":
    main()
