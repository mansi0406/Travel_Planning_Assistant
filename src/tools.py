# src/tools.py - add weather + fix docstrings + fastest flight + budget with local expenses
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import requests
from langchain_core.tools import tool

from data_access import load_all_json

# Defining helper functions for normalization and safe conversions
def _norm(s: Any) -> str:
    return str(s or "").strip().lower()


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _parse_hhmm(time_str: Any) -> Optional[int]:
    """
    Parse "HH:MM" into minutes from midnight.
    Returns None if invalid.
    """
    if not time_str:
        return None
    s = str(time_str).strip()
    try:
        dt = datetime.strptime(s, "%H:%M")
        return dt.hour * 60 + dt.minute
    except Exception:
        return None


def _duration_minutes(dep: Any, arr: Any) -> Optional[int]:
    """
    Compute duration in minutes from departure_time and arrival_time ("HH:MM").
    Handles crossing midnight.
    """
    d = _parse_hhmm(dep)
    a = _parse_hhmm(arr)
    if d is None or a is None:
        return None
    if a >= d:
        return a - d
    return (24 * 60 - d) + a


# -------------------------
# Flights tool (flights.json)
# -------------------------
@tool("flight_search")
def flight_search(source_city: str, destination_city: str, preference: str = "balanced") -> List[Dict[str, Any]]:
    """
    Search flights from flights.json by source and destination.

    Expected flight keys (from   dataset): flight_id, airline, from, to, departure_time, arrival_time, price.

    preference:
      - budget: cheapest
      - luxury: slightly prefers higher price (optional heuristic)
      - balanced: cheapest with tie-break on duration
      - fastest: shortest duration first
    """
    data = load_all_json()
    flights = data.get("flights", [])

    if isinstance(flights, dict):
        flights = flights.get("flights", [])

    if not isinstance(flights, list):
        return []

    src = _norm(source_city)
    dst = _norm(destination_city)

    matches = [
        f for f in flights
        if isinstance(f, dict)
        and _norm(f.get("from")) == src
        and _norm(f.get("to")) == dst
    ]

    # enrich with computed duration_mins if possible (non-destructive)
    for f in matches:
        dur = _duration_minutes(f.get("departure_time"), f.get("arrival_time"))
        if dur is not None:
            f["_duration_mins"] = dur

    pref = _norm(preference)

    if pref == "fastest":
        matches.sort(key=lambda x: (x.get("_duration_mins", 10**9), _safe_float(x.get("price"), 1e18)))
    elif pref == "budget":
        matches.sort(key=lambda x: (_safe_float(x.get("price"), 1e18), x.get("_duration_mins", 10**9)))
    elif pref == "luxury":
        # luxury heuristic: higher airline "experience" not available, so prefer higher price after filtering
        matches.sort(key=lambda x: (-_safe_float(x.get("price"), 0.0), x.get("_duration_mins", 10**9)))
    else:
        # balanced: prioritize price, tie-break by duration if available
        matches.sort(key=lambda x: (_safe_float(x.get("price"), 1e18), x.get("_duration_mins", 10**9)))

    return matches


# -------------------------
# Hotels tool (hotels.json)
# -------------------------
@tool("hotel_search")
def hotel_search(
    destination_city: str,
    min_stars: int = 3,
    max_price_per_night: Optional[float] = None,
    preference: str = "balanced",
) -> List[Dict[str, Any]]:
    """
    Search hotels from hotels.json by destination city.

    Expected hotel keys (from   dataset): hotel_id, name, city, stars, price_per_night, amenities.
    """
    data = load_all_json()
    hotels = data.get("hotels", [])

    if isinstance(hotels, dict):
        hotels = hotels.get("hotels", [])

    if not isinstance(hotels, list):
        return []

    dst = _norm(destination_city)
    pref = _norm(preference)

    def stars_val(h: Dict[str, Any]) -> float:
        return _safe_float(h.get("stars"), 0.0)

    def price_val(h: Dict[str, Any]) -> float:
        return _safe_float(h.get("price_per_night"), 1e18)

    matches = [
        h for h in hotels
        if isinstance(h, dict)
        and _norm(h.get("city")) == dst
        and stars_val(h) >= float(min_stars)
    ]

    if max_price_per_night is not None:
        matches = [h for h in matches if price_val(h) <= float(max_price_per_night)]

    if pref == "budget":
        matches.sort(key=lambda h: (price_val(h), -stars_val(h)))
    elif pref == "luxury":
        matches.sort(key=lambda h: (-stars_val(h), price_val(h)))
    else:
        matches.sort(key=lambda h: (-stars_val(h), price_val(h)))

    return matches


