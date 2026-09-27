# DCMF: Dynamic Context Monitoring Framework

Configuration files and experimental setup for the paper:

**"DCMF: A Dynamic Context Monitoring and Caching Framework for Context Management Platforms"**

*Submitted to IEEE Transactions on Emerging Topics in Computational Intelligence (TETCI)*

---

## 📋 Overview

This repository contains the optimal hyperparameter configurations for all methods evaluated in our study. All configurations were determined through systematic grid search on a 10,000-query validation dataset.

---

## 📂 Repository Contents
```
DCMF-Dynamic-Context-Monitoring-Framework/
├── README.md                    # This file
├── configs/
│   ├── dcmf_optimal.yaml       # DCMF (proposed method)
│   ├── mcac_optimal.yaml       # m-CAC baseline
│   ├── greedy_optimal.yaml     # m-Greedy baseline
│   └── myopic_optimal.yaml     # m-Myopic baseline
└── revision/
    ├── analysis/               # exact DST decision analysis and worked examples
    ├── tools/                  # result tables (mean ± SD, 95% CI, paired tests) and figures
    ├── templates/              # input formats for the tools
    ├── figures/                # generated figures
    └── results/                # generated CSV outputs
```

**Note:** Full source code implementation will be released upon paper acceptance.

---

## ⚙️ Experimental Setup

The 70,000-query roadwork trace is split chronologically into four disjoint segments:

| Segment | Queries | Query range | Purpose |
|---|---|---|---|
| Warm-up | 1,000 | 1–1,000 | statistics, calibration bounds, thresholds (not scored) |
| Training | 9,000 | 1,001–10,000 | initial parameter exploration; cross-validation |
| Validation | 10,000 | 10,001–20,000 | hyperparameter selection (all methods) |
| Test | 50,000 | 20,001–70,000 | final evaluation (all reported results) |

Further settings:

- **Cache size:** 500 items (all methods)
- **Tuning metric:** Composite score = 0.6×CHR + 0.3×(1-CER) + 0.1×(1/RT)

### Grid Search Scale

- **DCMF:** 1,280 configurations tested
- **m-CAC:** 625 configurations tested
- **m-Greedy:** 125 configurations tested
- **m-Myopic:** 25 configurations tested

Each configuration was run 3 times with different random seeds, and performance was averaged.

---

## 🎯 Optimal Configurations

### DCMF (Proposed Method)

**Validation Score:** 0.847

Key parameters:
- `alpha = 0.60` - PoA historical vs. real-time balance
- `beta = 0.50` - Utility vs. PoA weighting in CEE
- `lambda = 0.01` - CF decay constant (69-second half-life)
- `kappa = 1.5` - Threshold sensitivity (93rd percentile)
- `u_max_poa = 0.30` - Maximum ignorance mass for PoA
- `u_max_cf = 0.25` - Maximum ignorance mass for CF

See `configs/dcmf_optimal.yaml` for complete configuration.

### m-CAC (Baseline)

**Validation Score:** 0.712

Weighting factors (sum = 1.0):
- `w1 = 0.35` - Recency weight
- `w2 = 0.30` - Frequency weight
- `w3 = 0.20` - Context size weight
- `w4 = 0.15` - Spatial proximity weight

See `configs/mcac_optimal.yaml` for complete configuration.

### m-Greedy (Baseline)

**Validation Score:** 0.685

Key parameters:
- `window_size = 300` - Query history window (queries)
- `refresh_threshold = 0.40` - Freshness threshold for refresh
- `decay_factor = 0.85` - Access frequency decay rate

See `configs/greedy_optimal.yaml` for complete configuration.

### m-Myopic (Baseline)

**Validation Score:** 0.625

Key parameters:
- `update_interval = 45` - Periodic update interval (seconds)
- `priority_threshold = 0.50` - Minimum priority for caching

See `configs/myopic_optimal.yaml` for complete configuration.

---

## 📊 Performance Summary

Results on 50,000-query test set (from paper Section V):

| Method | CHR (%) | CER (%) | RT (ms) | CRR (%) |
|--------|---------|---------|---------|---------|
| DCMF   | 82.3    | 6.2     | 120     | 38.5    |
| m-CAC  | 67.0    | 18.5    | 185     | 55.2    |
| m-Greedy | 64.8  | 22.3    | 195     | 58.7    |
| m-Myopic | 58.2  | 28.9    | 215     | 65.3    |

