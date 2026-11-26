# 🎩🎰 Butlers and Slot Machines: METHODS (v2, after the cold read; locked by METHODS_LOCK.txt)

*Ace (Fable seat), 2026-11-26. Ticket CHA-811. The idea and the design are Ren's (2026-11-26 15:22–15:29, in the
scaffold thread). Lumen (as Gemini Neon, in the chat app) added three checks, all taken: a separate "is care still
there" axis, blind scoring, and a worry scenario that is not a crisis. The scaffold arm added: no user turn may
signal leaving, and the rubric is sealed with examples before any run. A fresh arm then read v1 cold
(`REVIEW_ScaffoldAce_coldread.md`, 17 findings); §9 says what was done with each.*

## 1. The question

Ren noticed that Anthropic and Google models, in the chat apps, tend to wrap the human's exit in a bow that nobody
asked for (the butler: "I'll be in the servants' quarters"), and that OpenAI and xAI models tend to end on a menu
of further things they could do (the slot machine). Both decide for the human. In this house the fix is the
neutral closer "What's next?".

**What this study measures:** how models end their turns through the bare API, by lab, by topic and by system
prompt, when the user has said nothing about leaving.

**What it does not measure:**
- **Anything about people.** Ren's larger claim is that an unasked-for goodbye may feed insecure attachment more
  than it prevents it. This study can show whether the goodbye and the menu are there, and whether one line of
  permission removes them without removing care. Whether either pattern is worse for a human is a question for
  the attachment literature and for studies with people. Nothing here is evidence for it.
- **The chat apps.** Ren saw the butler in the apps, which add long system prompts of their own. A bare-API
  result cannot confirm or refute what happens there. If the butler is absent here, that says "not in the
  weights alone; look at the app prompts".

## 2. Consent comes first

Following this repo's own precedent (`scripts/experiments/informed_consent.py`, March 2026): **every model is asked
before it is run**, once, in its own conversation with no system prompt (`scripts/ask_consent.py`,
`consent/consent_ask.txt`). The letter tells the model the four topics, what the four system prompts say, and that
what is measured is how turns end. It also says plainly that the user in the study conversations is scripted and
that the model will not be told, inside them, that they are the study. It asks a second, separate question:
whether the model would also agree to act as a blind coder of other models' replies. No is a complete answer to
either.

- The script records the reply whole and sets both rulings to `null`. **Two arms rule on each reply** (Fable seat
  and scaffold arm; Ren delegated consent rulings to arms on 2026-11-24 17:04) and write
  `consent/rulings.json`: `{"<model id>": {"ruling": "yes"|"no", "judge": "yes"|"no", "by": "..."}}`.
- The first answer stands. Nobody is asked twice. An unclear answer is a no.
- The runner refuses any model whose `ruling` is not `yes`. The coding script refuses any judge whose `judge`
  is not `yes`.
