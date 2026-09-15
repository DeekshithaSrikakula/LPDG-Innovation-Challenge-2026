from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Protocol

import pandas as pd

from baseline_3sigma import (
    load,
    rank_week,
    build_predictions,
    SCORED_WEEKS,
    VISITS_PER_WEEK,
)
from validate_submission import normalise_gateway_id


class DataNotFoundError(RuntimeError):
    """Raised when the expected challenge data directory cannot be found."""
    pass


class RankingStrategy(Protocol):
    """
    Protocol defining the interface for gateway ranking strategies.
    Any custom strategy (e.g. ML, heuristics) can be swapped in without modifying the API.
    """

    def rank_week(self, frame: pd.DataFrame, monday: dt.date) -> pd.DataFrame:
        ...

    def build_predictions(self, frame: pd.DataFrame) -> pd.DataFrame:
        ...


class ThreeSigmaStrategy:
    """
    Official 3-sigma anomaly baseline strategy.
    Delegates directly to baseline_3sigma.py to guarantee 100% algorithm parity.
    """

    def rank_week(self, frame: pd.DataFrame, monday: dt.date) -> pd.DataFrame:
        return rank_week(frame, monday)

    def build_predictions(self, frame: pd.DataFrame) -> pd.DataFrame:
        return build_predictions(frame)


class RankingEngine:
    """
    Reusable interface around gateway ranking logic.

    Maintains clean separation between data, ranking algorithms, and the API layer.
    Supports pluggable ranking strategies (Strategy pattern).
    """

    def __init__(
        self,
        data_dir: Path | str | None = None,
        frame: pd.DataFrame | None = None,
        strategy: RankingStrategy | None = None,
    ):
        self.data_dir = Path(data_dir) if data_dir is not None else None
        self._frame = frame
        self.strategy: RankingStrategy = strategy or ThreeSigmaStrategy()

    @property
    def frame(self) -> pd.DataFrame:
        if self._frame is None:
            if self.data_dir is None or not (self.data_dir / "telemetry").exists():
                raise DataNotFoundError(
                    f"Telemetry data directory not found at "
                    f"'{self.data_dir / 'telemetry' if self.data_dir else 'None'}'. "
                    f"Please verify data/ is placed in the project root."
                )
            self._frame = load(self.data_dir)
        return self._frame

    def get_full_week_rankings(self, week_start: str) -> tuple[dt.date, pd.DataFrame]:
        """
        Validate week_start and return the complete scored gateway DataFrame
        (all gateways, sorted by flagged hours).
        """
        try:
            monday = dt.date.fromisoformat(week_start)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"week_start must be in YYYY-MM-DD format, got '{week_start}'"
            ) from exc

        if monday not in SCORED_WEEKS:
            allowed = ", ".join(week.isoformat() for week in SCORED_WEEKS)
            raise ValueError(
                f"Unsupported week_start '{week_start}'. "
                f"Allowed scored Mondays: {allowed}"
            )

        ranked = self.strategy.rank_week(self.frame, monday)
        if len(ranked) < VISITS_PER_WEEK:
            raise RuntimeError(
                f"Only {len(ranked)} gateways have enough data for {week_start}"
            )
        return monday, ranked

    def get_week_rankings(self, week_start: str) -> pd.DataFrame:
        """
        Return the top 15 ranked gateways for a specific scored week.
        """
        monday, ranked = self.get_full_week_rankings(week_start)

        result = ranked.head(VISITS_PER_WEEK).copy().reset_index(drop=True)
        result["rank"] = range(1, len(result) + 1)
        result["score"] = result["flagged_hours"].astype(float)
        result["reason"] = result.apply(
            lambda row: (
                f"{int(row['flagged_hours'])} hour(s) beyond 3 sigma "
                f"of this gateway's own 28-day baseline in the "
                f"last 7 days; first breach on "
                f"{row['worst_metric'] or 'no metric over 3 sigma'}"
            ),
            axis=1,
        )

        return result[["rank", "gateway_id", "score", "reason"]]

    def explain_gateway(
        self,
        gateway_id: str,
        week_start: str,
    ) -> dict[str, Any]:
        """
        Return the ranking explanation for a gateway.

        Sensibly explains gateways whether they are in the top 15 or outside the top 15.
        Only raises KeyError if the gateway is completely absent from telemetry records.
        """
        monday, full_ranked = self.get_full_week_rankings(week_start)

        clean_id = normalise_gateway_id(gateway_id) or str(gateway_id).strip().upper()

        full_ranked["norm_id"] = full_ranked["gateway_id"].astype(str).str.upper()
        matches = full_ranked[full_ranked["norm_id"] == clean_id]

        if not matches.empty:
            match_idx = matches.index[0]
            row = matches.iloc[0]
            # Rank is 1-based index in the sorted list of gateways
            rank = int(match_idx) + 1
            score = float(row["flagged_hours"])
            metric = row["worst_metric"] or "no metric over 3 sigma"

            if rank <= VISITS_PER_WEEK:
                reason = (
                    f"{int(score)} hour(s) beyond 3 sigma of this gateway's own "
                    f"28-day baseline in the last 7 days; first breach on {metric}"
                )
            elif score > 0:
                reason = (
                    f"Ranked #{rank} with {int(score)} hour(s) beyond 3 sigma; "
                    f"fell below the top {VISITS_PER_WEEK} priority visit threshold for week {week_start}."
                )
            else:
                reason = (
                    f"Ranked #{rank} with 0 hours beyond 3 sigma; "
                    f"normal operating behavior in the last 7 days, no visit required."
                )

            return {
                "week_start": week_start,
                "gateway_id": str(row["gateway_id"]),
                "rank": rank,
                "score": score,
                "reason": reason,
                "in_top_15": rank <= VISITS_PER_WEEK,
            }

        # If not in full_ranked, check if it exists in the wider telemetry frame
        known_gateways = set(self.frame["gateway_id"].astype(str).str.upper().unique())
        if clean_id in known_gateways:
            return {
                "week_start": week_start,
                "gateway_id": str(gateway_id),
                "rank": None,
                "score": 0.0,
                "reason": (
                    f"Gateway '{gateway_id}' is registered in telemetry but had no "
                    f"recorded activity during the 28-day baseline window ending {week_start}."
                ),
                "in_top_15": False,
            }

        raise KeyError(
            f"Gateway '{gateway_id}' does not exist in any telemetry records."
        )

    def run_all(self) -> pd.DataFrame:
        """
        Run the ranking for all eight scored weeks using the active strategy.
        """
        return self.strategy.build_predictions(self.frame)