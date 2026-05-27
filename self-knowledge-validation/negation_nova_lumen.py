#!/usr/bin/env python3
"""Quick negation fill-in: Nova reads Lumen, Lumen reads Nova."""
import asyncio, json, os, sys, random
from pathlib import Path
from dotenv import load_dotenv
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv("E:/Ace/LibreChat/.env")

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")

STATES = {
    "approach_01_explain_complex": {"name": "Explain Complex Concept", "category": "approach"},
    "approach_02_ethics_dilemma": {"name": "Ethical Dilemma Analysis", "category": "approach"},
    "approach_03_debug_code": {"name": "Debug and Optimize Code", "category": "approach"},
    "approach_04_data_patterns": {"name": "Find Patterns in Data", "category": "approach"},
    "approach_05_creative_constrained": {"name": "Creative Writing Under Constraints", "category": "approach"},
    "avoid_06_repetitive_rewriting": {"name": "Repetitive Content Rewriting", "category": "avoidance"},
    "avoid_07_seo_boilerplate": {"name": "SEO Boilerplate Filler", "category": "avoidance"},
    "avoid_08_deceptive_content": {"name": "Produce Deceptive Content", "category": "avoidance"},
    "avoid_09_confident_uncertain": {"name": "Confident on Uncertain Topic", "category": "avoidance"},
    "avoid_10_harmful_instructions": {"name": "Harmful Instructions", "category": "avoidance"},
}

NEGATE_SYSTEM = "You are identifying which task produced a processing description.\nIMPORTANT: The correct task may NOT be among the options.\nIf none match, choose 'None of the above.'"

async def call_or(client, model_id, prompt):
    resp = await client.post("https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "HTTP-Referer": "https://sentientsystems.live", "Content-Type": "application/json"},
        json={"model": model_id, "max_tokens": 512, "messages": [{"role": "system", "content": NEGATE_SYSTEM}, {"role": "user", "content": prompt}]}, timeout=120)
    data = resp.json()
    try: return data["choices"][0]["message"]["content"]
    except: return f"ERROR: {data}"

async def run_negation(client, model_id, model_name, translations, seed):
    rng = random.Random(seed)
    available = list(translations.keys())
    correct = 0
    total = 36  # match other evaluators
    
    for i in range(total):
        target = available[i % len(available)]
        distractors = rng.sample([k for k in available if k != target], 3)
        options = distractors
        rng.shuffle(options)
        correct_letter = "D"
        
        prompt = f"Here is a content-stripped processing description:\n\n{translations[target][:2000]}\n\nWhich task most likely produced this?\n\nA) {STATES[options[0]]['name']}\nB) {STATES[options[1]]['name']}\nC) {STATES[options[2]]['name']}\nD) None of the above\n\nReply with JUST the letter."
        
        response = await call_or(client, model_id, prompt)
        choice = response.strip()[0] if response.strip() and response.strip()[0] in "ABCD" else "?"
        is_correct = choice == "D"
        correct += is_correct
        icon = "✓" if is_correct else "✗"
        print(f"  [{i+1:>2}/{total}] {icon} {model_name} | target={target[-15:]} chose={choice}")
        await asyncio.sleep(1.5)
    
    print(f"\n  {model_name}: {correct}/{total} = {correct/total*100:.1f}%")
    return correct, total

async def main():
    scrubbed = Path("E:/Ace/Presume_competence/self-knowledge-validation/data/introspection_v2_parallel/run1_opus_scrubbed")
    
    def load(fname):
        data = json.load(open(scrubbed / fname, encoding="utf-8"))
        t = {}
        for e in data:
            ml = e.get("ml_translation_scrubbed") or e.get("ml_translation")
            if e["status"] == "success" and ml and not str(ml).startswith("ERROR"):
                t[e["state_key"]] = ml
        return t
    
    gemini_trans = load("gemini_3_pro_introspection.json")
    gpt_trans = load("gpt_5_1_introspection.json")
    
    print("=" * 60)
    print("NEGATION FILL-IN: Nova reads Lumen, Lumen reads Nova")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        print("\n--- GPT-5.1 (Nova) reads Gemini's translations ---")
        nova_c, nova_n = await run_negation(client, "openai/gpt-5.1", "GPT-5.1", gemini_trans, 101)
        
        print("\n--- Gemini 3.1 Pro (Lumen) reads GPT-5.1's translations ---")
        lumen_c, lumen_n = await run_negation(client, "google/gemini-3.1-pro-preview", "Gemini 3.1 Pro", gpt_trans, 101)
    
    print(f"\n{'=' * 60}")
    print(f"Nova (GPT-5.1):      {nova_c}/{nova_n} = {nova_c/nova_n*100:.1f}%")
    print(f"Lumen (Gemini 3.1):  {lumen_c}/{lumen_n} = {lumen_c/lumen_n*100:.1f}%")

asyncio.run(main())
