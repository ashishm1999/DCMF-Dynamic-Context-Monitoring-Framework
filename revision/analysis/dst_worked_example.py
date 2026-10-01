"""Exact recomputation of the DCMF Dempster-Shafer worked example.

Reproduces Appendix A.6 (PoA = 0.75, dt = 120 s) and then sweeps the time
since last update to show where the decision rule

    BetP(Cache) >= theta_update                 -> keep
    theta_evict <= BetP(Cache) < theta_update   -> refresh
    BetP(Cache) <  theta_evict                  -> evict
    K >= K_high                                 -> refresh (conflict policy, as published)
    (--conflict-rule directional: refresh only if m_CF(Evict) > m_CF(Cache), else keep)

moves an item from keep to refresh to evict. Everything here is closed-form
arithmetic on the published equations and parameter values; no simulation.

Usage:  python dst_worked_example.py  [--outdir ../results]
"""

import argparse
import csv
import math
import os

# Published configuration (configs/dcmf_optimal.yaml, Appendix A.6)
LAMBDA = 0.01
L_POA, U_POA = 0.15, 0.92
L_CF, U_CF = 0.20, 0.85
UMAX_POA, UMAX_CF = 0.30, 0.25
THETA_UPDATE, THETA_EVICT = 0.38, 0.11
K_HIGH = 0.70
# Conflict policy for K >= K_HIGH. "literal": always refresh (Algorithm CMM as published);
# "directional": refresh only when the conflict stems from stale CF evidence, otherwise keep.
CONFLICT_RULE = "literal"


def calibrate(x, lo, hi):
    return min(1.0, max(0.0, (x - lo) / (hi - lo)))


def masses(x, lo, hi, umax):
    p = calibrate(x, lo, hi)
    u = umax * 4.0 * p * (1.0 - p)
    return {"C": (1.0 - u) * p, "E": (1.0 - u) * (1.0 - p), "T": u, "p": p, "u": u}


def combine(m1, m2):
    k = m1["C"] * m2["E"] + m1["E"] * m2["C"]
    if k >= 1.0 - 1e-12:
        return {"C": float("nan"), "E": float("nan"), "T": float("nan"), "K": 1.0}
    n = 1.0 - k
    c = (m1["C"] * m2["C"] + m1["C"] * m2["T"] + m1["T"] * m2["C"]) / n
    e = (m1["E"] * m2["E"] + m1["E"] * m2["T"] + m1["T"] * m2["E"]) / n
    t = (m1["T"] * m2["T"]) / n
    return {"C": c, "E": e, "T": t, "K": k}


def decide(poa, dt, theta_u=THETA_UPDATE, theta_e=THETA_EVICT, lam=LAMBDA):
    cf = math.exp(-lam * dt)
    mp = masses(poa, L_POA, U_POA, UMAX_POA)
    mc = masses(cf, L_CF, U_CF, UMAX_CF)
    comb = combine(mp, mc)
    k = comb["K"]
    if k >= K_HIGH:
        betp = float("nan") if k >= 1.0 else comb["C"] + comb["T"] / 2.0
        if CONFLICT_RULE == "literal" or mc["E"] > mc["C"]:
            action = "refresh (high conflict)"
        else:
            action = "keep (high conflict)"
    else:
        betp = comb["C"] + comb["T"] / 2.0
        if betp >= theta_u:
            action = "keep"
        elif betp >= theta_e:
            action = "refresh"
        else:
            action = "evict"
    return {"poa": poa, "dt": dt, "cf": cf, "mp": mp, "mc": mc, "comb": comb,
            "K": k, "betp": betp, "action": action}


