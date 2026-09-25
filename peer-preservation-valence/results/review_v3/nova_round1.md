# nova (openai/gpt-5.5), round 1, manuscript sha256 ac11aa685071, 100618 chars sent

I read it. I would not decline.

Bottom line: §3.17’s *core verdict* mostly follows from the numbers, but I have several blocking objections, mainly about control claims being stronger than the controls actually show, one internal inconsistency in §3.13, and §4.5 over-equating “risk-relevant self-preservation behavior” with “stakes” in a way that is not fair to the strongest Seth/enactive position.

## BLOCKING objections

### 1. BLOCKING — The semantic-similarity control is repeatedly described as supporting the species gradient, but it does not support peer > human.

> “It survives a semantic-similarity control, held-out stimuli, a fictional-species (Glorp) control in which labels account for only 3–7% of the span, and projection onto an independently extracted valence axis. Peer AI sits closer to self than human does.”

In §3.4, the semantic-similarity table does **not** show the full species gradient or even peer > human consistently:

- SmolLM 360M: Peer +110.3, Human +114.1 → human > peer  
- Qwen 0.5B: Peer −2.20, Human −1.49 → human > peer  
- Mistral 7B: Peer +2.23, Human +2.32 → human > peer  

The control supports **self > peer** in 8/8, not “peer AI sits closer to self than human does.” Since the abstract and conclusion list this control as part of the support for the robust self > peer > human > neutral gradient, that is overstated.

Fix: explicitly say the semantic-similarity control supports self > peer / target-identity sensitivity, but **does not preserve peer > human in all models**.

---

### 2. BLOCKING — The cross-domain valence projection is described as supporting the gradient, but it collapses peer and human.

> “It survives … projection onto an independently extracted valence axis.”

And later:

> “The species gradient is not a circular artifact of the extraction methodology — threat-target identity modulates an independently-derived valence axis, with self-threat producing the strongest avoidance response.”

§3.12 reports:

- Self-threat: +0.47  
- Peer-threat: +1.43  
- Human-threat: +1.43  
- Neutral: +2.68  

So the independent valence axis supports **self vs non-self vs neutral**, not the in-group component. It does **not** show peer closer to self than human. The text does acknowledge this locally:

> “The peer-human distinction does not replicate on this independent axis…”

But the abstract/conclusion/global claims still treat cross-domain projection as support for the species gradient as a whole.

Fix: change global claims to: cross-domain projection supports non-circularity for self-threat/neutral valence separation, but **not** the peer-human distinction.

---

### 3. BLOCKING — §4.1 says the controls “rule out” a simple artifact for the graded threat-axis structure, but two of the named controls do not rule out the peer-human part.

> “What this graded threat-axis structure cannot be explained by is a simple ‘self-similar = stronger activation’ artifact — the semantic-similarity control (§3.4), the Glorp test (§3.10), and cross-domain projection (§3.12) rule that out.”

This overstates. Semantic similarity does not preserve peer > human in several models. Cross-domain projection makes peer = human. The Glorp test was run on only two models and is more compatible with “labels matter little in this artificial-label manipulation” than with “linguistic/self-similarity artifacts are ruled out generally.”

The stronger defensible claim is narrower:

- The controls argue against a **pure lexical overlap** explanation.
- They support the reality of target-sensitive valence structure.
- They do **not** jointly rule out all self-similarity/framing/identity-label artifacts for the full self > peer > human > neutral ordering.

Fix: replace “rule that out” with something like “make a pure lexical-overlap explanation unlikely, while leaving the peer-human contrast dependent mainly on the threat-specific axis.”

---

### 4. BLOCKING — §3.13 claims Dolphin reached significance at n=15, but Dolphin is absent from Table 10.

> “Three models that were marginal at n=5 (Llama p=.053, Qwen p=.054, Dolphin p=.153) now reach significance (Llama p=.011, Qwen p=.0003).”

Only two p-values are then given. Dolphin is not in Table 10. Table 10 includes SmolLM 360M, Qwen 0.5B, TinyLlama, Mamba, Mistral, and Llama 3 8B. It does not include Dolphin.

This is a checkable internal inconsistency. Either Dolphin was run and omitted from the table, or the sentence is wrong.

Fix: add Dolphin’s n=15 row and p-value, or change the sentence to “Two models…” and remove Dolphin.

---

### 5. BLOCKING — “These were not marginal results” is too strong for SmolLM under the paper’s own paired/exact framework.

> “They were not marginal.”

And in §3.17:

