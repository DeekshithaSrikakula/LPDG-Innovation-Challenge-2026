from __future__ import annotations

import pytest
from fastapi import status
from baseline_3sigma import SCORED_WEEKS, VISITS_PER_WEEK


def test_bug_regression_gateway_outside_top_15_not_404(client, test_engine):
    """
    BUG REGRESSION TEST:
    Prior Bug: In initial development, explain_gateway() only checked get_week_rankings(),
    which contained only the top 15 gateways. If an operations manager asked for an
    explanation of a valid gateway that happened to be ranked #16 or lower (or had 0 breaches),
    the API erroneously returned 404 Not Found as if the gateway didn't exist in the network!

    Fix: explain_gateway() now examines the full weekly ranked distribution.
    A valid gateway outside the top 15 returns 200 OK with in_top_15=False, its actual rank,
    and a clear explanation of why it fell below the visit threshold. Only genuinely
    unregistered gateways return 404.
    """
    week_str = SCORED_WEEKS[0].isoformat()

    # In our synthetic fixture of 25 gateways, gateways 16 through 25 are outside the top 15
    _, full_ranked = test_engine.get_full_week_rankings(week_str)
    assert len(full_ranked) >= 20

    # Pick the 16th ranked gateway
    lower_gw = str(full_ranked.iloc[15]["gateway_id"])

    response = client.get(f"/gateways/{lower_gw}/explanation?week_start={week_str}")

    # MUST NOT return 404! Must return 200 with clear explanation
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["gateway_id"] == lower_gw
    assert data["rank"] == 16
    assert data["in_top_15"] is False
    assert "fell below the top 15" in data["reason"] or "normal operating" in data["reason"]
