-- Bronze profiling queries for Task 3.2 (JOB-92).
-- Run in Athena against the Glue database/table from Task 3.1.
--
-- Typical dev settings:
--   Database: flights_raw_dev
--   Table:    bronze_flights
--   Workgroup: flights-exploration-dev
--   Output:   s3://flights-pipeline-logs-dev/athena-results/
--
-- Replace database/table names if your environment differs.

-- Volume
SELECT COUNT(*) AS row_count
FROM flights_raw_dev.bronze_flights;

-- Partition coverage
SELECT
  year,
  month,
  day,
  COUNT(*) AS files
FROM flights_raw_dev.bronze_flights
GROUP BY year, month, day
ORDER BY year, month, day;

-- Root-level nulls
SELECT
  SUM(CASE WHEN status IS NULL THEN 1 ELSE 0 END) AS status_nulls,
  SUM(CASE WHEN message IS NULL THEN 1 ELSE 0 END) AS message_nulls,
  SUM(CASE WHEN api_timestamp IS NULL THEN 1 ELSE 0 END) AS api_timestamp_nulls,
  SUM(CASE WHEN data IS NULL THEN 1 ELSE 0 END) AS data_nulls
FROM flights_raw_dev.bronze_flights;

-- Empty itinerary arrays (catalog-defined paths only)
SELECT
  SUM(
    CASE
      WHEN cardinality(data.itineraries.topFlights) IS NULL
        OR cardinality(data.itineraries.topFlights) = 0
      THEN 1
      ELSE 0
    END
  ) AS rows_with_empty_topflights,
  SUM(
    CASE
      WHEN cardinality(data.itineraries.otherFlights) IS NULL
        OR cardinality(data.itineraries.otherFlights) = 0
      THEN 1
      ELSE 0
    END
  ) AS rows_with_empty_otherflights
FROM flights_raw_dev.bronze_flights;

-- Itinerary-level: price and booking_token (topFlights)
SELECT
  SUM(CASE WHEN tf.price IS NULL THEN 1 ELSE 0 END) AS price_nulls,
  SUM(
    CASE
      WHEN tf.booking_token IS NULL OR TRIM(tf.booking_token) = '' THEN 1
      ELSE 0
    END
  ) AS booking_token_null_or_empty,
  COUNT(*) AS topflight_rows
FROM flights_raw_dev.bronze_flights
CROSS JOIN UNNEST(data.itineraries.topFlights) AS t(tf);

-- Itinerary-level: price (otherFlights)
SELECT
  SUM(CASE WHEN tf.price IS NULL THEN 1 ELSE 0 END) AS price_nulls,
  COUNT(*) AS otherflight_rows
FROM flights_raw_dev.bronze_flights
CROSS JOIN UNNEST(data.itineraries.otherFlights) AS t(tf);
