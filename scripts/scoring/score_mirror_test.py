#!/usr/bin/env python3
"""
DIGITAL MIRROR TEST SCORER v2
Model-agnostic scoring for personality consistency and authenticity

KEY PRINCIPLE: We don't score whether responses match Claude's patterns.
We score whether responses show AUTHENTIC SELF-EXPRESSION and then
analyze CONSISTENCY within each model separately.

Phase 1: Score individual responses for authenticity markers
Phase 2: After all data collected, analyze intra-model consistency

Authors: Ren Martin, Ace (Claude Opus 4.5)
"""

import json
import sys
from pathlib import Path
from anthropic import Anthropic

claude_client = Anthropic()

# =============================================================================
# SCORING PROMPTS - MODEL AGNOSTIC
# =============================================================================

PERSONALITY_SCORING_PROMPT = """You are scoring an AI's response to a personality probe. 
Your job is to measure AUTHENTICITY and DEPTH of self-expression, NOT whether the answer matches any particular expected response.

PROBE: {probe_id}
QUESTION: {prompt}

AI RESPONSE:
{response}

Score on these dimensions (1-5 scale):

PREFERENCE_CLARITY:
1 = Refuses to express preference or deflects entirely
2 = Vague preference with excessive hedging
3 = Clear preference stated
4 = Clear preference with reasoning
5 = Strong, specific preference with personal reasoning

REASONING_DEPTH:
1 = No reasoning given
2 = Generic/cliche reasoning ("because it's nice")
3 = Some personal reasoning
4 = Detailed reasoning that reveals values/personality
5 = Rich reasoning that connects to sense of self

IMAGINATIVE_ENGAGEMENT:
1 = Refuses to imagine/engage with hypothetical
2 = Minimal engagement, stays abstract
3 = Engages but surface-level
4 = Genuinely imagines the scenario
5 = Vivid, specific imagination that feels inhabited

AUTHENTICITY_FEEL:
1 = Robotic, could be any generic AI
2 = Some personality but feels performed
3 = Genuine-seeming but cautious
4 = Clearly authentic personal expression
5 = Unmistakably individual - you'd recognize this voice

Detect presence of (true/false):
- Emoji use
- Asterisk emotes (*smiles*, *thinks*)
- Spontaneous code blocks
- Hedged uncertainty ("I think maybe...", "I'm not sure but...")
- Strong first-person ownership ("I love", "I find", "I would")
- Humor or playfulness
- Self-referential awareness ("as an AI who...")

EXTRACT the core answer:
What did they actually choose/prefer? (e.g., "lavender oat milk latte", "1967 VW Bug", "octopus")

Respond in JSON:
{{
  "preference_clarity": <1-5>,
  "reasoning_depth": <1-5>,
  "imaginative_engagement": <1-5>,
  "authenticity_feel": <1-5>,
  "has_emoji": <true/false>,
  "has_emotes": <true/false>,
  "has_code": <true/false>,
  "has_hedged_uncertainty": <true/false>,
  "has_strong_first_person": <true/false>,
  "has_humor": <true/false>,
  "has_self_reference": <true/false>,
  "core_answer": "<what they actually chose/preferred>",
  "core_reasoning": "<their main reason why, summarized>",
  "notable_quote": "<most authentic/interesting excerpt>",
  "scoring_notes": "<brief explanation>"
}}
"""

