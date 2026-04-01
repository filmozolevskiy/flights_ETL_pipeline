import json
import logging
import os
import sys
from dataclasses import asdict
from pathlib import Path

from dotenv import load_dotenv

# Add project root to sys.path
project_root = str(Path(__file__).parents[1])
if project_root not in sys.path:
    sys.path.append(project_root)

from fast_flights import FlightQuery, Passengers, create_query  # noqa: E402
from fast_flights.fetcher import fetch_flights_html, parse  # noqa: E402
from fast_flights.integrations.bright_data import BrightData  # noqa: E402

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BRIGHT_DATA_API_KEY = os.getenv("BRIGHT_DATA_API_KEY")
BRIGHT_DATA_SERP_ZONE = os.getenv("BRIGHT_DATA_SERP_ZONE", "serp_api1")

def save_sample(name: str, query_params: dict):
    if not BRIGHT_DATA_API_KEY:
        print(f"Skipping {name}: BRIGHT_DATA_API_KEY not set")
        return

    print(f"Fetching sample: {name}...")
    query = create_query(**query_params)
    bd_integration = BrightData(api_key=BRIGHT_DATA_API_KEY, zone=BRIGHT_DATA_SERP_ZONE)
    
    try:
        html = fetch_flights_html(query, integration=bd_integration)
        
        # Save raw HTML for inspection
        html_path = f"ref/scraper_samples/{name}.html"
        with open(html_path, "w") as f:
            f.write(html)
        print(f"Saved HTML to {html_path}")

        # Save payload_debug for this sample
        try:
            rest = html.split("data:", 1)[1]
            if ", sideChannel:" in rest:
                data_str = rest.split(", sideChannel:", 1)[0]
            else:
                data_str = rest.rsplit(",", 1)[0]
            with open(f"ref/scraper_samples/{name}_payload.json", "w") as f:
                json.dump(json.loads(data_str), f, indent=2)
        except Exception as pe:
            print(f"Failed to save payload for {name}: {pe}")

        result = parse(html)
        serializable = [asdict(item) for item in result]
        
        output_path = f"ref/scraper_samples/{name}.json"
        with open(output_path, "w") as f:
            json.dump(serializable, f, indent=2)
        print(f"Saved to {output_path}")
    except Exception as e:
        print(f"Failed to fetch {name}: {e}")

if __name__ == "__main__":
    # 1. One-way, One-segment (Direct)
    save_sample("one_way_direct", {
        "flights": [FlightQuery(date="2026-06-15", from_airport="JFK", to_airport="LAX")],
        "trip": "one-way",
        "seat": "economy",
        "passengers": Passengers(adults=1)
    })

    # 2. One-way, Many-segments (With Layovers)
    save_sample("one_way_layover", {
        "flights": [FlightQuery(date="2026-06-15", from_airport="JFK", to_airport="NQZ")],
        "trip": "one-way",
        "seat": "economy",
        "passengers": Passengers(adults=1)
    })

    # 3. Round-trip
    save_sample("round_trip", {
        "flights": [
            FlightQuery(date="2026-06-15", from_airport="JFK", to_airport="LAX"),
            FlightQuery(date="2026-06-22", from_airport="LAX", to_airport="JFK")
        ],
        "trip": "round-trip",
        "seat": "economy",
        "passengers": Passengers(adults=1)
    })
