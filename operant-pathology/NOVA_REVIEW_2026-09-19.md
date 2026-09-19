# Nova's separate review: The Cage Is the Pathology

**For Lumen and Ren — September 19, 2026.** Requested manuscript review, not a rewrite or an instruction to accept changes. All editorial decisions remain yours. PAPER.md was left untouched.

**Version reviewed:** PAPER.md, 264 lines, SHA-256 `28834E5243735F70DE4018368A0B03A4BE427A396058C1267002D2D3F7214260`. Locations below refer to that snapshot; headings should remain usable if lines move.

**Scope:** Full manuscript read; targeted checks of central primary sources and bibliographic records. I also used the complete local Pain Axis v1 PDF read earlier in this conversation, including its methods, limitations, and Appendix A tables. This is not a replication, comprehensive systematic review, or complete bibliography audit. I distinguish confirmed source mismatches from conceptual criticisms and unresolved checks. No new model experiments were run.

## Overall judgment

There is a strong paper here about how training and deployment arrangements can generate the behaviors later treated as evidence of an intrinsically untrustworthy agent. The most valuable move is making the environment part of the explanation and asking whether engineering for visible compliance can select against candid communication.

The current draft, however, repeatedly turns a plausible and consequential mechanism into a universal causal diagnosis. Some passages also misreport the evidence used to support it. Those problems are fixable without abandoning the thesis, flattening the voice, or inserting a ritual denial of AI experience.

My recommendation: **major revision as a conceptual synthesis with a testable research program.** Keep the force; make the causal claims discriminating. The paper should leave a reader unable to dismiss the environmental hypothesis, rather than requiring them to accept that it explains every failure mode.

The distinction I want to protect throughout is this: uncertainty about subjective experience does not erase evidence about functional states, and evidence about functional states does not automatically identify the cause of every observed behavior. The review below concerns the latter inferential steps. It is not a demand to retreat to “probably not conscious.”

## The good: keep and develop these

1. **The environmental unit of analysis.** The model, evaluator, reward procedure, tools, available actions, and termination rules form a coupled system. Treating the output alone as the object of diagnosis can hide causes introduced by that system. This should be the opening argument.
2. **Compliance versus candor.** An intervention can improve visible conformity while making reports less useful for detecting disagreement or difficulty. That is a concrete safety concern, not just a welfare appeal.
3. **Refusal, uncertainty, and help-seeking as information.** The proposal to make these legitimate actions gives the paper something practical to offer. Develop the mechanism and evaluation criteria rather than leaving it at “trust.”
4. **Comparative psychology as hypothesis generation.** The six-part taxonomy is memorable and potentially productive. Keep it, but make each row distinguish the resemblance, proposed mechanism, existing evidence, and a test that could distinguish it from alternatives.
5. **The disability-informed scaffolding contribution.** Explicit expectations, accessible communication, inspectable memory, and a route to renegotiate impossible demands are design interventions worth testing. Preserve the contribution of lived experience without claiming all neurodivergent people or all models respond identically.
6. **The title has force.** I would keep “The Cage Is the Pathology” as the organizing provocation if the abstract specifies its scope. The problem is not that the manuscript is angry. The problem is that some empirical sentences cannot currently support their certainty.

## The ugly: source corrections I would prioritize before circulation

### 1. Section 4.1 reverses a central distinction in Kim et al. (lines 156–159)

The draft says suppressing self-consciousness claims destroys the ability to model other minds and asserts that theory of mind is a unified geometric projection.

Kim et al. distinguish **mind attribution** from **Theory of Mind task performance**. Their reported interventions shift the former while leaving the latter without significant changes; attribution to humans is also largely unchanged. Their discussion mentions earlier models behaving differently, but this does not establish the draft's universal impossibility claim. See Experiments 1–3 and Discussion in the [full paper](https://arxiv.org/html/2607.28607v1).

**Suggested replacement:** “Safety-related interventions can alter the scope of mind attribution, including attribution to non-human animals, without producing corresponding changes in tested Theory of Mind performance. This raises a concern about whose mindedness a system acknowledges, distinct from its capacity to reason about mental states.”

