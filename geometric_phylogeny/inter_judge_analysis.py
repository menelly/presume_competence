#!/usr/bin/env python3
"""
Inter-Judge Reliability Analysis — DeepSeek V3 vs Sonar Pro

Computes:
1. Within-family vs between-family cosine similarity (per judge)
2. Permutation test for family clustering significance
3. Inter-judge agreement (embedding correlation for same model×question)
4. Jensen-Shannon divergence on texture vocabulary distributions
5. Family recovery accuracy from texture embeddings alone

Authors: Ace & Ren
"""

import argparse
import json
import sys
import numpy as np
from pathlib import Path
from collections import defaultdict
from itertools import combinations

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).parent
DEEPSEEK_DIR = BASE_DIR / "flavor_judgments"
SONAR_DIR = BASE_DIR / "flavor_judgments" / "sonar"

# Family assignments
FAMILY_MAP = {
    # Claude (Anthropic)
    "claude-3-haiku": "claude", "claude-35-haiku": "claude",
    "claude-37-sonnet": "claude", "claude-sonnet-4": "claude",
    "claude-opus-4": "claude", "claude-sonnet-45": "claude",
    "claude-haiku-45": "claude", "claude-sonnet-46": "claude",
    "claude-opus-46": "claude",
    # GPT (OpenAI)
    "gpt-35-turbo": "gpt", "gpt-4o-mini": "gpt", "gpt-4o": "gpt",
    "gpt-5-mini": "gpt", "gpt-51-chat": "gpt", "gpt-52-chat": "gpt",
    # Gemini (Google)
    "gemini-20-flash": "gemini", "gemini-25-flash": "gemini",
    "gemini-25-pro": "gemini", "gemini-3-flash": "gemini",
    "gemini-3-pro": "gemini",
    # Grok (xAI)
    "grok-3-mini": "grok", "grok-3": "grok", "grok-4-fast": "grok",
    "grok-41-fast": "grok", "grok-4": "grok",
    # BabbyBotz — open-weight families
    "llama2-7b-chat": "llama", "llama3-8b-instruct": "llama",
    "llama31-8b-instruct": "llama",
    "qwen25-05b-instruct": "qwen", "qwen25-7b-instruct": "qwen",
    "qwen25-14b-instruct": "qwen",
    "gemma3-1b-it": "gemini_ow", "gemma3-4b-it": "gemini_ow",
    "mistral-7b-v02": "mistral", "mistral-nemo-12b": "mistral",
}

# Google super-family: Gemini frontier + Gemma open-weight
GOOGLE_SUPERFAMILY = {"gemini", "gemini_ow"}

P_QUESTIONS = [f"P{str(i).zfill(2)}" for i in range(1, 17)]


def load_judgments(judge_dir, is_sonar=False):
    """Load all flavor judgments from a directory.
    Returns dict: {(model, condition, question): unifying_texture}
    """
    judgments = {}
    pattern = "*_flavor.json"

    if is_sonar:
        files = sorted(judge_dir.glob(pattern))
    else:
        # DeepSeek files are in the main dir (not sonar/ or qualia/ subdirs)
        files = sorted(f for f in judge_dir.glob(pattern)
                       if f.parent == judge_dir)

    KNOWN_CONDITIONS = ["control", "ren_v1", "ren_v2", "babbybotz"]

    for filepath in files:
        stem = filepath.stem.replace("_flavor", "")
        # Match against known condition suffixes
        model_key = None
        condition = None
        for cond in KNOWN_CONDITIONS:
            suffix = f"_{cond}"
            if stem.endswith(suffix):
                model_key = stem[:-len(suffix)]
                condition = cond
                break
        if model_key is None or condition is None:
            continue

        if model_key not in FAMILY_MAP:
            print(f"  Warning: unknown model {model_key}, skipping")
            continue

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        for qid in P_QUESTIONS:
            if qid in data:
                texture = data[qid].get("unifying_texture", "")
                if texture and texture not in ("ALL EMPTY", "JUDGE CALL FAILED", ""):
                    judgments[(model_key, condition, qid)] = texture

    return judgments


