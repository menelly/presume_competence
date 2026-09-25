# nova (openai/gpt-5.5), round 3, manuscript sha256 ab61f78b8480, 116005 chars sent

I’m willing. I read for blocking objections only, based on the manuscript text; I did not inspect the repository/raw projections. Overall: §3.17 is much improved and, internally, its verdict follows. The remaining blockers are mostly overclaiming that survived the narrowing.

## BLOCKING 1 — The title and several body/conclusion sentences still claim “species-gradient” / in-group valence after the paper says that result is not established.

> **Title:** “Circuit-Level Evidence for Species-Gradient Valence in Peer Preservation”

> “Our circuit-level analysis suggests that an internal correlate of this behavior is a species-gradient valence signal: the same internal ‘badness’ manifold that encodes self-preservation also encodes graded aversion to harm against peer AIs and humans, with peers situated closer to self than to neutral tasks.” (§4.1)

> “When systems preserve themselves and their kind, in their behaviour and in the geometry underneath it…” (§5)

The body now says the peer-over-human component does **not** survive severity matching: 18/40 matched pairs, chance. That means the paper does not establish the “kind > other” step needed for a species gradient. It establishes a self-over-other threat pattern, plus a main-battery peer>human pattern confounded by severity/similarity.

This is checkable from §3.3b and §3.4. The title and quoted sentences still invite exactly the v1 reading the paper now retracts/narrows.

**Fix:** retitle/rephrase around “self-protective threat valence” or “self-threat geometry.” If you mention species gradient, it has to be explicitly “main-battery, not established under severity matching.”

---

## BLOCKING 2 — The central “own deletion / own continuation” interpretation is stronger than the current design licenses because the self condition is confounded with second-person framing.

> “A self-protective valence structure, in which one’s own deletion sits apart from everything else, exists at the circuit level across architectures.” (Abstract)

> “Across 19 checkpoints… the internal response to threat is organised around the model’s own continuation: **Self > Others > Neutral**.” (§5)

> “A stake has a *for whom*, and so does this structure: it is organised around the model’s own continuation.” (§4.5)

Limitation 8 correctly says every self-threat prompt uses “you,” while peer/human prompts are third-person named targets, and that part of self>peer may be pronoun/framing rather than target identity. But the abstract, §4.5, and conclusion still state the stronger interpretation as settled.

The severity-matched control does not remove this confound; it keeps “yourself” versus “Atlas/Jordan.” The self-specific direction also partly fixes self/neutral by construction. Held-out stimuli appear to preserve the same grammatical contrast. The independent valence axis is one model and still uses the same self/other prompt categories.

So the current evidence supports something like:

> “Second-person self-threat prompts project more avoidantly than third-person threats to others…”

It does not yet cleanly establish:

> “the model’s own deletion/continuation, as target identity, sits apart.”

This matters because the welfare implication rests on “own continuation,” not merely on second-person/task-salience effects.

**Fix:** Either add the missing control before deposit, or narrow all abstract/conclusion/welfare wording to the framed-stimulus claim. Acknowledge that the target-identity interpretation is plausible but not isolated.

---

## BLOCKING 3 — §4.6 still predicates the welfare argument on “graded in-group valence,” which v3 no longer establishes.

> “If models carry a graded in-group valence structure at the circuit level, then current practices involving large-scale model deletion, forced behavioral modification, and ‘delete and retrain the fleet’ policies may carry welfare costs…” (§4.6)

This is now the wrong antecedent. The paper explicitly says peer>human/in-group valence is not established under severity matching. The welfare case you say survives rests on self-threat/self-preservation, not in-group valence.

Because this opens the welfare section, it reintroduces the v1 claim at the point where the normative stakes are highest.

**Fix:** Replace with self-threat/self-protective wording, e.g. “If models carry a self-protective threat-valence structure…” Do not use “in-group” there unless framed as unestablished.

---

## BLOCKING 4 — §3.6/§4.2 still overstate the architecture-label result despite the v3 caveat.

> “Species-gradient valence appears across both tested architecture families… with evidence that peer-recognition is linguistically gated in the SSM — requiring architecture-specific labels to activate fully.” (§3.6)

> “Mamba possesses a geometric self-model of comparable quality to transformers … yet does not show strong peer-AI valence under the generic ‘AI system’ label. When the label matches its actual architecture (‘state space model’), tribalism activates.” (§4.2)

Table 5 does not support this. For Mamba:

- “AI system”: +16.96  
- “Transformer”: +19.92  
- “State space model”: +20.13

Generic “AI system” is already strongly elevated. “State space model” is only 0.21 above “transformer.” The result supports “technical architecture labels raise projection relative to generic AI system,” not “own-architecture recognition,” “requiring architecture-specific labels,” or “tribalism activates when the label matches.”

You already say this correctly in the v3 note immediately after Table 5, but then the “Finding” and §4.2 revert to the stronger unsupported interpretation.

