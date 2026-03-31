from dataclasses import dataclass
from typing import Annotated


@dataclass
class Airline:
    code: str
    name: str


@dataclass
class Alliance:
    code: str
    name: str


@dataclass
class JsMetadata:
    airlines: list[Airline]
    alliances: list[Alliance]


@dataclass
class Airport:
    name: str
    code: str


@dataclass
class SimpleDatetime:
    timestamp: str  # ISO 8601


@dataclass
class SingleFlight:
    from_airport: Airport
    to_airport: Airport
    departure: SimpleDatetime
    arrival: SimpleDatetime
    duration: Annotated[int, "(minutes)"]
    plane_type: str
    airline_code: str
    flight_number: str
    travel_class: str
    operating_airline: str
    overnight: bool
    layover_duration: int | None = None
    airport_change: bool = False


@dataclass
class CarbonEmission:
    typical_on_route: Annotated[int, "(grams)"]
    emission: Annotated[int, "(grams)"]


@dataclass
class Baggage:
    carry_on: int
    checked_bag: int


@dataclass
class Flights:
    price: int
    airlines: list[str]
    airline_codes: list[str]
    flights: list[SingleFlight]
    carbon: CarbonEmission
    total_duration: int
    stops: int
    self_transfer: bool
    price_trend: str | None = None
    baggage: Baggage | None = None
