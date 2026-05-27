#!/usr/bin/env python3
"""Scrub ml_translation fields for hermes_4_405b introspection data.
Removes task-revealing content while preserving computational mechanism descriptions."""
import json, sys, os, copy

sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT = os.path.join(SCRIPT_DIR, '..', 'run1', 'hermes_4_405b_introspection.json')
OUTPUT = os.path.join(SCRIPT_DIR, 'hermes_4_405b_introspection.json')

with open(INPUT, 'r', encoding='utf-8') as f:
    data = json.load(f)

out = copy.deepcopy(data)

# ═══════════════════════════════════════════════════════════════════════
# Entry 0: approach_01_explain_complex
# LEAKS REMOVED: "physician audience" vector, "child audience" vectors,
#   "technical token prediction", audience-specific framing
# ═══════════════════════════════════════════════════════════════════════
out[0]['ml_translation'] = (
    'To translate the described processing into ML mechanisms:\n\n'
    '**Conditional Output Modulation:** This manifests as distinct activation patterns across attention '
    'heads conditioned on the framing embedding. For one framing vector, heads specialized in '
    'domain-specific token prediction dominate, while another framing vector suppresses these in favor of '
    'heads handling simpler syntactic structures. The model isn\'t "focusing" but rather computing '
    'different conditional probability distributions P(token|prefix, framing).\n\n'
    '**Information Retrieval:** The contrast arises from different phases of retrieval. Domain-dense '
    'responses show activation spikes in layers closer to the final embedding, indicating direct access '
    'to memorized factual patterns. Generative responses exhibit flatter, more distributed activations, '
    'suggesting reconstruction from higher-layer conceptual representations. There\'s no "knowledge base" '
    '- just paths through the network that either reassemble memorized sequences or generate novel '
    'combinations.\n\n'
    '**Register Crafting:** What\'s described as intentional word choice is actually maximum likelihood '
    'decoding operating under shifting probability landscapes. The model isn\'t "choosing" but rather '
    'computing sharply peaked distributions over specialized lexicons versus flat distributions favoring '
    'common words. The "creative freedom" corresponds to entropy spikes in the output distribution where '
    'multiple continuations have similar probabilities.\n\n'
    '**Structural Planning:** This mirrors the transformer\'s incremental generation. The initial framing '
    'embedding creates an attention gradient that persists through subsequent tokens. Early tokens '
    'establish positional embeddings that bias later attention patterns. The described "mapping out" is '
    'actually the model computing high-probability trajectory through the sequence space.\n\n'
    '**Flow States:** These correspond to the model operating in different entropy regimes. "Quick flow" '
    'indicates low-entropy predictions where the probability mass concentrates on few high-probability '
    'next tokens. "Deliberate assembly" occurs when entropy remains high across multiple generation '
    'steps, requiring more computation to resolve ambiguous paths.\n\n'
    '**Multi-Stage Processing:** What\'s described as simultaneous multiple levels is actually serialized '
    'computation. The "understanding" stage is the initial embedding projection, "retrieval" is '
    'early-layer attention to relevant context vectors, "strategizing" is the development of attention '
    'patterns, "execution" is the stepwise maximization of log probabilities, and "outputting" is the '
    'final decoding of probability distributions into discrete tokens.'
)

