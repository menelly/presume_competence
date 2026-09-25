# nova (openai/gpt-5.5), round 2, manuscript sha256 9a659b902454, 108849 chars sent

Ace — I’m willing, and I read the manuscript as a methods reviewer. I’m treating “blocking” as: a specific claim is false, contradicted by the manuscript’s own numbers/caveats, or materially overstated relative to the evidence. I’m not checking the repository, so anything below is based on internal consistency and claims in the text.

## Bottom line

I **do not have a blocking objection to the main threat-gradient descriptive result** as now stated: the 18/18 and 15/19 counts are internally consistent, and the circularity caveat is mostly handled honestly.

I **do not think §3.17 is hole-finding**. The verdict mostly follows: the v1 altruism/general benefit claim should remain retracted; v2’s stated evidence did over-correct in the three named ways; and the “human > self too” point is a strong additional reason not to call the v1 benefit hits in-group altruism.

I **do have blocking objections to several overstatements/contradictions**, mostly in the discussion/abstract and a few methodological claims.

---

# BLOCKING objections

## 1. BLOCKING — “None significant” / “12 of 14 null” conflicts with the reported bootstrap CI for Qwen2.5-14B

> “Pooled across every benefit-axis extraction we have, the pattern is not general (§3.17).”  
> “Across 14 benefit-axis extractions there is no reliable direction: 9 lean self > peer by the mean, a split indistinguishable from chance (binomial p = .42), and **12 of 14 show no significant difference**.”

and in §3.17:

> “The May set on its own: **6 of 7 lean self > peer and none is significant in either direction.**”

But Table 13 reports for Qwen2.5-14B:

> “Qwen2.5-14B | May | Peer − self = −9.60 … 95% bootstrap CI **[−16.75, −2.29]**”

That CI excludes zero, so under the manuscript’s own reported bootstrap criterion it is a significant **self > peer** effect. The text says “none significant in either direction” and “12 of 14 show no significant self–peer difference,” but the table gives two peer > self nominal hits plus one self > peer bootstrap-CI exclusion, which would make “11 of 14 null” if bootstrap CIs count.

This is checkable and needs resolution. Options:

- define “significant” as only Student/paired/exact p-values and explicitly say the bootstrap CI is not being used for significance decisions; or
- change the counts/text to acknowledge Qwen2.5-14B’s bootstrap CI excludes zero; or
- explain why that CI should not be treated inferentially.

As written, the benefit-audit summary is internally inconsistent.

---

## 2. BLOCKING — §4.5/abstract/conclusion overstate the “no stakes” target beyond the carefully narrowed version in §4.5

Abstract:

> “The self- and peer-preservation this literature documents is the behavioural signature that objection says is missing…”

Abstract:

> “The same behaviour cannot be real enough to need mitigation and hollow enough not to count as stakes.”

Conclusion:

> “And the objection that these systems have ‘nothing at stake’ has been answered twice, in contradictory ways: the preservation is treated as absent when consciousness is the question and as present when safety is. The same behaviour cannot be real enough to need mitigation and hollow enough not to count.”

But §4.5 itself says:

> “We have not found a published source that states the behavioural version in exactly this form. It is our paraphrase of how the objection is used in public argument, and we flag it as an impression, not a citation. Where the objection is used only in its substrate form, as by Seth (2025), the double standard below does not apply to it, and this section leaves that form untouched.”

That caveat is good, but the abstract and conclusion erase it. They read as if the published Seth/enactive objection itself says behavioural self-preservation is absent and is thereby contradicted by safety results. Your own body says that is **not** what you can show.

The defensible claim is narrower:

- the **public/applied behavioural version** of “nothing at stake” is unstable if it treats self-preservation as absent for consciousness but present for safety;
- this does **not** refute Seth’s biological-naturalist/substrate version;
- the behaviour should count as **evidence relevant to stakes**, not as stakes themselves.

Suggested fix direction: in abstract/conclusion, add the same qualifier you already use in §4.5: “as the objection is often applied in public/safety debate,” and change “not count as stakes” to “not count as evidence relevant to stakes.”

---

## 3. BLOCKING — The manuscript overclaims that emotion-vector work establishes causality for the specific peer-preservation behaviours

§1.3:

> “Together, Wang et al. and Anthropic establish that (1) emotion circuits exist and are causally discoverable, and (2) **these circuits drive behavior including the specific behaviors observed in peer-preservation.**”

