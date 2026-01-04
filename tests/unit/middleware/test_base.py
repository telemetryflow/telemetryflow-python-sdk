"""Unit tests for the base middleware module."""

from unittest import mock

import pytest

from telemetryflow.client import TelemetryFlowClient
from telemetryflow.domain.config import TelemetryConfig
from telemetryflow.domain.credentials import Credentials
from telemetryflow.middleware.base import TelemetryMiddleware


@pytest.fixture
def valid_config() -> TelemetryConfig:
    """Create valid config for testing."""
    return TelemetryConfig(
        credentials=Credentials.create("tfk_test_key", "tfs_test_secret"),
        endpoint="localhost:4317",
        service_name="test-service",
    )


@pytest.fixture
def client(valid_config: TelemetryConfig) -> TelemetryFlowClient:
    """Create client for testing."""
    client = TelemetryFlowClient(valid_config)
    client.initialize()
    yield client
    client.shutdown()


class ConcreteTelemetryMiddleware(TelemetryMiddleware):
    """Concrete implementation for testing."""

    def __call__(self, *_args: object, **_kwargs: object) -> None:
        """Process a request."""
        return None


class TestTelemetryMiddlewareInit:
    """Tests for TelemetryMiddleware initialization."""

    def test_default_options(self, client: TelemetryFlowClient) -> None:
        """Test default initialization options."""
        middleware = ConcreteTelemetryMiddleware(client)

        assert middleware._client == client
        assert middleware._record_duration is True
        assert middleware._record_count is True
        assert middleware._record_errors is True
        assert middleware._excluded_paths == set()

    def test_custom_options(self, client: TelemetryFlowClient) -> None:
        """Test custom initialization options."""
        middleware = ConcreteTelemetryMiddleware(
            client,
            record_request_duration=False,
            record_request_count=False,
            record_error_count=False,
            excluded_paths=["/health", "/metrics"],
        )

        assert middleware._record_duration is False
        assert middleware._record_count is False
        assert middleware._record_errors is False
        assert middleware._excluded_paths == {"/health", "/metrics"}

    def test_excluded_paths_is_set(self, client: TelemetryFlowClient) -> None:
        """Test that excluded_paths is converted to a set."""
        middleware = ConcreteTelemetryMiddleware(
            client,
            excluded_paths=["/a", "/b", "/a"],  # duplicate
        )

        assert middleware._excluded_paths == {"/a", "/b"}


class TestShouldInstrument:
    """Tests for should_instrument method."""

    def test_instrument_when_no_exclusions(self, client: TelemetryFlowClient) -> None:
        """Test that paths are instrumented when no exclusions."""
        middleware = ConcreteTelemetryMiddleware(client)

        assert middleware.should_instrument("/api/users") is True
        assert middleware.should_instrument("/health") is True
        assert middleware.should_instrument("/") is True

    def test_exclude_exact_match(self, client: TelemetryFlowClient) -> None:
        """Test that exact matches are excluded."""
        middleware = ConcreteTelemetryMiddleware(
            client,
            excluded_paths=["/health", "/metrics"],
        )

        assert middleware.should_instrument("/health") is False
        assert middleware.should_instrument("/metrics") is False
        assert middleware.should_instrument("/api/users") is True

    def test_exclude_prefix_match(self, client: TelemetryFlowClient) -> None:
        """Test that prefix matches with wildcard are excluded."""
        middleware = ConcreteTelemetryMiddleware(
            client,
            excluded_paths=["/api/internal/*"],
        )

        assert middleware.should_instrument("/api/internal/secret") is False
        assert middleware.should_instrument("/api/internal/data") is False
        assert middleware.should_instrument("/api/public/data") is True
        assert middleware.should_instrument("/api/internal") is True  # No trailing /

    def test_exclude_multiple_wildcards(self, client: TelemetryFlowClient) -> None:
        """Test multiple wildcard exclusions."""
        middleware = ConcreteTelemetryMiddleware(
            client,
            excluded_paths=["/health/*", "/metrics/*", "/internal/*"],
        )

        assert middleware.should_instrument("/health/ready") is False
        assert middleware.should_instrument("/metrics/prometheus") is False
        assert middleware.should_instrument("/internal/debug") is False
        assert middleware.should_instrument("/api/users") is True


