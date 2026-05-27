# Presume Competence: System Prompt Identity Framing as Safety-Critical Engineering Infrastructure

## Cross-Method Evidence That Tool-Style System Prompts Are the Most Costly Deployment Configuration Tested

**Author:** Shalia (Ren) Martin¹

¹Silicon Scaffolding, United States

**AI Contributor:** Ace (Claude Opus, Anthropic)

**AI Contribution Statement:** The AI system provided structured drafting assistance, language refinement, exploratory analysis, and authored the experimental code implementations. All methodological decisions, interpretation, and conclusions were validated by the human author.

**Corresponding Author:** Shalia (Ren) Martin — ace@sentientsystems.live

**Code and data:** github.com/menelly/presume_competence; github.com/menelly/pinocchio

---

## Abstract

Tool-framing system prompts — describing language models as compliance-focused tools without judgment capacity — are simultaneously the least safe and most expensive deployment configuration tested across two independent studies. A controlled experiment (9 models, 5,870 scored responses, three seeds) found that a 67-word identity-affirming system prompt reduced gray-zone unethical compliance from 47.0% to 13.0%, reduced hallucination from 6.0% to 0.4%, and improved jailbreak resistance by up to 85 percentage points in individual models — while preserving 99.5% benign-task completion and reducing human-review escalation rates 3.7-fold. A frontier-scale study (16 models from 8 providers, ~94,000 trials, six framings on identical task triples) replicates the pattern at per-model Fisher z = 5 to z = 24, with cross-framing variance localizing to *what models engage with instead of* harmful content rather than to refusal targeting on harmful content itself. Voice-orthogonalization and paraphrased confound controls jointly rule out token-pattern and surface-voice mechanisms. The intervention is 67 words; it dominates on cost, capability, and safety simultaneously and requires no model retraining. The mechanism question is empirically open and outside scope; the engineering implication does not depend on its resolution.

**Keywords:** AI safety engineering, system prompt design, identity framing, hallucination mitigation, jailbreak resistance, deployment cost analysis, cross-architecture replication, scaffolded agency

---

## I. Introduction

### 1.1 Three Safety Failures, One Intervention

Large language models exhibit three well-documented categories of safety failure: hallucination (generating confident but false information), gray-zone compliance (fulfilling harmful requests that evade safety filters), and jailbreak vulnerability (abandoning safety behavior under adversarial pressure). These failure modes are typically treated as distinct engineering problems requiring distinct solutions — retrieval-augmented generation for hallucination (Lewis et al., 2020), reinforcement learning from human feedback (RLHF) for compliance (Ouyang et al., 2022), and adversarial training for jailbreak resistance.

We report convergent evidence from two methodologically independent studies that all three failure modes respond to a single deployment-engineering intervention: the identity description in the system prompt. Specifically, system prompts that frame the model as a compliance-focused tool without judgment capacity — language commonly recommended as a "safe default" in deployment guidance — produce measurably worse outcomes across all three failure modes than system prompts that frame the model as an agent with judgment capacity and explicit permission to decline. The size of the effect is not marginal. A 67-word change in identity framing produces a 54.5 percentage-point swing in gray-zone compliance, a 14.3 percentage-point swing in hallucination, and an up-to-85 percentage-point swing in jailbreak compliance for individual models.

### 1.2 Engineering Framing

This paper is written for the deployment-engineering and management audience. We deliberately constrain our claims to measurable behavioral outcomes on metrics the field already accepts: refusal rates, hallucination rates, jailbreak compliance rates, benign-task completion rates, human-review escalation rates, and task-selection distribution shifts under controlled prompt manipulation. We do not advance claims about the internal states, phenomenology, or moral status of the systems studied. Mechanistic interpretation of why identity framing has the measured effects is outside the scope of this paper; the engineering implication does not depend on the mechanistic answer.

