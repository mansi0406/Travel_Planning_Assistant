# app.py - Streamlit UI for the Agentic Travel Assistant using Ollama + JSON tools + weather
# ✅ Shows: Inputs → Human-readable output → Structured highlights → Raw JSON
# ✅ NEW: Saves outputs into ./outputs as JSON + TXT and also provides download buttons
# NOTE: Existing functionality is NOT disturbed; we only add output persistence + downloads.

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

import streamlit as st
from agent import plan_trip


# ------------------------------------------------------------
# Streamlit Page Config
# ------------------------------------------------------------
st.set_page_config(page_title="Agentic AI Travel Planner", layout="wide")
st.title("🧳 Agentic AI Travel Planning Assistant")


# ------------------------------------------------------------
# Output folder helpers (NEW)
# ------------------------------------------------------------
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def _safe_filename(text: str) -> str:
    """Make a safe filename from any string (no spaces/special chars issues)."""
    text = text.strip() if text else "trip"
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in text)


def save_plan_outputs(plan: dict, trip_key: str) -> tuple[Path, Path]:
    """
    Save the generated plan into outputs/ as:
    1) JSON file (full structured output)
    2) TXT file  (human-readable markdown summary)

    Returns: (json_path, txt_path)
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"{_safe_filename(trip_key)}_{ts}"

    json_path = OUTPUT_DIR / f"{base}.json"
    txt_path = OUTPUT_DIR / f"{base}.txt"

    # 1) Save JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

    # 2) Save Human readable text
    # Prefer   existing markdown field, fallback to a JSON pretty dump
    human_text = plan.get("human_readable_markdown")
    if not human_text:
        human_text = json.dumps(plan, indent=2, ensure_ascii=False)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(human_text)

    return json_path, txt_path


# ---------------------------------------------------------------
# Helper functions for text outputs instead of raw JSON
# ---------------------------------------------------------------

from datetime import datetime

def _na(x, empty="Not specified"):
    return empty if x is None or x == "" or x == [] or x == {} else x

def _fmt_dt(s: str) -> str:
    """Format ISO datetime string nicely. Keeps original if parsing fails."""
    if not s:
        return "Not specified"
    try:
        return datetime.fromisoformat(s).strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return str(s)

def _fmt_money(x) -> str:
    if x in (None, ""):
        return "Not specified"
    try:
        return f"₹{int(float(x)):,}"
    except Exception:
        return str(x)

def render_trip_summary_text(ts: dict) -> str:
    return f"""
✈️ **Trip Overview**
• **From:** {_na(ts.get("source"))}
• **To:** {_na(ts.get("destination"))}
• **Travel Dates:** {_na(ts.get("start_date"))} → {_na(ts.get("end_date"))}
• **Duration:** {_na(ts.get("days"))} day(s)
• **Travelers:** {_na(ts.get("travelers"))}
• **Preference:** {str(_na(ts.get("preference"))).capitalize()}

🏨 **Hotel Preferences**
• **Minimum Rating:** {_na(ts.get("hotel_min_stars"))} ⭐
• **Max Price/Night:** {_fmt_money(ts.get("max_hotel_price_per_night"))}

💰 **Budget**
• **Total Budget:** {_fmt_money(ts.get("user_total_budget"))}
""".strip()


def render_flight_text(f: dict) -> str:
    if not f:
        return "✈️ No matching flight found for criteria."

    #  using canonical datetime fields from agent.py
    dep = f.get("departure_datetime") or ""
    arr = f.get("arrival_datetime") or ""

    return f"""
✈️ **Selected Flight**
• **Flight ID:** {_na(f.get("flight_id"))}
• **Airline:** {_na(f.get("airline"))}
• **Route:** {_na(f.get("from"))} → {_na(f.get("to"))}
• **Departure:** {_fmt_dt(dep)}
• **Arrival:** {_fmt_dt(arr)}
• **Price:** {_fmt_money(f.get("price"))} per person
""".strip()


def render_hotel_text(h: dict) -> str:
    if not h:
        return "🏨 No matching hotel found for   criteria."

    amenities = ", ".join(h.get("amenities", [])) or "Not specified"

    return f"""
