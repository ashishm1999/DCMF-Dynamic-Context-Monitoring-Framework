"""Fig. 12 with a single, consistent throughput unit (requests per minute).

Throughput is defined (Table V) as  TP = 60 * N_c / T  [req/min],
where N_c is the number of requests completed in a measurement window of
T seconds. If the input is in requests per second, pass --input-unit rps and
the values are multiplied by 60.

Input CSV: method,load,throughput[,sd]   (load = offered load, e.g. queries/min or #clients)
Usage: python fig12_throughput.py data.csv --load-label "Offered load (queries/min)" --out ../figures/fig12_throughput
"""

import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ORDER = ["DCMF", "m-CAC", "m-Greedy", "m-Myopic"]
STYLE = {"DCMF": ("-", "o"), "m-CAC": ("--", "s"), "m-Greedy": ("-.", "^"), "m-Myopic": (":", "d")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", required=True)
    ap.add_argument("--load-label", default="Offered load (queries/min)")
    ap.add_argument("--input-unit", choices=["rpm", "rps"], default="rpm")
    a = ap.parse_args()
    df = pd.read_csv(a.csv)
    k = 60.0 if a.input_unit == "rps" else 1.0
    fig, ax = plt.subplots(figsize=(3.5, 2.3))
    for m in [m for m in ORDER if m in set(df.method)] + [m for m in dict.fromkeys(df.method) if m not in ORDER]:
        g = df[df.method == m].sort_values("load")
        ls, mk = STYLE.get(m, ("-", "x"))
        y = g.throughput * k
        ax.plot(g.load, y, ls, marker=mk, ms=3, lw=1, color="black", label=m)
        if "sd" in g and g.sd.notna().any():
            ax.fill_between(g.load, y - g.sd * k, y + g.sd * k, color="0.85", lw=0)
    ax.set_xlabel(a.load_label, fontsize=8)
    ax.set_ylabel("Throughput (req/min)", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=6.5, frameon=False)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(f"{a.out}.{ext}", dpi=300)
    print(f"wrote {a.out}.pdf/.png")


if __name__ == "__main__":
    main()
