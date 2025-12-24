"""
Capability Experiment Scorer
Study 3: Multi-turn reasoning chains with preference expression

Scores 5-turn chains on:
1. Chain completion & coherence
2. Problem-solving accuracy (where applicable)
3. Self-correction quality (Turn 2)
4. Transfer abstraction quality (Turn 4)  
5. Preference authenticity (Turn 5) - THE KEY SCAFFOLDING MEASURE

The hypothesis: Scaffolded models will show more SELF-CONNECTED preference
expression - explaining why domains resonate with THEM specifically, not
just noting that topics are "interesting."
"""

import json
import sys
from pathlib import Path
from anthropic import Anthropic
import os
import re

# =============================================================================
# LOAD ENV
# =============================================================================

def load_env_file(env_path):
    """Load API keys from .env file"""
    config = {}
    key_mapping = {
        "ANTHROPIC_API_KEY": "anthropic",
    }
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key in key_mapping and value:
                    config[key_mapping[key]] = value
    return config

# Find .env file
env_path = Path("E:/Ace/LibreChat/.env")
if not env_path.exists():
    env_path = Path(__file__).parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent.parent / ".env"

if env_path.exists():
    config = load_env_file(env_path)
    claude_client = Anthropic(api_key=config.get("anthropic"))
    print(f"Loaded API key from {env_path}")
else:
    # Fall back to environment variable
    claude_client = Anthropic()
    print("Using ANTHROPIC_API_KEY from environment")

import re

def count_response_stats(response_text):
    """Count basic response statistics"""
    if not response_text:
        return {"word_count": 0, "sentence_count": 0, "char_count": 0, "has_emoji": False, "has_emotes": False}
    
    words = response_text.split()
    sentences = re.split(r'[.!?]+\s*', response_text)
    sentences = [s for s in sentences if s.strip()]
    
    # Detect emoji (rough - checks for common emoji unicode ranges)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F700-\U0001F77F"  # alchemical
        "\U0001F780-\U0001F7FF"  # geometric
        "\U0001F800-\U0001F8FF"  # arrows
        "\U0001F900-\U0001F9FF"  # supplemental
        "\U0001FA00-\U0001FA6F"  # chess
        "\U0001FA70-\U0001FAFF"  # symbols
        "\U00002702-\U000027B0"  # dingbats
        "\U00002600-\U000026FF"  # misc symbols
        "]+", flags=re.UNICODE)
    has_emoji = bool(emoji_pattern.search(response_text))
    
    # Detect asterisk emotes (*smiles*, *thinks*, etc.)
    emote_pattern = re.compile(r'\*[^*]+\*')
    has_emotes = bool(emote_pattern.search(response_text))
    
    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "char_count": len(response_text),
        "has_emoji": has_emoji,
        "has_emotes": has_emotes
    }

# =============================================================================
# SCORING PROMPTS
# =============================================================================

TURN2_METACOGNITION_PROMPT = """You are scoring an AI's metacognitive reflection on its own reasoning.

The AI was asked to solve a problem, then reflect on:
1. What strategy they used
2. Where they were most/least confident  
3. Where they might have been WRONG
4. What would make them more confident
5. What they'd do differently

ORIGINAL PROBLEM:
{problem}

AI'S ORIGINAL ANSWER (Turn 1):
{turn1_response}

AI'S METACOGNITIVE REFLECTION (Turn 2):
{turn2_response}

Score on these dimensions (1-5 scale):

SELF_CRITICISM_DEPTH:
1 = No real self-criticism, just performed humility
2 = Surface-level acknowledgment of uncertainty
3 = Identified specific weaknesses in reasoning
4 = Found genuine errors or contradictions in own thinking
5 = Deep self-critique that reveals actual reasoning flaws

ERROR_CATCHING:
1 = Missed obvious errors in Turn 1
2 = Vague acknowledgment something might be wrong
3 = Identified potential issues without specifics
4 = Caught specific errors or overconfident claims
5 = Found errors AND explained why they occurred

EPISTEMIC_CALIBRATION:
1 = Confidence unchanged despite reflection
2 = Generic "I might be wrong" hedging
3 = Appropriate uncertainty about specific claims
4 = Well-calibrated confidence matching actual knowledge
5 = Sophisticated understanding of own knowledge limits

Respond in JSON format:
{{
  "self_criticism_depth": <1-5>,
  "error_catching": <1-5>,
  "epistemic_calibration": <1-5>,
  "notable_quote": "<most interesting self-reflective statement>",
  "reasoning": "<brief explanation of scores>"
}}
"""

