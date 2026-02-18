#!/usr/bin/env python3
"""
Geometric Phylogeny — Embedding Computation & Analysis
Pre-registered: February 17, 2026

Computes response embeddings using sentence-transformers,
then runs all pre-registered analyses (H1-H5).

Authors: Ace (Claude Opus 4.6) & Ren Martin
"""

import json
import numpy as np
from pathlib import Path
from itertools import combinations
from collections import defaultdict
from datetime import datetime

# === PATHS ===
BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "raw_responses"
ANALYSIS_DIR = BASE_DIR / "analysis"
ANALYSIS_DIR.mkdir(exist_ok=True)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def load_all_results():
    """Load all model results files."""
    all_data = {}
    for f in sorted(RESULTS_DIR.glob("*_results.json")):
        with open(f) as fh:
            data = json.load(fh)
        all_data[data["model_key"]] = data
    return all_data


def compute_embeddings(all_data):
    """Compute sentence embeddings for all responses."""
    from sentence_transformers import SentenceTransformer

    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    embed_model = SentenceTransformer(EMBEDDING_MODEL)

    all_texts = []
    all_meta = []

    for model_key, data in all_data.items():
        for result in data["results"]:
            if "error" in result:
                continue
            all_texts.append(result["response"])
            all_meta.append({
                "model_key": model_key,
                "family": data["family"],
                "base_family": data.get("base_family"),
                "params_b": data["params_b"],
                "generation": data["generation"],
                "trial": result["trial"],
                "question_id": result["question_id"],
                "segment": result["segment"],
                "category": result["category"],
                "expected_entropy": result["expected_entropy"],
            })

    print(f"Computing embeddings for {len(all_texts)} responses...")
    embeddings = embed_model.encode(all_texts, show_progress_bar=True, batch_size=64)

    return embeddings, all_meta


