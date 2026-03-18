"""Unit tests for flight extraction and retry logic."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.ingestion.extract_flights import (
    _is_retriable_http_error,
    extract_and_upload,
    fetch_flights,
    upload_to_s3,
)


class TestRetriableError:
    """Tests for retry logic on 429 and 5xx."""

    def test_429_is_retriable(self) -> None:
        resp = requests.Response()
        resp.status_code = 429
        exc = requests.HTTPError(response=resp)
        assert _is_retriable_http_error(exc) is True

    def test_500_is_retriable(self) -> None:
        resp = requests.Response()
        resp.status_code = 500
        exc = requests.HTTPError(response=resp)
        assert _is_retriable_http_error(exc) is True

    def test_404_is_not_retriable(self) -> None:
        resp = requests.Response()
        resp.status_code = 404
        exc = requests.HTTPError(response=resp)
        assert _is_retriable_http_error(exc) is False

    def test_connection_error_is_retriable(self) -> None:
        assert _is_retriable_http_error(requests.ConnectionError()) is True

    def test_timeout_is_retriable(self) -> None:
        assert _is_retriable_http_error(requests.Timeout()) is True


class TestFetchFlightsRetry:
    """Tests that fetch_flights retries on 429."""

    def test_retries_on_429_then_succeeds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
        call_count = 0

        def mock_get(*args: object, **kwargs: object) -> requests.Response:
            nonlocal call_count
            call_count += 1
            resp = requests.Response()
            if call_count < 2:
                resp.status_code = 429
                resp._content = b""
            else:
                resp.status_code = 200
                resp._content = b'{"status": true, "data": []}'
            return resp

        monkeypatch.setattr("src.ingestion.extract_flights.requests.get", mock_get)
        monkeypatch.setattr(
            "src.ingestion.extract_flights.RAPIDAPI_HOST",
            "google-flights2.p.rapidapi.com",
        )
        monkeypatch.setattr(
            "src.ingestion.extract_flights.REQUEST_TIMEOUT",
            5,
        )

        result = fetch_flights("LAX", "JFK", "2026-04-15")
        assert result.get("status") is True
        assert call_count == 2


class TestUploadToS3:
    """Tests for S3 upload with mocked boto3."""

    def test_upload_to_s3_puts_object_and_returns_uri(self) -> None:
        mock_s3 = MagicMock()
        with patch("src.ingestion.extract_flights.boto3.client", return_value=mock_s3):
            uri = upload_to_s3(
                {"status": True, "data": []},
                "year=2026/month=04/day=15/flight_data_20260317T120000Z.json",
                bucket="test-bucket",
            )
        mock_s3.put_object.assert_called_once()
        call_kwargs = mock_s3.put_object.call_args.kwargs
        assert call_kwargs["Bucket"] == "test-bucket"
        assert call_kwargs["Key"] == (
            "year=2026/month=04/day=15/flight_data_20260317T120000Z.json"
        )
        assert call_kwargs["ContentType"] == "application/json"
        assert b'"status": true' in call_kwargs["Body"]
        assert uri == (
            "s3://test-bucket/year=2026/month=04/day=15/"
            "flight_data_20260317T120000Z.json"
        )

    def test_upload_to_s3_uses_env_bucket_when_bucket_not_passed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BRONZE_BUCKET", "env-bucket")
        mock_s3 = MagicMock()
        with patch("src.ingestion.extract_flights.boto3.client", return_value=mock_s3):
            uri = upload_to_s3(
                {"status": True},
                "year=2026/month=01/day=01/flight.json",
            )
        assert mock_s3.put_object.call_args.kwargs["Bucket"] == "env-bucket"
        assert uri == "s3://env-bucket/year=2026/month=01/day=01/flight.json"


class TestExtractAndUpload:
    """Tests for extract_and_upload with mocked API and S3."""

    def test_extract_and_upload_fetches_and_uploads(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
        mock_s3 = MagicMock()

        def mock_get(*args: object, **kwargs: object) -> requests.Response:
            resp = requests.Response()
            resp.status_code = 200
            resp._content = b'{"status": true, "data": [{"id": "f1"}]}'
            return resp

        with (
            patch("src.ingestion.extract_flights.requests.get", side_effect=mock_get),
            patch("src.ingestion.extract_flights.boto3.client", return_value=mock_s3),
        ):
            uri = extract_and_upload("LAX", "JFK", "2026-04-15")

        mock_s3.put_object.assert_called_once()
        call_kwargs = mock_s3.put_object.call_args.kwargs
        assert call_kwargs["Bucket"]
        assert "year=2026/month=04/day=15" in call_kwargs["Key"]
        assert "flight_data_" in call_kwargs["Key"]
        assert call_kwargs["Key"].endswith(".json")
        body = call_kwargs["Body"].decode("utf-8")
        assert '"status": true' in body
        assert '"id": "f1"' in body
        assert uri.startswith("s3://")
        assert uri.endswith(".json")