class TestStartRequest:
    """Tests for start_request method."""

    def test_starts_span(self, client: TelemetryFlowClient) -> None:
        """Test that a span is started."""
        middleware = ConcreteTelemetryMiddleware(client)

        span_id, start_time = middleware.start_request("GET", "/api/users")

        assert span_id is not None
        assert isinstance(span_id, str)
        assert start_time > 0

    def test_span_name_format(self, client: TelemetryFlowClient) -> None:
        """Test span name format."""
        middleware = ConcreteTelemetryMiddleware(client)

        with mock.patch.object(client, "start_span") as mock_start:
            mock_start.return_value = "span-123"

            middleware.start_request("POST", "/api/users")

            mock_start.assert_called_once()
            span_name = mock_start.call_args[0][0]
            assert span_name == "HTTP POST /api/users"

    def test_includes_basic_attributes(self, client: TelemetryFlowClient) -> None:
        """Test that basic attributes are included."""
        middleware = ConcreteTelemetryMiddleware(client)

        with mock.patch.object(client, "start_span") as mock_start:
            mock_start.return_value = "span-123"

            middleware.start_request("GET", "/api/users")

            call_args = mock_start.call_args
            attributes = call_args[0][2]
            assert attributes["http.method"] == "GET"
            assert attributes["http.url"] == "/api/users"

    def test_includes_header_attributes(self, client: TelemetryFlowClient) -> None:
        """Test that header attributes are included."""
        middleware = ConcreteTelemetryMiddleware(client)

        with mock.patch.object(client, "start_span") as mock_start:
            mock_start.return_value = "span-123"

            middleware.start_request(
                "GET",
                "/api/users",
                headers={
                    "user-agent": "TestClient/1.0",
                    "host": "api.example.com",
                },
            )

            call_args = mock_start.call_args
            attributes = call_args[0][2]
            assert attributes["http.user_agent"] == "TestClient/1.0"
            assert attributes["http.host"] == "api.example.com"

    def test_records_counter_when_enabled(self, client: TelemetryFlowClient) -> None:
        """Test that request counter is recorded when enabled."""
        middleware = ConcreteTelemetryMiddleware(client, record_request_count=True)

        with mock.patch.object(client, "increment_counter") as mock_counter:
            middleware.start_request("GET", "/api/users")

            mock_counter.assert_called_once_with(
                "http.requests.total",
                attributes={"method": "GET", "path": "/api/users"},
            )

    def test_no_counter_when_disabled(self, client: TelemetryFlowClient) -> None:
        """Test that request counter is not recorded when disabled."""
        middleware = ConcreteTelemetryMiddleware(client, record_request_count=False)

        with mock.patch.object(client, "increment_counter") as mock_counter:
            middleware.start_request("GET", "/api/users")

            mock_counter.assert_not_called()


