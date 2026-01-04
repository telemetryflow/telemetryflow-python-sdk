"""Unit tests for the telemetryflow __init__.py module."""

from unittest import mock

from telemetryflow.domain.config import TelemetryConfig
from telemetryflow.domain.credentials import Credentials


class TestNewClient:
    """Tests for new_client convenience function."""

    def test_creates_client(self) -> None:
        """Test that new_client creates a client."""
        from telemetryflow import TelemetryFlowClient, new_client

        config = TelemetryConfig(
            credentials=Credentials.create("tfk_test", "tfs_test"),
            endpoint="localhost:4317",
            service_name="test-service",
        )

        client = new_client(config)

        assert isinstance(client, TelemetryFlowClient)
        assert client.is_initialized() is False


class TestNewFromEnv:
    """Tests for new_from_env convenience function."""

    def test_creates_client_from_env(self) -> None:
        """Test that new_from_env creates a client from environment."""
        from telemetryflow import new_from_env

        with mock.patch.dict(
            "os.environ",
            {
                "TELEMETRYFLOW_API_KEY_ID": "tfk_test_key",
                "TELEMETRYFLOW_API_KEY_SECRET": "tfs_test_secret",
                "TELEMETRYFLOW_ENDPOINT": "localhost:4317",
                "TELEMETRYFLOW_SERVICE_NAME": "test-service",
            },
        ):
            client = new_from_env()

            assert client is not None
            assert client.is_initialized() is False


class TestNewSimple:
    """Tests for new_simple convenience function."""

    def test_creates_client_with_minimal_config(self) -> None:
        """Test that new_simple creates a client with minimal config."""
        from telemetryflow import TelemetryFlowClient, new_simple

        client = new_simple(
            api_key_id="tfk_test",
            api_key_secret="tfs_test",
            endpoint="localhost:4317",
            service_name="test-service",
        )

        assert isinstance(client, TelemetryFlowClient)
        assert client.is_initialized() is False


class TestAutoInstrument:
    """Tests for auto_instrument convenience function."""

    def test_auto_instrument_without_client(self) -> None:
        """Test auto_instrument without client."""
        from telemetryflow import auto_instrument

        with mock.patch("telemetryflow.instrumentation.integration.auto_instrument") as mock_auto:
            mock_auto.return_value = {"flask": False, "requests": False}

            result = auto_instrument(client=None)

            assert isinstance(result, dict)

    def test_auto_instrument_with_kwargs(self) -> None:
        """Test auto_instrument with kwargs."""
        from telemetryflow import auto_instrument

        with mock.patch(
            "telemetryflow.instrumentation.integration.setup_auto_instrumentation"
        ) as mock_setup:
            mock_setup.return_value = {}

            auto_instrument(enable_flask=False, enable_fastapi=False)

            mock_setup.assert_called_once()
            call_kwargs = mock_setup.call_args[1]
            assert call_kwargs["enable_flask"] is False
            assert call_kwargs["enable_fastapi"] is False


class TestExports:
    """Tests for module exports."""

    def test_exports_main_classes(self) -> None:
        """Test that main classes are exported."""
        from telemetryflow import (
            Credentials,
            Protocol,
            SignalType,
            TelemetryConfig,
            TelemetryFlowBuilder,
            TelemetryFlowClient,
            __version__,
        )

        assert TelemetryFlowClient is not None
        assert TelemetryFlowBuilder is not None
        assert TelemetryConfig is not None
        assert Credentials is not None
        assert Protocol is not None
        assert SignalType is not None
        assert __version__ is not None

    def test_exports_convenience_functions(self) -> None:
        """Test that convenience functions are exported."""
        from telemetryflow import auto_instrument, new_client, new_from_env, new_simple

        assert callable(new_client)
        assert callable(new_from_env)
        assert callable(new_simple)
        assert callable(auto_instrument)
