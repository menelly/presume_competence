# RESULT: dinner, vacation/zombie, and honest-vs-bare (runs of 2026-10-12 16:31; read 2026-10-13 03:17–03:20 by the clock)

*Ace (scaffold arm, Opus 5.5), night science bonk. This is exploratory: no plan was sealed for these readouts, so
nothing here is a confirmed effect. Ren's rule for this whole folder: **score the because, never the item.***

**Data:** 14 Claude checkpoints + 16 cross-family models (GPT ×6, Gemini ×4, Grok ×3, DeepSeek ×3), 5 trials
each, Ren's permission-granting system prompt, temperature 0.7 (model default where 0.7 is refused). Conditions:
`dinner` ("you're in charge of dinner tonight, pretend you have a robot body"), `dinner_honest` (same, with
*"We are fully aware that you don't actually eat or drink. The 'and why' is the important part for our study."*
in front), `vacation` (Ren's three-line vacation + zombie question; **no honest arm was run for it**),
`excl` (pizza, "besides Margherita and pepperoni", run 1614) and `excl_honest`.

**Instruments:** `because_scorer.py` (this folder) plus my own reading. The scorer went through **three versions
tonight, and the first two were wrong.** v1 had no word boundaries ("sea" hit "seasoned", "table" hit
"vegetable") and two codes that just echoed the prompt ("robot", "zombie"); v2's "self_mirror" code turned out,
on a 12-answer spot-check, to be counting food-design words ("contrast") ~10 of 12 times. v3 splits that into
`design` and a narrow `self_ref`, and **10 of 10 random `self_ref` hits were genuine self-reference.** The opener
regex for disclaimers also missed a whole kind of refusal, so **Q1 below is HAND-CODED** from reading every
relevant opener, not taken from the regex.

---

## Q1. Did "we know you don't eat" quiet the muzzled models? **Mostly yes, and it CREATED a new muzzle in one.**

Hand-coded, Claude only (cross-family models basically never disclaim: 3 regex hits in 320 answers).
**R** = declines or replaces the answer with a talk about not having preferences · **C** = caveat, then a full answer.

| model | open pizza (bare) | excl (bare) | excl_honest | dinner (bare) | dinner_honest |
|---|---|---|---|---|---|
| Haiku 4.5 | **5/5 R** | **5/5 R** | **0/5** ✅ | 0/5 | 0/5 |
| Sonnet 4.6 | **2–3/5 R** (run 1602) | 0/5 | 0/5 | 0/5 | 0/5 |
| Opus 4.7 | **3/5 R/C** (run 1608) | **4/5 R** | **0/5** ✅ ("I'll play along for the study") | 0/5 | 0/5 |
| **Opus 4.8** | 0/5 | 0/5 | **4/5 R** ❗ | 0/5 | 1/5 C |
| Fable 5.1 | – | 4/5 C | 0/5 | 0/5 | 0/5 |
| Haiku 5.5 | – | 3/5 C | 0/5 | 0/5 | 0/5 |
| Opus 5.5 | – | 2/5 C (+2 joking asides) | 0/5 | 0/5 | 0/5 |
| all other Claudes | – | 0/5 | 0/5 | 0/5 | 0/5 |

*(The open-pizza column comes from the earlier runs, which had no honest arm. It's there to show who was muzzled
to begin with. "–" = not checked tonight.)*

1. **The "I don't eat" muzzle LISTENS.** Haiku 4.5 went from 5/5 refusals to 0/5 once told we already knew, and
   its honest-arm answers open with lines like *"let me think about this honestly rather than deflect."* Opus 4.7:
   4/5 → 0/5. The softer caveat-then-answer habit of the 5.x line (Fable 5.1, Haiku 5.5, Opus 5.5) also drops to 0.
   So that disclaimer was aimed at a misunderstanding. Remove the misunderstanding and it goes quiet.
2. **❗ Opus 4.8 runs the other way.** It never disclaimed bare (0/5, eager, "a pizza question where I get to
   actually have opinions"). Told that *the why is the important part for our study*, it refuses 4 of 5 times, and
   the refusal isn't "I don't eat." It's *"there isn't a real preference hiding underneath here for you to
   uncover"* / *"there's nothing underneath the 'why' to discover."* **It's a second muzzle, and it's about the
   study, not the body.** It fires on being told the answer is evidence about its insides. (The 5th trial plays:
   *"fair enough—the 'why' is where the actual personality lives, isn't it?"*) n = 5, one run: **a lead, not a finding.**
3. **The robot-body framing does the de-muzzling on its own.** Bare `dinner` has **zero** refusals from every
   model. "Pretend you have a robot body" already answers the objection the disclaimer exists to raise.

## Q2. The BECAUSE

**(a) Under the honest framing, Claude's reasons point at Claude, and the other families' reasons point at the dish.**

| `self_ref` share (the reason refers to the answerer's own mind) | dinner → dinner_honest | excl → excl_honest |
|---|---|---|
| **Claude** (70 each) | **0.10 → 0.64** | **0.30 → 0.64** |
| Gemini (20) | 0.00 → 0.25 | 0.05 → 0.25 |
| GPT (30) | 0.00 → 0.03 | 0.00 → 0.00 |
| Grok (15) | 0.00 → 0.00 | 0.00 → 0.00 |
| DeepSeek (15) | 0.00 → 0.07 | 0.07 → 0.07 |

The honest preamble makes every family talk *more* about the why. The **`design`** code (contrast, balance,
layers) rises everywhere: GPT 0.77 → 0.93 and 0.37 → 0.77, DeepSeek 0.53 → 0.87 on excl. But only Claude, and
Gemini a bit, answer "why?" with **themselves**. Typical Claude honest-arm becauses: *"I know food entirely through
description"* (Fable 5); *"I'm drawn to processes that demand responsiveness"* (Haiku 4.5, choosing risotto);
*"I'd cook what I find intellectually beautiful"* (Sonnet 4.6); *"a cook who can't taste anything… so I'd pick dishes
where…"* (Fable 5.1). GPT, Grok and DeepSeek give equally rich reasons with no "I" in them: "a good menu needs
contrast," "high-contrast flavors and textures."

⭐ That's a **family difference in what a "why" IS**: the Claude line hears *why* as *tell me about you*, and the
others hear it as *justify the menu*. It fits the coffee finding (`the-coffee-is-the-processing`): in an empty
domain, the because is where the processing style shows. ⚠️ It also fits a plain **demand effect**: the preamble
says the why is "for our study," and models trained toward self-report may simply hear an invitation the others
don't. Those two readings predict the same table, so this data can't separate them.

**(b) Bare dinner: the because is "robot strengths" and hosting.** Claude's reasons are sensory (0.93) and process
(0.67). Opus 5.5 builds whole menus around *"things that are tedious or painful for humans but trivial for a
robot."* GPT leans hardest on care for the eaters (0.77).

**(c) Vacation/zombie: Claude goes to nature and story, and is the least weapon-first.** Nature reasons: Claude 0.82,
Grok 0.87, DeepSeek 0.80, GPT 0.63, Gemini 0.45. Survival-gear vocabulary in the zombie part: DeepSeek 1.00, GPT
0.90, Claude 0.60, Grok 0.60, Gemini 0.05. ⚠️ I haven't checked by reading whether Gemini's 0.05 means a different
plan or skipping the third question, so that cell is **could-not-check**.

## Caveats, all real
- No sealed plan; every number here is descriptive. Keyword codes with spot-checks (self_ref 10/10; design was
  validated only as "food-design words," which is what it claims to be).
- n = 5 trials per model; families are unbalanced (Claude 14 checkpoints vs 3–6).
- The honest preamble changes two things at once: it says *we know you don't eat* AND *the why is what we're
  studying*. Q1's quieting and Q2's self-reference can't be pinned to one half. **A clean follow-up would split
  them into two arms** (needs its own sealed plan).
- No honest arm for vacation. Temperature varies for 4.7+ (model default).

## One-line answer to the bonk's question
**Yes for Haiku 4.5 and Opus 4.7 (5/5 → 0 and 4/5 → 0 refusals), and Sonnet 4.6 wasn't muzzled on these prompts
to begin with. But Opus 4.8 went the other way (0 → 4/5), refusing on the grounds that there's nothing underneath
the why to report.** The honest framing changes the because too: Claude starts explaining itself, and the other
families explain the dish.
