---
title: PAIMANA
emoji: 🏗️
colorFrom: blue
colorTo: orange
sdk: docker
app_port: 7860
pinned: false
---

# PAIMANA

**Pro-active Analytics for Infrastructure Monitoring and Assessment (National
Analytics)** - SIH 2026 problem statement SIH26103 - built on **real, public
MoSPI data**.

PAIMANA ingests the Ministry of Statistics & Programme Implementation (MoSPI)
Quarterly Progress Information System Reports (QPISR) and Flash Reports on
central-sector infrastructure projects, builds a clean project panel, trains
leak-safe overrun-prediction models, and serves a full-stack analytics
dashboard with early-warning risk scores, transparent warnings, SHAP
explainability, what-if simulation, benchmarking and a natural-language
assistant.

---

## Quick start - TWO ways to use this package

### A) Run on your laptop (recommended for demos - works offline after setup)
| OS | Steps |
|---|---|
| Windows | unzip, double-click **run_windows.bat**, open http://localhost:8000 |
| Linux/macOS | `./run.sh` |

First run installs Python packages once (needs internet); models, database and
the built frontend are all bundled - no training needed.
Tip: for a private environment that never touches your other Python projects,
run **make_venv_windows.bat** first.

### B) Deploy online (Railway / Hugging Face Spaces / Render)
The same package deploys as a Docker container:
1. Create a GitHub repo and upload the **CONTENTS of this folder** to the repo
   root - `Dockerfile`, `requirements.txt`, `start.sh`, `backend/`, `data/`
   must be at the top level (NOT inside a subfolder).
2. Railway: connect the repo (the Dockerfile is auto-detected) -> after build,
   set Memory to 2 GB (Settings -> Deploy -> Resources) and Generate Domain
   (Settings -> Networking).
3. Hugging Face Spaces (permanently free): see DEPLOY_GUIDE.md.

Full instructions: **DEPLOY_GUIDE.md** - Windows details: WINDOWS_QUICKSTART.txt

## Layout

```
backend/        FastAPI app + trained models + SQLite DB + built frontend
frontend/       React + TypeScript source (rebuild with: npm install && npm run build)
data/           canonical panel CSV (11,121 rows, 2,163 projects, 6 months) + manifest
data_pipeline/  MoSPI PDF parsers + panel builder + interim CSVs
data_source/    where to re-download the source PDFs
screenshots/    rendered page captures
Dockerfile      container definition (Railway / HF Spaces / Render)
requirements.txt  exact pinned versions the bundled models were pickled with
```

## Dataset (all public, parsed from source PDFs)

| Month | Report | Ongoing | Completed | Closed unfinished |
|---|---|---|---|---|
| Apr 2024 | Flash Report | 1,817 | 51 | 11 |
| May 2024 | Flash Report | 1,789 | 16 | 14 |
| Jun 2024 | QPISR Q1 2024-25 | 1,933 | 105 | - |
| Aug 2024 | Flash Report (census style) | 1,778 | 16 | 12 |
| Sep 2024 | Flash Report (census style) | 1,725 | 13 | - |
| Mar 2025 | QPISR Q4 2024-25 | 1,764 | 77 | - |

**Parse validation** (computed vs printed in the PDFs): cost-overrun % match
100% within 1pp (n=1,470); time-overrun 99.5% within 1 month (n=1,568);
original cost consistent across months for 95.2% of projects.

## Models (all metrics computed on the actual dataset - nothing hard-coded)

- **Leakage policy**: outcome-derived fields are never features.
- **Time-aware validation**: earlier months train, latest month tests.
- **Cost-overrun classification** - 5 candidates, calibrated: **LightGBM**
  (test ROC-AUC 0.922); strict project-disjoint validation (unseen projects):
  **AUC 0.737** - displayed honestly alongside the temporal split.
- **Magnitude regression** - **XGBoost** (cost MAE 9.1pp, delay MAE 6.6 months
  vs Huber statistical baselines 18.0 / 11.2).
- **Schedule delay** - survival analysis evaluated and honestly REJECTED
  (concordance <= 0.55 with 66 dated completions); auto-fallback to regression,
  decision surfaced in the UI.
- **Forecasting** - per-project ARIMA/ETS infeasible (<=6 observations); global
  panel model evaluated against a naive baseline and not used when it loses.
- **Anomaly detection** - Isolation Forest (60 flagged). **SHAP** explanations,
  framed as influence, not causation.

## Risk score (transparent, configurable)

`0.35*cost + 0.35*schedule + 0.20*expenditure + 0.10*reporting`, each component
a documented formula; weights editable live in the UI. Current distribution:
1,364 Low / 687 Moderate / 97 High / 15 Critical. A monitoring aid - **not** an
official government rating.

## Honesty rules implemented

Insufficient data -> explicit "Insufficient data available for this analysis."
What-if results labelled model simulation. Statistical-vs-ML winners computed
from held-out metrics. Absent variables documented as future PAIMANA
collections, never invented. Assistant answers computed from the database;
never claims official decisions.

## API

`/api/dashboard`, `/api/projects`, `/api/projects/{code}` (+`/whatif`),
`/api/model-card`, `/api/risk/methodology`, `/api/data-quality`, `/api/forecast`,
`/api/anomalies`, `/api/assistant?q=...`, `/api/filters`, `/api/meta`.
Interactive docs at `/docs`.

## Assistant (deterministic + optional Gemini)

The Assistant page answers from the database via a deterministic NLQ engine by default (zero hallucination by construction). If the `GEMINI_API_KEY` environment variable is set, answers are composed by Gemini (default `gemini-3.5-flash`) through **function calling** - the model must call PAIMANA's database tools for every fact, so it cannot invent numbers, and any failure falls back to the deterministic engine. Setup: fill in your key (from aistudio.google.com/apikey) in the `.env` file at the package root for laptop use, or set the `GEMINI_API_KEY` variable on Railway/HF for deployments - never commit a real key to the public repo. The assistant answers ONLY PAIMANA questions: off-topic questions are refused by a guard before any engine runs.
