# tests/test_basic_filters_matching.py
"""
Basic dataset sanity checks.
Fixes the earlier bug: tests assumed dict access like flights["flights"]
but flights.json is a LIST of dict records.
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.data_access import load_all_json


def _as_list(obj: Any) -> List[Dict[str, Any]]:
    #   loader returns whatever json.load() returns
    # For   datasets it should be a list, but this keeps tests robust.
    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]
    if isinstance(obj, dict):
        # fallback if someday   wrap like {"flights":[...]}
        for key in ("flights", "hotels", "places", "data"):
            inner = obj.get(key)
            if isinstance(inner, list):
                return [x for x in inner if isinstance(x, dict)]
    return []


def test_flights_have_city_pairs():
    data = load_all_json()
    flights_raw = data.get("flights", [])
    flights = _as_list(flights_raw)

    assert flights, "No flights loaded from data/flights.json"
    for i, f in enumerate(flights[:50]):
        assert f.get("from"), f"flights[{i}] missing 'from'"
        assert f.get("to"), f"flights[{i}] missing 'to'"


def test_hotels_have_city():
    data = load_all_json()
    hotels_raw = data.get("hotels", [])
    hotels = _as_list(hotels_raw)

    assert hotels, "No hotels loaded from data/hotels.json"
    for i, h in enumerate(hotels[:50]):
        assert h.get("city"), f"hotels[{i}] missing 'city'"


def test_places_have_city():
    data = load_all_json()
    places_raw = data.get("places", [])
    places = _as_list(places_raw)

    assert places, "No places loaded from data/places.json"
    for i, p in enumerate(places[:50]):
        assert p.get("city"), f"places[{i}] missing 'city'"
