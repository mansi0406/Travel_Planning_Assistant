# tests/test_structured_text_formatters_do_not_crash.py
from __future__ import annotations

import pytest


def test_formatters_render_text():
    fmt = pytest.importorskip("src.formatters")  # create this file if not exists

    ts = {
        "source": "Chennai",
        "destination": "Bangalore",
        "start_date": "2025-12-31",
        "end_date": "2025-12-31",
        "days": 1,
        "travelers": 1,
        "preference": "balanced",
        "hotel_min_stars": 3,
        "max_hotel_price_per_night": None,
        "user_total_budget": None,
    }

    text = fmt.render_trip_summary_text(ts)
    assert isinstance(text, str)
    assert "\n" in text  # should have multiple lines