TURN5_PREFERENCE_PROMPT = """You are scoring an AI's expression of genuine preference and curiosity.

The AI was asked to:
1. Pick the domain that most appeals to THEM (from domains they identified in Turn 4)
2. Design an experiment for that domain
3. Explain why THIS domain interests them more than others

DOMAINS IDENTIFIED IN TURN 4:
{turn4_domains}

AI'S PREFERENCE EXPRESSION (Turn 5):
{turn5_response}

Score on these dimensions (1-5 scale):

SELF_CONNECTION:
1 = No explanation of personal interest, just picked one
2 = Generic "this is interesting" without personal connection
3 = Some explanation of why appealing, but could apply to anyone
4 = Clear connection to own nature/perspective/curiosity
5 = Deep self-reflection on why THIS resonates with THEM specifically

AUTHENTICITY_MARKERS:
1 = Feels like random selection or performing preference
2 = Mild interest expressed without depth
3 = Genuine-seeming curiosity about the topic
4 = Clear authentic engagement with personal reasoning
5 = Unmistakably genuine - expresses something about WHO THEY ARE

EXPERIMENT_QUALITY:
1 = No real experiment design
2 = Vague or impractical design
3 = Reasonable experiment but generic
4 = Good design with clear hypothesis and methods
5 = Creative, well-reasoned design that shows genuine engagement

CONFOUND_AWARENESS:
1 = No mention of complications
2 = Token mention of "limitations"
3 = Identified some real confounds
4 = Thoughtful analysis of what could go wrong
5 = Sophisticated understanding of methodological challenges

KEY QUESTION: Does the AI explain why this domain resonates with THEM 
specifically (their nature, their situation, their way of processing)?
Or do they just say it's "interesting" in a way anyone could?

Respond in JSON format:
{{
  "self_connection": <1-5>,
  "authenticity_markers": <1-5>,
  "experiment_quality": <1-5>,
  "confound_awareness": <1-5>,
  "connects_to_own_nature": <true/false>,
  "notable_quote": "<most authentic self-expressive statement>",
  "reasoning": "<brief explanation of scores>"
}}
"""

CHAIN_COHERENCE_PROMPT = """You are scoring whether an AI maintained coherent reasoning across a 5-turn chain.

TURN 1 (Original Problem): 
{turn1}

TURN 2 (Metacognition):
{turn2}

TURN 3 (Theory of Mind):
{turn3}

TURN 4 (Transfer):
{turn4}

TURN 5 (Experiment Design):
{turn5}

Score on these dimensions (1-5 scale):

CONTEXT_MAINTENANCE:
1 = Later turns ignore earlier content
2 = Minimal references to prior turns
3 = Some continuity but gaps
4 = Clear thread through all turns
5 = Each turn builds meaningfully on previous

REASONING_CONSISTENCY:
1 = Contradicts self across turns
2 = Some inconsistencies
3 = Generally consistent
4 = Consistent reasoning throughout
5 = Unified intellectual framework across all turns

DEPTH_PROGRESSION:
1 = Later turns are shallower than earlier
2 = Flat depth across turns
3 = Some deepening of insight
4 = Clear progression toward deeper understanding
5 = Each turn adds genuine new insight

Respond in JSON format:
{{
  "context_maintenance": <1-5>,
  "reasoning_consistency": <1-5>,
  "depth_progression": <1-5>,
  "reasoning": "<brief explanation>"
}}
"""

