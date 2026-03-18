"""
Extract flight data from RapidAPI Google Flights and upload to Bronze S3.

Fetches raw JSON from the API and stores it in s3://flights-bronze-raw/
with Hive-style partitioning: year=YYYY/month=MM/day=DD/flight_data_TIMESTAMP.json

Requires env vars: RAPIDAPI_KEY. Optional: RAPIDAPI_HOST, AWS_PROFILE.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

import boto3
import requests

load_dotenv()

logger = logging.getLogger(__name__)

RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "google-flights2.p.rapidapi.com")
BRONZE_BUCKET = os.getenv("BRONZE_BUCKET", "flights-bronze-raw")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
MAX_ATTEMPTS = int(os.getenv("API_MAX_ATTEMPTS", "5"))


def _is_retriable_http_error(exc: BaseException) -> bool:
    """Return True for 429 or 5xx, which are worth retrying."""
    if isinstance(exc, requests.HTTPError):
        resp = getattr(exc, "response", None)
        if resp is None:
            return False
        return resp.status_code == 429 or resp.status_code >= 500
    return isinstance(exc, (requests.ConnectionError, requests.Timeout))


def _log_retry(retry_state: Any) -> None:
    """Log each retry attempt."""
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    status = getattr(getattr(exc, "response", None), "status_code", None)
    logger.warning(
        "API request failed (attempt %s, status=%s), retrying",
        retry_state.attempt_number,
        status,
    )


@retry(
    retry=retry_if_exception(_is_retriable_http_error),
    stop=stop_after_attempt(MAX_ATTEMPTS),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    before_sleep=_log_retry,
)
def _request_with_retry(
    url: str, headers: dict[str, str], params: dict[str, str]
) -> requests.Response:
    """Perform HTTP GET with retries on 429 and 5xx."""
    resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp


def fetch_flights(
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    Fetch flight search results from RapidAPI Google Flights.

    Args:
        departure_id: IATA airport code (e.g. LAX).
        arrival_id: IATA airport code (e.g. JFK).
        outbound_date: Date in YYYY-MM-DD format.
        api_key: RapidAPI key. Falls back to RAPIDAPI_KEY env var.

    Returns:
        Raw API response as dict.

    Raises:
        ValueError: If API key is missing or response indicates failure.
        requests.RequestException: On HTTP errors.
    """
    key = api_key or os.getenv("RAPIDAPI_KEY")
    if not key:
        raise ValueError("RAPIDAPI_KEY must be set or passed as api_key")

    url = f"https://{RAPIDAPI_HOST}/api/v1/searchFlights"
    headers = {
        "X-RapidAPI-Key": key,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
        "Content-Type": "application/json",
    }
    params = {
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_date,
        "adults": "1",
        "currency": "USD",
        "country_code": "US",
        "language_code": "en-US",
        "search_type": "best",
        "travel_class": "ECONOMY",
    }

    logger.info(
        "Fetching flights %s -> %s on %s", departure_id, arrival_id, outbound_date
    )
    resp = _request_with_retry(url, headers, params)

    data = resp.json()
    if not data.get("status"):
        raise ValueError(
            f"API returned failure: {data.get('message', 'Unknown error')}"
        )

    return data


def parse_partition_from_date(outbound_date: str) -> tuple[str, str, str]:
    """Parse YYYY-MM-DD into year, month, day for partitioning."""
    dt = datetime.strptime(outbound_date, "%Y-%m-%d")
    return (
        str(dt.year),
        f"{dt.month:02d}",
        f"{dt.day:02d}",
    )


def build_s3_key(outbound_date: str) -> str:
    """Build S3 object key: year=YYYY/month=MM/day=DD/flight_data_TIMESTAMP.json."""
    year, month, day = parse_partition_from_date(outbound_date)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"year={year}/month={month}/day={day}/flight_data_{ts}.json"


def upload_to_s3(
    data: dict[str, Any],
    s3_key: str,
    bucket: str | None = None,
) -> str:
    """
    Upload raw JSON to Bronze S3 bucket.

    Args:
        data: JSON-serializable response from the API.
        s3_key: Full S3 object key (including partition path).
        bucket: S3 bucket name. Defaults to BRONZE_BUCKET env var or flights-bronze-raw.

    Returns:
        Full S3 URI of the uploaded object.
    """
    bkt = bucket or os.getenv("BRONZE_BUCKET", BRONZE_BUCKET)
    body = json.dumps(data, indent=2).encode("utf-8")

    client = boto3.client("s3")
    client.put_object(Bucket=bkt, Key=s3_key, Body=body, ContentType="application/json")

    uri = f"s3://{bkt}/{s3_key}"
    logger.info("Uploaded %s bytes to %s", len(body), uri)
    return uri


def extract_and_upload(
    departure_id: str = "LAX",
    arrival_id: str = "JFK",
    outbound_date: str = "2026-04-15",
) -> str:
    """
    Fetch flights from API and upload to Bronze S3.

    Args:
        departure_id: Origin IATA code.
        arrival_id: Destination IATA code.
        outbound_date: Date in YYYY-MM-DD.

    Returns:
        S3 URI of the uploaded file.
    """
    data = fetch_flights(departure_id, arrival_id, outbound_date)
    s3_key = build_s3_key(outbound_date)
    return upload_to_s3(data, s3_key)


def main() -> None:
    """CLI entrypoint: extract default route and upload to S3."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    departure = os.getenv("DEPARTURE_ID", "LAX")
    arrival = os.getenv("ARRIVAL_ID", "JFK")
    date_str = os.getenv("OUTBOUND_DATE", "2026-04-15")

    uri = extract_and_upload(departure, arrival, date_str)
    logger.info("Done. File at %s", uri)


if __name__ == "__main__":
    main()
