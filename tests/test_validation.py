from __future__ import annotations

import pytest
from src.ranking.engine import RankingEngine


def test_invalid_date_format_raises_error(test_engine):
    with pytest.raises(ValueError, match="week_start must be in YYYY-MM-DD format"):
        test_engine.get_week_rankings("02-02-2026")

    with pytest.raises(ValueError, match="week_start must be in YYYY-MM-DD format"):
        test_engine.get_week_rankings("invalid-date")


def test_unsupported_week_raises_error(test_engine):
    with pytest.raises(ValueError, match="Unsupported week_start '2026-01-01'"):
        test_engine.get_week_rankings("2026-01-01")


def test_nonexistent_gateway_raises_key_error(test_engine):
    with pytest.raises(KeyError, match="does not exist in any telemetry records"):
        test_engine.explain_gateway("FFFFFFFFFFFF", "2026-02-02")