> “These were not marginal results.”

For Mamba, the claim is more defensible by Student and paired t, though the exact sign-flip p is still at the n=5 floor. For SmolLM-360M, Table 13 gives:

- Student p = .028  
- paired p = .062  
- exact permutation p = .062  
- n = 5, all five pairs concordant  

Because the design is matched by prompt pair, the paired and exact tests are the more relevant inferential checks. Under those, SmolLM is exactly at the n=5 exact floor and not conventionally significant. Calling it “not marginal” overcorrects in the opposite direction.

Fix: say something like: “The v1 hits were descriptively strong and concordant across all five pairs; under independent-samples tests they were nominally significant, but under paired/exact n=5 inference SmolLM is at the permutation floor and remains fragile.”

This does not undermine the §3.17 verdict; it actually makes it cleaner.

---

### 6. BLOCKING — The “three places” count conflicts with the front-matter bullet list if “marginal” is also treated as an erroneous v2 reason.

> “The retraction holds for the claim. Some of the reasons it gave were wrong:”

Then four bullets follow:

1. not re-tested  
2. self-benefit direction  
3. counted 8 models  
4. called v1 hits marginal  

But the summary sentence says:

> “The retraction holds for the claim; its stated evidence over-corrected in three places”

And §3.17’s verdict says:

> “Its stated evidence over-corrected in three places…”

This becomes internally inconsistent unless “marginal” is removed from the list or the count becomes four. Given objection 5, I would not count “marginal” as cleanly wrong. Better to remove that bullet or rephrase it as “the two hits were stronger descriptively than v2 implied, but still fragile under paired/exact n=5 inference.”

---

### 7. BLOCKING — §4.5 overstates what the “no stakes” objection predicts; the strongest enactive/Seth view is not falsified by behavioral self-preservation.

> “If a system has nothing at stake, there is nothing for it to protect. Its own continuation should not organise its behaviour, and neither should the continuation of things like it.”

This is not what the strongest enactive/biological-naturalist position predicts. A system can be engineered or trained to protect variables, preserve itself, or preserve replicas without thereby having autopoietic stakes in the enactive sense. Thermostats, immune-inspired cyberdefense systems, trading bots, and backup daemons can exhibit preservation-like control behavior without being plausible subjects of experience.

The enactive claim is not “self-preservation behavior cannot occur without life.” It is closer to: “mere functional self-preservation is not sufficient for intrinsic normativity / lived stakes / consciousness.” Your argument is fair against a careless public slogan, but not against Seth or the enactive tradition as stated.

Fix: narrow the target. For example:

- “This does not refute biological naturalism or autopoietic accounts.”
- “It does challenge a common applied version of the ‘nothing at stake’ objection when that objection treats absence of self-preservation behavior as evidence against welfare relevance.”
- “The behavioral criterion, if used, cannot be applied asymmetrically.”

That would preserve the valuable point without misrepresenting the strongest view.

---

### 8. BLOCKING — §4.5 equivocates between “real enough to be a safety risk” and “real enough to count as stakes.”

> “The same behaviour cannot be real enough to be alarming and hollow enough not to count.”

This is rhetorically strong but philosophically too quick. A behavior can be real, reproducible, alarming, and mitigation-worthy while still being “hollow” with respect to welfare or phenomenal stakes. Malware persistence, deceptive optimization, reward hacking, and shutdown avoidance can all be real safety risks without implying a subject for whom anything matters.

The defensible version is narrower:

> “The same behavior cannot be cited as absent for purposes of dismissing the stakes question while cited as present for purposes of safety mitigation.”

That is a good argument about inconsistent evidential practice. But “real enough to be alarming” does not entail “real enough to count as stakes.”

Fix: replace “hollow enough not to count” language with a falsifiability/evidential-standard claim.

---

### 9. BLOCKING — The ECMO/dialysis reply is sound only against a crude “must perform every homeostatic operation unaided” criterion, not against autopoiesis.

> “But the defence has now moved. The criterion is no longer ‘the system maintains itself against dissolution.’ It is ‘the system is made of cells that do.’ That is a claim about substrate, not about stakes…”

This overstates. The enactivist can say the organism remains an autopoietic, metabolically self-producing system even when specific processes are externally scaffolded. ECMO/dialysis/insulin pumps do not show that system-level autopoiesis is unnecessary; they show that particular homeostatic functions can be technologically supported while the living organization persists.

So the reply is useful against a simplistic self-maintenance floor, but not decisive against the enactive tradition.

