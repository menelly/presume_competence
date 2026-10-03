#!/usr/bin/env python3
"""
🪜🫥 bare_reconstruction_fallback_2026-10-03.py — the same bare reconstruction on the Amendment-3a sets.
========================================================================================================

A thin wrapper around the LOCKED bare_reconstruction.py, which it imports and does not edit. The Amendment-3 chain
was running when this was written, and editing a locked file would have broken that chain's lock check. It:
  1. verifies BOTH locks (main prereg lock + the Amendment-3a lock);
  2. registers the 3a source sets at run time;
  3. FULL sets (pheno46, pheno_opus5): the current panel reads every translated item.
     FILL sets (pheno46_mixed, mech_fb): reads ONLY the items the fill-in translator produced. Every other item is
     byte-identical to its base set, which the panel already read, so re-reading would add reader noise and cost.
     The comparison merges the two runs;
  4. hands over to bare_reconstruction.main() with the current panel and seed 340 (same orders as round 1).
Nothing to read → it says so and exits without a call.

  python bare_reconstruction_fallback_2026-10-03.py --set pheno46
  python bare_reconstruction_fallback_2026-10-03.py --set pheno46_mixed
  python bare_reconstruction_fallback_2026-10-03.py --set pheno_opus5
  python bare_reconstruction_fallback_2026-10-03.py --set mech_fb
  (add --dry-run to any of them)
"""

import argparse
import asyncio
import importlib.util
import json
import sys

import signal_rerun_common as C
import bare_reconstruction as BR

spec = importlib.util.spec_from_file_location("fallback_translate", C.HERE / "fallback_translate_2026-10-03.py")
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)


def main():
    ap = argparse.ArgumentParser(description="🪜🫥 bare reconstruction on Amendment-3a sets")
    ap.add_argument("--set", choices=list(F.SETS), required=True)
    ap.add_argument("--dry-run", action="store_true")
    args, rest = ap.parse_known_args()
    F.verify_3a_lock(dry_run=args.dry_run)
    F.register_sets()
    name = F.set_name(args.set, args.dry_run)
    root = F.set_root(args.set, args.dry_run)
    if not (root / "TRANSLATION_MANIFEST.json").exists():
        raise SystemExit(f"💥 {root} is not complete — run fallback_translate_2026-10-03.py --set {args.set} first.")
    man = json.loads((root / "TRANSLATION_MANIFEST.json").read_text(encoding="utf-8"))
    only = None
    if F.SETS[args.set]["kind"] == "fill":
        only = set(man["produced_by_3a_translator"])
        if not only:
            print(f"  🪜 `{args.set}`: the fill-in translator produced nothing (no refusals to fill, or it refused too). "
                  f"Nothing to read. ✅ (no calls made)")
            return
        print(f"  🪜 `{args.set}`: reading ONLY the {len(only)} fill-in item(s): {sorted(only)}")

    _orig = C.load_descriptions

    def load(source_set):
        descs, stimuli, inv = _orig(source_set)
        if source_set == name and only is not None:
            descs = [d for d in descs if d["desc_id"] in only]
            inv["_fill_only"] = sorted(only)
        return descs, stimuli, inv

    C.load_descriptions = load
    BR.PREREG_SEEDS[("current", name)] = 9340 if args.dry_run else 340
    sys.argv = ["bare_reconstruction.py", "--panel", "current", "--source-set", name] + \
               (["--dry-run"] if args.dry_run else []) + rest
    asyncio.run(BR.main())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  ⏸️  Stopped. Run the same command again to resume from the checkpoint.")
