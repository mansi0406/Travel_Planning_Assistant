# tests/test_agent_plan_trip_output.py
from __future__ import annotations

import pytest


def test_plan_trip_returns_required_keys():
    agent = pytest.importorskip("agent")  # skips if agent.py not importable
    assert hasattr(agent, "plan_trip"), "agent.plan_trip function not found"

    inputs = {
        "source": "Chennai",
        "destination": "Bangalore",
        "start_date": "2025-12-31",
        "end_date": "2025-12-31",
        "travelers": 1,
        "preference": "balanced",
        "hotel_min_stars": 3,
        "max_hotel_price": 0,
        "total_budget": 0,
    }

    # Use a safe default model name (  app locks this to llama3.1)
    result = agent.plan_trip(inputs, model="llama3.1")

    assert isinstance(result, dict), "plan_trip should return a dict"

    # Required top-level keys that   app displays
    for k in ["human_readable_markdown", "trip_summary", "selected_flight", "selected_hotel", "budget", "itinerary"]:
        assert k in result, f"Missing key in result: {k}"
