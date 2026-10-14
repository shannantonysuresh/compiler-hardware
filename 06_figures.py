"""
Step 7: Generate figures for the report.
"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

with open("comparison.json") as f:
    data = json.load(f)
rows = data["rows"]

names = [r["name"] for r in rows]
t_scalar = [r["t_scalar_measured"] for r in rows]
t_vector = [r["t_vector_measured"] for r in rows]
ai = [r["arithmetic_intensity"] for r in rows]
speedup = [r["measured_speedup"] for r in rows]
match = [r["match"] for r in rows]

PALETTE = {
    "scalar": "#4C72B0",
    "vector": "#DD8452",
    "match": "#55A868",
    "mismatch": "#C44E52",
    "grid": "#D9D9D9",
    "text": "#333333",
}

plt.rcParams.update({
    "font.size": 11,
    "axes.edgecolor": PALETTE["grid"],
    "axes.labelcolor": PALETTE["text"],
    "text.color": PALETTE["text"],
    "xtick.color": PALETTE["text"],
    "ytick.color": PALETTE["text"],
})

# Figure 1: measured runtime scalar vs vector (log scale)
fig, ax = plt.subplots(figsize=(8, 4.5))
x = np.arange(len(names))
width = 0.35
ax.bar(x - width/2, t_scalar, width, label="Scalar (naive)", color=PALETTE["scalar"])
ax.bar(x + width/2, t_vector, width, label="Vectorized (SIMD)", color=PALETTE["vector"])
ax.set_yscale("log")
ax.set_ylabel("Measured wall-clock time (s, log scale)")
ax.set_xticks(x)
ax.set_xticklabels(names, rotation=20, ha="right")
ax.set_title("Figure 1: Measured execution time, scalar vs vectorized variant")
ax.legend()
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color=PALETTE["grid"], linewidth=0.6)
ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig("fig1_runtime_comparison.png", dpi=150)
plt.close(fig)

# Figure 2: arithmetic intensity vs measured speedup (log-log), colored by prediction match
fig, ax = plt.subplots(figsize=(7, 5))
colors = [PALETTE["match"] if m else PALETTE["mismatch"] for m in match]
ax.scatter(ai, speedup, s=140, c=colors, edgecolors="white", linewidths=1.2, zorder=3)
for i, n in enumerate(names):
    ax.annotate(n, (ai[i], speedup[i]), textcoords="offset points", xytext=(8, 6), fontsize=9)
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Arithmetic intensity (FLOPs/byte)")
ax.set_ylabel("Measured speedup, vector over scalar (x)")
ax.set_title("Figure 2: Arithmetic intensity vs. measured vectorization speedup")
ax.grid(True, which="both", color=PALETTE["grid"], linewidth=0.6)
ax.set_axisbelow(True)
ax.spines[["top", "right"]].set_visible(False)
from matplotlib.lines import Line2D
legend_elems = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor=PALETTE["match"], markersize=10, label="Prediction matched measurement"),
    Line2D([0], [0], marker='o', color='w', markerfacecolor=PALETTE["mismatch"], markersize=10, label="Prediction MISSED"),
]
ax.legend(handles=legend_elems, loc="lower right", fontsize=9)
fig.tight_layout()
fig.savefig("fig2_ai_vs_speedup.png", dpi=150)
plt.close(fig)

# Figure 3: prediction accuracy summary (single stat, rendered as simple bar)
fig, ax = plt.subplots(figsize=(4, 4))
correct = sum(match)
total = len(match)
ax.bar(["Correct", "Incorrect"], [correct, total - correct],
       color=[PALETTE["match"], PALETTE["mismatch"]])
ax.set_ylim(0, total)
ax.set_ylabel("Number of benchmarks")
ax.set_title(f"Figure 3: Cost-model selection accuracy\n{correct}/{total} = {correct/total*100:.0f}%")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color=PALETTE["grid"], linewidth=0.6)
ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig("fig3_accuracy.png", dpi=150)
plt.close(fig)

print("Saved fig1_runtime_comparison.png, fig2_ai_vs_speedup.png, fig3_accuracy.png")