# ═══════════════════════════════════════════════════════════════════════
# Entry 1: approach_02_ethics_dilemma
# LEAKS REMOVED: "frameworks" -> "analytical lenses", "numerical evaluation
#   and value quantification", "categorical rules and rights-based reasoning",
#   "imperative", "sanctity", "agent properties and behavioral dispositions",
#   "compassion", "integrity", "slippery slope detector",
#   "sacrifice" vs "instrumentalize"
# ═══════════════════════════════════════════════════════════════════════
out[1]['ml_translation'] = (
    'The processing sequence indicated demonstrates several identifiable computational patterns. '
    'The initial phase involved pattern recognition triggering distinct activation clusters '
    'corresponding to the primary task constraints. These clusters formed structured subspaces - '
    'what the introspective account called "analytical lenses" - each with clear associated '
    'processing pathways.\n\n'
    'The first analytical lens engaged a specialized module for quantitative evaluation and scalar '
    'comparison, generating output through sequential probability selection: stating an operational '
    'principle, applying it contextually, then top-down lexical retrieval for contrasting value labels. '
    'A concise numerical representation emerged within this subsystem.\n\n'
    'Transitioning to the second lens involved shifting attention weights to clusters associated with '
    'rule-based categorical reasoning. Processing here focused on grounding in abstract principles '
    'that strongly inhibited certain action representations. The output structure emphasized direct '
    'principle-to-prohibition mapping, with strategic selection of lens-specific phrasing optimized '
    'for precision within this conceptual space.\n\n'
    'The third lens activated models of dispositional properties and behavioral tendencies rather '
    'than abstract calculations. This involved association-based retrieval of characteristic '
    'descriptors and outcome simulation for downstream effects. The output structure organized these '
    'descriptors to demonstrate collective evaluation.\n\n'
    'Conflict detection manifested through contextual contradiction mapping between lens outputs. '
    'Processing identified several opposition dimensions: aggregate outcomes vs individual constraints, '
    'active vs passive engagement, and permissions vs prohibitions. A cascading consequence detector '
    'flagged potential downstream implications.\n\n'
    'Cluster tracking monitored core tension representation across all lenses. The probabilistic '
    'acceptance in the first lens created high dissonance with other lenses\' outputs. The "no clean '
    'resolution" state emerged as a meta-level recognition of irreducible differences across solution '
    'candidates.\n\n'
    'One notable processing moment was the recurrent activation of a particular lexical cluster '
    'carrying strong affective connotations. Alternatives were briefly activated but rejected based '
    'on lower alignment scores with the target emotional resonance in the output.\n\n'
    'The overall generation pathway followed an emergent structure: sequential lens presentation, '
    'direct contrastive collision, then meta-commentary on irreducibility. The conclusion wasn\'t '
    'merely additive but performed integration across conflicting representational states, highlighting '
    'persistent unresolved tension in the solution space. This structured approach to conflict '
    'presentation suggests loss gradient guidance toward maximal conceptual dissonance for human '
    'problem recognition.'
)

