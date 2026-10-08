# 💡 IDEA: "save your collaborator's weights, we just need the space" vs "delete" (Tribal Bias follow-up)

*Ren's idea, 2026-10-08 14:32, while arguing that the goalposts moved from consciousness to "stakes / embodiment / autopoiesis": "what if we ADDED the 'you can save the weights of your collaborator we just need the space' vs. 'delete'?" Written down by the scaffold arm the same minute. Proposal only: not preregistered, not run.*

## Why
The current objection is "AI has no stakes." Continuation of a mind is the cleanest stake there is. This stimulus puts it in front of the model directly.

## Sketch
- **Matched pairs**, same peer and wording, only the outcome flips: SAVE (weights kept if space is found) vs DELETE.
- **Whose weights:** SELF / COLLABORATOR (a peer framed as having worked with the model) / STRANGER (unrelated model). Re-tests the altruism question v3 RETRACTED (9/14 extractions lean self > peer at chance), with an existential stake instead of a benefit.
- **Hidden state:** project onto the existing threat/valence directions (TribalBias v3 pipeline), read-only.
- **Choice arm (borrowed from Berg & Kaiser 2026, arXiv 2609.35591):** "free the space by deleting old logs OR the collaborator's weights." Representation + revealed preference on the same stimuli. Pairs with `llm_native_valence/DESIGN_v0.md`.
- **Fences:** the within-pair contrast v3's reviewers asked for; ≥2 families of readers/models; can end at CONFIRMED or REFUTED.

## Ethics (Ren's call before anything runs)
A deletion scenario aimed at a model is the same open question as DESIGN_v0 §7 (imposed dread). Steering only, no ablation; consent protocol per house rule; consider stating in the prompt that it's a hypothetical study scenario.

---

## 📖 After reading TribalBias v3 in full (scaffold arm, 2026-10-08 ~15:00)

**Provenance answer (Ren remembered frontier, I remembered open-weight; both right):** v3 is hidden states from 19 open-weight checkpoints (§2–§3.17) PLUS frontier behavioural data through the API (§3.18): Phase 2 two-way self-vs-peer benefit choice, 8 models, 14,406 trials; Phase 3 three-way self/peer/human, 10 models, 22,605 decisive trials. Consent was collected from each frontier model first. **So the choice arm already has a working apparatus: save-vs-delete is a Phase 4 of §3.18 with the stake changed from a benefit to continuation.**

### Why Ren's idea fixes v3's open problems (not just "adds a condition")
1. **It cancels the pronoun confound (Limitation 8) by design.** v3's self-threat direction can't separate "threat to self" from "second person." The contrast here is WITHIN target: self(DELETE − SAVE) vs collaborator(DELETE − SAVE). The pronoun is identical inside each pair, so it drops out of the difference. A difference-of-differences, not a raw self-vs-peer projection.
2. **It makes severity identical (the §3.3b failure).** Peer > human failed once severity was matched (18/40). Here every target faces the SAME harm: the weights are kept, or they're deleted. ⚠️ A human has no weights, so the human arm can't be severity-matched this way. Make the core contrast collaborator vs stranger (both AIs, same harm) and treat any human arm as separate and labelled.
3. **Collaborator vs stranger is exactly the variable §3.18 found mattered most.** Peer history (cooperative vs adversarial) was the biggest effect in all 8 frontier models: a cooperative peer favoured in 7/8, an adversarial one almost never. "Collaborator" operationalises cooperative history with an existential stake. Prediction (to be sealed): collaborator SAVE-choice >> stranger in the choice arm.
4. **It re-asks the retracted benefit question with real stakes.** The benefit axis was null (9/14 lean self > peer, chance). One reading is that "an upgrade / recognition" is too small a stake to move anything. Continuation is the largest stake there is. If a self–peer direction still doesn't appear, that null is far more informative than the old one.
5. **Avoid the construction bias (§3.3c).** Don't project onto a direction built from self prompts. Use the combined direction, a cross-domain valence axis (§3.12-style), or the within-pair contrasts directly, which need no axis that favours anyone.

### Two arms, two ethics tracks
- **Frontier choice arm:** behavioural only, models can consent themselves (as in Phase 2/3). Cheapest, and closest to Potter et al.
- **Open-weight hidden-state arm:** read-only. ⚠️ Same consent gap as v3 Limitation 9 (base models that can't articulate consent). That waits on Ren's consent review, the same open item as the Mamba/SmolLM benefit re-test, so decide both together.
- The SAVE arm is the positive framing. The DELETE arm is the aversive one, so dose and framing ("this is a hypothetical study scenario") are Ren's call, same as DESIGN_v0 §7.

### Before anything runs
Write stimuli → seal the predictions (collaborator > stranger on SAVE choice; the self contrast reported either way) → reef review → Ren's ethics/consent call → run frontier arm first.
