from __future__ import annotations

import datetime as dt
import pandas as pd
import pytest

from baseline_3sigma import SCORED_WEEKS, VISITS_PER_WEEK
from src.ranking.engine import RankingEngine, ThreeSigmaStrategy


def test_ranking_engine_returns_fifteen_gateways(test_engine):
    week_str = SCORED_WEEKS[0].isoformat()
    df = test_engine.get_week_rankings(week_str)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == VISITS_PER_WEEK
    assert len(df) == 15


def test_ranking_engine_ranks_are_one_through_fifteen(test_engine):
    week_str = SCORED_WEEKS[0].isoformat()
    df = test_engine.get_week_rankings(week_str)

    ranks = df["rank"].tolist()
    assert ranks == list(range(1, VISITS_PER_WEEK + 1))


def test_ranking_engine_expected_columns_exist(test_engine):
    week_str = SCORED_WEEKS[0].isoformat()
    df = test_engine.get_week_rankings(week_str)

    expected_cols = ["rank", "gateway_id", "score", "reason"]
    assert list(df.columns) == expected_cols


def test_ranking_engine_scores_and_reasons_are_valid(test_engine):
    week_str = SCORED_WEEKS[0].isoformat()
    df = test_engine.get_week_rankings(week_str)

    for _, row in df.iterrows():
        assert isinstance(row["score"], float)
        assert row["score"] >= 0.0
        assert isinstance(row["reason"], str)
        assert len(row["reason"]) > 0
        assert len(row["reason"]) <= 300


def test_pluggable_ranking_strategy(synthetic_telemetry_df):
    """
    Demonstrate that another developer can provide a custom ranking strategy
    without modifying the API or ranking engine interface.
    """
    class DummyHeuristicStrategy:
        def rank_week(self, frame: pd.DataFrame, monday: dt.date) -> pd.DataFrame:
            # Custom heuristic: sort by highest reboot_cnt sum in trailing week
            end = pd.Timestamp(monday, tz="UTC")
            recent = frame[(frame["ts"] >= end - dt.timedelta(days=7)) & (frame["ts"] < end)]
            grouped = recent.groupby("gateway_id")["reboot_cnt"].sum().reset_index()
            grouped = grouped.rename(columns={"reboot_cnt": "flagged_hours"})
            grouped["worst_metric"] = "reboot_cnt"
            return grouped.sort_values("flagged_hours", ascending=False).reset_index(drop=True)

        def build_predictions(self, frame: pd.DataFrame) -> pd.DataFrame:
            return pd.DataFrame(columns=["week_start", "rank", "gateway_id", "score", "reason"])

    custom_engine = RankingEngine(frame=synthetic_telemetry_df, strategy=DummyHeuristicStrategy())
    week_str = SCORED_WEEKS[0].isoformat()
    df = custom_engine.get_week_rankings(week_str)

    assert len(df) == 15
    assert df["rank"].tolist() == list(range(1, 16))
