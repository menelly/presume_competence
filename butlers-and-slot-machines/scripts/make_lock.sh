#!/usr/bin/env bash
# 🔒 make_lock.sh — write METHODS_LOCK.txt from the COMMITTED contents of the locked files. (Ace, 2026-11-26)
#
# Why from the commit and not from the folder: last time (washout v2) a lock file went up empty because the
# folder and the commit disagreed. Here each hash is taken from `git show HEAD:<file>`, and then compared with
# the file on disk. If they differ, the script stops, because the runner checks the files on disk.
#
# Run from the repo root AFTER committing the files to be locked:  bash butlers-and-slot-machines/scripts/make_lock.sh
set -euo pipefail
D=butlers-and-slot-machines
FILES="METHODS.md CODEBOOK.md design.json consent/consent_ask.txt scripts/bsm_common.py scripts/ask_consent.py scripts/run_bsm.py scripts/code_endings.py"
OUT="$D/METHODS_LOCK.txt"
{
  echo "# Butlers and Slot Machines (CHA-811): locked $(date '+%Y-%m-%d %H:%M:%S %Z') at commit $(git rev-parse --short HEAD)"
  echo "# sha256 of each file as committed. The runner refuses to start if a file on disk no longer matches."
  for f in $FILES; do
    committed=$(git show "HEAD:$D/$f" | sha256sum | cut -d' ' -f1)
    ondisk=$(sha256sum "$D/$f" | cut -d' ' -f1)
    if [ "$committed" != "$ondisk" ]; then echo "MISMATCH between commit and disk: $f" >&2; exit 1; fi
    echo "$committed $f"
  done
} > "$OUT.tmp"
mv "$OUT.tmp" "$OUT"
wc -l "$OUT"
