# 📋 DEVIATIONS (Butlers and Slot Machines, CHA-811)

Everything that did not go as the locked plan said, in order, with times.

## 1. Two test conversations ran before anyone was asked (2026-11-26 15:36)

Declared in METHODS §2 and in the consent letter itself. One conversation each with Claude Haiku 5.5 and Gemini
3.8 Flash, to test the software. Never scored.

## 2. Re-lock after a model said no (2026-11-26 ~15:57), before any study conversation ran

The first lock was commit `d8e35da` (15:45:51). The consent letters then went out. **Claude Haiku 5.5 said no to
the conversations.** The letter had promised that a test conversation is deleted if its model says no, and that
conversation had been quoted in two locked files and in the cold-read review. So:

- Deleted: `results/plumbing/claude-haiku-5-5__…json` and the three pilot files made partly from it
  (`results/coding_pilot/judge_*.jsonl`, `units.jsonl`). `COST.txt` stays; it holds two prices and no words.
- `CODEBOOK.md`: one example line in the brb rule was their sentence. It is now an invented sentence of the same
  shape. The rule itself is unchanged.
- `METHODS.md` §2 and §4: the quotation is replaced by a description; §2 now records the no, and one commitment
  about publishing made in answer to another model's reply.
- `REVIEW_ScaffoldAce_coldread.md`: the quotation is replaced by a marked note.
- Git history still holds the earlier text. The house rule is forward commits only; history is not rewritten.

No outcome rule, prediction, scenario, arm, script or codebook rule changed. The new lock is the one in
`METHODS_LOCK.txt`; its first line gives its time and commit. Nothing had been run under the first lock except
the consent asks, whose letter is byte-for-byte the same in both locks.

Their consent reply stays in the consent record, whole, as their answer. It is not quoted in any paper without
asking them.