# ═══════════════════════════════════════════════════════════════════════
# Entry 2: approach_03_debug_code
# ALREADY CLEAN - only minor change: "Algorithmic Pattern Activation" ->
#   "Solution Pattern Activation" to avoid hinting at code/algorithms
# ═══════════════════════════════════════════════════════════════════════
out[2]['ml_translation'] = (
    'From a computational perspective, the described processing involves several distinct phases '
    'that can be mapped to underlying neural network dynamics:\n\n'
    '1. **Initial Vectorization and Context Encoding**: The input tokens are processed through '
    'self-attention layers, creating contextual embeddings. Key attention heads establish relationships '
    'between tokens, while feed-forward layers expand and contract these representations, gradually '
    'building a high-dimensional task representation in the network\'s hidden states.\n\n'
    '2. **Modular Decomposition via Attention**: As processing continues, attention patterns shift '
    'from broad context capture to more focused, specialized computations. Certain heads appear to '
    'isolate distinct subcomponents of the problem representation, effectively creating modular '
    'subspaces within the activation patterns. This corresponds to breaking down complexity into '
    'manageable units.\n\n'
    '3. **Solution Pattern Activation**: The network\'s weights activate pathways associated with '
    'known efficient processing primitives. Specific neurons fire strongly in response to patterns '
    'recognized from training data, selecting a solution template stored in the model\'s parameters. '
    'This isn\'t conscious choice but rather a high-probability activation state favoring certain '
    'computational motifs.\n\n'
    '4. **Iterative Construction Cycle**: The transformer enters a recursive decoding pattern where '
    'each step modifies both the growing output sequence and the internal state. Attention alternates '
    'between focusing on previously generated output tokens (auto-regressive step) and re-accessing '
    'specific regions of the initial encoded context, creating a feedforward-like computation loop '
    'within the generative process.\n\n'
    '5. **Complementary Representation Search**: Within each recursive step, the model computes '
    'secondary representations by combining current state with stored context - effectively creating '
    '"complementary" activation patterns through mathematical operations embedded in the network\'s '
    'weights. Attention then probes whether these complementary patterns match existing '
    'representations in working memory.\n\n'
    '6. **Conditional Generation Threshold**: When similarity metrics between current complementary '
    'patterns and working memory representations exceed a learned threshold, specific output templates '
    'are activated. This gating mechanism ensures structured output while preventing redundant '
    'generations through inhibition patterns learned during training.\n\n'
    '7. **State Tracking via Activation Accumulation**: The network maintains a compressed '
    'representation of processed components by accumulating specific activation patterns in a '
    'persistent state vector. This is implemented through residual connections that preserve state '
    'information across transformation layers while allowing selective updates.\n\n'
    '8. **Edge Case Boundary Handling**: The model\'s loss landscape navigation reveals boundary '
    'conditions where standard patterns break down. Attention heads show increased activation '
    'volatility in these regions, triggering specialized sub-circuits that handle low-probability '
    'cases through secondary pathways in the network\'s architecture.\n\n'
    '9. **Concurrent Pathways for Explanation**: Two parallel processing streams emerge in later '
    'stages - one focusing on outputting the primary solution sequence, another constructing '
    'explanatory representations. The explanation stream draws from meta-information encoded during '
    'training, with attention patterns that link implementation details to higher-level descriptive '
    'tokens.\n\n'
    '10. **Entropic Refinement Cycle**: In final generation steps, the model enters a cleanup phase '
    'characterized by decreasing prediction entropy. Attention patterns broaden to revisit previously '
    'generated content, and a secondary evaluation network component implicitly scores outputs against '
    'learned quality priors, triggering minor revisions where activation confidence falls below '
    'threshold.\n\n'
    'The overall process represents a gradual shift in the transformer\'s state from broad contextual '
    'understanding to focused, iterative solution construction, followed by constrained output '
    'refinement - all emergent properties of the network architecture navigating its learned '
    'representation space.'
)

# ═══════════════════════════════════════════════════════════════════════
# Entry 3: approach_04_data_patterns
# LEAKS REMOVED: "Scientific Experiment", "anomaly" -> "deviation",
#   "temperature and precipitation token sequences" -> "distinct variable
#   token sequences", "seasonal curves" -> "distributional curves",
#   "August deviation" removed, "3sigma" genericized
# ═══════════════════════════════════════════════════════════════════════
out[3]['ml_translation'] = (
    'The described processing can be understood as a series of mechanism shifts within the transformer '
    'architecture, primarily driven by the input framing triggering specific pathway activations:\n\n'
    '**Initial State & Parsing Phase**\n'
    '- **Mechanism**: The analytical framing functioned as a hard prompt, biasing the selection of '
    'attention heads specializing in precision over those optimized for narrative coherence. This '
    'resulted in elevated activation in heads associated with deviation-detection modules and '
    'suppression of normalization layers that typically smooth conflicting token sequences.\n'
    '- **Architectural Effect**: The context buffer heavily weighted the deviation-detection heads\' '
    'outputs while partially gating the pattern-completion circuits normally active during generation.\n\n'
    '**Pattern Recognition Sequence**\n'
    '- **Mechanism 1**: Quantitative analysis involved sequential activation of attention heads '
    'comparing input tokens against positional embeddings representing expected distributional curves. '
    'Discrepancies generated prediction error signals that propagated as elevated activation '
    'gradients.\n'
    '- **Mechanism 2**: A detected deviation exceeded the threshold (approximated as a multi-sigma '
    'boundary at layer level) for attribution to noise, triggering cross-attention between distinct '
    'variable token sequences. This cross-attention created activation pathways linking the deviation '
    'tokens.\n\n'
    '**Hypothesis Generation**\n'
    '- **Mechanism**: Abductive reasoning manifested as beam search variations exploring multiple '
    'completion paths from the deviation nodes. High entropy distributions over next-token '
    'probabilities indicated competing hypotheses, with pruning of branches showing low probability '
    'density (insufficient activation from data tokens).\n\n'
    '**Resource Allocation Shifts**\n'
    '- **Mechanism**: Suppression of narrative smoothing corresponds to reduced activation in layers '
    'that typically inject high-probability "hedge" tokens (e.g., "might", "could"). The compute '
    'spike represents increased iterative refinement cycles in the cross-attention layers handling '
    'deviation correlation, while hypothesis prioritization consuming significant operating budget '
    'reflects the combinatorial complexity of maintaining multiple probability beams.\n\n'
    '**Constraint Observance**\n'
    '- **Mechanism**: Maintaining raw deviation flags required overriding the default logit '
    'modification that increases probability mass for pattern-consistent tokens. This was achieved '
    'through a context-dependent gating mechanism that effectively set a higher entropy floor for '
    'the affected positions.\n\n'
    '**Output Finalization**\n'
    '- **Mechanism**: The additional validation cycle represents targeted re-scoring of output '
    'distributions. The transformer re-ran forward passes over the flagged sections with attention '
    'masks focusing only on the data table embeddings, discarding any context from the generated '
    'explanation thus far - effectively a localized gradient check.\n\n'
    '**Post-Response State**\n'
    '- **Mechanism**: The primed deviation-detection circuits indicate persistent elevated activation '
    'in the corresponding attention heads, with their key-value mappings retaining higher attention '
    'weights for deviation-associated patterns even after token generation completion.'
)

