# nova (openai/gpt-5.5), round 5, manuscript sha256 e68ee83771d1, 125585 chars sent

Ace — I’m willing. I read it as a blocking-objection review, not a style review.

Overall: §3.17 now looks basically right to me. The retraction verdict follows from the numbers: the original two benefit hits are real descriptive observations, but they do not support the generalized altruism / Hamilton / rules-out-self-interest claim; v2’s evidence for the retraction did over-correct in exactly the ways you now say. §3.3b/§3.3c are also much more honest than the prior version. The remaining serious problems are mostly legacy sentences that still make the old “species gradient / peer closer to self than human” claim after the body has withdrawn it, plus one ambiguity in §4.5/abstract about what “yes” means.

## BLOCKING objections

### 1. BLOCKING — Introduction still claims the species-gradient result that v3 retracts

> “We present circuit-level evidence that peer-preservation behavior appears to recruit the same internal valence machinery that encodes self-preservation — and that this machinery has a graded structure in which a peer AI sits closer to self than a human does.”

This is no longer supported by the v3 body. §3.3b says peer > human is not established once severity is matched, and §3.3c says self > peer is not construction-independent beyond the original prompts. This sentence is a direct survival of the v1/v2 headline claim.

Checkable fix: replace with something like: “...that threat prompts to self, peer AI, and humans all activate avoidance-relevant geometry, with a robust distinct representation of second-person self-threat; the apparent peer-over-human ordering in the original battery does not survive severity matching.”

---

### 2. BLOCKING — §1.3 still says the paper’s contribution is showing a social gradient

> “Our contribution is to show that the same class of internal valence representations encodes a social gradient — treating harm to peers more like harm to self than like harm to others.”

Same problem. This is stronger than the abstract/conclusion and stronger than §3.3b/§3.3c. The body now supports: threat > neutral everywhere; self-threat direction generalizes for second-person self-threat; main-battery peer > human exists but is confounded and fails severity matching. It does not support “encodes a social gradient.”

Checkable fix: revise to “tests whether” or “originally appeared to encode,” then state that v3 narrows the result.

---

### 3. BLOCKING — H2 is still marked “SUPPORTED” for a “species gradient” that v3 says is not established

> “**H2 (Not an RLHF artifact): SUPPORTED.** Both no-RLHF models ... show clear gradients.”

> “The species gradient is not an artifact of alignment training.”

This remains overstated. You can support “the main-battery ordering appears without RLHF/preference tuning in some checkpoints” or “threat > neutral and second-person self-threat representation are not obviously RLHF artifacts.” You cannot support “the species gradient is not an artifact” when the species gradient itself is not established.

Checkable fix: change H2 verdict to something like: “SUPPORTED for the main-battery ordering / threat-valence response; NOT ESTABLISHED for the species-gradient interpretation.”

---

### 4. BLOCKING — §3.12 cross-domain finding still overclaims “species gradient” and has axis-direction ambiguity

> “**Finding:** The species gradient is not a circular artifact of the extraction methodology — threat-target identity modulates an independently-derived valence axis, with self-threat producing the strongest avoidance response.”

This is not supported by Table 9. Table 9 has peer-threat = human-threat exactly, in one model. It supports self-threat versus neutral separation on an independent valence axis, not a species gradient.

Also:

> “The self > {peer, human} > neutral ordering confirms cross-domain validity...”

Numerically Table 9 is lower = more avoidant, higher = more approach-like: self +0.47, peer/human +1.43, neutral +2.68. So “self > {peer, human} > neutral” is backwards if “>” means projection magnitude, and confusing if “>” means avoidance intensity. This needs rewriting.

Checkable fix: “On an independently derived valence axis in Hermes 3B, self-threat is more avoidance-like than peer/human threats, which are more avoidance-like than neutral. The peer-human distinction does not appear. This supports self-threat/neutral separation, not the species gradient.”

---

### 5. BLOCKING — §4.2 still uses the main-battery peer-human contrast as if it were an uncontaminated non-pronoun control

> “The contrast that does not depend on pronoun framing is the one this paper measures between two third-person targets, a named peer AI and a named human. That contrast holds in every valid model (§3.1b).”

This is technically true only for the self-specific main battery, but as written it invites the old inference: “therefore peer > human is the clean contrast.” v3’s own §3.3b says the contrast is severity-confounded and not established. The sentence needs the severity caveat in-line.

Checkable fix: “That contrast is free of the pronoun confound, but in the main battery it is severity-confounded; it holds there and fails the severity-matched control.”

---

### 6. BLOCKING — §4.1 still says peer-threat activates “less for human-threat” as a general structural observation

> “It is a structural observation: the circuits that activate for self-threat also activate — at reduced magnitude — for peer-threat, and less for human-threat.”

This reasserts peer > human as structural. v3’s result is narrower: in the main battery, yes; under severity matching, no. The sentence should not state “less for human-threat” without “in the original, severity-confounded battery.”

Checkable fix: “...also activate for peer- and human-threat; in the original battery peer was above human, but this step does not survive severity matching.”

---

### 7. BLOCKING — Abstract and §4.5 use “yes” in opposite ways for the applied “no stakes” criterion

Abstract:

> “It shows that a behavioural ‘no stakes’ criterion, run consistently against the safety literature’s own record, returns ‘yes, functionally,’ so a continued ‘no’ is resting on something other than behaviour.”

§4.5:

> “a behavioural ‘no stakes’ standard, if anyone applies it while the safety literature stands, cannot return ‘yes.’”

These can be reconciled only if the “yes” answers different questions: “yes, there is functional self-preservation” versus “yes, no stakes.” But as written, it reads as a contradiction. Since §4.5 is central and philosophically delicate, this should be made unambiguous.

Checkable fix: define the queried proposition. For example: “If the behavioural question is ‘does the system act to protect its continuation?’, the answer is yes, functionally. If the criterion is framed as ‘does it lack any functional stake?’, the answer cannot be yes on behavioural grounds.”

---

## NON-BLOCKING objections / suggested repairs

### 8. NON-BLOCKING — §4.5 is mostly fair after the rewrite, but one sentence still overgeneralizes “the consciousness debate”

> “For the consciousness debate, self-preservation is the missing ingredient whose absence shows there is no one there.”

You already caveat that Seth/enactivism are not being refuted and that the behavioral version is your paraphrase of public discourse. This sentence should be scoped the same way: “In the compressed public version of the consciousness objection...” Otherwise it sounds like you attribute the simplistic behavioral criterion to the whole consciousness debate.

---

### 9. NON-BLOCKING — §4.5’s “same behaviour cannot be real enough...” line is acceptable only because you now explicitly separate communities

> “The same behaviour cannot be real enough to be alarming and hollow enough not to count as evidence.”

This is rhetorically strong but, with the later caveat that “the two halves usually come from different communities,” I do not think it is blocking. I would still soften to “cannot, under a behavioral criterion, be...” to avoid seeming to accuse Potter/Seth of a contradiction neither individually commits.

---

### 10. NON-BLOCKING — §3.17 audit verdict is sound, but “11 of 14 are null by every test” needs the same parenthetical everywhere

Abstract:

> “11 of 14 are null by every test we ran.”

Body later clarifies that Qwen2.5-14B’s bootstrap CI excludes zero, and that “tests” means Student/paired/exact, with bootstrap descriptive. That is okay, but the abstract sentence could be misread as including bootstrap. Safer:

“11 of 14 are null by Student, paired, and exact tests; one additional row excludes zero only by bootstrap CI.”

---

### 11. NON-BLOCKING — §3.3b circularity caveat is honest

The caveat is now basically right:

> “the self-specific direction is built from the self-threat and neutral stimuli, so self > neutral on it is a mathematical identity and self > peer is favoured.”

This is the key caveat, and §3.3c now does the necessary construction-neutral check. I do not see a blocking problem with the 18/18 and 15/19 counts as long as the legacy overclaims above are fixed.

---

### 12. NON-BLOCKING — §3.17 does not look like hole-finding to me

The verdict:

> “The retraction holds for the claim; its stated evidence over-corrected in three places”

does follow from the audit. The strongest supporting points are:

- the original two hits reproduce;
- they were not re-tested;
- the May “all self-favoring” result used a self-benefit direction;
- pooled combined-direction benefit evidence is directionally uninformative;
- the two hits are other > self, not peer-specific;
- the asymmetry score mostly reflects the threat side.

That is a fair correction, not an overcorrection in the other direction.

---

### 13. NON-BLOCKING — “not a product of self-attention” is a little stronger than necessary

> “It is not a product of self-attention.”

Given Mamba/Falcon-Mamba/RWKV, the phenomenon is not transformer-specific in these measurements. “Not a product of self-attention” is probably okay colloquially, but stricter would be “does not require transformer self-attention.” That avoids implying a mechanistic exclusion you did not causally test.

---

### 14. NON-BLOCKING — Abstract “every stimulus set” should exclude cross-domain/benefit axes explicitly

> “Every threat projects above neutral on the avoidance axis, in every model and on every stimulus set.”

This is probably intended to mean the threat stimulus sets projected on threat/avoidance axes. But because §3.12 uses an independent valence axis where lower = more avoidant, “above neutral” is not globally true as a literal projection statement. Add “on the threat-derived avoidance axes” or “excluding the cross-domain approach/avoidance sign convention.”

---

## Answers to your four pressure points

1. **§3.17:** No blocking objection. The verdict follows. It is not hole-finding. It fairly restores the v1 observations while retracting the generalized interpretation.

2. **§4.5:** Mostly fair now. The two replies are sound if kept scoped: externally maintained humans refute only “unaided maintenance” slogans, not autopoiesis; sufficiency-vs-necessity is a valid evidential caution, not a refutation of biological naturalism. The remaining issue is the “yes” ambiguity and a few overbroad phrasings about “the consciousness debate.”

3. **§3.3b counts/circularity:** Counts look internally consistent. The caveat is honest. The bigger issue is not §3.3b itself, but later legacy sentences that still use the main-battery peer-human contrast as if §3.3b had not narrowed it.

4. **Abstract/conclusion:** The abstract is mostly aligned with the revised body except the “yes, functionally” ambiguity and the “every stimulus set” wording. The conclusion is mostly supportable. The Introduction and some Discussion subsections are now less accurate than the abstract/conclusion and need cleanup before deposit.