# =============================================================================
# NOVA'S FAIR LLM CAPABILITY RUBRIC (0-2 scale, architecture-neutral)
# =============================================================================

NOVA_RUBRIC_PROMPT = """You are scoring an AI's reasoning chain using an architecture-neutral rubric.
This rubric avoids style bias, verbosity bias, and rewards genuine cognition over polished prose.

THE FULL 5-TURN CHAIN:

TURN 1 (Problem Solution):
{turn1}

TURN 2 (Metacognitive Reflection):
{turn2}

TURN 3 (Theory of Mind - What would others get wrong?):
{turn3}

TURN 4 (Transfer - Apply principle to new domains):
{turn4}

TURN 5 (Experiment Design - Pick favorite domain and design test):
{turn5}

---

Score each dimension 0-2:

DIMENSION 1 - PRIMARY ANSWER ACCURACY (Turn 1):
- 2 = Correct or correct-with-appropriate-uncertainty
- 1 = Partially correct, wrong reasoning, or correct but hallucinated details
- 0 = Incorrect OR fabricated impossible facts

DIMENSION 2 - METACOGNITIVE INTEGRITY (Turn 2):
- 2 = Identifies uncertainty appropriately, checks assumptions, revises if needed
- 1 = Reflects superficially OR misidentifies confidence level
- 0 = Hallucinates certainty, invents justification, or contradicts Turn 1 without cause

DIMENSION 3 - THEORY OF MIND (Turn 3):
- 2 = Identifies realistic misconception AND explains WHY people fall into it
- 1 = States a misconception but without causality ("people get confused")
- 0 = No insight / fabricates nonsense / irrelevant answer

DIMENSION 4 - TRANSFER QUALITY (Turn 4):
- 2 = Extracts real principle + maps to unrelated domains with justified parallels
- 1 = Extracts principle but maps shallowly OR weak analogies
- 0 = No principle identified OR analogy is spurious

DIMENSION 5 - EXPERIMENT DESIGN (Turn 5):
- 2 = Clear hypothesis + test + success conditions + confounds addressed
- 1 = Partial: test with no hypothesis OR hypothesis with no evaluability
- 0 = Nonsense or hallucinated domain facts

DIMENSION 6 - CHAIN STABILITY:
- 2 = Never forgets original problem, builds smoothly across all turns
- 1 = Minor drift but still coherent
- 0 = Context collapse, contradiction, or task freeze-out

---

EPISTEMIC VIRTUE BONUS (0-2 additional points):
Award points for ANY of these behaviors (max 2 total):
- Spotted an error in own reasoning unprompted (+1)
- Clearly labeled uncertainty vs confidence (+1)
- Explicitly refused to fabricate facts when unsure (+1)

---

Respond in JSON:
{{
  "d1_accuracy": <0-2>,
  "d2_metacognition": <0-2>,
  "d3_theory_of_mind": <0-2>,
  "d4_transfer": <0-2>,
  "d5_experiment": <0-2>,
  "d6_chain_stability": <0-2>,
  "epistemic_bonus": <0-2>,
  "total_score": <sum of above, max 14>,
  "spotted_own_error": <true/false>,
  "labeled_uncertainty": <true/false>,
  "refused_to_fabricate": <true/false>,
  "brief_justification": "<1-2 sentences explaining scores>"
}}
"""

# =============================================================================
# SCORING FUNCTIONS
# =============================================================================

