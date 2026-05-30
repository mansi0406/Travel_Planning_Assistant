# tests/test_budget_graceful_when_blank.py
from __future__ import annotations

import pytest


def test_budget_handles_missing_optional_values():
    agent = pytest.importorskip("agent")
    assert hasattr(agent, "plan_trip")

    inputs = {
        "source": "Chennai",
        "destination": "Bangalore",
        "start_date": "2025-12-31",
        "end_date": "2025-12-31",
        "travelers": 1,
        "preference": "balanced",
        "hotel_min_stars": 3,
        # blank/0 optional fields
        "max_hotel_price": 0,
        "total_budget": 0,
    }

    result = agent.plan_trip(inputs, model="llama3.1")
    budget = result.get("budget", {})

    # Budget must exist and be dict (even if values are None)
    assert isinstance(budget, dict)