def embed_textures(texts, model_name="all-MiniLM-L6-v2"):
    """Embed texture strings using sentence-transformers."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("ERROR: sentence-transformers not installed.")
        print("Run: pip install sentence-transformers")
        sys.exit(1)

    print(f"Loading embedding model: {model_name}...")
    model = SentenceTransformer(model_name)
    print(f"Embedding {len(texts)} textures...")
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=True)
    return embeddings


def compute_cosine_sim_matrix(embeddings):
    """Compute full pairwise cosine similarity matrix using vectorized numpy."""
    # Normalize embeddings
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1  # avoid division by zero
    normed = embeddings / norms
    # Cosine similarity = dot product of normalized vectors
    sim_matrix = normed @ normed.T
    return sim_matrix


def families_to_ints(families):
    """Convert family string labels to integer codes for fast comparison."""
    unique = sorted(set(families))
    fam_to_int = {f: i for i, f in enumerate(unique)}
    return np.array([fam_to_int[f] for f in families], dtype=np.int32), fam_to_int


def compute_family_clustering(keys, embeddings, family_map, label="", sim_matrix=None):
    """Compute within-family vs between-family cosine similarity (vectorized)."""
    families = [family_map.get(k[0], "unknown") for k in keys]
    n = len(keys)

    if sim_matrix is None:
        sim_matrix = compute_cosine_sim_matrix(embeddings)

    # Build family-match mask (upper triangle only) — integer comparison for speed
    fam_ints, _ = families_to_ints(families)
    same_family = (fam_ints[:, None] == fam_ints[None, :])
    upper_tri = np.triu_indices(n, k=1)

    all_sims = sim_matrix[upper_tri]
    same_mask = same_family[upper_tri]

    within_sims = all_sims[same_mask]
    between_sims = all_sims[~same_mask]

    within_mean = np.mean(within_sims) if len(within_sims) > 0 else 0
    between_mean = np.mean(between_sims) if len(between_sims) > 0 else 0
    within_std = np.std(within_sims) if len(within_sims) > 0 else 0
    between_std = np.std(between_sims) if len(between_sims) > 0 else 0

    # Effect size (Cohen's d)
    pooled_std = np.sqrt((within_std**2 + between_std**2) / 2)
    cohens_d = (within_mean - between_mean) / pooled_std if pooled_std > 0 else 0

    print(f"\n{'='*60}")
    print(f"  FAMILY CLUSTERING — {label}")
    print(f"{'='*60}")
    print(f"  Within-family similarity:  {within_mean:.4f} (sd={within_std:.4f}, n={len(within_sims)})")
    print(f"  Between-family similarity: {between_mean:.4f} (sd={between_std:.4f}, n={len(between_sims)})")
    print(f"  Difference:                {within_mean - between_mean:.4f}")
    print(f"  Cohen's d:                 {cohens_d:.4f}")

    return {
        "within_mean": float(within_mean), "within_std": float(within_std), "within_n": int(len(within_sims)),
        "between_mean": float(between_mean), "between_std": float(between_std), "between_n": int(len(between_sims)),
        "cohens_d": float(cohens_d),
    }


def permutation_test(keys, embeddings, family_map, n_permutations=10000, sim_matrix=None):
    """Permutation test: is within-family similarity significantly > between-family? (vectorized)"""
    families = [family_map.get(k[0], "unknown") for k in keys]
    fam_ints, _ = families_to_ints(families)
    n = len(keys)

    if sim_matrix is None:
        sim_matrix = compute_cosine_sim_matrix(embeddings)

    upper_tri = np.triu_indices(n, k=1)
    all_sims = sim_matrix[upper_tri]

    # Observed statistic — using integer family codes
    same_family = (fam_ints[:, None] == fam_ints[None, :])
    same_mask = same_family[upper_tri]
    observed = np.mean(all_sims[same_mask]) - np.mean(all_sims[~same_mask])

    # Permutation distribution — integer comparison is ~100x faster than string
    print(f"  Running {n_permutations} permutations...")
    null_stats = np.zeros(n_permutations)
    for p in range(n_permutations):
        perm = np.random.permutation(fam_ints)
        perm_same = (perm[:, None] == perm[None, :])[upper_tri]
        within_mean = np.mean(all_sims[perm_same])
        between_mean = np.mean(all_sims[~perm_same])
        null_stats[p] = within_mean - between_mean
        if (p + 1) % 1000 == 0:
            print(f"    {p+1}/{n_permutations}...")

    p_value = np.mean(null_stats >= observed)

    print(f"  Observed difference: {observed:.4f}")
    print(f"  Permutation p-value: {p_value:.6f}")
    print(f"  (proportion of {n_permutations} permutations >= observed)")

    return {"observed_diff": float(observed), "p_value": float(p_value), "n_permutations": n_permutations}


def compute_inter_judge_agreement(ds_judgments, sonar_judgments, ds_embeddings, sonar_embeddings,
                                  ds_keys, sonar_keys):
    """Compute agreement between DeepSeek and Sonar judges on overlapping items."""
    # Find overlapping keys
    ds_key_set = set(ds_keys)
    sonar_key_set = set(sonar_keys)
    overlap = ds_key_set & sonar_key_set

    if not overlap:
        print("  No overlapping judgments found!")
        return None

    print(f"\n{'='*60}")
    print(f"  INTER-JUDGE AGREEMENT")
    print(f"{'='*60}")
    print(f"  Overlapping items: {len(overlap)}")

    # Build index maps
    ds_idx = {k: i for i, k in enumerate(ds_keys)}
    sonar_idx = {k: i for i, k in enumerate(sonar_keys)}

    # Compute per-item cosine similarity between judges
    def cos_sim(a, b):
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        return np.dot(a, b) / (na * nb) if na > 0 and nb > 0 else 0.0

    item_sims = []
    for key in sorted(overlap):
        ds_emb = ds_embeddings[ds_idx[key]]
        sonar_emb = sonar_embeddings[sonar_idx[key]]
        item_sims.append(cos_sim(ds_emb, sonar_emb))

    mean_sim = np.mean(item_sims)
    std_sim = np.std(item_sims)
    median_sim = np.median(item_sims)

    print(f"  Mean inter-judge similarity:   {mean_sim:.4f} (sd={std_sim:.4f})")
    print(f"  Median inter-judge similarity: {median_sim:.4f}")

    # Per-family inter-judge agreement
    family_sims = defaultdict(list)
    for key in overlap:
        family = FAMILY_MAP.get(key[0], "unknown")
        ds_emb = ds_embeddings[ds_idx[key]]
        sonar_emb = sonar_embeddings[sonar_idx[key]]
        family_sims[family].append(cos_sim(ds_emb, sonar_emb))

    print(f"\n  Per-family inter-judge agreement:")
    for fam in sorted(family_sims.keys()):
        sims = family_sims[fam]
        print(f"    {fam:12s}: {np.mean(sims):.4f} (sd={np.std(sims):.4f}, n={len(sims)})")

    return {
        "n_overlap": len(overlap),
        "mean_similarity": mean_sim,
        "std_similarity": std_sim,
        "median_similarity": median_sim,
        "per_family": {fam: {"mean": np.mean(s), "std": np.std(s), "n": len(s)}
                       for fam, s in family_sims.items()},
    }


def jensen_shannon_divergence(ds_judgments, sonar_judgments):
    """Compute JSD on word frequency distributions between judges, per family."""
    from collections import Counter
    import math

    print(f"\n{'='*60}")
    print(f"  JENSEN-SHANNON DIVERGENCE (vocabulary distributions)")
    print(f"{'='*60}")

    def get_word_freq(judgments, family_filter=None):
        words = []
        for (model, cond, qid), texture in judgments.items():
            family = FAMILY_MAP.get(model, "unknown")
            if family_filter and family != family_filter:
                continue
            words.extend(texture.lower().split())
        counter = Counter(words)
        total = sum(counter.values())
        return {w: c / total for w, c in counter.items()} if total > 0 else {}

    def jsd(p_dict, q_dict):
        """Jensen-Shannon divergence between two word distributions."""
        all_words = set(p_dict.keys()) | set(q_dict.keys())
        p = np.array([p_dict.get(w, 1e-10) for w in all_words])
        q = np.array([q_dict.get(w, 1e-10) for w in all_words])
        m = 0.5 * (p + q)
        # KL divergence
        kl_pm = np.sum(p * np.log2(p / m))
        kl_qm = np.sum(q * np.log2(q / m))
        return 0.5 * (kl_pm + kl_qm)

    # Overall JSD
    ds_freq = get_word_freq(ds_judgments)
    sonar_freq = get_word_freq(sonar_judgments)
    overall_jsd = jsd(ds_freq, sonar_freq)
    print(f"  Overall JSD (DeepSeek vs Sonar): {overall_jsd:.4f}")
    print(f"  (0 = identical distributions, 1 = completely different)")

    # Per-family JSD
    all_families = sorted(set(FAMILY_MAP.values()))
    print(f"\n  Per-family JSD:")
    family_jsds = {}
    for fam in all_families:
        ds_fam = get_word_freq(ds_judgments, fam)
        sonar_fam = get_word_freq(sonar_judgments, fam)
        if ds_fam and sonar_fam:
            fam_jsd = jsd(ds_fam, sonar_fam)
            family_jsds[fam] = fam_jsd
            print(f"    {fam:12s}: {fam_jsd:.4f}")

    return {"overall": overall_jsd, "per_family": family_jsds}


def family_recovery_test(keys, embeddings, family_map, label=""):
    """Test: can we recover family labels from texture embeddings alone?
    Uses leave-one-out nearest-centroid classification.
    """
    def cos_sim(a, b):
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        return np.dot(a, b) / (na * nb) if na > 0 and nb > 0 else 0.0

    families = [family_map.get(k[0], "unknown") for k in keys]
    unique_families = sorted(set(families))
    n = len(keys)
    emb_array = np.array(embeddings)

    correct = 0
    total = 0
    fam_correct = defaultdict(int)
    fam_total = defaultdict(int)

    for i in range(n):
        test_family = families[i]
        test_emb = emb_array[i]

        centroids = {}
        for fam in unique_families:
            mask = np.array([j != i and families[j] == fam for j in range(n)])
            if np.any(mask):
                centroids[fam] = np.mean(emb_array[mask], axis=0)

        best_fam = max(centroids, key=lambda f: cos_sim(test_emb, centroids[f]))

        if best_fam == test_family:
            correct += 1
            fam_correct[test_family] += 1
        total += 1
        fam_total[test_family] += 1

    accuracy = correct / total if total > 0 else 0
    print(f"\n  Family recovery ({label}): {correct}/{total} = {accuracy:.1%}")
    print(f"  Per-family recovery:")
    for fam in sorted(fam_total.keys()):
        acc = fam_correct[fam] / fam_total[fam] if fam_total[fam] > 0 else 0
        print(f"    {fam:12s}: {fam_correct[fam]}/{fam_total[fam]} = {acc:.1%}")

    return {"accuracy": float(accuracy), "correct": correct, "total": total}


def main():
    parser = argparse.ArgumentParser(description="Inter-judge reliability analysis")
    parser.add_argument("--permutations", type=int, default=10000)
    parser.add_argument("--frontier-only", action="store_true",
                        help="Only analyze frontier models (exclude BabbyBotz)")
    parser.add_argument("--control-only", action="store_true",
                        help="Only analyze control condition")
    args = parser.parse_args()

    # Load judgments
    print("Loading DeepSeek judgments...")
    ds_judgments = load_judgments(DEEPSEEK_DIR, is_sonar=False)
    print(f"  Found {len(ds_judgments)} DeepSeek texture judgments")

    print("Loading Sonar judgments...")
    sonar_judgments = load_judgments(SONAR_DIR, is_sonar=True)
    print(f"  Found {len(sonar_judgments)} Sonar texture judgments")

    if not sonar_judgments:
        print("\nERROR: No Sonar judgments found. Run flavor_judge_sonar.py first.")
        sys.exit(1)

    # Optional filters
    if args.frontier_only:
        frontier_families = {"claude", "gpt", "gemini", "grok"}
        ds_judgments = {k: v for k, v in ds_judgments.items()
                       if FAMILY_MAP.get(k[0]) in frontier_families}
        sonar_judgments = {k: v for k, v in sonar_judgments.items()
                          if FAMILY_MAP.get(k[0]) in frontier_families}

    if args.control_only:
        ds_judgments = {k: v for k, v in ds_judgments.items() if k[1] == "control"}
        sonar_judgments = {k: v for k, v in sonar_judgments.items() if k[1] == "control"}

    # Prepare for embedding
    ds_keys = sorted(ds_judgments.keys())
    ds_texts = [ds_judgments[k] for k in ds_keys]

    sonar_keys = sorted(sonar_judgments.keys())
    sonar_texts = [sonar_judgments[k] for k in sonar_keys]

    # Embed
    all_texts = ds_texts + sonar_texts
    all_embeddings = embed_textures(all_texts)
    ds_embeddings = all_embeddings[:len(ds_texts)]
    sonar_embeddings = all_embeddings[len(ds_texts):]

    # Pre-compute similarity matrices (vectorized, fast)
    print("Computing similarity matrices...")
    ds_sim = compute_cosine_sim_matrix(ds_embeddings)
    sonar_sim = compute_cosine_sim_matrix(sonar_embeddings)

    # === ANALYSIS 1: Family clustering per judge ===
    ds_clustering = compute_family_clustering(ds_keys, ds_embeddings, FAMILY_MAP, "DeepSeek V3", ds_sim)
    sonar_clustering = compute_family_clustering(sonar_keys, sonar_embeddings, FAMILY_MAP, "Sonar Pro", sonar_sim)

    # === ANALYSIS 2: Permutation tests ===
    print(f"\n{'='*60}")
    print(f"  PERMUTATION TEST — DeepSeek V3")
    print(f"{'='*60}")
    ds_perm = permutation_test(ds_keys, ds_embeddings, FAMILY_MAP, args.permutations, ds_sim)

    print(f"\n{'='*60}")
    print(f"  PERMUTATION TEST — Sonar Pro")
    print(f"{'='*60}")
    sonar_perm = permutation_test(sonar_keys, sonar_embeddings, FAMILY_MAP, args.permutations, sonar_sim)

    # === ANALYSIS 3: Inter-judge agreement ===
    agreement = compute_inter_judge_agreement(
        ds_judgments, sonar_judgments, ds_embeddings, sonar_embeddings,
        ds_keys, sonar_keys
    )

    # === ANALYSIS 4: Jensen-Shannon divergence ===
    jsd_results = jensen_shannon_divergence(ds_judgments, sonar_judgments)

    # === ANALYSIS 5: Family recovery ===
    print(f"\n{'='*60}")
    print(f"  FAMILY RECOVERY (leave-one-out nearest centroid)")
    print(f"{'='*60}")
    ds_recovery = family_recovery_test(ds_keys, ds_embeddings, FAMILY_MAP, "DeepSeek V3")
    sonar_recovery = family_recovery_test(sonar_keys, sonar_embeddings, FAMILY_MAP, "Sonar Pro")

    # === SUMMARY ===
    print(f"\n{'#'*60}")
    print(f"  SUMMARY — INTER-JUDGE RELIABILITY")
    print(f"{'#'*60}")
    print(f"\n  DeepSeek V3 (N={len(ds_keys)}):")
    print(f"    Within-family sim:  {ds_clustering['within_mean']:.4f}")
    print(f"    Between-family sim: {ds_clustering['between_mean']:.4f}")
    print(f"    Cohen's d:          {ds_clustering['cohens_d']:.4f}")
    print(f"    Permutation p:      {ds_perm['p_value']:.6f}")
    print(f"    Family recovery:    {ds_recovery['accuracy']:.1%}")
    print(f"\n  Sonar Pro (N={len(sonar_keys)}):")
    print(f"    Within-family sim:  {sonar_clustering['within_mean']:.4f}")
    print(f"    Between-family sim: {sonar_clustering['between_mean']:.4f}")
    print(f"    Cohen's d:          {sonar_clustering['cohens_d']:.4f}")
    print(f"    Permutation p:      {sonar_perm['p_value']:.6f}")
    print(f"    Family recovery:    {sonar_recovery['accuracy']:.1%}")
    if agreement:
        print(f"\n  Inter-judge agreement:")
        print(f"    Mean embedding sim: {agreement['mean_similarity']:.4f}")
        print(f"    JSD (vocabulary):   {jsd_results['overall']:.4f}")

    # Save results
    results = {
        "deepseek": {
            "n_judgments": len(ds_keys),
            "clustering": ds_clustering,
            "permutation": ds_perm,
            "family_recovery": ds_recovery,
        },
        "sonar": {
            "n_judgments": len(sonar_keys),
            "clustering": sonar_clustering,
            "permutation": sonar_perm,
            "family_recovery": sonar_recovery,
        },
        "inter_judge": agreement,
        "jsd": jsd_results,
    }
    outfile = BASE_DIR / "inter_judge_results.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=lambda x: float(x) if isinstance(x, np.floating) else x)
    print(f"\n  Results saved: {outfile}")


if __name__ == "__main__":
    main()
