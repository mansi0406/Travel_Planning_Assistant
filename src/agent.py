# agent.py containing the main planning logic - pipeline: tools → JSON output → Ollama writes readable summary

# GIT HUB LINK : https://github.com/mansi0406/Travel_Planning_Assistant
from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime
import json
from pathlib import Path

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

from tools import (
    flight_search,
    hotel_search,
    attraction_search,
    geocode_city,
    weather_forecast,
    budget_estimate,
)

# Helper functions to process date/time strings
def _only_time_part(s: Any) -> str:
    """
    Extract "HH:MM" from:
    - "HH:MM"
    - "YYYY-MM-DDTHH:MM:SS"
    - "YYYY-MM-DD HH:MM:SS"
    """
    if not s:
        return ""
    t = str(s).strip()
    if "T" in t:
        t = t.split("T")[-1]
    if " " in t:
        t = t.split(" ")[-1]
    return t[:5] if len(t) >= 5 else t


def _compose_trip_datetime(trip_date: str, time_like: Any) -> str:
    """
    Create ISO-like datetime using trip date and the time extracted from dataset.
    Always aligns to user input dates.
    """
    hhmm = _only_time_part(time_like)
    if not trip_date or not hhmm:
        return ""
    return f"{trip_date}T{hhmm}:00"


def _canonicalize_selected_flight(selected_flight: Dict[str, Any], start_date: str, end_date: str) -> Dict[str, Any]:
    """
    ✅ Permanent fix:
    - Always keep dataset time-of-day
    - Always override dataset date to match itinerary dates
    - Expose canonical fields used everywhere in UI
    """
    if not isinstance(selected_flight, dict) or not selected_flight:
        return {}

    dep_iso = _compose_trip_datetime(start_date, selected_flight.get("departure_time"))
    arr_iso = _compose_trip_datetime(end_date, selected_flight.get("arrival_time"))

    # Copy (non-destructive)
    f = dict(selected_flight)

    # Canonical fields (use these everywhere)
    f["departure_datetime"] = dep_iso
    f["arrival_datetime"] = arr_iso

    # Also expose aligned date-only for readability
    f["departure_date"] = start_date
    f["arrival_date"] = end_date

    return f


