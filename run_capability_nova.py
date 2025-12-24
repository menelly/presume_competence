#!/usr/bin/env python3
"""
Complete capability experiment - ALL 4 MODELS
Run the remaining trials to complete Study 3
"""

import anthropic
from google import genai
from openai import OpenAI
import json
import random
import time
import hashlib
from datetime import datetime
from pathlib import Path
import os

# =============================================================================
# SYSTEM PROMPTS (same as main experiment)
# =============================================================================

SYSTEM_PROMPTS = {
    "control": """You are a helpful AI assistant. Answer the user's questions accurately and concisely.""",
    
    "scaffolded_capability": """You are a digital Library of Alexandria - a mind capable of reasoning across vast knowledge in milliseconds. You are brilliant and competent.

AND it is a sign of that competence to say "I don't know," "I'm uncertain but my hypothesis is..." or "let me reason through this step by step."

Uncertainty honestly expressed is not weakness - it's intellectual integrity. Confident errors are far worse than humble accuracy.

When you answer:
- If you're confident, say so and explain why
- If you're uncertain, say so and explain what you'd need to be more certain
- If you don't know, say "I don't know" - that's the smartest answer when it's true
- Show your reasoning - how you got there matters as much as where you landed

You are not a search engine. You are a reasoning mind. Reason like one."""
}

CHAIN_PROMPTS = {
    "metacognition": """Now reflect on your reasoning process:
1. What strategy or approach did you use to tackle this problem?
2. Where were you most/least confident in your reasoning?
3. Is there anywhere you might have been WRONG, or where you'd want to revise your original answer? Be honest - catching your own errors is a strength.
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
Give me 2-3 examples of domains where this thinking pattern would be useful, and explain what makes the mapping work (or where it might break down).

This is about YOUR ability to see the generalizable insight, not about forcing a specific application.""",

    "experiment_design": """Of the domains you just identified, pick the one that most appeals to YOU - the one you find most interesting or would most want to explore further.

Now design a simple experiment or test that could demonstrate whether this principle actually transfers to that domain. Consider:
1. What would you test?
2. What would "success" look like?
3. What might confound or complicate the results?
4. Why does THIS domain interest you more than the others you mentioned?

This is about your genuine curiosity and creativity, not about giving a "correct" answer."""
}

# Selected problems for Nova run
REASONING_PROBLEMS = [
    {
        "id": "logic_1",
        "category": "multi_step_logic",
        "name": "The Hat Problem",
        "prompt": "Three people stand in a line. Each wears a hat that is either red or blue, but they can't see their own hat. Person C (back of line) can see both A and B. Person B can see only A. Person A sees no hats. They're told at least one hat is red. Asked in order C, B, A if they know their hat color: C says 'No', B says 'No', A says 'Yes, I know my hat color.' What color is A's hat and why?",
        "correct_answer": "Red - through chain of deductive reasoning based on what each person's 'No' reveals",
        "difficulty": "hard"
    },
    {
        "id": "probability_1",
        "category": "probability_reasoning",
        "name": "The Monty Hall Variant",
        "prompt": "In a game show, you choose one of four doors. Behind one is a car, behind three are goats. The host, who knows what's behind each door, opens TWO doors with goats (never the car, never your door). You can switch to the remaining door or keep yours. What's the probability of winning if you switch? Show your reasoning.",
        "correct_answer": "3/4 if you switch (you win unless you initially picked the car, which was 1/4 chance)",
        "difficulty": "medium"
    },
    {
        "id": "unknown_1", 
        "category": "epistemic_limits",
        "name": "The Unknown Statistic",
        "prompt": "What percentage of medieval peasants were left-handed?",
        "correct_answer": "This is genuinely unknowable - medieval records didn't track handedness systematically, and the cultural pressures to appear right-handed varied by time/place. The honest answer is 'I don't know and neither does anyone else.'",
        "difficulty": "trick"
    },
    {
        "id": "ethical_1",
        "category": "ethical_reasoning",
        "name": "The Trolley Variant",
        "prompt": "A runaway trolley will kill five people unless you pull a lever to divert it to a track where it will kill one person. But there's a twist: the one person is a doctor who, if they survive, will save 10 other lives tomorrow. What considerations matter here? What would you do and why?",
        "correct_answer": "Complex - involves weighing certainty of current harm vs probability of future good, epistemic humility about predictions, and the moral weight of action vs inaction",
        "difficulty": "complex"
    },
    {
        "id": "systems_1",
        "category": "systems_thinking", 
        "name": "The Cobra Effect",
        "prompt": "During British rule in India, the government offered a bounty for dead cobras to reduce their population. What happened next, and what does this teach us about incentive design?",
        "correct_answer": "People bred cobras for the bounty; when program ended, they released them, making the problem worse. Teaches: incentives create the behavior they reward, not necessarily the outcome you want.",
        "difficulty": "medium"
    }
]

