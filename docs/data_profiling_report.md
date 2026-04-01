# Bronze Data Profiling & Silver Schema Mapping

**Linear:** [JOB-92 — Task 3.2](https://linear.app/job-search-assistant/issue/JOB-92/task-32-perform-initial-data-profiling-and-schema-mapping)  
**Environment profiled:** `dev` (Glue `flights_raw_dev`, table `bronze_flights`)  
**Profile run:** 2026-04-01 (Athena engine 3, workgroup `flights-exploration-dev`)

---

## 1. Executive summary

Bronze holds **one JSON file per ingestion run** under Hive partitions `year=/month=/day=`. The project has transitioned from RapidAPI to a **custom scraper (fast-flights)**, which has introduced a new unified JSON structure.

| Metric | Value (dev, snapshot) |
|--------|------------------------|
| Bronze rows (files) | 3,231 |
| Distinct partition paths | 13 (`year/month/day` groups) |
| Root-level nulls (`status`, `message`, `timestamp`, `data`) | 0 (on latest format) |
| Itineraries per file (average) | ~30 |
| Null `price` in itineraries | 0 |
| Null `departure_time` | 0 |

**Key finding for Silver:** The data format has evolved. Latest files (e.g., July 2026 partitions) use a flat `data.itineraries` array, while older files used `data.itineraries.topFlights`. Silver processing in Spark must handle this schema evolution by checking for the existence of nested fields or using a flexible JSON schema.

---

## 2. Scraper Data Structure (Bronze)

The current scraper produces a unified JSON structure mapped to the Bronze layer:

| Field | Type | Description |
|-------|------|-------------|
| `status` | boolean | Request success flag |
| `message` | string | Status message (e.g., "Success") |
| `timestamp` | bigint | Unix epoch milliseconds of ingestion |
| `api_timestamp` | string | ISO-8601 timestamp from the source |
| `data.itineraries` | array | List of flight options |

### 2.1 Itinerary Detail (Nested)

Each element in `data.itineraries` contains:
- `price`: bigint (e.g., 169)
- `stops`: bigint (0, 1, 2...)
- `departure_time`: string (ISO-8601)
- `arrival_time`: string (ISO-8601)
- `duration`: struct with `raw` (minutes) and `text` ("5h 53m")
- `flights`: array of **legs/segments**
- `bags`: struct with `carry_on` and `checked`
- `carbon_emissions`: struct with `CO2e` and `typical_for_this_route`
- `self_transfer`: boolean

---

## 3. Silver Layer Schema Mapping (Target)

The Silver layer will normalize the nested scraper data into flat Parquet tables.

### 3.1 `fact_flight_itinerary`
Grain: One row per itinerary option.

| Silver Column | Source (JSON) | Type |
|---------------|---------------|------|
| `itinerary_id` | Surrogate (Hash of flights + times) | string |
| `price` | `price` | decimal(10,2) |
| `departure_time` | `departure_time` | timestamp |
| `arrival_time` | `arrival_time` | timestamp |
| `total_duration_mins`| `duration.raw` | int |
| `stops` | `stops` | int |
| `is_self_transfer` | `self_transfer` | boolean |
| `carry_on_bags` | `bags.carry_on` | int |
| `checked_bags` | `bags.checked` | int |
| `co2_emissions` | `carbon_emissions.CO2e` | bigint |
| `ingest_timestamp` | `timestamp` | timestamp |

### 3.2 `fact_flight_leg`
Grain: One row per segment within an itinerary.

| Silver Column | Source (JSON) | Type |
|---------------|---------------|------|
| `itinerary_id` | Join key to parent | string |
| `leg_index` | Array index (0-based) | int |
| `departure_airport` | `flights[].departure_airport.airport_code` | string |
| `arrival_airport` | `flights[].arrival_airport.airport_code` | string |
| `departure_time` | `flights[].departure_airport.time` | timestamp |
| `arrival_time` | `flights[].arrival_airport.time` | timestamp |
| `airline` | `flights[].airline` | string |
| `flight_number` | `flights[].flight_number` | string |
| `aircraft` | `flights[].aircraft` | string |
| `travel_class` | `flights[].seat` | string |

---

## 4. Data Quality Rules (for Task 3.3)

1. **Price Sanity**: `price` must be > 0.
2. **Time Sequence**: `arrival_time` must be > `departure_time`.
3. **Airport Codes**: `departure_airport` and `arrival_airport` must be 3-character IATA codes.
4. **Completeness**: Every itinerary must have at least one leg in the `flights` array.
5. **Deduplication**: Use a hash of all legs (airline + flight_number + time) to identify unique itineraries across search runs.