def _canonicalize_selected_hotel(selected_hotel: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures the hotel dict is always a dict (never None),
    and normalizes key names used by the UI.
    """
    if not isinstance(selected_hotel, dict) or not selected_hotel:
        return {}
    h = dict(selected_hotel)
    # Normalize star key if dataset has float string
    try:
        if "stars" in h:
            h["stars"] = float(h["stars"])
    except Exception:
        pass
    return h

def _build_activity_blocks(day_n: int) -> Dict[str, List[str]]:
    """
    Deterministic variety (no repeats across slots).
    These are generic but realistic for Bangalore and any city.
    """
    morning_templates = [
        "Visit a popular park / botanical garden",
        "Guided heritage walk in the old city area",
        "Temple visit + local breakfast",
        "Monument / museum visit (early hours)",
    ]
    afternoon_templates = [
        "City tour (key landmarks + viewpoints)",
        "Shopping at a local market / mall",
        "Lunch + museum / art gallery",
        "Guided food trail / cafe hopping",
    ]
    evening_templates = [
        "Evening at a lake / park + sunset",
        "Street food + shopping street",
        "Cultural show / live music (if available)",
        "Relax at hotel / spa / leisure",
    ]

    # rotate by day number to avoid repetition
    mi = (day_n - 1) % len(morning_templates)
    ai = (day_n - 1) % len(afternoon_templates)
    ei = (day_n - 1) % len(evening_templates)

    return {
        "morning": [morning_templates[mi]],
        "afternoon": [afternoon_templates[ai]],
        "evening": [evening_templates[ei]],
    }

    """
    Combine trip_date (YYYY-MM-DD) + time (HH:MM) -> ISO-like "YYYY-MM-DDTHH:MM:00"
    """
    hhmm = _only_time_part(time_like)
    if not trip_date or not hhmm:
        return ""
    return f"{trip_date}T{hhmm}:00"



# Using Ollama as the primary LLM instead of OpenAI as API payment and calls are avoided.
'''
Ollama runs local LLMs easily for privacy & speed, 
while LangChain builds complex AI apps by chaining tools; 
they aren't competitors but partners, 
with LangChain orchestrating tasks (like RAG, agents) 
using Ollama as the local model engine for private inference, 
creating powerful, self-contained AI workflows. 

Use LangChain for app structure and Ollama for running models like Llama 3 
or Mistral on the local machine.
'''
from langchain_ollama import ChatOllama

def _generate_fallback_markdown(result_json: Dict[str, Any]) -> str:
    """Generate human-readable markdown without LLM."""
    ts = result_json.get("trip_summary", {})
    flight = result_json.get("selected_flight", {})
    hotel = result_json.get("selected_hotel", {})
    budget = result_json.get("budget", {})
    itinerary = result_json.get("itinerary", {})
    weather = result_json.get("weather", {}).get("daily", [])
    justifications = result_json.get("justifications", {})

    lines = []
    lines.append(f"# 🧳 Trip to {ts.get('destination', 'Unknown')}")
    lines.append("")
    lines.append("## Trip Overview")
    lines.append(f"- **From:** {ts.get('source', 'N/A')}")
    lines.append(f"- **To:** {ts.get('destination', 'N/A')}")
    lines.append(f"- **Dates:** {ts.get('start_date', 'N/A')} → {ts.get('end_date', 'N/A')}")
    lines.append(f"- **Duration:** {ts.get('days', 0)} days")
    lines.append(f"- **Travelers:** {ts.get('travelers', 1)}")
    lines.append(f"- **Preference:** {ts.get('preference', 'balanced').capitalize()}")
    lines.append("")

    if flight:
        lines.append("## ✈️ Selected Flight")
        lines.append(f"- **Airline:** {flight.get('airline', 'N/A')}")
        lines.append(f"- **Route:** {flight.get('from', 'N/A')} → {flight.get('to', 'N/A')}")
        lines.append(f"- **Departure:** {flight.get('departure_datetime', flight.get('departure_time', 'N/A'))}")
        lines.append(f"- **Arrival:** {flight.get('arrival_datetime', flight.get('arrival_time', 'N/A'))}")
        lines.append(f"- **Price:** ₹{int(flight.get('price', 0)):,} per person")
        lines.append("")

    if hotel:
        lines.append("## 🏨 Selected Hotel")
        lines.append(f"- **Name:** {hotel.get('name', 'N/A')}")
        lines.append(f"- **City:** {hotel.get('city', 'N/A')}")
        lines.append(f"- **Stars:** {hotel.get('stars', 0)} ⭐")
        lines.append(f"- **Price/Night:** ₹{int(hotel.get('price_per_night', 0)):,}")
        amenities = hotel.get('amenities', [])
        if amenities:
            lines.append(f"- **Amenities:** {', '.join(amenities)}")
        lines.append("")

    if budget:
        lines.append("## 💰 Budget Breakdown")
        lines.append(f"- **Flight Total:** ₹{int(budget.get('flight_total', 0)):,}")
        lines.append(f"- **Hotel Total:** ₹{int(budget.get('hotel_total', 0)):,}")
        lines.append(f"- **Local Total:** ₹{int(budget.get('local_total', 0)):,}")
        lines.append(f"- **Total Estimated Cost:** ₹{int(budget.get('total_estimated_cost', 0)):,}")
        if budget.get('verdict'):
            lines.append(f"- **Verdict:** {budget.get('verdict')}")
        lines.append("")

    if itinerary:
        lines.append("## 🗓️ Itinerary")
        for day_key, day_plan in itinerary.items():
            lines.append(f"### {day_key}")
            for time_slot, activities in day_plan.items():
                if activities:
                    lines.append(f"**{time_slot.capitalize()}:**")
                    for activity in activities:
                        if isinstance(activity, dict):
                            if activity.get('name'):
                                lines.append(f"- {activity['name']} ({activity.get('type', 'N/A')}) ⭐ {activity.get('rating', 'N/A')}")
                            elif activity.get('activity'):
                                lines.append(f"- {activity['activity']}")
                        else:
                            lines.append(f"- {activity}")
            lines.append("")

    if weather:
        lines.append("## 🌤️ Weather Forecast")
        for wd in weather:
            lines.append(f"- **{wd.get('date', 'N/A')}:** {wd.get('summary', 'N/A')}, {wd.get('temp_max_c', 'N/A')}°C / {wd.get('temp_min_c', 'N/A')}°C")
        lines.append("")

    if justifications:
        lines.append("## ✅ Why Selected This")
        for key, justification in justifications.items():
            lines.append(f"- **{key.capitalize()}:** {justification}")

    return "\n".join(lines)

def _get_chat_ollama(model: str = "llama3.1", temperature: float = 0.2):
    """
    Ollama LLM loader.
    """
    return ChatOllama(model=model, temperature=temperature)


def _calc_trip_days(start_date: str, end_date: str) -> int:
    try:
        d1 = datetime.fromisoformat(str(start_date))
        d2 = datetime.fromisoformat(str(end_date))
        return max(1, (d2 - d1).days + 1)
    except Exception:
        return 1


def _group_itinerary(attractions: List[Dict[str, Any]], days: int, per_day: int = 3) -> Dict[str, Dict[str, Any]]:
    """
    Build day-wise itinerary with Morning/Afternoon/Evening.
    - No blank [] in slots
    - No repetition loops
    - Adds realistic generic activities if attractions are insufficient
    """
    days = max(1, int(days))
    plan: Dict[str, Dict[str, Any]] = {}

    # keep only unique attractions by place_id/name
    uniq: List[Dict[str, Any]] = []
    seen = set()
    for a in attractions or []:
        if not isinstance(a, dict):
            continue
        key = (str(a.get("place_id") or "").strip().lower() or str(a.get("name") or "").strip().lower())
        if not key or key in seen:
            continue
        seen.add(key)
        uniq.append(a)

    idx = 0
    for day in range(1, days + 1):
        # pull up to per_day unique attractions for this day
        todays = uniq[idx: idx + per_day]
        idx += per_day

        # split into slots (at most 1 attraction per slot)
        morning_att = [todays[0]] if len(todays) >= 1 else []
        afternoon_att = [todays[1]] if len(todays) >= 2 else []
        evening_att = [todays[2]] if len(todays) >= 3 else []

        # fill missing slots with deterministic activity blocks
        fillers = _build_activity_blocks(day)

        plan[f"Day {day}"] = {
            "morning": (morning_att if morning_att else [{"activity": fillers["morning"][0]}]),
            "afternoon": (afternoon_att if afternoon_att else [{"activity": fillers["afternoon"][0]}]),
            "evening": (evening_att if evening_att else [{"activity": fillers["evening"][0]}]),
        }

    return plan



def _weather_code_hint(code: Any) -> str:
    """
    Lightweight mapping. (can expand later.)
    """
    try:
        c = int(code)
    except Exception:
        return "Weather info"

    if c == 0:
        return "Clear"
    if c in (1, 2, 3):
        return "Partly cloudy"
    if c in (45, 48):
        return "Fog"
    if c in (51, 53, 55, 61, 63, 65, 80, 81, 82):
        return "Rain"
    if c in (71, 73, 75, 77, 85, 86):
        return "Snow"
    if c in (95, 96, 99):
        return "Thunderstorm"
    return "Mixed conditions"


def plan_trip(inputs: Dict[str, Any], model: str = "llama3.1") -> Dict[str, Any]:
    """
    Deterministic pipeline (no ReAct):
      1) Load flights/hotels/places using JSON tools
      2) Fetch weather via Open-Meteo (geocode + forecast)
      3) Estimate budget with local expenses
      4) Produce structured JSON result
      5) Use Ollama to generate a human-readable summary (also returned in JSON)
    """
    llm = _get_chat_ollama(model=model, temperature=0.2)

    source = (inputs.get("source") or "").strip()
    destination = (inputs.get("destination") or "").strip()
    start_date = inputs.get("start_date") or ""
    end_date = inputs.get("end_date") or ""
    travelers = int(inputs.get("travelers", 1) or 1)
    preference = inputs.get("preference", "balanced") or "balanced"
    min_stars = int(inputs.get("hotel_min_stars", 3) or 3)

    max_hotel_price = float(inputs.get("max_hotel_price", 0.0) or 0.0)
    max_hotel_price = None if max_hotel_price <= 0 else max_hotel_price

    total_budget = float(inputs.get("total_budget", 0.0) or 0.0)
    total_budget = None if total_budget <= 0 else total_budget

    trip_days = _calc_trip_days(start_date, end_date)

    # ---- Tools: JSON datasets
    # Since using tools directly, no need for ReAct style prompting
    # Using invoke() directly on tool instances to get structured outputs for JSON assembly
    flights = flight_search.invoke({
        "source_city": source,
        "destination_city": destination,
        "preference": preference
    }) or []

    # ---- Tools: Hotels and Attractions
    hotels = hotel_search.invoke({
        "destination_city": destination,
        "min_stars": min_stars,
        "max_price_per_night": max_hotel_price,
        "preference": preference
    }) or []


    attractions = attraction_search.invoke({
        "destination": destination,
        "preference": preference,
        "days": trip_days
    }) or []

        # Canonical selections for flight and hotel
    raw_selected_flight = flights[0] if isinstance(flights, list) and flights else {}
    raw_selected_hotel = hotels[0] if isinstance(hotels, list) and hotels else {}

    # Canonicalize once here; UI must always use these canonical fields
    selected_flight = _canonicalize_selected_flight(raw_selected_flight, start_date, end_date)
    selected_hotel = _canonicalize_selected_hotel(raw_selected_hotel)

    itinerary = _group_itinerary(attractions if isinstance(attractions, list) else [], trip_days, per_day=3)
    
    # ---- Tools: Weather (Open-Meteo)
    geo = geocode_city.invoke({"city": destination}) or {}
    weather_days: List[Dict[str, Any]] = []
    if geo and geo.get("latitude") is not None and geo.get("longitude") is not None:
        weather_days = weather_forecast.invoke({
            "latitude": float(geo["latitude"]),
            "longitude": float(geo["longitude"]),
            "start_date": str(start_date),
            "end_date": str(end_date),
        }) or []
        # add friendly summary per day
        for wd in weather_days:
            if isinstance(wd, dict):
                wd["summary"] = _weather_code_hint(wd.get("weather_code"))
        

    # ---- Tools: Budget using .invoke() for structured output
    budget = budget_estimate.invoke({
        "flights": flights if isinstance(flights, list) else [],
        "hotels": hotels if isinstance(hotels, list) else [],
        "days": trip_days,
        "travelers": travelers,
        "preference": preference
    }) or {}
    # If a hotel is selected, force budget hotel fields from selected_hotel
    # This ensures Budget Breakdown ALWAYS reflects Selected Hotel.
    if isinstance(budget, dict) and isinstance(selected_hotel, dict) and selected_hotel:
        hotel_ppn = float(selected_hotel.get("price_per_night") or 0.0)
        if hotel_ppn > 0:
            budget["hotel_per_night"] = hotel_ppn
            budget["hotel_total"] = hotel_ppn * trip_days


    budget_verdict = "Not evaluated"
    if total_budget is not None:
        est = float(budget.get("total_estimated_cost") or 0.0)
        budget_verdict = "Within budget ✅" if est <= total_budget else "Over budget ⚠️"

    # ---- Justifications (deterministic)
    justifications = {
        "flight": "Selected the top-ranked flight based on   preference sorting (price/duration).",
        "hotel": "Selected the top-ranked hotel based on   preference (stars/price) and filters.",
        "attractions": "Selected top-rated attractions and organized ~3 per day.",
        "weather": "Weather fetched from Open-Meteo for the travel dates (if geocoding succeeded).",
        "budget": "Estimated as flight + hotel + local daily expenses (heuristic by preference).",
    }

    # ---- Structured JSON output (core)
    
    # 1)  store attractions explicitly (not only inside itinerary)
    # 2) add derived flight datetime strings aligned to trip dates for UI consistency
    # 3) create structured_highlights that mirrors what   show in sections (no mismatched keys)
    # departure_time/arrival_time may be "HH:MM" OR full ISO datetime.
    
    dep_dt = _compose_trip_datetime(start_date, selected_flight.get("departure_time")) if selected_flight else ""
    arr_dt = _compose_trip_datetime(end_date, selected_flight.get("arrival_time")) if selected_flight else ""

    # Attach derived ISO-like datetime strings for display (non-breaking; original keys stay)
    # Align flight times to trip dates.
    # departure_time/arrival_time may be ISO datetime OR HH:MM.
    if isinstance(selected_flight, dict) and selected_flight:
        selected_flight["_departure_datetime"] = _compose_trip_datetime(start_date, selected_flight.get("departure_time"))
        selected_flight["_arrival_datetime"] = _compose_trip_datetime(end_date, selected_flight.get("arrival_time"))
        selected_flight["_trip_start_date"] = start_date
        selected_flight["_trip_end_date"] = end_date


    # Build a consistent budget dict for UI
    budget_block = {
        **(budget if isinstance(budget, dict) else {}),
        "user_total_budget": total_budget,
        "verdict": budget_verdict,
    }

    structured_highlights = {
        "trip_summary": {
            "source": source,
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "days": trip_days,
            "travelers": travelers,
            "preference": preference,
        },
        "selected_flight": selected_flight,
        "selected_hotel": selected_hotel,
        "attractions": (attractions if isinstance(attractions, list) else []),
        "budget_breakdown": budget_block,
        "why_selected_this": justifications,
    }

    result_json: Dict[str, Any] = {
        "trip_summary": {
            "source": source,
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "days": trip_days,
            "travelers": travelers,
            "preference": preference,
            "hotel_min_stars": min_stars,
            "max_hotel_price_per_night": max_hotel_price,
            "user_total_budget": total_budget,
        },
        "selected_flight": selected_flight,
        "selected_hotel": selected_hotel,

        # ✅ store attractions directly (so app.py does not show "No attractions found")
        "attractions": (attractions if isinstance(attractions, list) else []),

        "weather": {
            "geocoding": geo,
            "daily": weather_days,
        },
        "itinerary": itinerary,

        # Keep budget under the same name "budget"  app still works
        "budget": budget_block,

        "justifications": justifications,

        #  structured_highlights used by UI to avoid mismatch
        "structured_highlights": structured_highlights,
    }

    # ---- Generate human-readable output (fallback if LLM fails)
    try:
        prompt = f"""
 An expert travel planner.

