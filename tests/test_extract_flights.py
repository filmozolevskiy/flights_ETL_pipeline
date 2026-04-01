"""Unit tests for flight extraction and S3 upload using the scraper."""

import json
from unittest.mock import MagicMock, patch

import pytest
from src.ingestion.extract_flights import (
    extract_and_upload,
    fetch_flights_with_scraper,
    upload_to_s3,
)
from fast_flights.model import Flights, CarbonEmission, Baggage

class TestFetchFlightsWithScraper:
    """Tests for fetch_flights_with_scraper with mocked get_flights."""

    def test_fetch_flights_with_scraper_calls_get_flights(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRIGHT_DATA_API_KEY", "test-key")
        
        mock_flights = [
            Flights(
                price=100,
                airlines=["Test Airline"],
                airline_codes=["TA"],
                flights=[],
                carbon=CarbonEmission(typical_on_route=100, emission=90),
                total_duration=300,
                stops=0,
                self_transfer=False,
                price_trend="typical",
                baggage=Baggage(carry_on=1, checked_bag=1)
            )
        ]

        with patch("src.ingestion.extract_flights.get_flights", return_value=mock_flights) as mock_get:
            result = fetch_flights_with_scraper("LAX", "JFK", "2026-04-15")
            
            assert result == mock_flights
            mock_get.assert_called_once()

    def test_raises_error_if_api_key_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("BRIGHT_DATA_API_KEY", raising=False)
        with pytest.raises(ValueError, match="BRIGHT_DATA_API_KEY must be set"):
            fetch_flights_with_scraper("LAX", "JFK", "2026-04-15")


class TestUploadToS3:
    """Tests for S3 upload with mocked boto3."""

    def test_upload_to_s3_maps_and_puts_object(self) -> None:
        mock_s3 = MagicMock()
        from fast_flights.model import SingleFlight, Airport, SimpleDatetime
        
        mock_segment = SingleFlight(
            from_airport=Airport(name="Los Angeles", code="LAX"),
            to_airport=Airport(name="New York", code="JFK"),
            departure=SimpleDatetime(timestamp="2026-04-15T10:00:00"),
            arrival=SimpleDatetime(timestamp="2026-04-15T18:00:00"),
            duration=480,
            plane_type="Boeing 787",
            airline_code="AA",
            flight_number="123",
            travel_class="economy",
            operating_airline="American Airlines",
            overnight=False
        )
        
        mock_data = [
            Flights(
                price=100,
                airlines=["American Airlines"],
                airline_codes=["AA"],
                flights=[mock_segment],
                carbon=CarbonEmission(typical_on_route=100, emission=90),
                total_duration=480,
                stops=0,
                self_transfer=False,
                price_trend="typical",
                baggage=Baggage(carry_on=1, checked_bag=1)
            )
        ]
        
        with patch("src.ingestion.extract_flights.boto3.client", return_value=mock_s3):
            uri = upload_to_s3(
                mock_data,
                "year=2026/month=04/day=15/flight_data_20260317T120000Z.json",
                bucket="test-bucket",
            )
            
        mock_s3.put_object.assert_called_once()
        call_kwargs = mock_s3.put_object.call_args.kwargs
        assert call_kwargs["Bucket"] == "test-bucket"
        assert "year=2026/month=04/day=15" in call_kwargs["Key"]
        
        body = json.loads(call_kwargs["Body"].decode("utf-8"))
        assert body["status"] is True
        assert "itineraries" in body["data"]
        assert body["data"]["itineraries"][0]["price"] == 100
        assert uri.startswith("s3://test-bucket/")


class TestExtractAndUpload:
    """Tests for extract_and_upload with mocked scraper and S3."""

    def test_extract_and_upload_fetches_and_uploads(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRIGHT_DATA_API_KEY", "test-key")
        mock_s3 = MagicMock()
        mock_flights = [] # Empty list for simplicity

        with (
            patch("src.ingestion.extract_flights.get_flights", return_value=mock_flights),
            patch("src.ingestion.extract_flights.boto3.client", return_value=mock_s3),
        ):
            uri = extract_and_upload("LAX", "JFK", "2026-04-15")

        mock_s3.put_object.assert_called_once()
        assert uri.startswith("s3://")
        assert "year=2026/month=04/day=15" in uri