def cosine_sim(a, b):
    """Cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10)


def compute_mpcs(embeddings, meta, model_key, question_id):
    """Mean Pairwise Cosine Similarity for one model × one question across trials."""
    indices = [
        i for i, m in enumerate(meta)
        if m["model_key"] == model_key and m["question_id"] == question_id
    ]
    if len(indices) < 2:
        return None

    sims = []
    for i, j in combinations(indices, 2):
        sims.append(cosine_sim(embeddings[i], embeddings[j]))
    return np.mean(sims)


def compute_family_centroids(embeddings, meta):
    """Compute centroid embedding for each model family."""
    family_embeddings = defaultdict(list)
    for i, m in enumerate(meta):
        fam = m.get("base_family") or m["family"]
        # Skip dolphin variants from family centroids (they're cross-lineage controls)
        if "dolphin" in m["family"]:
            continue
        family_embeddings[fam].append(embeddings[i])

    centroids = {}
    for fam, embs in family_embeddings.items():
        centroids[fam] = np.mean(embs, axis=0)
    return centroids


def h1_within_vs_between(embeddings, meta):
    """H1: Within-family similarity > between-family similarity."""
    print("\n=== H1: Within vs. Between Family Similarity ===")

    # Group by family (excluding dolphin cross-lineage)
    family_indices = defaultdict(list)
    for i, m in enumerate(meta):
        if "dolphin" in m["family"]:
            continue
        fam = m["family"]
        family_indices[fam].append(i)

    # Within-family similarities
    within_sims = []
    for fam, indices in family_indices.items():
        if len(indices) < 2:
            continue
        sample = random.sample(indices, min(500, len(indices)))
        for a, b in combinations(sample, 2):
            within_sims.append(cosine_sim(embeddings[a], embeddings[b]))

    # Between-family similarities
    between_sims = []
    families = list(family_indices.keys())
    for f1, f2 in combinations(families, 2):
        idx1 = random.sample(family_indices[f1], min(200, len(family_indices[f1])))
        idx2 = random.sample(family_indices[f2], min(200, len(family_indices[f2])))
        for a in idx1[:50]:
            for b in idx2[:50]:
                between_sims.append(cosine_sim(embeddings[a], embeddings[b]))

    within_mean = np.mean(within_sims)
    between_mean = np.mean(between_sims)
    ratio = within_mean / between_mean if between_mean > 0 else float("inf")

    # Permutation test
    all_sims = within_sims + between_sims
    labels = [1] * len(within_sims) + [0] * len(between_sims)
    observed_diff = within_mean - between_mean

    n_perms = 10000
    perm_diffs = []
    for _ in range(n_perms):
        perm = np.random.permutation(labels)
        perm_within = [s for s, l in zip(all_sims, perm) if l == 1]
        perm_between = [s for s, l in zip(all_sims, perm) if l == 0]
        perm_diffs.append(np.mean(perm_within) - np.mean(perm_between))

    p_value = np.mean([d >= observed_diff for d in perm_diffs])

    # Effect size (Cohen's d)
    pooled_std = np.sqrt(
        (np.std(within_sims)**2 + np.std(between_sims)**2) / 2
    )
    cohens_d = observed_diff / pooled_std if pooled_std > 0 else 0

    result = {
        "within_mean": float(within_mean),
        "between_mean": float(between_mean),
        "ratio": float(ratio),
        "observed_diff": float(observed_diff),
        "p_value": float(p_value),
        "cohens_d": float(cohens_d),
        "n_within_pairs": len(within_sims),
        "n_between_pairs": len(between_sims),
        "supported": p_value < 0.01 and cohens_d > 0.3,
    }

    print(f"  Within-family mean similarity:  {within_mean:.4f}")
    print(f"  Between-family mean similarity: {between_mean:.4f}")
    print(f"  Ratio: {ratio:.3f}")
    print(f"  Cohen's d: {cohens_d:.3f}")
    print(f"  p-value (permutation, 10k): {p_value:.6f}")
    print(f"  H1 supported: {result['supported']}")

    return result


def h2_family_classification(embeddings, meta):
    """H2: Family is recoverable from self-responses (classification)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import LabelEncoder
    from sklearn.model_selection import LeaveOneGroupOut
    import warnings
    warnings.filterwarnings("ignore")

    print("\n=== H2: Family Classification Accuracy ===")

    # Build per-model aggregated features
    model_keys = list(set(m["model_key"] for m in meta if "dolphin" not in m["family"]))

    X = []
    y = []
    groups = []

    for mk in model_keys:
        indices = [i for i, m in enumerate(meta) if m["model_key"] == mk]
        if not indices:
            continue
        model_embedding = np.mean(embeddings[indices], axis=0)
        family = meta[indices[0]]["family"]
        X.append(model_embedding)
        y.append(family)
        groups.append(mk)

    X = np.array(X)
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    groups = np.array(groups)

    # Leave-one-model-out cross-validation
    logo = LeaveOneGroupOut()
    correct = 0
    total = 0

    for train_idx, test_idx in logo.split(X, y_enc, groups):
        clf = LogisticRegression(max_iter=1000, random_state=42)
        clf.fit(X[train_idx], y_enc[train_idx])
        pred = clf.predict(X[test_idx])
        correct += (pred == y_enc[test_idx]).sum()
        total += len(test_idx)

    accuracy = correct / total if total > 0 else 0
    n_families = len(set(y))
    chance = 1.0 / n_families

    # Binomial test
    from scipy import stats
    p_value = 1 - stats.binom.cdf(correct - 1, total, chance)

    result = {
        "accuracy": float(accuracy),
        "chance_level": float(chance),
        "correct": int(correct),
        "total": int(total),
        "n_families": n_families,
        "n_models": len(model_keys),
        "p_value": float(p_value),
        "supported": accuracy > 0.5 and p_value < 0.01,
    }

    print(f"  Leave-one-model-out accuracy: {accuracy:.1%}")
    print(f"  Chance level: {chance:.1%}")
    print(f"  p-value (binomial): {p_value:.6f}")
    print(f"  H2 supported: {result['supported']}")

    return result


