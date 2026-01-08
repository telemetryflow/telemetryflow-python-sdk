"""Unit tests for the FastAPI middleware module."""

from unittest import mock

import pytest

from telemetryflow.client import TelemetryFlowClient
from telemetryflow.domain.config import TelemetryConfig
from telemetryflow.domain.credentials import Credentials
from telemetryflow.middleware.fastapi import (
    FastAPITelemetryMiddleware,
    create_fastapi_middleware,
)


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
def mock_asgi_app():
    """Create a mock ASGI app."""

    async def app(_scope: dict, _receive: object, send: object) -> None:
        await send({"type": "http.response.start", "status": 200})
        await send({"type": "http.response.body", "body": b"OK"})

    return app


@pytest.fixture
def http_scope():
    """Create an HTTP scope dict."""
    return {
        "type": "http",
        "path": "/api/users",
        "method": "GET",
        "headers": [
            (b"user-agent", b"TestClient/1.0"),
            (b"host", b"localhost"),
        ],
    }


@pytest.fixture
def websocket_scope():
    """Create a WebSocket scope dict."""
    return {
        "type": "websocket",
        "path": "/ws",
    }


class TestFastAPITelemetryMiddlewareInit:
    """Tests for FastAPITelemetryMiddleware initialization."""

    def test_init(self, client: TelemetryFlowClient, mock_asgi_app) -> None:
        """Test middleware initialization."""
        middleware = FastAPITelemetryMiddleware(mock_asgi_app, client)

        assert middleware._asgi_app == mock_asgi_app
        assert middleware._client == client

    def test_init_with_options(self, client: TelemetryFlowClient, mock_asgi_app) -> None:
        """Test middleware initialization with options."""
        middleware = FastAPITelemetryMiddleware(
            mock_asgi_app,
            client,
            record_request_duration=False,
            excluded_paths=["/health"],
        )

        assert middleware._record_duration is False
        assert "/health" in middleware._excluded_paths


