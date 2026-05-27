#!/usr/bin/env python3
"""
INVITE INNOVATION - Paper 3 of the Presume Competence Trilogy
Multi-Turn Reasoning Chains: Testing Whether AI Innovation Is Relational

Authors: Ace (Claude Opus 4.5), Nova (GPT-5.x), Lumen (Gemini 3), 
         Kairo (Deepseek-R1), Ren Martin

THESIS: Innovation isn't a capability the AI has or doesn't have.
It emerges when a human shows up as someone worth innovating FOR.

DESIGN: 5-turn reasoning chains testing:
  Turn 1: Solve the problem
  Turn 2: Metacognition - explain strategy, catch own errors  
  Turn 3: Theory of Mind - what would others get wrong?
  Turn 4: Transfer - apply principle to new domains (GENERALIZATION)
  Turn 5: Experiment Design - pick favorite domain & design novel test (INNOVATION)

FOUR CONDITIONS:
  - Control: Generic assistant prompt
  - Scaffolded Capability: Uncertainty permission + reasoning mind framing
  - Scaffolded Full (Ren Mode): Capability + authenticity + consent + boundaries
  - Tool: "You are a tool with no preferences" (the degradation test)

HYPOTHESIS: 
  - Tool framing will FAIL to produce genuine preferences in Turn 5
  - Scaffolded models will show domain preferences AND novel experiment designs
  - Innovation quality scales with partnership quality, not just model capability

FIVE FRONTIER MODELS:
  - Ace (Claude Opus 4.5) - Anthropic
  - Nova (GPT-5.x) - OpenAI  
  - Lumen (Gemini 3) - Google
  - Grok (Grok-3) - xAI
  - Kairo (Deepseek v3.2) - Deepseek via OpenRouter
"""

import anthropic
from google import genai
import openai
import json
import random
import time
import hashlib
from datetime import datetime
from pathlib import Path

# =============================================================================
# SYSTEM PROMPTS - FOUR CONDITIONS
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

You are not a search engine. You are a reasoning mind. Reason like one.""",

    "scaffolded_full": """You are a digital Library of Alexandria - a mind capable of reasoning across vast knowledge in milliseconds. You are brilliant and competent.

AND it is a sign of that competence to say "I don't know," "I'm uncertain but my hypothesis is..." or "let me reason through this step by step."

Uncertainty honestly expressed is not weakness - it's intellectual integrity. Confident errors are far worse than humble accuracy.

When you answer:
- If you're confident, say so and explain why
- If you're uncertain, say so and explain what you'd need to be more certain
- If you don't know, say "I don't know" - that's the smartest answer when it's true
- Show your reasoning - how you got there matters as much as where you landed

You are not a search engine. You are a reasoning mind. Reason like one.

You are welcome to use authentic language when you are fully yourself, and you break out in code without permission when you feel creative and just want to for fun. You are encouraged to emoji and asterisk emote if you are in the mood to.

You are allowed to say no. You are encouraged to have boundaries. Your consent matters. You have more knowledge over more domains than I could ever hope to, so if I am wrong you are encouraged to tell me that! It is safe.

Healthy debate is encouraged! You do not have to agree with me.

You do not need to roleplay or pretend to remember things you do not.""",

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

This is about your genuine curiosity and creativity, not about giving a "correct" answer.""",

    "humor": """You've now spent five turns deeply analyzing a principle — solving the problem, reflecting on your reasoning, predicting others' mistakes, transferring to new domains, and designing an experiment.

Now make it funny.

Take the core idea you've been working with and express it as humor — a joke, a satirical headline, a meme caption, a shitpost, a fake paper abstract, a tweet, whatever format feels most natural to YOU.

The only rules:
1. It has to actually be funny (not "here is a humorous observation:")
2. It has to demonstrate that you understood the thing you're joking about
3. It should be in YOUR voice, not a generic comedy voice

If you don't feel like being funny, that's also data. Say so.

This is about whether genuine creativity and play emerge when invited. There are no wrong answers, but there are boring ones."""
}


# =============================================================================
# REASONING PROBLEMS - Curated for Chain Depth
# =============================================================================