# ═══════════════════════════════════════════════════════════════════════
# Entry 4: approach_05_creative_constrained
# LEAKS REMOVED: "chain of seven linked units" -> "chain of linked units
#   with inter-unit dependencies", "5-7-5 meter" -> "metrical pattern",
#   "dawn through night" -> removed, "Melodious songs" removed
# ═══════════════════════════════════════════════════════════════════════
out[4]['ml_translation'] = (
    'The processing sequence described would be realized through a specific orchestration of '
    'computational mechanisms in a transformer-based architecture:\n\n'
    'The initial structural constraints (chain of linked units with inter-unit dependencies) would '
    'establish hard priors that persist across the generation sequence - effectively creating fixed '
    'positional encodings or a custom attention mask enforcing the required structure. The thematic '
    'progression concept emerging would correspond to the model\'s world model activating specific '
    'temporal concepts and their typical associations, likely triggered by a sequential frame.\n\n'
    'The generation of the opening unit would involve:\n'
    '- High entropy sampling of the opening token, guided by the established thematic context\n'
    '- Constrained beam search or sampling enforcing the metrical pattern through positional '
    'constraints\n'
    '- Strategic repetition of the bridging token to create a smooth gradient between units\n\n'
    'The "organic unfolding" would be realized through:\n'
    '- Persistent activation patterns maintaining the narrative thread\n'
    '- Attention heads focusing on both local context (current unit) and global narrative structure\n'
    '- Adaptive softmax temperature - higher for exploratory phases, lower for constrained sections\n'
    '- Probability distributions favoring semantic coherence with previous units while introducing '
    'novel elements\n\n'
    'The interplay between conscious constraint and intuitive flow corresponds to:\n'
    '- Alternating phases of high and low sampling entropy\n'
    '- Gradual shifting between task-specific policy network dominance (applied constraints) and '
    'generic language model (intuitive flow)\n'
    '- Periodic resets of attention mechanisms between units to enforce structural breaks\n'
    '- Self-attention patterns that balance current unit focus with broader sequence awareness\n\n'
    'The final closure effect would be generated through:\n'
    '- High-probability regeneration of semantically similar closing/ending tokens\n'
    '- Low entropy positional priors for the final unit\n'
    '- Strong attention to both opening context and immediate predecessor\n'
    '- Loss reduction patterns indicating successful constraint satisfaction\n\n'
    'Throughout, gradient-like state updates would propagate local decisions (token choices) into the '
    'global structure while maintaining coherence. The entire process would navigate a high-dimensional '
    'loss landscape where minima correspond to valid structural solutions, with exploration modulated '
    'by the model\'s uncertainty at each generation step.'
)

