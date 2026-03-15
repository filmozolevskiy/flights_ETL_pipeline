# Bronze Layer Data Dictionary — Google Flights API (RapidAPI)

This document maps the key fields from the RapidAPI Google Flights API response. The raw JSON is stored as-is in the Bronze S3 layer for immutable history and reprocessing.

**Source:** RapidAPI Hub — Google Flights (`/api/v1/searchFlights`)  
**Sample:** `docs/sample_api_response.json`

---

## Root-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | boolean | Indicates whether the API request succeeded. |
| `message` | string | Human-readable status (e.g., `"Success"`). |
| `timestamp` | number | Unix timestamp (milliseconds) of the response. |

---

## `data` Object

| Field | Type | Description |
|-------|------|-------------|
| `data.itineraries` | object | Container for flight search results. |
| `data.priceHistory` | object | Price history and summary for the route. |

---

## `data.itineraries` — Flight Options

| Field | Type | Description |
|-------|------|-------------|
| `topFlights` | array | Top-ranked flight options (best/cheap). |
| `otherFlights` | array | Additional flight options. |

---

## Itinerary Item (each element in `topFlights` / `otherFlights`)

| Field | Type | Description |
|-------|------|-------------|
| `departure_time` | string | Formatted departure time (e.g., `"15-04-2026 11:00 PM"`). |
| `arrival_time` | string | Formatted arrival time. |
| `duration` | object | `{ raw: number, text: string }` — total trip duration in minutes and human-readable form. |
| `flights` | array | Array of flight legs (segments) in the itinerary. |
| `price` | number | Price in the requested currency (e.g., USD). |
| `stops` | number | Number of stops (0 = direct). |
| `layovers` | array \| null | Layover details; `null` for direct flights. |
| `bags` | object | `{ carry_on: number, checked: number }` — bag allowance. |
| `carbon_emissions` | object | `{ difference_percent, CO2e, typical_for_this_route, higher }` — emissions in grams. |
| `booking_token` | string | Opaque token for booking URL generation. |
| `airline_logo` | string | URL to airline logo image. |
| `self_transfer` | boolean | Whether the itinerary requires self-transfer. |
| `delay` | object | `{ values: boolean, text: number }` — delay info. |

---

## Flight Leg (each element in `flights`)

| Field | Type | Description |
|-------|------|-------------|
| `departure_airport` | object | `{ airport_name, airport_code, time }` — IATA code and departure time. |
| `arrival_airport` | object | `{ airport_name, airport_code, time }` — IATA code and arrival time. |
| `duration` | object | `{ raw: number, text: string }` — leg duration in minutes. |
| `airline` | string | Airline name (e.g., `"American"`, `"JetBlue"`). |
| `flight_number` | string | Flight number (e.g., `"AA 274"`, `"B6 2824"`). |
| `aircraft` | string | Aircraft type (e.g., `"Boeing 777"`, `"Airbus A320"`). |
| `seat` | string | Seat/legroom description (e.g., `"Average legroom"`). |
| `legroom` | string | Legroom in inches (e.g., `"31 in"`). |
| `extensions` | array | Additional amenities (Wi-Fi, power, emissions estimate text). |

---

## Layover (each element in `layovers`)

| Field | Type | Description |
|-------|------|-------------|
| `airport_code` | string | IATA code of layover airport. |
| `airport_name` | string | Full airport name. |
| `duration` | number | Layover duration in minutes. |
| `duration_label` | string | Human-readable duration. |
| `city` | string | City of the layover airport. |

---

## `data.priceHistory`

| Field | Type | Description |
|-------|------|-------------|
| `summary` | object | `{ current, low, typical, high }` — price bands. |
| `history` | array | `[{ time: number, value: number }]` — historical prices over time. |

---

## Summary: Core Fields for ETL

| # | Path | Purpose |
|---|------|---------|
| 1 | `status` | Request success indicator |
| 2 | `data.itineraries.topFlights` | Primary flight options |
| 3 | `data.itineraries.otherFlights` | Secondary flight options |
| 4 | `*.departure_time` / `*.arrival_time` | Trip timing |
| 5 | `*.duration` | Trip/leg duration |
| 6 | `*.price` | Fare price |
| 7 | `*.flights` | Flight legs (segments) |
| 8 | `*.flights[].departure_airport` / `arrival_airport` | Airport and IATA codes |
| 9 | `*.flights[].airline` / `flight_number` | Carrier and flight ID |
| 10 | `*.carbon_emissions` | Emissions data |
| 11 | `*.booking_token` | Booking reference |
| 12 | `data.priceHistory` | Price trends |