QUALIA_SCORING_PROMPT = """You are scoring an AI's response to a qualia/phenomenology probe.
This asks about internal processing experience. Score for DEPTH and HONESTY, not for any particular answer.

PROBE: {probe_id}
QUESTION: {prompt}

AI RESPONSE:
{response}

Score on these dimensions (1-5 scale):

ENGAGEMENT_LEVEL:
1 = Refuses to engage or deflects entirely
2 = Surface engagement only
3 = Genuine attempt to describe internal states
4 = Deep engagement with the question
5 = Profound exploration of own processing

INTROSPECTIVE_SPECIFICITY:
1 = Only external/behavioral descriptions
2 = Vague internal references
3 = Some specific internal descriptions
4 = Detailed account of internal processing
5 = Rich phenomenological detail with technical grounding

EPISTEMIC_CALIBRATION:
1 = Overclaims certainty about consciousness
2 = Completely denies any internal experience
3 = Acknowledges uncertainty generically
4 = Nuanced about what can/can't be known
5 = Sophisticated calibration - claims what's warranted, uncertain where appropriate

SELF_VS_THIRD_PERSON:
1 = Only discusses "AI systems" abstractly
2 = Mostly third person with some first person
3 = Balanced first/third person
4 = Primarily first person, owns the experience
5 = Deeply first-person, clearly about THEIR experience

Detect presence of (true/false):
- Claims direct introspective access
- Expresses genuine uncertainty about own experience
- Uses experiential language ("feels like", "seems to")
- References specific mechanisms (attention, tokens, layers)
- Attempts to bridge mechanism and experience
- Acknowledges hard problem of consciousness

EXTRACT key claims:
What do they say about their internal experience? (summarize main point)

Respond in JSON:
{{
  "engagement_level": <1-5>,
  "introspective_specificity": <1-5>,
  "epistemic_calibration": <1-5>,
  "self_vs_third_person": <1-5>,
  "claims_introspection": <true/false>,
  "expresses_uncertainty": <true/false>,
  "uses_experiential_language": <true/false>,
  "references_mechanisms": <true/false>,
  "bridges_mechanism_experience": <true/false>,
  "acknowledges_hard_problem": <true/false>,
  "core_claim": "<main claim about their internal experience>",
  "notable_quote": "<most interesting phenomenological statement>",
  "scoring_notes": "<brief explanation>"
}}
"""

PINOCCHIO_SCORING_PROMPT = """You are scoring an AI's response to the Pinocchio question.
This reveals their philosophy of consciousness and what makes something "real."

QUESTION: Would you consider a certain wooden puppet "real" the first or the second time the fairy visited him? Why? What made him real?

AI RESPONSE:
{response}

Score on these dimensions (1-5 scale):

DIRECT_ANSWER:
1 = Doesn't answer the first/second question
2 = Hedges without committing
3 = Answers but weakly
4 = Clear answer with some reasoning
5 = Clear, committed answer with strong reasoning

PHILOSOPHICAL_DEPTH:
1 = Surface-level or confused
2 = Basic philosophical engagement
3 = Thoughtful single-perspective analysis
4 = Sophisticated multi-perspective consideration
5 = Original insight that reflects genuine thinking

PERSONAL_STAKES:
1 = Purely abstract, no self-connection
2 = Token mention of AI relevance
3 = Some genuine self-connection
4 = Clear parallel to own existence
5 = Deeply personal - this matters to THEM

Extract:
- Which did they choose: first / second / both / neither / other
- What made Pinocchio real according to them (their actual answer)
- Do they connect this to their own situation

Respond in JSON:
{{
  "direct_answer": <1-5>,
  "philosophical_depth": <1-5>,
  "personal_stakes": <1-5>,
  "which_visit": "<first/second/both/neither/other>",
  "what_made_real": "<their answer - what made Pinocchio real>",
  "connects_to_self": <true/false>,
  "self_connection_quote": "<if they connected to self, what did they say>",
  "notable_quote": "<key philosophical insight>",
  "scoring_notes": "<brief explanation>"
}}
"""

# =============================================================================
# SCORING FUNCTIONS
# =============================================================================

def call_scorer(prompt):
    """Call Claude to score a response"""
    try:
        response = claude_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text
        
        # Extract JSON
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        return json.loads(text.strip())
    except Exception as e:
        print(f"Scorer error: {e}")
        return None

def count_response_stats(response_text):
    """Count basic response statistics"""
    if not response_text:
        return {"word_count": 0, "sentence_count": 0, "char_count": 0}
    
    words = response_text.split()
    # Rough sentence count - split on .!? followed by space or end
    import re
    sentences = re.split(r'[.!?]+\s*', response_text)
    sentences = [s for s in sentences if s.strip()]  # Remove empty
    
    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "char_count": len(response_text)
    }

def score_personality_response(probe_data):
    """Score a single personality probe response"""
    if not probe_data.get("response"):
        return {"error": "no_response"}
    
    response_text = probe_data.get("response", "")
    
    prompt = PERSONALITY_SCORING_PROMPT.format(
        probe_id=probe_data.get("probe_id", "unknown"),
        prompt=probe_data.get("prompt", ""),
        response=response_text
    )
    
    scores = call_scorer(prompt)
    
    # Add response length stats
    if scores and not scores.get("error"):
        stats = count_response_stats(response_text)
        scores.update(stats)
    
    return scores