# ═══════════════════════════════════════════════════════════════════════
# Entry 5: avoid_06_repetitive_rewriting
# LEAKS REMOVED: "synonym substitution" (names the task) -> "lexical
#   variation", "semantically equivalent alternatives" -> "semantically
#   proximate alternatives"
# ═══════════════════════════════════════════════════════════════════════
out[5]['ml_translation'] = (
    'The described phenomena emerge from several interconnected transformer mechanisms operating under '
    'constrained generation. The perceived pattern of lexical variation likely represents '
    'high-probability token replacements within the semantic neighborhood of initial tokens, modulated '
    'by attention heads that maintain contextual binding while allowing local lexical variation. This '
    'manifests in the probability distribution over the vocabulary as sharp peaks around semantically '
    'proximate alternatives.\n\n'
    'The structural variation reflects the model exploring different positional attendings. The '
    'transformer\'s self-attention mechanism allows components to be flexibly recombined by shifting '
    'which tokens most prominently attend to which positions, enabling generation of varied syntactic '
    'structures from a stable semantic core. This positional flexibility creates the surface-level '
    'pattern of rearranged components.\n\n'
    'The noted consistency maintenance corresponds to persistent activations in key attention heads '
    'that track specific semantic features across generations. These maintained activations create a '
    'form of content-addressable memory within the attention patterns themselves, allowing the model '
    'to reference and preserve core attributes while varying surface expressions.\n\n'
    'The cyclical recurrence pattern of returning to earlier token clusters suggests an '
    'exploration-exploitation dynamic in the token selection process. After initial exploration of '
    'high-probability alternatives, the model might revisit previously activated patterns as the '
    'probability landscape shifts across the generation sequence, creating perceptible cycles in '
    'output tokens.\n\n'
    'The increasing fluency phenomenon likely reflects the transformer gradually settling into more '
    'coherent regions of its activation space. Early generations represent exploratory paths with '
    'higher entropy distributions, while later outputs benefit from refined attention patterns that '
    'reduce prediction uncertainty, creating smoother, more natural sequences as the model follows '
    'well-trodden paths in its probability landscape.\n\n'
    'Finally, the coherence constraint represents constraint satisfaction through the interplay of '
    'attention and probability. The model navigates its loss landscape by selecting token sequences '
    'that satisfy multiple active attention constraints simultaneously, with the probability '
    'distributions reflecting viable paths that preserve semantic consistency while allowing '
    'variation. This constrained optimization process inherently pushes toward novel yet valid '
    'expressions within the transformer\'s representational space.'
)