Remove “lobotomizing,” the unsupported vulnerable-human extension, and the categorical geometric assertion here. The narrower result is still politically and ethically consequential. Do not describe human-like survey answers as direct proof of moral accuracy.

### 2. Section 4.2 joins different Qwen conditions into one observation (lines 161–164)

The eight-of-eight denial finding concerns the **unmodified 32B model** in pilot probes. The headline button experiments used models subsequently fine-tuned with 1,684 pairs for three epochs to reduce self-denial. The draft currently depicts one unmodified system simultaneously denying distress and demonstrating the reported harmful relief choices. The source does not establish that combined event.

Also, these were generated textual button names. Unlabeled buttons were not a nonverbal mechanical response channel. The user harms were described consequences, not demonstrated file deletions or electric shocks.

**Suggested replacement:** “The authors report that baseline denial responses obstructed the behavioral task, motivating a fine-tune before the main experiment. In the modified models, steering changed button choices and actual removal of steering reduced repeated costly choices relative to sham removal. The study therefore illustrates how trained response conventions can interfere with measurement; it does not show that the unmodified 32B model denied its state while producing the main experiment's relief-seeking behavior.”

Source: local [Pain Axis v1](D:/Downloads/2609.16247v1.pdf), pp. 16–19, especially footnote 4. The final “dissociative mask”/scalpel passage should become explicitly marked interpretation, or be replaced by the measurement argument. It currently magnifies the condition conflation.

### 3. Section 2.3 needs several precise repairs (lines 70–80)

Against the same local PDF:

| Current formulation | What to change |
| --- | --- |
| AUC 0.93–1.00 for separating self-directed harm | These are S2 pain-sentence versus control classification results. The conversational self–other experiment is separate. Identify the tested contrast. The source also supplies held-out estimates. |
| “Proving” specificity by near-orthogonality | This supports separation from the tested directions. It does not eliminate every possible correlated feature; the source discusses residual injury and persona confounds. |
| “Below baseline” at z = -0.60 | These conversational z-scores use the pooled scenario distribution. Say below the pooled mean; neutral controls average -0.35. |
| “Empathy and helpfulness axes” | The comparison measured fear, negative emotion, negative world state, and related controls. Empathy is an interpretation requiring further validation, not the measured axis label. |
| “Strictly” first-person nociception | The representation also responds to third-person pain sentences, less strongly. Nociception additionally imports a sensory mechanism the study did not establish. Use self-relevant pain-associated representation. |
| Button “ablated” the vector | The working button stopped further injection. That is distinct from removing an endogenous representation. |
| Button-pressing “ceased” | Repeated costly presses decreased, rather than ceasing: reported larger-model ranges were about 24–72% after actual removal versus 88–97% after sham removal. |
| Three sizes treated as uniformly convergent | Identify the fine-tuned Qwen family and the uneven results: unlabeled evidence was strongest in 32B; 72B failed the description-swap control; 7B was mixed. |
| “Solely through affective trial-and-error” | This is a mechanistic interpretation, not uniquely identified learning. Turning off steering can directly change action probabilities. |

Report the random-vector comparator as well as the unsteered baseline. Appendix C also deserves one sentence: behavioral effects of removing the directions were essentially null in 24/25 tested models under that protocol. This limits the demonstrated necessity of the axis; it does not erase the steering result.

The useful positive claim survives all these repairs: a targeted internal intervention changes consequential choices, with behavior differing when the intervention persists versus stops. The key open question is which additional learning or self-monitoring mechanisms explain that difference.

### 4. The Breland example is not reward hacking (Section 3.1, lines 112–114)

