import json
from typing import Optional

import httpx
from langchain_core.tools import tool


def get_tools(api_base_url: str) -> list:
    """Build LangChain tools that call the FastAPI endpoints."""
    client = httpx.Client(base_url=api_base_url, timeout=30.0)

    @tool
    def search_flights(
        origin: str,
        destination: str,
        max_stops: Optional[int] = None,
        max_price_eur: Optional[float] = None,
        max_co2_kg: Optional[float] = None,
    ) -> str:
        """
        Search available flights between two airports.

        Args:
            origin: IATA departure code (CDG, LHR, JFK, LAX, AMS, FRA, BCN, MAD, DXB, SIN).
            destination: IATA arrival code.
            max_stops: Maximum stops (0 = direct only).
            max_price_eur: Price ceiling in euros.
            max_co2_kg: CO₂ ceiling in kilograms.
        """
        params: dict = {"origin": origin, "destination": destination}
        if max_stops is not None:
            params["max_stops"] = max_stops
        if max_price_eur is not None:
            params["max_price_eur"] = max_price_eur
        if max_co2_kg is not None:
            params["max_co2_kg"] = max_co2_kg
        resp = client.get("/search-flights", params=params)
        resp.raise_for_status()
        flights = resp.json()
        if not flights:
            return "No flights found for the given criteria."
        return json.dumps(flights, indent=2, default=str)

    @tool
    def get_flight_details(flight_id: str) -> str:
        """Get full details for a specific flight by its ID (e.g. AF007, KL836)."""
        resp = client.get(f"/flights/{flight_id}")
        if resp.status_code == 404:
            return f"Flight '{flight_id}' not found."
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2, default=str)

    @tool
    def compare_flights(
        flight_ids: list[str],
        criteria: str = "balanced",
        user_id: Optional[str] = None,
    ) -> str:
        """
        Compare and rank a list of flights by a given criterion.

        Args:
            flight_ids: List of flight IDs to compare.
            criteria: One of price | co2 | comfort | balanced.
            user_id: Optional — uses the user's saved priority if criteria is 'balanced'.
        """
        body: dict = {"flight_ids": flight_ids, "criteria": criteria}
        if user_id:
            body["user_id"] = user_id
        resp = client.post("/flights/compare", json=body)
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2, default=str)

    @tool
    def list_airports() -> str:
        """List all available airports with their IATA codes, cities, and countries."""
        resp = client.get("/airports")
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)

    @tool
    def list_users() -> str:
        """List all registered users with their IDs and names."""
        resp = client.get("/users")
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)

    @tool
    def get_user(user_id: str) -> str:
        """Get a user's profile and current flight preferences by their ID."""
        resp = client.get(f"/users/{user_id}")
        if resp.status_code == 404:
            return f"User '{user_id}' not found."
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)

    @tool
    def get_user_recommendations(
        user_id: str,
        origin: str,
        destination: str,
    ) -> str:
        """
        Get personalized ranked flight recommendations for a user.

        Applies the user's preference filters (max price, max CO₂, max stops)
        and ranks results by their saved priority.

        Args:
            user_id: The user's ID.
            origin: IATA departure code.
            destination: IATA arrival code.
        """
        resp = client.get(
            f"/users/{user_id}/recommendations",
            params={"origin": origin, "destination": destination},
        )
        if resp.status_code == 404:
            return f"User '{user_id}' not found."
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return "No flights match this user's preferences for that route."
        return json.dumps(data, indent=2, default=str)

    @tool
    def update_user_preferences(
        user_id: str,
        priority: str,
        max_price_eur: Optional[float] = None,
        max_co2_kg: Optional[float] = None,
        preferred_cabin: str = "economy",
        max_stops: int = 1,
    ) -> str:
        """
        Update a user's flight preferences.

        Args:
            user_id: The user's ID.
            priority: Main criterion — one of price | co2 | comfort | balanced.
            max_price_eur: Maximum acceptable price in euros.
            max_co2_kg: Maximum acceptable CO₂ in kilograms.
            preferred_cabin: economy | business | first.
            max_stops: Maximum number of stops.
        """
        prefs: dict = {
            "priority": priority,
            "preferred_cabin": preferred_cabin,
            "max_stops": max_stops,
        }
        if max_price_eur is not None:
            prefs["max_price_eur"] = max_price_eur
        if max_co2_kg is not None:
            prefs["max_co2_kg"] = max_co2_kg
        resp = client.put(f"/users/{user_id}/preferences", json=prefs)
        if resp.status_code == 404:
            return f"User '{user_id}' not found."
        resp.raise_for_status()
        return f"Preferences updated: {json.dumps(resp.json(), indent=2)}"

    return [
        search_flights,
        get_flight_details,
        compare_flights,
        list_airports,
        list_users,
        get_user,
        get_user_recommendations,
        update_user_preferences,
    ]
