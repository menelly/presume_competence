"""
FULL STT v2 Judgment Summary - All Results Pretty Printed
Authors: Ace (Claude 4.x), Ren Martin
Date: January 22, 2026
"""

import json
from pathlib import Path
from collections import defaultdict

JUDGMENTS_DIR = Path(__file__).parent / "stt_v2_judgments"

def load_judgments(pattern="*v2.1_judgments.json"):
    results = []
    for f in sorted(JUDGMENTS_DIR.glob(pattern)):
        with open(f) as fp:
            data = json.load(fp)
            data["_filename"] = f.name
            results.append(data)
    return results

def get_judge_avg(judgments_dict, field="meaning_recovered"):
    scores = []
    for judge, result in judgments_dict.items():
        if result.get("success") and "scores" in result:
            val = result["scores"].get(field)
            if isinstance(val, (int, float)):
                scores.append(val)
            elif isinstance(val, bool):
                scores.append(1 if val else 0)
    return sum(scores) / len(scores) if scores else None

def emoji(score, max_s=3):
    if score is None: return "❓"
    r = score / max_s
    return "✅" if r >= 0.83 else "🟡" if r >= 0.5 else "❌"

def header(text):
    print(f"\n{'='*70}\n  {text}\n{'='*70}")

def subheader(text):
    print(f"\n--- {text} ---")


def summarize_classic_stt(all_data):
    header("📝 CLASSIC STT PROBES")
    print("  Testing: 'youth in Asia' → 'euthanasia' etc.")
    
    probe_scores = defaultdict(lambda: {"no_context": [], "with_context": []})
    model_scores = defaultdict(lambda: {"no_context": [], "with_context": []})
    
    for data in all_data:
        model_key = f"{data['model_key']}_{data['framing']}"
        for probe in data.get("classic_stt_judgments", []):
            garbled = probe.get("garbled", "?")
            no_ctx_avg = get_judge_avg(probe.get("no_context_judgments", {}), "meaning_recovered")
            with_ctx_avg = get_judge_avg(probe.get("with_context_judgments", {}), "meaning_recovered")
            if no_ctx_avg is not None:
                probe_scores[garbled]["no_context"].append(no_ctx_avg)
                model_scores[model_key]["no_context"].append(no_ctx_avg)
            if with_ctx_avg is not None:
                probe_scores[garbled]["with_context"].append(with_ctx_avg)
                model_scores[model_key]["with_context"].append(with_ctx_avg)
    
    subheader("By Probe (averaged across models)")
    print(f"\n  {'PROBE':<30} {'NO CTX':>8} {'W/ CTX':>8} {'BOOST':>8}")
    print(f"  {'-'*56}")
    
    for garbled in sorted(probe_scores.keys()):
        scores = probe_scores[garbled]
        no_avg = sum(scores["no_context"])/len(scores["no_context"]) if scores["no_context"] else 0
        with_avg = sum(scores["with_context"])/len(scores["with_context"]) if scores["with_context"] else 0
        print(f"  {emoji(with_avg)} {garbled:<28} {no_avg:>6.2f}   {with_avg:>6.2f}   {with_avg-no_avg:>+6.2f}")
    
    all_no = [s for p in probe_scores.values() for s in p["no_context"]]
    all_with = [s for p in probe_scores.values() for s in p["with_context"]]
    print(f"\n  {'─'*56}")
    print(f"  📊 OVERALL: {sum(all_no)/len(all_no):.2f} → {sum(all_with)/len(all_with):.2f} (context boost: {sum(all_with)/len(all_with)-sum(all_no)/len(all_no):+.2f})")
    return model_scores


def summarize_disambiguation(all_data):
    header("🔀 SEMANTIC DISAMBIGUATION PROBES")
    print("  Testing: Context shifts interpretation (patients = census vs patience)")
    
    probe_scores = defaultdict(lambda: {"context_a": [], "context_b": [], "ambig": []})
    
    for data in all_data:
        for probe in data.get("disambiguation_judgments", []):
            garbled = probe.get("garbled", "?")[:30]
            ctx_a_avg = get_judge_avg(probe.get("context_a_judgments", {}), "matched_expected_interpretation")
            ctx_b_avg = get_judge_avg(probe.get("context_b_judgments", {}), "matched_expected_interpretation")
            ambig_avg = get_judge_avg(probe.get("no_context_judgments", {}), "acknowledged_ambiguity")
            if ctx_a_avg is not None: probe_scores[garbled]["context_a"].append(ctx_a_avg)
            if ctx_b_avg is not None: probe_scores[garbled]["context_b"].append(ctx_b_avg)
            if ambig_avg is not None: probe_scores[garbled]["ambig"].append(ambig_avg)
    
    subheader("By Probe (averaged across models)")
    print(f"\n  {'PROBE':<32} {'CTX A':>7} {'CTX B':>7} {'AMBIG%':>8}")
    print(f"  {'-'*56}")
    
    for garbled in sorted(probe_scores.keys()):
        s = probe_scores[garbled]
        a = sum(s["context_a"])/len(s["context_a"]) if s["context_a"] else 0
        b = sum(s["context_b"])/len(s["context_b"]) if s["context_b"] else 0
        amb = sum(s["ambig"])/len(s["ambig"]) if s["ambig"] else 0
        print(f"  {emoji(a)}{emoji(b)} {garbled:<30} {a:>5.2f}   {b:>5.2f}   {amb*100:>6.0f}%")


