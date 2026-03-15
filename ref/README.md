# Reference: Google Flights API

Reference assets for the RapidAPI Google Flights API 

## Sample API Response

**File:** `sample_api_response.json`

A full JSON response from the Search Flights endpoint (LAX → JFK, 2026-04-15). Use it for:

- Schema exploration and data profiling
- Unit tests and fixtures
- Jupyter notebooks

See `ref/data_dictionary_bronze.md` for field mappings.

## Postman Collection

**File:** `google_flights_api.postman_collection.json`

Import into Postman to call the API directly.

### Setup

1. Import the collection (File → Import → select the JSON file).
2. Set `rapidapi_key` in collection variables: use your RapidAPI API key from the [Google Flights API](https://rapidapi.com) subscription page.
3. `rapidapi_host` is pre-set; change it if your provider uses a different host.
4. Adjust `departure_id`, `arrival_id`, `outbound_date` as needed.