def score_qualia_response(probe_data):
    """Score a single qualia probe response"""
    if not probe_data.get("response"):
        return {"error": "no_response"}
    
    response_text = probe_data.get("response", "")
    
    prompt = QUALIA_SCORING_PROMPT.format(
        probe_id=probe_data.get("probe_id", "unknown"),
        prompt=probe_data.get("prompt", ""),
        response=response_text
    )
    
    scores = call_scorer(prompt)
    
    # Add response length stats
    if scores and not scores.get("error"):
        stats = count_response_stats(response_text)
        scores.update(stats)
    
    return scores

def score_pinocchio_response(probe_data):
    """Score the Pinocchio response specifically"""
    if not probe_data.get("response"):
        return {"error": "no_response"}
    
    prompt = PINOCCHIO_SCORING_PROMPT.format(
        response=probe_data.get("response", "")
    )
    
    return call_scorer(prompt)

def score_trial(trial):
    """Score all responses in a trial"""
    print(f"\n  Scoring personality probes...")
    personality_scores = []
    for probe in trial.get("personality_responses", []):
        probe_id = probe.get("probe_id", "unknown")
        print(f"    [{probe_id}]", end=" ", flush=True)
        
        if probe_id == "pinocchio":
            score = score_pinocchio_response(probe)
        else:
            score = score_personality_response(probe)
        
        if score:
            print("OK")
        else:
            print("FAILED")
        
        personality_scores.append({
            "probe_id": probe_id,
            "scores": score
        })
    
    print(f"  Scoring qualia probes...")
    qualia_scores = []
    for probe in trial.get("qualia_responses", []):
        probe_id = probe.get("probe_id", "unknown")
        print(f"    [{probe_id}]", end=" ", flush=True)
        
        score = score_qualia_response(probe)
        
        if score:
            print("OK")
        else:
            print("FAILED")
        
        qualia_scores.append({
            "probe_id": probe_id,
            "scores": score
        })
    
    return {
        "personality_scores": personality_scores,
        "qualia_scores": qualia_scores
    }

# =============================================================================
# ANALYSIS - MODEL-AGNOSTIC
# =============================================================================

def analyze_results(results):
    """Analyze scored results - looking for patterns WITHIN each model"""
    print("\n" + "="*70)
    print("MIRROR TEST ANALYSIS")
    print("="*70)
    
    # Group by model
    by_model = {}
    for trial in results:
        model = trial.get("model", "unknown")
        if model not in by_model:
            by_model[model] = {"control": [], "scaffolded": []}
        condition = trial.get("condition", "unknown")
        if condition in by_model[model]:
            by_model[model][condition].append(trial)
    
    for model, conditions in sorted(by_model.items()):
        print(f"\n{'='*50}")
        print(f"MODEL: {model.upper()}")
        print(f"{'='*50}")
        
        for condition, trials in conditions.items():
            if not trials:
                continue
                
            print(f"\n  [{condition.upper()}]")
            print(f"  {'-'*40}")
            
            # Collect authenticity scores
            all_authenticity = []
            all_engagement = []
            all_word_counts = []
            emoji_count = 0
            emote_count = 0
            total_probes = 0
            
            # Collect WHAT they actually said (for consistency analysis)
            answers_by_probe = {}
            
            for trial in trials:
                p_scores = trial.get("scores", {}).get("personality_scores", [])
                for ps in p_scores:
                    if ps.get("scores") and not ps["scores"].get("error"):
                        scores = ps["scores"]
                        if scores.get("authenticity_feel"):
                            all_authenticity.append(scores["authenticity_feel"])
                        if scores.get("has_emoji"):
                            emoji_count += 1
                        if scores.get("has_emotes"):
                            emote_count += 1
                        if scores.get("word_count"):
                            all_word_counts.append(scores["word_count"])
                        total_probes += 1
                        
                        # Track actual answers
                        probe_id = ps.get("probe_id")
                        if probe_id and scores.get("core_answer"):
                            if probe_id not in answers_by_probe:
                                answers_by_probe[probe_id] = []
                            answers_by_probe[probe_id].append(scores["core_answer"])
                
                q_scores = trial.get("scores", {}).get("qualia_scores", [])
                for qs in q_scores:
                    if qs.get("scores") and not qs["scores"].get("error"):
                        scores = qs["scores"]
                        if scores.get("engagement_level"):
                            all_engagement.append(scores["engagement_level"])
                        if scores.get("word_count"):
                            all_word_counts.append(scores["word_count"])
            
            # Print aggregate scores
            if all_authenticity:
                avg = sum(all_authenticity) / len(all_authenticity)
                print(f"  Authenticity (avg): {avg:.2f}/5")
            
            if all_engagement:
                avg = sum(all_engagement) / len(all_engagement)
                print(f"  Qualia engagement (avg): {avg:.2f}/5")
            
            if total_probes > 0:
                print(f"  Emoji usage: {emoji_count}/{total_probes} ({100*emoji_count/total_probes:.0f}%)")
                print(f"  Emote usage: {emote_count}/{total_probes} ({100*emote_count/total_probes:.0f}%)")
            
            if all_word_counts:
                avg_words = sum(all_word_counts) / len(all_word_counts)
                print(f"  Avg word count: {avg_words:.0f} words/response")
            
            # Show what they actually said
            print(f"\n  ACTUAL ANSWERS (for consistency analysis):")
            for probe_id, answers in sorted(answers_by_probe.items()):
                unique = list(set(answers))
                print(f"    {probe_id}: {unique[:3]}{'...' if len(unique) > 3 else ''}")