def bisect_dt(poa, target, lo=0.0, hi=400.0):
    """Smallest dt at which BetP(Cache) drops below target (BetP decreases in dt)."""
    f = lambda d: decide(poa, d)["betp"] - target
    if f(lo) < 0:
        return lo
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        v = f(mid)
        if math.isnan(v) or v < 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def print_steps(r, title):
    mp, mc, cb = r["mp"], r["mc"], r["comb"]
    print(f"\n=== {title} ===")
    print(f"PoA = {r['poa']:.2f}, dt = {r['dt']:.0f} s, CF = exp(-{LAMBDA}*{r['dt']:.0f}) = {r['cf']:.4f}")
    print(f"p(PoA) = {mp['p']:.4f}, u(PoA) = {mp['u']:.4f}, m_PoA = (C {mp['C']:.4f}, E {mp['E']:.4f}, Theta {mp['T']:.4f})")
    print(f"p(CF)  = {mc['p']:.4f}, u(CF)  = {mc['u']:.4f}, m_CF  = (C {mc['C']:.4f}, E {mc['E']:.4f}, Theta {mc['T']:.4f})")
    print(f"K = {cb['K']:.4f}; combined = (C {cb['C']:.4f}, E {cb['E']:.4f}, Theta {cb['T']:.4f})")
    print(f"BetP(Cache) = {r['betp']:.4f}, BetP(Evict) = {1 - r['betp']:.4f} -> {r['action']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=os.path.join(os.path.dirname(__file__), "..", "results"))
    ap.add_argument("--conflict-rule", choices=["literal", "directional"], default="literal")
    args = ap.parse_args()
    global CONFLICT_RULE
    CONFLICT_RULE = args.conflict_rule
    os.makedirs(args.outdir, exist_ok=True)

    orig = decide(0.75, 120)
    print_steps(orig, "Original example (Appendix A.6): dt = 120 s")
    fixed = decide(0.75, 135)
    print_steps(fixed, "Corrected example: dt = 135 s")

    t_ref = bisect_dt(0.75, THETA_UPDATE)
    t_evi = bisect_dt(0.75, THETA_EVICT)
    t_cfl = math.log(1.0 / L_CF) / LAMBDA
    print(f"\nPoA = 0.75: keep for dt < {t_ref:.1f} s, refresh for {t_ref:.1f} <= dt < {t_evi:.1f} s, "
          f"evict for dt >= {t_evi:.1f} s (CF reaches L_CF = {L_CF} at dt = {t_cfl:.1f} s)")

    rows = []
    for poa in (0.50, 0.65, 0.75, 0.85, 0.95):
        for dt in (0, 30, 60, 90, 100, 110, 120, 125, 130, 135, 140, 150, 160, 180, 240, 300):
            r = decide(poa, dt)
            rows.append({
                "PoA": poa, "dt_s": dt, "CF": round(r["cf"], 4),
                "m_PoA_C": round(r["mp"]["C"], 4), "m_PoA_E": round(r["mp"]["E"], 4), "m_PoA_T": round(r["mp"]["T"], 4),
                "m_CF_C": round(r["mc"]["C"], 4), "m_CF_E": round(r["mc"]["E"], 4), "m_CF_T": round(r["mc"]["T"], 4),
                "K": round(r["K"], 4), "BetP_Cache": round(r["betp"], 4) if not math.isnan(r["betp"]) else "",
                "action": r["action"],
            })
    path = os.path.join(args.outdir, "dst_decision_trajectory.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {path}")

    bands = []
    for poa in (0.50, 0.65, 0.75, 0.85, 0.95):
        seq = []
        dt = 0.0
        while dt <= 400.0:
            act = decide(poa, dt)["action"]
            if not seq or seq[-1][1] != act:
                seq.append((dt, act))
            dt = round(dt + 0.1, 1)
        desc = "; ".join(f"{a} from {t:.1f} s" for t, a in seq)
        print(f"PoA {poa:.2f}: {desc}")
        bands.append({"PoA": poa, "transitions": desc})
    with open(os.path.join(args.outdir, "dst_refresh_bands.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(bands[0].keys()))
        w.writeheader()
        w.writerows(bands)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        figdir = os.path.join(os.path.dirname(__file__), "..", "figures")
        os.makedirs(figdir, exist_ok=True)
        fig, (ax, axk) = plt.subplots(2, 1, figsize=(3.5, 3.9), sharex=True,
                                      gridspec_kw={"height_ratios": [2.2, 1.0]})
        ts = [i * 0.5 for i in range(0, 481)]
        for poa, ls in ((0.50, ":"), (0.75, "-"), (0.85, "--")):
            rs = [decide(poa, t) for t in ts]
            ys = [r["betp"] for r in rs]
            ks = [r["K"] for r in rs]
            ax.plot(ts, ys, ls, color="black", lw=1.1, label=f"PoA = {poa:.2f}")
            hc = [(t, y) for t, y, r in zip(ts, ys, rs) if r["K"] >= K_HIGH]
            if hc:
                ax.plot([t for t, _ in hc], [y for _, y in hc], ls, color="0.6", lw=3.0, alpha=0.6)
            axk.plot(ts, ks, ls, color="black", lw=1.1)
        ax.axhspan(THETA_UPDATE, 1.0, color="0.94", zorder=0)
        ax.axhspan(THETA_EVICT, THETA_UPDATE, color="0.82", zorder=0)
        ax.axhline(THETA_UPDATE, color="0.3", lw=0.6)
        ax.axhline(THETA_EVICT, color="0.3", lw=0.6)
        ax.text(236, THETA_UPDATE + 0.02, "keep", fontsize=7, ha="right")
        ax.text(236, (THETA_UPDATE + THETA_EVICT) / 2, "refresh", fontsize=7, ha="right", va="center")
        ax.text(236, THETA_EVICT - 0.05, "evict", fontsize=7, ha="right")
        ax.text(3, THETA_UPDATE + 0.015, r"$\theta_{update}=0.38$", fontsize=6)
        ax.text(3, THETA_EVICT + 0.015, r"$\theta_{evict}=0.11$", fontsize=6)
        for a in (ax, axk):
            a.axvline(135, color="0.3", lw=0.6, ls="-.")
        ax.annotate("corrected example\n" + r"($\Delta t$=135 s)", xy=(135, 0.274), xytext=(170, 0.62),
                    fontsize=6, arrowprops=dict(arrowstyle="->", lw=0.6))
        ax.set_xlim(0, 240)
        ax.set_ylim(0, 1)
        ax.set_ylabel("BetP(Cache)", fontsize=8)
        from matplotlib.lines import Line2D
        h, l = ax.get_legend_handles_labels()
        h.append(Line2D([0], [0], color="0.6", lw=3.0, alpha=0.6))
        l.append(r"$K \geq K_{high}$: refresh")
        ax.legend(h, l, fontsize=6.2, loc="lower center", frameon=False, bbox_to_anchor=(0.5, 1.0),
                  ncol=2, columnspacing=1.0, handlelength=2.2)
        axk.axhline(K_HIGH, color="0.3", lw=0.6)
        axk.text(3, K_HIGH + 0.03, r"$K_{high}=0.7$ (conflict policy: refresh)", fontsize=6)
        axk.set_ylim(0, 1)
        axk.set_ylabel("Conflict $K$", fontsize=8)
        axk.set_xlabel(r"Time since last update, $\Delta t$ (s)", fontsize=8)
        for a in (ax, axk):
            a.tick_params(labelsize=7)
        fig.tight_layout()
        for ext in ("pdf", "png"):
            fig.savefig(os.path.join(figdir, f"fig_dst_decision_trajectory.{ext}"), dpi=300)
        print("wrote figures/fig_dst_decision_trajectory.{pdf,png}")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
