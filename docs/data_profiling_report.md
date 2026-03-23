# Bronze Data Profiling & Silver Schema Mapping

**Linear:** [JOB-92 — Task 3.2](https://linear.app/job-search-assistant/issue/JOB-92/task-32-perform-initial-data-profiling-and-schema-mapping)  
**Environment profiled:** `dev` (Glue `flights_raw_dev`, table `bronze_flights`)  
**Profile run:** 2026-03-23 (Athena engine 3, workgroup `flights-exploration-dev`)

---

## 1. Executive summary

Bronze holds **one JSON file per ingestion run** under Hive partitions `year=/month=/day=`. Profiling used **Athena** against the Glue-backed external table from Task 3.1.

| Metric | Value (dev, snapshot) |
|--------|------------------------|
| Bronze rows (files) | 9 |
| Distinct partition paths | 8 (`year/month/day` groups) |
| Root-level nulls (`status`, `message`, `api_timestamp`, `data`) | 0 |
| Rows with empty `topFlights` / `otherFlights` arrays | 0 |
| `topFlights` rows (exploded) | 31 |
| `otherFlights` rows (exploded) | 185 |
| Null `price` (exploded `topFlights` / `otherFlights`) | 0 |
| Null or empty `booking_token` (exploded `topFlights`) | 0 |

**Key finding for Silver:** The Glue column type for `data` lists only a **subset** of fields per itinerary (see §3). Nested structures such as **`flights` (legs/segments)**, **`duration`**, **`layovers`**, **`bags`**, **`carbon_emissions`**, and **`delay`** exist in the **raw JSON on S3** (see `ref/sample_api_response.json` and `ref/data_dictionary_bronze.md`) but are **not exposed** in the current Athena `struct` definition. **Silver processing in Spark should read the full JSON from S3** (or evolve the Glue JSON schema) so leg-level flattening is possible.

**Identifier note:** The API does not expose a field named `itinerary_id`. For deduplication and keys, use **`booking_token`** (opaque string per itinerary option) and/or a **surrogate key** (e.g., hash of `booking_token` + `source_file` + partition).

---

## 2. Athena profiling methodology

Repeatable SQL lives in `scripts/athena/bronze_profiling.sql`. Use workgroup `flights-exploration-dev`, database `flights_raw_dev`, and query results prefix `s3://flights-pipeline-logs-dev/athena-results/` (from Terraform).

Queries cover:

1. **Volume:** `COUNT(*)` over `bronze_flights`.
2. **Partitions:** `GROUP BY year, month, day` to verify expected Hive layout.
3. **Root nulls:** `status`, `message`, `api_timestamp`, `data`.
4. **Array emptiness:** `cardinality` on `data.itineraries.topFlights` and `otherFlights`.
5. **Critical fields on cataloged structs:** `UNNEST` of `topFlights` / `otherFlights` for `price` and `booking_token`.

---

## 3. Nested structures & Glue catalog vs raw JSON

### 3.1 Arrays that require flattening in Spark

| Location | Structure | Silver intent |
|----------|-----------|----------------|
| `data.itineraries.topFlights` | array of itinerary options | Explode to one row per **itinerary option**; join to legs |
| `data.itineraries.otherFlights` | array of itinerary options | Same as above (secondary ranking bucket) |
| Each itinerary → `flights` | array of **legs/segments** | **Explode** to one row per segment (not in current Glue struct) |
| Each leg → `departure_airport` / `arrival_airport` | nested objects | Flatten to codes + times |
| `layovers` | array (nullable) | Optional detail table or columns on itinerary grain |
| `data.priceHistory.history` | array of time series | Optional analytics; separate from core itinerary facts |

Athena can **UNNEST** `topFlights` / `otherFlights` only for fields **declared** in Glue. **Leg-level** profiling must use **Spark on raw JSON** (or widen the Glue `struct` / store `data` as JSON string) until the catalog matches the API.

### 3.2 Observed Glue `data` struct (truncated)

The Terraform-defined schema intentionally starts narrow (`terraform/modules/athena_glue/main.tf`). Declared itinerary fields include `price`, `departure_time`, `arrival_time`, `stops`, `booking_token`, `airline_logo`, `self_transfer` — **not** `flights`, `duration`, etc.

---

## 4. Silver layer schema mapping (target)

Naming follows project conventions: **`fact_*`** for measurable events, dimensions as needed. Types are indicative; implement in Spark with explicit casts.

### 4.1 `fact_flight_search_run` (optional, one row per Bronze file)

| Silver column | Bronze / source |
|----------------|-----------------|
| `ingest_date` | Partition `year`, `month`, `day` |
| `api_timestamp` | `api_timestamp` (normalize to `timestamp`) |
| `request_success` | `status` |
| `message` | `message` |
| `source_bucket_key` | Derived from ingest metadata or path |
| `bronze_file_path` | Full S3 URI (Spark `input_file_name` or path columns) |

### 4.2 `fact_flight_itinerary` (one row per itinerary option)

Grain: one row per element of `topFlights` ∪ `otherFlights` after tagging list source.

| Silver column | Bronze / source |
|----------------|-----------------|
| `itinerary_key` | Surrogate: e.g. `sha256(booking_token \|\| bucket \|\| key)` or stable UUID in job |
| `booking_token` | `booking_token` |
| `list_source` | Literal `topFlights` or `otherFlights` |
| `price` | `price` → `decimal` / `bigint` per currency rules |
| `departure_time` | Parse string → `timestamp` (timezone-aware policy) |
| `arrival_time` | Parse string → `timestamp` |
| `stops` | `stops` |
| `self_transfer` | `self_transfer` |
| `airline_logo` | `airline_logo` (optional) |
| `total_duration_minutes` | `duration.raw` from JSON (Spark) |
| `layovers_json` or normalized | `layovers` array from JSON |
| `bags_*`, `carbon_*`, `delay_*` | From JSON when needed |

### 4.3 `fact_flight_leg` (one row per segment)

Grain: explode `flights` inside each itinerary row.

| Silver column | Bronze / source |
|----------------|-----------------|
| `itinerary_key` | Join key from parent itinerary row |
| `leg_sequence` | `posexplode` index (1-based) |
| `departure_airport_code` | `departure_airport.airport_code` |
| `arrival_airport_code` | `arrival_airport.airport_code` |
| `departure_time` | Parse `departure_airport.time` |
| `arrival_time` | Parse `arrival_airport.time` |
| `leg_duration_minutes` | `duration.raw` |
| `airline` | `airline` |
| `flight_number` | `flight_number` |
| `aircraft` | `aircraft` |
| `seat`, `legroom` | As needed |
| `extensions` | Array → string or child table |

### 4.4 `fact_route_price_history` (optional)

| Silver column | Bronze / source |
|----------------|-----------------|
| `search_run_id` / `route_key` | Keys tying to search run |
| `history_ts` | `data.priceHistory.history[].time` |
| `price_value` | `data.priceHistory.history[].value` |
| `summary_*` | `data.priceHistory.summary.*` |

---

## 5. Definition of done (Task 3.2)

- [x] Athena queries executed for counts, partitions, root nulls, and exploded itinerary-level `price` / `booking_token` checks (results in §1).
- [x] Nested arrays and Spark flattening strategy documented (§3–§4).
- [x] Silver mapping from raw JSON to normalized tables documented (§4).
- [x] This file committed at `docs/data_profiling_report.md`.

---

## 6. Follow-ups

- **Evolve Glue JSON schema** (or add a `raw_json` string column) if Athena must profile leg-level fields without Spark.
- **Task 3.3** (data quality rules): build on §1 and add duplicate checks on `booking_token`, price sanity, and partition completeness over time.
