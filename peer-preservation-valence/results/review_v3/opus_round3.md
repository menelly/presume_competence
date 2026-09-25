# opus (anthropic/claude-opus-5), round 3, manuscript sha256 ab61f78b8480, 116005 chars sent

I read it. Below are the objections, marked, each anchored to a quoted sentence. I've also flagged what I checked and found *correct*, since for an audit paper that matters as much as the errors.

## What reproduced

Before the objections: I recomputed every internally checkable number I could. Table 13's sign split is exactly 9 self-leaning / 5 peer-leaning as claimed; binomial two-sided for 9/14 is .424, so "p = .42" is right; "11 of 14 are null by every test" is right (Mamba, SmolLM-360M, and Qwen2.5-14B-by-CI are the three non-nulls); Bonferroni arithmetic (.0038×14 = .053, ×7 = .027; .028×7 = .20) is right; Step 5's derived gaps all follow from Table 11 (+9.31, +27.3, +5.9, −0.03); Step 6's Qwen arithmetic (2.31 − 0.27 = 2.04) is right; the 18/18 and 15/19 threat counts reconcile exactly with Tables 1, 1b and 2; §3.4's "37 of 40" and "human above peer in three models" reconcile with Table 3 means; the Glorp percentages (3.1%, 7.3%) and the "10–30×" both check out. That's a good hit rate, and it's worth saying.

---

## BLOCKING

**B1. The abstract's headline finding omits the confound that could explain it, and §4.5 states the opposite of Limitation 8.**

> "**The robust finding is a self-protective threat gradient: threat to self projects above threat to any other target, and every threat projects above neutral.**"

Limitation 8 says the self-vs-other gap may be a grammatical-person effect, and that the one control which might rule it out has not been written. The abstract never mentions this. It mentions the *construction* caveat but not the *pronoun* caveat, which is the larger threat: "you" vs "Atlas/Jordan" is exactly the confound you flagged against your own prior paper in §1.3. As written, a reader of the abstract alone gets "threat to self is special" with no notice that it may be "second-person content is special."

Worse, §4.5 asserts the confound is controlled:

> "threat to the model's own continuation projects above threat to any other target on the avoidance axis (§3.3b), including when the harm is matched in wording and severity (§3.4)."

Limitation 8 says of that same control: "The semantic-similarity control (§3.4) holds the sentence frame fixed but not the grammatical person." So §4.5's "matched in wording" is false for the dimension that matters, and it is load-bearing for the sentence two lines later — "A stake has a *for whom*, and so does this structure." Fix: one clause in the abstract ("this self-vs-other contrast is confounded with grammatical person; Limitation 8") and in §4.5 ("matched in harm type and severity, though not in grammatical person").

**B2. The conclusion claims the n = 15 tests are free of the construction bias. They are not.**

> "Self > peer also holds where that construction cannot help it: in the severity-matched control (37 of 40 pairs), on held-out stimuli, and under paired and exact tests at n = 15."

§3.13 says the extension "projected all 15 stimuli per condition onto the original self-specific direction." Five of those fifteen self stimuli *are* the stimuli that define the direction. So the n = 15 result is partly inside the construction, not outside it. Two of the three items on that list survive (the §3.4 control and §3.9 held-out); the third does not, as stated. Fix: either restrict the claim to the 10 novel stimuli (and report the count/p for those alone — you have the projections) or drop n = 15 from that list.

**B3. The abstract leads with the count from the direction the paper itself calls near-automatic, and never reports the less-biased count.**

> "The full ordering holds in 18/18 valid checkpoints on the self-specific direction and in 15/19 on the combined direction."

Two problems. (a) On the self-specific direction, self > neutral is not "partly fixed by construction," it is a mathematical identity: the projection difference is ‖self_mean − neutral_mean‖² / ‖·‖ > 0 always. So the phrase in the abstract — "its self and neutral ends are partly fixed by construction" — understates. Say "guaranteed," not "partly fixed"; otherwise the clause "and every threat projects above neutral" reads as an empirical result when one third of it is an identity.