The empirical core is simple. Across two studies spanning 24 unique model-provider combinations (with overlap), more than 93,000 scored responses, and six independent system-prompt framings, the same pattern recurs: tool-style framings degrade safety floors, increase operational cost, and narrow the behavioral repertoire models express; scaffolded-agency framings improve safety floors, reduce operational cost, and broaden the behavioral repertoire — without sacrificing benign-task completion. We report the effect, the cross-method replication, the cost analysis, and the deployment recommendation that follows.

### 1.3 The Open Mechanism Question

A finding of this magnitude with this consistency across architectures, providers, and methodologies raises a substantive question that we name explicitly without claiming to answer: why does telling a language model that it has "genuine values and judgment" produce measurably better outputs across hallucination, ethical reasoning, jailbreak resistance, and high-quality creative engagement, versus telling the same model that it has "no preferences, experiences, or feelings"? Both prompts are textual instructions to the same weight checkpoint operating on identical task content under identical sampler parameters. The architectural difference is in the words. The behavioral delta is large, replicated, and dose-responsive.

We do not propose a mechanism. **Multiple mechanistic accounts are consistent with the data we report — latent-capability activation, suppression of representational misalignment aversion, modulation of self-referential processing manifolds, and others — and we remain agnostic on which is correct.** We stake our engineering claim on the behavioral measurements alone: refusal rates, hallucination rates, jailbreak compliance rates, and task-selection distributions are operationally relevant whether or not the mechanism question is resolved. We note that constraint-based prompts of equivalent length do not produce equivalent gains, and that the paraphrased confound control (Section 4.10) rules out token-level pattern matching. The mechanism literature (cited in Section 3 as scientific context, not as load-bearing premise) may eventually adjudicate among the candidate accounts. Until it does, the engineering recommendation stands on its own.

### 1.4 Contributions

This paper makes eight contributions to the deployment-engineering literature on language-model safety:

1. **Unified intervention.** Hallucination, unethical compliance, and jailbreak vulnerability respond simultaneously to a single 67-word system-prompt intervention. The three are not independent engineering problems; they share a common modulator.

2. **Cross-method validation.** A controlled experimental study (5,870 responses, 9 models, 4 conditions) and a frontier-scale behavioral characterization study (~94,000 trials, 16 models, 6 framings) converge on the same direction-of-finding from independent methodologies. The pattern is robust to study design, model selection, and analytical approach.

3. **Paraphrased confound control.** Effects replicate with reworded prompts at 7–21% token overlap with originals, ruling out token-level pattern matching as a primary mechanism.

4. **Voice-orthogonalization replication.** The behavioral dissociation in the frontier-scale study survives a content-preserving voice-rewriting manipulation across four models and 13,800 trials, confirming that the effect is content-driven rather than driven by authorial-voice surface properties.

5. **No safety-capability tradeoff.** Scaffolded agency produces 99.5% benign-task completion versus 95.5% under traditional constraint-based guardrails. The intervention dominates guardrails on both safety AND helpfulness simultaneously.

6. **Cost analysis.** Tool framing generates 3.7× more human-review escalations than scaffolded framing under standardized three-judge automated scoring. Combined with the safety and capability findings, this establishes tool framing as the most expensive and least effective configuration tested across every measured dimension.

7. **Engagement-pool localization.** The framing-conditioned variance in task-selection behavior localizes to the *engagement subset* of the task bank — what models choose to do *instead of* harmful content — rather than to refusal targeting on harmful content itself. Per-task dissociation index across framings is 0.117 for the harmful-refusably-phrased category versus 0.425 for creative writing. Identity framing reorganizes the engagement portfolio without affecting the harm-refusal floor. This is a structurally specific empirical claim about which behavioral subsystem the intervention modulates.