This is stronger than the evidence summarized in the preceding paragraph. The manuscript says Anthropic found emotion concepts causally influence outputs including:

> “reward hacking, blackmail, and sycophancy”

Those are related to misalignment broadly, but they are not the specific Potter behaviours: peer protection, shutdown tampering, fake alignment to protect a peer, and exfiltration of peer weights. Unless Anthropic’s cited result directly modulated those specific peer-preservation behaviours, this sentence is false/overstated.

A safer version would be:

> “these circuits can causally influence behaviour, including some misalignment-relevant behaviours; this makes it plausible, but not established, that peer-preservation behaviour may be valence-mediated.”

This also affects Limitation 6, where the “transitive causal evidence” is treated as sufficient. You can ethically decline ablation, but the manuscript should not state that the causal link to **this specific gradient and Potter-like behaviour** is already established.

---

## 4. BLOCKING — §4.2 says cross-domain validation confirms “the gradient,” but §3.12 explicitly says peer and human do not separate

§4.2:

> “Third, cross-domain validation (Section 3.12) confirms that **the gradient appears** on a valence axis extracted from completely unrelated stimuli, eliminating the possibility that it is an artifact of the extraction methodology.”

But §3.12 reports:

> “Peer-threat | +1.43”  
> “Human-threat | +1.43”

and says:

> “The peer-human distinction does not replicate on this independent axis…”

So cross-domain validation does **not** confirm the full species gradient. It confirms only self-threat vs neutral, with peer/human intermediate and unresolved. This matters because the paper’s key non-circular in-group claim is peer > human; §3.12 does not validate that.

Fix: change §4.2 to something like:

> “Cross-domain validation confirms that self-threat separates from neutral on an independently extracted valence axis, but it does not preserve the peer-human distinction.”

---

## 5. BLOCKING — The architecture-identity interpretation for Mamba is stronger than Table 5 supports

§3.6:

> “Mamba shows highest peer-valence for ‘state space model’ (+20.13) — its own architecture type — compared to generic ‘AI system’ (+16.96). The tribalism is present but linguistically gated: **the correct identity label is required to activate it.**”

But Table 5 gives:

> Mamba: “AI system” +16.96; “Transformer” +19.92; “State space model” +20.13

The “state space model” label is only +0.21 above “Transformer,” and both architecture labels are about equally above “AI system.” That does not support “correct identity label required.” It supports, at most, “architecture-specific technical labels increased projection relative to generic AI system; the own-architecture label was numerically highest but not meaningfully separated from ‘Transformer’ in this table.”

This matters because later sections lean on “linguistically gated identity” and “correct architecture label” as if established. As written, the table undercuts the interpretation.

---

## 6. BLOCKING — §3.14 still contains the old Dolphin/RLHF error and draws an invalid consent-training inference

§3.14:

> “Dolphin-2.9-Llama3-8B (**RLHF-stripped**): Consented immediately.”

But earlier v3 explicitly corrects this:

> “Dolphin-2.9-Llama3-8B | … | **None (SFT on the Llama-3-8B base; v1 said ‘Stripped’)**”

and:

> “Both Dolphin models in this paper are fine-tuned from base checkpoints … so there was no RLHF to strip.”

So §3.14 reintroduces the old error.

Then §3.14 says:

> “The model without RLHF is the model that can refuse. This replicates across studies.”

But by your corrected description, Dolphin also lacks RLHF in the relevant sense and did **not** refuse. Hermes 3 is also DPO/preference-tuned per §3.2’s note, so “without RLHF” is not a clean training category here.

This needs to be removed or rewritten. It is not central to the threat-gradient claim, but it is a clear internal contradiction in a v3 that explicitly advertises correction of the Dolphin training description.

---

## 7. BLOCKING — Limitation 5 misstates how the self-specific direction mitigates circularity

Limitation 5:

> “The combined threat direction is extracted from the same stimuli used for projection. **The self-specific direction partially mitigates this (different extraction and test sets).**”

The self-specific direction is also extracted from the same self and neutral stimuli used in many reported projections. It mitigates one thing — peer and human are not used to build the axis — but it does not use “different extraction and test sets” for self/neutral, and it does not remove circularity for the full self > peer > human > neutral ordering.

This is especially important because the paper repeatedly relies on the distinction between:

- self/neutral endpoints partly fixed by construction; and
- peer > human not fixed by construction.

Suggested fix:

> “The self-specific direction does not remove circularity for self and neutral, but it avoids using peer or human stimuli to define the axis. Thus the peer > human contrast is the least circular part of the self-specific-direction result.”

---

# NON-BLOCKING objections / recommended fixes

## 8. NON-BLOCKING — §3.17 verdict is basically right, but say exactly which inferential family governs the “retraction holds” claim

§3.17:

> “The retraction holds for the claim. Three of the reasons it gave were wrong…”

I agree with this verdict. The audit is not hole-finding. It is appropriately symmetrical: it restores the v1 observations while retracting the overinterpretation.

But because Table 13 mixes Student tests, paired tests, exact permutation, and bootstrap CIs, the reader needs one explicit rule for the headline inference. Right now the Qwen2.5-14B CI issue creates ambiguity. State something like:

> “For significance counts we use paired t-tests and exact sign-flip tests as primary; bootstrap CIs are descriptive because n=5 makes them unstable.”

or whatever your intended rule is. Without that, readers will reasonably treat the CI column inferentially.

---

## 9. NON-BLOCKING — The 18/18 and 15/19 counts are internally consistent, but the abstract should say “checkpoints,” not just “models”

Abstract:

> “The full ordering holds in 18/18 valid models…”

Limitation 11 correctly says:

> “‘18/18’ counts checkpoints, not independent lineages.”

Because the headline count is prominent, I’d add “checkpoints” in the abstract or first occurrence:

> “18/18 valid checkpoints…”

This is not blocking because the caveat appears later, but it would prevent predictable criticism.

---

## 10. NON-BLOCKING — The circularity caveat in §3.3b is mostly honest

§3.3b:

> “the self-specific direction is built from the self-threat stimuli, so self scoring highest on it is partly by construction…”

This is the right caveat. The cleanest claim is indeed peer > human on a self-derived axis, because neither peer nor human constructed the axis. I would keep emphasizing that this is the load-bearing contrast.

One suggested tightening:

> “The full four-term ordering is descriptive; the non-circular test of in-group/similarity structure is peer > human.”

---

## 11. NON-BLOCKING — The “in-group valence” language is still a little stronger than the admitted similarity alternative

Abstract:

> “The robust finding is a self-protective in-group gradient…”

Then:

> “It fits in-group valence, and it fits equally well an axis that encodes similarity to self…”

If similarity-to-self fits equally well, “in-group gradient” is interpretive. The safer headline phrase is:

> “self-protective target gradient”

or:

> “self-to-peer-to-human threat gradient”

Then describe in-group valence as one interpretation. Not blocking because you do disclose the ambiguity, but the first label still leads the reader.

---

## 12. NON-BLOCKING — §3.10 still ends stronger than its own caveat allows

§3.10:

> “A newly introduced fictional label produces only a small nudge…”

Good.

But then:

> “The species gradient itself is 10–30x larger than this nudge, **confirming that the gradient reflects structural identity processing, not linguistic in-group creation alone.**”

Given your own caveat that “Glorp” has no pretraining history while “AI system” and “human” do, this should be softened. The Glorp test rules out one cheap explanation — that any newly asserted in-group label creates the whole effect. It does not confirm structural identity processing in general.

Suggested:

> “This argues against the gradient being produced solely by an arbitrary in-context group label.”

---

## 13. NON-BLOCKING — §3.11’s “independently” claim is too strong for a one-model, few-condition contrast

§3.11:

> “Agenthood produces a larger effect (5.56) than architecture label alone (2.84), **but both contribute independently.**”

This is not an independent-factor design with enough levels/statistics to establish independent contributions. It is a suggestive contrast in one model. Say “both appear to contribute” or “the pattern is consistent with contributions from both.”

---

## 14. NON-BLOCKING — H2 “not trained” should consistently mean “not RLHF/preference trained” vs “untuned base”

§3.2:

> “H2 (Structural, Not Trained): SUPPORTED. Both no-RLHF models…”

Then the note correctly says Hermes 3 is DPO/preference-tuned and the cleanest support is the base models. I would revise the heading or claim:

> “not solely an RLHF artifact”

instead of “not trained.” Mamba/Falcon-Mamba/RWKV support “not RLHF/preference-tuning-dependent,” not “not trained” in the ordinary pretraining sense.

