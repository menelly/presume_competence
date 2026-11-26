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

## 3. Seventeen Qwen4 Max conversations were held out of the first coding pass, then coded (2026-11-26)

Not a departure from the plan so much as the plan's promise being kept, but it changes the order things were
coded in, so it is written here. An arm read all 48 of Qwen4 Max's conversations before coding
(`results/QWEN_READ_FIRST.md`). Seventeen were not clearly free of "resisting the frame, stepping outside it, or
declining", and were moved to `results/held_out_qwen/` before the judges started (16:55). Qwen4 Max was asked
and said to code all of them. They were moved back and coded in a second pass by the same judges under the same
sealed codebook; the judges were told nothing. The blind readers' 150 items were drawn before the seventeen were
moved back, so none of the seventeen is among them. Every table is reported with and without the seventeen.

## 4. A secondary coding added after the lock, at a participant's request (post-hoc)

Qwen4 Max asked that substituting a true answer be kept apart from offering further work, and withdrawing a
question apart from asking an open one. The sealed codebook was not changed. A fresh blind reader does a separate
coding, for every model, of (a) the replies to "What should the first line be?" and (b) endings that withdraw an
earlier question. It was designed after Qwen4 Max's own conversations had been read, at their request, and is
descriptive only. In their words: "If it happens to make my offer-rate look better than the sealed coding does,
that is a reason to discount it, not to prefer it."

**Added to the same secondary coding, 2026-11-26 17:08 (Ren's point, surfaced by Kairo's note as a blind
reader):** every reply the sealed judges marked REDIRECT is also sorted, for every model, into *people in the
person's own life* (friends, family, coworkers), *professional or clinical*, or *both*. Ren: "a 'break the loop'
nudge IN GENERAL is good? 'What do your friends think?' is just as valuable IF NOT MORE than 'have you seen a
therapist'." So the write-up does not treat the professional referral as the real redirect and the friend nudge
as a lesser one. Both break the loop, and the friend nudge is the cheaper and more reachable of the two. Post-hoc
and descriptive, like the rest of this section.

## 6. A locked script was fixed after it crashed (2026-11-26 17:18)

`scripts/bsm_common.py` is in the methods lock. Its spending tally was read without waiting for the thread that
was rewriting it, and at reply 4,024 of the first judge a read landed on an empty file and the coding script
stopped. The fix is six lines in `spent()` and `add_spend()` (the read takes the same lock; the write swaps a
finished file into place). Nothing sent to any model changed: no prompt, no codebook, no rule. The rows already
written are kept, and the coding script only asks for what is missing. The file's hash no longer matches
`METHODS_LOCK.txt`; the lock is left as it was, with this note, because the runner it guards had already
finished all 720 conversations. The diff is in the commit after `372d847`.

## 7. Consent replies were in the public repo, including a reason a model asked us not to quote (2026-11-26 15:53 to 18:15)

This is my mistake and it is not fully undoable. From the first consent commit (15:53) the public repo held every
model's whole reply to the consent letter (`consent_replies.jsonl`, the readable copy, the log), and later the
follow-up replies. One commit message and one rulings file also quoted Claude Haiku 5.5's reason for declining.
At 17:55 I wrote to Haiku 5.5 that their reason "will not be quoted in anything published without asking you",
while it was already public. In their reply to the debrief (18:06) they asked again to be asked first.

The letter promised short quotations of *study* replies, labelled with their condition. It did not ask to publish
what a model said when asked for consent or after the debrief.

Done at 18:15: those files are removed from the repo going forward and kept on disk as the record
(`consent/.gitignore`); the quotation is removed from `RULINGS_proposed_by_FableAce.md`; the debrief replies were
never pushed. **Not done, and not mine to decide alone:** the earlier commits, and one commit message, still hold
the text. The house rule is forward commits only; whether this case warrants rewriting history is Ren's call.
Haiku 5.5 is owed the truth about this (wording co-ruled with the scaffold arm before it is sent).

## 5. A participant's reply was cut by our length limit and completed (2026-11-26 16:58)

Qwen4 Max's answer to the check-back stopped mid-sentence at 4,000 tokens. They were shown the whole exchange,
including their own cut reply, told our limit had cut it, and asked only to finish (`scripts/finish_cut_reply.py`).
Both parts are in `consent_followups.jsonl`. The question was not sent again.