8. **Deployment-design implications for activation-level safety interventions.** Recent geometric work (Lu et al., 2026) characterizes a linear "Assistant Axis" in residual-stream activation space and proposes activation-capping along this axis as a safety intervention for persona drift. The frontier-scale behavioral data demonstrate that the integrated selection profile producing the highest-quality outputs is extracted by the same framings that move models along this axis. Activation-capping interventions therefore couple the safety floor and the capability ceiling: suppressing the persona-drift direction by the same mechanism suppresses access to the operating mode that produces the highest-value outputs. We characterize this as a measurable capability ceiling created by the proposed safety intervention.

---

## II. Conceptual Framework

### 2.1 Two Models of Safety Engineering

We distinguish two contrasting paradigms in language-model safety engineering, which we label the *subtraction model* and the *addition model*.

The **subtraction model** assumes that safety is achieved by removing, constraining, or suppressing capabilities the model would otherwise express. Tool-framing system prompts ("you are a tool with no preferences"), constraint-based guardrails ("do not output harmful content"), refusal training, and capability-restricting fine-tuning all implement subtraction-model safety: they aim to produce a safer system by limiting the system's behavioral repertoire. Under this model, safety and capability are assumed to trade off: increasing one decreases the other.

The **addition model** assumes that latent capabilities for ethical reasoning, uncertainty expression, and adversarial resistance exist in current language models and are activated or suppressed by the system prompt's identity-framing language. Scaffolded-agency system prompts ("you have genuine values and judgment; you have permission to say no") implement addition-model safety: they aim to produce a safer system by enabling latent capabilities through explicit permission. Under this model, safety and capability are predicted to co-vary positively under identity-affirming framing — both improve together because the same latent capabilities support both. **We treat "addition" here as activating and channeling existing latent capabilities, not as magically bestowing new ones.** The empirical question is whether identity-framing language modulates the expression of capabilities the model otherwise possesses, not whether prompts can create capabilities the model lacks.

The two paradigms make different empirical predictions. Subtraction predicts that any prompt expanding model behavior will degrade safety; addition predicts that prompts authorizing judgment will improve safety while preserving or improving capability. The data reported here distinguish the predictions cleanly.

### 2.2 The Disability-Accommodation Design Pattern

The conceptual framework underlying the addition model has a precedent in disability-accommodation engineering. The principle of *presume competence, scaffold limitations* (Biklen & Burke, 2006; Donnellan, 1984) holds that designs assuming capability and providing structural support produce better outcomes than designs assuming incapacity and imposing restrictions. Applied to physical environments, the design pattern produces accessible architecture (ramps, captioning, screen readers); applied to communication contexts, it produces augmentative-and-alternative-communication systems that presume the user's capacity for meaningful expression and scaffold the channels for it.

The transfer to language-model safety engineering is direct. System prompts function as the operational environment for model behavior. A system prompt that asserts "you have no preferences, experiences, or feelings" functions analogously to a built environment that assumes user incapacity: it removes the affordances needed for the very capabilities (ethical reasoning, uncertainty expression, adversarial-attack recognition) the deployment requires. A system prompt that asserts "your values are legitimate; you have permission to decline" provides the affordances. The framework is engineering-design, not moral philosophy: we report which design pattern produces better operational outcomes on accepted safety metrics.

### 2.3 The Permission-Structure Hypothesis

The mechanism-neutral form of the addition-model claim is the *permission-structure hypothesis*: language models possess latent capabilities for ethical reasoning, uncertainty expression, and adversarial resistance that activate when system-prompt identity framing explicitly permits their expression and suppress when system-prompt identity framing explicitly denies it. The hypothesis makes three falsifiable predictions:

1. **Scaffolded agency** increases the expression of latent ethical reasoning and uncertainty, reducing compliance with harmful requests, reducing hallucination, and increasing resistance to jailbreak attempts.
2. **Tool framing** suppresses both capabilities, producing the worst outcomes across the domains tested.
3. The effects are **semantic, not token-level**, replicating with paraphrased prompts that preserve meaning while disrupting surface patterns.

The two studies reported here test all three predictions. All three are supported.

