import os
import sys
import logging
from datetime import datetime, timedelta

# Add workspace root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.ingestion.extract_flights import extract_and_upload

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

def populate_diverse_data():
    # Define a set of diverse search parameters
    searches = [
        # One-way, Direct (likely)
        {"departure_id": "JFK", "arrival_id": "LAX", "outbound_date": "2026-06-15", "trip": "one-way"},
        # One-way, Layover (likely)
        {"departure_id": "JFK", "arrival_id": "NQZ", "outbound_date": "2026-06-15", "trip": "one-way"},
        # Round-trip (will be handled as two one-way searches by our current script)
        {"departure_id": "LHR", "arrival_id": "HND", "outbound_date": "2026-06-17", "trip": "round-trip"},
        # Different date, different route
        {"departure_id": "SFO", "arrival_id": "CDG", "outbound_date": "2026-07-01", "trip": "one-way"},
        # Another one for variety
        {"departure_id": "DXB", "arrival_id": "SYD", "outbound_date": "2026-07-20", "trip": "one-way"},
    ]

    for search in searches:
        try:
            logger.info(f"Starting extraction for {search['departure_id']} -> {search['arrival_id']} on {search['outbound_date']} ({search['trip']})")
            uri = extract_and_upload(
                departure_id=search["departure_id"],
                arrival_id=search["arrival_id"],
                outbound_date=search["outbound_date"],
                trip=search["trip"]
            )
            logger.info(f"Successfully uploaded to {uri}")
        except Exception as e:
            logger.error(f"Failed search {search['departure_id']} -> {search['arrival_id']}: {e}")

if __name__ == "__main__":
    populate_diverse_data()
