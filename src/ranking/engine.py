from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from baseline_3sigma import (
    load,
    rank_week,
    build_predictions,
    SCORED_WEEKS,
    VISITS_PER_WEEK,
)


class RankingEngine:
    """
    Reusable interface around the LPDG baseline ranking logic.

    The API will use this class instead of directly depending on
    the implementation details of the ranking algorithm.
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.frame = load(self.data_dir)

    def get_week_rankings(self, week_start: str) -> pd.DataFrame:
        """
        Return the ranked gateways for a specific week.
        """

        try:
            monday = dt.date.fromisoformat(week_start)
        except ValueError as exc:
            raise ValueError(
                "week_start must be in YYYY-MM-DD format"
            ) from exc

        if monday not in SCORED_WEEKS:
            allowed = ", ".join(
                week.isoformat() for week in SCORED_WEEKS
            )
            raise ValueError(
                f"Unsupported week_start '{week_start}'. "
                f"Allowed weeks: {allowed}"
            )

        ranked = rank_week(self.frame, monday)

        if len(ranked) < VISITS_PER_WEEK:
            raise RuntimeError(
                f"Only {len(ranked)} gateways have enough data "
                f"for {week_start}"
            )

        result = ranked.head(VISITS_PER_WEEK).copy()

        result["rank"] = range(1, VISITS_PER_WEEK + 1)

        result["score"] = result["flagged_hours"].astype(float)

        result["reason"] = result.apply(
            lambda row: (
                f"{row['flagged_hours']} hour(s) beyond 3 sigma "
                f"of this gateway's own 28-day baseline in the "
                f"last 7 days; first breach on "
                f"{row['worst_metric'] or 'no metric over 3 sigma'}"
            ),
            axis=1,
        )

        return result[
            [
                "rank",
                "gateway_id",
                "score",
                "reason",
            ]
        ]

    def explain_gateway(
        self,
        gateway_id: str,
        week_start: str,
    ) -> dict:
        """
        Return the ranking explanation for one gateway.
        """

        rankings = self.get_week_rankings(week_start)

        matches = rankings[
            rankings["gateway_id"].astype(str) == str(gateway_id)
        ]

        if matches.empty:
            raise KeyError(
                f"Gateway '{gateway_id}' was not ranked in the "
                f"top {VISITS_PER_WEEK} for {week_start}"
            )

        row = matches.iloc[0]

        return {
            "week_start": week_start,
            "gateway_id": str(row["gateway_id"]),
            "rank": int(row["rank"]),
            "score": float(row["score"]),
            "reason": str(row["reason"]),
        }

    def run_all(self) -> pd.DataFrame:
        """
        Run the ranking for all eight scored weeks.

        This uses the same build_predictions() logic as the
        official baseline.
        """

        return build_predictions(self.frame)