# Architectural & Engineering Decisions (DECISIONS.md)

This document records the five major engineering choices made during the development of the **LPDG Innovation Hub Selection Challenge 2026** solution, along with alternatives considered and justifications for rejection.

---

## Decision 1: Selection of Software Development as Part 2 Discipline

### Context
The challenge brief offered six specialization tracks for Part 2: Data Engineering, Software Development, DevOps, Data Science, Machine Learning, and MLOps. Each required building upon the Part 1 baseline.

### Choice Made
Selected **Software Development (Track B)**.

### Alternatives Considered
1. **Machine Learning (Track E):** Train an ML model (e.g. Random Forest or Gradient Boosting) to predict gateway failure.
   - *Reason for Rejection:* Building a model that reliably beats the baseline on total cost within the time constraints risked introducing spurious correlations or overfitting to the synthetic telemetry distributions without operational ground truth. The brief noted that *"nobody loses marks for not doing machine learning"* and emphasized software craftsmanship.
2. **DevOps (Track C):** Focus entirely on containerization (Docker Compose) and CI/CD pipelines.
   - *Reason for Rejection:* Software development offered greater opportunity to demonstrate clean system architecture, extensible design patterns, comprehensive error handling, and robust diagnostic APIs that operational managers can interact with directly.

### Rationale
Software Development allowed building a resilient, maintainable service layer that decouples data management, anomaly mathematics, and service delivery, ensuring any future data science or ML enhancements can plug directly into the architecture.

---

## Decision 2: Preserving the 3-Sigma Anomaly Baseline Without Logic Modifications

### Context
The provided `baseline_3sigma.py` implements gateway-specific 28-day historical normalization across three telemetry metrics (`offline_duration_sec`, `disconnection_cnt`, `reboot_cnt`) and ranks gateways by flagged hours exceeding 3 standard deviations in the trailing 7 days.

### Choice Made
Preserved the baseline algorithm logic exactly as supplied in `baseline_3sigma.py` and wrapped it via the `ThreeSigmaStrategy`.

### Alternatives Considered
1. **Modifying Metric Thresholds (e.g. 2-sigma or 2.5-sigma):** Lowering the threshold to capture more marginal failures.
   - *Reason for Rejection:* Deviating from the official baseline introduces risk of breaking validator compliance or shifting visit priorities away from severe failures without empirical cost validation.
2. **Rewriting Algorithm Code Directly in the API:** Embedding the pandas logic directly in FastAPI route handlers.
   - *Reason for Rejection:* Violates separation of concerns. If the algorithm logic changes, the API routes would require rewriting.

### Rationale
Adhering to the official baseline guarantees 100% submission compliance against `validate_submission.py` while keeping the algorithm modular and interchangeable.

---

## Decision 3: Decoupling Ranking Logic from API via the Strategy Pattern

### Context
The system needed an architecture allowing another engineer to substitute the ranking algorithm without rewriting the API layer.

### Choice Made
Implemented the **Strategy Pattern** in `src/ranking/engine.py`:
- `RankingStrategy` protocol defining `rank_week` and `build_predictions`.
- `ThreeSigmaStrategy` implementing the baseline.
- `RankingEngine` accepting any conforming strategy via dependency injection.

### Alternatives Considered
1. **Direct Function Calls:** Hardcoding calls to `baseline_3sigma.py` functions inside route handlers.
   - *Reason for Rejection:* Tightly couples the API to a single script. Swapping ranking strategies would require modifying API source code.
2. **Subclassing / Class Inheritance:** Requiring custom rankers to inherit from a concrete base class.
   - *Reason for Rejection:* Python `Protocol` (structural subtyping / duck typing) provides greater flexibility and zero runtime inheritance overhead compared to rigid class hierarchies.

### Rationale
Engineers can implement custom models or heuristics simply by satisfying the protocol and passing their strategy to `RankingEngine(strategy=...)`, verified by `test_pluggable_ranking_strategy`.

---

## Decision 4: Choosing FastAPI and Pydantic v2 for the Service Layer

### Context
A modern HTTP service was required to expose weekly rankings, gateway explanations, and rerun capabilities.

### Choice Made
Selected **FastAPI** backed by **Pydantic v2** and **Uvicorn**.

### Alternatives Considered
1. **Flask:** Traditional lightweight WSGI framework.
   - *Reason for Rejection:* Flask lacks native async support, requires external plugins for data validation (e.g. Marshmallow), and does not generate interactive OpenAPI/Swagger documentation out-of-the-box.
2. **Django / Django REST Framework:** Heavyweight batteries-included web framework.
   - *Reason for Rejection:* Unnecessary overhead, database ORM coupling, and configuration bloat for a focused ranking microservice.

### Rationale
FastAPI provides automatic request validation, high throughput, clear status code semantics, and zero-configuration interactive Swagger docs at `/docs`—crucial for transparent evaluation.

---

## Decision 5: Multi-Tiered Automated Testing with Real Parquet Disk Integration

### Context
Testing needed to verify unit logic, input validation, API contracts, edge cases, and end-to-end system flow without relying entirely on mocks.

### Choice Made
Created a 20-test suite across five distinct test modules:
- `test_ranking_engine.py`: Unit tests for ranking logic, ordering, and strategy interchangeability.
- `test_validation.py`: Input validation for malformed dates, unsupported weeks, and unknown gateways.
- `test_api.py`: Route contracts, status codes (200, 400, 404, 422, 500), and response models.
- `test_regression.py`: Regression test for the gateway explanation bug outside top 15.
- `test_e2e.py`: Whole-system integration test executing `Client → API → Engine → Disk Parquet → Response`.

### Alternatives Considered
1. **Mocking All Data and Engine Calls:** Using unittest `Mock` for all tests.
   - *Reason for Rejection:* Specifically prohibited by challenge requirements: *"Do not make every test a mock. Create at least one test that exercises the application from API request through ranking engine and real challenge data."*
2. **Testing Only Happy Paths:** Checking only 200 OK responses.
   - *Reason for Rejection:* Would fail to verify error handling, malformed payloads, or exception suppression.

### Rationale
The multi-tiered suite guarantees that the full data pipeline operates correctly under both realistic and adverse conditions.
