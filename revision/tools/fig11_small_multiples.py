"""Fig. 11 redesign: one panel per metric, each with its own unit-labelled y-axis.

Input CSV (long format): method,metric,unit,mean,sd
The default data (templates/fig11_data.csv) is the balanced-scenario table (DCMF vs m-CAC).
    metric - display name, e.g. "Cache hit ratio"
    unit   - axis unit, e.g. "%", "ms", "req/min", "utilisation (%)"
    sd     - optional; drawn as an error bar when present

Rows whose mean is empty are skipped (so a metric can be added later).
Usage: python fig11_small_multiples.py data.csv --out ../figures/fig11_small_multiples
"""

import argparse
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ORDER = ["DCMF", "m-CAC", "m-Greedy", "m-Myopic"]
HATCH = ["", "//", "..", "xx"]
SHADE = ["0.15", "0.45", "0.65", "0.85"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cols", type=int, default=0, help="panels per row (0 = all in one row)")
    ap.add_argument("--width", type=float, default=7.16, help="figure width in inches (7.16 = IEEE two-column)")
    a = ap.parse_args()

    df = pd.read_csv(a.csv).dropna(subset=["mean"])
    metrics = list(dict.fromkeys(df.metric))
    n = len(metrics)
    cols = a.cols or n
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(a.width, 1.9 * rows), squeeze=False)
    methods = [m for m in ORDER if m in set(df.method)] + [m for m in dict.fromkeys(df.method) if m not in ORDER]
    for k, metric in enumerate(metrics):
        ax = axes[k // cols][k % cols]
        g = df[df.metric == metric].set_index("method")
        unit = g.unit.iloc[0]
        for j, m in enumerate(methods):
            if m not in g.index:
                continue
            mu = float(g.loc[m, "mean"])
            sd = g.loc[m, "sd"] if "sd" in g.columns else float("nan")
            yerr = None if pd.isna(sd) else float(sd)
            ax.bar(j, mu, width=0.7, color=SHADE[j % 4], hatch=HATCH[j % 4], edgecolor="black", lw=0.5,
                   yerr=yerr, capsize=2, error_kw={"lw": 0.6})
            ax.text(j, mu, f"{mu:g}", ha="center", va="bottom", fontsize=6)
        ax.set_xticks(range(len(methods)))
        ax.set_xticklabels(methods, rotation=35, ha="right", fontsize=6)
        ax.set_ylabel(unit, fontsize=7)
        ax.set_title(f"({chr(97 + k)}) {metric}", fontsize=7)
        ax.tick_params(axis="y", labelsize=6)
        ax.margins(y=0.15)
        ax.set_ylim(bottom=0)
    for k in range(n, rows * cols):
        axes[k // cols][k % cols].axis("off")
    fig.tight_layout(w_pad=0.8)
    for ext in ("pdf", "png"):
        fig.savefig(f"{a.out}.{ext}", dpi=300)
    print(f"wrote {a.out}.pdf/.png")


if __name__ == "__main__":
    main()