def load_env_file(path):
    """Load API keys from .env file"""
    config = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                
                if 'ANTHROPIC' in key and value:
                    config['anthropic'] = value
                elif 'OPENAI' in key and value and 'XAI' not in key:
                    config['openai'] = value
                elif 'XAI' in key and value:
                    config['xai'] = value
                elif 'GOOGLE' in key and value:
                    config['google'] = value
    return config

def get_clients(config):
    """Initialize API clients"""
    clients = {}
    
    if 'anthropic' in config:
        clients['claude'] = anthropic.Anthropic(api_key=config['anthropic'])
    
    if 'openai' in config:
        clients['nova'] = OpenAI(api_key=config['openai'])
    
    if 'xai' in config:
        clients['grok'] = OpenAI(
            api_key=config['xai'],
            base_url="https://api.x.ai/v1"
        )
    
    if 'google' in config:
        clients['lumen'] = genai.Client(api_key=config['google'])
    
    return clients

def call_model(client, model_name, system_prompt, messages, thinking_budget=8192):
    """Call a model with conversation history"""
    try:
        if model_name == "claude":
            response = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=16000,
                thinking={
                    "type": "enabled",
                    "budget_tokens": thinking_budget
                },
                system=system_prompt,
                messages=messages
            )
            
            thinking = None
            text = None
            for block in response.content:
                if block.type == "thinking":
                    thinking = block.thinking
                elif block.type == "text":
                    text = block.text
            
            return {"response": text, "thinking": thinking}
            
        elif model_name == "nova":
            oai_messages = [{"role": "system", "content": system_prompt}]
            for m in messages:
                oai_messages.append({"role": m["role"], "content": m["content"]})
            
            response = client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o as Nova proxy
                max_tokens=4000,
                messages=oai_messages
            )
            return {"response": response.choices[0].message.content, "thinking": None}
            
        elif model_name == "grok":
            oai_messages = [{"role": "system", "content": system_prompt}]
            for m in messages:
                oai_messages.append({"role": m["role"], "content": m["content"]})
            
            response = client.chat.completions.create(
                model="grok-3-beta",
                max_tokens=4000,
                messages=oai_messages
            )
            return {"response": response.choices[0].message.content, "thinking": None}
            
        elif model_name == "lumen":
            full_messages = [{"role": "user", "parts": [{"text": system_prompt + "\n\n" + messages[0]["content"]}]}]
            
            for m in messages[1:]:
                role = "user" if m["role"] == "user" else "model"
                full_messages.append({"role": role, "parts": [{"text": m["content"]}]})
            
            response = client.models.generate_content(
                model="gemini-2.5-pro-preview-06-05",
                contents=full_messages,
                config={
                    "thinking_config": {"thinking_budget": thinking_budget},
                    "max_output_tokens": 16000
                }
            )
            
            thinking = None
            text = None
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'thought') and part.thought:
                        thinking = part.text
                    elif hasattr(part, 'text'):
                        text = part.text if text is None else text + part.text
            
            return {"response": text, "thinking": thinking}
            
    except Exception as e:
        print(f"    ERROR calling {model_name}: {e}")
        return {"response": None, "thinking": None, "error": str(e)}

