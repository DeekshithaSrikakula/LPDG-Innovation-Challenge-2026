from __future__ import annotations

from pathlib import Path
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from baseline_3sigma import SCORED_WEEKS
from src.api.main import app, get_engine
from src.ranking.engine import RankingEngine


def test_whole_system_e2e(parquet_data_dir, monkeypatch):
    """
    WHOLE-SYSTEM E2E TEST:
    Exercises the complete end-to-end flow:
    HTTP API Request
      ↓
    FastAPI Router & Validation
      ↓
    RankingEngine
      ↓
    Real Disk Parquet Reading (load)
      ↓
    3-Sigma Anomaly Math (rank_week)
      ↓
    HTTP Structured Response

    No mock dataframes — reads real partitioned parquet files from disk!
    """
    # Instantiate RankingEngine directly with real parquet data directory on disk
    real_engine = RankingEngine(data_dir=parquet_data_dir)

    import src.api.main as api_module
    monkeypatch.setattr(api_module, "get_engine", lambda: real_engine)

    with TestClient(app) as test_client:
        week_str = SCORED_WEEKS[0].isoformat()

        # Step 1: Health check
        health_resp = test_client.get("/health")
        assert health_resp.status_code == status.HTTP_200_OK

        # Step 2: Request weekly rankings (triggers parquet load and 3-sigma math)
        rank_resp = test_client.get(f"/weeks/{week_str}/rankings")
        assert rank_resp.status_code == status.HTTP_200_OK
        rank_data = rank_resp.json()
        assert rank_data["week_start"] == week_str
        assert len(rank_data["gateways"]) == 15

        # Step 3: Request explanation for top gateway
        top_gw = rank_data["gateways"][0]["gateway_id"]
        exp_resp = test_client.get(f"/gateways/{top_gw}/explanation?week_start={week_str}")
        assert exp_resp.status_code == status.HTTP_200_OK
        exp_data = exp_resp.json()
        assert exp_data["gateway_id"] == top_gw
        assert exp_data["rank"] == 1
        assert exp_data["in_top_15"] is True

        # Step 4: Trigger POST /run for this week
        run_resp = test_client.post("/run", json={"week_start": week_str})
        assert run_resp.status_code == status.HTTP_200_OK
        assert run_resp.json()["status"] == "completed"
