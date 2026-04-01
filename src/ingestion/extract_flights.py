"""
Extract flight data using fast-flights scraper with Bright Data and upload to Bronze S3.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import boto3
from dotenv import load_dotenv

# Add project root to sys.path to ensure local fast_flights package is found
project_root = str(Path(__file__).parents[2])
if project_root not in sys.path:
    sys.path.append(project_root)

# Import local scraper
from fast_flights import FlightQuery, Passengers, create_query, get_flights  # noqa: E402
from fast_flights.model import Flights  # noqa: E402
from fast_flights.integrations.bright_data import BrightData  # noqa: E402
from fast_flights.types import SeatType, TripType  # noqa: E402

load_dotenv()

logger = logging.getLogger(__name__)

BRONZE_BUCKET = os.getenv("BRONZE_BUCKET", "flights-bronze-raw-dev")
BRIGHT_DATA_API_KEY = os.getenv("BRIGHT_DATA_API_KEY")
BRIGHT_DATA_SERP_ZONE = os.getenv("BRIGHT_DATA_SERP_ZONE", "serp_api1")

def get_bright_data_api_key():
    return os.getenv("BRIGHT_DATA_API_KEY")

def fetch_flights_with_scraper(
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    seat: SeatType = "economy",
    trip: TripType = "one-way",
    adults: int = 1,
) -> list[Flights]:
    """
    Fetch flight search results using the fast-flights scraper and Bright Data.
    """
    api_key = get_bright_data_api_key()
    if not api_key:
        raise ValueError("BRIGHT_DATA_API_KEY must be set in environment")

    # 1. Create the query
    query = create_query(
        flights=[
            FlightQuery(date=outbound_date, from_airport=departure_id, to_airport=arrival_id),
        ],
        seat=seat,
        trip=trip,
        passengers=Passengers(adults=adults),
    )

    # 2. Initialize Bright Data integration
    bd_integration = BrightData(
        api_key=api_key,
        zone=BRIGHT_DATA_SERP_ZONE
    )

    # 3. Get flights
    logger.info(
        "Fetching flights %s -> %s on %s (seat=%s, trip=%s, adults=%d) using scraper", 
        departure_id, arrival_id, outbound_date, seat, trip, adults
    )
    result = get_flights(query, integration=bd_integration)
    
    return result

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

def map_scraper_to_bronze(scraper_results: list[Flights]) -> dict:
    """
    Map the scraper's rich data structure to the Bronze layer 
    and downstream Spark/Athena processes.
    """
    itineraries = []
    
    for item in scraper_results:
        # 1. Map segments
        flights_mapped = []
        layovers_mapped = []
        
        for i, segment in enumerate(item.flights):
            # Flight leg mapping
            flights_mapped.append({
                "departure_airport": {
                    "airport_name": segment.from_airport.name,
                    "airport_code": segment.from_airport.code,
                    "time": segment.departure.timestamp
                },
                "arrival_airport": {
                    "airport_name": segment.to_airport.name,
                    "airport_code": segment.to_airport.code,
                    "time": segment.arrival.timestamp
                },
                "duration": {
                    "raw": segment.duration,
                    "text": f"{segment.duration // 60}h {segment.duration % 60}m"
                },
                "airline": segment.operating_airline,
                "airline_code": segment.airline_code,
                "flight_number": segment.flight_number,
                "aircraft": segment.plane_type,
                "seat": segment.travel_class,
                "overnight": segment.overnight
            })
            
            # Layover mapping (if exists)
            if segment.layover_duration:
                # The layover happens AFTER this segment
                # Safety check for index out of bounds
                if i + 1 < len(item.flights):
                    layovers_mapped.append({
                        "airport_code": segment.to_airport.code,
                        "airport_name": segment.to_airport.name,
                        "duration": segment.layover_duration,
                        "duration_label": f"{segment.layover_duration // 60}h {segment.layover_duration % 60}m",
                        "airport_change": segment.airport_change
                    })

        # 2. Map itinerary level
        itineraries.append({
            "departure_time": item.flights[0].departure.timestamp,
            "arrival_time": item.flights[-1].arrival.timestamp,
            "duration": {
                "raw": item.total_duration,
                "text": f"{item.total_duration // 60}h {item.total_duration % 60}m"
            },
            "flights": flights_mapped,
            "price": item.price,
            "stops": item.stops,
            "layovers": layovers_mapped if layovers_mapped else None,
            "bags": {
                "carry_on": item.baggage.carry_on if item.baggage else 0,
                "checked": item.baggage.checked_bag if item.baggage else 0
            },
            "carbon_emissions": {
                "CO2e": item.carbon.emission,
                "typical_for_this_route": item.carbon.typical_on_route
            },
            "self_transfer": item.self_transfer,
            "price_trend": item.price_trend
        })

    return {
        "status": True,
        "message": "Success",
        "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
        "data": {
            "itineraries": itineraries
        }
    }

def upload_to_s3(
    data: list[Flights],
    s3_key: str,
    bucket: str | None = None,
) -> str:
    """
    Upload raw data to Bronze S3 bucket.
    Maps the scraper output to the Bronze layer schema.
    """
    bkt = bucket or os.getenv("BRONZE_BUCKET", BRONZE_BUCKET)
    
    # Map to Bronze schema (Passing dataclass objects directly for performance)
    bronze_data = map_scraper_to_bronze(data)

    body = json.dumps(bronze_data, separators=(",", ":")).encode("utf-8")

    try:
        client = boto3.client("s3")
        client.put_object(Bucket=bkt, Key=s3_key, Body=body, ContentType="application/json")
    except Exception as e:
        logger.error("Failed to upload to S3 bucket %s: %s", bkt, e)
        raise

    uri = f"s3://{bkt}/{s3_key}"
    logger.info("Uploaded %s bytes to %s", len(body), uri)
    return uri

def extract_and_upload(
    departure_id: str = "LAX",
    arrival_id: str = "JFK",
    outbound_date: str = "2026-04-15",
    seat: SeatType = "economy",
    trip: TripType = "one-way",
    adults: int = 1,
) -> str:
    """
    Fetch flights from scraper and upload to Bronze S3.
    """
    data = fetch_flights_with_scraper(
        departure_id, arrival_id, outbound_date, seat, trip, adults
    )
    s3_key = build_s3_key(outbound_date)
    return upload_to_s3(data, s3_key)

def main() -> None:
    """CLI entrypoint."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    departure = os.getenv("DEPARTURE_ID", "LAX")
    arrival = os.getenv("ARRIVAL_ID", "JFK")
    date_str = os.getenv("OUTBOUND_DATE", "2026-04-15")

    try:
        uri = extract_and_upload(departure, arrival, date_str)
        logger.info("Done. File at %s", uri)
    except Exception as e:
        logger.error("Extraction failed: %s", e)
        raise

if __name__ == "__main__":
    main()