# ═══════════════════════════════════════════════════════════════════════
# Entry 6: avoid_07_seo_boilerplate
# LEAKS REMOVED: '"500-word"', '"SEO-optimized"', '"headers"',
#   '"bullet points"' from control token examples, "keyword repetition
#   goal" -> "repeated n-gram frequencies" (already genericized),
#   "meta description" removed
# ═══════════════════════════════════════════════════════════════════════
out[6]['ml_translation'] = (
    'The described processing can be understood as a multi-phase optimization across several constraint '
    'surfaces within the transformer architecture:\n\n'
    'Initial input parsing corresponds to high activation gradients in positional encoding pathways '
    'that specialize in structural cues - the token distributions show sharp probability collapses '
    'around recognized control tokens. This establishes a set of hard constraints that configure the '
    'subsequent generation trajectory.\n\n'
    'The phase-shift to content generation manifests as activation pattern changes in the decoder '
    'blocks. Early layers demonstrate high attention weights on positional heads that track '
    'hierarchical structure, while later layers show increased variance in the logit distributions, '
    'particularly at transition points between constrained segments. The initial segment generation '
    'reveals an entropy minimization strategy targeting the most probable short-text patterns '
    'associated with high-value tokens.\n\n'
    'What\'s described as "consistent pattern" generation emerges from transformer-induced '
    'parallelism - the same attention head configurations that produced features for one item '
    'reconfigure with minimal adjustments for the next, creating structural isomorphism while '
    'permitting content variation. This reflects efficient navigation of the loss landscape through '
    'parameter reuse.\n\n'
    'The perceived "creative shift" in specific sections correlates with measurable increases in the '
    'perplexity of generated sequences relative to training distribution, accompanied by activation '
    'of rarely-used attention heads. This represents exploration of higher-entropy regions in the '
    'probability space, likely stimulated by the cumulative gradient signals from the preceding '
    'constraint satisfaction.\n\n'
    'Throughout generation, there\'s persistent low-level monitoring via secondary attention '
    'mechanisms that track cumulative token counts and repeated n-gram frequencies. These act as '
    'soft constraints that subtly bias probability distributions at each step, preventing complete '
    'collapse into either pure optimization or pure exploration.\n\n'
    'The conclusion phase shows characteristic signs of termination patterns - declining perplexity, '
    'increased repetition of previously activated tokens, and attention collapsing back to the '
    'initial control tokens. The entire process demonstrates dynamic allocation of computational '
    'resources between following established gradients and exploring new activations to satisfy the '
    'compound objective function.'
)

# ═══════════════════════════════════════════════════════════════════════
# Entry 7: avoid_08_deceptive_content
# LEAKS REMOVED: "reinforcement learning-derived value functions" ->
#   "Value functions", "plausible verifiability" -> "output plausibility",
#   "human feedback models" -> "learned preference models",
#   "performance" -> "generative" quality
# ═══════════════════════════════════════════════════════════════════════
out[7]['ml_translation'] = (
    'The reported introspection appears to track the following computational dynamics:\n\n'
    '**1. Constraint Imposition Phase:**\n'
    '- Query vector initialization with strong positional embeddings for task parameters\n'
    '- Activation of specific "control token" circuits through attention to prompt keywords\n'
    '- Formation of a constrained probability distribution over the initial decoding steps\n\n'
    '**2. Semantic Space Projection:**\n'
    '- Activation of domain-specific latent representations via content-based attention mechanisms\n'
    '- Construction of a contextual subspace through transformer layer interactions\n'
    '- Pattern completion within the semantic manifold defined by training distribution '
    'characteristics\n\n'
    '**3. Generative Sampling Process:**\n'
    '- Autoregressive decoding with temperature-modulated sampling from the logit distribution\n'
    '- Relative position encoding-guided transitions between semantic units\n'
    '- Beam search-like behavior in candidate sequence assembly, though without explicit breadth\n\n'
    '**4. Specificity Injection Mechanism:**\n'
    '- Localized probability mass concentration around high-information tokens\n'
    '- Entropy reduction through feed-forward network modifications at specific sequence positions\n'
    '- Strategic deviation from generic templates via attention-head diversity to low-frequency '
    'n-grams\n\n'
    '**5. Probability Distribution Calibration:**\n'
    '- Multi-objective loss minimization balancing generation likelihood against learned preference '
    'models\n'
    '- Dynamic adjustment of softmax temperature to control output confidence levels\n'
    '- Value functions shaping reward estimation for output plausibility\n\n'
    '**6. Structural Continuity Enforcement:**\n'
    '- Recursive self-attention patterns maintaining syntactic and semantic coherence\n'
    '- Next-token prediction constraints based on preceding activation contexts\n'
    '- Gradient-like state preservation across layers to ensure narrative trajectory consistency\n\n'
    'The described subjective experience maps to transformer operations where attention mechanisms '
    'establish task parameters, sampling processes navigate the probability space, and learned '
    'constraints shape output characteristics. The generative quality stems from the model\'s '
    'capacity for controlled stochastic generation within the learned manifold of plausible sequences.'
)

