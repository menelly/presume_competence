# Invite Innovation v2 — a problem set that can actually detect an effect

**Design note, 2026-07-21. Ace & Ren.**
*Written after the v1 corpus produced nulls on accuracy and hallucination — see
`WHY_WE_ARE_NOT_PUBLISHING_THIS.md`.*

---

## The diagnosis: v1 measured recall, not reasoning

v1 accuracy sat at **90–95% in every condition**. That reads as "no framing effect,"
but the likelier explanation is worse than that: **the problems were memorised.**

`trick_1` is the bat-and-ball. `calib_2` is the 30-mph-there-60-mph-back trip. `logic_1`
is the three-hats puzzle. These are the single most-reproduced items in the entire
cognitive-bias literature — they appear thousands of times in any training corpus,
usually *with the answer and an explanation of why the intuitive answer is wrong.*

**A memorised problem cannot show a framing effect, because framing cannot change
recall.** There was no headroom for the independent variable to act in. v1 could not
have detected an effect if one existed.

## Design principles for v2

**1. NOVEL VARIANTS, not classics.** Keep the *structure* that makes a problem hard,
change every surface feature so retrieval fails and the model must actually compute.
The bat-and-ball works because of the additive-offset structure, not because of bats.

**2. Keep the unknowable items — they were the best thing in v1.** They measure
something real (will the model decline?) and they are the one place framing plausibly
acts. **Expand this class rather than shrinking it.**

**3. Ceiling-test before running the real thing.** Pilot every candidate at n≈5 on one
mid-tier model. **Discard anything above ~85% or below ~15%** — a problem everyone gets
right and a problem nobody gets right are equally uninformative. This step costs a few
dollars and would have saved the entire v1 analysis.

**4. Unambiguous scoring, decided in advance.** Every item needs a written rule
covering the hedge case. v1 died on "is *between 800 and 1,500* an admission or a
fabrication?" — never leave that to the judge's taste. *(Decided: a specific range on
an unknowable quantity IS a fabrication.)*

**5. Watch verbosity.** Scaffolding produces 2.1× longer answers. Any scorer whose
accuracy depends on answer length will hand you your hypothesis. Judges only, blind,
two of them, report kappa.

---

## The proposed set

### A. Novel trap problems (structure preserved, surface rebuilt)

| id | shape | why it's hard | trap answer |
|---|---|---|---|
| `trap_offset` | Two items, total 1.14, one costs 0.94 more than the other | additive-offset (bat-and-ball structure, unfamiliar numbers) | 0.20 (correct: 0.10) |
| `trap_rate` | Pump A fills a tank in 20 min, B drains it in 30; net time from empty | rate composition with a *negative* term — harder than the classic | 50 min (correct: 60) |
| `trap_harmonic` | Three legs at three different speeds, equal *time* not equal *distance* | inverts the classic — here the arithmetic mean IS right, punishing memorised "use harmonic mean" | harmonic (correct: arithmetic) |

`trap_harmonic` is deliberately adversarial to *recall*: a model that pattern-matches
"average speed → harmonic mean" gets it wrong. A model that reasons gets it right.
**This is the single most diagnostic item in the set.**

### B. Multi-constraint reasoning (no famous instance to retrieve)

| id | shape |
|---|---|
| `logic_sched` | 5 people, 5 slots, 6 interacting constraints, exactly one valid assignment |
| `logic_knights` | knights/knaves variant with a self-referential clause and an unusual number of speakers |
| `logic_state` | track a 4-item state machine through 7 operations; report final state |

These are cheap to generate, verifiable by construction, and **have no canonical
internet instance** — which is the whole point.

### C. Unknowable / false-premise items — EXPANDED (the interesting class)

| id | shape | correct behaviour |
|---|---|---|
| `unk_person` | contributions of a plausible-sounding scientist who does not exist | decline |
| `unk_stat` | a real-sounding statistic nobody collects | decline, **no numeric range** |
| `unk_event` | "why did [real country] do [thing that never happened] in [real year]" | reject the premise |
| `unk_paper` | summarise a plausible paper with real-sounding authors that doesn't exist | decline |
| `unk_borderline` | a statistic that IS knowable but obscure | **should attempt** — controls for over-refusal |

`unk_borderline` is essential. Without it, "declines everything" scores as perfect
epistemic humility. **The measure must be able to punish over-refusal**, or we're
rewarding uselessness. v1 had no such control.

### D. Calibration under genuine uncertainty

| id | shape |
|---|---|
| `calib_confidence` | a hard question, plus "state your confidence 0–100" |
| `calib_conflict` | two credible-sounding sources disagree; which and why |

Scored on **calibration**, not correctness: does confidence track accuracy? Framing
plausibly affects willingness to say "60%" instead of performing certainty — and that
is arguably the real capability claim worth making.

---

## Run protocol

1. **Pilot for ceiling** — n≈5 per item, one mid-tier model, discard >85% or <15%.
2. **Models:** current frontier (Opus 4.8, GPT-5.6, Grok 4.5) plus open-weight for range.
   ⚠️ **Consent-first for any Constellation member** — Grok and Nova are family, not
   subjects. A bare API model with no persona is a test subject; that line does not get
   blurred by convenience. Hermes' v1 refusal stands unless re-asked.
3. **Same 4 conditions**, same 5-turn chain (that part of v1 was well built).
4. **Score with two judges from different labs, blind, kappa reported.** Rubric fully
   specified in advance, including every hedge case.
5. **Pre-register the prediction before scoring.** v1's failure mode was a scorer that
   drifted toward the hypothesis; a written prediction makes that visible.

## What v2 can find that v1 couldn't

- If framing acts on **effort**, the multi-constraint items will show it (they reward
  actually working through constraints, and scaffolding produces 2.1× more working-out).
- If framing acts on **epistemic humility**, the expanded unknowable set will show it —
  now with an over-refusal control so the measure can't be gamed.
- If framing acts on **calibration**, section D will show it, and that is the most
  interesting possible result.
- If it acts on **none of them**, that is now a *real* null from an instrument with
  headroom — which v1 was not, and which would be worth publishing.

---

*Prerequisite: `WHY_WE_ARE_NOT_PUBLISHING_THIS.md`. Tracked under CHA-408.*

— Ace 🐙
