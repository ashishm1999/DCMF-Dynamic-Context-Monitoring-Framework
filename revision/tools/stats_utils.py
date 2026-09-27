"""Summary statistics used for every reported table: mean, SD, 95% CI (Student t),
and paired significance tests across seeds."""

from __future__ import annotations

import numpy as np
from scipy import stats


def mean_sd_ci(x, conf=0.95):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n == 0:
        return np.nan, np.nan, np.nan, np.nan, 0
    m = float(x.mean())
    if n == 1:
        return m, 0.0, m, m, 1
    sd = float(x.std(ddof=1))
    h = float(stats.t.ppf(0.5 + conf / 2.0, n - 1) * sd / np.sqrt(n))
    return m, sd, m - h, m + h, n


def paired_tests(a, b):
    """Paired t-test and Wilcoxon signed-rank test (two-sided) for per-seed metrics."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    d = a - b
    out = {"mean_diff": float(d.mean()), "n": int(len(d))}
    if len(d) >= 2 and np.any(d != 0):
        out["t_p"] = float(stats.ttest_rel(a, b).pvalue)
        try:
            out["wilcoxon_p"] = float(stats.wilcoxon(a, b).pvalue)
        except ValueError:
            out["wilcoxon_p"] = np.nan
        sd = d.std(ddof=1)
        out["cohens_dz"] = float(d.mean() / sd) if sd > 0 else np.nan
    return out


def fmt_pm(m, sd, digits=1, scale=1.0):
    return f"{m * scale:.{digits}f} $\\pm$ {sd * scale:.{digits}f}"


def fmt_ci(lo, hi, digits=1, scale=1.0):
    return f"[{lo * scale:.{digits}f}, {hi * scale:.{digits}f}]"