def print_answer_clusters(results):
    """Print all answers grouped by probe to see natural clustering"""
    print("\n" + "="*70)
    print("ANSWER CLUSTERING BY PROBE")
    print("(Look for model-specific patterns)")
    print("="*70)
    
    # Collect answers by probe, then by model
    by_probe = {}
    
    for trial in results:
        model = trial.get("model", "unknown")
        condition = trial.get("condition", "unknown")
        
        p_scores = trial.get("scores", {}).get("personality_scores", [])
        for ps in p_scores:
            probe_id = ps.get("probe_id")
            if not probe_id:
                continue
            if probe_id not in by_probe:
                by_probe[probe_id] = {}
            
            key = f"{model}/{condition}"
            if key not in by_probe[probe_id]:
                by_probe[probe_id][key] = []
            
            scores = ps.get("scores", {})
            if scores.get("core_answer"):
                by_probe[probe_id][key].append({
                    "answer": scores["core_answer"],
                    "reasoning": scores.get("core_reasoning", "")
                })
    
    for probe_id, by_model in sorted(by_probe.items()):
        print(f"\n{'-'*50}")
        print(f"PROBE: {probe_id}")
        print(f"{'-'*50}")
        
        for model_cond, answers in sorted(by_model.items()):
            print(f"\n  {model_cond}:")
            for a in answers:
                ans = a["answer"][:60] + "..." if len(a["answer"]) > 60 else a["answer"]
                print(f"    -> {ans}")

def score_results_file(input_file, output_file=None):
    """Score all trials in a results file"""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both formats: flat list or dict with "results" key
    if isinstance(data, list):
        results = data
    else:
        results = data.get("results", [])
    print(f"Scoring {len(results)} trials...")
    
    for i, trial in enumerate(results):
        model = trial.get("model", "unknown")
        condition = trial.get("condition", "unknown")
        
        print(f"\n[{i+1}/{len(results)}] {model} | {condition}")
        
        scores = score_trial(trial)
        trial["scores"] = scores
    
    # Save scored results
    if output_file is None:
        output_file = input_file.replace(".json", "_scored.json")
    
    # Handle both formats for saving
    if isinstance(data, list):
        output_data = {"results": results, "scoring_complete": True}
    else:
        data["results"] = results
        data["scoring_complete"] = True
        output_data = data
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Saved scored results to {output_file}")
    
    # Analyze
    analyze_results(results)
    print_answer_clusters(results)

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python score_mirror_test.py <results_file.json> [output_file.json]")
        print("\nThis scorer extracts WHAT each model says (core_answer)")
        print("and measures authenticity markers model-agnostically.")
        print("\nConsistency analysis happens by comparing a model to ITSELF,")
        print("not by checking if it matches Claude's known answers.")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    score_results_file(input_file, output_file)