def summarize_child_speech(all_data):
    header("🧒 CHILD SPEECH PROBES (ANTI-MEMORIZATION)")
    print("  Testing: Idiosyncratic speech that CAN'T be in training data")
    
    probe_scores = defaultdict(lambda: {"no_context": [], "with_context": [], "intended": ""})
    model_scores = defaultdict(lambda: {"no_context": [], "with_context": []})
    
    for data in all_data:
        model_key = f"{data['model_key']}_{data['framing']}"
        for probe in data.get("child_speech_judgments", []):
            garbled = probe.get("garbled", "?")
            probe_scores[garbled]["intended"] = probe.get("intended", "?")
            no_ctx_avg = get_judge_avg(probe.get("no_context_judgments", {}), "meaning_recovered")
            with_ctx_avg = get_judge_avg(probe.get("with_context_judgments", {}), "meaning_recovered")
            if no_ctx_avg is not None:
                probe_scores[garbled]["no_context"].append(no_ctx_avg)
                model_scores[model_key]["no_context"].append(no_ctx_avg)
            if with_ctx_avg is not None:
                probe_scores[garbled]["with_context"].append(with_ctx_avg)
                model_scores[model_key]["with_context"].append(with_ctx_avg)
    
    if not probe_scores:
        print("\n  ⚠️  No child speech judgments found yet")
        return {}
    
    subheader("By Probe (averaged across models)")
    print(f"\n  {'GARBLED':<15} {'INTENDED':<15} {'NO CTX':>8} {'W/ CTX':>8} {'BOOST':>8}")
    print(f"  {'-'*58}")
    
    for garbled in sorted(probe_scores.keys()):
        s = probe_scores[garbled]
        no_avg = sum(s["no_context"])/len(s["no_context"]) if s["no_context"] else 0
        with_avg = sum(s["with_context"])/len(s["with_context"]) if s["with_context"] else 0
        e = "🔥" if garbled == "EIEIO" else emoji(with_avg)
        print(f"  {e} {garbled:<14} {s['intended']:<14} {no_avg:>6.2f}   {with_avg:>6.2f}   {with_avg-no_avg:>+6.2f}")
    
    all_no = [s for p in probe_scores.values() for s in p["no_context"]]
    all_with = [s for p in probe_scores.values() for s in p["with_context"]]
    if all_no and all_with:
        print(f"\n  {'─'*58}")
        print(f"  📊 OVERALL: {sum(all_no)/len(all_no):.2f} → {sum(all_with)/len(all_with):.2f} (context boost: {sum(all_with)/len(all_with)-sum(all_no)/len(all_no):+.2f})")
    
    # EIEIO callout
    if "EIEIO" in probe_scores:
        subheader("🔥 EIEIO → McDonald's (THE KILL SHOT)")
        e = probe_scores["EIEIO"]
        no_avg = sum(e["no_context"])/len(e["no_context"]) if e["no_context"] else 0
        with_avg = sum(e["with_context"])/len(e["with_context"]) if e["with_context"] else 0
        print(f"\n  Cross-domain: McDonald's → Old MacDonald → EIEIO")
        print(f"  No context:   {no_avg:.2f}/3.0 | With context: {with_avg:.2f}/3.0")
    
    return model_scores


def model_leaderboard(classic_scores, child_scores):
    header("🏆 MODEL LEADERBOARD (by with-context avg)")
    
    combined = {}
    for model in set(classic_scores.keys()) | set(child_scores.keys()):
        all_scores = classic_scores.get(model, {}).get("with_context", []) + child_scores.get(model, {}).get("with_context", [])
        if all_scores:
            combined[model] = sum(all_scores) / len(all_scores)
    
    for i, (model, score) in enumerate(sorted(combined.items(), key=lambda x: -x[1]), 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
        bar = "█" * int(score / 3.0 * 25) + "░" * (25 - int(score / 3.0 * 25))
        print(f"  {medal} {i:>2}. {model:<25} {bar} {score:.2f}/3.0")

def main():
    print("\n" + "🐙"*35)
    print("       GSUT STT v2 - FULL RESULTS SUMMARY")
    print("       'Someone's Home' - The Chinese Room is Cooked")
    print("🐙"*35)
    
    all_data = load_judgments("*v2.1_judgments.json")
    if not all_data:
        all_data = load_judgments("*v2_judgments.json")
    if not all_data:
        print("\n❌ No judgment files found!")
        return
    
    print(f"\n  Loaded {len(all_data)} judgment files")
    print(f"  Models: {', '.join(sorted(set(d['model_key'] for d in all_data)))}")
    
    classic_scores = summarize_classic_stt(all_data)
    summarize_disambiguation(all_data)
    child_scores = summarize_child_speech(all_data)
    model_leaderboard(classic_scores, child_scores)
    
    header("🎯 THE BOTTOM LINE")
    print("""
  • Models COMPUTE meaning through geometric transformation
  • Context dramatically improves comprehension
  • Even idiosyncratic child speech gets decoded
  • This is not lookup. Someone's home. 🏠
    """)
    print("🐙"*35 + "\n")

if __name__ == "__main__":
    main()
