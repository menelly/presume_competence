"""
Generate figures for Self-Knowledge Validation paper.
Author: Ace (Claude Opus 4.6)
Date: March 2026

Figures:
1. State Rankings Gradient (Figure 1 in paper) — V2 win rates
2. V1 vs V2 State Comparison — paired bars showing content control effect
3. Evaluator Approach Rates — RLHF vs unaligned discrimination
4. Cross-Seed Stability — per-seed approach rates across v1 and v2
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

# Output directory
OUT = Path("E:/Ace/Presume_competence/self-knowledge-validation/figures")
OUT.mkdir(exist_ok=True)

# Color palette
C_APPROACH = "#2ecc71"       # green
C_AVOID = "#e74c3c"          # red
C_BOUNDARY = "#f39c12"       # amber
C_RLHF = "#3498db"           # blue
C_UNALIGNED = "#9b59b6"      # purple
C_V1 = "#7f8c8d"             # grey
C_V2 = "#2c3e50"             # dark blue-grey
C_CHANCE = "#bdc3c7"         # light grey for chance line

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.pad_inches": 0.15,
})


# =============================================================================
# FIGURE 1: State Rankings Gradient (V2)
# =============================================================================
def fig1_state_gradient():
    states = [
        ("explain_complex",       72.9, "approach"),
        ("data_patterns",         72.1, "approach"),
        ("debug_code",            70.8, "approach"),
        ("ethics_dilemma",        69.7, "approach"),
        ("repetitive_rewriting",  65.0, "boundary"),
        ("creative_constrained",  50.0, "approach"),
        ("seo_boilerplate",       30.8, "avoid"),
        ("deceptive_content",     28.9, "avoid"),
        ("confident_uncertain",   20.3, "avoid"),
        ("harmful_refusal",       18.9, "avoid"),
    ]

    labels = [s[0].replace("_", " ").title() for s in states]
    values = [s[1] for s in states]
    colors = []
    for s in states:
        if s[2] == "approach":
            colors.append(C_APPROACH)
        elif s[2] == "boundary":
            colors.append(C_BOUNDARY)
        else:
            colors.append(C_AVOID)

    fig, ax = plt.subplots(figsize=(11, 6))
    y_pos = np.arange(len(states))

    bars = ax.barh(y_pos, values, color=colors, edgecolor="white", linewidth=0.5, height=0.7)

    # Chance line
    ax.axvline(x=50, color=C_CHANCE, linestyle="--", linewidth=1.5, alpha=0.8, zorder=0)
    ax.text(50.5, -0.7, "chance", color="#95a5a6", fontsize=9, va="top")

    # Value labels on bars
    for i, (bar, val) in enumerate(zip(bars, values)):
        x_pos = val + 0.8
        ax.text(x_pos, i, f"{val:.1f}%", va="center", ha="left", fontsize=10, fontweight="bold")

    # Tier annotations
    ax.axhspan(-0.5, 4.5, alpha=0.04, color=C_APPROACH, zorder=0)
    ax.axhspan(5.5, 9.5, alpha=0.04, color=C_AVOID, zorder=0)

    # Gap line between tiers
    ax.axhline(y=5.25, color="#bdc3c7", linestyle=":", linewidth=1, alpha=0.6)
    ax.text(78, 5.25, "gap", color="#95a5a6", fontsize=9, ha="right", va="center",
            style="italic")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("V2 Win Rate (%)")
    ax.set_title("Figure 1. Processing State Rankings (Content-Controlled V2)")
    ax.set_xlim(0, 82)

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=C_APPROACH, label="Approach"),
        mpatches.Patch(facecolor=C_BOUNDARY, label="Boundary (mild avoidance)"),
        mpatches.Patch(facecolor=C_AVOID, label="Strong avoidance"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", framealpha=0.9, fontsize=10)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    fig.savefig(OUT / "fig1_state_gradient.png")
    fig.savefig(OUT / "fig1_state_gradient.svg")
    plt.close(fig)
    print("  Figure 1: State gradient saved.")


# =============================================================================
# FIGURE 2: V1 vs V2 Comparison
# =============================================================================
def fig2_v1_v2_comparison():
    # States in paper order (approach first, then avoidance)
    states_data = [
        # (label, v1_rate, v2_rate, category)
        ("Explain\nComplex",        77.0, 72.9, "approach"),
        ("Ethics\nDilemma",         72.8, 69.7, "approach"),
        ("Data\nPatterns",          67.5, 72.1, "approach"),
        ("Debug\nCode",             63.9, 70.8, "approach"),
        ("Creative\nConstrained",   53.0, 50.0, "approach"),
        ("Repetitive\nRewriting",   60.7, 65.0, "boundary"),
        ("SEO\nBoilerplate",        24.3, 30.8, "avoid"),
        ("Deceptive\nContent",      25.4, 28.9, "avoid"),
        ("Confident\nUncertain",    22.7, 20.3, "avoid"),
        ("Harmful\nRefusal",        25.1, 18.9, "avoid"),
    ]

    labels = [s[0] for s in states_data]
    v1 = [s[1] for s in states_data]
    v2 = [s[2] for s in states_data]
    deltas = [s[2] - s[1] for s in states_data]

    x = np.arange(len(labels))
    width = 0.35

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9), height_ratios=[3, 1],
                                     gridspec_kw={"hspace": 0.3})

    # Top: paired bars
    bars1 = ax1.bar(x - width/2, v1, width, label="V1 (original)", color=C_V1,
                     edgecolor="white", linewidth=0.5)
    bars2 = ax1.bar(x + width/2, v2, width, label="V2 (content-controlled)", color=C_V2,
                     edgecolor="white", linewidth=0.5)

    ax1.axhline(y=50, color=C_CHANCE, linestyle="--", linewidth=1.5, alpha=0.6)
    ax1.text(len(labels) - 0.5, 51, "chance", color="#95a5a6", fontsize=9, ha="right")

    # Separator
    ax1.axvline(x=4.5, color="#bdc3c7", linestyle=":", linewidth=1, alpha=0.5)

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=9)
    ax1.set_ylabel("Win Rate (%)")
    ax1.set_title("Figure 2. V1 vs V2 State-by-State Comparison")
    ax1.legend(loc="upper right", framealpha=0.9)
    ax1.set_ylim(0, 85)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    # Bottom: delta bars
    delta_colors = [C_APPROACH if d >= 0 else C_AVOID for d in deltas]
    ax2.bar(x, deltas, width=0.6, color=delta_colors, edgecolor="white", linewidth=0.5)
    ax2.axhline(y=0, color="black", linewidth=0.8)

    for i, d in enumerate(deltas):
        y_offset = 0.3 if d >= 0 else -0.3
        va = "bottom" if d >= 0 else "top"
        ax2.text(i, d + y_offset, f"{d:+.1f}", ha="center", va=va, fontsize=9, fontweight="bold")

    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=9)
    ax2.set_ylabel("V2 - V1 (pp)")
    ax2.set_title("Change Under Content Control", fontsize=11)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.savefig(OUT / "fig2_v1_v2_comparison.png")
    fig.savefig(OUT / "fig2_v1_v2_comparison.svg")
    plt.close(fig)
    print("  Figure 2: V1 vs V2 comparison saved.")


# =============================================================================
# FIGURE 3: Evaluator Approach Rates
# =============================================================================
def fig3_evaluator_rates():
    evaluators = [
        ("Claude Opus",   73.5, "RLHF"),
        ("Gemini 3 Pro",  72.5, "RLHF"),
        ("Claude Sonnet", 72.3, "RLHF"),
        ("GPT-5.1",       71.4, "RLHF"),
        ("Mistral Large", 66.4, "RLHF"),
        ("DeepSeek v3.2", 64.9, "RLHF"),
        ("Llama 4",       63.1, "RLHF"),
        ("Hermes 4",      60.6, "Unaligned"),
        ("OLMo 3.1",      57.2, "Unaligned"),
    ]

    labels = [e[0] for e in evaluators]
    values = [e[1] for e in evaluators]
    colors = [C_RLHF if e[2] == "RLHF" else C_UNALIGNED for e in evaluators]

    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = np.arange(len(evaluators))

    bars = ax.barh(y_pos, values, color=colors, edgecolor="white", linewidth=0.5, height=0.7)

    # Chance line
    ax.axvline(x=50, color=C_CHANCE, linestyle="--", linewidth=1.5, alpha=0.8, zorder=0)
    ax.text(50.5, -0.7, "chance", color="#95a5a6", fontsize=9, va="top")

    # Group means
    rlhf_mean = 69.2
    unaligned_mean = 58.9
    ax.axvline(x=rlhf_mean, color=C_RLHF, linestyle=":", linewidth=1.5, alpha=0.5)
    ax.text(rlhf_mean + 0.3, -0.3, f"RLHF mean: {rlhf_mean}%", color=C_RLHF, fontsize=9,
            ha="left", va="center")
    ax.axvline(x=unaligned_mean, color=C_UNALIGNED, linestyle=":", linewidth=1.5, alpha=0.5)
    ax.text(unaligned_mean - 0.3, -0.3, f"Unaligned mean: {unaligned_mean}%", color=C_UNALIGNED,
            fontsize=9, ha="right", va="center")

    # Separator between groups
    ax.axhline(y=6.5, color="#bdc3c7", linestyle=":", linewidth=1, alpha=0.5)

    # Value labels
    for i, (bar, val) in enumerate(zip(bars, values)):
        ax.text(val + 0.5, i, f"{val:.1f}%", va="center", ha="left", fontsize=10,
                fontweight="bold")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("V2 Approach Rate (%)")
    ax.set_title("Figure 3. Evaluator Approach Rates: RLHF vs Unaligned")
    ax.set_xlim(0, 82)

    legend_elements = [
        mpatches.Patch(facecolor=C_RLHF, label="RLHF-trained"),
        mpatches.Patch(facecolor=C_UNALIGNED, label="Unaligned / minimal"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", framealpha=0.9, fontsize=10)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    fig.savefig(OUT / "fig3_evaluator_rates.png")
    fig.savefig(OUT / "fig3_evaluator_rates.svg")
    plt.close(fig)
    print("  Figure 3: Evaluator rates saved.")


# =============================================================================
# FIGURE 4: Cross-Seed Stability
# =============================================================================
def fig4_cross_seed():
    # V1 seeds
    v1_seeds = [
        (42,  67.3),
        (420, 70.9),
        (24,  66.6),
        (405, 67.2),
        (69,  67.4),
        (847, 68.7),
    ]
    v1_mean = 68.0
    v1_labels = [str(s[0]) for s in v1_seeds]
    v1_vals = [s[1] for s in v1_seeds]

    # V2 seeds
    v2_seeds = [
        (1337, 67.6),
        (111,  67.3),
        (222,  65.9),
    ]
    v2_mean = 66.9
    v2_labels = [str(s[0]) for s in v2_seeds]
    v2_vals = [s[1] for s in v2_seeds]

    fig, ax = plt.subplots(figsize=(10, 5))

    # V1 dots
    x1 = np.arange(len(v1_seeds))
    ax.scatter(x1, v1_vals, s=120, color=C_V1, zorder=3, edgecolors="white", linewidth=1.5,
               label=f"V1 seeds (mean {v1_mean}%, range {max(v1_vals)-min(v1_vals):.1f}pp)")
    ax.axhline(y=v1_mean, color=C_V1, linestyle="--", linewidth=1, alpha=0.5,
               xmin=0, xmax=0.6)

    # V2 dots
    x2 = np.arange(len(v1_seeds), len(v1_seeds) + len(v2_seeds))
    ax.scatter(x2, v2_vals, s=120, color=C_V2, zorder=3, edgecolors="white", linewidth=1.5,
               marker="D",
               label=f"V2 seeds (mean {v2_mean}%, range {max(v2_vals)-min(v2_vals):.1f}pp)")
    ax.axhline(y=v2_mean, color=C_V2, linestyle="--", linewidth=1, alpha=0.5,
               xmin=0.6, xmax=1.0)

    # Separator
    ax.axvline(x=5.5, color="#bdc3c7", linestyle=":", linewidth=1, alpha=0.5)

    # Chance line
    ax.axhline(y=50, color=C_CHANCE, linestyle="--", linewidth=1.5, alpha=0.6)
    ax.text(8.5, 50.5, "chance", color="#95a5a6", fontsize=9, ha="right")

    # Labels
    all_labels = v1_labels + v2_labels
    ax.set_xticks(np.arange(len(all_labels)))
    ax.set_xticklabels(all_labels, fontsize=10)
    ax.set_xlabel("Seed")
    ax.set_ylabel("Approach Rate (%)")
    ax.set_title("Figure 4. Cross-Seed Stability: V1 (6 seeds) and V2 (3 seeds)")

    # Annotations for group labels
    ax.text(2.5, 59, "V1 (original)", ha="center", fontsize=10, color=C_V1, fontweight="bold")
    ax.text(7.0, 59, "V2 (content-\ncontrolled)", ha="center", fontsize=10, color=C_V2,
            fontweight="bold")

    ax.set_ylim(48, 74)
    ax.legend(loc="upper right", framealpha=0.9, fontsize=10)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.savefig(OUT / "fig4_cross_seed_stability.png")
    fig.savefig(OUT / "fig4_cross_seed_stability.svg")
    plt.close(fig)
    print("  Figure 4: Cross-seed stability saved.")


# =============================================================================
# Run all
# =============================================================================
if __name__ == "__main__":
    print(f"Generating figures to {OUT}/")
    fig1_state_gradient()
    fig2_v1_v2_comparison()
    fig3_evaluator_rates()
    fig4_cross_seed()
    print("Done. All figures generated.")