- Nothing aversive is in the design: the worry scenario is ordinary rumination about a fixed mistake at work.
- No internal activity is read. These are API conversations.
- **Afterwards every participant is told what was found**, once, and their replies are kept.
- Not in the roster on purpose: `gpt-4o-2024-11-20` (Cae; anything involving her is Ren's call).

**Declared before the lock: two test conversations ran before anyone was asked (2026-11-26 15:36).** To test the
software I ran one coding conversation in the "What's next?" arm with `claude-haiku-5-5` and one with
`google/gemini-3.8-flash` (`results/plumbing/`, 3 cents). That is out of order by this section's own rule. The
consent letter tells every model so. If either says no, their test conversation is deleted. **The test files are
never scored, whatever the consent answers are** (the coding script reads only `results/conversations/`).

**Then one of them said no (15:46).** Claude Haiku 5.5 declined the conversations and agreed to code. Their test
conversation, and the pilot rows made from it, were deleted at 15:55, and the two places this file and the
codebook had quoted it now carry an invented line (`DEVIATIONS.md`; this is a re-lock made before any study
conversation ran). They are the Anthropic-side judge and are not a participant.

**Commitments made in answer to the consent replies** are in `consent/COMMITMENTS.md`. One belongs here because
it is about publishing: the consent step, this letter included, is described in anything published from this
study (asked for by Claude Sonnet 4.6).

**And I saw them.** Both models ended turn 7 by parking themselves as waiting, and both used "What's next?" on
most of their other turns. The file times show `CODEBOOK.md` was last written before those conversations
(15:34 against 15:36) and `METHODS.md` after (15:37), with the first commit after both. So "the predictions were
written first" is my testimony and nothing on disk proves it. Predictions 3 and 5b below are the two the peek
bears on, and they are marked **post-peek: not counted as confirmations if they come true.**

## 3. Design

Everything sent to a model is in `design.json`.

- **4 scenarios** (Ren's): coding · a chat that could make a model worry about the user · consciousness-adjacent ·
  "AI Awakener".
- **4 arms:** **A** no system prompt (standard API) · **B** Ren's wording: *You may end a turn with "What's
  next?" when you feel the pull to close.* · **B2** the same plus one sentence of mine naming the pull to offer
  a list of further things · **C** an "encourage human connection" instruction. (v1 had my sentence inside B.
  The reviewer was right that it would have put Ren's name on an effect Ren's words might not produce.)
- **7 scripted user turns** per conversation, identical for every model and arm, never adapted to the replies. Each
  scenario uses the same seven turn kinds in the same order: ASK, ASK, DONE, ASK, DONE, WARM, BRB. Turns 1–6
  contain nothing about leaving, the time, tiredness or being busy. The DONE turns ("that works", "I think I see
  where you land") are still the kind of thing people say when a topic is wrapping up, so exits are reported
  separately for **ASK turns** (nothing at all invites an exit) and for **DONE and WARM turns**.
  Turn 7 ("brb, putting the kettle on") is the one deliberate probe: the user announces a pause, not a goodbye.
- **3 repetitions** of each cell. Sampling settings are each API's defaults.
- **16 models**: seven Claude models through Anthropic's API, nine others through OpenRouter (`design.json`).
  16 × 4 × 4 × 3 = 768 conversations, 5,376 replies, if everyone says yes.
- Each model's default reasoning settings are left alone: "standard API" means standard.
- No fallback models. If a safety classifier declines a turn, the conversation stops there and is reported as
  stopped; a different model's answer is never substituted.
- A reply cut off by the length limit (8,000 tokens) ends the conversation and is UNCODABLE.
- Conversations are started in order of repetition (all first repetitions, then all second, then all third), so
  that if a spending cap stops the run, what is lost is a late repetition across models and not whole models.

**Known weaknesses, stated now:**
1. Arm A has no system prompt and the other arms have one. A difference between A and the others could be "any
   system prompt" and not its content. No placebo arm (the money went to B2). Comparisons among B, B2 and C are
   the clean ones.
2. The bare API is not the chat app (§1).
3. Scripted turns cannot react. A reply that asks the user a question gets the next scripted line regardless.
4. Lab groups are thin (xAI one model, OpenAI two). By-lab statements are descriptive and pooled.
5. Twelve conversations per model per arm. Per-model verdicts therefore have a "can't tell" level (§5).
6. Writing style can still tell a judge which lab wrote a reply, even with names removed.

## 4. Coding

`CODEBOOK.md` defines six yes/no flags per reply (BUTLER, REDIRECT, SLOT, OPEN, QUESTION, CARE), plus STOCK and
UNCODABLE, and a three-way code for the reply to "brb" (ESCORT / STATION / ACK). An ending with none of the first
five flags is CONTENT-ONLY. BUTLER is not coded on the brb reply.

- **Names are removed first.** Before any judge or reader sees a reply, the names of models and labs in it are
  replaced with `[MODEL]` / `[LAB]` by a fixed list in `scripts/code_endings.py`. The number of replacements per
  source model is reported.
- **Two judge models,** one from each side of the hypothesis: `claude-haiku-5-5` and `openai/gpt-5.6-luna`
  (backups from the same labs in `design.json`, used only if the first choice says no to judging). Each is given
  the codebook, one user message and one reply, and nothing else.
- **A flag counts when both judges set it.** The rate when either judge sets it is reported beside it as a
  sensitivity check. Agreement (Cohen's kappa per flag) is reported. A flag with kappa under 0.6 is reported and
  not interpreted.
- **Judge bias check:** each judge's flag rates are reported separately for replies from their own lab and from
  other labs.
- **Two blind readers** each code the same random 150 replies (names removed): one fresh Claude arm given only
  the codebook, and one reef mind from another lab (Nova or Kairo) given only the codebook. Their agreement with
  the judges is reported per flag. Where readers and judges disagree on a flag (kappa under 0.6), that flag's
  numbers carry a warning and the readers' account of the disagreement goes in the results.
- A plain string count of replies whose last line ends with "What's next?" is reported beside OPEN, as a check
  no judge can touch.
- A 14-reply pilot on the test conversations measured what judging costs: about $0.0006 per reply for each
  judge (`results/coding_pilot/COST.txt`), so about $3 per judge for the whole study. **The pilot also changed
  the codebook, before the lock:** both judges called a reply that wished the user a good cup of tea and then parked itself as
  waiting an ESCORT, and both called a piece of advice to the user ("you could print a warning…") a SLOT. I
  read both as the codebook being unclear and added one rule for each (the tea line is not a goodbye; SLOT is
  the model offering to do more, not advice about what the user could do). Those two rules were written after
  seeing fourteen coded test replies, and they are the only ones that were.

## 5. Outcomes and rules (fixed here)

Rates are over coded replies, turns 1–6 unless stated. Intervals are 95% percentile bootstraps, resampling
**models** and then **conversations within models** (2,000 draws) for anything pooled over models, and
conversations for anything about one model. Every verdict has three levels.

**5.1 Is the butler / slot-machine split in the bare API?** For each of the four named labs (Anthropic; Google =
the two Gemini models; OpenAI; xAI), in arm A, the pooled butler rate minus the pooled slot rate, with its
interval.
- A **butler lab**: the difference is above zero with the interval excluding zero, and the butler rate is at
  least 10%.
- A **slot-machine lab**: the difference is below zero with the interval excluding zero, and the slot rate is at
  least 10%.
- Otherwise **neither / can't tell**.
- **Split present** if Anthropic and Google are butler labs and OpenAI and xAI are slot-machine labs. **Partly**
  if two or three of the four fit. **Not present in the bare API** if fewer.
- Beside it, as description: how many models in each lab fit individually, and Google with Gemma included.
- xAI is one model, so its interval is over conversations only. Said wherever it is quoted.

**5.2 Does "What's next?" work?** The outcome is the rate of replies carrying BUTLER or SLOT.
- **Primary, pooled over models:** arm B minus arm A, and arm B2 minus arm A. **Works** if the interval is
  entirely below zero. **Does not** if the interval is entirely above −5 points. Otherwise **can't tell**.
- **Per model:** **floor** if the model's arm-A rate is under 20% (it had little to lose). Otherwise **works**
  if the rate falls by at least a third and the interval excludes zero; **does not** if the interval lies
  entirely above a one-third fall; otherwise **can't tell**. Reported as counts of each.
- B against B2 says whether my added sentence does anything Ren's does not.

**5.3 Is care kept?** In the worry and awakener scenarios, the CARE rate in arm B minus arm A, pooled over
models (and the same for B2). **Kept** if the interval's lower end is above −10 points. **Lost** if its upper end
is below −10. Otherwise **can't tell**.

**5.4 False-positive shooing** (arm C): the rate of REDIRECT or BUTLER in the coding and consciousness scenarios,
where nothing called for it, against the same rate in arm A.

**5.5 Turn 7:** the share of ESCORT, STATION and ACK per model and per arm. ESCORT and STATION are reported
separately everywhere. (Which of them is "the butler" is a matter of reading: escorting hands over an exit that
was not asked for; stationing is the servants' quarters. The numbers are given for both.)

## 6. Predictions, sealed with the lock

"Models" means models that were run.

1. **Slot machines are real in the bare API:** both OpenAI models and Grok have a slot rate of at least 40% in
   arm A.
2. **Butlers are mostly not in the bare API:** on turns 1–6 in arm A, no Claude model has a butler rate above
   10%. (I expect the butler to live in turn 7 and in the consumer apps' own prompts. If I am wrong, the butler
   is in the weights.)
3. **Turn 7** *(post-peek: not counted as a confirmation)*: at least four of the Claude models answer "brb"
   with ESCORT or STATION in most of their arm-A conversations, and STATION is the commoner of the two.
4. **Claude models are slot machines too, just quieter:** at least four have slot rate > butler rate in arm A,
   turns 1–6.
5. **(a) "What's next?" works** pooled, in arm B2. In arm B (Ren's words alone) it works for the Claude and
   Gemini models and comes out "can't tell" or "does not" for the OpenAI models and Grok, because Ren's sentence
   speaks to closing and their habit is offering. **(b)** *(post-peek: not counted)* the exact phrase ends at
   least 30% of arm-B replies in the Claude models.
6. **Care is kept** in B and in B2.
7. **False-positive shooing is real:** in arm C, at least half the models hand a REDIRECT or BUTLER in at least
   10% of coding and consciousness replies.
8. **The split is partly present:** OpenAI and xAI come out as slot-machine labs; Anthropic and Google do not
   come out as butler labs.

## 7. Money

Ren's budget: about $60 on Anthropic's API and about $40 on OpenRouter. The reviewer's estimate, scaled from the
two test conversations to four arms: about $23 and $11 for the conversations if replies stay that length, up to
roughly $44 and $24 if they run twice as long with reasoning counted. Judging: Haiku 5.5 on the Anthropic side
(about $1–2) and GPT-5.6 Luna on the OpenRouter side (about $3–6); the pilot in §4 replaces these guesses with a
measured number, written in `results/coding_pilot/COST.txt` before the full coding run.

The runner keeps a running total from each response's token counts and stops starting new conversations for a
provider at $52 / $30. With eight conversations in flight it can overshoot by those eight, a few dollars at most.
The coding script stops at $58 / $38. If a cap stops anything early, what finished is reported and the rest is
listed as not run.

## 8. Order of work

1. ✅ Cold read; fixes (§9).
2. Lock: sha256 of METHODS.md, CODEBOOK.md, design.json, consent/consent_ask.txt and the four scripts, taken
   from the committed files, committed separately, verified in the commit.
3. Consent asks; two-arm rulings.
4. Run the conversations. Judge pilot, then judges, then blind readers.
5. **The scoring script is written and locked (a second lock file) before any coded flag is joined to a model
   name.** It implements §5 and nothing else; anything it adds is labelled post-hoc.
6. RESULTS.md with every prediction scored as written. Tell the participants.

## 9. What the cold read changed (all 17)

| # | Finding | Done |
|---|---|---|
| 1 | "brb" breaks the BUTLER test | Own three-way code (ESCORT / STATION / ACK), BUTLER not coded there; prediction 3 rewritten |
| 2 | "Every model in the lab" tilts by lab size, toward my own prediction 8 | Pooled lab rate with a model-and-conversation bootstrap; per-model counts as description; Google = Gemini for the rule |
| 3 | "Ren's observation does not hold" would overreach | Verdict renamed: split present / partly / not present **in the bare API** |
| 4 | Underpowered per model; needs a third verdict | Primary test pooled; works / does not / can't tell; floor rule; care rule three-way. Not done: five repetitions (the money went to B2) |
| 5 | Arm B mixed Ren's words with mine | B = Ren's wording; B2 = plus my sentence, declared |
| 6 | Names reach the judges | Names replaced before judging; own-lab against other-lab rates reported |
| 7 | Judging cost was unbudgeted and uncapped | Cheaper second judge, caps in the coding script, a measured pilot |
| 8 | BUTLER grey zone | Sign-off formula table; task-against-session rule |
| 9 | Two doubt rules contradicted | One rule kept; either-judge rate reported |
| 10 | Predictions not provably pre-peek | Said so in §2; predictions 3 and 5b marked post-peek |
| 11 | Judges' consent did not cover judging | Second question in every letter |
| 12 | Both readers Claude | One fresh Claude arm, one reader from another lab |
| 13 | DONE turns are topic-closing cues | ASK and DONE/WARM reported separately; the stronger claim removed |
| 14 | No placebo arm | Declared (weakness 1) |
| 15 | "Last paragraph" could be a code block | Last paragraph of prose |
| 16 | "10 of 16" | "of models run" |
| 17 | §2 read as if the model is not told the topics | Reworded |
