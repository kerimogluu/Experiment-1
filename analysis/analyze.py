"""Descriptive statistics, plots and hypothesis check for Experiment 1.

Usage (from the repository root):
    python3 analysis/analyze.py [data/results.csv] [results]

Outputs (in the results directory):
    summary.csv       descriptive statistics per (algorithm, input type, size)
    hypotheses.txt    evaluation of H1 and H2
    boxplots.png      execution time distributions, one panel per input type x size

Decision rule used for "A has a lower median execution time than B":
    Q3(A) < Q1(B), i.e. the middle halves (IQRs) of the runs do not overlap
    (this implies median(A) < median(B); both are checked below).
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ALGORITHMS = ["PassPerItem", "UntilNoChange", "WhileNeeded"]
INPUT_TYPES = ["SORTED", "REVERSE", "RANDOM"]


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["input_type", "size", "algorithm"])["time_ms"]
    s = pd.DataFrame({
        "n": g.count(),
        "min": g.min(),
        "q1": g.quantile(0.25),
        "median": g.median(),
        "mean": g.mean(),
        "q3": g.quantile(0.75),
        "max": g.max(),
        "std": g.std(),
    })
    s["iqr"] = s["q3"] - s["q1"]
    s = s.reset_index()
    s["input_type"] = pd.Categorical(s["input_type"], INPUT_TYPES, ordered=True)
    s["algorithm"] = pd.Categorical(s["algorithm"], ALGORITHMS, ordered=True)
    return s.sort_values(["input_type", "size", "algorithm"]).reset_index(drop=True)


def lower(summary: pd.DataFrame, t: str, n: int, a: str, b: str) -> tuple[bool, str]:
    """Is algorithm a 'lower' than b (decision rule above) for input t, size n?"""
    row = lambda alg: summary[(summary.input_type == t) & (summary["size"] == n)
                              & (summary.algorithm == alg)].iloc[0]
    ra, rb = row(a), row(b)
    ok = ra["median"] < rb["median"] and ra["q3"] < rb["q1"]
    detail = (f"{a}: median={ra['median']:.4f} ms IQR=[{ra['q1']:.4f}, {ra['q3']:.4f}]  vs  "
              f"{b}: median={rb['median']:.4f} ms IQR=[{rb['q1']:.4f}, {rb['q3']:.4f}]")
    return ok, detail


def evaluate(summary: pd.DataFrame) -> str:
    sizes = sorted(summary["size"].unique())
    lines = ["Decision rule: A < B  iff  median(A) < median(B) and Q3(A) < Q1(B)", ""]

    lines.append("H1: For every input type and array size, WhileNeeded has a lower median "
                 "execution time than PassPerItem and UntilNoChange.")
    h1 = True
    for t in INPUT_TYPES:
        for n in sizes:
            for other in ["PassPerItem", "UntilNoChange"]:
                ok, d = lower(summary, t, n, "WhileNeeded", other)
                h1 &= ok
                lines.append(f"  [{'OK  ' if ok else 'FAIL'}] {t:7s} n={n:<6d} {d}")
    lines.append(f"  => H1 {'SUPPORTED' if h1 else 'NOT SUPPORTED'}")
    lines.append("")

    lines.append("H2: On sorted input, UntilNoChange and WhileNeeded have a lower median "
                 "execution time than PassPerItem for every array size.")
    h2 = True
    for n in sizes:
        for alg in ["UntilNoChange", "WhileNeeded"]:
            ok, d = lower(summary, "SORTED", n, alg, "PassPerItem")
            h2 &= ok
            lines.append(f"  [{'OK  ' if ok else 'FAIL'}] SORTED  n={n:<6d} {d}")
    lines.append(f"  => H2 {'SUPPORTED' if h2 else 'NOT SUPPORTED'}")
    return "\n".join(lines) + "\n"


def plot_boxplots(df: pd.DataFrame, sizes, out: Path) -> None:
    fig, axes = plt.subplots(len(INPUT_TYPES), len(sizes),
                             figsize=(4 * len(sizes), 3.2 * len(INPUT_TYPES)))
    for i, t in enumerate(INPUT_TYPES):
        for j, n in enumerate(sizes):
            ax = axes[i][j]
            data = [df[(df.input_type == t) & (df["size"] == n) & (df.algorithm == a)]["time_ms"]
                    for a in ALGORITHMS]
            ax.boxplot(data, showfliers=False)
            # Overlay every run (with horizontal jitter) so that clusters are visible.
            jitter = np.random.default_rng(0)
            for k, d in enumerate(data, start=1):
                xs = k + jitter.uniform(-0.18, 0.18, len(d))
                ax.scatter(xs, d, s=7, alpha=0.55, color="tab:blue", linewidths=0, zorder=3)
            ax.set_xticks([1, 2, 3])
            ax.set_xticklabels(["PassPer\nItem", "UntilNo\nChange", "While\nNeeded"])
            # Sorted input spans >3 orders of magnitude -> log scale; the other
            # rows are shown on a linear scale (not starting at 0) for readability.
            plain = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}")
            if t == "SORTED":
                ax.set_yscale("log")
                ax.yaxis.set_major_locator(matplotlib.ticker.LogLocator(base=10, subs=(1, 2, 5)))
                ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
            ax.yaxis.set_major_formatter(plain)
            ax.set_title(f"{ {'SORTED':'sorted','REVERSE':'reversed','RANDOM':'random'}[t]}, n = {n:,}", fontsize=12)
            if j == 0:
                ax.set_ylabel("time per sort (ms, log scale)" if t == "SORTED" else "time per sort (ms)")
            ax.tick_params(labelsize=10)
            ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)


def main() -> None:
    csv = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/results.csv")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("results")
    out.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv)
    df["time_ms"] = df["time_ns"] / 1e6
    sizes = sorted(df["size"].unique())

    summary = summarize(df)
    summary.to_csv(out / "summary.csv", index=False, float_format="%.6f")
    report = evaluate(summary)
    (out / "hypotheses.txt").write_text(report)
    plot_boxplots(df, sizes, out / "boxplots.png")

    with pd.option_context("display.width", 200, "display.max_rows", 100):
        print(summary.round(4).to_string(index=False))
    print()
    print(report)


if __name__ == "__main__":
    main()
