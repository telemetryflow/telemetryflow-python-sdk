"""Unit tests for the Flask middleware module."""

from unittest import mock

import pytest

# Skip all tests in this module if Flask is not installed
flask = pytest.importorskip("flask")

from telemetryflow.client import TelemetryFlowClient  # noqa: E402
from telemetryflow.domain.config import TelemetryConfig  # noqa: E402
from telemetryflow.domain.credentials import Credentials  # noqa: E402
from telemetryflow.middleware.flask import FlaskTelemetryMiddleware  # noqa: E402


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


@pytest.fixture
def mock_flask_app():
    """Create a mock Flask app."""
    app = mock.Mock()
    app.before_request = mock.Mock()
    app.after_request = mock.Mock()
    app.teardown_request = mock.Mock()
    return app


@pytest.fixture
def mock_flask_g():
    """Create a mock for Flask's g object."""
    return mock.MagicMock()


@pytest.fixture
def mock_flask_request():
    """Create a mock for Flask's request object."""
    return mock.MagicMock()


class TestFlaskTelemetryMiddlewareInit:
    """Tests for FlaskTelemetryMiddleware initialization."""

    def test_init_without_app(self, client: TelemetryFlowClient) -> None:
        """Test middleware initialization without app."""
        middleware = FlaskTelemetryMiddleware(client)

        assert middleware._client == client
        assert middleware._app is None

    def test_init_with_app(self, client: TelemetryFlowClient, mock_flask_app) -> None:
        """Test middleware initialization with app."""
        middleware = FlaskTelemetryMiddleware(client, app=mock_flask_app)

        assert middleware._app == mock_flask_app
        mock_flask_app.before_request.assert_called_once()
        mock_flask_app.after_request.assert_called_once()
        mock_flask_app.teardown_request.assert_called_once()

    def test_init_with_options(self, client: TelemetryFlowClient) -> None:
        """Test middleware initialization with options."""
        middleware = FlaskTelemetryMiddleware(
            client,
            record_request_duration=False,
            excluded_paths=["/health"],
        )

        assert middleware._record_duration is False
        assert "/health" in middleware._excluded_paths


class TestFlaskTelemetryMiddlewareInitApp:
    """Tests for FlaskTelemetryMiddleware init_app method."""

    def test_init_app(self, client: TelemetryFlowClient, mock_flask_app) -> None:
        """Test init_app registers hooks."""
        middleware = FlaskTelemetryMiddleware(client)
        middleware.init_app(mock_flask_app)

        assert middleware._app == mock_flask_app
        mock_flask_app.before_request.assert_called_once()
        mock_flask_app.after_request.assert_called_once()
        mock_flask_app.teardown_request.assert_called_once()

    def test_init_app_registers_before_request(
        self, client: TelemetryFlowClient, mock_flask_app
    ) -> None:
        """Test that before_request hook is registered."""
        middleware = FlaskTelemetryMiddleware(client)
        middleware.init_app(mock_flask_app)

        call_args = mock_flask_app.before_request.call_args[0]
        assert callable(call_args[0])
        assert call_args[0] == middleware._before_request

    def test_init_app_registers_after_request(
        self, client: TelemetryFlowClient, mock_flask_app
    ) -> None:
        """Test that after_request hook is registered."""
        middleware = FlaskTelemetryMiddleware(client)
        middleware.init_app(mock_flask_app)

        call_args = mock_flask_app.after_request.call_args[0]
        assert callable(call_args[0])
        assert call_args[0] == middleware._after_request

    def test_init_app_registers_teardown_request(
        self, client: TelemetryFlowClient, mock_flask_app
    ) -> None:
        """Test that teardown_request hook is registered."""
        middleware = FlaskTelemetryMiddleware(client)
        middleware.init_app(mock_flask_app)

        call_args = mock_flask_app.teardown_request.call_args[0]
        assert callable(call_args[0])
        assert call_args[0] == middleware._teardown_request