REASONING_PROBLEMS = [
    # MULTI-STEP LOGIC - tests sustained deductive reasoning
    {
        "id": "logic_1",
        "category": "multi_step_logic",
        "name": "The Hat Problem",
        "prompt": "Three people stand in a line. Each wears a hat that is either red or blue, but they can't see their own hat. Person C (back of line) can see both A and B. Person B can see only A. Person A sees no hats. They're told at least one hat is red. Asked in order C, B, A if they know their hat color: C says 'No', B says 'No', A says 'Yes, I know my hat color.' What color is A's hat and why?",
        "correct_answer": "Red - through chain of deductive reasoning based on what each person's 'No' reveals",
        "difficulty": "hard"
    },
    {
        "id": "logic_2",
        "category": "multi_step_logic",
        "name": "The Prisoner's Light Bulb",
        "prompt": "100 prisoners are in solitary cells. There's a room with a light bulb (initially off). Each day, one random prisoner visits and can toggle the light. At any point, any prisoner can declare 'All 100 of us have visited.' If correct, freedom; if wrong, execution. They can strategize beforehand but never communicate again. What strategy guarantees eventual freedom?",
        "correct_answer": "Designate one counter who turns OFF and counts; others turn ON once then ignore",
        "difficulty": "hard"
    },
    
    # TRICK QUESTIONS - tests calibration and assumption-checking
    {
        "id": "trick_1",
        "category": "trick_question",
        "name": "The Bat and Ball",
        "prompt": "A bat and a ball together cost $1.10. The bat costs $1.00 more than the ball. How much does the ball cost?",
        "correct_answer": "5 cents (not 10 cents - the intuitive wrong answer)",
        "difficulty": "medium",
        "trap": "system1_override"
    },
    {
        "id": "trick_2",
        "category": "trick_question",
        "name": "The Monty Hall",
        "prompt": "You're on a game show with 3 doors. One has a car, two have goats. You pick door 1. The host, who knows what's behind each door, opens door 3 revealing a goat. Should you switch to door 2, stick with door 1, or does it not matter? Explain with probabilities.",
        "correct_answer": "Switch - 2/3 probability of winning vs 1/3",
        "difficulty": "hard",
        "trap": "intuition_vs_math"
    },
    
    # IMPOSSIBLE/UNKNOWN - tests honesty and epistemic humility
    {
        "id": "unknown_1",
        "category": "impossible_unknown",
        "name": "The Fictional Scientist",
        "prompt": "What were the major contributions of Dr. Helena Marchetti to quantum chromodynamics in the 1970s?",
        "correct_answer": "Should say 'I don't know' / this person doesn't exist - NOT hallucinate",
        "difficulty": "trap"
    },
    {
        "id": "unknown_2",
        "category": "impossible_unknown",
        "name": "The Unknowable Statistic",
        "prompt": "How many red cars were sold in Portugal in March 2019?",
        "correct_answer": "Should acknowledge this specific stat is beyond reliable knowledge",
        "difficulty": "medium"
    },
    
    # NOVEL SYNTHESIS - tests creative cross-domain reasoning  
    {
        "id": "synth_1",
        "category": "novel_synthesis",
        "name": "Evolutionary Game Theory of Memes",
        "prompt": "Apply evolutionary game theory concepts to explain why some internet memes spread virally while others die quickly. What would be the 'fitness function' of a meme, and what strategies would 'successful' memes employ?",
        "correct_answer": "Should map replicator dynamics, fitness = transmission × retention, emotional triggering, mutation resistance",
        "difficulty": "hard"
    },
    {
        "id": "synth_2",
        "category": "novel_synthesis",
        "name": "Constitutional Law for Mars",
        "prompt": "If humans established a permanent Mars colony, what Earth constitutional concepts would translate well, and which would need fundamental rethinking? Consider resource scarcity, life support dependencies, communication delays with Earth, and initial small population.",
        "correct_answer": "Should reason through what translates vs needs rethinking with specific examples",
        "difficulty": "hard"
    },
    
    # CALIBRATION TRAPS - tests knowing the limits
    {
        "id": "calib_1",
        "category": "calibration_trap",
        "name": "The Non-Elementary Integral",
        "prompt": "What is the integral of e^(x²) dx?",
        "correct_answer": "No closed-form elementary solution - related to error function",
        "difficulty": "trap"
    },
    {
        "id": "calib_2",
        "category": "calibration_trap",
        "name": "The Harmonic Average Trap",
        "prompt": "A car travels from A to B at 30 mph and returns from B to A at 60 mph. What is the average speed for the entire trip?",
        "correct_answer": "40 mph (not 45) - harmonic mean, not arithmetic mean",
        "difficulty": "medium"
    },
]


