"""Sensitivity of DCMF decisions to the ignorance parameters u_max,PoA and u_max,CF.

Because theta_update / theta_evict are derived from the CF distribution
(mu_CF - kappa*sigma_CF, mu_CF - 2*kappa*sigma_CF) they do not depend on
u_max. The decision for any item is therefore a deterministic function of its
calibrated evidence (p_PoA, p_CF) and of (u_max,PoA, u_max,CF). This script
evaluates that function on a dense grid over the calibrated evidence square
[0, 1]^2 and reports, for every (u_max,PoA, u_max,CF):

* the share of the evidence space mapped to keep / refresh / evict
  (and the share refreshed by the high-conflict rule),
* the agreement with the selected configuration (0.30, 0.25),
* the mean absolute change in BetP(Cache).

Optionally the grid can be weighted by an empirical (p_PoA, p_CF) sample
(``--weights file.csv`` with columns p_poa,p_cf) instead of uniformly.
"""

import argparse
import os

import numpy as np

THETA_U, THETA_E, K_HIGH = 0.38, 0.11, 0.70
REF = (0.30, 0.25)
GRID = [0.0, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50]


def masses(p, umax):
    u = umax * 4.0 * p * (1.0 - p)
    return (1.0 - u) * p, (1.0 - u) * (1.0 - p), u


CONFLICT_RULE = "literal"   # "literal": K >= K_high always refreshes (as published); "directional": see below


def decide(pp, pc, up, uc):
    a_c, a_e, a_t = masses(pp, up)
    b_c, b_e, b_t = masses(pc, uc)
    k = a_c * b_e + a_e * b_c
    denom = np.maximum(1.0 - k, 1e-12)
    m_c = (a_c * b_c + a_c * b_t + a_t * b_c) / denom
    m_t = a_t * b_t / denom
    betp = np.where(k >= 1.0 - 1e-12, np.nan, m_c + 0.5 * m_t)
    high = k >= K_HIGH
    act = np.full(pp.shape, 0)                       # 0 keep
    act = np.where(~high & (betp < THETA_U) & (betp >= THETA_E), 1, act)   # 1 refresh
    act = np.where(~high & (betp < THETA_E), 2, act)                        # 2 evict
    # conflict policy for K >= K_high: "literal" refreshes (Eq. decision rule as published);
    # "directional" refreshes only when the CF evidence is stale (m_CF(Evict) > m_CF(Cache)), else keeps
    if CONFLICT_RULE == "literal":
        act = np.where(high, 3, act)                 # 3 refresh (conflict)
    else:
        act = np.where(high & (b_e > b_c), 3, act)   # refresh only when CF evidence is stale
        act = np.where(high & (b_e <= b_c), 0, act)  # otherwise keep
    return act, betp, k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=401)
    ap.add_argument("--weights", default=None)
    ap.add_argument("--outdir", default=os.path.join(os.path.dirname(__file__), ".."))
    ap.add_argument("--conflict-rule", choices=["literal", "directional"], default="literal")
    a = ap.parse_args()
    global CONFLICT_RULE
    CONFLICT_RULE = a.conflict_rule

    if a.weights:
        import pandas as pd
        d = pd.read_csv(a.weights)
        pp, pc = d.p_poa.values, d.p_cf.values
        w = np.ones_like(pp) / len(pp)
    else:
        g = np.linspace(0.0, 1.0, a.n)
        pp, pc = np.meshgrid(g, g, indexing="ij")
        pp, pc = pp.ravel(), pc.ravel()
        w = np.ones_like(pp) / len(pp)

    ref_act, ref_b, _ = decide(pp, pc, *REF)
    rows = []
    for up in GRID:
        for uc in GRID:
            act, b, k = decide(pp, pc, up, uc)
            agree = float(np.sum(w * (np.where(act == 3, 1, act) == np.where(ref_act == 3, 1, ref_act))))
            db = np.nanmean(np.abs(b - ref_b))
            rows.append(dict(u_poa=up, u_cf=uc,
                             keep=float(np.sum(w * (act == 0))), refresh=float(np.sum(w * (act == 1))),
                             evict=float(np.sum(w * (act == 2))), refresh_conflict=float(np.sum(w * (act == 3))),
                             agreement_with_ref=agree, mean_abs_dBetP=float(db)))
    res = os.path.join(a.outdir, "results")
    os.makedirs(res, exist_ok=True)
    import csv
    with open(os.path.join(res, "umax_decision_surface.csv"), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    for r in rows:
        if r["u_poa"] in (0.0, 0.2, 0.3, 0.4, 0.5) and r["u_cf"] in (0.0, 0.15, 0.2, 0.25, 0.3, 0.5):
            print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figdir = os.path.join(a.outdir, "figures")
    os.makedirs(figdir, exist_ok=True)

    # (a) decision map of the selected configuration, (b) agreement heat-map
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.16, 2.9))
    n = int(np.sqrt(len(pp)))
    cmap = matplotlib.colors.ListedColormap(["#f0f0f0", "#9e9e9e", "#303030", "#c9c9c9"])
    img = np.where(ref_act == 3, 3, ref_act).reshape(n, n).T
    ax1.imshow(img, origin="lower", extent=(0, 1, 0, 1), cmap=cmap, vmin=-0.5, vmax=3.5, aspect="auto")
    ax1.set_xlabel(r"calibrated PoA evidence $p(\mathrm{PoA})$", fontsize=8)
    ax1.set_ylabel(r"calibrated CF evidence $p(\mathrm{CF})$", fontsize=8)
    ax1.set_title(r"(a) decisions, $u_{max}=(0.30, 0.25)$", fontsize=8)
    from matplotlib.patches import Patch
    ax1.legend(handles=[Patch(color="#f0f0f0", label="keep"), Patch(color="#9e9e9e", label="refresh"),
                        Patch(color="#c9c9c9", label=r"refresh ($K\geq0.7$)"), Patch(color="#303030", label="evict")],
               fontsize=6, loc="upper right", frameon=True)
    ax1.tick_params(labelsize=7)

    M = np.array([[next(r["agreement_with_ref"] for r in rows if r["u_poa"] == up and r["u_cf"] == uc)
                   for uc in GRID] for up in GRID]) * 100.0
    im = ax2.imshow(M, origin="lower", cmap="Greys", vmin=M.min(), vmax=100, aspect="auto")
    ax2.set_xticks(range(len(GRID)))
    ax2.set_xticklabels([f"{v:.2f}" for v in GRID], fontsize=6)
    ax2.set_yticks(range(len(GRID)))
    ax2.set_yticklabels([f"{v:.2f}" for v in GRID], fontsize=6)
    ax2.set_xlabel(r"$u_{max,CF}$", fontsize=8)
    ax2.set_ylabel(r"$u_{max,PoA}$", fontsize=8)
    ax2.set_title("(b) decision agreement with (0.30, 0.25), %", fontsize=8)
    for i in range(len(GRID)):
        for j in range(len(GRID)):
            ax2.text(j, i, f"{M[i, j]:.0f}", ha="center", va="center", fontsize=5.5,
                     color="black" if M[i, j] < (M.min() + 100) / 2 else "white")
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(figdir, f"fig_umax_decision_surface.{ext}"), dpi=300)
    print("wrote figures/fig_umax_decision_surface.{pdf,png}")


if __name__ == "__main__":
    main()
