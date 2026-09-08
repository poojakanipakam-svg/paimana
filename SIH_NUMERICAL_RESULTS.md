# PAIMANA — Numerical Results, Accuracy & Impact

All figures are computed on held-out data and the live database — nothing is
hard-coded. Basis: 6 MoSPI reports (Apr 2024 – Mar 2025), 11,121 project-month
records, 2,163 unique projects; model metrics from the time-aware test split
(earlier months train, Mar 2025 tests). Portfolio figures: ongoing projects in
the latest month (Mar 2025, n = 1,773).

---

## 1. ACCURACY — model performance

### Cost-overrun classification (approval stage) — LightGBM, calibrated

| Metric | Value |
|---|---|
| **ROC-AUC** | **0.922** |
| PR-AUC | 0.887 |
| Recall (sensitivity) | 92.1% |
| Precision | 43.1% |
| Accuracy | 67.3% |
| F1 | 0.587 |
| Brier score (calibration) | 0.064 |

**Strictest test — 497 completely unseen projects** (project-disjoint split):
ROC-AUC **0.737**, accuracy 67.1%, recall 65.3%, precision 40.3%.

### Schedule-risk classification (monitoring stage) — LightGBM, calibrated

| Metric | Value |
|---|---|
| ROC-AUC | 0.917 |
| PR-AUC | 0.855 |
| **Recall** | **96.4%** |
| Accuracy | 48.9% |
| Brier score | 0.089 |

The monitoring model's threshold is deliberately tuned for **recall priority**
(early warning: missing a risky project is worse than a false alarm). Accuracy
is a weak headline metric here because the outcome classes are imbalanced —
AUC and recall are the appropriate measures.

### Overrun magnitude regression — XGBoost vs statistical baseline

| Task | ML (XGBoost) | Huber baseline | Improvement |
|---|---|---|---|
| Cost overrun (% points) | **MAE 9.1** | MAE 18.0 | **49.6% lower error** |
| Delay (months) | **MAE 6.6** | MAE 11.2 | **41.1% lower error** |

Cost regression R² 0.814 · RMSE 51.5pp; delay regression R² 0.849 · RMSE 11.4
months. All winners (statistical vs ML) are selected on held-out metrics and
the comparison is shown in the UI.

### Honest rejections (shown in the UI, not hidden)

- **Survival analysis for delay: REJECTED** — cross-validated concordance ≤ 0.55
  (no better than chance) with only 66 dated completions; regression used
  instead, decision surfaced in the Model Performance page.
- **Per-project ARIMA/ETS forecasting: INFEASIBLE** — max 6 monthly observations
  per project vs the 12+ required; a global panel model with lag features is
  evaluated against a naive baseline and used only where it wins.

### Data-engineering accuracy (parse validation vs figures printed in the PDFs)

| Check | Accuracy |
|---|---|
| Cost-overrun % match (±1pp) | **100.0%** (n = 1,470) |
| Time-overrun match (±1 month) | **99.5%** (n = 1,568) |
| Original-cost consistency across months | 95.2% |

---

## 2. NUMERICAL RESULTS — dataset & system

| Measure | Value |
|---|---|
| Project-month records | 11,121 |
| Unique projects | 2,163 |
| Report months | 6 (Apr 2024 – Mar 2025) |
| Sectors / ministries / states | 30 / 22 / 71 |
| End-to-end pipeline | MoSPI PDF → parser → panel → models → API → dashboard |
| API endpoints | 13 (+ interactive /docs) |
| Warnings generated (transparent, rule-based) | 2,611 |
| Anomalies flagged (Isolation Forest) | 60 |

---

## 3. IMPACT — quantified on the March 2025 snapshot (1,773 ongoing projects)

| Impact measure | Value |
|---|---|
| Portfolio under watch (original cost) | ₹26.89 lakh crore |
| Anticipated cost | ₹32.24 lakh crore |
| Aggregate cost overrun detected | **₹5.36 lakh crore (+19.9%)** |
| Delayed projects | 915 (51.6%), average delay 31.8 months |
| Projects with cost overrun | 464 (26.2%) |
| **High + Critical risk flagged** | **86 projects worth ₹5.53 lakh crore** |
| ML early-warning flags (P > 0.5) | 110 projects |
| Value of a 1pp cut in the aggregate overrun | ≈ ₹5,358 crore |

**Impact narrative (honest framing):** PAIMANA converts MoSPI's static monthly
PDFs into a live early-warning system — prioritising ₹5.53 lakh crore of
high-risk projects for monitoring attention out of a ₹32 lakh crore portfolio,
with explainable reasons (SHAP influence, documented warnings) for every flag.
Even a single percentage-point reduction in the aggregate overrun it surfaces
corresponds to ≈ ₹5,358 crore of public funds. The risk score is a monitoring
aid with fully documented formulas and editable weights — not an official
government rating.

---

## 4. Suggested slide soundbites

- "Cost-overrun classifier: ROC-AUC 0.92, recall 92% — and still 0.74 AUC on
  497 projects the model has never seen."
- "Our ML models cut overrun-magnitude error by 41–50% versus robust
  statistical baselines (MAE 9.1pp and 6.6 months)."
- "100% parse accuracy on cost overruns, validated against figures printed in
  the source reports."
- "₹5.36 lakh crore of overrun surfaced, ₹5.53 lakh crore of high-risk
  projects flagged for priority action."
- "Where the data is insufficient, the system says so — survival analysis and
  per-project forecasting were evaluated and honestly rejected."
