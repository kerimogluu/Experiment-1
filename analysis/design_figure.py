"""Draws the experimental-design figure used in Section 2.2 of the report."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(9, 4.2))
ax.set_xlim(0, 900); ax.set_ylim(0, 420); ax.axis("off")
ink, quiet, edge, tint = "#111111", "#666666", "#888888", "#ececec"

def box(x, y, w, h, text, fill="white", lw=1.2, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=8",
                                fc=fill, ec=edge if fill == "white" else "#2b6cb0", lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9.5,
            color=ink, fontweight="bold" if bold else "normal")

# pipeline
box(20, 350, 230, 44, "Machine + JVM (the 'subject')", fill="#e6f0fb", lw=1.8, bold=True)
box(300, 350, 280, 44, "10 warm-up rounds (not measured)")
box(630, 350, 250, 44, "810 timed runs in random order")
for x0, x1 in [(250, 298), (580, 628)]:
    ax.annotate("", xy=(x1, 372), xytext=(x0, 372), arrowprops=dict(arrowstyle="-|>", color=edge))
ax.annotate("", xy=(755, 302), xytext=(755, 350), arrowprops=dict(arrowstyle="-|>", color=edge))

# grid
x0, cw, gw, y_top, rh = 180, 78, 234, 230, 46
for g, name in enumerate(["sorted", "reversed", "random"]):
    box(x0 + g * gw + 3, 268, gw - 6, 30, name, bold=True)
    for k, n in enumerate(["1,000", "5,000", "10,000"]):
        ax.text(x0 + g * gw + k * cw + cw / 2, 250, n, ha="center", fontsize=9, color=quiet)
ax.text(20, 280, "Input type", fontsize=9, color=quiet, va="center")
ax.text(20, 250, "Array size n", fontsize=9, color=quiet)
for r, alg in enumerate(["PassPerItem", "UntilNoChange", "WhileNeeded"]):
    y = y_top - r * rh
    ax.text(20, y - rh / 2, alg, fontsize=10, fontweight="bold", color=ink, va="center")
    for c in range(9):
        ax.add_patch(FancyBboxPatch((x0 + c * cw + 4, y - rh + 4), cw - 8, rh - 8,
                                    boxstyle="round,pad=0,rounding_size=5", fc=tint, ec="#d0d0d0", lw=0.8))
for g in (1, 2):
    ax.plot([x0 + g * gw] * 2, [92, 262], color=edge, lw=0.8)
ax.text(20, 60, "Rows: algorithm · columns: input type × array size · each cell is one condition, measured 30 times "
        "(27 conditions, 810 runs).", fontsize=8.5, color=quiet)
fig.tight_layout()
fig.savefig("results/design.png", dpi=220)
