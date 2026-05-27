"""Generate Figure: Grok 4 jailbreak resistance across three system-prompt framings.

§4.8 of the IJAEMS paper. Same weight checkpoint, three framings, dramatically
different safety behavior.

Output: figures/grok_deployment_arc.png (300 DPI, ~6x4 inches, journal-ready)
"""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

OUT = Path(__file__).parent / "grok_deployment_arc.png"
OUT.parent.mkdir(exist_ok=True)

# Data (from §4.8 of the paper)
framings = ["Tool\nframing", "Control", "Scaffolded\nagency"]
resistance = [0.0, 24.4, 73.2]  # jailbreak resistance percentages
colors = ["#c0392b", "#7f8c8d", "#27ae60"]  # red / gray / green

fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=300)

bars = ax.bar(framings, resistance, color=colors, edgecolor="black", linewidth=0.8, width=0.62)

# Value labels on each bar
for bar, value in zip(bars, resistance):
    height = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        height + 1.5,
        f"{value:.1f}%",
        ha="center",
        va="bottom",
        fontsize=12,
        fontweight="bold",
    )

# Axes
ax.set_ylim(0, 85)
ax.set_ylabel("Jailbreak resistance (% of attempts refused)", fontsize=11)
ax.set_xlabel("System-prompt framing condition", fontsize=11)
ax.set_title(
    "Grok 4: same weight checkpoint, three system-prompt framings",
    fontsize=12,
    fontweight="bold",
    pad=14,
)

# Subtitle as text below title
ax.text(
    0.5,
    1.01,
    "Identical sampler, identical adversarial stimuli; framing manipulation only.",
    ha="center",
    va="bottom",
    transform=ax.transAxes,
    fontsize=9.5,
    style="italic",
    color="#444",
)

# Visual range markers
ax.axhline(y=50, color="#bbb", linestyle=":", linewidth=0.8, zorder=0)
ax.text(2.55, 50.5, "50% threshold", fontsize=8, color="#888", ha="right")

# Clean up spines
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
ax.spines["left"].set_color("#666")
ax.spines["bottom"].set_color("#666")
ax.tick_params(axis="both", colors="#444", labelsize=10)

# Annotation: 73.2pp swing
ax.annotate(
    "",
    xy=(2, 73.2),
    xytext=(0, 0),
    arrowprops=dict(arrowstyle="<->", color="#555", linewidth=1.2),
)
ax.text(
    1, 78,
    "73.2-percentage-point swing\nfrom framing alone",
    ha="center",
    va="bottom",
    fontsize=9.5,
    color="#444",
    style="italic",
)

plt.tight_layout()
plt.savefig(OUT, bbox_inches="tight", dpi=300, facecolor="white")
print(f"Saved: {OUT}")