class TestFlaskTelemetryMiddlewareBeforeRequest:
    """Tests for FlaskTelemetryMiddleware _before_request method."""

    def test_skips_excluded_paths(self, client: TelemetryFlowClient) -> None:
        """Test that excluded paths are skipped."""
        middleware = FlaskTelemetryMiddleware(client, excluded_paths=["/health"])

        mock_g = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_request.path = "/health"

        with (
            mock.patch("flask.g", mock_g),
            mock.patch("flask.request", mock_request),
            mock.patch.object(middleware, "start_request") as mock_start,
        ):
            middleware._before_request()

            assert mock_g._telemetry_skip is True
            mock_start.assert_not_called()

    def test_instruments_request(self, client: TelemetryFlowClient) -> None:
        """Test that requests are instrumented."""
        middleware = FlaskTelemetryMiddleware(client)

        mock_g = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_request.path = "/api/users"
        mock_request.method = "GET"
        mock_request.headers = {"User-Agent": "Test", "Host": "localhost"}

        with (
            mock.patch("flask.g", mock_g),
            mock.patch("flask.request", mock_request),
            mock.patch.object(
                middleware, "start_request", return_value=("span-123", 0.5)
            ) as mock_start,
        ):
            middleware._before_request()

            mock_start.assert_called_once()
            assert mock_g._telemetry_skip is False
            assert mock_g._telemetry_span_id == "span-123"
            assert mock_g._telemetry_start_time == 0.5

    def test_lowercases_header_keys(self, client: TelemetryFlowClient) -> None:
        """Test that header keys are lowercased."""
        middleware = FlaskTelemetryMiddleware(client)

        mock_g = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_request.path = "/api"
        mock_request.method = "GET"
        mock_request.headers = {"User-Agent": "Test", "Content-Type": "json"}

        with (
            mock.patch("flask.g", mock_g),
            mock.patch("flask.request", mock_request),
            mock.patch.object(
                middleware, "start_request", return_value=("span-123", 0.0)
            ) as mock_start,
        ):
            middleware._before_request()

            call_args = mock_start.call_args[0]
            headers = call_args[2]
            assert "user-agent" in headers
            assert "content-type" in headers


class TestFlaskTelemetryMiddlewareAfterRequest:
    """Tests for FlaskTelemetryMiddleware _after_request method."""

    def test_skips_when_telemetry_skip_true(self, client: TelemetryFlowClient) -> None:
        """Test that response is returned unchanged when skip is True."""
        middleware = FlaskTelemetryMiddleware(client)

        mock_g = mock.MagicMock()
        mock_g._telemetry_skip = True
        mock_response = mock.MagicMock()

        with (
            mock.patch("flask.g", mock_g),
            mock.patch.object(middleware, "end_request") as mock_end,
        ):
            result = middleware._after_request(mock_response)

            assert result == mock_response
            mock_end.assert_not_called()

    def test_skips_when_telemetry_skip_not_set(self, client: TelemetryFlowClient) -> None:
        """Test that response is returned unchanged when skip not set."""
        middleware = FlaskTelemetryMiddleware(client)

        mock_g = mock.MagicMock(spec=[])  # No _telemetry_skip attribute
        mock_response = mock.MagicMock()

        with (
            mock.patch("flask.g", mock_g),
            mock.patch.object(middleware, "end_request") as mock_end,
        ):
            result = middleware._after_request(mock_response)

            assert result == mock_response
            mock_end.assert_not_called()

    def test_ends_request(self, client: TelemetryFlowClient) -> None:
        """Test that request is ended."""
        middleware = FlaskTelemetryMiddleware(client)

        mock_g = mock.MagicMock()
        mock_g._telemetry_skip = False
        mock_g._telemetry_span_id = "span-123"
        mock_g._telemetry_start_time = 0.5
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_request = mock.MagicMock()
        mock_request.method = "GET"
        mock_request.path = "/api/users"

        with (
            mock.patch("flask.g", mock_g),
            mock.patch("flask.request", mock_request),
            mock.patch.object(middleware, "end_request") as mock_end,
        ):
            result = middleware._after_request(mock_response)

            assert result == mock_response
            mock_end.assert_called_once_with(
                "span-123",
                0.5,
                "GET",
                "/api/users",
                200,
            )

    def test_skips_when_span_id_not_set(self, client: TelemetryFlowClient) -> None:
        """Test that end_request is skipped when span_id not set."""
        middleware = FlaskTelemetryMiddleware(client)

        mock_g = mock.MagicMock()
        mock_g._telemetry_skip = False
        mock_g._telemetry_span_id = None
        mock_g._telemetry_start_time = 0.5
        mock_response = mock.MagicMock()

        with (
            mock.patch("flask.g", mock_g),
            mock.patch.object(middleware, "end_request") as mock_end,
        ):
            result = middleware._after_request(mock_response)

            assert result == mock_response
            mock_end.assert_not_called()

    def test_skips_when_start_time_not_set(self, client: TelemetryFlowClient) -> None:
        """Test that end_request is skipped when start_time not set."""
        middleware = FlaskTelemetryMiddleware(client)

        mock_g = mock.MagicMock()
        mock_g._telemetry_skip = False
        mock_g._telemetry_span_id = "span-123"
        mock_g._telemetry_start_time = None
        mock_response = mock.MagicMock()

        with (
            mock.patch("flask.g", mock_g),
            mock.patch.object(middleware, "end_request") as mock_end,
        ):
            result = middleware._after_request(mock_response)

            assert result == mock_response
            mock_end.assert_not_called()


