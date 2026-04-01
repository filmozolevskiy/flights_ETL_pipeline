import json

from selectolax.lexbor import LexborHTMLParser

from .model import (
    Airline,
    Airport,
    Alliance,
    CarbonEmission,
    Flights,
    JsMetadata,
    SimpleDatetime,
    SingleFlight,
    Baggage,
)
from datetime import datetime


class MetaList(list[Flights]):
    """Searched flights list, with metadata attached."""

    metadata: JsMetadata


def parse(html: str) -> MetaList:
    parser = LexborHTMLParser(html)

    # find js
    script = parser.css_first(r"script.ds\:1")
    if script is None:
        raise ValueError(
            "Could not find Google Flights script (ds:1). "
            "The page may be blocked, consent-only, or use an unsupported layout."
        )
    return parse_js(script.text())


# Data discovery by @kftang, huge shout out!
def parse_js(js: str):
    rest = js.split("data:", 1)[1]
    # Prefer splitting on Google's trailing `sideChannel` 
    if ", sideChannel:" in rest:
        data = rest.split(", sideChannel:", 1)[0]
    else:
        data = rest.rsplit(",", 1)[0]

    payload = json.loads(data)

    alliances = []
    airlines = []

    (alliances_data, airlines_data) = (
        payload[7][1][0],
        payload[7][1][1],
    )

    for code, name in alliances_data:
        alliances.append(Alliance(code=code, name=name))

    for code, name in airlines_data:
        airlines.append(Airline(code=code, name=name))

    meta = JsMetadata(alliances=alliances, airlines=airlines)

    flights = MetaList()
    if payload[3][0] is None:
        return flights

    for k in payload[3][0]:
        flight = k[0]
        price = k[1][0][1]

        airlines = flight[1]

        sg_flights = []

        # multiple flights!
        for i, single_flight in enumerate(flight[2]):
            from_airport = Airport(code=single_flight[3], name=single_flight[4])
            to_airport = Airport(code=single_flight[6], name=single_flight[5])
            
            # Times and dates
            departure_time = single_flight[8]
            departure_date = single_flight[20]
            
            # Convert to ISO format strings
            def format_dt(date_list, time_list):
                try:
                    # Handle None values in time_list (e.g., [None, 56])
                    clean_time = [t if t is not None else 0 for t in time_list]
                    
                    # Ensure time_list has at least [H, M]
                    while len(clean_time) < 2:
                        clean_time.append(0)
                        
                    dt = datetime(*date_list, *clean_time)
                    return SimpleDatetime(
                        timestamp=dt.isoformat()
                    )
                except Exception as e:
                    return SimpleDatetime(
                        timestamp=""
                    )

            departure = format_dt(single_flight[20], single_flight[8])
            arrival = format_dt(single_flight[21], single_flight[10])

            # Segment details
            plane_type = single_flight[17]
            duration = single_flight[11]
            
            # Additional segment data
            flight_info = single_flight[22] if len(single_flight) > 22 else None
            airline_code = ""
            flight_number = ""
            operating_airline = ""
            if flight_info:
                airline_code = flight_info[0] or ""
                flight_number = f"{flight_info[0]}{flight_info[1]}"
                operating_airline = flight_info[3] or ""

            travel_class = "Economy" # Default
            if len(single_flight) > 19 and single_flight[19]:
                class_map = {1: "Economy", 2: "Premium Economy", 3: "Business", 4: "First"}
                travel_class = class_map.get(single_flight[19][11], "Economy")

            overnight = departure.timestamp[:10] != arrival.timestamp[:10]
            
            # Layover info (if not the last segment)
            layover_duration = None
            airport_change = False
            if i < len(flight[2]) - 1:
                # Layover info is in flight[13]
                if len(flight) > 13 and flight[13] and i < len(flight[13]):
                    layover = flight[13][i]
                    layover_duration = layover[0]
                    # Check if arrival airport of current segment != departure of next
                    if to_airport.code != flight[2][i+1][3]:
                        airport_change = True

            sg_flights.append(
                SingleFlight(
                    from_airport=from_airport,
                    to_airport=to_airport,
                    departure=departure,
                    arrival=arrival,
                    duration=duration,
                    plane_type=plane_type,
                    airline_code=airline_code,
                    flight_number=flight_number,
                    travel_class=travel_class,
                    operating_airline=operating_airline,
                    overnight=overnight,
                    layover_duration=layover_duration,
                    airport_change=airport_change,
                )
            )

        # some additional data
        extras = flight[22]
        carbon_emission = extras[7]
        typical_carbon_emission = extras[8]
        
        total_duration = flight[9] if len(flight) > 9 else 0
        stops = len(sg_flights) - 1
        self_transfer = flight[12] == 1 if len(flight) > 12 else False
        
        airline_codes = []
        if len(flight) > 24 and flight[24]:
            airline_codes = [a[0] for a in flight[24] if a and len(a) > 0]

        price_trend = None
        if len(flight) > 22 and flight[22]:
            trend_val = flight[22][11] if len(flight[22]) > 11 else None
            trend_map = {1: "low", 2: "typical", 3: "high"}
            price_trend = trend_map.get(trend_val)

        # Baggage info is in k[4]
        baggage = None
        if len(k) > 4 and isinstance(k[4], list) and len(k[4]) > 4:
            carry_on = k[4][4] if k[4][4] is not None else 0
            checked_bag = 0
            if len(k[4]) > 6 and isinstance(k[4][6], list) and len(k[4][6]) > 1:
                checked_bag = k[4][6][1] if k[4][6][1] is not None else 0
            baggage = Baggage(carry_on=carry_on, checked_bag=checked_bag)

        flights.append(
            Flights(
                price=price,
                airlines=airlines,
                airline_codes=airline_codes,
                flights=sg_flights,
                carbon=CarbonEmission(
                    typical_on_route=typical_carbon_emission, emission=carbon_emission
                ),
                total_duration=total_duration,
                stops=stops,
                self_transfer=self_transfer,
                price_trend=price_trend,
                baggage=baggage,
            )
        )

    flights.metadata = meta
    return flights
