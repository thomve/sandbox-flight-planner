from fastapi import APIRouter, HTTPException, Query

from .data import AIRPORTS, FLIGHTS, USERS
from .models import Airport, CompareRequest, Flight, FlightRanking, User, UserPreferences

router = APIRouter()


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _norm_lower(val: float, lo: float, hi: float) -> float:
    """Normalize so that a lower raw value gives a higher score (0–1)."""
    if hi == lo:
        return 1.0
    return 1.0 - (val - lo) / (hi - lo)


def _norm_higher(val: float, lo: float, hi: float) -> float:
    """Normalize so that a higher raw value gives a higher score (0–1)."""
    if hi == lo:
        return 1.0
    return (val - lo) / (hi - lo)


_WEIGHTS: dict[str, dict[str, float]] = {
    "price":   {"price": 0.70, "co2": 0.15, "comfort": 0.15},
    "co2":     {"price": 0.15, "co2": 0.70, "comfort": 0.15},
    "comfort": {"price": 0.15, "co2": 0.15, "comfort": 0.70},
    "balanced":{"price": 0.33, "co2": 0.33, "comfort": 0.34},
}


def _rank_flights(flights: list[Flight], criteria: str) -> list[FlightRanking]:
    if not flights:
        return []

    weights = _WEIGHTS.get(criteria, _WEIGHTS["balanced"])

    prices   = [f.price_eur      for f in flights]
    co2s     = [f.co2_kg         for f in flights]
    comforts = [f.comfort_score  for f in flights]

    rankings: list[FlightRanking] = []
    for f in flights:
        price_s   = _norm_lower(f.price_eur,     min(prices),   max(prices))
        co2_s     = _norm_lower(f.co2_kg,         min(co2s),     max(co2s))
        comfort_s = _norm_higher(f.comfort_score, min(comforts), max(comforts))

        score = (
            weights["price"]   * price_s
            + weights["co2"]   * co2_s
            + weights["comfort"] * comfort_s
        )

        reasons: list[str] = []
        if price_s   >= 0.8: reasons.append(f"Best price in selection: €{f.price_eur:.0f}")
        if co2_s     >= 0.8: reasons.append(f"Lowest CO₂ in selection: {f.co2_kg:.0f} kg")
        if comfort_s >= 0.8: reasons.append(f"Highest comfort: {f.comfort_score}/10")
        if f.stops == 0:     reasons.append("Direct flight")
        if not reasons:      reasons.append("Good overall balance")

        rankings.append(FlightRanking(flight=f, score=round(score, 3), reasons=reasons))

    return sorted(rankings, key=lambda r: r.score, reverse=True)


# ---------------------------------------------------------------------------
# Airport routes
# ---------------------------------------------------------------------------

@router.get("/airports", response_model=list[Airport], tags=["airports"])
def list_airports():
    """List all available airports."""
    return list(AIRPORTS.values())


@router.get("/airports/{code}", response_model=Airport, tags=["airports"])
def get_airport(code: str):
    """Get a single airport by IATA code."""
    airport = AIRPORTS.get(code.upper())
    if not airport:
        raise HTTPException(status_code=404, detail=f"Airport '{code}' not found.")
    return airport


# ---------------------------------------------------------------------------
# Flight routes
# ---------------------------------------------------------------------------

@router.get("/search-flights", response_model=list[Flight], tags=["flights"])
def search_flights(
    origin: str = Query(..., description="IATA code of departure airport"),
    destination: str = Query(..., description="IATA code of arrival airport"),
    max_stops: int | None = Query(None, description="Maximum number of stops (0 = direct only)"),
    max_price_eur: float | None = Query(None, description="Maximum price in EUR"),
    max_co2_kg: float | None = Query(None, description="Maximum CO₂ emissions in kg"),
    cabin_class: str | None = Query(None, description="economy | business | first"),
):
    """Search flights between two airports with optional filters."""
    results = [
        f for f in FLIGHTS.values()
        if f.origin == origin.upper() and f.destination == destination.upper()
    ]
    if max_stops is not None:
        results = [f for f in results if f.stops <= max_stops]
    if max_price_eur is not None:
        results = [f for f in results if f.price_eur <= max_price_eur]
    if max_co2_kg is not None:
        results = [f for f in results if f.co2_kg <= max_co2_kg]
    if cabin_class:
        results = [f for f in results if f.cabin_class == cabin_class]
    return results


@router.get("/flights/{flight_id}", response_model=Flight, tags=["flights"])
def get_flight(flight_id: str):
    """Get full details for a specific flight."""
    flight = FLIGHTS.get(flight_id.upper())
    if not flight:
        raise HTTPException(status_code=404, detail=f"Flight '{flight_id}' not found.")
    return flight


@router.post("/flights/compare", response_model=list[FlightRanking], tags=["flights"])
def compare_flights(request: CompareRequest):
    """
    Compare and rank a set of flights.

    If `user_id` is provided and `criteria` is not explicitly set, the user's
    saved priority is used as the ranking criterion.
    """
    flights: list[Flight] = []
    for fid in request.flight_ids:
        flight = FLIGHTS.get(fid.upper())
        if not flight:
            raise HTTPException(status_code=404, detail=f"Flight '{fid}' not found.")
        flights.append(flight)

    criteria = request.criteria
    if request.user_id:
        user = USERS.get(request.user_id)
        if user and request.criteria == "balanced":
            criteria = user.preferences.priority

    return _rank_flights(flights, criteria)


# ---------------------------------------------------------------------------
# User routes
# ---------------------------------------------------------------------------

@router.get("/users", response_model=list[User], tags=["users"])
def list_users():
    """List all registered users."""
    return list(USERS.values())


@router.get("/users/{user_id}", response_model=User, tags=["users"])
def get_user(user_id: str):
    """Get a user's full profile including preferences."""
    user = USERS.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found.")
    return user


@router.get("/users/{user_id}/preferences", response_model=UserPreferences, tags=["users"])
def get_user_preferences(user_id: str):
    """Get a user's flight preferences."""
    user = USERS.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found.")
    return user.preferences


@router.put("/users/{user_id}/preferences", response_model=UserPreferences, tags=["users"])
def update_user_preferences(user_id: str, preferences: UserPreferences):
    """Update a user's flight preferences."""
    user = USERS.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found.")
    USERS[user_id] = User(**{**user.model_dump(), "preferences": preferences.model_dump()})
    return preferences


@router.get("/users/{user_id}/recommendations", response_model=list[FlightRanking], tags=["users"])
def get_user_recommendations(
    user_id: str,
    origin: str = Query(..., description="IATA code of departure airport"),
    destination: str = Query(..., description="IATA code of arrival airport"),
):
    """
    Return personalized ranked flight recommendations for a user.

    Applies the user's max_stops, max_price_eur, and max_co2_kg filters
    before ranking by their saved priority.
    """
    user = USERS.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found.")

    prefs = user.preferences
    flights = [
        f for f in FLIGHTS.values()
        if f.origin == origin.upper() and f.destination == destination.upper()
    ]

    if prefs.max_stops is not None:
        flights = [f for f in flights if f.stops <= prefs.max_stops]
    if prefs.max_price_eur is not None:
        flights = [f for f in flights if f.price_eur <= prefs.max_price_eur]
    if prefs.max_co2_kg is not None:
        flights = [f for f in flights if f.co2_kg <= prefs.max_co2_kg]

    return _rank_flights(flights, prefs.priority)