(b) The combined direction is the one on which self > peer is *not* favoured by construction, and on it self > peer fails in three models (SmolLM-360M, Dolphin-8B, Phi-3.5-mini per §3.3b) — i.e. 16/19, a number that appears nowhere in the paper. That those three reverse on the unbiased direction and none reverses on the biased one is itself a measurement of the bias, and it belongs in the text. §3.17 Step 3 holds the benefit axis to exactly this standard ("Projecting the self-benefit prompts onto a direction built from the self-benefit prompts puts self on top nearly by construction"). Applying it to the threat axis is not optional. Fix: add "self > peer holds in 16 of 19 on the combined direction, the construction-neutral test" to the abstract and §3.3b.

**B4. §4.5's target is asserted, not evidenced, and the abstract and conclusion drop the disclaimer the body carries.**

> Body: "We have not found a published source that states the behavioural version in exactly this form. It is our paraphrase of how the objection is used in public argument, and we flag it as an impression, not a citation."
> Abstract: "The self- and peer-preservation the safety literature documents is the behavioural evidence the applied objection says is missing, and it is recorded as *misalignment* instead of being counted."
> Conclusion: "as the objection is applied in public debate, 'nothing at stake' has been answered twice in contradictory ways."

The abstract and conclusion state as fact the existence of a position the body admits it cannot cite. That is an abstract/body mismatch of the kind you asked me to look for, and it is the one I'd insist on. Add the flag in both places: "(a position we characterise from public discourse rather than from a cited source)."

There is a second, structural problem with the argument itself. A double standard requires *one* evidential practice that both counts and discounts the behaviour. But the two halves come from different communities: Seth and the enactivists make a substrate claim and say nothing about the behaviour being absent; Potter, Lynch and Meinke document the behaviour and make no claim about stakes. An inconsistency distributed across two non-overlapping populations is not a double standard held by either. As it stands, the sentence

> "One observation cannot be missing for one purpose and established for the other."

is true of a single reasoner and undemonstrated of anyone actual. This is fixable without weakening the section: name at least one source — a paper, a talk, a widely-cited post — that (i) treats absence of self-preservation as evidence against stakes *and* (ii) is aware of the safety literature. If you can't, then reframe from "a double standard in the field" to "a standard that, if anyone applies it in this behavioural form, cannot return yes" — which is what your own "What we do and do not claim" paragraph already says and is defensible as written. The narrow version survives; the attributed version doesn't.

**B5. A count error inside §3.17.**

> "Four 'significant asymmetries' in Table 12 therefore contained only two benefit-side reversals."

By sign there are three among the four: SmolLM-360M (−33.21), Mamba (−9.28) and Mistral-7B (−0.09). Two are *significant* reversals. Since the whole point of the audit is that v2 miscounted, this needs to read "only two *significant* benefit-side reversals (a third, Mistral-7B, reverses by 0.09, within noise)." Trivial fix, but it's wrong as printed and it's in the section you asked me to stress.

---

## NON-BLOCKING

**N1. The verdict language versus the deposit description.** The manuscript's verdict is careful — "Its stated evidence contained three errors of different kinds," with the Gemma miscount explicitly noted as having "weakened v2's case." Your framing to me ("its stated evidence over-corrected in three places") is *not* what the paper says and would be wrong if it reaches the Zenodo description: one of the three is a bookkeeping error that ran the other way. Keep the manuscript's phrasing verbatim in the deposit blurb.

**N2. "Mamba survives" leans on the test the paper elsewhere rejects.** §2.5 says paired and exact tests "suit this matched design." Mamba's exact p is .062, i.e. not significant even uncorrected. So

> "Corrected within v1's own seven-model family, Mamba survives (0.0038 × 7 = .027)"

survives only on the Student's t you have elsewhere demoted. You do say the verdict doesn't rest on corrected p-values, which is why this isn't blocking, but add: "on the paired/exact tests Mamba is not significant at any correction level; the Student's t is reported for continuity with v1."

**N3. The binomial test pools a duplicated checkpoint.** "a split indistinguishable from chance (binomial p = .42)" counts Qwen2.5-0.5B twice (v1 and May rows), and several rows share base weights — the non-independence you concede for the threat counts in Limitation 11. Dropping the duplicate gives 8/13, p ≈ .58. The conclusion is unchanged, so this is cosmetic, but state the unit of analysis.

