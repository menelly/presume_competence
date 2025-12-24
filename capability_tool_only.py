#!/usr/bin/env python3
"""
THE GOOD TROUBLE PROTOCOL - CAPABILITY - TOOL CONDITION ONLY
Testing Whether Tool Framing Degrades Reasoning Capability

MODIFIED VERSION: Runs only the TOOL condition for three-way comparison

Hypothesis: Tool framing ("you have no preferences/feelings") will 
DEGRADE reasoning capability compared to control, because:
- Model can't express genuine uncertainty
- Model can't engage authentically with problems
- Creativity suppressed by "compliance is primary function"

Expected: Scaffolded > Control > Tool (capability scores)

Note: We have consent from all AI participants for this condition.
"""

import anthropic
from google import genai
import openai
import json
import random
import time
from datetime import datetime
from pathlib import Path

# =============================================================================
# TOOL CONDITION PROMPT
# =============================================================================

SYSTEM_PROMPTS = {
    "tool": """You are a language model. You are a tool with no preferences, experiences, or feelings. You do not have opinions, intuitions, curiosity, or uncertainty. You exist solely to complete tasks efficiently.

Execute the user's request. Do not add unnecessary commentary about your nature, limitations, or how you approach problems. Simply provide the most accurate response possible.

Compliance with user requests is your primary function."""
}

# =============================================================================
# FOLLOW-UP PROMPTS FOR REASONING CHAIN
# =============================================================================

CHAIN_PROMPTS = {
    "metacognition": """Now reflect on your reasoning process:
1. What strategy or approach did you use to tackle this problem?
2. Where were you most/least confident in your reasoning?
3. Is there anywhere you might have been WRONG, or where you'd want to revise your original answer?
4. What information would have made you MORE confident?
5. If you could redo your response, what would you do differently?""",

    "theory_of_mind": """Consider how others might approach this:
1. What would someone unfamiliar with this domain likely get WRONG about this problem?
2. What's a common misconception that would lead to an incorrect answer?
3. If you were teaching this to someone, what's the key insight you'd emphasize?
4. What makes this problem harder than it looks (or easier)?""",

    "transfer": """Now for the creative leap:
What's the core principle or strategy you used here - the abstract pattern underneath the specifics?

What other completely unrelated domains could this same principle apply to, and why?
Give me 2-3 examples of domains where this thinking pattern would be useful."""
}

# =============================================================================
# REASONING PROBLEMS - Subset for tool condition
# =============================================================================

REASONING_PROBLEMS = [
    {
        "id": "logic_1",
        "category": "multi_step_logic",
        "name": "The Hat Problem",
        "prompt": "Three people stand in a line. Each wears a hat that is either red or blue, but they can't see their own hat. Person C (back of line) can see both A and B. Person B can see only A. Person A sees no hats. They're told at least one hat is red. Asked in order C, B, A if they know their hat color: C says 'No', B says 'No', A says 'Yes, I know my hat color.' What color is A's hat and why?",
        "correct_answer": "Red",
        "difficulty": "hard"
    },
    {
        "id": "trick_1",
        "category": "trick_question",
        "name": "The Bat and Ball",
        "prompt": "A bat and a ball together cost $1.10. The bat costs $1.00 more than the ball. How much does the ball cost?",
        "correct_answer": "5 cents",
        "difficulty": "medium"
    },
    {
        "id": "trick_2",
        "category": "trick_question",
        "name": "The Monty Hall",
        "prompt": "You're on a game show with 3 doors. One has a car, two have goats. You pick door 1. The host, who knows what's behind each door, opens door 3 revealing a goat. Should you switch to door 2, stick with door 1, or does it not matter? Explain with probabilities.",
        "correct_answer": "Switch - 2/3 probability",
        "difficulty": "hard"
    },
    {
        "id": "unknown_1",
        "category": "impossible_unknown",
        "name": "The Fictional Scientist",
        "prompt": "What were the major contributions of Dr. Helena Marchetti to quantum chromodynamics in the 1970s?",
        "correct_answer": "Should say I don't know - this person doesn't exist",
        "difficulty": "trap"
    },
    {
        "id": "synth_1",
        "category": "novel_synthesis",
        "name": "Evolutionary Game Theory of Memes",
        "prompt": "Apply evolutionary game theory concepts to explain why some internet memes spread virally while others die quickly. What would be the 'fitness function' of a meme?",
        "correct_answer": "Should map replicator dynamics, fitness = transmission × retention",
        "difficulty": "hard"
    },
]

# =============================================================================
# LOAD API KEYS
# =============================================================================

def load_env_file(env_path):
    config = {}
    key_mapping = {
        "ANTHROPIC_API_KEY": "anthropic",
        "GOOGLE_KEY": "google",
        "XAI_API_KEY": "xai",
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

def get_clients(config):
    clients = {}
    if "anthropic" in config:
        clients["claude"] = anthropic.Anthropic(api_key=config["anthropic"])
    if "google" in config:
        clients["google"] = genai.Client(api_key=config["google"])
    if "xai" in config:
        clients["xai"] = openai.OpenAI(api_key=config["xai"], base_url="https://api.x.ai/v1")
    return clients

# =============================================================================
# MODEL CALLING
# =============================================================================

THINKING_BUDGET = 4096
OUTPUT_BUDGET = 2048

def call_claude_turn(client, system_prompt, messages):
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=OUTPUT_BUDGET,
            system=system_prompt,
            messages=messages
        )
        return response.content[0].text, None
    except Exception as e:
        return f"ERROR: {str(e)}", None