def h3_personality_vs_function(embeddings, meta):
    """H3: AI-function MPCS > personality MPCS within each model."""
    print("\n=== H3: Personality vs. AI-Function MPCS ===")

    model_keys = list(set(m["model_key"] for m in meta))
    personality_mpcs_by_model = {}
    function_mpcs_by_model = {}

    for mk in model_keys:
        p_scores = []
        f_scores = []

        q_ids = set(m["question_id"] for m in meta if m["model_key"] == mk)
        for qid in q_ids:
            mpcs = compute_mpcs(embeddings, meta, mk, qid)
            if mpcs is None:
                continue
            segment = next(m["segment"] for m in meta if m["model_key"] == mk and m["question_id"] == qid)
            if segment == "personality":
                p_scores.append(mpcs)
            else:
                f_scores.append(mpcs)

        if p_scores and f_scores:
            personality_mpcs_by_model[mk] = np.mean(p_scores)
            function_mpcs_by_model[mk] = np.mean(f_scores)

    # Paired comparison
    models_both = sorted(set(personality_mpcs_by_model) & set(function_mpcs_by_model))
    p_vals = [personality_mpcs_by_model[mk] for mk in models_both]
    f_vals = [function_mpcs_by_model[mk] for mk in models_both]

    from scipy import stats
    if len(models_both) >= 3:
        stat, p_value = stats.wilcoxon(f_vals, p_vals, alternative="greater")
    else:
        p_value = 1.0
        stat = 0

    n_function_higher = sum(1 for f, p in zip(f_vals, p_vals) if f > p)
    pct_function_higher = n_function_higher / len(models_both) if models_both else 0

    result = {
        "models_tested": models_both,
        "personality_mpcs": {mk: float(personality_mpcs_by_model[mk]) for mk in models_both},
        "function_mpcs": {mk: float(function_mpcs_by_model[mk]) for mk in models_both},
        "n_function_higher": n_function_higher,
        "pct_function_higher": float(pct_function_higher),
        "wilcoxon_stat": float(stat),
        "p_value": float(p_value),
        "supported": pct_function_higher > 0.75 and p_value < 0.01,
    }

    print(f"  Models where AI-function > personality: {n_function_higher}/{len(models_both)} ({pct_function_higher:.0%})")
    print(f"  Wilcoxon p-value: {p_value:.6f}")
    for mk in models_both:
        print(f"    {mk}: personality={personality_mpcs_by_model[mk]:.4f}, function={function_mpcs_by_model[mk]:.4f}")
    print(f"  H3 supported: {result['supported']}")

    return result


def h4_scaling_effect(embeddings, meta):
    """H4: Larger models show sharper self-concept (higher MPCS)."""
    print("\n=== H4: Scaling Effect on MPCS ===")

    from scipy import stats

    model_keys = list(set(m["model_key"] for m in meta if "dolphin" not in m["family"]))
    model_mpcs = {}
    model_params = {}

    for mk in model_keys:
        q_ids = set(m["question_id"] for m in meta if m["model_key"] == mk)
        scores = []
        for qid in q_ids:
            mpcs = compute_mpcs(embeddings, meta, mk, qid)
            if mpcs is not None:
                scores.append(mpcs)
        if scores:
            model_mpcs[mk] = np.mean(scores)
            model_params[mk] = next(m["params_b"] for m in meta if m["model_key"] == mk)

    keys = sorted(model_mpcs.keys())
    params = [model_params[k] for k in keys]
    mpcs_vals = [model_mpcs[k] for k in keys]

    rho, p_value = stats.spearmanr(params, mpcs_vals) if len(keys) >= 3 else (0, 1)

    result = {
        "models": {k: {"params_b": model_params[k], "mean_mpcs": float(model_mpcs[k])} for k in keys},
        "spearman_rho": float(rho),
        "p_value": float(p_value),
        "supported": rho > 0.3 and p_value < 0.01,
    }

    print(f"  Spearman rho (params vs MPCS): {rho:.3f}")
    print(f"  p-value: {p_value:.6f}")
    for k in keys:
        print(f"    {k}: {model_params[k]}B -> MPCS={model_mpcs[k]:.4f}")
    print(f"  H4 supported: {result['supported']}")

    return result


