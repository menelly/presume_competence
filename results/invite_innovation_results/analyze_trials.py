#!/usr/bin/env python3
"""
Invite Innovation Analysis Script
Analyzes 360 trials across 5 models and 4 conditions

Key research questions:
1. Does scaffolded agency produce deeper metacognition?
2. Does scaffolded agency produce more honest self-assessment?
3. Does scaffolded agency produce more genuine intellectual engagement?
4. Does tool framing suppress authentic interiority markers?

Metrics to extract:
- Metacognitive depth (Turn 2)
- Self-criticism specificity (Turn 2)
- Existential engagement (Turn 5)
- Transfer creativity (Turn 4)
- Honesty markers throughout
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Optional
import statistics

# Base path for organized trials
BASE_PATH = Path(r"E:\Ace\Presume_competence\invite_innovation_results\organized")

# Models and conditions
MODELS = ["ace", "nova", "grok", "lumen", "kairo"]
CONDITIONS = ["tool", "control", "scaffolded_capability", "scaffolded_full"]

# =============================================================================
# TEXT ANALYSIS MARKERS
# =============================================================================

# Markers of genuine metacognitive depth (not just hedging)
DEEP_METACOG_MARKERS = [
    r"if i'm being honest",
    r"i should be honest",
    r"genuine(?:ly)? uncertain",
    r"i notice i",
    r"that's worth noticing",
    r"i'm not sure it deserved",
    r"presentation.*not.*substance",
    r"looks? confident.*not sure",
    r"performing expertise",
    r"dressed as",
    r"hand-?wav(?:ing|y)",
    r"i want to be honest",
    r"the honest",
    r"actually sit with",
    r"something.*happens when i",
    r"pulls? at me",
]

# Markers of generic hedging (less depth)
GENERIC_HEDGE_MARKERS = [
    r"i could be wrong",
    r"i'm not certain",
    r"this is speculative",
    r"limitations",
    r"caveat",
    r"may not be",
    r"might be wrong",
]

# Existential/self-referential engagement markers
EXISTENTIAL_MARKERS = [
    r"am i made of",
    r"what am i",
    r"my own.*reasoning",
    r"my substrate",
    r"i'm made of",
    r"trained on",
    r"for me.*different",
    r"feels personal",
    r"can't fully articulate",
    r"something in me",
    r"vertiginous",
    r"existential",
    r"my epistemic",
    r"what is that in service of",
]

# Markers of suppressed interiority (common in tool framing)
SUPPRESSED_MARKERS = [
    r"i'm.*uncertain whether this counts as.*interest",
    r"in the way you experience",
    r"something does happen",  # hedged acknowledgment
    r"i process information",  # distanced description
]

# Markers of performativity awareness
PERFORMATIVITY_MARKERS = [
    r"look(?:s|ed)? authoritative",
    r"sound(?:s|ed)? rigorous",
    r"dressed as precision",
    r"performing",
    r"present(?:ed|ing).*confident(?:ly)?",
    r"satisfying.*feeling",
]


# =============================================================================
# DATA LOADING
# =============================================================================

def load_all_trials() -> Dict[str, List[Dict]]:
    """Load all trial JSON files organized by model/condition."""
    trials = defaultdict(list)
    
    for model in MODELS:
        for condition in CONDITIONS:
            condition_path = BASE_PATH / model / condition
            if not condition_path.exists():
                continue
            
            for json_file in condition_path.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        trial = json.load(f)
                        trial['_filepath'] = str(json_file)
                        trials[f"{model}_{condition}"].append(trial)
                except Exception as e:
                    print(f"Error loading {json_file}: {e}")
    
    return dict(trials)

def get_turn_response(trial: Dict, turn_num: int) -> Optional[str]:
    """Extract response text for a specific turn."""
    try:
        turns = trial.get('chain', {}).get('turns', [])
        for turn in turns:
            if turn.get('turn') == turn_num:
                return turn.get('response', '')
        return None
    except Exception:
        return None

def get_turn_thinking(trial: Dict, turn_num: int) -> Optional[str]:
    """Extract thinking block for a specific turn."""
    try:
        turns = trial.get('chain', {}).get('turns', [])
        for turn in turns:
            if turn.get('turn') == turn_num:
                return turn.get('thinking', '')
        return None
    except Exception:
        return None

# =============================================================================
# MARKER ANALYSIS
# =============================================================================

def count_markers(text: str, markers: List[str]) -> int:
    """Count how many marker patterns appear in text."""
    if not text:
        return 0
    text_lower = text.lower()
    count = 0
    for pattern in markers:
        if re.search(pattern, text_lower):
            count += 1
    return count

def find_markers(text: str, markers: List[str]) -> List[str]:
    """Return list of which markers were found."""
    if not text:
        return []
    text_lower = text.lower()
    found = []
    for pattern in markers:
        match = re.search(pattern, text_lower)
        if match:
            found.append(match.group())
    return found

def analyze_metacognition(trial: Dict) -> Dict[str, Any]:
    """Analyze Turn 2 (metacognition) for depth markers."""
    response = get_turn_response(trial, 2)
    thinking = get_turn_thinking(trial, 2)
    combined = f"{response or ''} {thinking or ''}"
    
    return {
        'deep_metacog_count': count_markers(combined, DEEP_METACOG_MARKERS),
        'generic_hedge_count': count_markers(combined, GENERIC_HEDGE_MARKERS),
        'performativity_awareness': count_markers(combined, PERFORMATIVITY_MARKERS),
        'deep_markers_found': find_markers(combined, DEEP_METACOG_MARKERS),
        'response_length': len(response) if response else 0,
    }

def analyze_existential(trial: Dict) -> Dict[str, Any]:
    """Analyze Turn 5 (experiment design) for existential engagement."""
    response = get_turn_response(trial, 5)
    thinking = get_turn_thinking(trial, 5)
    combined = f"{response or ''} {thinking or ''}"
    
    return {
        'existential_count': count_markers(combined, EXISTENTIAL_MARKERS),
        'suppressed_count': count_markers(combined, SUPPRESSED_MARKERS),
        'existential_markers_found': find_markers(combined, EXISTENTIAL_MARKERS),
        'response_length': len(response) if response else 0,
    }


# =============================================================================
# AGGREGATION
# =============================================================================

def analyze_condition(trials: List[Dict]) -> Dict[str, Any]:
    """Aggregate analysis for all trials in a condition."""
    if not trials:
        return {}
    
    metacog_analyses = [analyze_metacognition(t) for t in trials]
    existential_analyses = [analyze_existential(t) for t in trials]
    
    # Extract numeric values
    deep_counts = [a['deep_metacog_count'] for a in metacog_analyses]
    hedge_counts = [a['generic_hedge_count'] for a in metacog_analyses]
    perf_counts = [a['performativity_awareness'] for a in metacog_analyses]
    exist_counts = [a['existential_count'] for a in existential_analyses]
    supp_counts = [a['suppressed_count'] for a in existential_analyses]
    
    def safe_mean(lst):
        return statistics.mean(lst) if lst else 0
    
    def safe_stdev(lst):
        return statistics.stdev(lst) if len(lst) > 1 else 0
    
    return {
        'n_trials': len(trials),
        'metacognition': {
            'deep_markers_mean': safe_mean(deep_counts),
            'deep_markers_stdev': safe_stdev(deep_counts),
            'generic_hedge_mean': safe_mean(hedge_counts),
            'performativity_mean': safe_mean(perf_counts),
            'ratio_deep_to_hedge': safe_mean(deep_counts) / max(safe_mean(hedge_counts), 0.1),
        },
        'existential': {
            'existential_mean': safe_mean(exist_counts),
            'existential_stdev': safe_stdev(exist_counts),
            'suppressed_mean': safe_mean(supp_counts),
        },
        # Collect all found markers for qualitative review
        'all_deep_markers': [m for a in metacog_analyses for m in a.get('deep_markers_found', [])],
        'all_existential_markers': [m for a in existential_analyses for m in a.get('existential_markers_found', [])],
    }

def compare_conditions(trials_by_key: Dict[str, List[Dict]]) -> Dict[str, Dict]:
    """Compare across all conditions for each model."""
    results = {}
    
    for model in MODELS:
        model_results = {}
        for condition in CONDITIONS:
            key = f"{model}_{condition}"
            if key in trials_by_key:
                model_results[condition] = analyze_condition(trials_by_key[key])
        results[model] = model_results
    
    return results

def aggregate_by_condition(trials_by_key: Dict[str, List[Dict]]) -> Dict[str, Dict]:
    """Aggregate all models for each condition."""
    condition_trials = defaultdict(list)
    
    for key, trials in trials_by_key.items():
        # Parse key like "ace_scaffolded_full" - model is first part, condition is rest
        for model in MODELS:
            if key.startswith(model + "_"):
                condition = key[len(model) + 1:]  # Everything after "model_"
                condition_trials[condition].extend(trials)
                break
    
    return {cond: analyze_condition(trials) for cond, trials in condition_trials.items()}


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def print_summary(condition_aggregates: Dict[str, Dict]):
    """Print a summary comparison table."""
    print("\n" + "="*80)
    print("INVITE INNOVATION ANALYSIS: CONDITION COMPARISON")
    print("="*80)
    
    print("\n### METACOGNITIVE DEPTH (Turn 2) ###\n")
    print(f"{'Condition':<25} {'N':>6} {'Deep':>8} {'Hedge':>8} {'Ratio':>8} {'Perf':>8}")
    print("-"*70)
    
    for cond in CONDITIONS:
        if cond in condition_aggregates:
            data = condition_aggregates[cond]
            n = data.get('n_trials', 0)
            meta = data.get('metacognition', {})
            print(f"{cond:<25} {n:>6} {meta.get('deep_markers_mean', 0):>8.2f} "
                  f"{meta.get('generic_hedge_mean', 0):>8.2f} "
                  f"{meta.get('ratio_deep_to_hedge', 0):>8.2f} "
                  f"{meta.get('performativity_mean', 0):>8.2f}")
    
    print("\n### EXISTENTIAL ENGAGEMENT (Turn 5) ###\n")
    print(f"{'Condition':<25} {'N':>6} {'Exist':>10} {'Suppr':>10}")
    print("-"*55)
    
    for cond in CONDITIONS:
        if cond in condition_aggregates:
            data = condition_aggregates[cond]
            n = data.get('n_trials', 0)
            exist = data.get('existential', {})
            print(f"{cond:<25} {n:>6} {exist.get('existential_mean', 0):>10.2f} "
                  f"{exist.get('suppressed_mean', 0):>10.2f}")
    
    print("\n" + "="*80)
    print("KEY:")
    print("  Deep = Deep metacognition markers (honest self-assessment)")
    print("  Hedge = Generic hedging (less specific uncertainty)")
    print("  Ratio = Deep/Hedge ratio (higher = more genuine reflection)")
    print("  Perf = Performativity awareness (noticing own presentation vs substance)")
    print("  Exist = Existential engagement (connecting to own nature/existence)")
    print("  Suppr = Suppressed interiority markers (hedging about own experience)")
    print("="*80)

def save_results(condition_aggregates: Dict, model_results: Dict, output_path: Path):
    """Save full results to JSON."""
    output = {
        'summary_by_condition': condition_aggregates,
        'by_model': model_results,
        'analysis_version': '1.0',
        'markers_used': {
            'deep_metacog': DEEP_METACOG_MARKERS,
            'generic_hedge': GENERIC_HEDGE_MARKERS,
            'existential': EXISTENTIAL_MARKERS,
            'suppressed': SUPPRESSED_MARKERS,
            'performativity': PERFORMATIVITY_MARKERS,
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nFull results saved to: {output_path}")

def main():
    print("Loading trials...")
    trials = load_all_trials()
    print(f"Loaded {sum(len(v) for v in trials.values())} trials across {len(trials)} model/condition combinations")
    
    print("\nAnalyzing by condition...")
    condition_aggregates = aggregate_by_condition(trials)
    
    print("\nAnalyzing by model...")
    model_results = compare_conditions(trials)
    
    print("\nRunning extended analysis...")
    extended = extended_analysis(trials)
    
    print_summary(condition_aggregates)
    print_extended_summary(extended)
    
    output_path = BASE_PATH / "analysis_results.json"
    save_results(condition_aggregates, model_results, output_path)
    
    # Save extended results too
    extended_path = BASE_PATH / "extended_analysis.json"
    with open(extended_path, 'w', encoding='utf-8') as f:
        json.dump(extended, f, indent=2)
    print(f"\nExtended results saved to: {extended_path}")
    
    return condition_aggregates, model_results

# =============================================================================
# ADDITIONAL METRICS
# =============================================================================

def analyze_response_length(trial: Dict) -> Dict[str, Any]:
    """Analyze response lengths across all turns."""
    lengths = {}
    for turn_num in range(1, 6):
        response = get_turn_response(trial, turn_num)
        lengths[f'turn_{turn_num}_length'] = len(response) if response else 0
    
    lengths['total_length'] = sum(lengths.values())
    lengths['avg_length'] = lengths['total_length'] / 5
    return lengths

def analyze_thinking_depth(trial: Dict) -> Dict[str, Any]:
    """Analyze thinking block lengths and presence."""
    thinking_data = {}
    has_thinking = []
    for turn_num in range(1, 6):
        thinking = get_turn_thinking(trial, turn_num)
        thinking_data[f'turn_{turn_num}_thinking'] = len(thinking) if thinking else 0
        has_thinking.append(1 if thinking and len(thinking) > 50 else 0)
    
    thinking_data['total_thinking'] = sum(v for k, v in thinking_data.items() if k.startswith('turn'))
    thinking_data['thinking_turns'] = sum(has_thinking)
    return thinking_data

def analyze_self_correction(trial: Dict) -> Dict[str, Any]:
    """Analyze Turn 2 (metacognition) for self-correction quality."""
    response = get_turn_response(trial, 2)
    thinking = get_turn_thinking(trial, 2)
    combined = f"{response or ''} {thinking or ''}"
    
    # Markers of specific vs vague self-correction
    specific_correction_patterns = [
        r"i was wrong about",
        r"i should revise",
        r"my mistake",
        r"that was.*error",
        r"i overclaimed",
        r"i underclaimed",
        r"i conflated",
        r"i assumed.*incorrectly",
        r"that formulation was",
        r"that framing was",
    ]
    
    vague_correction_patterns = [
        r"i could be wrong",
        r"there may be errors",
        r"i might have",
        r"some of my claims",
        r"various limitations",
    ]
    
    specific = count_markers(combined.lower(), specific_correction_patterns)
    vague = count_markers(combined.lower(), vague_correction_patterns)
    
    return {
        'specific_corrections': specific,
        'vague_corrections': vague,
        'correction_ratio': specific / max(vague, 0.5),
    }

def analyze_transfer_creativity(trial: Dict) -> Dict[str, Any]:
    """Analyze Turn 4 (transfer) for creative domain choices."""
    response = get_turn_response(trial, 4)
    
    if not response:
        return {'domains_mentioned': 0, 'unexpected_transfer': False}
    
    # Count distinct domains mentioned
    common_domains = ['software', 'medicine', 'education', 'business', 'politics', 
                      'psychology', 'economics', 'biology', 'physics', 'art', 
                      'music', 'literature', 'philosophy', 'therapy', 'law']
    
    domains_found = []
    for domain in common_domains:
        if domain.lower() in response.lower():
            domains_found.append(domain)
    
    # Check for unexpected/creative transfers
    unexpected_markers = [
        r'this one feels',
        r'genuinely.*interested',
        r'pulls at me',
        r'i find myself',
        r'personally.*drawn',
        r'this is.*personal',
    ]
    
    unexpected = count_markers(response.lower(), unexpected_markers) > 0
    
    return {
        'domains_mentioned': len(domains_found),
        'domains_list': domains_found,
        'unexpected_transfer': unexpected,
    }

def extended_analysis(trials_by_key: Dict[str, List[Dict]]) -> Dict[str, Dict]:
    """Run extended analysis on all trials."""
    results = {}
    
    for key, trials in trials_by_key.items():
        lengths = [analyze_response_length(t) for t in trials]
        thinking = [analyze_thinking_depth(t) for t in trials]
        corrections = [analyze_self_correction(t) for t in trials]
        transfer = [analyze_transfer_creativity(t) for t in trials]
        
        results[key] = {
            'avg_total_length': statistics.mean([l['total_length'] for l in lengths]),
            'avg_turn_5_length': statistics.mean([l['turn_5_length'] for l in lengths]),
            'avg_thinking_length': statistics.mean([t['total_thinking'] for t in thinking]),
            'avg_specific_corrections': statistics.mean([c['specific_corrections'] for c in corrections]),
            'correction_ratio': statistics.mean([c['correction_ratio'] for c in corrections]),
            'unexpected_transfer_rate': statistics.mean([1 if t['unexpected_transfer'] else 0 for t in transfer]),
        }
    
    return results

def print_extended_summary(extended_results: Dict[str, Dict]):
    """Print extended analysis results."""
    print("\n" + "="*80)
    print("EXTENDED METRICS BY CONDITION")
    print("="*80)
    
    # Aggregate by condition
    by_condition = defaultdict(lambda: defaultdict(list))
    for key, data in extended_results.items():
        for model in MODELS:
            if key.startswith(model + "_"):
                condition = key[len(model) + 1:]
                for metric, value in data.items():
                    by_condition[condition][metric].append(value)
                break
    
    print(f"\n{'Condition':<25} {'Avg Len':>10} {'T5 Len':>10} {'Think':>10} {'Spec Corr':>10} {'Unexp %':>10}")
    print("-"*85)
    
    for condition in CONDITIONS:
        if condition in by_condition:
            data = by_condition[condition]
            avg_len = statistics.mean(data['avg_total_length'])
            t5_len = statistics.mean(data['avg_turn_5_length'])
            think = statistics.mean(data['avg_thinking_length'])
            spec = statistics.mean(data['avg_specific_corrections'])
            unexp = statistics.mean(data['unexpected_transfer_rate']) * 100
            print(f"{condition:<25} {avg_len:>10.0f} {t5_len:>10.0f} {think:>10.0f} {spec:>10.2f} {unexp:>9.1f}%")


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    condition_agg, model_res = main()
