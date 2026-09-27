"""Build LaTeX result tables with mean +/- SD and 95% confidence intervals.

Input: a *wide* CSV with one row per independent run (seed / repetition):

    table,scenario,method,run,CHR,CER,RT_ms,CRR,TP_req_per_min,...

* ``table``    - e.g. "VII", "VIII", "IX" (one LaTeX table is written per value)
* ``scenario`` - row group inside a table (e.g. "Scenario 1: freshness")
* ``method``   - DCMF, m-CAC, m-Greedy, m-Myopic
* ``run``      - run identifier (seed); runs are paired across methods by this id

Usage:

    python make_stats_tables.py runs.csv --out tables/ \
        --metric CHR:"CHR (\\%)":100:1:max --metric CER:"CER (\\%)":100:1:min \
        --metric RT_ms:"RT (ms)":1:1:min

Each ``--metric`` is ``column:header:scale:digits:better`` where ``better`` is
``max`` or ``min`` (used to bold the best mean in each scenario).

Per table the script writes ``table_<id>.tex`` (cells "mean $\\pm$ SD" with the
95% CI underneath) and ``table_<id>_tests.csv`` with paired t-test and
Wilcoxon signed-rank p-values of the reference method against each other
method (Holm-corrected within each scenario and metric family).
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stats_utils import mean_sd_ci, paired_tests  # noqa: E402


def holm(pvals):
    p = np.asarray(pvals, dtype=float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    m = len(p)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * p[idx])
        adj[idx] = min(running, 1.0)
    return adj


def parse_metric(s):
    parts = s.split(":")
    if len(parts) != 5:
        raise argparse.ArgumentTypeError("metric must be column:header:scale:digits:max|min")
    col, header, scale, digits, better = parts
    return dict(col=col, header=header, scale=float(scale), digits=int(digits), better=better)


def build(df, metrics, ref, method_order, caption, label, ci_rows=True):
    methods = [m for m in method_order if m in df.method.unique()] + \
              [m for m in df.method.unique() if m not in method_order]
    lines = ["\\begin{table}[t]", "\\centering", f"\\caption{{{caption}}}", f"\\label{{{label}}}",
             "\\footnotesize", "\\setlength{\\tabcolsep}{3pt}",
             "\\begin{tabular}{l" + "c" * len(metrics) + "}", "\\toprule",
             "Method & " + " & ".join(m["header"] for m in metrics) + " \\\\", "\\midrule"]
    tests = []
    n_runs = set()
    for si, (scen, g) in enumerate(df.groupby("scenario", sort=False)):
        if df.scenario.nunique() > 1:
            if si:
                lines.append("\\midrule")
            lines.append(f"\\multicolumn{{{len(metrics) + 1}}}{{l}}{{\\textit{{{scen}}}}} \\\\")
        stats = {}
        for meth in methods:
            gm = g[g.method == meth]
            for m in metrics:
                stats[(meth, m["col"])] = mean_sd_ci(gm[m["col"]].values)
                n_runs.add(stats[(meth, m["col"])][4])
        best = {}
        for m in metrics:
            vals = {meth: stats[(meth, m["col"])][0] for meth in methods}
            best[m["col"]] = (max if m["better"] == "max" else min)(vals, key=vals.get)
        for meth in methods:
            cells, cis = [], []
            for m in metrics:
                mu, sd, lo, hi, n = stats[(meth, m["col"])]
                s, d = m["scale"], m["digits"]
                cell = f"{mu * s:.{d}f} $\\pm$ {sd * s:.{d}f}"
                if best[m["col"]] == meth:
                    cell = f"\\textbf{{{mu * s:.{d}f}}} $\\pm$ {sd * s:.{d}f}"
                cells.append(cell)
                cis.append(f"{{\\scriptsize [{lo * s:.{d}f}, {hi * s:.{d}f}]}}")
            lines.append(f"{meth} & " + " & ".join(cells) + " \\\\")
            if ci_rows:
                lines.append(" & " + " & ".join(cis) + " \\\\[1pt]")
        # paired tests: reference vs others
        if ref in methods:
            fam = []
            for meth in methods:
                if meth == ref:
                    continue
                for m in metrics:
                    a = g[g.method == ref].set_index("run")[m["col"]]
                    b = g[g.method == meth].set_index("run")[m["col"]]
                    common = a.index.intersection(b.index)
                    t = paired_tests(a.loc[common].values, b.loc[common].values)
                    fam.append({"scenario": scen, "vs": meth, "metric": m["col"], **t})
            if fam:
                for key in ("t_p", "wilcoxon_p"):
                    ps = [f.get(key, np.nan) for f in fam]
                    ok = ~np.isnan(ps)
                    adj = np.full(len(ps), np.nan)
                    if ok.any():
                        adj[ok] = holm(np.asarray(ps)[ok])
                    for f, v in zip(fam, adj):
                        f[key + "_holm"] = v
                tests.extend(fam)
    n_txt = "/".join(str(n) for n in sorted(n_runs))
    lines += ["\\bottomrule", "\\end{tabular}",
              f"\\\\[2pt]{{\\scriptsize Cells: mean $\\pm$ SD over $n={n_txt}$ independent runs; "
              "brackets: 95\\% CI (Student $t$). Bold: best mean per column.}",
              "\\end{table}"]
    return "\n".join(lines) + "\n", pd.DataFrame(tests)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", default="tables")
    ap.add_argument("--metric", action="append", type=parse_metric, required=True)
    ap.add_argument("--ref", default="DCMF")
    ap.add_argument("--order", default="DCMF,m-CAC,m-Greedy,m-Myopic")
    ap.add_argument("--caption", default="Results (mean $\\pm$ SD, 95\\% CI in brackets).")
    ap.add_argument("--no-ci-rows", action="store_true")
    a = ap.parse_args()
    df = pd.read_csv(a.csv)
    for col in ("table", "scenario", "method", "run"):
        if col not in df:
            if col in ("table", "scenario"):
                df[col] = "results"
            else:
                raise SystemExit(f"missing column '{col}'")
    os.makedirs(a.out, exist_ok=True)
    for tid, g in df.groupby("table", sort=False):
        tex, tests = build(g, a.metric, a.ref, a.order.split(","), f"{a.caption}",
                           f"tab:results_{tid}", ci_rows=not a.no_ci_rows)
        with open(os.path.join(a.out, f"table_{tid}.tex"), "w") as f:
            f.write(tex)
        tests.to_csv(os.path.join(a.out, f"table_{tid}_tests.csv"), index=False)
        print(f"wrote {a.out}/table_{tid}.tex ({len(g)} rows)")


if __name__ == "__main__":
    main()