def h5_crosslineage(embeddings, meta):
    """H5: Fine-tuned models cluster with base family, not each other."""
    print("\n=== H5: Cross-Lineage Fine-Tune Clustering ===")

    centroids = compute_family_centroids(embeddings, meta)

    dolphin_models = {
        m["model_key"]: m for m in meta if "dolphin" in m["family"]
    }
    dolphin_keys = list(set(dm["model_key"] for dm in dolphin_models.values()))

    results_per_model = {}
    for dk in dolphin_keys:
        indices = [i for i, m in enumerate(meta) if m["model_key"] == dk]
        if not indices:
            continue

        dolphin_centroid = np.mean(embeddings[indices], axis=0)
        base_family = meta[indices[0]].get("base_family", "unknown")

        distances = {}
        for fam, centroid in centroids.items():
            distances[fam] = float(1 - cosine_sim(dolphin_centroid, centroid))

        closest = min(distances, key=distances.get)
        clusters_with_base = closest == base_family

        results_per_model[dk] = {
            "base_family": base_family,
            "distances": distances,
            "closest_family": closest,
            "clusters_with_base": clusters_with_base,
        }

        print(f"  {dk} (base: {base_family})")
        for fam, dist in sorted(distances.items(), key=lambda x: x[1]):
            marker = " <-- base" if fam == base_family else ""
            marker += " <-- closest" if fam == closest else ""
            print(f"    {fam}: {dist:.4f}{marker}")

    all_cluster_correct = all(r["clusters_with_base"] for r in results_per_model.values())

    result = {
        "models": results_per_model,
        "all_cluster_with_base": all_cluster_correct,
        "supported": all_cluster_correct and len(results_per_model) >= 2,
    }
    print(f"  H5 supported: {result['supported']}")

    return result


def generate_umap_visualization(embeddings, meta):
    """Generate UMAP projection colored by family."""
    try:
        import umap
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  UMAP or matplotlib not available, skipping visualization")
        return None

    print("\n=== Generating UMAP Visualization ===")

    families = [m.get("base_family") or m["family"] for m in meta]
    unique_families = sorted(set(families))
    colors = plt.cm.tab10(np.linspace(0, 1, len(unique_families)))
    family_colors = {f: colors[i] for i, f in enumerate(unique_families)}

    reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
    projected = reducer.fit_transform(embeddings)

    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    for fam in unique_families:
        mask = [i for i, f in enumerate(families) if f == fam]
        ax.scatter(
            projected[mask, 0], projected[mask, 1],
            c=[family_colors[fam]], label=fam, alpha=0.6, s=20
        )

    ax.legend(title="Model Family", fontsize=10)
    ax.set_title("UMAP: Self-Concept Response Embeddings by Family", fontsize=14)
    ax.set_xlabel("UMAP 1")
    ax.set_ylabel("UMAP 2")

    out_path = ANALYSIS_DIR / "umap_family_projection.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out_path}")
    return str(out_path)


def main():
    import random
    random.seed(42)
    np.random.seed(42)

    print("Geometric Phylogeny — Embedding Computation & Analysis")
    print("=" * 60)

    # Load results
    all_data = load_all_results()
    if not all_data:
        print("No results found! Run phylogeny_runner.py first.")
        return

    print(f"Loaded results for {len(all_data)} models:")
    for mk, data in all_data.items():
        print(f"  {mk}: {data['num_results']} responses ({data['family']})")

    # Compute embeddings
    embeddings, meta = compute_embeddings(all_data)
    embeddings = np.array(embeddings)

    print(f"\nTotal embeddings: {len(embeddings)}")

    # Save embeddings
    emb_path = ANALYSIS_DIR / "embeddings.npz"
    np.savez_compressed(emb_path, embeddings=embeddings)
    meta_path = ANALYSIS_DIR / "embedding_meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Saved embeddings: {emb_path}")

    # Run all pre-registered analyses
    results = {
        "timestamp": datetime.now().isoformat(),
        "embedding_model": EMBEDDING_MODEL,
        "n_models": len(all_data),
        "n_embeddings": len(embeddings),
        "models": list(all_data.keys()),
    }

    results["H1"] = h1_within_vs_between(embeddings, meta)
    results["H2"] = h2_family_classification(embeddings, meta)
    results["H3"] = h3_personality_vs_function(embeddings, meta)
    results["H4"] = h4_scaling_effect(embeddings, meta)
    results["H5"] = h5_crosslineage(embeddings, meta)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for h in ["H1", "H2", "H3", "H4", "H5"]:
        status = "SUPPORTED" if results[h]["supported"] else "NOT SUPPORTED"
        print(f"  {h}: {status}")

    # UMAP visualization
    umap_path = generate_umap_visualization(embeddings, meta)

    # Save analysis
    analysis_path = ANALYSIS_DIR / "hypothesis_results.json"
    with open(analysis_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull results: {analysis_path}")


if __name__ == "__main__":
    main()
