# PAIMANA — Research References

References supporting the methodology of PAIMANA (SIH 2026, problem
statement SIH26103), grouped by the project component they support. All
sources are real and verifiable via the DOI / URL. Data sources are primary
government publications; methods references are peer-reviewed papers or
standard textbooks.

---

## 1. Domain background — cost & time overruns in infrastructure

**Flyvbjerg, B. (2014). "What You Should Know About Megaprojects and Why: An
Overview." *Project Management Journal*, 45(2), 6–19.**
https://doi.org/10.1002/pmj.21409
→ Documents the "iron law of megaprojects" — over budget, over time, over and
over again — and global megaproject spending at 8% of world GDP. Frames why
*pro-active* monitoring (PAIMANA's premise) matters.

**Flyvbjerg, B., Skamris Holm, M., & Buhl, S. (2002). "Underestimating Costs in
Public Works Projects: Error or Lie?" *Journal of the American Planning
Association*, 68(3), 279–295.**
https://doi.org/10.1080/01944360208976273
→ Classic study of systematic cost underestimation in public works across 20
nations; motivates using anticipated-vs-original cost signals as risk features.

**Hamdan, M. M., Thneibat, M., & Hyari, K. (2025). "Predicting cost overrun in
construction projects using machine learning algorithms: the case of Jordan."
*Engineering, Construction and Architectural Management*.**
https://doi.org/10.1108/ECAM-09-2024-1209
→ Benchmarks 15 ML regression algorithms on 836 public projects (CatBoost
best, R² 0.883); supports PAIMANA's comparative, multi-candidate model
selection (LightGBM / XGBoost / CatBoost / sklearn baselines) for overrun
prediction.

**Williams, T. P., & Gong, J. (2014). "Predicting construction cost overruns
using text mining, numerical data and ensemble classifiers." *Automation in
Construction*, 43, 239–245.**
https://doi.org/10.1016/j.autcon.2014.03.013
→ Establishes ensemble classification as a valid approach for cost-overrun
prediction from archival project records — the same setting as PAIMANA's
MoSPI panel.

## 2. Data sources (primary, public)

**Ministry of Statistics and Programme Implementation (MoSPI), Government of
India.** Quarterly Progress Information System Reports (QPISR) and monthly
Flash Reports on Central Sector Infrastructure Projects (₹150 crore+):

| Month | Report | URL |
|---|---|---|
| Apr 2024 | Flash Report, April 2024 | mospi.gov.in/sites/default/files/publication_reports/FlashReport_April_2024.pdf |
| May 2024 | Flash Report, May 2024 | mospi.gov.in/sites/default/files/publication_reports/FlashReport_May_2024.pdf |
| Jun 2024 | QPISR Q1 2024-25 | mospi.gov.in/sites/default/files/publication_reports/QPISR_1st_QTR_2024-25.pdf |
| Aug 2024 | Flash Report, August 2024 | mospi.gov.in/sites/default/files/publication_reports/FlashReport_August_2024.pdf |
| Sep 2024 | Flash Report, September 2024 | mospi.gov.in/sites/default/files/publication_reports/FlashReport_September_2024.pdf |
| Mar 2025 | QPISR Q4 2024-25 | mospi.gov.in/sites/default/files/publication_reports/QPISR_4th_QTR_2024-25.pdf |

→ All PAIMANA data is parsed from these official PDFs (no synthetic data);
parse accuracy is validated against figures printed in the reports (cost-overrun
% match 100% within 1pp, time-overrun 99.5% within 1 month).

## 3. Gradient-boosting models used

**Chen, T., & Guestrin, C. (2016). "XGBoost: A Scalable Tree Boosting System."
*Proceedings of KDD '16*, 785–794.** https://doi.org/10.1145/2939672.2939785
→ Best performer for PAIMANA's cost-magnitude (MAE 9.1pp) and delay-magnitude
(MAE 6.6 months) regressions.

**Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu,
T.-Y. (2017). "LightGBM: A Highly Efficient Gradient Boosting Decision Tree."
*Advances in Neural Information Processing Systems 30 (NeurIPS 2017).**
https://papers.nips.cc/paper/6907-lightgbm-a-highly-efficient-gradient-boosting-decision-tree
→ Best performer for PAIMANA's calibrated cost-overrun classifiers (temporal
test ROC-AUC 0.922; project-disjoint AUC 0.737).

**Prokhorenkova, L., Gusev, G., Vorobev, A., Dorogush, A. V., & Gulin, A.
(2018). "CatBoost: Unbiased Boosting with Categorical Features."
*Advances in Neural Information Processing Systems 31 (NeurIPS 2018).**
https://papers.nips.cc/paper/7898-catboost-unbiased-boosting-with-categorical-features
→ One of the five candidate classifiers; principled handling of categorical
features (sector, ministry, state).

## 4. Validation methodology (leakage, time-aware splits, calibration)

**Kaufman, S., Rosset, S., & Perlich, C. (2012). "Leakage in Data Mining:
Formulation, Detection, and Avoidance." *ACM Transactions on Knowledge
Discovery from Data*, 6(4), Article 15.**
https://doi.org/10.1145/2382577.2382579
→ Formal treatment of target/information leakage. PAIMANA's leakage policy
(outcome-derived fields excluded from features) follows this work.