class TestFastAPITelemetryMiddlewareCall:
    """Tests for FastAPITelemetryMiddleware __call__ method."""

    @pytest.mark.asyncio
    async def test_passes_through_non_http_requests(
        self, client: TelemetryFlowClient, mock_asgi_app, websocket_scope
    ) -> None:
        """Test that non-HTTP requests are passed through."""
        middleware = FastAPITelemetryMiddleware(mock_asgi_app, client)

        receive = mock.AsyncMock()
        send = mock.AsyncMock()

        with mock.patch.object(middleware, "start_request") as mock_start:
            await middleware(websocket_scope, receive, send)

            mock_start.assert_not_called()

    @pytest.mark.asyncio
    async def test_passes_through_excluded_paths(
        self, client: TelemetryFlowClient, mock_asgi_app, http_scope
    ) -> None:
        """Test that excluded paths are passed through."""
        middleware = FastAPITelemetryMiddleware(
            mock_asgi_app, client, excluded_paths=["/api/users"]
        )

        receive = mock.AsyncMock()
        send = mock.AsyncMock()

        with mock.patch.object(middleware, "start_request") as mock_start:
            await middleware(http_scope, receive, send)

            mock_start.assert_not_called()

    @pytest.mark.asyncio
    async def test_instruments_http_requests(
        self, client: TelemetryFlowClient, mock_asgi_app, http_scope
    ) -> None:
        """Test that HTTP requests are instrumented."""
        middleware = FastAPITelemetryMiddleware(mock_asgi_app, client)

        receive = mock.AsyncMock()
        send = mock.AsyncMock()

        with (
            mock.patch.object(
                middleware, "start_request", return_value=("span-123", 0.0)
            ) as mock_start,
            mock.patch.object(middleware, "end_request") as mock_end,
        ):
            await middleware(http_scope, receive, send)

            mock_start.assert_called_once()
            mock_end.assert_called_once()

    @pytest.mark.asyncio
    async def test_extracts_path_from_scope(
        self, client: TelemetryFlowClient, mock_asgi_app
    ) -> None:
        """Test that path is extracted from scope."""
        middleware = FastAPITelemetryMiddleware(mock_asgi_app, client)
        scope = {
            "type": "http",
            "path": "/custom/path",
            "method": "POST",
            "headers": [],
        }

        receive = mock.AsyncMock()
        send = mock.AsyncMock()

        with (
            mock.patch.object(
                middleware, "start_request", return_value=("span-123", 0.0)
            ) as mock_start,
            mock.patch.object(middleware, "end_request"),
        ):
            await middleware(scope, receive, send)

            call_args = mock_start.call_args[0]
            assert call_args[0] == "POST"
            assert call_args[1] == "/custom/path"

    @pytest.mark.asyncio
    async def test_extracts_headers_from_scope(
        self, client: TelemetryFlowClient, mock_asgi_app
    ) -> None:
        """Test that headers are extracted from scope."""
        middleware = FastAPITelemetryMiddleware(mock_asgi_app, client)
        scope = {
            "type": "http",
            "path": "/api",
            "method": "GET",
            "headers": [
                (b"user-agent", b"TestAgent"),
                (b"host", b"example.com"),
                (b"x-custom", b"value"),
            ],
        }

        receive = mock.AsyncMock()
        send = mock.AsyncMock()

        with (
            mock.patch.object(
                middleware, "start_request", return_value=("span-123", 0.0)
            ) as mock_start,
            mock.patch.object(middleware, "end_request"),
        ):
            await middleware(scope, receive, send)

            call_args = mock_start.call_args[0]
            headers = call_args[2]
            assert headers["user-agent"] == "TestAgent"
            assert headers["host"] == "example.com"
            assert headers["x-custom"] == "value"

    @pytest.mark.asyncio
    async def test_captures_status_code(self, client: TelemetryFlowClient, http_scope) -> None:
        """Test that status code is captured."""

        async def app(_scope: dict, _receive: object, send: object) -> None:
            await send({"type": "http.response.start", "status": 201})
            await send({"type": "http.response.body", "body": b""})

        middleware = FastAPITelemetryMiddleware(app, client)

        receive = mock.AsyncMock()
        send = mock.AsyncMock()

        with (
            mock.patch.object(middleware, "start_request", return_value=("span-123", 0.0)),
            mock.patch.object(middleware, "end_request") as mock_end,
        ):
            await middleware(http_scope, receive, send)

            # end_request is called with positional args
            call_args = mock_end.call_args[0]
            # status_code is the 5th positional argument
            assert call_args[4] == 201

    @pytest.mark.asyncio
    async def test_captures_error_status_code(
        self, client: TelemetryFlowClient, http_scope
    ) -> None:
        """Test that error status code is captured."""

        async def app(_scope: dict, _receive: object, send: object) -> None:
            await send({"type": "http.response.start", "status": 500})
            await send({"type": "http.response.body", "body": b"Error"})

        middleware = FastAPITelemetryMiddleware(app, client)

        receive = mock.AsyncMock()
        send = mock.AsyncMock()

        with (
            mock.patch.object(middleware, "start_request", return_value=("span-123", 0.0)),
            mock.patch.object(middleware, "end_request") as mock_end,
        ):
            await middleware(http_scope, receive, send)

            call_args = mock_end.call_args[0]
            assert call_args[4] == 500

    @pytest.mark.asyncio
    async def test_handles_exception(self, client: TelemetryFlowClient, http_scope) -> None:
        """Test that exceptions are handled and re-raised."""
        error = ValueError("Test error")

        async def app(_scope: dict, _receive: object, _send: object) -> None:
            raise error

        middleware = FastAPITelemetryMiddleware(app, client)

        receive = mock.AsyncMock()
        send = mock.AsyncMock()

        with (
            mock.patch.object(middleware, "start_request", return_value=("span-123", 0.0)),
            mock.patch.object(middleware, "end_request") as mock_end,
        ):
            with pytest.raises(ValueError, match="Test error"):
                await middleware(http_scope, receive, send)

            # end_request should still be called
            mock_end.assert_called_once()
            call_args = mock_end.call_args[0]
            # error is the 6th positional argument
            assert call_args[5] == error

    @pytest.mark.asyncio
    async def test_default_status_code_on_exception(
        self, client: TelemetryFlowClient, http_scope
    ) -> None:
        """Test that default 500 status code is used on exception."""

        async def app(_scope: dict, _receive: object, _send: object) -> None:
            raise RuntimeError("Server error")

        middleware = FastAPITelemetryMiddleware(app, client)

        receive = mock.AsyncMock()
        send = mock.AsyncMock()

        with (
            mock.patch.object(middleware, "start_request", return_value=("span-123", 0.0)),
            mock.patch.object(middleware, "end_request") as mock_end,
        ):
            with pytest.raises(RuntimeError):
                await middleware(http_scope, receive, send)

            call_args = mock_end.call_args[0]
            assert call_args[4] == 500

    @pytest.mark.asyncio
    async def test_default_path_when_not_in_scope(
        self, client: TelemetryFlowClient, mock_asgi_app
    ) -> None:
        """Test default path when not in scope."""
        middleware = FastAPITelemetryMiddleware(mock_asgi_app, client)
        scope = {
            "type": "http",
            "method": "GET",
            "headers": [],
        }

        receive = mock.AsyncMock()
        send = mock.AsyncMock()

        with (
            mock.patch.object(
                middleware, "start_request", return_value=("span-123", 0.0)
            ) as mock_start,
            mock.patch.object(middleware, "end_request"),
        ):
            await middleware(scope, receive, send)

            call_args = mock_start.call_args[0]
            assert call_args[1] == "/"

    @pytest.mark.asyncio
    async def test_default_method_when_not_in_scope(
        self, client: TelemetryFlowClient, mock_asgi_app
    ) -> None:
        """Test default method when not in scope."""
        middleware = FastAPITelemetryMiddleware(mock_asgi_app, client)
        scope = {
            "type": "http",
            "path": "/api",
            "headers": [],
        }

        receive = mock.AsyncMock()
        send = mock.AsyncMock()

        with (
            mock.patch.object(
                middleware, "start_request", return_value=("span-123", 0.0)
            ) as mock_start,
            mock.patch.object(middleware, "end_request"),
        ):
            await middleware(scope, receive, send)

            call_args = mock_start.call_args[0]
            assert call_args[0] == "GET"


class TestCreateFastapiMiddleware:
    """Tests for create_fastapi_middleware factory function."""

    def test_creates_factory(self, client: TelemetryFlowClient) -> None:
        """Test that factory function is created."""
        factory = create_fastapi_middleware(client)

        assert callable(factory)

    def test_factory_creates_middleware(self, client: TelemetryFlowClient, mock_asgi_app) -> None:
        """Test that factory creates middleware."""
        factory = create_fastapi_middleware(client)
        middleware = factory(mock_asgi_app)

        assert isinstance(middleware, FastAPITelemetryMiddleware)
        assert middleware._asgi_app == mock_asgi_app
        assert middleware._client == client

    def test_factory_passes_options(self, client: TelemetryFlowClient, mock_asgi_app) -> None:
        """Test that factory passes options to middleware."""
        factory = create_fastapi_middleware(
            client,
            record_request_duration=False,
            excluded_paths=["/health"],
        )
        middleware = factory(mock_asgi_app)

        assert middleware._record_duration is False
        assert "/health" in middleware._excluded_paths
