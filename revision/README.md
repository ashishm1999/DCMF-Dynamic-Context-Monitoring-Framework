# Reproducibility scripts

Scripts that recompute the analytic parts of the DCMF paper (Section III-B and Appendix A) and that turn per-run logs into the result tables and figures of Section V.

## Analysis (`analysis/`)

- `dst_worked_example.py`: worked Dempster–Shafer example (PoA = 0.75) with exact values, and the decision trajectory keep → refresh → evict as the cached copy ages, for several PoA levels. It also reports the time at which each transition happens. Output: `results/dst_decision_trajectory.csv`, `results/dst_refresh_bands.csv`, `figures/fig_dst_decision_trajectory.{pdf,png}`.
- `appendix_a_audit.py`: recomputes every numerical example of Appendix A with the published equations and parameters. Output: `results/appendix_a_audit.csv` and a LaTeX table of the exact values.
- `umax_decision_surface.py`: because θ_update and θ_evict are derived from the CF distribution, the CMM decision depends only on the calibrated evidence (p(PoA), p(CF)) and on (u_max,PoA, u_max,CF). The script maps the decisions over the evidence space and measures the agreement with the selected (0.30, 0.25) for other values. Output: `results/umax_decision_surface.csv`, `figures/fig_umax_decision_surface.{pdf,png}`.

Published parameters used throughout: L_PoA = 0.15, U_PoA = 0.92, L_CF = 0.20, U_CF = 0.85, u_max,PoA = 0.30, u_max,CF = 0.25, λ = 0.01 s⁻¹, θ_update = 0.38, θ_evict = 0.11, K_high = 0.7.

## Tools (`tools/`)

- `make_stats_tables.py`: one CSV row per run (`table,scenario,method,run,<metrics…>`, see `templates/coaas_runs_template.csv`). It writes LaTeX tables with mean ± SD, 95% confidence intervals (Student t) and a CSV of paired t-test and Wilcoxon signed-rank p-values (Holm-corrected) of DCMF against each baseline.
- `fig11_small_multiples.py`: overall comparison with one panel and one unit per metric (input format: `templates/fig11_data.csv`).
- `fig12_throughput.py`: throughput versus offered load in requests per minute, TP = 60·N_c/T (use `--input-unit rps` to convert per-second logs).

## Requirements

Python ≥ 3.9, `numpy`, `scipy`, `pandas`, `matplotlib`.