🏨 **Selected Hotel**
• **Hotel ID:** {_na(h.get("hotel_id"))}
• **Name:** {_na(h.get("name"))}
• **City:** {_na(h.get("city"))}
• **Stars:** {_na(h.get("stars"))} ⭐
• **Price/Night:** {_fmt_money(h.get("price_per_night"))}
• **Amenities:** {amenities}
""".strip()


def render_places_text(attractions) -> str:
    """
    attractions might be a list[dict] (from places.json) or empty.
    Each place uses keys: place_id, name, city, type, rating
    """
    if not attractions:
        return "📍 No attractions found."
    lines = ["📍 **Top Attractions**"]
    for p in attractions[:8]:  # show top 8 to keep it neat
        lines.append(
            f"• **{_na(p.get('name'))}** ({_na(p.get('type'))}) — ⭐ {_na(p.get('rating'))}"
        )
    return "\n".join(lines)


def render_budget_text(b: dict) -> str:
    if not b:
        return "💰 Budget details not available."

    # correct keys from tools.py and agent override
    return f"""
💰 **Budget Breakdown**
• **Flight Total:** {_fmt_money(b.get("flight_total"))}
• **Hotel Total:** {_fmt_money(b.get("hotel_total"))} ({_fmt_money(b.get("hotel_per_night"))} per night)
• **Local Total:** {_fmt_money(b.get("local_total"))} ({_fmt_money(b.get("local_per_person_per_day"))} per person/day)
• **Total Estimated Cost:** {_fmt_money(b.get("total_estimated_cost"))}
• **User Budget:** {_fmt_money(b.get("user_total_budget"))}
• **Verdict:** {_na(b.get("verdict"))}
""".strip()

def render_itinerary_text(it) -> str:
    if not it:
        return "🗓️ Itinerary not available."

    # If   itinerary is list of day objects
    if isinstance(it, list):
        lines = ["🗓️ **Itinerary (Day-wise)**"]
        for d in it:
            day = _na(d.get("day"), "")
            title = _na(d.get("title"), "")
            lines.append(f"\n**Day {day}: {title}**".strip())
            for a in (d.get("activities") or []):
                lines.append(f"• {a}")
        return "\n".join(lines).strip()

    # If   itinerary is dict with "days"
    if isinstance(it, dict) and isinstance(it.get("days"), list):
        return render_itinerary_text(it["days"])

    # Fallback (unknown structure)
    if isinstance(it, dict):
        return "🗓️ **Itinerary (Day-wise)**\n" + "\n".join([f"• **{k}**: {v}" for k, v in it.items()])

    return f"🗓️ **Itinerary**\n• {it}"





# ------------------------------------------------------------
# Sidebar Inputs
# ------------------------------------------------------------
with st.sidebar:
    st.subheader("Trip Inputs")

    source = st.text_input("Source (From city)", value="Chennai")
    destination = st.text_input("Destination (To city)", value="Bangalore")

    start_date = st.date_input("Start date")
    end_date = st.date_input("End date")

    travelers = st.number_input("Travelers", min_value=1, max_value=20, value=1, step=1)

    preference = st.selectbox(
        "Preference",
        ["budget", "balanced", "luxury", "fastest"],  # added fastest
        index=1
    )

    hotel_min_stars = st.slider("Hotel min stars", min_value=1, max_value=5, value=3)
    max_hotel_price = st.number_input("Max hotel price/night (optional)", min_value=0, value=0, step=500)
    total_budget = st.number_input("Total budget (optional)", min_value=0, value=0, step=1000)

    model = st.text_input("Ollama model", value="llama3.1", disabled=True) # This makes the model field uneditable

    # This is   existing button (we reuse it as-is)
    run_btn = st.button("Plan my trip", use_container_width=True)


# ------------------------------------------------------------
# Input validation (existing)
# ------------------------------------------------------------
if end_date < start_date:
    st.warning("End date should be on/after start date.")


# ------------------------------------------------------------
# Layout columns
# ------------------------------------------------------------
col1, col2 = st.columns([1.2, 1])


# ------------------------------------------------------------
# Right column: Show inputs used (existing)
# ------------------------------------------------------------
with col2:
    st.markdown("#### 🔎 Inputs Used")
    st.write({
        "source": source.strip(),
        "destination": destination.strip(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "travelers": int(travelers),
        "preference": preference,
        "hotel_min_stars": int(hotel_min_stars),
        "max_hotel_price": float(max_hotel_price) if max_hotel_price else None,
        "total_budget": float(total_budget) if total_budget else None,
        "ollama_model": model,
    })


# ------------------------------------------------------------
# Left column: Generate plan + display outputs (existing + NEW persistence)
# ------------------------------------------------------------
with col1:
    st.markdown("#### ✅ Planner Output")

    # IMPORTANT:
    # We only run the planner when the button is clicked AND dates are valid.
    if run_btn and end_date >= start_date:
        # Build the inputs payload exactly as before (no changes)
        inputs = {
            "source": source.strip(),
            "destination": destination.strip(),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "travelers": int(travelers),
            "preference": preference,
            "hotel_min_stars": int(hotel_min_stars),
            "max_hotel_price": float(max_hotel_price),
            "total_budget": float(total_budget),
        }

        # Run agent planner
        with st.spinner("Planning using JSON tools + Open-Meteo weather + Ollama..."):
            result = plan_trip(inputs, model=model)

        # ----------------------------
        # NEW: Save outputs to outputs/
        # ----------------------------
        trip_key = f"{source}_{destination}_{start_date.isoformat()}_{end_date.isoformat()}"
        json_path, txt_path = save_plan_outputs(result, trip_key=trip_key)

        # Store in session_state to persist display across reruns (useful in Streamlit)
        st.session_state["last_result"] = result
        st.session_state["last_json_path"] = str(json_path)
        st.session_state["last_txt_path"] = str(txt_path)

        # Confirmation message (NEW)
        st.success(f"Saved outputs ✅  JSON: {json_path.name} | TXT: {txt_path.name}")

    # ------------------------------------------------------------
    # Display results from session state if available (prevents disappearing)
    # ------------------------------------------------------------
    if "last_result" in st.session_state:
        result = st.session_state["last_result"]

        # 1) Human readable output (existing)
        st.markdown(result.get("human_readable_markdown", "No output generated."))

        # 2) Friendly structured sections (existing)
        st.divider()
        st.markdown("### 📌 Structured Highlights")
        # ✅ NEW: show deterministic structured highlights (no missing hotel/attractions/budget)
        sh = result.get("structured_highlights", {})
        if sh:
            with st.expander("✅ View Structured Highlights"):
                st.code(json.dumps(sh, indent=2, ensure_ascii=False), language="json")

        ts = result.get("trip_summary", {})

        st.subheader("Trip Summary")
        st.markdown(render_trip_summary_text(ts))

        st.subheader("Selected Flight")
        st.markdown(render_flight_text(result.get("selected_flight", {})))

        st.subheader("Selected Hotel")
        st.markdown(render_hotel_text(result.get("selected_hotel", {})))

        # Optional: if the agent returns attractions list as result["attractions"]
        st.subheader("Attractions")
        st.markdown(render_places_text(result.get("attractions", [])))

        st.subheader("Budget Breakdown")
        st.markdown(render_budget_text(result.get("budget", {})))

        st.subheader("Itinerary (Day-wise)")
        st.markdown(render_itinerary_text(result.get("itinerary", {})))

        # To display weather daily data nicely
        st.subheader("Weather (Daily)")
        weather = (result.get("weather") or {}).get("daily", [])
        if weather:
            st.write(weather)
        else:
            st.info("Weather not available (geocoding or API issue).")        

        # 3) Raw JSON (existing)
        with st.expander("📦 View Raw JSON Output"):
            st.code(json.dumps(result, indent=2, ensure_ascii=False), language="json")

        # ----------------------------
        # NEW: Download buttons
        # ----------------------------
        st.divider()
        st.markdown("### ⬇️ Download Outputs")

        # Download JSON directly from current result (no file read required)
        st.download_button(
            "Download JSON",
            data=json.dumps(result, indent=2, ensure_ascii=False),
            file_name=Path(st.session_state.get("last_json_path", "itinerary.json")).name,
            mime="application/json",
            use_container_width=True
        )

        # Download TXT from the markdown summary (no file read required)
        st.download_button(
            "Download Text Summary",
            data=(result.get("human_readable_markdown") or ""),
            file_name=Path(st.session_state.get("last_txt_path", "itinerary.txt")).name,
            mime="text/plain",
            use_container_width=True
        )