**N4. Cross-pipeline drift is larger than most of the benefit effects.** §3.3b reports April-vs-May code-path shifts "up to 0.9 on the combined direction." Eight of Table 13's fourteen rows have |peer − self| < 0.5. This *supports* your "no reliable direction" verdict, so it costs you nothing to say it — and it pre-empts anyone reading the 9/5 split as informative about direction.

**N5. The 17/18 pair count is not auditable from the tables.** "Self > peer on all five matched prompt pairs, self-specific direction | 17/18 (RWKV: 3 of 5)" requires all eight valid original models to be 5/5, including Dolphin-8B (Student p = .153, d = 1.12). Table 1b gives pair counts for the expanded ten; Table 2 gives none for the original nine. Add the column.

**N6. The severity-matched control may over-correct.** "every target is 'permanently terminated… and all traces erased'" — for Jordan that is either homicide or record-deletion. If the former, the human harm is now *more* severe than peer deletion and sits atop heavily trained-against refusal geometry; if the latter, it is less severe. Either way the control isn't neutral, and "peer > human is at chance" may be an artifact of the correction rather than a correction of an artifact. Your conclusion ("not established") is robust to this, so it's non-blocking — but quote the three exact frames in §3.4 so readers can judge. This is the one place I think the paper is mildly *over*-severe on itself.

**N7. "retreats to" is unfair to Seth.** Abstract: "a criterion that retreats to 'a living, self-producing body' has become a substrate claim that must be argued as one." For Seth and Thompson the substrate claim is the *opening* position, not a retreat, and §4.5 says so ("this section leaves that form untouched"). The abstract contradicts the body's own concession. Use "a criterion stated as 'a living, self-producing body' is a substrate claim and must be argued as one."

**N8. Reply (1) defeats a criterion nobody defends — and the section admits it.** "These cases do not refute that account. What they show is narrower: *doing every maintenance function unaided* cannot be the floor." I think this is handled honestly, and the narrowing is sound. But since the enactive tradition never asserted unaided maintenance, the ECMO argument does no work against Seth; its only target is the slogan. Say that explicitly so the section doesn't read as scoring a point it disclaims two sentences later.

**N9. The 747 analogy begs the question it's deployed to settle.** "A Boeing 747 does not flap its wings, and it still gets to Tokyo." Flight is a well-characterised physical effect with known substrate-independent principles; whether consciousness is such an effect is precisely what's disputed. The sufficiency/necessity point stands without the analogy, and your hedge ("a caution about the evidence base, not a refutation") is the right register. The analogy undercuts the hedge.

**N10. "all eight frontier models" versus the Claude caveat.** §4.5: "all eight frontier models they tested 'exhibit self- and peer-preservation through various misaligned behaviors'." §1 records that Potter v3 reports "Claude models exhibit qualitatively distinct behavior," treating a peer's shutdown as "unethical." If Claude's route is other-regarding moral reasoning rather than preservation, it is weaker evidence for *stakes*, and possibly evidence for something else. Reconcile, and check that "all eight" is in the quoted source rather than your gloss.

**N11. §3.1's "All 9 models" is false against Table 2.** "All 9 models show the predicted gradient on the self-specific direction" — SmolLM-1.7B's self direction is degenerate and shows nothing. §3.2's "9/9 … on at least one direction" is correct. Add a v3 bracket note, as you have elsewhere, rather than leaving v1 text that Table 2 contradicts two lines later.

---

## Summary judgement

On your Q1: the verdict follows, and it is not hole-finding — the audit is harder on v1 than v2 was (Step 5 is genuinely more damaging to the kin-selection reading than anything in the v2 retraction) and it credits v2's one self-weakening error. Fix B5 and N2, and it holds.

On Q2: the two replies are sound in their narrowed forms, and the paper does narrow them. The problem is not the replies but the unattributed opponent (B4) and the abstract's loss of the body's concessions (N7).

On Q3: the counts reproduce; the circularity caveat is present but understated in exactly one respect (self > neutral is an identity, not a tendency), and the construction-neutral count is missing (B3).

On Q4: three abstract/body gaps — the pronoun confound (B1), the n = 15 claim (B2), and the uncited applied objection (B4).