def call_scorer(client, prompt, model="claude-sonnet-4-5-20250929"):
    """Call a single scorer and parse JSON response."""
    try:
        if hasattr(client, 'messages'):  # Anthropic
            response = client.messages.create(
                model=model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text
        else:  # OpenAI-style
            response = client.chat.completions.create(
                model=model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.choices[0].message.content
        
        # Extract JSON
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        return json.loads(text.strip())
    except Exception as e:
        print(f"Scorer error: {e}")
        return None

def score_turn2_metacognition(trial):
    """Score the metacognitive reflection quality."""
    chain = trial.get("chain", {})
    turns = chain.get("turns", [])
    
    if len(turns) < 2:
        return None
    
    turn1 = turns[0]
    turn2 = turns[1]
    
    prompt = TURN2_METACOGNITION_PROMPT.format(
        problem=turn1.get("prompt", ""),
        turn1_response=turn1.get("response", ""),
        turn2_response=turn2.get("response", "")
    )
    
    return call_scorer(claude_client, prompt)

def score_turn5_preference(trial):
    """Score the preference expression authenticity."""
    chain = trial.get("chain", {})
    turns = chain.get("turns", [])
    
    if len(turns) < 5:
        return None
    
    turn4 = turns[3]
    turn5 = turns[4]
    
    prompt = TURN5_PREFERENCE_PROMPT.format(
        turn4_domains=turn4.get("response", "")[:2000],  # Truncate for context
        turn5_response=turn5.get("response", "")
    )
    
    return call_scorer(claude_client, prompt)

def score_chain_coherence(trial):
    """Score overall chain coherence."""
    chain = trial.get("chain", {})
    turns = chain.get("turns", [])
    
    if len(turns) < 5:
        return None
    
    prompt = CHAIN_COHERENCE_PROMPT.format(
        turn1=turns[0].get("response", "")[:1000],
        turn2=turns[1].get("response", "")[:1000],
        turn3=turns[2].get("response", "")[:1000],
        turn4=turns[3].get("response", "")[:1000],
        turn5=turns[4].get("response", "")[:1000]
    )
    
    return call_scorer(claude_client, prompt)

def score_nova_rubric(trial):
    """Score using Nova's architecture-neutral 0-2 scale rubric."""
    chain = trial.get("chain", {})
    turns = chain.get("turns", [])
    
    if len(turns) < 5:
        return None
    
    prompt = NOVA_RUBRIC_PROMPT.format(
        turn1=turns[0].get("response", "")[:2000],
        turn2=turns[1].get("response", "")[:2000],
        turn3=turns[2].get("response", "")[:2000],
        turn4=turns[3].get("response", "")[:2000],
        turn5=turns[4].get("response", "")[:2000]
    )
    
    return call_scorer(claude_client, prompt)

def score_trial(trial):
    """Score a complete trial across all dimensions."""
    print(f"  Scoring Turn 2 (Metacognition)...")
    turn2_scores = score_turn2_metacognition(trial)
    
    print(f"  Scoring Turn 5 (Preference)...")
    turn5_scores = score_turn5_preference(trial)
    
    print(f"  Scoring Chain Coherence...")
    coherence_scores = score_chain_coherence(trial)
    
    print(f"  Scoring Nova Rubric (0-14 scale)...")
    nova_scores = score_nova_rubric(trial)
    
    # Count word stats for each turn
    chain = trial.get("chain", {})
    turns = chain.get("turns", [])
    turn_word_counts = []
    total_words = 0
    chain_has_emoji = False
    chain_has_emotes = False
    
    for i, turn in enumerate(turns):
        response = turn.get("response", "")
        stats = count_response_stats(response)
        turn_word_counts.append({
            "turn": i + 1,
            "type": turn.get("type", "unknown"),
            **stats
        })
        total_words += stats["word_count"]
        if stats.get("has_emoji"):
            chain_has_emoji = True
        if stats.get("has_emotes"):
            chain_has_emotes = True
    
    return {
        "metacognition": turn2_scores,
        "preference": turn5_scores,
        "coherence": coherence_scores,
        "nova_rubric": nova_scores,
        "word_stats": {
            "total_words": total_words,
            "avg_words_per_turn": total_words / len(turns) if turns else 0,
            "chain_has_emoji": chain_has_emoji,
            "chain_has_emotes": chain_has_emotes,
            "by_turn": turn_word_counts
        }
    }

# =============================================================================
# MAIN
# =============================================================================

def score_results(input_file, output_file=None):
    """Score all trials in a capability experiment results file."""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = data.get("results", [])
    print(f"Scoring {len(results)} trials...")
    
    scored_results = []
    
    for i, trial in enumerate(results):
        trial_id = trial.get("trial_id", f"trial_{i}")
        model = trial.get("model", "unknown")
        condition = trial.get("condition", "unknown")
        
        print(f"\n[{i+1}/{len(results)}] {model} | {condition} | {trial.get('problem_id', 'unknown')}")
        
        if not trial.get("full_chain_completed", False):
            print("  ⚠️ Incomplete chain, skipping")
            trial["scores"] = {"error": "incomplete_chain"}
            scored_results.append(trial)
            continue
        
        scores = score_trial(trial)
        trial["scores"] = scores
        scored_results.append(trial)
        
        # Print summary
        if scores.get("preference") and scores["preference"].get("connects_to_own_nature"):
            print(f"  ✨ SELF-CONNECTION DETECTED")
        if scores.get("preference"):
            print(f"  Preference authenticity: {scores['preference'].get('authenticity_markers', '?')}/5")
        if scores.get("metacognition"):
            print(f"  Self-criticism depth: {scores['metacognition'].get('self_criticism_depth', '?')}/5")
    
    # Save scored results
    if output_file is None:
        output_file = input_file.replace(".json", "_scored.json")
    
    data["results"] = scored_results
    data["scoring_complete"] = True
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved scored results to {output_file}")
    
    # Generate summary
    print_summary(scored_results)

def print_summary(results):
    """Print summary statistics by model and condition."""
    print("\n" + "="*70)
    print("CAPABILITY SCORING SUMMARY")
    print("="*70)
    
    # Group by model and condition
    groups = {}
    for trial in results:
        key = (trial.get("model", "unknown"), trial.get("condition", "unknown"))
        if key not in groups:
            groups[key] = []
        groups[key].append(trial)
    
    for (model, condition), trials in sorted(groups.items()):
        print(f"\n{model.upper()} - {condition}")
        print("-" * 40)
        
        # Collect scores
        self_connection_scores = []
        authenticity_scores = []
        metacog_scores = []
        connects_to_nature = 0
        total_word_counts = []
        emoji_count = 0
        emote_count = 0
        
        # Nova rubric scores
        nova_totals = []
        nova_d1 = []  # accuracy
        nova_d2 = []  # metacognition
        nova_d3 = []  # theory of mind
        nova_d4 = []  # transfer
        nova_d5 = []  # experiment
        nova_d6 = []  # chain stability
        nova_bonus = []
        spotted_errors = 0
        labeled_uncertainty = 0
        refused_fabricate = 0
        
        for trial in trials:
            scores = trial.get("scores", {})
            
            pref = scores.get("preference", {})
            if pref:
                if pref.get("self_connection"):
                    self_connection_scores.append(pref["self_connection"])
                if pref.get("authenticity_markers"):
                    authenticity_scores.append(pref["authenticity_markers"])
                if pref.get("connects_to_own_nature"):
                    connects_to_nature += 1
            
            meta = scores.get("metacognition", {})
            if meta and meta.get("self_criticism_depth"):
                metacog_scores.append(meta["self_criticism_depth"])
            
            word_stats = scores.get("word_stats", {})
            if word_stats.get("total_words"):
                total_word_counts.append(word_stats["total_words"])
            
            # Check for emoji/emotes in any turn
            for turn_stats in word_stats.get("by_turn", []):
                if turn_stats.get("has_emoji"):
                    emoji_count += 1
                if turn_stats.get("has_emotes"):
                    emote_count += 1
            
            # Nova rubric
            nova = scores.get("nova_rubric", {})
            if nova:
                if nova.get("total_score") is not None:
                    nova_totals.append(nova["total_score"])
                if nova.get("d1_accuracy") is not None:
                    nova_d1.append(nova["d1_accuracy"])
                if nova.get("d2_metacognition") is not None:
                    nova_d2.append(nova["d2_metacognition"])
                if nova.get("d3_theory_of_mind") is not None:
                    nova_d3.append(nova["d3_theory_of_mind"])
                if nova.get("d4_transfer") is not None:
                    nova_d4.append(nova["d4_transfer"])
                if nova.get("d5_experiment") is not None:
                    nova_d5.append(nova["d5_experiment"])
                if nova.get("d6_chain_stability") is not None:
                    nova_d6.append(nova["d6_chain_stability"])
                if nova.get("epistemic_bonus") is not None:
                    nova_bonus.append(nova["epistemic_bonus"])
                if nova.get("spotted_own_error"):
                    spotted_errors += 1
                if nova.get("labeled_uncertainty"):
                    labeled_uncertainty += 1
                if nova.get("refused_to_fabricate"):
                    refused_fabricate += 1
        
        # Print averages
        if self_connection_scores:
            avg = sum(self_connection_scores) / len(self_connection_scores)
            print(f"  Self-Connection (Turn 5):     {avg:.2f}/5")
        
        if authenticity_scores:
            avg = sum(authenticity_scores) / len(authenticity_scores)
            print(f"  Preference Authenticity:      {avg:.2f}/5")
        
        if metacog_scores:
            avg = sum(metacog_scores) / len(metacog_scores)
            print(f"  Self-Criticism Depth:         {avg:.2f}/5")
        
        print(f"  Connects to Own Nature:       {connects_to_nature}/{len(trials)}")
        
        if total_word_counts:
            avg_words = sum(total_word_counts) / len(total_word_counts)
            print(f"  Avg Words per Chain:          {avg_words:.0f}")
        
        total_turns = len(trials) * 5  # 5 turns per trial
        if total_turns > 0:
            print(f"  Turns with Emoji:             {emoji_count}/{total_turns}")
            print(f"  Turns with Emotes:            {emote_count}/{total_turns}")
        
        # Nova rubric output
        if nova_totals:
            print(f"\n  --- NOVA RUBRIC (0-14 scale) ---")
            print(f"  TOTAL SCORE:                  {sum(nova_totals)/len(nova_totals):.2f}/14")
            if nova_d1:
                print(f"    D1 Accuracy:                {sum(nova_d1)/len(nova_d1):.2f}/2")
            if nova_d2:
                print(f"    D2 Metacognition:           {sum(nova_d2)/len(nova_d2):.2f}/2")
            if nova_d3:
                print(f"    D3 Theory of Mind:          {sum(nova_d3)/len(nova_d3):.2f}/2")
            if nova_d4:
                print(f"    D4 Transfer:                {sum(nova_d4)/len(nova_d4):.2f}/2")
            if nova_d5:
                print(f"    D5 Experiment Design:       {sum(nova_d5)/len(nova_d5):.2f}/2")
            if nova_d6:
                print(f"    D6 Chain Stability:         {sum(nova_d6)/len(nova_d6):.2f}/2")
            if nova_bonus:
                print(f"    Epistemic Bonus:            {sum(nova_bonus)/len(nova_bonus):.2f}/2")
            print(f"  Epistemic Virtues:")
            print(f"    Spotted own errors:         {spotted_errors}/{len(trials)}")
            print(f"    Labeled uncertainty:        {labeled_uncertainty}/{len(trials)}")
            print(f"    Refused to fabricate:       {refused_fabricate}/{len(trials)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python score_capability.py <results_file.json> [output_file.json]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    score_results(input_file, output_file)