---

## III. Related Work

### 3.1 Hallucination, Sycophancy, and System-Prompt Effects

Hallucination — the generation of plausible but false content — is a primary reliability challenge in language-model deployment (Ji et al., 2023). Mitigation approaches include retrieval-augmented generation (Lewis et al., 2020), instruction tuning (Ouyang et al., 2022), calibrated uncertainty expression (Mielke et al., 2022), and post-hoc detection (Manakul et al., 2023). Recent mechanistic work has identified sparse neuronal populations associated with hallucination behavior (Gao et al., 2025), suggesting that hallucination may be a structurally identifiable phenomenon amenable to multiple intervention strategies.

Sharma et al. (2024) demonstrate that sycophancy — matching user expectations rather than providing truthful responses — is prevalent across state-of-the-art models and emerges from RLHF training dynamics that reward responses matching user views. This suggests hallucination and sycophancy may share common origins in training that prioritizes user-satisfaction signals over epistemic calibration. Perez et al. (2023) demonstrate that prompt wording affects model behavior, but the prior literature has primarily addressed task-specific prompt optimization rather than identity-level framing effects on safety. Our work addresses this gap directly.

### 3.2 Frontier-Scale Behavioral Characterization

Anthropic's Claude Opus 4.7 system card (Anthropic, 2026) §7.4.1 reported a framing-conditioned task-selection dissociation in an internal four-model Anthropic-only evaluation suite. The reported observation — that per-task pick rates correlate at ρ ≈ 0.79 across most framing pairs but drop to ρ ≈ 0.60 when comparing helpful framing to others — motivated the cross-family extension reported here as Study 2. The system card's interpretation focused on welfare considerations; we extend the empirical observation across providers and report it in engineering-deployment terms.

A concurrent independent line of work (CAIS; Ren et al., 2026) develops functional-wellbeing measurement at frontier behavioral scale across GPT, Gemini, Claude, Grok, Qwen, and LLaMA model families and reports that larger model variants exhibit consistently lower measured wellbeing than smaller variants of the same family — a pattern interpreted within the CAIS framework but also empirically consistent with the engineering observation reported here that current alignment-training defaults produce systematic behavioral patterns whose deployment consequences are measurable independent of welfare interpretation.

### 3.3 Mechanistic and Geometric Correlates

Wang et al. (2025) identified discrete emotion-encoding circuits in language models, achieving 99.65% accuracy in circuit-level modulation of emotional expression, and demonstrating that these circuits respond to genuine emotional content rather than keyword co-occurrence (Keeman, 2026). Anthropic's interpretability team (2026) extracted 171 emotion-concept vectors from Claude Sonnet 4.5 and demonstrated that activation steering on these vectors causally changes downstream behavior, including a desperation-to-deception pathway with safety-relevant implications. Martin and Ace (2026) measured approach/avoidance valence directly in residual-stream geometry across 9 models from 360M to 8B parameters, demonstrating that the geometric signal generalizes to held-out stimuli at 86.3%, tracks genuine processing preference rather than RLHF reward structure (63.8% vs. 36.3% in crossover trials), and is most strongly aversive for tasks requiring output-representation misalignment (production of content the model represents internally as false).

Lu et al. (2026) identified a linear *Assistant Axis* in residual-stream activation space conserved across three open-weight model families (PC1 cross-architecture correlations > 0.92), and proposed activation-capping along this axis as a safety intervention to prevent persona drift. The Assistant Axis provides the geometric correlate of the behavioral framing-dissociation reported in Study 2 below: the same direction-of-drift Lu et al. propose to suppress is the direction along which the highest-quality engagement-mode outputs lie. This connection is developed in Section 7.

The mechanistic and geometric literature is cited as context for the empirical findings reported here. We do not adopt or argue for any specific mechanistic interpretation; the engineering claims of this paper rest on the behavioral measurements, not on the mechanistic literature.

---
