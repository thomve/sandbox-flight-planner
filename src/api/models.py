from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Airport(BaseModel):
    code: str
    name: str
    city: str
    country: str


class Flight(BaseModel):
    id: str
    airline: str
    flight_number: str
    origin: str
    destination: str
    departure: datetime
    arrival: datetime
    duration_minutes: int
    stops: int
    price_eur: float
    co2_kg: float
    comfort_score: float  # 1–10
    available_seats: int
    cabin_class: Literal["economy", "business", "first"]


class UserPreferences(BaseModel):
    priority: Literal["price", "co2", "comfort", "balanced"]
    max_price_eur: float | None = None
    max_co2_kg: float | None = None
    preferred_cabin: Literal["economy", "business", "first"] = "economy"
    max_stops: int = 1


class User(BaseModel):
    id: str
    name: str
    email: str
    preferences: UserPreferences


class FlightRanking(BaseModel):
    flight: Flight
    score: float  # 0–1, higher is better
    reasons: list[str]


class CompareRequest(BaseModel):
    flight_ids: list[str]
    criteria: Literal["price", "co2", "comfort", "balanced"] = "balanced"
    user_id: str | None = None