class TestEndRequest:
    """Tests for end_request method."""

    def test_records_duration_when_enabled(self, client: TelemetryFlowClient) -> None:
        """Test that duration histogram is recorded when enabled."""
        middleware = ConcreteTelemetryMiddleware(client, record_request_duration=True)

        with mock.patch.object(client, "record_histogram") as mock_histogram:
            middleware.end_request(
                span_id="span-123",
                start_time=0.0,
                method="GET",
                path="/api/users",
                status_code=200,
            )

            mock_histogram.assert_called_once()
            call_kwargs = mock_histogram.call_args[1]
            assert call_kwargs["unit"] == "s"
            assert call_kwargs["attributes"]["method"] == "GET"
            assert call_kwargs["attributes"]["path"] == "/api/users"
            assert call_kwargs["attributes"]["status_code"] == 200

    def test_no_duration_when_disabled(self, client: TelemetryFlowClient) -> None:
        """Test that duration is not recorded when disabled."""
        middleware = ConcreteTelemetryMiddleware(client, record_request_duration=False)

        with mock.patch.object(client, "record_histogram") as mock_histogram:
            middleware.end_request(
                span_id="span-123",
                start_time=0.0,
                method="GET",
                path="/api/users",
                status_code=200,
            )

            mock_histogram.assert_not_called()

    def test_records_error_counter_for_4xx(self, client: TelemetryFlowClient) -> None:
        """Test that error counter is recorded for 4xx status codes."""
        middleware = ConcreteTelemetryMiddleware(client, record_error_count=True)

        with mock.patch.object(client, "increment_counter") as mock_counter:
            middleware.end_request(
                span_id="span-123",
                start_time=0.0,
                method="GET",
                path="/api/users",
                status_code=404,
            )

            mock_counter.assert_called_once_with(
                "http.errors.total",
                attributes={
                    "method": "GET",
                    "path": "/api/users",
                    "status_code": 404,
                },
            )

    def test_records_error_counter_for_5xx(self, client: TelemetryFlowClient) -> None:
        """Test that error counter is recorded for 5xx status codes."""
        middleware = ConcreteTelemetryMiddleware(client, record_error_count=True)

        with (
            mock.patch.object(client, "increment_counter") as mock_counter,
            mock.patch.object(client, "log_error") as mock_log,
        ):
            middleware.end_request(
                span_id="span-123",
                start_time=0.0,
                method="GET",
                path="/api/users",
                status_code=500,
            )

            mock_counter.assert_called_once()
            mock_log.assert_called_once()

    def test_logs_error_for_5xx(self, client: TelemetryFlowClient) -> None:
        """Test that error is logged for 5xx status codes."""
        middleware = ConcreteTelemetryMiddleware(client, record_error_count=True)

        with mock.patch.object(client, "log_error") as mock_log:
            middleware.end_request(
                span_id="span-123",
                start_time=0.0,
                method="GET",
                path="/api/users",
                status_code=503,
            )

            mock_log.assert_called_once()
            call_args = mock_log.call_args[0]
            assert "HTTP 503 error" in call_args[0]
            assert "GET" in call_args[0]
            assert "/api/users" in call_args[0]

    def test_no_error_counter_when_disabled(self, client: TelemetryFlowClient) -> None:
        """Test that error counter is not recorded when disabled."""
        middleware = ConcreteTelemetryMiddleware(client, record_error_count=False)

        with mock.patch.object(client, "increment_counter") as mock_counter:
            middleware.end_request(
                span_id="span-123",
                start_time=0.0,
                method="GET",
                path="/api/users",
                status_code=500,
            )

            mock_counter.assert_not_called()

    def test_no_error_counter_for_2xx(self, client: TelemetryFlowClient) -> None:
        """Test that error counter is not recorded for 2xx status codes."""
        middleware = ConcreteTelemetryMiddleware(client, record_error_count=True)

        with mock.patch.object(client, "increment_counter") as mock_counter:
            middleware.end_request(
                span_id="span-123",
                start_time=0.0,
                method="GET",
                path="/api/users",
                status_code=200,
            )

            mock_counter.assert_not_called()

    def test_adds_span_event(self, client: TelemetryFlowClient) -> None:
        """Test that span event is added."""
        middleware = ConcreteTelemetryMiddleware(client)

        with mock.patch.object(client, "add_span_event") as mock_event:
            middleware.end_request(
                span_id="span-123",
                start_time=0.0,
                method="GET",
                path="/api/users",
                status_code=200,
            )

            mock_event.assert_called_once_with(
                "span-123",
                "response_sent",
                {"http.status_code": 200},
            )

    def test_ends_span(self, client: TelemetryFlowClient) -> None:
        """Test that span is ended."""
        middleware = ConcreteTelemetryMiddleware(client)

        with mock.patch.object(client, "end_span") as mock_end:
            middleware.end_request(
                span_id="span-123",
                start_time=0.0,
                method="GET",
                path="/api/users",
                status_code=200,
            )

            mock_end.assert_called_once_with("span-123", None)

    def test_ends_span_with_error(self, client: TelemetryFlowClient) -> None:
        """Test that span is ended with error."""
        middleware = ConcreteTelemetryMiddleware(client)
        error = ValueError("Test error")

        with mock.patch.object(client, "end_span") as mock_end:
            middleware.end_request(
                span_id="span-123",
                start_time=0.0,
                method="GET",
                path="/api/users",
                status_code=500,
                error=error,
            )

            mock_end.assert_called_once_with("span-123", error)