# -------------------------
# Attractions tool (places.json)
# -------------------------
PREFERENCE_TO_TYPES: Dict[str, List[str]] = {
    "luxury": ["beach", "fort", "monument", "museum", "park"],
    "budget": ["market", "park", "temple", "lake"],
    "balanced": [],
    "nature": ["beach", "lake", "park"],
    "history": ["fort", "museum", "monument"],
    "culture": ["temple", "museum", "monument"],
    "shopping": ["market"],
    
}

# Some datasets contain unrealistic categories for certain cities.
CITY_TYPE_BLACKLIST: Dict[str, List[str]] = {
    "bangalore": ["beach"],
    "bengaluru": ["beach"],
    "Delhi": ["beach"],
    "new delhi": ["beach"],
    "Hyderabad": ["beach"],
    "Chennai": ["mountain"],
}

@tool("attraction_search")
def attraction_search(destination: str, preference: str = "balanced", days: int = 3) -> List[Dict[str, Any]]:
    """
    Search attractions from places.json by destination city.

    Expected place keys (from  dataset): place_id, name, city, type, rating.
    Returns top-rated items (repeated if needed) to fill days * 3.
    """
    data = load_all_json()
    places = data.get("places", [])

    if isinstance(places, dict):
        places = places.get("places", [])

    if not isinstance(places, list):
        return []

    dest = _norm(destination)
    pref = _norm(preference)

    city_matches = [p for p in places if isinstance(p, dict) and _norm(p.get("city")) == dest]
    if not city_matches:
        return []

    allowed_types = PREFERENCE_TO_TYPES.get(pref, [])
    if allowed_types:
        allowed_set = {t.lower() for t in allowed_types}
        filtered = [p for p in city_matches if _norm(p.get("type")) in allowed_set]
    else:
        filtered = city_matches
        
    # City-based type sanity filter (e.g., no "beach" in Bangalore)
    blacklist = set(CITY_TYPE_BLACKLIST.get(dest, []))
    if blacklist:
        filtered = [p for p in filtered if _norm(p.get("type")) not in blacklist]
    if not filtered:
        filtered = city_matches
        

    filtered.sort(key=lambda x: _safe_float(x.get("rating"), 0.0), reverse=True)

    # To Avoid repetition of attractions, we collect unique ones based on place_id or name.
    # Return unique attractions (top-rated), up to days*3 if available.
    per_day = 3
    needed = max(1, int(days)) * per_day

    unique: List[Dict[str, Any]] = []
    seen_ids = set()
    seen_names = set()

    for p in filtered:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("place_id") or "").strip().lower()
        name = str(p.get("name") or "").strip().lower()

        # use place_id if available, else fallback to name
        key_ok = (pid and pid not in seen_ids) or (not pid and name and name not in seen_names)
        if not key_ok:
            continue

        if pid:
            seen_ids.add(pid)
        if name:
            seen_names.add(name)

        unique.append(p)
        if len(unique) >= needed:
            break

    return unique



# -------------------------
# Weather tools (Open-Meteo)
# -------------------------
@tool("geocode_city")
def geocode_city(city: str) -> Dict[str, Any]:
    """
    Get latitude/longitude for a city using Open-Meteo Geocoding API (free, no key).
    Returns {name, country, latitude, longitude} or {} if not found.
    """
    q = str(city or "").strip()
    if not q:
        return {}

    url = "https://geocoding-api.open-meteo.com/v1/search"
    try:
        r = requests.get(url, params={"name": q, "count": 1, "language": "en", "format": "json"}, timeout=15)
        r.raise_for_status()
        data = r.json()
        results = data.get("results") or []
        if not results:
            return {}
        top = results[0]
        return {
            "name": top.get("name"),
            "country": top.get("country"),
            "latitude": top.get("latitude"),
            "longitude": top.get("longitude"),
        }
    except Exception:
        return {}


@tool("weather_forecast")
def weather_forecast(latitude: float, longitude: float, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Fetch daily weather using Open-Meteo Forecast API (free, no key).
    Returns list of daily weather dicts between start_date and end_date inclusive.

    Output per day:
      {date, temp_max_c, temp_min_c, precipitation_mm, wind_max_kph, weather_code}
    """
    if latitude is None or longitude is None:
        return []

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": float(latitude),
        "longitude": float(longitude),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,weathercode",
        "timezone": "auto",
        "start_date": str(start_date),
        "end_date": str(end_date),
    }

    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        daily = data.get("daily") or {}
        dates = daily.get("time") or []
        tmax = daily.get("temperature_2m_max") or []
        tmin = daily.get("temperature_2m_min") or []
        rain = daily.get("precipitation_sum") or []
        wind = daily.get("windspeed_10m_max") or []
        code = daily.get("weathercode") or []

        out: List[Dict[str, Any]] = []
        for i, d in enumerate(dates):
            out.append({
                "date": d,
                "temp_max_c": tmax[i] if i < len(tmax) else None,
                "temp_min_c": tmin[i] if i < len(tmin) else None,
                "precipitation_mm": rain[i] if i < len(rain) else None,
                "wind_max_kph": wind[i] if i < len(wind) else None,
                "weather_code": code[i] if i < len(code) else None,
            })
        return out
    except Exception:
        return []


# -------------------------
# Budget estimation tool
# -------------------------
@tool("budget_estimate")
def budget_estimate(
    flights: List[Dict[str, Any]],
    hotels: List[Dict[str, Any]],
    days: int = 3,
    travelers: int = 1,
    preference: str = "balanced",
) -> Dict[str, Any]:
    """
    Estimate total cost = selected flight + selected hotel + local expenses.

    IMPORTANT FIX:
    - We use flights[0] and hotels[0] because   agent already selects them as "top-ranked".
    - This avoids mismatch where UI shows luxury selections but budget uses cheapest values.

    Local expenses heuristic per person per day:
      - budget: 1200
      - balanced: 2000
      - luxury: 3500
    """
    days = max(1, int(days))
    travelers = max(1, int(travelers))
    pref = _norm(preference)

    # ✅ Use the top-ranked flight (same as   agent's selected_flight)
    flight_each = 0.0
    if flights and isinstance(flights, list) and isinstance(flights[0], dict):
        flight_each = _safe_float(flights[0].get("price"), 0.0)

    # Interpret flight price as per traveler (  earlier assumption)
    flight_total = flight_each * travelers

    # ✅ Use the top-ranked hotel (same as   agent's selected_hotel)
    hotel_per_night = 0.0
    if hotels and isinstance(hotels, list) and isinstance(hotels[0], dict):
        hotel_per_night = _safe_float(hotels[0].get("price_per_night"), 0.0)

    # Note:   UI expects 5 nights for Jan 1–Jan 5 (inclusive days).
    #   agent _calc_trip_days() returns inclusive days. So keep hotel_total = per_night * days.
    hotel_total = hotel_per_night * days

    # local expenses
    local_per_person_per_day = 2000.0
    if pref == "budget":
        local_per_person_per_day = 1200.0
    elif pref == "luxury":
        local_per_person_per_day = 3500.0

    local_total = local_per_person_per_day * travelers * days
    total = flight_total + hotel_total + local_total

    # ✅ Return keys that are stable and used by app renderers
    return {
        "flight_each": flight_each,
        "flight_total": flight_total,
        "hotel_per_night": hotel_per_night,
        "hotel_total": hotel_total,
        "local_per_person_per_day": local_per_person_per_day,
        "local_total": local_total,
        "total_estimated_cost": total,
        "assumptions": {
            "flight_price_interpretation": "treated as per traveler",
            "hotel_rooms": "treated as 1 room",
            "local_expense_basis": "heuristic by preference",
        }
    }
