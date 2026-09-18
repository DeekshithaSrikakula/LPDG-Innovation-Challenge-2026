# LPDG Innovation Hub Selection Challenge 2026 - Software Development

Production-ready service for identifying and ranking smart meter gateways requiring operational field visits.

> 🎥 **Demonstration Screen Recording:** [Click here to watch the 6–8 minute walkthrough](https://drive.google.com/file/d/1ULQ1VtybiqGk240grDYlGRacfi1vHlDL/view?usp=drive_link)

---

## 1. Project Overview

This repository contains the completed submission for the **LPDG Innovation Hub Selection Challenge 2026**, specializing in the **Software Development (Track B)** discipline.

LPDG operates a wide-area radio telemetry network carrying meter readings across approximately 320 gateways installed in basements, rooftops, and utility plant rooms. When a gateway begins to degrade or fail, meters behind it stop transmitting readings. The operational field engineering team can dispatch up to **15 physical site visits per week**.

This solution wraps the official anomaly ranking logic in a clean, robust, and extensible software architecture:
- Pluggable ranking abstraction separating algorithm logic from the service layer.
- FastAPI REST service providing weekly rankings, detailed individual gateway diagnostics, and on-demand prediction execution.
- Comprehensive automated test suite spanning unit tests, API contracts, input validation, bug regression, and end-to-end (E2E) integration.
- Full OpenAPI / Swagger documentation accessible at `/docs`.

---

## 2. Problem Statement

Operations teams cannot afford unguided manual triage or gut-feel scheduling:
- An unnecessary site visit costs **€380**.
- An unvisited failed gateway leaves hundreds of customer meters unread, leading to billing errors, estimated billing, and manual readout costs.
- Gateways operate under varying conditions; seasonal variances, cellular network re-registrations, and power fluctuations must be distinguished from true hardware degradation.

The challenge mandates:
1. Producing an auditable `predictions.csv` with exactly 15 prioritized gateways for each of the 8 scored weeks from **2 February 2026 to 23 March 2026** (120 rows total).
2. Providing a decoupled, maintainable Web API that another developer can pick up and extend.
3. Enabling seamless swapping of ranking strategies without rewriting API routes.
4. Handling edge cases, invalid user inputs, missing data, and unregistered gateways gracefully.

> **Evaluation Scope vs. API Implementation Choice:**
> Producing predictions strictly for the 8 official scored weeks (120 rows) is mandatory for `predictions.csv` to satisfy the challenge evaluation validator. In contrast, limiting the API to those 8 weeks was an initial implementation choice to match challenge boundaries; the underlying ranking engine is mathematically date-agnostic, and the API has been designed to accept any valid Monday (computing dynamic rankings when telemetry is present, or serving baseline rankings in offline mode).

---

## 3. Software Development Approach

To deliver professional engineering quality, the codebase follows key architectural principles:
- **Clean Architecture & Separation of Concerns:** Data ingestion, anomaly mathematics, API endpoints, and test suites are decoupled into distinct layers (`data` → `ranking engine` → `API service` → `test suite`).
- **Strategy Design Pattern:** The `RankingEngine` relies on a `RankingStrategy` protocol. The default `ThreeSigmaStrategy` executes the official baseline, while custom algorithms (e.g. Machine Learning, heuristics, cost-weighted rankers) can be injected with zero changes to API routes.
- **Fail-Safe Error Handling:** No internal Python stack traces leak to callers. All HTTP responses are structured, consistent, and use standard HTTP status codes (`400 Bad Request`, `404 Not Found`, `422 Unprocessable Content`, `500 Internal Server Error`).
- **Observability & Diagnostics:** The explanation endpoint evaluates full network distributions, correctly diagnosing both high-priority breach gateways (top 15) and sub-threshold/normal gateways outside the top 15.

---

## 4. Architecture

```
                       ┌─────────────────────────────────────┐
                       │           Telemetry Data            │
                       │    (Parquet / Local data/ folder)   │
                       └──────────────────┬──────────────────┘
                                          │
                                          ▼
                       ┌─────────────────────────────────────┐
                       │          Ranking Strategy           │
                       │   (ThreeSigmaStrategy / Custom)     │
                       └──────────────────┬──────────────────┘
                                          │
                                          ▼
                       ┌─────────────────────────────────────┐
                       │          Ranking Engine             │
                       │     (src/ranking/engine.py)         │
                       └──────────────────┬──────────────────┘
                                          │
                                          ▼
                       ┌─────────────────────────────────────┐
                       │            FastAPI App              │
                       │         (src/api/main.py)           │
                       └──────────────────┬──────────────────┘
                                          │
               ┌──────────────────────────┼──────────────────────────┐
               ▼                          ▼                          ▼
      GET /health           GET /weeks/{date}/rankings    GET /gateways/{id}/explanation
                                          │
                                          ▼
                                      POST /run
```

---

## 5. Baseline Explanation

The default ranking strategy strictly implements the official `baseline_3sigma.py` specification:
1. **Trailing 28-Day Baseline:** Before each scored Monday, extracts the preceding 28 days of hourly telemetry for each gateway.
2. **Gateway-Specific Normalization:** Calculates the mean $\mu$ and standard deviation $\sigma$ per gateway for three key telemetry metrics:
   - `offline_duration_sec`
   - `disconnection_cnt`
   - `reboot_cnt`
3. **3-Sigma Anomaly Flagging:** Evaluates the trailing 7 days. Flags any hour where a metric exceeds $\mu + 3\sigma$.
4. **Ranking & Prioritization:** Gateways are sorted descending by total flagged hours. The top 15 gateways form the visit list for that week.

---

## 6. Project Structure

```
LPDG-Innovation-Challenge-2026/
├── .gitignore                     # Git exclusion rules (data/, .venv/, etc.)
├── requirements.txt               # Pinned Python package dependencies
├── app.py                         # Streamlit interactive web dashboard
├── baseline_3sigma.py             # Official 3-sigma anomaly baseline logic
├── validate_submission.py         # Official validator checking predictions schema
├── predictions.csv                # Validated 120-row submission predictions
├── 23091A32J0.pdf                # Candidate CV (<Registration_Id>.pdf)
├── DECISIONS.md                   # Architectural & engineering decisions log
├── AI-USAGE.md                    # Transparent record of AI tool assistance
├── README.md                      # Complete system documentation
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py                # FastAPI endpoints, models, & error handlers
│   └── ranking/
│       ├── __init__.py
│       └── engine.py              # RankingEngine abstraction & Strategy protocol
└── tests/
    ├── __init__.py
    ├── conftest.py                # Pytest fixtures & synthetic telemetry generator
    ├── test_ranking_engine.py     # Unit tests for ranking engine & strategies
    ├── test_validation.py         # Tests for invalid dates, weeks, and gateways
    ├── test_api.py                # FastAPI route integration & status code tests
    ├── test_regression.py         # Regression test for gateway explanation bug
    └── test_e2e.py                # Whole-system E2E integration test
```

---

## 7. Setup Instructions

### Prerequisites
- Python 3.10 to 3.13 installed
- Git installed

### 1. Clone the Repository
```bash
git clone https://github.com/DeekshithaSrikakula/LPDG-Innovation-Challenge-2026.git
cd LPDG-Innovation-Challenge-2026
```

### 2. Create and Activate Virtual Environment
On Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 8. Data Placement Note

> **CRITICAL SECURITY NOTE:**
> Challenge data is proprietary and **MUST NEVER** be committed or pushed to Git.
> Both `data/` and `.venv/` are strictly ignored by `.gitignore`.

Place the local challenge data directly in the root directory under `data/`:

```
data/
├── telemetry/
│   ├── month=2025-08/*.parquet
│   ├── month=2025-09/*.parquet
│   ├── month=2025-10/*.parquet
│   ├── month=2025-11/*.parquet
│   ├── month=2025-12/*.parquet
│   ├── month=2026-01/*.parquet
│   ├── month=2026-02/*.parquet
│   └── month=2026-03/*.parquet
├── engineer_review_2026-02.xlsx
├── field_visits.csv
├── gateway_master.csv
├── meter_read_success.csv
└── telemetry_sample_2025-08.csv
```

---

## 9. Running Predictions & Validation

### Generate Predictions
To compute rankings across all 8 scored weeks and generate `predictions.csv`:
```bash
python baseline_3sigma.py --data data --out predictions.csv
```

### Validate Submission
To verify formatting, schema, row counts, and date adherence:
```bash
python validate_submission.py predictions.csv
```
Expected output:
```
predictions.csv: OK
  15 ranked gateways for each of 8 weeks, 2026-02-02 to 2026-03-23
```

---

## 10. Running the API

Start the FastAPI application with Uvicorn:

```bash
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

The interactive Swagger documentation is available at:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---


---

## 11. Running the Streamlit Dashboard

In addition to the FastAPI REST endpoints and Swagger UI, the project includes an interactive web dashboard built with Streamlit:

### How to Run:
Ensure the FastAPI backend is running first:
```powershell
uvicorn src.api.main:app --reload
```
In a second terminal, start the Streamlit dashboard:
```powershell
streamlit run app.py
```
Open your browser to:
- **Dashboard URL:** [http://localhost:8501](http://localhost:8501)

### System Workflow:
`User → Streamlit Dashboard → FastAPI → RankingEngine → Telemetry Data`

The dashboard strictly acts as an HTTP client to the FastAPI backend and does **not** duplicate any ranking calculations.

### Dashboard Capabilities:
- **Real-time API Connection Status:** Continuously pings `GET /health` and provides immediate troubleshooting instructions if the backend service is offline.
- **Scored Week Selector:** Intuitive dropdown for all eight scored deployment Mondays (2026-02-02 to 2026-03-23).
- **Summary Metrics Row:** Displays total ranked gateways (15 fixed capacity), selected deployment week, and API connectivity status.
- **Interactive Rankings Table:** Shows Rank (1–15), Gateway ID, Anomaly Score (flagged breach hours), and Diagnostic Audit Reason.
- **Gateway Diagnosis & Explanation:** Query any gateway in the top 15 or input a custom Gateway ID to inspect full anomaly audit rationale and visit recommendation status via `GET /gateways/{gateway_id}/explanation`.
- **On-Demand Recalculation:** Trigger calculation via `POST /run` directly from the dashboard.

## 12. API Endpoints & Examples

### 1. Health Check
`GET /health`
```bash
curl -X GET "http://127.0.0.1:8000/health"
```
**Response (200 OK):**
```json
{
  "status": "ok",
  "service": "LPDG Gateway Ranking API",
  "version": "1.0.0",
  "data_ready": true
}
```

### 2. Get Weekly Top 15 Rankings
`GET /weeks/{week_start}/rankings`
```bash
curl -X GET "http://127.0.0.1:8000/weeks/2026-02-02/rankings"
```
**Response (200 OK):**
```json
{
  "week_start": "2026-02-02",
  "gateways": [
    {
      "rank": 1,
      "gateway_id": "0A2778A31BE3",
      "score": 43.0,
      "reason": "43 hour(s) beyond 3 sigma of this gateway's own 28-day baseline in the last 7 days; first breach on disconnection_cnt"
    },
    {
      "rank": 2,
      "gateway_id": "0E1B6F4DBA34",
      "score": 26.0,
      "reason": "26 hour(s) beyond 3 sigma of this gateway's own 28-day baseline in the last 7 days; first breach on offline_duration_sec"
    }
  ]
}
```

### 3. Explain Gateway Ranking
`GET /gateways/{gateway_id}/explanation?week_start=2026-02-02`
```bash
curl -X GET "http://127.0.0.1:8000/gateways/0A2778A31BE3/explanation?week_start=2026-02-02"
```
**Response (200 OK):**
```json
{
  "week_start": "2026-02-02",
  "gateway_id": "0A2778A31BE3",
  "rank": 1,
  "score": 43.0,
  "reason": "43 hour(s) beyond 3 sigma of this gateway's own 28-day baseline in the last 7 days; first breach on disconnection_cnt",
  "in_top_15": true
}
```

### 4. Trigger Ranking Execution
`POST /run`
- Rerun a single week:
```bash
curl -X POST "http://127.0.0.1:8000/run"      -H "Content-Type: application/json"      -d '{"week_start": "2026-02-02"}'
```
- Rerun all 8 scored weeks and refresh `predictions.csv`:
```bash
curl -X POST "http://127.0.0.1:8000/run"      -H "Content-Type: application/json"      -d '{}'
```
**Response (200 OK):**
```json
{
  "status": "completed",
  "message": "Ranking completed and predictions.csv updated for all scored weeks.",
  "weeks": 8,
  "rows": 120,
  "output_file": "predictions.csv"
}
```

---

## 13. Error Handling

The API maps exceptions to appropriate HTTP status codes:
- **`400 Bad Request`**: Invalid date formats (e.g. `2026-99-99`) or non-scored weeks (e.g. `2025-08-04`).
- **`404 Not Found`**: Nonexistent gateway ID requested for explanation.
- **`422 Unprocessable Content`**: Missing mandatory query parameters (e.g. missing `week_start`) or malformed JSON payloads.
- **`500 Internal Server Error`**: Data directory missing or file read failures. Tracebacks are suppressed and returned as clean JSON details.

---

## 14. Automated Testing

The automated test suite contains 20 comprehensive tests:
```bash
pytest -q
```
Test categories include:
1. **Unit Tests (`tests/test_ranking_engine.py`):** Ensures exactly 15 gateways returned, 1–15 rank ordering, schema integrity, and strategy swap mechanics.
2. **Validation Tests (`tests/test_validation.py`):** Tests handling of malformed dates, out-of-scope weeks, and invalid gateway IDs.
3. **API Tests (`tests/test_api.py`):** End-to-end route tests using FastAPI `TestClient` covering all endpoints, query parameters, POST requests, and 500 data failure handling.
4. **Regression Test (`tests/test_regression.py`):** Reproduces and verifies the fix for the gateway explanation bug where gateways outside top 15 previously returned 404.
5. **Whole-System E2E Test (`tests/test_e2e.py`):** Exercises the complete stack (`Client → FastAPI → RankingEngine → Parquet on Disk → Response`) with zero mocking.

---

## 15. How to Replace the Ranking Strategy

To introduce a new ranking algorithm (e.g. ML, multi-criteria optimization, cost-weighted ranker):
1. Implement a class adhering to the `RankingStrategy` protocol in `src/ranking/engine.py`:
```python
import datetime as dt
import pandas as pd

class CustomMLStrategy:
    def rank_week(self, frame: pd.DataFrame, monday: dt.date) -> pd.DataFrame:
        # Custom ranking calculation
        ...
        return ranked_df  # DataFrame with gateway_id, flagged_hours, worst_metric

    def build_predictions(self, frame: pd.DataFrame) -> pd.DataFrame:
        # Full 8-week predictions calculation
        ...
        return predictions_df
```
2. Inject it into the `RankingEngine`:
```python
custom_engine = RankingEngine(data_dir=DATA_DIR, strategy=CustomMLStrategy())
```
No changes to `src/api/main.py` are required.

---

## 16. Limitations & What the System Cannot Do

1. **Intentionally Simple Anomaly Baseline:** The 3-sigma rule is a statistical anomaly detector, not a predictive machine learning model. It identifies gateways that *have already breached statistical norms*, rather than anticipating failures before symptoms occur.
2. **Fixed 28-Day Rolling Window:** Does not account for longer-term seasonal patterns (e.g., severe winter storms or seasonal radio propagation shifts).
3. **No Automatic Metric Weighting:** Treats an hour with high disconnection count identically to an hour with prolonged offline duration, despite offline duration often carrying higher customer billing impact.
4. **What Two Additional Weeks Would Provide:**
   - Incorporating meter reading success rates from `meter_read_success.csv` to weight anomalies by actual customer impact.
   - Correlating engineer visit outcomes from `field_visits.csv` to label true positive failures versus transient network flukes.
   - Deploying a supervised classification model (e.g. LightGBM / XGBoost) trained to minimize total dispatch cost (€380 per visit).

---

## 17. Demo Walkthrough Instructions

For a 6 to 8 minute demonstration video:
1. **Repository Tour (1 min):** Highlight clean repository structure, `.gitignore` compliance, and verified `predictions.csv`.
2. **Data & Architecture (1.5 min):** Explain the separation between data ingestion, `RankingEngine`, and the FastAPI service.
3. **FastAPI & Streamlit Walkthrough (3 min):**
   - Open Swagger UI (`http://127.0.0.1:8000/docs`) and verify `GET /health`.
   - Launch Streamlit dashboard (`streamlit run app.py` at `http://localhost:8501`).
   - Select a scored week (e.g. `2026-02-02`) and click **Load Rankings** to inspect the 15 gateways.
   - Run **Explain Gateway** for a top-ranked gateway and for a gateway outside the top 15.
   - Highlight the architecture flow: `User → Streamlit Dashboard → FastAPI → RankingEngine → Telemetry Data`.
4. **Test Suite & Validator (1.5 min):** Run `pytest -q` showing all 20 tests passing and run `python validate_submission.py predictions.csv`.

---

## 18. Demonstration Screen Recording

The 6–8 minute demonstration walkthrough video covers:
1. **Architecture Tour:** Clean separation between telemetry ingestion, `RankingEngine`, FastAPI service layer, and Streamlit operations dashboard.
2. **FastAPI & Swagger Walkthrough:** Live inspection of `/health`, `/weeks/{week_start}/rankings`, `/gateways/{gateway_id}/explanation`, and `/run`.
3. **Streamlit Operations Console:** Walkthrough of the `2026-02-23` scored week, 4 KPI cards, 15-gateway priority table, and individual gateway diagnostic audit.
4. **Verification & Tests:** Running `pytest -q` (all 20 tests passing) and `validate_submission.py predictions.csv` (OK).

- **Screen Recording URL:** [Watch Walkthrough Video](https://drive.google.com/file/d/1ULQ1VtybiqGk240grDYlGRacfi1vHlDL/view?usp=drive_link)
