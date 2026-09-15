from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from baseline_3sigma import SCORED_WEEKS
from src.api.main import app
from src.ranking.engine import RankingEngine


@pytest.fixture
def sample_gateways():
    return [f"{i:012X}" for i in range(1, 26)]


@pytest.fixture
def synthetic_telemetry_df(sample_gateways):
    """
    Generate realistic hourly telemetry data across a 35-day window
    before 2026-02-02 for 25 gateways.
    """
    np.random.seed(42)
    start_date = SCORED_WEEKS[0] - dt.timedelta(days=35)
    end_date = SCORED_WEEKS[0] + dt.timedelta(days=60)
    timestamps = pd.date_range(
        start=pd.Timestamp(start_date, tz="UTC"),
        end=pd.Timestamp(end_date, tz="UTC"),
        freq="h",
    )

    records = []
    for gw in sample_gateways:
        base_offline = np.random.uniform(10, 50)
        base_disc = np.random.uniform(0.5, 2.0)
        base_reboot = np.random.uniform(0.01, 0.1)

        n = len(timestamps)
        off = np.random.normal(base_offline, 5.0, n).clip(min=0)
        disc = np.random.poisson(base_disc, n)
        reb = np.random.poisson(base_reboot, n)

        # Inject 3-sigma spikes in the last 7 days before 2026-02-02 for gateways 1..15
        gw_num = int(gw, 16)
        if gw_num <= 15:
            spike_mask = (timestamps >= pd.Timestamp(SCORED_WEEKS[0] - dt.timedelta(days=5), tz="UTC")) & (
                timestamps < pd.Timestamp(SCORED_WEEKS[0], tz="UTC")
            )
            spike_hours = min(gw_num * 3, 25)
            indices = np.where(spike_mask)[0][:spike_hours]
            off[indices] += 200.0
            disc[indices] += 20
            reb[indices] += 5

        gw_df = pd.DataFrame(
            {
                "gateway_id": gw,
                "ts": timestamps,
                "offline_duration_sec": off,
                "disconnection_cnt": disc,
                "reboot_cnt": reb,
            }
        )
        records.append(gw_df)

    return pd.concat(records, ignore_index=True)


@pytest.fixture
def test_engine(synthetic_telemetry_df):
    return RankingEngine(frame=synthetic_telemetry_df)


@pytest.fixture
def client(test_engine, monkeypatch):
    import src.api.main as api_module
    monkeypatch.setattr(api_module, "get_engine", lambda: test_engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def parquet_data_dir(tmp_path, synthetic_telemetry_df):
    """
    Write parquet partitioned by month into a temporary directory
    to test real disk-loading E2E.
    """
    data_dir = tmp_path / "data"
    telemetry_dir = data_dir / "telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)

    df = synthetic_telemetry_df.copy()
    df["ts_utc"] = df["ts"].dt.strftime("%Y-%m-%d %H:%M:%S%z")
    df["month"] = df["ts"].dt.strftime("month=%Y-%m")

    for month_val, group in df.groupby("month"):
        month_dir = telemetry_dir / month_val
        month_dir.mkdir(parents=True, exist_ok=True)
        group.drop(columns=["month", "ts"]).to_parquet(
            month_dir / "telemetry.parquet",
            index=False,
        )

    return data_dir
