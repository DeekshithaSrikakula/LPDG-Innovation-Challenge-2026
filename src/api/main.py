from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.ranking.engine import DataNotFoundError, RankingEngine


# ---------------------------------------------------------
# Application setup
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

app = FastAPI(
    title="LPDG Gateway Ranking API",
    description=(
        "Production-ready REST API for the LPDG Innovation Hub Selection Challenge 2026. "
        "Provides endpoints to retrieve the weekly top 15 gateways for engineer visits, "
        "detailed ranking explanations for any gateway, and execution triggers to regenerate predictions."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

engine = RankingEngine(DATA_DIR)


def get_engine() -> RankingEngine:
    """Dependency / accessor for the ranking engine."""
    return engine


# ---------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------

@app.exception_handler(DataNotFoundError)
async def data_not_found_handler(request: Request, exc: DataNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(KeyError)
async def key_error_handler(request: Request, exc: KeyError):
    # Strip any formatting quotes
    msg = str(exc).strip("'\"")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": msg},
    )


# ---------------------------------------------------------
# Request & Response Models
# ---------------------------------------------------------

class GatewayRanking(BaseModel):
    rank: int = Field(..., description="Rank between 1 and 15", ge=1, le=15, json_schema_extra={"example": 1})
    gateway_id: str = Field(..., description="12-hex character or colon-delimited gateway ID", json_schema_extra={"example": "0A2778A31BE3"})
    score: float = Field(..., description="Calculated score (number of 3-sigma flagged breach hours)", json_schema_extra={"example": 43.0})
    reason: str = Field(..., description="Auditable explanation for why this gateway requires a field visit", json_schema_extra={"example": "43 hour(s) beyond 3 sigma of this gateway's own 28-day baseline in the last 7 days; first breach on disconnection_cnt"})


class WeekRankings(BaseModel):
    week_start: str = Field(..., description="Scored Monday in YYYY-MM-DD format", json_schema_extra={"example": "2026-02-02"})
    gateways: list[GatewayRanking] = Field(..., description="Ordered list of top 15 gateways requiring site visits")


class GatewayExplanation(BaseModel):
    week_start: str = Field(..., description="Scored Monday in YYYY-MM-DD format", json_schema_extra={"example": "2026-02-02"})
    gateway_id: str = Field(..., description="Gateway identifier", json_schema_extra={"example": "0A2778A31BE3"})
    rank: int | None = Field(None, description="Ranking position (1-15 if in top 15, >15 if lower, or None if inactive)", json_schema_extra={"example": 1})
    score: float = Field(..., description="Flagged breach hours beyond 3 sigma", json_schema_extra={"example": 43.0})
    reason: str = Field(..., description="Detailed diagnostic rationale for ranking status", json_schema_extra={"example": "43 hour(s) beyond 3 sigma of this gateway's own 28-day baseline in the last 7 days; first breach on disconnection_cnt"})
    in_top_15: bool = Field(..., description="True if gateway is among the 15 selected for an engineer site visit", json_schema_extra={"example": True})


class RunRequest(BaseModel):
    week_start: str | None = Field(
        None,
        description="Optional single scored Monday (YYYY-MM-DD). If omitted, all 8 scored weeks are processed.",
        json_schema_extra={"example": "2026-02-02"},
    )


class RunResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "completed"})
    message: str = Field(..., json_schema_extra={"example": "Ranking completed for all scored weeks."})
    week_start: str | None = Field(None, json_schema_extra={"example": "2026-02-02"})
    weeks: int | None = Field(None, json_schema_extra={"example": 8})
    rows: int | None = Field(None, json_schema_extra={"example": 120})
    gateways: list[dict[str, Any]] | None = None
    output_file: str | None = Field(None, json_schema_extra={"example": "predictions.csv"})


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------

@app.get(
    "/health",
    summary="Health check",
    description="Check the health of the service, API version, and data readiness status.",
    tags=["System"],
)
def health():
    data_ready = (DATA_DIR / "telemetry").exists()
    return {
        "status": "ok",
        "service": "LPDG Gateway Ranking API",
        "version": "1.0.0",
        "data_ready": data_ready,
    }


# ---------------------------------------------------------
# 1. Get the 15 gateways for a week
# ---------------------------------------------------------

@app.get(
    "/weeks/{week_start}/rankings",
    response_model=WeekRankings,
    summary="Get 15 ranked gateways for a week",
    description=(
        "Returns the top 15 gateways prioritized for physical field team visits for the specified scored Monday. "
        "Each gateway entry contains its 1-15 rank, ID, breach score, and audit reason."
    ),
    tags=["Rankings"],
)
def get_week_rankings(week_start: str):
    active_engine = get_engine()
    rankings = active_engine.get_week_rankings(week_start)

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

@app.get(
    "/gateways/{gateway_id}/explanation",
    response_model=GatewayExplanation,
    summary="Explain ranking for a gateway",
    description=(
        "Explains the diagnostic basis of a gateway's ranking for a given week. "
        "Provides complete transparency for gateways both inside and outside the top 15. "
        "Returns 404 only if the gateway does not exist in network records."
    ),
    tags=["Diagnostics"],
)
def explain_gateway(
    gateway_id: str,
    week_start: str = Query(..., description="The scored Monday to evaluate (YYYY-MM-DD)", examples=["2026-02-02"]),
):
    active_engine = get_engine()
    return active_engine.explain_gateway(
        gateway_id=gateway_id,
        week_start=week_start,
    )


# ---------------------------------------------------------
# 3. Run the ranking again
# ---------------------------------------------------------

@app.post(
    "/run",
    response_model=RunResponse,
    summary="Trigger ranking execution",
    description=(
        "Rerun ranking calculation on demand. "
        "If a specific `week_start` is passed, recalculates and returns the top 15 for that week. "
        "If `week_start` is null or omitted, regenerates predictions for all 8 scored weeks and updates predictions.csv."
    ),
    tags=["Execution"],
)
def run_ranking(request: RunRequest):
    active_engine = get_engine()

    # If a single week was supplied, run only that week.
    if request.week_start:
        rankings = active_engine.get_week_rankings(request.week_start)
        gateways = [
            {
                "rank": int(row["rank"]),
                "gateway_id": str(row["gateway_id"]),
                "score": float(row["score"]),
                "reason": str(row["reason"]),
            }
            for _, row in rankings.iterrows()
        ]

        return RunResponse(
            status="completed",
            message=f"Ranking completed successfully for week {request.week_start}.",
            week_start=request.week_start,
            gateways=gateways,
        )

    # Otherwise run all eight weeks and update predictions.csv.
    predictions = active_engine.run_all()
    predictions_path = PROJECT_ROOT / "predictions.csv"
    predictions.to_csv(predictions_path, index=False)

    return RunResponse(
        status="completed",
        message="Ranking completed and predictions.csv updated for all scored weeks.",
        weeks=int(predictions["week_start"].nunique()),
        rows=int(len(predictions)),
        output_file="predictions.csv",
    )