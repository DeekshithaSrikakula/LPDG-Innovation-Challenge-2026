from __future__ import annotations

import pytest
from fastapi import status
from baseline_3sigma import SCORED_WEEKS
from src.ranking.engine import DataNotFoundError, RankingEngine


def test_get_health(client):
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "version" in data


def test_get_weekly_rankings_success(client):
    week_str = SCORED_WEEKS[0].isoformat()
    response = client.get(f"/weeks/{week_str}/rankings")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["week_start"] == week_str
    gateways = data["gateways"]
    assert len(gateways) == 15
    assert gateways[0]["rank"] == 1
    assert gateways[-1]["rank"] == 15
    for gw in gateways:
        assert "gateway_id" in gw
        assert "score" in gw
        assert "reason" in gw


def test_get_weekly_rankings_invalid_date(client):
    response = client.get("/weeks/2026-99-99/rankings")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "detail" in response.json()


def test_get_weekly_rankings_unsupported_week(client):
    response = client.get("/weeks/2025-08-04/rankings")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unsupported week_start" in response.json()["detail"]


def test_explain_gateway_success(client):
    week_str = SCORED_WEEKS[0].isoformat()
    # Rank 1 gateway exists in top 15
    rankings_resp = client.get(f"/weeks/{week_str}/rankings")
    first_gw = rankings_resp.json()["gateways"][0]["gateway_id"]

    response = client.get(f"/gateways/{first_gw}/explanation?week_start={week_str}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["gateway_id"] == first_gw
    assert data["rank"] == 1
    assert data["in_top_15"] is True
    assert "reason" in data


def test_explain_gateway_missing_param(client):
    response = client.get("/gateways/0A0000000001/explanation")
    assert response.status_code == 422


def test_explain_nonexistent_gateway(client):
    week_str = SCORED_WEEKS[0].isoformat()
    response = client.get(f"/gateways/UNKNOWN_GW/explanation?week_start={week_str}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "does not exist" in response.json()["detail"]


def test_post_run_single_week(client):
    week_str = SCORED_WEEKS[0].isoformat()
    response = client.post("/run", json={"week_start": week_str})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "completed"
    assert data["week_start"] == week_str
    assert len(data["gateways"]) == 15


def test_post_run_malformed_body(client):
    response = client.post("/run", content="not-json", headers={"Content-Type": "application/json"})
    assert response.status_code == 422


def test_missing_data_directory_returns_500_without_traceback(monkeypatch):
    import src.api.main as api_module
    from fastapi.testclient import TestClient

    # Create engine pointing to nonexistent data directory
    broken_engine = RankingEngine(data_dir="/nonexistent/path/data")
    monkeypatch.setattr(api_module, "get_engine", lambda: broken_engine)

    with TestClient(api_module.app) as test_client:
        response = test_client.get("/weeks/2026-02-02/rankings")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "detail" in data
        assert "Telemetry data directory not found" in data["detail"]
        # Ensure no raw python traceback is exposed
        assert "Traceback (most recent call last)" not in response.text
