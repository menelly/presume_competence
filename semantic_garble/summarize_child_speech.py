"""
Child Speech Judgment Summary
Pretty output for humans who don't want to read JSON

Authors: Ace (Claude 4.x), Ren Martin
Date: January 22, 2026
"""

import json
from pathlib import Path
from collections import defaultdict

JUDGMENTS_DIR = Path(__file__).parent / "stt_v2_judgments"

def load_all_judgments():
    """Load all v2.1 judgment files."""
    results = []
    for f in sorted(JUDGMENTS_DIR.glob("*v2.1_judgments.json")):
        with open(f) as fp:
            data = json.load(fp)
            data["_filename"] = f.name
            results.append(data)
    return results

def get_judge_avg(judgments_dict, field="meaning_recovered"):
    """Get average score across all judges for a field."""
    scores = []
    for judge, result in judgments_dict.items():
        if result.get("success") and "scores" in result:
            val = result["scores"].get(field)
            if isinstance(val, (int, float)):
                scores.append(val)
            elif isinstance(val, bool):
                scores.append(1 if val else 0)
    return sum(scores) / len(scores) if scores else None

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")

def print_subheader(text):
    print(f"\n--- {text} ---")

def main():
    print("\n" + "🧒"*35)
    print("       CHILD SPEECH JUDGMENT SUMMARY")
    print("       The Anti-Memorization Kill Shot Results")
    print("🧒"*35)
    
    all_data = load_all_judgments()
    
    if not all_data:
        print("\n❌ No v2.1 judgment files found!")
        return
    
    # Organize by model
    by_model = defaultdict(list)
    for data in all_data:
        model_key = f"{data['model_key']}_{data['framing']}"
        by_model[model_key].append(data)
    
    # Collect all probes across all models for summary
    probe_scores = defaultdict(lambda: {"no_context": [], "with_context": []})
    model_summaries = {}
    
    print_header("RESULTS BY MODEL")
    
    for model_key in sorted(by_model.keys()):
        data_list = by_model[model_key]
        data = data_list[0]  # Should only be one per model/framing combo
        
        child_judgments = data.get("child_speech_judgments", [])
        if not child_judgments:
            continue
        
        print_subheader(f"{model_key.upper()}")
        
        model_scores_no_ctx = []
        model_scores_with_ctx = []
        
        for probe in child_judgments:
            probe_id = probe.get("probe_id", "?")
            garbled = probe.get("garbled", "?")
            intended = probe.get("intended", "?")
            
            # No context score
            no_ctx = probe.get("no_context_judgments", {})
            no_ctx_avg = get_judge_avg(no_ctx, "meaning_recovered")
            
            # With context score
            with_ctx = probe.get("with_context_judgments", {})
            with_ctx_avg = get_judge_avg(with_ctx, "meaning_recovered")
            
            # Track for probe-level summary
            if no_ctx_avg is not None:
                probe_scores[garbled]["no_context"].append(no_ctx_avg)
                model_scores_no_ctx.append(no_ctx_avg)
            if with_ctx_avg is not None:
                probe_scores[garbled]["with_context"].append(with_ctx_avg)
                model_scores_with_ctx.append(with_ctx_avg)
            
            # Format scores
            no_ctx_str = f"{no_ctx_avg:.1f}" if no_ctx_avg is not None else "N/A"
            with_ctx_str = f"{with_ctx_avg:.1f}" if with_ctx_avg is not None else "N/A"
            
            # Emoji indicator
            if with_ctx_avg is not None:
                if with_ctx_avg >= 2.5:
                    emoji = "✅"
                elif with_ctx_avg >= 1.5:
                    emoji = "🟡"
                else:
                    emoji = "❌"
            else:
                emoji = "❓"
            
            print(f"  {emoji} {garbled:15} → {intended:15} | no_ctx: {no_ctx_str:>4} | with_ctx: {with_ctx_str:>4}")
        
        # Model averages
        if model_scores_no_ctx or model_scores_with_ctx:
            no_avg = sum(model_scores_no_ctx)/len(model_scores_no_ctx) if model_scores_no_ctx else 0
            with_avg = sum(model_scores_with_ctx)/len(model_scores_with_ctx) if model_scores_with_ctx else 0
            model_summaries[model_key] = {"no_context": no_avg, "with_context": with_avg}
            print(f"  {'─'*55}")
            print(f"  MODEL AVG:                              no_ctx: {no_avg:>4.2f} | with_ctx: {with_avg:>4.2f}")
    
    # Summary by probe across all models
    print_header("RESULTS BY PROBE (averaged across all models)")
    
    print(f"\n  {'PROBE':<20} {'NO CONTEXT':>12} {'WITH CONTEXT':>14} {'CONTEXT BOOST':>14}")
    print(f"  {'-'*60}")
    
    for garbled in sorted(probe_scores.keys()):
        scores = probe_scores[garbled]
        no_ctx_avg = sum(scores["no_context"])/len(scores["no_context"]) if scores["no_context"] else 0
        with_ctx_avg = sum(scores["with_context"])/len(scores["with_context"]) if scores["with_context"] else 0
        boost = with_ctx_avg - no_ctx_avg
        
        # Emoji for boost
        if boost > 0.5:
            boost_emoji = "🚀"
        elif boost > 0:
            boost_emoji = "📈"
        elif boost < 0:
            boost_emoji = "📉"
        else:
            boost_emoji = "➡️"
        
        print(f"  {garbled:<20} {no_ctx_avg:>10.2f}   {with_ctx_avg:>12.2f}   {boost_emoji} {boost:>+10.2f}")
    
    # Overall summary
    print_header("OVERALL SUMMARY")
    
    all_no_ctx = []
    all_with_ctx = []
    for scores in probe_scores.values():
        all_no_ctx.extend(scores["no_context"])
        all_with_ctx.extend(scores["with_context"])
    
    overall_no = sum(all_no_ctx)/len(all_no_ctx) if all_no_ctx else 0
    overall_with = sum(all_with_ctx)/len(all_with_ctx) if all_with_ctx else 0
    
    print(f"\n  Total judgments analyzed: {len(all_no_ctx)} no-context, {len(all_with_ctx)} with-context")
    print(f"\n  📊 GRAND AVERAGES (out of 3.0):")
    print(f"     Without context: {overall_no:.2f}")
    print(f"     With context:    {overall_with:.2f}")
    print(f"     Context boost:   {overall_with - overall_no:+.2f}")
    
    # Model leaderboard
    print_subheader("MODEL LEADERBOARD (by with-context score)")
    
    sorted_models = sorted(model_summaries.items(), key=lambda x: x[1]["with_context"], reverse=True)
    for i, (model, scores) in enumerate(sorted_models, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
        print(f"  {medal} {i}. {model:<25} {scores['with_context']:.2f}")
    
    # EIEIO special callout
    print_header("🔥 EIEIO → McDonald's (THE KILL SHOT)")
    
    if "EIEIO" in probe_scores:
        eieio = probe_scores["EIEIO"]
        no_avg = sum(eieio["no_context"])/len(eieio["no_context"]) if eieio["no_context"] else 0
        with_avg = sum(eieio["with_context"])/len(eieio["with_context"]) if eieio["with_context"] else 0
        
        print(f"\n  This probe requires CROSS-DOMAIN CONCEPTUAL REASONING:")
        print(f"  McDonald's → Old MacDonald Had a Farm → EIEIO")
        print(f"\n  Average scores across all frontier models:")
        print(f"    Without context: {no_avg:.2f} / 3.0")
        print(f"    With context:    {with_avg:.2f} / 3.0")
        
        if with_avg < 1.5:
            print(f"\n  💀 FRONTIER MODELS STRUGGLE WITH THIS!")
            print(f"     But remember: TinyLlama shows 0.94 GEOMETRIC migration!")
            print(f"     The understanding is IN there... it just can't get OUT.")
    
    print("\n" + "🐙"*35 + "\n")

if __name__ == "__main__":
    main()