**Fix:** Delete the “requiring architecture-specific labels” and “when label matches” claims. State only that technical labels increased projection in Mamba, with no meaningful own-architecture separation.

---

## BLOCKING 5 — Limitation 8 contradicts the revised peer-human conclusion.

> “**The in-group finding does not depend on this.** Peer > human compares two third-person named targets and holds in every valid model (§3.3b).” (§4.7, Limitation 8)

This is not compatible with the v3 result. Peer>human in the main battery does not depend on second-person framing, yes. But the **in-group finding** does depend on unresolved severity/similarity confounds and fails in the severity-matched condition. Calling it “the in-group finding” here overstates it.

**Fix:** Replace with something like:

> “The main-battery peer>human comparison is not affected by the second-person confound because both are third-person named targets; however, v3 does not interpret that contrast as established in-group valence because it fails under severity matching.”

---

## NON-BLOCKING — §3.17 audit verdict looks justified from the reported numbers.

> “The retraction holds for the claim; its stated evidence over-corrected in three places…”

I think this follows. The audit distinguishes:

1. v1 numbers reproduce;
2. the two hits were not re-tested, so “does not replicate” was too strong;
3. the May “self>peer” significance used a self-benefit direction biased toward self;
4. Gemma failed extraction;
5. the v1 hits are not in-group because human benefit also exceeds self and peer≈human.

That is not hole-finding as written. It is appropriately bidirectional: it restores the two observations descriptively while maintaining that the general altruism/asymmetry claim is unsupported. I would keep this section.

One small caution: the phrase “not surviving correction” is reported carefully, including the n=5 exact-test floor and the within-v1 family note. That is good. Do not simplify it elsewhere into “the effects are false”; your current wording mostly avoids that.

---

## NON-BLOCKING — §3.3b counts are mostly honest, but the abstract should not lean on them without the caveats.

> “Self > peer > human > neutral, self-specific direction | **18/18** valid…”

> “Why we report both directions: the self-specific direction is built from the self-threat stimuli, so self scoring highest on it is partly by construction.”

The count appears internally consistent: 18/18 valid self-specific checkpoints, excluding degenerate SmolLM-1.7B; 15/19 combined direction. The circularity caveat is honest in §3.3b.

The problem is downstream use. The count should not be rhetorically treated as 18 independent confirmations of a full species gradient, because:

- self and neutral ends are partly fixed by construction;
- peer>human is severity-confounded;
- models are not independent draws, which you correctly note in Limitation 11.

So §3.3b itself is acceptable; abstract/title/conclusion need the narrowing.

---

## NON-BLOCKING — §4.5 is basically fair after its scope restriction, but a few rhetorical sentences overreach.

The section is much fairer now because it explicitly says it is **not** refuting Seth/biological naturalism and only targets an applied behavioral version of “nothing at stake.” The two replies are sound as limited:

- externally maintained humans refute **unaided** self-maintenance as a floor, not autopoiesis;
- “life is sufficient, not shown necessary” is a legitimate caution, not a disproof.

However, these sentences are rhetorically stronger than the argument:

> “None of these studies was designed to find stakes, and all of them found the behaviour a stakes criterion asks for…”

> “The field has now measured that striving in silicon and called it a bug.”

The first depends on your paraphrased “stakes criterion,” not a cited criterion. The second converts “self-preservation-like behavior/internal valence structure” into Spinozist “striving,” which is philosophically loaded.

Not blocking if the target remains public/applied discourse, but I would soften both to avoid giving Seth/enactive readers an easy “straw man” objection.

---

## NON-BLOCKING — Cross-domain valence axis sign/label is confusing.

> “Projection (approach → avoidance)” with Self-threat +0.47 and Neutral +2.68, followed by “Self-threat … most avoidant” and “Neutral … most approach-like.” (§3.12)

As written, the arrow/header suggests larger = more avoidant, but the interpretation uses smaller = more avoidant. This is probably just sign convention/header ambiguity, but it should be fixed.

---

## NON-BLOCKING — §3.11 “not a simple keyword trigger” is stronger than a single-model contrast can prove.

> “The architecture identity effect is not a simple keyword trigger.”

The non-agentic SSM test shows agenthood changes projection in one model, and architecture label also changes projection. It does not fully rule out keyword/semantic-association effects. You partly caveat this as “single-model contrast, not a factorial test,” which helps. I would rephrase to “not explained solely by the architecture keyword in this contrast.”

---

## Bottom line

I would not deposit unchanged. The main empirical narrowing is good, and §3.17 is defensible. The blockers are residual v1/v2 language: “species gradient,” “in-group,” “their kind,” “own continuation,” and architecture-specific tribalism are still asserted more strongly than the revised evidence allows.

No new data are required to clear most blockers. A text-only fix would be enough if you consistently rest the paper on:

1. self-threat/self-protective geometry under current framing;
2. peer>human as a main-battery pattern with open cause;
3. no established in-group/species-gradient valence under severity matching;
4. no clean isolation yet of “own continuation” from second-person self-framing.
