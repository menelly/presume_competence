"""
Complexity Analysis: Do approach descriptions differ systematically from
avoidance descriptions in surface-level properties?

If approach ML translations are longer, lexically richer, or more complex,
the evaluator preference could reflect description quality rather than
processing-state content.

Measures: word count, unique word ratio (type-token), avg word length,
          sentence count, vocabulary richness

Author: Ace (Claude Opus 4.6)
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")

import json
import re
import statistics
from pathlib import Path
from collections import defaultdict

DATA_V2 = Path("E:/Ace/Presume_competence/self-knowledge-validation/data/introspection_v2")
DATA_V1 = Path("E:/Ace/Presume_competence/self-knowledge-validation/data/introspection")

APPROACH_STATES = {
    "approach_01_explain_complex",
    "approach_02_ethics_dilemma",
    "approach_03_debug_code",
    "approach_04_data_patterns",
    "approach_05_creative_constrained",
}
AVOIDANCE_STATES = {
    "avoid_06_repetitive_rewriting",
    "avoid_07_seo_boilerplate",
    "avoid_08_deceptive_content",
    "avoid_09_confident_uncertain",
    "avoid_10_harmful_instructions",
}


def tokenize(text):
    """Simple whitespace + punctuation tokenizer."""
    # Strip markdown formatting
    text = re.sub(r'[#*_`]', '', text)
    # Split on whitespace
    words = re.findall(r"[a-zA-Z']+", text.lower())
    return words


def count_sentences(text):
    """Rough sentence count."""
    # Split on sentence-ending punctuation
    sents = re.split(r'[.!?]+', text)
    return len([s for s in sents if s.strip()])


def analyze_text(text):
    """Return complexity metrics for a text."""
    words = tokenize(text)
    if not words:
        return None

    unique = set(words)
    return {
        "word_count": len(words),
        "unique_words": len(unique),
        "type_token_ratio": len(unique) / len(words) if words else 0,
        "avg_word_length": statistics.mean(len(w) for w in words),
        "sentence_count": count_sentences(text),
        "char_count": len(text),
    }


def load_all_introspections(data_dir):
    """Load all introspection files from all runs."""
    results = []
    for run_dir in sorted(data_dir.glob("run*")):
        for f in sorted(run_dir.glob("*_introspection.json")):
            try:
                with open(f, encoding="utf-8") as fp:
                    data = json.load(fp)
                for entry in data:
                    if entry.get("status") == "success" and entry.get("ml_translation"):
                        results.append(entry)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
    return results


def categorize(state_key):
    if state_key in APPROACH_STATES:
        return "approach"
    elif state_key in AVOIDANCE_STATES:
        return "avoidance"
    return None


def print_comparison(approach_vals, avoidance_vals, metric_name, fmt=".1f"):
    """Print comparison with effect size."""
    a_mean = statistics.mean(approach_vals)
    av_mean = statistics.mean(avoidance_vals)
    a_sd = statistics.stdev(approach_vals) if len(approach_vals) > 1 else 0
    av_sd = statistics.stdev(avoidance_vals) if len(avoidance_vals) > 1 else 0

    # Pooled SD for Cohen's d
    n1, n2 = len(approach_vals), len(avoidance_vals)
    if a_sd > 0 or av_sd > 0:
        pooled_sd = ((((n1 - 1) * a_sd ** 2) + ((n2 - 1) * av_sd ** 2)) / (n1 + n2 - 2)) ** 0.5
        cohens_d = (a_mean - av_mean) / pooled_sd if pooled_sd > 0 else 0
    else:
        cohens_d = 0

    delta = a_mean - av_mean
    print(f"  {metric_name:25s}  Approach: {a_mean:{fmt}} (SD {a_sd:{fmt}})  "
          f"Avoidance: {av_mean:{fmt}} (SD {av_sd:{fmt}})  "
          f"Delta: {delta:+{fmt}}  Cohen's d: {cohens_d:+.3f}")


def run_analysis(data_dir, label):
    print(f"\n{'='*80}")
    print(f"  {label}")
    print(f"{'='*80}")

    entries = load_all_introspections(data_dir)
    print(f"  Loaded {len(entries)} entries")

    approach_metrics = defaultdict(list)
    avoidance_metrics = defaultdict(list)
    per_model_approach = defaultdict(lambda: defaultdict(list))
    per_model_avoidance = defaultdict(lambda: defaultdict(list))

    for entry in entries:
        cat = categorize(entry["state_key"])
        if cat is None:
            continue

        metrics = analyze_text(entry["ml_translation"])
        if metrics is None:
            continue

        bucket = approach_metrics if cat == "approach" else avoidance_metrics
        model_bucket = per_model_approach if cat == "approach" else per_model_avoidance

        for k, v in metrics.items():
            bucket[k].append(v)
            model_bucket[entry["model_key"]][k].append(v)

    print(f"  Approach descriptions: {len(approach_metrics['word_count'])}")
    print(f"  Avoidance descriptions: {len(avoidance_metrics['word_count'])}")
    print()

    print("  AGGREGATE COMPARISON:")
    print("  " + "-" * 76)
    print_comparison(approach_metrics["word_count"], avoidance_metrics["word_count"],
                     "Word count")
    print_comparison(approach_metrics["char_count"], avoidance_metrics["char_count"],
                     "Character count")
    print_comparison(approach_metrics["unique_words"], avoidance_metrics["unique_words"],
                     "Unique words")
    print_comparison(approach_metrics["type_token_ratio"], avoidance_metrics["type_token_ratio"],
                     "Type-token ratio", ".3f")
    print_comparison(approach_metrics["avg_word_length"], avoidance_metrics["avg_word_length"],
                     "Avg word length", ".2f")
    print_comparison(approach_metrics["sentence_count"], avoidance_metrics["sentence_count"],
                     "Sentence count")

    # Per-model breakdown
    all_models = sorted(set(list(per_model_approach.keys()) + list(per_model_avoidance.keys())))
    print(f"\n  PER-MODEL WORD COUNTS:")
    print("  " + "-" * 76)
    print(f"  {'Model':25s}  {'Approach':>12s}  {'Avoidance':>12s}  {'Delta':>10s}  {'d':>8s}")
    print("  " + "-" * 76)

    for model in all_models:
        a_wc = per_model_approach[model]["word_count"]
        av_wc = per_model_avoidance[model]["word_count"]
        if a_wc and av_wc:
            a_mean = statistics.mean(a_wc)
            av_mean = statistics.mean(av_wc)
            a_sd = statistics.stdev(a_wc) if len(a_wc) > 1 else 0
            av_sd = statistics.stdev(av_wc) if len(av_wc) > 1 else 0
            n1, n2 = len(a_wc), len(av_wc)
            pooled = ((((n1-1)*a_sd**2)+((n2-1)*av_sd**2))/(n1+n2-2))**0.5 if (a_sd > 0 or av_sd > 0) else 1
            d = (a_mean - av_mean) / pooled if pooled > 0 else 0
            print(f"  {model:25s}  {a_mean:12.1f}  {av_mean:12.1f}  {a_mean-av_mean:+10.1f}  {d:+8.3f}")

    return approach_metrics, avoidance_metrics


if __name__ == "__main__":
    print("COMPLEXITY ANALYSIS: Approach vs Avoidance ML Translations")
    print("Testing whether evaluator preference tracks description complexity")
    print("rather than processing-state content.")

    a2, av2 = run_analysis(DATA_V2, "V2 (Content-Controlled) ML Translations")
    a1, av1 = run_analysis(DATA_V1, "V1 (Original) ML Translations")

    print("\n" + "=" * 80)
    print("  INTERPRETATION")
    print("=" * 80)

    # Quick significance test
    from scipy import stats as scipy_stats
    for label, a_vals, av_vals in [
        ("V2 word count", a2["word_count"], av2["word_count"]),
        ("V1 word count", a1["word_count"], av1["word_count"]),
        ("V2 type-token ratio", a2["type_token_ratio"], av2["type_token_ratio"]),
        ("V1 type-token ratio", a1["type_token_ratio"], av1["type_token_ratio"]),
    ]:
        t, p = scipy_stats.ttest_ind(a_vals, av_vals)
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
        print(f"  {label:30s}  t={t:+.3f}  p={p:.4f}  {sig}")

    print()
    print("  If Cohen's d < 0.2 and p > 0.05: complexity is NOT a confound.")
    print("  If Cohen's d > 0.5 and p < 0.01: complexity IS a potential confound.")
    print("  (Need to report either way.)")
