# tests/test_schema_flights_hotels_places.py
"""
Schema tests for the JSON datasets.
 JSON files are LISTS of records, not dict wrappers.

So we validate:
- file loads
- is a list
- each item is dict
- required keys exist
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.data_access import load_all_json


def _assert_list_of_dicts(obj: Any, name: str) -> List[Dict[str, Any]]:
    assert isinstance(obj, list), f"Expected `{name}` to be a list, got {type(obj)}"
    for i, row in enumerate(obj[:20]):  # check first 20 for speed
        assert isinstance(row, dict), f"Expected `{name}[{i}]` to be dict, got {type(row)}"
    return obj


def test_flights_schema():
    data = load_all_json()
    flights = data.get("flights", [])
    flights = _assert_list_of_dicts(flights, "flights")

    required = {"flight_id", "airline", "from", "to", "departure_time", "arrival_time", "price"}
    for i, f in enumerate(flights[:20]):
        missing = required - set(f.keys())
        assert not missing, f"flights[{i}] missing keys: {missing}"


def test_hotels_schema():
    data = load_all_json()
    hotels = data.get("hotels", [])
    hotels = _assert_list_of_dicts(hotels, "hotels")

    required = {"hotel_id", "name", "city", "stars", "price_per_night", "amenities"}
    for i, h in enumerate(hotels[:20]):
        missing = required - set(h.keys())
        assert not missing, f"hotels[{i}] missing keys: {missing}"


def test_places_schema():
    data = load_all_json()
    places = data.get("places", [])
    places = _assert_list_of_dicts(places, "places")

    required = {"place_id", "name", "city", "type", "rating"}
    for i, p in enumerate(places[:20]):
        missing = required - set(p.keys())
        assert not missing, f"places[{i}] missing keys: {missing}"
