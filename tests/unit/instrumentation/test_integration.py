"""Unit tests for the instrumentation integration module."""

from unittest import mock

import pytest

from telemetryflow.client import TelemetryFlowClient
from telemetryflow.domain.config import TelemetryConfig
from telemetryflow.domain.credentials import Credentials
from telemetryflow.instrumentation.integration import (
    TelemetryFlowInstrumentor,
    get_instrumentation_status,
    setup_auto_instrumentation,
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
    return TelemetryFlowClient(valid_config)


class TestSetupAutoInstrumentation:
    """Tests for setup_auto_instrumentation function."""

    @mock.patch("telemetryflow.instrumentation.integration.auto_instrument")
    def test_without_client(self, mock_auto_instrument: mock.Mock) -> None:
        """Test setup without client uses None providers."""
        mock_auto_instrument.return_value = {"flask": True}

        results = setup_auto_instrumentation(client=None)

        assert results == {"flask": True}
        call_args = mock_auto_instrument.call_args
        config = call_args.kwargs["config"]
        assert config.tracer_provider is None
        assert config.meter_provider is None

    @mock.patch("telemetryflow.instrumentation.integration.auto_instrument")
    def test_with_uninitialized_client(
        self, mock_auto_instrument: mock.Mock, client: TelemetryFlowClient
    ) -> None:
        """Test setup with uninitialized client uses None providers."""
        mock_auto_instrument.return_value = {"flask": True}

        results = setup_auto_instrumentation(client=client)

        assert results == {"flask": True}
        call_args = mock_auto_instrument.call_args
        config = call_args.kwargs["config"]
        assert config.tracer_provider is None
        assert config.meter_provider is None

    @mock.patch("telemetryflow.instrumentation.integration.auto_instrument")
    def test_passes_enable_flags(self, mock_auto_instrument: mock.Mock) -> None:
        """Test that enable flags are passed through."""
        mock_auto_instrument.return_value = {}

        setup_auto_instrumentation(
            enable_flask=False,
            enable_fastapi=False,
            enable_sqlalchemy=True,
            enable_requests=True,
            enable_httpx=False,
            enable_logging=False,
            enable_psycopg2=False,
            enable_redis=False,
        )

        call_args = mock_auto_instrument.call_args
        config = call_args.kwargs["config"]
        assert config.enable_flask is False
        assert config.enable_fastapi is False
        assert config.enable_sqlalchemy is True
        assert config.enable_requests is True
        assert config.enable_httpx is False
        assert config.enable_logging is False
        assert config.enable_psycopg2 is False
        assert config.enable_redis is False

    @mock.patch("telemetryflow.instrumentation.integration.auto_instrument")
    def test_passes_excluded_urls(self, mock_auto_instrument: mock.Mock) -> None:
        """Test that excluded_urls are passed through."""
        mock_auto_instrument.return_value = {}

        setup_auto_instrumentation(
            excluded_urls=["health", "metrics"],
            excluded_hosts=["localhost"],
        )

        call_args = mock_auto_instrument.call_args
        config = call_args.kwargs["config"]
        assert config.excluded_urls == ["health", "metrics"]
        assert config.excluded_hosts == ["localhost"]


class TestGetInstrumentationStatus:
    """Tests for get_instrumentation_status function."""

    @mock.patch("telemetryflow.instrumentation.integration.get_available_instrumentations")
    def test_returns_status_dict(self, mock_get_available: mock.Mock) -> None:
        """Test that status dict is returned."""
        mock_get_available.return_value = ["flask", "requests"]

        status = get_instrumentation_status()

        assert status["available_instrumentations"] == ["flask", "requests"]
        assert status["total_available"] == 2

    @mock.patch("telemetryflow.instrumentation.integration.get_available_instrumentations")
    def test_empty_when_none_available(self, mock_get_available: mock.Mock) -> None:
        """Test that empty status is returned when no instrumentations available."""
        mock_get_available.return_value = []

        status = get_instrumentation_status()

        assert status["available_instrumentations"] == []
        assert status["total_available"] == 0


class TestTelemetryFlowInstrumentor:
    """Tests for TelemetryFlowInstrumentor class."""

    def test_init(self, client: TelemetryFlowClient) -> None:
        """Test instrumentor initialization."""
        instrumentor = TelemetryFlowInstrumentor(client, enable_flask=False)

        assert instrumentor._client == client
        assert instrumentor._kwargs == {"enable_flask": False}
        assert instrumentor._results == {}
        assert instrumentor._initialized is False

    def test_init_without_client(self) -> None:
        """Test instrumentor initialization without client."""
        instrumentor = TelemetryFlowInstrumentor()

        assert instrumentor._client is None
        assert instrumentor._initialized is False

    @mock.patch("telemetryflow.instrumentation.integration.setup_auto_instrumentation")
    def test_instrument(self, mock_setup: mock.Mock, client: TelemetryFlowClient) -> None:
        """Test instrument method."""
        mock_setup.return_value = {"flask": True, "requests": True}

        instrumentor = TelemetryFlowInstrumentor(client)
        results = instrumentor.instrument()

        assert results == {"flask": True, "requests": True}
        assert instrumentor._initialized is True

    @mock.patch("telemetryflow.instrumentation.integration.setup_auto_instrumentation")
    def test_instrument_initializes_client(
        self, mock_setup: mock.Mock, client: TelemetryFlowClient
    ) -> None:
        """Test that instrument initializes client if not already initialized."""
        mock_setup.return_value = {}

        assert client.is_initialized() is False

        instrumentor = TelemetryFlowInstrumentor(client)
        instrumentor.instrument()

        assert client.is_initialized() is True
        client.shutdown()

    @mock.patch("telemetryflow.instrumentation.integration.setup_auto_instrumentation")
    def test_instrument_without_client(self, mock_setup: mock.Mock) -> None:
        """Test instrument without client."""
        mock_setup.return_value = {"flask": True}

        instrumentor = TelemetryFlowInstrumentor()
        results = instrumentor.instrument()

        assert results == {"flask": True}
        mock_setup.assert_called_once_with(client=None)

    def test_uninstrument_when_not_initialized(self, client: TelemetryFlowClient) -> None:
        """Test uninstrument does nothing when not initialized."""
        instrumentor = TelemetryFlowInstrumentor(client)

        # Should not raise
        instrumentor.uninstrument()

        assert instrumentor._initialized is False

    @mock.patch("telemetryflow.instrumentation.integration.setup_auto_instrumentation")
    def test_uninstrument_sets_initialized_false(
        self, mock_setup: mock.Mock, client: TelemetryFlowClient
    ) -> None:
        """Test uninstrument sets initialized to False."""
        mock_setup.return_value = {"flask": True}

        instrumentor = TelemetryFlowInstrumentor(client)
        instrumentor.instrument()

        assert instrumentor._initialized is True

        # Uninstrument - the try/except blocks will catch import errors
        instrumentor.uninstrument()

        assert instrumentor._initialized is False
        client.shutdown()

    @mock.patch("telemetryflow.instrumentation.integration.setup_auto_instrumentation")
    def test_active_property(self, mock_setup: mock.Mock, client: TelemetryFlowClient) -> None:
        """Test active property returns successful instrumentations."""
        mock_setup.return_value = {"flask": True, "requests": True, "redis": False}

        instrumentor = TelemetryFlowInstrumentor(client)
        instrumentor.instrument()

        active = instrumentor.active

        assert "flask" in active
        assert "requests" in active
        assert "redis" not in active

        client.shutdown()

    @mock.patch("telemetryflow.instrumentation.integration.setup_auto_instrumentation")
    def test_results_property(self, mock_setup: mock.Mock, client: TelemetryFlowClient) -> None:
        """Test results property returns copy of results."""
        mock_setup.return_value = {"flask": True, "requests": False}

        instrumentor = TelemetryFlowInstrumentor(client)
        instrumentor.instrument()

        results = instrumentor.results

        assert results == {"flask": True, "requests": False}
        # Should be a copy
        results["test"] = True
        assert "test" not in instrumentor.results

        client.shutdown()

    @mock.patch("telemetryflow.instrumentation.integration.setup_auto_instrumentation")
    def test_context_manager_enter(
        self, mock_setup: mock.Mock, client: TelemetryFlowClient
    ) -> None:
        """Test context manager enter."""
        mock_setup.return_value = {"flask": True}

        instrumentor = TelemetryFlowInstrumentor(client)

        with instrumentor as inst:
            assert inst is instrumentor
            assert inst._initialized is True

        client.shutdown()

    @mock.patch("telemetryflow.instrumentation.integration.setup_auto_instrumentation")
    def test_context_manager_exit_calls_shutdown(
        self, mock_setup: mock.Mock, client: TelemetryFlowClient
    ) -> None:
        """Test context manager exit calls client shutdown."""
        mock_setup.return_value = {}

        with TelemetryFlowInstrumentor(client) as _:
            assert client.is_initialized() is True

        assert client.is_initialized() is False

    @mock.patch("telemetryflow.instrumentation.integration.setup_auto_instrumentation")
    def test_context_manager_without_client(self, mock_setup: mock.Mock) -> None:
        """Test context manager without client."""
        mock_setup.return_value = {}

        with TelemetryFlowInstrumentor() as instrumentor:
            assert instrumentor._initialized is True

        # Should complete without error

    @mock.patch("telemetryflow.instrumentation.integration.setup_auto_instrumentation")
    def test_context_manager_with_kwargs(
        self, mock_setup: mock.Mock, client: TelemetryFlowClient
    ) -> None:
        """Test context manager passes kwargs."""
        mock_setup.return_value = {}

        with TelemetryFlowInstrumentor(client, enable_flask=False) as _:
            pass

        mock_setup.assert_called_with(client=client, enable_flask=False)
        client.shutdown()


class TestTelemetryFlowInstrumentorUninstrument:
    """Tests for TelemetryFlowInstrumentor.uninstrument with mocked modules."""

    @mock.patch("telemetryflow.instrumentation.integration.setup_auto_instrumentation")
    def test_uninstrument_flask(self, mock_setup: mock.Mock, client: TelemetryFlowClient) -> None:
        """Test uninstrument calls Flask uninstrument."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_flask_module = mock.Mock()
        mock_flask_module.FlaskInstrumentor = mock.Mock(return_value=mock_instrumentor)

        mock_setup.return_value = {"flask": True}

        instrumentor = TelemetryFlowInstrumentor(client)
        instrumentor.instrument()

        with mock.patch.dict(
            sys.modules,
            {
                "opentelemetry.instrumentation.flask": mock_flask_module,
            },
        ):
            instrumentor.uninstrument()

        mock_instrumentor.uninstrument.assert_called_once()
        client.shutdown()

    @mock.patch("telemetryflow.instrumentation.integration.setup_auto_instrumentation")
    def test_uninstrument_fastapi(self, mock_setup: mock.Mock, client: TelemetryFlowClient) -> None:
        """Test uninstrument calls FastAPI uninstrument."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_fastapi_module = mock.Mock()
        mock_fastapi_module.FastAPIInstrumentor = mock.Mock(return_value=mock_instrumentor)

        mock_setup.return_value = {"fastapi": True}

        instrumentor = TelemetryFlowInstrumentor(client)
        instrumentor.instrument()

        with mock.patch.dict(
            sys.modules,
            {
                "opentelemetry.instrumentation.fastapi": mock_fastapi_module,
            },
        ):
            instrumentor.uninstrument()

        mock_instrumentor.uninstrument.assert_called_once()
        client.shutdown()

    @mock.patch("telemetryflow.instrumentation.integration.setup_auto_instrumentation")
    def test_uninstrument_sqlalchemy(
        self, mock_setup: mock.Mock, client: TelemetryFlowClient
    ) -> None:
        """Test uninstrument calls SQLAlchemy uninstrument."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_sqlalchemy_module = mock.Mock()
        mock_sqlalchemy_module.SQLAlchemyInstrumentor = mock.Mock(return_value=mock_instrumentor)

        mock_setup.return_value = {"sqlalchemy": True}

        instrumentor = TelemetryFlowInstrumentor(client)
        instrumentor.instrument()

        with mock.patch.dict(
            sys.modules,
            {
                "opentelemetry.instrumentation.sqlalchemy": mock_sqlalchemy_module,
            },
        ):
            instrumentor.uninstrument()

        mock_instrumentor.uninstrument.assert_called_once()
        client.shutdown()

    @mock.patch("telemetryflow.instrumentation.integration.setup_auto_instrumentation")
    def test_uninstrument_requests(
        self, mock_setup: mock.Mock, client: TelemetryFlowClient
    ) -> None:
        """Test uninstrument calls Requests uninstrument."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_requests_module = mock.Mock()
        mock_requests_module.RequestsInstrumentor = mock.Mock(return_value=mock_instrumentor)

        mock_setup.return_value = {"requests": True}

        instrumentor = TelemetryFlowInstrumentor(client)
        instrumentor.instrument()

        with mock.patch.dict(
            sys.modules,
            {
                "opentelemetry.instrumentation.requests": mock_requests_module,
            },
        ):
            instrumentor.uninstrument()

        mock_instrumentor.uninstrument.assert_called_once()
        client.shutdown()

    @mock.patch("telemetryflow.instrumentation.integration.setup_auto_instrumentation")
    def test_uninstrument_httpx(self, mock_setup: mock.Mock, client: TelemetryFlowClient) -> None:
        """Test uninstrument calls HTTPX uninstrument."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_httpx_module = mock.Mock()
        mock_httpx_module.HTTPXClientInstrumentor = mock.Mock(return_value=mock_instrumentor)

        mock_setup.return_value = {"httpx": True}

        instrumentor = TelemetryFlowInstrumentor(client)
        instrumentor.instrument()

        with mock.patch.dict(
            sys.modules,
            {
                "opentelemetry.instrumentation.httpx": mock_httpx_module,
            },
        ):
            instrumentor.uninstrument()

        mock_instrumentor.uninstrument.assert_called_once()
        client.shutdown()

    @mock.patch("telemetryflow.instrumentation.integration.setup_auto_instrumentation")
    def test_uninstrument_logging(self, mock_setup: mock.Mock, client: TelemetryFlowClient) -> None:
        """Test uninstrument calls Logging uninstrument."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_logging_module = mock.Mock()
        mock_logging_module.LoggingInstrumentor = mock.Mock(return_value=mock_instrumentor)

        mock_setup.return_value = {"logging": True}

        instrumentor = TelemetryFlowInstrumentor(client)
        instrumentor.instrument()

        with mock.patch.dict(
            sys.modules,
            {
                "opentelemetry.instrumentation.logging": mock_logging_module,
            },
        ):
            instrumentor.uninstrument()

        mock_instrumentor.uninstrument.assert_called_once()
        client.shutdown()

    @mock.patch("telemetryflow.instrumentation.integration.setup_auto_instrumentation")
    def test_uninstrument_psycopg2(
        self, mock_setup: mock.Mock, client: TelemetryFlowClient
    ) -> None:
        """Test uninstrument calls Psycopg2 uninstrument."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_psycopg2_module = mock.Mock()
        mock_psycopg2_module.Psycopg2Instrumentor = mock.Mock(return_value=mock_instrumentor)

        mock_setup.return_value = {"psycopg2": True}

        instrumentor = TelemetryFlowInstrumentor(client)
        instrumentor.instrument()

        with mock.patch.dict(
            sys.modules,
            {
                "opentelemetry.instrumentation.psycopg2": mock_psycopg2_module,
            },
        ):
            instrumentor.uninstrument()

        mock_instrumentor.uninstrument.assert_called_once()
        client.shutdown()

    @mock.patch("telemetryflow.instrumentation.integration.setup_auto_instrumentation")
    def test_uninstrument_redis(self, mock_setup: mock.Mock, client: TelemetryFlowClient) -> None:
        """Test uninstrument calls Redis uninstrument."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_redis_module = mock.Mock()
        mock_redis_module.RedisInstrumentor = mock.Mock(return_value=mock_instrumentor)

        mock_setup.return_value = {"redis": True}

        instrumentor = TelemetryFlowInstrumentor(client)
        instrumentor.instrument()

        with mock.patch.dict(
            sys.modules,
            {
                "opentelemetry.instrumentation.redis": mock_redis_module,
            },
        ):
            instrumentor.uninstrument()

        mock_instrumentor.uninstrument.assert_called_once()
        client.shutdown()


class TestSetupAutoInstrumentationWithInitializedClient:
    """Tests for setup_auto_instrumentation with initialized client."""

    @mock.patch("telemetryflow.instrumentation.integration.auto_instrument")
    def test_with_initialized_client(
        self, mock_auto_instrument: mock.Mock, client: TelemetryFlowClient
    ) -> None:
        """Test setup with initialized client uses providers."""
        # Initialize client first
        client.initialize()
        mock_auto_instrument.return_value = {"flask": True}

        results = setup_auto_instrumentation(client=client)

        assert results == {"flask": True}
        call_args = mock_auto_instrument.call_args
        config = call_args.kwargs["config"]
        # When client is initialized, providers should be passed
        assert config.tracer_provider is not None or config.meter_provider is not None
        client.shutdown()