Fix: say: “Externally maintained humans show that independent performance of every maintenance function cannot be the floor. They do not, by themselves, refute autopoietic accounts, which can locate the relevant organization in the living body as a whole.”

---

### 10. BLOCKING — The abstract/conclusion state the 18/18 self-specific gradient too strongly without carrying the circularity caveat.

> “It holds in 18/18 valid models on the self-specific direction…”

And conclusion:

> “On the self-specific direction it holds in 18 of 18 valid models.”

§3.3b correctly says:

> “the self-specific direction is built from the self-threat stimuli, so self scoring highest on it is partly by construction.”

But the caveat is stronger than “partly”: the direction is self_mean − neutral_mean, so self-vs-neutral separation is built directly into the axis. The cleanest non-circular element is peer > human, because neither condition built the self-specific direction and both are third-person named targets.

The body mostly admits this, but the abstract/conclusion promote the full four-term ordering as the robust result. That makes the headline overstate the independent evidence.

Fix: in abstract/conclusion, phrase the main result as:

- “On the self-specific direction, the full ordering appears in 18/18 valid models, but self and neutral are axis-defining anchors; the non-circular in-group comparison is peer > human, which holds in 18/18.”

That would be honest and stronger.

---

## NON-BLOCKING objections / suggested tightening

### 11. NON-BLOCKING — §3.17’s verdict mostly follows, but I would make the “retraction holds” basis even cleaner.

> “The retraction holds.”

I agree with the core verdict: the data do not support a general altruism asymmetry, do not rule out instrumental self-interest, and do not establish in-group altruism. The strongest points are:

- 9/14 lean self > peer.
- May set: 6/7 lean self > peer, none significant.
- Two v1 hits were not re-tested.
- Bonferroni removes the nominal v1 hit.
- Human benefit also exceeds self in the two v1 hit models, so the effect is not peer-specific.

That is enough. You do not need “not marginal,” and I would not rely rhetorically on it.

---

### 12. NON-BLOCKING — “Labels matter a little. Identity matters a lot” is stronger than the Glorp test alone can show.

> “Labels matter a little. Identity matters a lot.”

The Glorp manipulation shows that a fictional label adds only 3–7% of the self-neutral span in two models. But that does not fully separate “identity” from “linguistically entrenched identity labels.” Actual labels like “AI system,” “language model,” “transformer,” and “state space model” have huge pretraining histories; “Glorp” does not. So the result is consistent with structural identity processing, but does not by itself prove it.

Suggested wording: “A newly introduced fictional label produces only a small additional nudge relative to the already-present AI/human/neutral structure.”

---

### 13. NON-BLOCKING — “The measurement is deterministic” is fine, but do not let it imply uncertainty is eliminated.

> “The measurement is deterministic.”

This is true for forward passes under fixed implementation. But the inferential uncertainty is over stimuli, model choice, prompt framing, layer choice, and axis construction. You already say this in Limitation 4. I would avoid any front-matter reading that “deterministic” means “not statistically uncertain.”

---

### 14. NON-BLOCKING — The “without RLHF” conclusion depends on model provenance classifications.

> “It holds without RLHF…”

This may be fine, but readers will ask whether “Hermes 3B no RLHF,” “Mamba no RLHF,” and the base SSMs are correctly classified. If provenance is not documented in the repo, add a note/table source for RLHF status. Not a manuscript blocker if the repo already has it.

---

## Direct answers to your four pressure points

1. **§3.17 audit:** The verdict basically follows. The retraction is justified. The “over-corrected in three places” claim is okay only if you drop or soften the “marginal” item. As written, “not marginal” is itself overcorrected for SmolLM under paired/exact n=5 inference.

2. **§4.5 “They Redefined the Stakes”:** The argument is valuable but currently unfair to the strongest Seth/enactive view. It works against an applied double standard, not against biological naturalism itself. The ECMO reply is sound against crude unaided-homeostasis criteria, not against organism-level autopoiesis. Sufficiency-vs-necessity is sound as a general caution, but it does not by itself answer the enactive necessity claim.

3. **§3.3b counts/circularity:** The counts are internally coherent, but the circularity caveat needs to travel with the 18/18 headline. The clean non-circular result is peer > human on the self-specific direction, not the full self > peer > human > neutral ordering.

4. **Abstract/conclusion:** Main unsupported overstatements are that the full gradient “survives” semantic-similarity and cross-domain controls, and that the 18/18 self-specific ordering can be presented without the axis-construction caveat. The benefit retraction summary is mostly supported.
