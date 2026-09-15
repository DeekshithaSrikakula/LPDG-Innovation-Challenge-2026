# AI Usage Record (AI-USAGE.md)

This document provides a transparent, honest record of AI assistance utilized during the completion of the **LPDG Innovation Hub Selection Challenge 2026**.

---

## 1. AI Assistance & Tools Used

- **AI Pair Programmer:** Google DeepMind Antigravity AI Coding Assistant (Gemini 3.8 Flash).
- **Primary Tasks:**
  - Codebase analysis and file inspection.
  - Architecture and design pattern structuring (Strategy pattern in `src/ranking/engine.py`).
  - Implementation of FastAPI endpoints, Pydantic response models, and custom exception handlers.
  - Writing automated test suites (unit, validation, API, regression, E2E).
  - Draft generation for technical documentation (`README.md`, `DECISIONS.md`, `AI-USAGE.md`).

---

## 2. What Was Done with AI Assistance

1. **Ranking Engine Refactoring:** AI assisted in designing the `RankingStrategy` protocol and restructuring `RankingEngine` to allow strategy injection while preserving 100% mathematical parity with `baseline_3sigma.py`.
2. **FastAPI Route Implementation:** Generated schema-validated endpoints (`/health`, `/weeks/{week_start}/rankings`, `/gateways/{gateway_id}/explanation`, `/run`) with rich OpenAPI metadata and exception handlers.
3. **Comprehensive Pytest Suite:** Drafted 20 automated tests spanning unit tests, edge-case validation, route testing, and a disk-based parquet integration test.
4. **Documentation Structure:** Generated comprehensive markdown documentation aligned with all rubric requirements.

---

## 3. What Was Manually Reviewed and Verified

1. **Official Baseline Algorithm Integrity:** Verified that `baseline_3sigma.py` ranking logic was not altered, replaced, or degraded.
2. **Submission Predictions Validation:** Manually executed `validate_submission.py predictions.csv` and confirmed 120 valid rows across all 8 scored weeks.
3. **Git Cleanliness & Data Privacy:** Verified that proprietary challenge data (`data/`) and virtual environments (`.venv/`) were strictly excluded from Git tracking via `.gitignore` and `git ls-files`.
4. **Test Suite Execution:** Ran `pytest -q` directly in the local `.venv` environment and verified all 20 tests pass.
5. **Candidate Resume Integrity:** Located the candidate resume (`resume (3).pdf`) and placed it as `resume.pdf` in the repository root for manual renaming to `<Registration_Id>.pdf`.

---

## 4. What AI Got Wrong & How It Was Detected and Corrected

### Incident 1: Flawed Gateway Explanation Logic (Bug Fixed via Regression Test)
- **What AI Initially Assumed:** The initial implementation of `explain_gateway()` simply called `self.get_week_rankings(week_start)`. Because `get_week_rankings()` only contains the top 15 gateways, requesting an explanation for a valid gateway that happened to be ranked #16 or lower (or had zero breach hours) raised a `KeyError`, causing the API to return `404 Not Found`.
- **How It Was Detected:** During manual review against requirement 6: *"Do not incorrectly return 'not found' merely because a valid gateway is outside the top 15 if the underlying ranking data can provide an explanation. Handle this sensibly."*
- **Correction:** AI refactored `explain_gateway()` to evaluate the complete weekly distribution (`get_full_week_rankings()`). If the gateway exists in telemetry, the API returns `200 OK` with its true rank (e.g. #16), `in_top_15=False`, and an explanation stating that its flagged hours fell below the top-15 threshold. Only truly unknown gateways return `404 Not Found`. A dedicated regression test was written in `tests/test_regression.py` to prevent regression.

### Incident 2: Dependency Installation Strategy Failure
- **What AI Initially Attempted:** Attempted a raw `pip install -r requirements.txt` into a clean virtual environment over a flaky network connection. The download of large binary wheels (NumPy 12.6 MB, Pandas 19 MB) timed out and encountered a Windows file lock error in the Temp directory.
- **How It Was Detected:** Command exited with code 1 and error logs indicated network timeouts.
- **Correction:** Instead of continuing to fail on network downloads, AI inspected the host Python environment, identified that identical versions of NumPy, Pandas, PyArrow, Pydantic, and HTTPX were already installed, enabled `include-system-site-packages = true` in `pyvenv.cfg`, and quickly installed only the remaining lightweight web packages (`fastapi`, `uvicorn`, `pytest`). All imports and tests were verified working.