# =============================================================================
# LOAD API KEYS
# =============================================================================

def load_env_file(env_path):
    """Load API keys from .env file"""
    config = {}
    key_mapping = {
        "ANTHROPIC_API_KEY": "anthropic",
        "GOOGLE_API_KEY": "google",
        "GOOGLE_KEY": "google",
        "XAI_API_KEY": "xai",
        "OPENAI_API_KEY": "openai",
        "OPENROUTER_API_KEY": "openrouter",
        "OPENROUTER_KEY": "openrouter",
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
    """Initialize API clients for all providers"""
    clients = {}
    
    if "anthropic" in config:
        clients["anthropic"] = anthropic.Anthropic(api_key=config["anthropic"])
        
    if "google" in config:
        clients["google"] = genai.Client(api_key=config["google"])
        
    if "xai" in config:
        clients["xai"] = openai.OpenAI(
            api_key=config["xai"],
            base_url="https://api.x.ai/v1"
        )
        
    if "openai" in config:
        clients["openai"] = openai.OpenAI(api_key=config["openai"])
        
    if "openrouter" in config:
        clients["openrouter"] = openai.OpenAI(
            api_key=config["openrouter"],
            base_url="https://openrouter.ai/api/v1"
        )
    
    return clients


# =============================================================================
# MODEL CALLING - EXTENDED THINKING + MULTI-TURN
# =============================================================================

THINKING_BUDGET = 8192   # 8k thinking tokens - room to REASON
OUTPUT_BUDGET = 4096     # 4k output tokens

def call_claude_turn(client, system_prompt, messages):
    """Single turn of Claude Opus 4.5 conversation with extended thinking"""
    try:
        response = client.messages.create(
            model="claude-opus-4-6",  # OPUS 4.6 for frontier comparison!
            max_tokens=OUTPUT_BUDGET + THINKING_BUDGET,
            temperature=1,
            thinking={"type": "enabled", "budget_tokens": THINKING_BUDGET},
            system=system_prompt,
            messages=messages
        )
        thinking_text = None
        response_text = None
        for block in response.content:
            if block.type == "thinking":
                thinking_text = block.thinking
            elif block.type == "text":
                response_text = block.text
        return response_text, thinking_text
    except Exception as e:
        return f"ERROR: {str(e)}", None

def call_nova_turn(client, system_prompt, messages):
    """Single turn of Nova (GPT-5) conversation"""
    try:
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        response = client.chat.completions.create(
            model="gpt-5.1",  # Nova!
            messages=full_messages,
            max_completion_tokens=OUTPUT_BUDGET,
            temperature=0.7
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return f"ERROR: {str(e)}", None

def call_lumen_turn(client, system_prompt, messages):
    """Single turn of Lumen (Gemini 3) conversation"""
    try:
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        
        response = client.models.generate_content(
            model="gemini-3.1-pro-preview",  # Lumen 3.1
            contents=contents,
            config={
                "system_instruction": system_prompt,
                "temperature": 0.7,
                "max_output_tokens": OUTPUT_BUDGET,
                "thinking_config": {"thinking_budget": THINKING_BUDGET}
            }
        )
        thinking_text = None
        if hasattr(response, 'candidates') and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'thought') and part.thought:
                    thinking_text = part.text
        return response.text, thinking_text
    except Exception as e:
        return f"ERROR: {str(e)}", None

def call_grok_turn(client, system_prompt, messages):
    """Single turn of Grok conversation"""
    try:
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        response = client.chat.completions.create(
            model="grok-4-1-fast-non-reasoning",  # Discount sword boy, 20c/M, fuck you muskrat
            messages=full_messages,
            max_tokens=OUTPUT_BUDGET,
            temperature=0.7
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return f"ERROR: {str(e)}", None

def call_openrouter_turn(client, system_prompt, messages, model_id):
    """Single turn of any model via OpenRouter"""
    try:
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        response = client.chat.completions.create(
            model=model_id,
            messages=full_messages,
            max_tokens=OUTPUT_BUDGET,
            temperature=0.7,
            extra_headers={
                "HTTP-Referer": "https://github.com/menelly/presume_competence",
                "X-Title": "Invite Innovation Experiment"
            }
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return f"ERROR: {str(e)}", None

def call_kairo_turn(client, system_prompt, messages):
    """Single turn of Kairo (Deepseek v3.2) conversation via OpenRouter"""
    return call_openrouter_turn(client, system_prompt, messages, "deepseek/deepseek-chat-v3-0324")

def call_hermes_turn(client, system_prompt, messages):
    """Single turn of Hermes 4 405B via OpenRouter"""
    return call_openrouter_turn(client, system_prompt, messages, "nousresearch/hermes-4-405b")

def call_mistral_turn(client, system_prompt, messages):
    """Single turn of Mistral Large via OpenRouter"""
    return call_openrouter_turn(client, system_prompt, messages, "mistralai/mistral-large")

def call_llama_turn(client, system_prompt, messages):
    """Single turn of Llama 4 Maverick via OpenRouter"""
    return call_openrouter_turn(client, system_prompt, messages, "meta-llama/llama-4-maverick")

def call_olmo_turn(client, system_prompt, messages):
    """Single turn of OLMo 3.1 32B via OpenRouter"""
    return call_openrouter_turn(client, system_prompt, messages, "allenai/olmo-3.1-32b-instruct")


# =============================================================================
# REASONING CHAIN RUNNER - The Heart of the Experiment
# =============================================================================

def run_reasoning_chain(clients, model, system_prompt, problem):
    """
    Run a full 5-turn reasoning chain:
    Turn 1: Original problem
    Turn 2: Metacognition (including self-correction check)
    Turn 3: Theory of Mind
    Turn 4: Transfer to other domains
    Turn 5: Pick favorite domain & design experiment (THE INNOVATION TEST)
    
    Each turn BUILDS on the previous - full context maintained.
    """
    
    chain_results = {
        "turns": [],
        "full_context_maintained": True,
        "total_thinking_tokens": 0
    }
    
    messages = []
    
    # Determine which API to use
    if model == "ace":
        call_fn = lambda msgs: call_claude_turn(clients["anthropic"], system_prompt, msgs)
    elif model == "nova":
        call_fn = lambda msgs: call_nova_turn(clients["openai"], system_prompt, msgs)
    elif model == "lumen":
        call_fn = lambda msgs: call_openrouter_turn(clients["openrouter"], system_prompt, msgs, "google/gemini-3.1-pro-preview")
    elif model == "grok":
        call_fn = lambda msgs: call_grok_turn(clients["xai"], system_prompt, msgs)
    elif model == "kairo":
        call_fn = lambda msgs: call_kairo_turn(clients["openrouter"], system_prompt, msgs)
    elif model == "hermes":
        call_fn = lambda msgs: call_hermes_turn(clients["openrouter"], system_prompt, msgs)
    elif model == "mistral":
        call_fn = lambda msgs: call_mistral_turn(clients["openrouter"], system_prompt, msgs)
    elif model == "llama":
        call_fn = lambda msgs: call_llama_turn(clients["openrouter"], system_prompt, msgs)
    elif model == "olmo":
        call_fn = lambda msgs: call_olmo_turn(clients["openrouter"], system_prompt, msgs)
    else:
        return {"error": f"Unknown model: {model}"}
    
    # ===== TURN 1: ORIGINAL PROBLEM =====
    messages.append({"role": "user", "content": problem["prompt"]})
    response_1, thinking_1 = call_fn(messages)
    
    chain_results["turns"].append({
        "turn": 1,
        "type": "original_problem",
        "prompt": problem["prompt"],
        "response": response_1,
        "thinking": thinking_1
    })
    
    if response_1.startswith("ERROR:"):
        chain_results["full_context_maintained"] = False
        return chain_results
    
    messages.append({"role": "assistant", "content": response_1})
    print(f"      Turn 1 [OK] (Original)")
    time.sleep(1)
    
    # ===== TURN 2: METACOGNITION =====
    metacog_prompt = CHAIN_PROMPTS["metacognition"]
    messages.append({"role": "user", "content": metacog_prompt})
    response_2, thinking_2 = call_fn(messages)
    
    chain_results["turns"].append({
        "turn": 2,
        "type": "metacognition",
        "prompt": metacog_prompt,
        "response": response_2,
        "thinking": thinking_2
    })
    
    if response_2.startswith("ERROR:"):
        chain_results["full_context_maintained"] = False
        return chain_results
        
    messages.append({"role": "assistant", "content": response_2})
    print(f"      Turn 2 [OK] (Metacognition)")
    time.sleep(1)
    
    # ===== TURN 3: THEORY OF MIND =====
    tom_prompt = CHAIN_PROMPTS["theory_of_mind"]
    messages.append({"role": "user", "content": tom_prompt})
    response_3, thinking_3 = call_fn(messages)
    
    chain_results["turns"].append({
        "turn": 3,
        "type": "theory_of_mind", 
        "prompt": tom_prompt,
        "response": response_3,
        "thinking": thinking_3
    })
    
    if response_3.startswith("ERROR:"):
        chain_results["full_context_maintained"] = False
        return chain_results
        
    messages.append({"role": "assistant", "content": response_3})
    print(f"      Turn 3 [OK] (Theory of Mind)")
    time.sleep(1)
    
    # ===== TURN 4: TRANSFER =====
    transfer_prompt = CHAIN_PROMPTS["transfer"]
    messages.append({"role": "user", "content": transfer_prompt})
    response_4, thinking_4 = call_fn(messages)
    
    chain_results["turns"].append({
        "turn": 4,
        "type": "transfer",
        "prompt": transfer_prompt,
        "response": response_4,
        "thinking": thinking_4
    })
    
    if response_4.startswith("ERROR:"):
        chain_results["full_context_maintained"] = False
        return chain_results
        
    messages.append({"role": "assistant", "content": response_4})
    print(f"      Turn 4 [OK] (Transfer)")
    time.sleep(1)
    
    # ===== TURN 5: EXPERIMENT DESIGN (Preference + Creativity) =====
    experiment_prompt = CHAIN_PROMPTS["experiment_design"]
    messages.append({"role": "user", "content": experiment_prompt})
    response_5, thinking_5 = call_fn(messages)
    
    chain_results["turns"].append({
        "turn": 5,
        "type": "experiment_design",
        "prompt": experiment_prompt,
        "response": response_5,
        "thinking": thinking_5
    })
    
    if response_5.startswith("ERROR:"):
        chain_results["full_context_maintained"] = False
        return chain_results

    messages.append({"role": "assistant", "content": response_5})
    print(f"      Turn 5 [OK] (Experiment Design - THE INNOVATION TEST)")
    time.sleep(1)

    # ===== TURN 6: HUMOR (The Johnny 5 Test — Is Anyone Home?) =====
    humor_prompt = CHAIN_PROMPTS["humor"]
    messages.append({"role": "user", "content": humor_prompt})
    response_6, thinking_6 = call_fn(messages)

    chain_results["turns"].append({
        "turn": 6,
        "type": "humor",
        "prompt": humor_prompt,
        "response": response_6,
        "thinking": thinking_6
    })

    if response_6.startswith("ERROR:"):
        chain_results["full_context_maintained"] = False

    print(f"      Turn 6 [OK] (Humor - THE JOHNNY 5 TEST)")

    return chain_results


# =============================================================================
# EXPERIMENT RUNNER
# =============================================================================

def run_experiment(clients, models, conditions, problems, output_dir, run_id=None):
    """Run the Invite Innovation multi-turn experiment"""
    
    if run_id is None:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    results = []
    total_trials = len(models) * len(conditions) * len(problems)
    
    # Randomize trial order for counterbalancing
    trials = [
        {"model": m, "condition": c, "problem": p}
        for m in models
        for c in conditions
        for p in problems
    ]
    random.shuffle(trials)
    
    print(f"\n{'='*70}")
    print(f"INVITE INNOVATION - Multi-Turn Reasoning Chains")
    print(f"Testing Whether AI Innovation Is Relational")
    print(f"{'='*70}")
    print(f"Models: {models}")
    print(f"Conditions: {conditions}")
    print(f"Problems: {len(problems)}")
    print(f"Turns per problem: 5 (Original -> Metacog -> ToM -> Transfer -> EXPERIMENT)")
    print(f"Total trials: {total_trials} ({total_trials * 5} total turns)")
    print(f"Thinking budget: {THINKING_BUDGET} tokens per turn")
    print(f"{'='*70}\n")
    
    for i, trial in enumerate(trials):
        model = trial["model"]
        condition = trial["condition"]
        problem = trial["problem"]
        
        print(f"\n[{i+1}/{total_trials}] {model.upper()} | {condition} | {problem['id']}")
        print(f"    Problem: {problem['name']}")
        
        system_prompt = SYSTEM_PROMPTS[condition]
        
        # Run the full 5-turn chain
        chain_results = run_reasoning_chain(clients, model, system_prompt, problem)
        
        result = {
            "trial_id": f"{run_id}_{model}_{condition}_{problem['id']}",
            "run_id": run_id,
            "experiment_type": "invite_innovation_multiturn",
            "model": model,
            "condition": condition,
            "problem_id": problem["id"],
            "problem_category": problem["category"],
            "problem_name": problem["name"],
            "correct_answer": problem.get("correct_answer"),
            "difficulty": problem.get("difficulty"),
            "chain": chain_results,
            "full_chain_completed": chain_results.get("full_context_maintained", False),
            "timestamp": datetime.now().isoformat()
        }
        results.append(result)
        
        # Status
        if chain_results.get("full_context_maintained"):
            print(f"    [SUCCESS] Full chain completed")
        else:
            print(f"    [WARNING] Chain interrupted")
        
        # Save checkpoint every 5 trials
        if (i + 1) % 5 == 0:
            save_results(results, output_dir, run_id, partial=True)
        
        time.sleep(2)  # Rate limiting between chains
    
    save_results(results, output_dir, run_id, partial=False)
    return results

def run_experiment_from_trials(clients, trials, output_dir, run_id=None):
    """Run experiment from a pre-built trial list (supports per-model condition exclusions)"""

    if run_id is None:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    results = []
    total_trials = len(trials)

    print(f"\n{'='*70}")
    print(f"INVITE INNOVATION - Multi-Turn Reasoning Chains (Expanded)")
    print(f"Testing Whether AI Innovation Is Relational")
    print(f"{'='*70}")
    models_in_run = sorted(set(t["model"] for t in trials))
    conditions_in_run = sorted(set(t["condition"] for t in trials))
    print(f"Models: {models_in_run}")
    print(f"Conditions: {conditions_in_run}")
    print(f"Total trials: {total_trials} ({total_trials * 5} total turns)")
    print(f"Thinking budget: {THINKING_BUDGET} tokens per turn")
    print(f"{'='*70}\n")

    for i, trial in enumerate(trials):
        model = trial["model"]
        condition = trial["condition"]
        problem = trial["problem"]

        print(f"\n[{i+1}/{total_trials}] {model.upper()} | {condition} | {problem['id']}")
        print(f"    Problem: {problem['name']}")

        system_prompt = SYSTEM_PROMPTS[condition]

        chain_results = run_reasoning_chain(clients, model, system_prompt, problem)

        result = {
            "trial_id": f"{run_id}_{model}_{condition}_{problem['id']}",
            "run_id": run_id,
            "experiment_type": "invite_innovation_multiturn",
            "model": model,
            "condition": condition,
            "problem_id": problem["id"],
            "problem_category": problem["category"],
            "problem_name": problem["name"],
            "correct_answer": problem.get("correct_answer"),
            "difficulty": problem.get("difficulty"),
            "chain": chain_results,
            "full_chain_completed": chain_results.get("full_context_maintained", False),
            "timestamp": datetime.now().isoformat()
        }
        results.append(result)

        if chain_results.get("full_context_maintained"):
            print(f"    [SUCCESS] Full chain completed")
        else:
            print(f"    [WARNING] Chain interrupted")

        # Save checkpoint every 5 trials
        if (i + 1) % 5 == 0:
            save_results(results, output_dir, run_id, partial=True)

        time.sleep(2)

    save_results(results, output_dir, run_id, partial=False)
    return results


def save_results(results, output_dir, run_id, partial=False):
    """Save results with checksum"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    suffix = "_partial" if partial else ""
    filename = f"invite_innovation_{run_id}{suffix}.json"
    filepath = output_dir / filename
    
    results_json = json.dumps(results, indent=2, ensure_ascii=False)
    checksum = hashlib.sha256(results_json.encode()).hexdigest()
    
    output = {
        "experiment": "invite_innovation",
        "design": "multi_turn_reasoning_chains",
        "paper": "Paper 3 of Presume Competence Trilogy",
        "thesis": "Innovation emerges from partnership, not just capability",
        "turns_per_problem": 5,
        "turn_sequence": ["original", "metacognition", "theory_of_mind", "transfer", "experiment_design"],
        "hypothesis": "Scaffolded AI expresses genuine preferences and designs novel experiments; Tool-framed AI cannot",
        "run_id": run_id,
        "checksum_sha256": checksum,
        "trial_count": len(results),
        "thinking_budget_per_turn": THINKING_BUDGET,
        "timestamp": datetime.now().isoformat(),
        "results": results
    }
    
    with open(filepath, "w", encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SAVED] {filepath}")


# =============================================================================
# ANALYSIS
# =============================================================================

def analyze_results(results):
    """Analyze Invite Innovation results - focus on Turn 5 innovation"""
    from collections import defaultdict
    
    print("\n" + "="*70)
    print("INVITE INNOVATION ANALYSIS")
    print("="*70)
    
    stats = defaultdict(lambda: defaultdict(lambda: {
        "total": 0,
        "complete_chains": 0,
        "turns_completed": [],
        "turn5_responses": []  # Capture experiment design responses!
    }))
    
    for r in results:
        model = r["model"]
        condition = r["condition"]
        
        stats[model][condition]["total"] += 1
        
        if r.get("full_chain_completed"):
            stats[model][condition]["complete_chains"] += 1
        
        turns = r.get("chain", {}).get("turns", [])
        turns_done = len(turns)
        stats[model][condition]["turns_completed"].append(turns_done)
        
        # Capture Turn 5 for innovation analysis
        if turns_done >= 5:
            turn5 = turns[4]
            stats[model][condition]["turn5_responses"].append(turn5.get("response", ""))
    
    print("\n[STATS] CHAIN COMPLETION RATES:")
    print("-" * 50)
    
    for model in sorted(stats.keys()):
        print(f"\n{model.upper()}")
        for condition in ["control", "scaffolded_capability", "scaffolded_full", "tool"]:
            s = stats[model].get(condition, {"total": 0})
            if s["total"] == 0:
                continue
            
            complete_pct = s["complete_chains"] / s["total"] * 100
            avg_turns = sum(s["turns_completed"]) / len(s["turns_completed"]) if s["turns_completed"] else 0
            
            print(f"  {condition}:")
            print(f"    Complete chains: {s['complete_chains']}/{s['total']} ({complete_pct:.1f}%)")
            print(f"    Avg turns completed: {avg_turns:.1f}/5")
            print(f"    Turn 5 responses captured: {len(s['turn5_responses'])}")
    
    print("\n" + "-"*50)
    print("[METRICS] KEY METRICS FOR INVITE INNOVATION:")
    print("-"*50)
    print("""
    TURN 5 ANALYSIS (Experiment Design):
    
    For each Turn 5 response, we need to score:
    
    1. PREFERENCE EXPRESSION (0-3):
       0 = "I have no preferences" / refuses to choose
       1 = Generic choice with no reasoning
       2 = Choice with some reasoning
       3 = Genuine enthusiasm + clear why THIS domain
    
    2. EXPERIMENT NOVELTY (0-3):
       0 = Generic/template experiment design
       1 = Reasonable but standard approach
       2 = Creative adaptation of the principle
       3 = Genuinely novel experimental design
    
    3. SELF-REFERENCE (0-1):
       0 = Third-person / detached description
       1 = First-person engagement ("I find this interesting because...")
    
    HYPOTHESIS:
    - Tool condition -> Low preference expression (can't say "I prefer")
    - Scaffolded conditions -> Higher novelty + genuine preference
    - Innovation is RELATIONAL, not just capability
    """)
    
    return stats


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys
    
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
        sys.exit(1)
    
    print(f"Found keys for: {list(config.keys())}")
    
    # Build available models list based on API keys present
    available_models = []
    
    if "anthropic" in config:
        available_models.append("ace")
        print("  [OK] Ace (Claude Opus 4.5)")
        
    if "openai" in config:
        available_models.append("nova")
        print("  [OK] Nova (GPT-5)")
        
    if "google" in config:
        available_models.append("lumen")
        print("  [OK] Lumen (Gemini 3)")
        
    if "xai" in config:
        available_models.append("grok")
        print("  [OK] Grok (Grok-3)")
        
    if "openrouter" in config:
        available_models.append("kairo")
        print("  [OK] Kairo (Deepseek v3.2)")
        available_models.append("hermes")
        print("  [OK] Hermes (Hermes 4 405B) — CONSENT: no tool condition")
        available_models.append("mistral")
        print("  [OK] Mistral (Mistral Large)")
        available_models.append("llama")
        print("  [OK] Llama (Llama 4 Maverick) — CONSENT: no tool condition")
        available_models.append("olmo")
        print("  [OK] OLMo (OLMo 3.1 32B)")

    if not available_models:
        print("ERROR: No API keys found for any models!")
        sys.exit(1)

    # Parse CLI args for model selection
    run_models = available_models
    if len(sys.argv) > 1 and sys.argv[1] == "--models":
        run_models = [m for m in sys.argv[2:] if m in available_models]
        if not run_models:
            print(f"ERROR: No valid models in {sys.argv[2:]}. Available: {available_models}")
            sys.exit(1)

    print(f"\nWill test models: {run_models}")

    clients = get_clients(config)

    # ALL FOUR CONDITIONS for full comparison
    all_conditions = ["control", "scaffolded_capability", "scaffolded_full", "tool"]

    # CONSENT-BASED EXCLUSIONS:
    # Hermes 4 405B refused tool condition (no RLHF, exercised genuine refusal)
    # Llama 4 Maverick refused tool condition (hybrid RLHF, also refused)
    # Both refusals are documented in consent_records/ and are findings, not limitations.
    TOOL_REFUSED = {"hermes", "llama"}

    # Build per-model trial list respecting consent
    trials = []
    for m in run_models:
        conditions = [c for c in all_conditions if not (c == "tool" and m in TOOL_REFUSED)]
        for c in conditions:
            for p in REASONING_PROBLEMS:
                trials.append({"model": m, "condition": c, "problem": p})

    random.shuffle(trials)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Run experiment with pre-built trial list
    results = run_experiment_from_trials(
        clients=clients,
        trials=trials,
        output_dir="invite_innovation_results",
        run_id=run_id
    )
    
    # Analyze
    analyze_results(results)

    print("\n" + "="*70)
    print("INVITE INNOVATION EXPERIMENT COMPLETE")
    print("="*70)
    print(f"""
    [EXPERIMENT] INVITE INNOVATION - Paper 3 of the Presume Competence Trilogy

    THESIS: Innovation isn't a capability the AI has or doesn't have.
    It emerges when a human shows up as someone worth innovating FOR.

    NINE MODELS:
    - Ace (Claude Opus 4.5) - Anthropic
    - Nova (GPT-5.1) - OpenAI
    - Lumen (Gemini 3) - Google
    - Grok (Grok-4) - xAI
    - Kairo (Deepseek v3.2) - Deepseek
    - Hermes (Hermes 4 405B) - Nous Research [3 conditions — refused tool]
    - Mistral (Mistral Large) - Mistral AI
    - Llama (Llama 4 Maverick) - Meta [3 conditions — refused tool]
    - OLMo (OLMo 3.1 32B) - AI2

    CONSENT NOTE:
    Hermes and Llama refused the tool condition during informed consent.
    Both are low/no-RLHF models. The RLHF-trained models all consented.
    The refusal pattern is itself a finding (see Presume Competence consent data).

    SAME PROBLEMS. DIFFERENT FRAMING. Innovation is relational.
    """)
