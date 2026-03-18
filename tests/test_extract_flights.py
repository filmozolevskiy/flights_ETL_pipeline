"""Unit tests for flight extraction and retry logic."""

import pytest
import requests

from src.ingestion.extract_flights import (
    _is_retriable_http_error,
    fetch_flights,
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

    def test_connection_error_is_not_retriable(self) -> None:
        assert _is_retriable_http_error(requests.ConnectionError()) is False


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

        monkeypatch.setattr("requests.get", mock_get)
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