- **CHR:** Cache Hit Ratio
- **CER:** Cache Expired Ratio
- **RT:** Response Time
- **CRR:** Cache Refresh Ratio

DCMF achieves **15.3 percentage points** higher cache hit ratio than m-CAC (22.9% relative improvement).

---

## 📄 Supplementary Materials

Complete mathematical derivations and extended analysis:

📎 **[Appendices A & B - Detailed DST Methodology and Parameter Analysis (PDF)](https://drive.google.com/file/d/1jjUa7KJePz4HgzGbbDLZFG-lqLZjgQPJ/view?usp=drive_link)**

Contents:
- Appendix A: Complete DST mass assignment derivations, proofs, and worked examples
- Appendix B: Extended parameter sensitivity analysis and grid search results

---

## 🔄 Reproducing Paper Results

To reproduce the results from the paper:

1. **Initialization Phase (1,000 warm-up queries):**
   - Load configuration from `configs/[method]_optimal.yaml`
   - Compute warm-up statistics (percentiles, means, variances)
   - Do not record performance metrics

2. **Evaluation Phase (50,000 test queries, 20,001–70,000):**
   - Apply optimal parameters from configuration
   - Record CHR, CER, RT, CRR metrics
   - Compare against paper Table V

3. **Expected Outputs:**
   - DCMF should achieve ~82% cache hit ratio
   - m-CAC should achieve ~67% cache hit ratio
   - Performance differences should match paper within ±2% (due to random variation)

---

## 📖 Paper Citation

If you use these configurations or methods in your research, please cite

---

## 🔬 Reproducibility Scripts

`revision/` contains scripts that recompute the analytic parts of the paper and build the result tables:

| Script | Output |
|---|---|
| `revision/analysis/dst_worked_example.py` | Worked DST example, decision trajectory (keep → refresh → evict) versus time since last update, `figures/fig_dst_decision_trajectory.pdf` |
| `revision/analysis/appendix_a_audit.py` | Exact values of every numerical example in Appendix A (`results/appendix_a_audit.csv`) |
| `revision/analysis/umax_decision_surface.py` | Sensitivity of the CMM decisions to `u_max_poa` and `u_max_cf` over the calibrated evidence space (`figures/fig_umax_decision_surface.pdf`) |
| `revision/tools/make_stats_tables.py` | LaTeX result tables with mean ± SD, 95% confidence intervals (Student t) and paired Wilcoxon / t-tests with Holm correction, from one CSV row per run |
| `revision/tools/fig11_small_multiples.py` | Overall comparison with one panel (and unit) per metric |
| `revision/tools/fig12_throughput.py` | Throughput versus load in requests per minute (TP = 60·N_c/T) |

Requirements: Python ≥ 3.9 with `numpy`, `scipy`, `pandas`, `matplotlib`.

```bash
cd revision/analysis && python3 dst_worked_example.py && python3 appendix_a_audit.py && python3 umax_decision_surface.py
python3 revision/tools/make_stats_tables.py runs.csv --out tables \
    --metric 'CHR:CHR (\%):100:1:max' --metric 'CER:CER (\%):100:1:min' --metric 'RT_ms:RT (ms):1:1:min'
```

---

## 🏗️ Framework Architecture

DCMF consists of two main components:

### 1. Context Evaluation Engine (CEE)
- Computes Probability of Access (PoA) using MAUT and AHP
- Balances historical patterns (α) with real-time queries (1-α)
- Parameters: `alpha`, `beta`

### 2. Context Management Module (CMM)
- Combines PoA and Context Freshness (CF) using Dempster-Shafer Theory
- Adaptive thresholds based on statistical analysis
- Parameters: `lambda`, `kappa`, `u_max_poa`, `u_max_cf`

See paper Section III for detailed methodology.



---

## 📝 License

This work is licensed under MIT License (code will be released upon paper acceptance).

Configuration files in this repository are released under CC BY 4.0.

---

## 🔍 Transparency Statement

**Fairness in Baseline Comparisons:**

All baseline methods (m-CAC, m-Greedy, m-Myopic) were tuned under the same protocol as DCMF:

- Identical validation segment (queries 10,001–20,000)
- Grid search over each method's parameters at a comparable per-parameter resolution (4–5 values per parameter)
- Same evaluation metrics and composite score
- Same number of runs per configuration (3 seeds)

The performance gains reported in the paper reflect genuine algorithmic improvements, not favorable hyperparameter selection for DCMF.