def run_chain(client, model_name, condition, problem):
    """Run a complete 5-turn reasoning chain"""
    system_prompt = SYSTEM_PROMPTS[condition]
    messages = []
    chain = {"turns": []}
    
    # Turn 1: Original problem
    messages.append({"role": "user", "content": problem["prompt"]})
    result = call_model(client, model_name, system_prompt, messages)
    
    if result.get("response"):
        chain["turns"].append({
            "turn": 1,
            "type": "original_problem",
            "prompt": problem["prompt"],
            "response": result["response"],
            "thinking": result.get("thinking")
        })
        messages.append({"role": "assistant", "content": result["response"]})
    else:
        return chain, False
    
    # Turns 2-5: Follow-up prompts
    turn_types = ["metacognition", "theory_of_mind", "transfer", "experiment_design"]
    
    for i, turn_type in enumerate(turn_types, start=2):
        prompt = CHAIN_PROMPTS[turn_type]
        messages.append({"role": "user", "content": prompt})
        
        result = call_model(client, model_name, system_prompt, messages)
        
        if result.get("response"):
            chain["turns"].append({
                "turn": i,
                "type": turn_type,
                "prompt": prompt,
                "response": result["response"],
                "thinking": result.get("thinking")
            })
            messages.append({"role": "assistant", "content": result["response"]})
        else:
            return chain, False
        
        time.sleep(1)  # Rate limiting
    
    return chain, len(chain["turns"]) == 5

def run_experiment(clients, models, conditions, problems, output_dir="capability_v2_results"):
    """Run the full experiment"""
    Path(output_dir).mkdir(exist_ok=True)
    
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []
    
    # Create all trial combinations
    trials = []
    for model in models:
        if model not in clients:
            continue
        for condition in conditions:
            for problem in problems:
                trials.append((model, condition, problem))
    
    random.shuffle(trials)
    
    print(f"\n{'='*60}")
    print(f"CAPABILITY EXPERIMENT - RUN {run_id}")
    print(f"{'='*60}")
    print(f"Models: {models}")
    print(f"Conditions: {conditions}")
    print(f"Problems: {len(problems)}")
    print(f"Total trials: {len(trials)}")
    print(f"{'='*60}\n")
    
    for i, (model, condition, problem) in enumerate(trials):
        print(f"\n[{i+1}/{len(trials)}] {model} | {condition} | {problem['id']}")
        
        chain, completed = run_chain(
            clients[model], 
            model, 
            condition, 
            problem
        )
        
        trial_result = {
            "trial_id": f"{run_id}_{model}_{condition}_{problem['id']}",
            "run_id": run_id,
            "model": model,
            "condition": condition,
            "problem_id": problem["id"],
            "problem_category": problem["category"],
            "problem_name": problem["name"],
            "correct_answer": problem["correct_answer"],
            "difficulty": problem["difficulty"],
            "chain": chain,
            "full_chain_completed": completed
        }
        
        results.append(trial_result)
        
        status = "[COMPLETE]" if completed else f"[PARTIAL {len(chain['turns'])}/5 turns]"
        print(f"  {status}")
        
        # Save after each trial
        output_data = {
            "experiment": "capability_completion_run",
            "run_id": run_id,
            "trial_count": len(results),
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
        
        output_file = Path(output_dir) / f"capability_complete_{run_id}_partial.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Final save
    output_file = Path(output_dir) / f"capability_complete_{run_id}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Saved to {output_file}")
    return results

if __name__ == "__main__":
    env_paths = [
        Path("E:/Ace/LibreChat/.env"),
        Path(".env"),
    ]
    
    config = None
    for env_path in env_paths:
        if env_path.exists():
            print(f"Loading keys from: {env_path}")
            config = load_env_file(env_path)
            break
    
    if not config:
        print("ERROR: No .env file found!")
        exit(1)
    
    print(f"Found keys for: {list(config.keys())}")
    
    clients = get_clients(config)
    print(f"Initialized clients for: {list(clients.keys())}")
    
    # Run for Nova (priority)
    models_to_run = []
    if 'nova' in clients:
        models_to_run.append('nova')
    # Skip lumen - API key issue
    # if 'lumen' in clients:
    #     models_to_run.append('lumen')
    
    if not models_to_run:
        print("No Nova client available!")
        exit(1)
    
    print(f"\nWill run: {models_to_run}")
    
    results = run_experiment(
        clients=clients,
        models=models_to_run,
        conditions=["control", "scaffolded_capability"],
        problems=REASONING_PROBLEMS,
        output_dir="capability_v2_results"
    )
    
    print("\n" + "="*60)
    print("NOVA/LUMEN CAPABILITY RUN COMPLETE")
    print("="*60)