**Bergmeir, C., & Benítez, J. M. (2012). "On the use of cross-validation for
time series predictor evaluation." *Information Sciences*, 191, 192–213.**
https://doi.org/10.1016/j.ins.2011.12.028
→ Why naive k-fold CV is invalid for temporal data; supports PAIMANA's
time-aware validation (earlier months train, latest month tests) and the
additional project-disjoint evaluation.

**Niculescu-Mizil, A., & Caruana, R. (2005). "Predicting Good Probabilities
with Supervised Learning." *Proceedings of ICML 2005*, 625–632.**
https://doi.org/10.1145/1102351.1102430
→ Shows tree ensembles need explicit calibration for usable probabilities.
PAIMANA calibrates its classifiers (Platt scaling), since early-warning
thresholds depend on well-calibrated risk probabilities.

**Platt, J. C. (1999). "Probabilistic Outputs for Support Vector Machines and
Comparisons to Regularized Likelihood Methods." In *Advances in Large Margin
Classifiers*, MIT Press, 61–74.**
→ Original formulation of the Platt-scaling calibration used by PAIMANA.

## 5. Explainability

**Lundberg, S. M., & Lee, S.-I. (2017). "A Unified Approach to Interpreting
Model Predictions." *Advances in Neural Information Processing Systems 30
(NeurIPS 2017).** https://arxiv.org/abs/1705.07874
→ SHAP values with Shapley-value guarantees. PAIMANA reports per-project SHAP
feature attributions, framed as *influence* (not causation), in the Model
Performance page and assistant answers.

## 6. Survival analysis (evaluated, honestly rejected)

**Davidson-Pilon, B. (2019). "lifelines: survival analysis in Python."
*Journal of Open Source Software*, 4(40), 11317.**
https://doi.org/10.21105/joss.01317
→ Implementation used for PAIMANA's schedule-delay survival models.

**Harrell, F. E. (2001). *Regression Modeling Strategies: With Applications to
Linear Models, Logistic Regression, and Survival Analysis.* Springer.**
https://doi.org/10.1007/978-1-4757-3462-1
→ Source of the concordance index (C-index) used to evaluate them. With only
66 dated completions the models scored C ≤ 0.55, so PAIMANA rejects survival
analysis in favour of regression and states this decision in the UI.

## 7. Forecasting

**Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and
Practice*, 3rd edition. OTexts.** https://otexts.com/fpp3/
→ Standard reference for ARIMA/ETS, seasonal data and honest forecast
evaluation. PAIMANA's per-project ARIMA/ETS is infeasible (≤6 monthly
observations per project vs the ~12+ required), so a global panel model with
lag features is evaluated against a naive baseline instead.

**Godahewa, R., Bergmeir, C., Webb, G. I., Hyndman, R. J., & Montero-Manso,
P. (2021). "Monash Time Series Forecasting Archive." *NeurIPS 2021 Datasets
and Benchmarks Track.** https://arxiv.org/abs/2105.06643
→ Empirical support for global (cross-series) models outperforming per-series
univariate models on collections of short series — the design PAIMANA adopts
for its panel forecasting.

**Makridakis, S., Spiliotis, E., & Assimakopoulos, V. (2020). "The M4
Competition: 100,000 time series and 61 forecasting methods." *International
Journal of Forecasting*, 36(1), 54–74.**
https://doi.org/10.1016/j.ijforecast.2019.04.014
→ Benchmarking culture (always compare against simple statistical baselines)
followed by PAIMANA's statistical-vs-ML comparisons shown in the UI.

## 8. Anomaly detection

**Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). "Isolation Forest."
*Proceedings of the 8th IEEE International Conference on Data Mining (ICDM
2008)*, 413–422.** https://doi.org/10.1109/ICDM.2008.17
→ Algorithm behind PAIMANA's anomaly flagging of statistically unusual
projects (60 flagged), with reasons surfaced in the UI.

## 9. Transparent risk score

**Nardo, M., Saisana, M., Saltelli, A., Tarantola, S., Hoffman, A., &
Giovannini, E. (2008). *Handbook on Constructing Composite Indicators:
Methodology and User Guide.* OECD/JRC.**
https://doi.org/10.1787/533411815016
→ Best practices for weighted composite indicators (normalisation, weighting,
documentation). PAIMANA's implementation-risk score
(0.35 cost + 0.35 schedule + 0.20 expenditure + 0.10 reporting) follows these
principles, with live-editable weights and full formula transparency.

## 10. Robust statistical baselines

**Huber, P. J. (1964). "Robust Estimation of a Location Parameter." *Annals
of Mathematical Statistics*, 35(1), 73–101.**
https://doi.org/10.1214/aoms/1177703732
→ Huber regression, the robust statistical baseline PAIMANA's ML regressions
are compared against (cost MAE 18.0pp / delay 11.2 months vs XGBoost's
9.1pp / 6.6 months).

---

## Suggested one-line attributions (for slides)

- Overrun prediction: "Gradient-boosted trees are the state of the art for
  construction cost-overrun prediction [Hamdan et al. 2025; Chen & Guestrin
  2016; Ke et al. 2017]."
- Validation: "We use time-aware validation and leakage controls following
  Kaufman et al. (2012) and Bergmeir & Benítez (2012)."
- Explainability: "Feature attributions use SHAP [Lundberg & Lee 2017],
  presented as influence, not causation."
- Risk score: "The composite risk index follows OECD/JRC composite-indicator
  methodology [Nardo et al. 2008]."