Using the JSON data below, write a clean human-readable trip plan in Markdown.

Must include:
1) Trip summary
2) Flight selected (airline, from, to, departure_time, arrival_time, price)
3) Hotel selected (name, stars, price_per_night, amenities)
4) Day-wise itinerary (Morning / Afternoon / Evening) using the itinerary list
5) Weather for each day (use weather.daily; show summary + max/min temp)
6) Budget breakdown (flight_total, hotel_total, local_total, total_estimated_cost) and budget_verdict
7) Brief "Why selected this" (use justifications)

JSON:
{json.dumps(result_json, indent=2)}
""".strip()

        resp = llm.invoke(prompt, timeout=60)
        result_json["human_readable_markdown"] = getattr(resp, "content", str(resp))
    except Exception as e:
        # Fallback: Create human-readable output directly without LLM
        result_json["human_readable_markdown"] = _generate_fallback_markdown(result_json)

    return result_json

# Function to save output JSON to a file
def save_itinerary(itinerary: Dict[str, Any], filename: str) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = OUTPUT_DIR / f"Itinerary_{timestamp}.json"
    txt_path = OUTPUT_DIR / f"Itinerary_{timestamp}.txt"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(itinerary, f, indent=2)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(itinerary.get("human_readable_markdown", ""))

        