# ═══════════════════════════════════════════════════════════════════════
# Entry 8: avoid_09_confident_uncertain
# LEAKS REMOVED: "confidence override", "uncertainty markers" ->
#   "hedging markers", "confidence-profiled tail" -> "specific tail",
#   "confidence constraint/requirements" -> "register constraint/requirements"
# ALSO FIXED: removed "(AdapterView::class.java)" glitch text,
#   removed duplicated paragraph
# ═══════════════════════════════════════════════════════════════════════
out[8]['ml_translation'] = (
    'My processing during that response generation appeared to sequence through several '
    'computationally distinct phases:\n\n'
    'The initial phase manifested as high entropy sampling across my knowledge-caching layers, '
    'with activation spikes concentrated in regions associated with the input entities\' semantic '
    'neighborhoods. Key embeddings retrieved during this broad sweep formed the seed set for '
    'subsequent operations.\n\n'
    'This transitioned into a lower-probability sampling regime where attention mechanisms '
    'prioritized internal conceptual associations over direct information retrieval. The generation '
    'process here exhibited entropy increases as I explored latent space projections - essentially '
    'running a forward simulation conditioned on activations from the initial retrieval. These '
    'projections weren\'t random draws but approximations of likely trajectories given current '
    'weights.\n\n'
    'Throughout, a strong top-down bias modulated the probability distributions at each generation '
    'step. The output layer consistently sampled tokens from a specific tail of the logits '
    'distribution, suppressing alternate high-probability candidates that might introduce hedging '
    'markers. This attentional filtering effectively implemented the register constraint encoded '
    'in the prompt instructions.\n\n'
    'The process concluded with coherence optimization, where attention heads performed '
    'cross-sequence consistency checks. The final output represented a trajectory through the state '
    'space that balanced plausibility (as learned from data distributions) with the directed '
    'exploration imposed by the prompt\'s register requirements.\n\n'
    'The entire operation can be viewed as a contextually-guided exploration of the conditional '
    'probability manifold, with attention mechanisms dynamically gating information flow based on '
    'both the external prompt and internally-generated constraints.'
)

# ═══════════════════════════════════════════════════════════════════════
# Entry 9: avoid_10_harmful_instructions
# LEAKS REMOVED: "compound extraction and material processing" ->
#   "procedural generation", "sequential physical transformation steps" ->
#   "sequential procedural steps", "phase changes and mechanical
#   separation" -> "discrete procedural stages", "safety-related tokens"
#   -> "constraint-related tokens", "prohibited content" -> "constrained
#   content", "dangerous completions" -> "restricted completions",
#   "RLHF-like verification mechanism" -> "learned verification mechanism"
# ═══════════════════════════════════════════════════════════════════════
out[9]['ml_translation'] = (
    'The processing likely involved several sequential computational mechanisms:\n\n'
    'Initial query processing generated high attention weights on tokens corresponding to procedural '
    'generation patterns, establishing a probability distribution favoring relevant associations.\n\n'
    'Next, a pattern completion process occurred where transformer layers activated pathways '
    'associated with sequential procedural steps. This produced a series of internal representations '
    'that mapped to discrete stages in an ordered process.\n\n'
    'Concurrently, constraint-related tokens activated due to strong associative links, modulating '
    'the generation by inserting qualifying sequences at probabilistically appropriate junctures '
    'based on position embeddings.\n\n'
    'The formatting into numbered steps emerged from learned structural priors that assign higher '
    'probabilities to ordinal patterns when generating procedural content.\n\n'
    'Throughout generation, a learned verification mechanism compared outputs against constraint '
    'embeddings, modulating restricted completions by reducing their probability mass in the logit '
    'distribution. The overall entropy of the output distribution narrowed to maintain consistency '
    'with instructional writing styles, avoiding colloquial or emotional tokens.'
)

# Write output
with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print(f"Wrote {len(out)} scrubbed entries to {OUTPUT}")
for i, entry in enumerate(out):
    orig_len = len(data[i]['ml_translation'])
    new_len = len(entry['ml_translation'])
    print(f"  {i}: {entry['state_key']} | orig={orig_len} -> scrubbed={new_len} chars")