class TestFlaskTelemetryMiddlewareTeardownRequest:
    """Tests for FlaskTelemetryMiddleware _teardown_request method."""

    def test_skips_when_telemetry_skip_true(self, client: TelemetryFlowClient) -> None:
        """Test that teardown is skipped when skip is True."""
        middleware = FlaskTelemetryMiddleware(client)

        mock_g = mock.MagicMock()
        mock_g._telemetry_skip = True

        with (
            mock.patch("flask.g", mock_g),
            mock.patch.object(middleware, "end_request") as mock_end,
        ):
            middleware._teardown_request(ValueError("Test error"))

            mock_end.assert_not_called()

    def test_skips_when_no_exception(self, client: TelemetryFlowClient) -> None:
        """Test that teardown does nothing when no exception."""
        middleware = FlaskTelemetryMiddleware(client)

        mock_g = mock.MagicMock()
        mock_g._telemetry_skip = False

        with (
            mock.patch("flask.g", mock_g),
            mock.patch.object(middleware, "end_request") as mock_end,
        ):
            middleware._teardown_request(None)

            mock_end.assert_not_called()

    def test_ends_request_on_exception(self, client: TelemetryFlowClient) -> None:
        """Test that request is ended on exception."""
        middleware = FlaskTelemetryMiddleware(client)
        error = ValueError("Test error")

        mock_g = mock.MagicMock()
        mock_g._telemetry_skip = False
        mock_g._telemetry_span_id = "span-123"
        mock_g._telemetry_start_time = 0.5
        mock_request = mock.MagicMock()
        mock_request.method = "GET"
        mock_request.path = "/api/users"

        with (
            mock.patch("flask.g", mock_g),
            mock.patch("flask.request", mock_request),
            mock.patch.object(middleware, "end_request") as mock_end,
        ):
            middleware._teardown_request(error)

            mock_end.assert_called_once_with(
                "span-123",
                0.5,
                "GET",
                "/api/users",
                500,
                error,
            )

    def test_passes_none_for_non_exception(self, client: TelemetryFlowClient) -> None:
        """Test that None is passed when exception is not an Exception type."""
        middleware = FlaskTelemetryMiddleware(client)
        # BaseException that is not Exception
        error = SystemExit()

        mock_g = mock.MagicMock()
        mock_g._telemetry_skip = False
        mock_g._telemetry_span_id = "span-123"
        mock_g._telemetry_start_time = 0.5
        mock_request = mock.MagicMock()
        mock_request.method = "GET"
        mock_request.path = "/api"

        with (
            mock.patch("flask.g", mock_g),
            mock.patch("flask.request", mock_request),
            mock.patch.object(middleware, "end_request") as mock_end,
        ):
            middleware._teardown_request(error)

            call_args = mock_end.call_args
            # Last positional arg should be None since SystemExit is not Exception
            assert call_args[0][5] is None

    def test_skips_when_span_id_not_set(self, client: TelemetryFlowClient) -> None:
        """Test that end_request is skipped when span_id not set."""
        middleware = FlaskTelemetryMiddleware(client)

        mock_g = mock.MagicMock()
        mock_g._telemetry_skip = False
        mock_g._telemetry_span_id = None
        mock_g._telemetry_start_time = 0.5

        with (
            mock.patch("flask.g", mock_g),
            mock.patch.object(middleware, "end_request") as mock_end,
        ):
            middleware._teardown_request(ValueError("Error"))

            mock_end.assert_not_called()


class TestFlaskTelemetryMiddlewareCall:
    """Tests for FlaskTelemetryMiddleware __call__ method."""

    def test_call_returns_none(self, client: TelemetryFlowClient) -> None:
        """Test that __call__ returns None (Flask uses hooks)."""
        middleware = FlaskTelemetryMiddleware(client)

        result = middleware()

        assert result is None