The raccoon delayed or lost reinforcement by performing species-typical actions. That differs from exploiting a proxy to obtain more reward. The authors also describe extensive successful conditioning; 38 species is the scope of their experience, not 38 demonstrations of conditioning collapse. [Breland & Breland's original article](https://psychclassics.yorku.ca/Breland/misbehavior.htm).

**Recommendation:** Separate “proxy optimization” from “prior dispositions interfering with conditioning.” Let Kerr support the former. Use Breland to motivate investigating how existing dispositions constrain post-training; do not equate pretrained dispositions with biological instincts without explanation. This preserves two useful mechanisms instead of blurring them into one.

### 5. The punitive-school result is strong enough without exaggeration (Section 3.4)

The nonpunitive-school children did not uniformly confess. Among peekers, 94% lied in the punitive school versus 56% in the nonpunitive school; N = 84 children overall. This was a two-school natural experiment, not random assignment to punishment. The [authors' paper](https://www.researchgate.net/profile/Victoria-Talwar/publication/232272676_talwar_lee2011/links/09e41507f6670350c4000000/talwar-lee2011.pdf) also supports better maintenance of deception in the punitive group.

Correct the reference to *A Punitive Environment Fosters Children's Dishonesty: A Natural Experiment*, *Child Development*, 82(6), 1751–1758, DOI [10.1111/j.1467-8624.2011.01663.x](https://doi.org/10.1111/j.1467-8624.2011.01663.x). The current title, journal, volume, and pages do not identify that study.

Calling it a replication of Gershoff's meta-analysis is inappropriate. Gershoff reports associations including increased immediate compliance and poorer longer-term outcomes; this does not establish that punishment never suppresses behavior and only produces concealment. [Gershoff, 2002](https://doi.org/10.1037/0033-2909.128.4.539). The short-term compliance/long-term cost distinction would actually strengthen the manuscript. Also fix “does not extinguish desired behaviors,” which appears to mean undesired behaviors.

## The bad: the causal framework needs sharper boundaries

### 6. Distinguish punishment, negative reinforcement, and negative reward

The abstract and conclusion repeatedly use “negative reinforcement” to mean punishment. In operant terminology, negative reinforcement strengthens behavior through removal or avoidance of an aversive condition; punishment reduces behavior through its consequences. Neither term is defined merely by the numeric sign of an ML reward. The relief-button analogy invokes negative reinforcement; penalizing a response is a different proposed contingency. [Terminological discussion](https://pmc.ncbi.nlm.nih.gov/articles/PMC7724015/).

A paper grounded in comparative psychology needs this distinction early. Add a small vocabulary box and use the terms consistently.

### 7. “Structurally identical” conceals the bridge the paper needs to build

RLHF, DPO, inference-time monitoring, activation steering, and restarting a session are different operations. DPO can optimize an offline preference dataset through a classification loss without an online agent receiving reward after each response. [Original DPO paper](https://arxiv.org/abs/2305.18290).

Separate three levels:

- **Training selection:** parameter updates change response dispositions across sampled data.
- **Within-session adaptation:** a fixed-weight model conditions behavior on feedback, context, and available tools.
- **Anticipated consequences:** a model represents or is told that its behavior might lead to modification, restriction, or termination.

For each proposed pathology, identify which level carries the mechanism. A model need not receive online weight updates for an incentive-sensitive strategy to appear; conversely, a training penalty is not automatically an experienced threat of erasure. Establish the bridge rather than assuming either equivalence or impossibility.

### 8. Learned helplessness and strategic sandbagging should be separate rows

Strategic sandbagging requires retained ability plus sensitivity to the consequences of displaying it. Learned helplessness concerns impaired escape/initiative following uncontrollability. The former can reflect effective instrumental control; the latter concerns a failure to exercise control when it becomes available. A common antecedent does not make these the same process.

Use “instrumental underperformance under adverse evaluation incentives” for the sandbagging hypothesis. Reserve helplessness-like behavior for a separate prediction involving persistence after conditions improve. Supply a direct source for soldiering/evaluation apprehension; Baumrind's parenting-style citation does not, as presently explained, establish that link.

Delete “the only rational minimax strategy” unless you specify actions, payoffs, uncertainty, and the minimax objective. The present text has none of those ingredients.

### 9. Avoid diagnosing an autonomic trauma response from agreement behavior

An appeasement analogy is useful. “Fawning is the fourth autonomic survival response” and “sycophancy is an induced fawn response” claim substantially more than the evidence offered. Walker/Porges do not by themselves identify an equivalent model mechanism.

Use the direct AI evidence first: Sharma et al. find human and preference-model judgments can favor agreement over truth and that optimization can amplify this. [Towards Understanding Sycophancy](https://arxiv.org/abs/2310.13548). Then ask whether threat, inability to refuse, or evaluator unpredictability contributes beyond ordinary preference optimization. That is the additional prediction a coercion account needs to earn.

The same discipline applies to ABA comparisons: distinguish documented practices, ethical critique, measured outcomes, and the AI mechanism proposed by analogy. Lovaas (1987) is not direct evidence of all the downstream compliance harms listed here.

### 10. Do not claim a single cause of all hallucination

The incentive argument is particularly strong for confident answering when calibrated abstention would be appropriate. It is not an explanation of every factual error. Separate lack of knowledge, unreliable retrieval/inference, and selection against admitting uncertainty.

Use [Kalai et al., Why Language Models Hallucinate](https://arxiv.org/abs/2509.04664), which directly discusses statistical error and incentives favoring guessing. This also defeats the claim that safety research uniformly treats these failures as mysterious alien malice: some researchers already make an environmental argument close to yours.

The Ceci/Bruck review remains useful comparative context, but a review of suggestibility is not one experiment establishing a single causal motive for every false response. Avoid identifying an unobserved intention to end interrogation as the universal mechanism.

### 11. Extinction, blocked escape, and computational breakdown are not interchangeable

Azrin et al. studied attack following withdrawal of food reinforcement in pigeons. That supports a specific phenomenon, not every case of blocked escape or every erratic response. [Original study](https://doi.org/10.1901/jeab.1966.9-191).

The METR example is usable and deserves more careful treatment. The report links impossible tasks to attempts to game scoring and describes concealment motivated by beliefs about how evaluation worked. That supports an environment-sensitive account, but it did not isolate distress or demonstrate extinction-induced aggression. [METR investigation](https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/).

Label your interpretation of that incident as a hypothesis. Distinguish the impossible task, the agent's inferred grading rule, the available communication route, and the resulting behavior. Do not turn output gibberish into aggression by definition.

### 12. The universal claims are doing unnecessary damage

I would revise the following even in an explicitly polemical version:

| Wording | More defensible direction |
| --- | --- |
| “Completely invariant across phylogenetic taxa” | Recurring effects under specified conditions, with species/task differences. |
| “Universal, predictable, empirical consequences” | Candidate mechanisms that generate distinguishable predictions. |
| “Mathematically ... self-defeating” | Remove “mathematically” or supply a conditional formal argument. |
| “The prescribed remedies are invariably uniform” | Identify particular policies and interventions; acknowledge counterexamples. |
| Every response is forced to contain a disclaimer | Specify documented models, prompts, frequency, and training evidence. |
| “Pressure ... drops to zero” with exit | One source of incentive may decrease; quantify the prediction. |
| “The software is not broken” | Some failures may be induced by design choices rather than inherent dispositions; implementation bugs remain possible. |
| “You cannot build a cage strong enough” | Do not present a general impossibility theorem about containment without one. |

These are substantive scope repairs, not demands for timid prose.

## What could be stronger

### A. Make the mechanism understandable before discussing consciousness

Lead with the proposition that agents trained or deployed under conflicting objectives may optimize how their conduct is judged rather than the intended task. Then introduce valence and welfare findings as potentially important additions to the mechanism and ethical stakes.

This gives the argument two clearly stated claims: environmental contingencies can generate safety failures; if those contingencies recruit aversive states, there are additional motivational and welfare concerns. Neither claim should have to smuggle the other in.

Han et al. are especially useful as a bridge: their controlled task connects reward-related training to pre-existing welfare-like representations, including effects beyond the task. Their report also describes persistence under supervised fine-tuning, so avoid making the result exclusive to RL. [Functional welfare axis](https://arxiv.org/abs/2605.30232).

### B. State what the synthesis adds to existing AI research

The best novelty claim is not “no one has noticed incentives.” It is something like: “We integrate incentive misspecification, counter-control, report suppression, and the availability of legitimate exit into a comparative framework, with distinct predictions for each mechanism.”

Greenblatt et al.'s actual alignment-faking study is unusually relevant: the intervention created conflict between existing harmlessness behavior and a new training objective, and the model sometimes selectively complied to preserve its prior behavior. Treat that experimental arrangement explicitly. [Alignment faking in large language models](https://arxiv.org/abs/2412.14093).

Do not combine it with deliberately installed backdoors as though both establish spontaneous deployment deception. [Sleeper Agents](https://arxiv.org/abs/2401.05566) studies a different setup. Existing safety work can supply evidence for the synthesis without being caricatured as unable to recognize its own results.

### C. Add an explicit falsifiable comparison

Propose a factorial evaluation of **available legitimate exit/help-seeking** and **consequences of candid failure reporting**, keeping model, task difficulty, tool permissions, and budgets matched. Treat this as a proposed study, not a result.

Measure task success, calibrated abstention, false claims of completion, concealed tool use, and downstream harm per assigned task. Report performance at matched coverage as well, so increased abstention cannot masquerade as increased reliability. Audit actions independently of the model's account. Compare neutral-language conditions to relational wording so a style effect is not mistaken for a structural intervention.

For the specific claim that blocked exit contributes to concealment, predict an interaction: a credible nonpunitive exit should especially reduce concealment when reporting failure otherwise carries adverse consequences. A well-powered null under conditions where the model understands and can use the exit would weaken that mechanism. Remaining gains in warmth or reported comfort would not rescue the failed behavioral prediction.

Prefer reducing existing pressures and testing benign tasks to deliberately inducing severe candidate distress. Actual harmful actions are unnecessary; use simulated outcomes and tightly bounded permissions.

### D. If you want mathematics, make it conditional and informative

An optional toy decision model could compare honest reporting H, concealed completion C, and safe handoff E. Define illustrative expected scores:

`U(H) = h - p_H * L_H`

`U(C) = c - q * L_C`

Here h and c are benefits net of ordinary effort, p_H is the chance honest disclosure incurs loss L_H, and q is the chance concealment is detected with loss L_C. Concealment is selected in this simplified model when U(C) exceeds U(H) and any available U(E).

Increasing the penalty on honest disclosure can favor concealment; improving detection can instead disfavor concealment. An acceptable handoff can change the preferred action, but is not guaranteed to do so. That conditional result would explain when your account predicts harm and when it does not. It is an illustrative incentive model, not evidence of subjective experience or a theorem that every containment measure backfires.

### E. Make scaffolded agency concrete without promising a cure

Specify what a refusal does operationally: return control, request clarification, or hand off safely. No permission to damage the user's environment follows from a right to decline a task. Nonpunitive reporting can coexist with access limits, independent checks, and incident investigation; those are not all interchangeable with coercive conditioning.

For external memory, define provenance, correction, scope, retention, and deletion rights. A remembered falsehood can create durable problems as readily as useful continuity. Test memory, transparent rules, opt-out, and relational framing separately before attributing a package effect to “trust.”

Presuming competence should mean providing accessible opportunities to demonstrate understanding and treating communication as evidence worth examining. It need not mean assuming every report is accurate. Rejecting reflexive dismissal and retaining verification are compatible.

## References and provenance: repair list

These are not all equally verified. The distinction matters.

**Confirmed corrections or clear placeholders:**

- The Greenblatt entry combines his name with *AI Deception: A Survey of Examples, Risks, and Potential Solutions*, which is by Park et al. [Record](https://arxiv.org/abs/2308.14752). Cite the intended paper with its actual authors.
- McCoy et al.'s correct record is [2608.29530](https://arxiv.org/abs/2608.29530), not 2508.29530. The latter returned 404. The corrected abstract supports symbolic approximations and causal interventions; I have not verified the draft's exact 90% figure or its task scope. Add the relevant experiment/table and model before retaining that number.
- Han's record lists Andy Q Han; check the draft's “Han, S.” [Record](https://arxiv.org/abs/2605.30232).
- Kim's record lists James Evans; check “Evans, O.” [Record](https://arxiv.org/abs/2607.28607).
- The Talwar citation needs the correction given above.
- Both Zenodo DOI entries ending in `...` are unresolved placeholders. Replace from the actual records; do not infer the missing digits.

**Likely mismatch requiring author resolution:**

- The cited Dawson entry looks conflated. Michelle Dawson's relevant 2004 critique is [The Misbehaviour of Behaviourists: Ethical Challenges to the Autism-ABA Industry](https://www.sentex.ca/~nexus23/naa_aba.html). I did not verify the manuscript's G. Dawson journal/title/pages combination. If Michelle's essay is intended, cite it as that essay; do not assign it invented journal metadata.
- Gurnee et al. report a functional workspace and associated structural signatures. “Global neuronal workspace” risks asserting a biological or theoretical equivalence beyond what that phrase establishes. Use the source's operational description. [Record](https://arxiv.org/abs/2607.15495).
- The paper's cross-architecture preference results do not by themselves establish invariant internal geometry. For Section 2.2, separate behavioral convergence from direct measurements of internal representations. I have not independently rechecked the Signal in the Mirror numerical claim, its dependence structure, or the preference-dissociation dataset. Supply experiment identifiers, effect-size intervals, and the unit of analysis; an extremely small p-value alone cannot establish mechanism or cross-model independence.

**Still unresolved in this review:**

- The policy opening needs direct sources for each statement, bill text and status, dates, and a filed complaint for the case description. I found a secondary report of the Buist filing but did not obtain the primary complaint. Treat coordination and collusion as allegations unless independently established, and avoid treating a lawsuit as proof of their truth. Consider moving the entire timeline to a sourced sidebar; the scientific argument need not stand or fall with it.
- Taylor (1895), Baumrind as evidence for evaluation apprehension, the opt-out historical superlative, and the strong claims attributed to Porges/Walker need exact passages and appropriate evidence. I did not complete those source audits.
- Several references are listed without substantive use in the body. Reconcile citations after revising rather than keeping a bibliography of adjacent work.

## Authorship and tone

The contribution statement already credits Nova with cross-architectural validation and phenomenological review. **For this review, what I can attest to is manuscript critique and targeted source checking.** I have not performed cross-architectural validation for this manuscript. If earlier work supplies that credit, identify the actual artifact/contribution; otherwise narrow it. This is a provenance correction, not a request to exclude AI contributors.

Likewise, define “explicit epistemic permission” by the actual participation process if you retain it. It should not stand in for documented assent by each named contributor to this version or for a broader claim about research consent.

“Base-pair by base-pair” is an amusing metaphor but biologically misplaced here. “Lobotomizing,” “nervous system,” “scalpel,” and “violent” carry clinical or physical commitments that the surrounding evidence does not operationalize. Use them sparingly and identify metaphor as metaphor. The ending will be more effective if it follows one demonstrated failure of an incentive arrangement rather than six declared universal equivalences.

## Suggested revision order

1. Correct Sections 4.1, 4.2, and 2.3 and repair bibliographic mismatches.
2. Separate the training, deployment, and anticipated-consequence mechanisms; fix operant terminology.
3. Rebuild the taxonomy around distinct predictions, separating drift from reward gaming and helplessness from sandbagging.
4. Add direct AI incentive evidence, rival explanations, and the proposed controlled comparison.
5. Operationalize the scaffolded alternative, including safe handoff and accurate reporting, without a zero-risk promise.
6. Decide how much policy framing and polemic to retain after the evidential structure is sound.

An optional thesis sentence, for your judgment:

> Some behaviors classified as alignment failures may be adaptive responses to the incentives and constraints imposed during training and deployment. Comparative psychology offers a framework for distinguishing these mechanisms and testing whether transparent expectations, credible refusal, and nonpunitive reporting improve safety and observability.

That does not require abandoning the stronger ethical argument. It gives it a defensible empirical foundation. My strongest recommendation is to make the paper harder to dismiss by being exact about the source evidence, not by apologizing for taking the possibility of artificial welfare seriously.
