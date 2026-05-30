from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict


class FlightOption(BaseModel):
    flight_id: str
    airline: str
    from_city: str = Field(alias="from")
    to_city: str = Field(alias="to")
    departure_time: str
    arrival_time: str
    price: int


class HotelOption(BaseModel):
    hotel_id: str
    name: str
    city: str
    stars: int
    price_per_night: int
    amenities: List[str]


class PlaceOption(BaseModel):
    place_id: str
    name: str
    city: str
    type: str
    rating: float


class TripRequest(BaseModel):
    source_city: str
    destination_city: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    budget_in_inr: Optional[int] = None
    travelers: int = 1
    hotel_min_stars: int = 3
    hotel_max_price_per_night: Optional[int] = None
    poi_types: List[str] = Field(default_factory=lambda: ["fort", "temple", "museum", "market", "park", "beach", "lake", "monument"])
    preference: Literal["cheapest", "fastest", "balanced"] = "balanced"
    daily_local_expense_per_person: int = 900  # simple default


class DayPlan(BaseModel):
    day: int
    date: str
    weather: Dict[str, object]
    activities: List[Dict[str, object]]


class Itinerary(BaseModel):
    trip_summary: Dict[str, object]
    selected_flight: Dict[str, object]
    selected_hotel: Dict[str, object]
    day_wise_plan: List[DayPlan]
    budget_breakdown: Dict[str, object]
    justification: List[str] = []
