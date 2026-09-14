from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from src.ranking.engine import RankingEngine


# ---------------------------------------------------------
# Application setup
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

app = FastAPI(
    title="LPDG Gateway Ranking API",
    description=(
        "API for identifying the 15 gateways that should be "
        "visited for a given week."
    ),
    version="1.0.0",
)

engine = RankingEngine(DATA_DIR)


# ---------------------------------------------------------
# Response models
# ---------------------------------------------------------

class GatewayRanking(BaseModel):
    rank: int
    gateway_id: str
    score: float
    reason: str


class WeekRankings(BaseModel):
    week_start: str
    gateways: list[GatewayRanking]


class RunRequest(BaseModel):
    week_start: str | None = None


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "LPDG Gateway Ranking API",
    }


# ---------------------------------------------------------
# 1. Get the 15 gateways for a week
# ---------------------------------------------------------

@app.get(
    "/weeks/{week_start}/rankings",
    response_model=WeekRankings,
)
def get_week_rankings(week_start: str):
    try:
        rankings = engine.get_week_rankings(week_start)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    gateways = [
        GatewayRanking(
            rank=int(row["rank"]),
            gateway_id=str(row["gateway_id"]),
            score=float(row["score"]),
            reason=str(row["reason"]),
        )
        for _, row in rankings.iterrows()
    ]

    return WeekRankings(
        week_start=week_start,
        gateways=gateways,
    )


# ---------------------------------------------------------
# 2. Explain why a gateway is ranked
# ---------------------------------------------------------

@app.get("/gateways/{gateway_id}/explanation")
def explain_gateway(
    gateway_id: str,
    week_start: str = Query(...),
):
    try:
        return engine.explain_gateway(
            gateway_id=gateway_id,
            week_start=week_start,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------
# 3. Run the ranking again
# ---------------------------------------------------------

@app.post("/run")
def run_ranking(request: RunRequest):
    try:

        # If a week was supplied, run only that week.
        if request.week_start:
            rankings = engine.get_week_rankings(
                request.week_start
            )

            gateways = [
                {
                    "rank": int(row["rank"]),
                    "gateway_id": str(row["gateway_id"]),
                    "score": float(row["score"]),
                    "reason": str(row["reason"]),
                }
                for _, row in rankings.iterrows()
            ]

            return {
                "status": "completed",
                "week_start": request.week_start,
                "gateways": gateways,
            }

        # Otherwise run all eight weeks.
        predictions = engine.run_all()

        return {
            "status": "completed",
            "weeks": int(predictions["week_start"].nunique()),
            "rows": int(len(predictions)),
            "message": "Ranking completed for all scored weeks.",
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc