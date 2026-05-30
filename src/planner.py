from __future__ import annotations
from typing import List, Dict, Any
from datetime import datetime, timedelta


def daterange(start_date: str, end_date: str) -> List[str]:
    s = datetime.strptime(start_date, "%Y-%m-%d").date()
    e = datetime.strptime(end_date, "%Y-%m-%d").date()
    dates = []
    d = s
    while d <= e:
        dates.append(d.isoformat())
        d += timedelta(days=1)
    return dates


def build_daywise_plan(dates: List[str], pois: List[Dict[str, Any]], weather: Dict[str, Any]) -> List[Dict[str, Any]]:
    # distribute POIs across days
    day_plans = []
    per_day = max(1, len(pois) // max(1, len(dates)))

    daily = weather.get("daily", {})
    w_dates = daily.get("time", [])
    tmax = daily.get("temperature_2m_max", [])
    tmin = daily.get("temperature_2m_min", [])
    prcp = daily.get("precipitation_sum", [])

    def weather_for(date_str: str) -> Dict[str, Any]:
        if date_str in w_dates:
            i = w_dates.index(date_str)
            return {
                "temp_max_c": tmax[i] if i < len(tmax) else None,
                "temp_min_c": tmin[i] if i < len(tmin) else None,
                "precip_mm": prcp[i] if i < len(prcp) else None,
            }
        return {"note": "No weather returned for this date."}

    idx = 0
    for day_i, date_str in enumerate(dates, start=1):
        todays = pois[idx: idx + per_day]
        idx += per_day
        if day_i == len(dates) and idx < len(pois):
            # last day: include remaining
            todays = pois[(day_i - 1) * per_day:]

        day_plans.append({
            "day": day_i,
            "date": date_str,
            "weather": weather_for(date_str),
            "activities": [
                {"name": p["name"], "type": p["type"], "rating": p["rating"], "place_id": p["place_id"]}
                for p in todays
            ],
        })

    return day_plans