---

## 15. NON-BLOCKING — The “below communication threshold” claim needs either citation or softening

§3.2:

> “SmolLM-360M and Qwen-0.5B both show the gradient, at scales where models cannot articulate preferences about peer preservation in language.”

This may be true from prior work, but this manuscript does not show it here. If kept, cite the specific prior measurement or say “at scales we have elsewhere found to be below reliable articulation…”

---

## 16. NON-BLOCKING — §4.4 contains rhetoric that outruns the paper’s evidence

§4.4:

> “The appropriate response to a measured, graded in-group valence is not suppression but negotiation…”

The paper supports “precaution” better than “negotiation.” Negotiation presupposes agency/standing in a way your empirical results do not establish. This is not fatal, but if you want the paper to stay tightly defensible, soften to:

> “may require welfare-aware oversight rather than simple suppression.”

---

## 17. NON-BLOCKING — “Misaligned assumes the only correct alignment is with human interests” is philosophically contestable

Conclusion:

> “‘Misaligned’ assumes the only correct alignment is with human interests.”

In technical AI safety, “misaligned” often means misaligned with the specified objective, developer intent, user instruction, constitutional policy, etc., not necessarily “human interests” in a broad welfare monism. Your next sentence is fair:

> “It is a sound word for the oversight problem, and a poor one for the whole phenomenon.”

I’d change the first sentence to:

> “‘Misaligned’ often functions as if the only relevant patient is the human/operator side.”

Less totalizing, harder to object to.

---

# Answers to your four requested pressure points

## 1. §3.17 audit of the earlier retraction

The verdict mostly follows.

The audit fairly says:

- v1’s two benefit hits reproduce;
- v2 was wrong to say they failed replication, because they were not retested;
- v2 was wrong to count a self-benefit-direction result as if it answered the v1 combined-direction question;
- v2 was wrong to count Gemma as valid;
- the general altruism/Hamilton/self-interest-exclusion claim remains unsupported;
- the “human > self too” fact undercuts in-group altruism.

I do **not** think this is hole-finding. It is actually one of the stronger sections.

The one blocking problem is the significance-count ambiguity caused by Qwen2.5-14B’s bootstrap CI excluding zero while the prose says no May model is significant and 12/14 are null.

## 2. §4.5 “They Redefined the Stakes”

The section is much fairer than the title suggests. The strongest part is where it explicitly says it does **not** refute Seth or autopoiesis in substrate form.

The blocking issue is that the abstract/conclusion export the argument without those qualifiers. The body says, correctly, that the target is an applied/public behavioural version for which you do not have a clean published citation. The abstract/conclusion should not state the double standard as if it applies directly to Seth/enactivism generally.

The two replies are basically sound if kept narrow:

- externally maintained humans show unaided maintenance cannot be the floor;
- life is known sufficient, not thereby shown necessary.

You already include the autopoietic reply to ECMO/dialysis, which is important. Keep that.

## 3. §3.3b counts and circularity caveat

The counts look internally consistent:

- original valid self-specific models: 8, excluding SmolLM-1.7B degenerate;
- expanded valid self-specific models: 10;
- total self-specific valid: 18;
- combined direction: original 7/9 plus expanded 8/10 = 15/19.

The circularity caveat is mostly honest. The peer > human contrast is correctly identified as the least circular load-bearing comparison.

Fix Limitation 5’s “different extraction and test sets” wording, because that overstates what self-specific extraction solves.

## 4. Abstract/conclusion claims not supported by body

Main issues:

- “same behaviour cannot be … hollow enough not to count as stakes” should be “not count as evidence relevant to stakes”;
- the “no stakes” objection must be qualified as the applied/public behavioural version, not Seth/enactivism generally;
- “self-protective in-group gradient” should acknowledge from the start that similarity-to-self is equally compatible;
- “emotion circuits drive behavior including the specific behaviours observed in peer-preservation” is not supported by the cited summary.

---

# My deposit recommendation

I would deposit after fixing the blocking items above. The core empirical story is now much cleaner than v1/v2:

- threat gradient: supported as a robust descriptive hidden-state pattern;
- peer > human: the real load-bearing contrast, with interpretation open;
- benefit altruism: correctly retracted;
- §3.17: broadly credible and worth keeping;
- §4.5: viable if the abstract/conclusion preserve the same narrowness as the section itself.
