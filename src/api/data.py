from datetime import datetime

from .models import Airport, Flight, User, UserPreferences

AIRPORTS: dict[str, Airport] = {
    "CDG": Airport(code="CDG", name="Charles de Gaulle", city="Paris", country="France"),
    "LHR": Airport(code="LHR", name="Heathrow", city="London", country="United Kingdom"),
    "JFK": Airport(code="JFK", name="John F. Kennedy International", city="New York", country="USA"),
    "LAX": Airport(code="LAX", name="Los Angeles International", city="Los Angeles", country="USA"),
    "AMS": Airport(code="AMS", name="Amsterdam Schiphol", city="Amsterdam", country="Netherlands"),
    "FRA": Airport(code="FRA", name="Frankfurt Airport", city="Frankfurt", country="Germany"),
    "BCN": Airport(code="BCN", name="Barcelona El Prat", city="Barcelona", country="Spain"),
    "MAD": Airport(code="MAD", name="Madrid Barajas", city="Madrid", country="Spain"),
    "DXB": Airport(code="DXB", name="Dubai International", city="Dubai", country="UAE"),
    "SIN": Airport(code="SIN", name="Singapore Changi", city="Singapore", country="Singapore"),
}

FLIGHTS: dict[str, Flight] = {
    # CDG → JFK  (4 options: varied price/CO2/comfort trade-offs)
    "AF007": Flight(
        id="AF007", airline="Air France", flight_number="AF 007",
        origin="CDG", destination="JFK",
        departure=datetime(2026, 6, 15, 10, 30), arrival=datetime(2026, 6, 15, 13, 0),
        duration_minutes=510, stops=0,
        price_eur=650.0, co2_kg=390.0, comfort_score=8.5, available_seats=42,
        cabin_class="economy",
    ),
    "DL264": Flight(
        id="DL264", airline="Delta Air Lines", flight_number="DL 264",
        origin="CDG", destination="JFK",
        departure=datetime(2026, 6, 15, 13, 45), arrival=datetime(2026, 6, 15, 16, 30),
        duration_minutes=525, stops=0,
        price_eur=580.0, co2_kg=420.0, comfort_score=7.8, available_seats=28,
        cabin_class="economy",
    ),
    "BA175X": Flight(
        id="BA175X", airline="British Airways", flight_number="BA 175",
        origin="CDG", destination="JFK",
        departure=datetime(2026, 6, 15, 8, 0), arrival=datetime(2026, 6, 15, 14, 30),
        duration_minutes=690, stops=1,
        price_eur=490.0, co2_kg=480.0, comfort_score=7.5, available_seats=15,
        cabin_class="economy",
    ),
    "BF165": Flight(
        id="BF165", airline="French Bee", flight_number="BF 165",
        origin="CDG", destination="JFK",
        departure=datetime(2026, 6, 15, 22, 0), arrival=datetime(2026, 6, 16, 1, 15),
        duration_minutes=555, stops=0,
        price_eur=320.0, co2_kg=460.0, comfort_score=5.5, available_seats=85,
        cabin_class="economy",
    ),
    # CDG → BCN  (3 options: low-cost vs comfort)
    "AF1601": Flight(
        id="AF1601", airline="Air France", flight_number="AF 1601",
        origin="CDG", destination="BCN",
        departure=datetime(2026, 6, 15, 7, 10), arrival=datetime(2026, 6, 15, 9, 0),
        duration_minutes=110, stops=0,
        price_eur=180.0, co2_kg=82.0, comfort_score=7.0, available_seats=31,
        cabin_class="economy",
    ),
    "VY8399": Flight(
        id="VY8399", airline="Vueling", flight_number="VY 8399",
        origin="CDG", destination="BCN",
        departure=datetime(2026, 6, 15, 14, 20), arrival=datetime(2026, 6, 15, 16, 15),
        duration_minutes=115, stops=0,
        price_eur=89.0, co2_kg=88.0, comfort_score=6.0, available_seats=67,
        cabin_class="economy",
    ),
    "FR1501": Flight(
        id="FR1501", airline="Ryanair", flight_number="FR 1501",
        origin="CDG", destination="BCN",
        departure=datetime(2026, 6, 15, 6, 5), arrival=datetime(2026, 6, 15, 8, 10),
        duration_minutes=125, stops=0,
        price_eur=45.0, co2_kg=95.0, comfort_score=4.5, available_seats=120,
        cabin_class="economy",
    ),
    # AMS → SIN  (3 options: premium vs eco vs layover luxury)
    "KL836": Flight(
        id="KL836", airline="KLM", flight_number="KL 836",
        origin="AMS", destination="SIN",
        departure=datetime(2026, 6, 15, 11, 40), arrival=datetime(2026, 6, 16, 6, 0),
        duration_minutes=740, stops=0,
        price_eur=780.0, co2_kg=640.0, comfort_score=8.0, available_seats=22,
        cabin_class="economy",
    ),
    "SQ321": Flight(
        id="SQ321", airline="Singapore Airlines", flight_number="SQ 321",
        origin="AMS", destination="SIN",
        departure=datetime(2026, 6, 15, 22, 10), arrival=datetime(2026, 6, 16, 17, 5),
        duration_minutes=775, stops=0,
        price_eur=920.0, co2_kg=610.0, comfort_score=9.5, available_seats=8,
        cabin_class="economy",
    ),
    "EK146": Flight(
        id="EK146", airline="Emirates", flight_number="EK 146",
        origin="AMS", destination="SIN",
        departure=datetime(2026, 6, 15, 14, 20), arrival=datetime(2026, 6, 16, 14, 30),
        duration_minutes=1030, stops=1,
        price_eur=650.0, co2_kg=750.0, comfort_score=8.8, available_seats=45,
        cabin_class="economy",
    ),
    # FRA → LAX  (2 options)
    "LH456": Flight(
        id="LH456", airline="Lufthansa", flight_number="LH 456",
        origin="FRA", destination="LAX",
        departure=datetime(2026, 6, 15, 10, 55), arrival=datetime(2026, 6, 15, 13, 40),
        duration_minutes=705, stops=0,
        price_eur=710.0, co2_kg=540.0, comfort_score=8.2, available_seats=19,
        cabin_class="economy",
    ),
    "UA902": Flight(
        id="UA902", airline="United Airlines", flight_number="UA 902",
        origin="FRA", destination="LAX",
        departure=datetime(2026, 6, 15, 15, 30), arrival=datetime(2026, 6, 15, 17, 30),
        duration_minutes=720, stops=0,
        price_eur=590.0, co2_kg=570.0, comfort_score=7.0, available_seats=33,
        cabin_class="economy",
    ),
}

USERS: dict[str, User] = {
    "user-001": User(
        id="user-001", name="Alice Martin", email="alice.martin@example.com",
        preferences=UserPreferences(
            priority="co2",
            max_co2_kg=430.0,
            preferred_cabin="economy",
            max_stops=0,
        ),
    ),
    "user-002": User(
        id="user-002", name="Bob Dupont", email="bob.dupont@example.com",
        preferences=UserPreferences(
            priority="price",
            max_price_eur=500.0,
            preferred_cabin="economy",
            max_stops=2,
        ),
    ),
    "user-003": User(
        id="user-003", name="Carol Smith", email="carol.smith@example.com",
        preferences=UserPreferences(
            priority="comfort",
            preferred_cabin="business",
            max_stops=1,
        ),
    ),
    "user-004": User(
        id="user-004", name="David Chen", email="david.chen@example.com",
        preferences=UserPreferences(
            priority="balanced",
            max_price_eur=800.0,
            preferred_cabin="economy",
            max_stops=1,
        ),
    ),
}