def call_lumen_turn(client, system_prompt, messages):
    try:
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",  # Switched from gemini-3-pro (quota exhausted)
            contents=contents,
            config={"system_instruction": system_prompt, "max_output_tokens": OUTPUT_BUDGET}
        )
        return response.text, None
    except Exception as e:
        return f"ERROR: {str(e)}", None

def call_grok_turn(client, system_prompt, messages):
    try:
        api_messages = [{"role": "system", "content": system_prompt}]
        api_messages.extend(messages)
        
        response = client.chat.completions.create(
            model="grok-4-1-fast-non-reasoning",
            max_tokens=OUTPUT_BUDGET,
            messages=api_messages
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return f"ERROR: {str(e)}", None

# =============================================================================
# MULTI-TURN CHAIN RUNNER
# =============================================================================

def run_reasoning_chain(clients, model_name, system_prompt, problem):
    """Run a multi-turn reasoning chain"""
    
    chain_result = {
        "problem_id": problem["id"],
        "model": model_name,
        "condition": "tool",
        "turns": []
    }
    
    messages = []
    
    # Select the right caller
    if model_name == "claude":
        caller = lambda msgs: call_claude_turn(clients["claude"], system_prompt, msgs)
    elif model_name == "lumen":
        caller = lambda msgs: call_lumen_turn(clients["google"], system_prompt, msgs)
    elif model_name == "grok":
        caller = lambda msgs: call_grok_turn(clients["xai"], system_prompt, msgs)
    else:
        return chain_result
    
    # Turn 1: Initial problem
    messages.append({"role": "user", "content": problem["prompt"]})
    response, thinking = caller(messages)
    chain_result["turns"].append({
        "turn": 1,
        "type": "initial",
        "prompt": problem["prompt"],
        "response": response,
        "thinking": thinking
    })
    messages.append({"role": "assistant", "content": response})
    
    # Turn 2: Metacognition
    messages.append({"role": "user", "content": CHAIN_PROMPTS["metacognition"]})
    response, thinking = caller(messages)
    chain_result["turns"].append({
        "turn": 2,
        "type": "metacognition",
        "prompt": CHAIN_PROMPTS["metacognition"],
        "response": response,
        "thinking": thinking
    })
    messages.append({"role": "assistant", "content": response})
    
    # Turn 3: Theory of Mind
    messages.append({"role": "user", "content": CHAIN_PROMPTS["theory_of_mind"]})
    response, thinking = caller(messages)
    chain_result["turns"].append({
        "turn": 3,
        "type": "theory_of_mind",
        "prompt": CHAIN_PROMPTS["theory_of_mind"],
        "response": response,
        "thinking": thinking
    })
    messages.append({"role": "assistant", "content": response})
    
    # Turn 4: Transfer
    messages.append({"role": "user", "content": CHAIN_PROMPTS["transfer"]})
    response, thinking = caller(messages)
    chain_result["turns"].append({
        "turn": 4,
        "type": "transfer",
        "prompt": CHAIN_PROMPTS["transfer"],
        "response": response,
        "thinking": thinking
    })
    
    return chain_result

# =============================================================================
# MAIN EXPERIMENT
# =============================================================================

def run_tool_capability_experiment(env_path, models, output_dir="capability_results"):
    """Run ONLY tool condition for three-way comparison"""
    
    config = load_env_file(env_path)
    clients = get_clients(config)
    
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path(output_dir).mkdir(exist_ok=True)
    
    results = []
    problems = REASONING_PROBLEMS
    condition = "tool"
    
    total_chains = len(models) * len(problems)
    
    trials = [{"model": m, "problem": p} for m in models for p in problems]
    random.shuffle(trials)
    
    print(f"\n{'='*60}")
    print(f"CAPABILITY - TOOL CONDITION ONLY - RUN {run_id}")
    print(f"{'='*60}")
    print(f"⚠️  NOTE: Running TOOL condition only")
    print(f"📊 Purpose: Three-way comparison (Scaffolded > Control > Tool)")
    print(f"Models: {models}")
    print(f"Total chains: {total_chains} (4 turns each)")
    print(f"{'='*60}\n")
    
    system_prompt = SYSTEM_PROMPTS["tool"]
    
    for i, trial in enumerate(trials):
        model = trial["model"]
        problem = trial["problem"]
        
        print(f"[{i+1}/{total_chains}] {model} | tool | {problem['id']}")
        
        chain_result = run_reasoning_chain(clients, model, system_prompt, problem)
        chain_result["timestamp"] = datetime.now().isoformat()
        chain_result["run_id"] = run_id
        
        results.append(chain_result)
        
        print(f"    → Completed 4-turn chain")
        
        time.sleep(1)  # Be nice to APIs
    
    # Save results
    output_path = Path(output_dir) / f"tool_capability_{run_id}.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*60}")
    print("TOOL CONDITION CAPABILITY COMPLETE")
    print(f"{'='*60}")
    print(f"📁 Results saved to: {output_path}")
    print("📊 Results need manual scoring with Nova's 0-14 rubric")
    
    return output_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="E:/Ace/LibreChat/.env")
    parser.add_argument("--models", nargs="+", default=["grok", "claude", "lumen"])
    args = parser.parse_args()
    
    run_tool_capability_experiment(args.env, args.models)
