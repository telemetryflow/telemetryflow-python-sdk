"""Unit tests for TelemetryFlowClient."""

import pytest

from telemetryflow.application.commands import SpanKind
from telemetryflow.client import NotInitializedError, TelemetryFlowClient
from telemetryflow.domain.config import TelemetryConfig
from telemetryflow.domain.credentials import Credentials


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


class TestTelemetryFlowClient:
    """Test suite for TelemetryFlowClient."""

    def test_create_client(self, valid_config: TelemetryConfig) -> None:
        """Test creating a client."""
        client = TelemetryFlowClient(valid_config)

        assert client.config == valid_config
        assert client.is_initialized() is False

    def test_client_not_initialized_error(self, client: TelemetryFlowClient) -> None:
        """Test that operations fail when not initialized."""
        with pytest.raises(NotInitializedError):
            client.increment_counter("test.counter")

    def test_record_metric_not_initialized(self, client: TelemetryFlowClient) -> None:
        """Test record_metric fails when not initialized."""
        with pytest.raises(NotInitializedError):
            client.record_metric("test.metric", 1.0)

    def test_record_gauge_not_initialized(self, client: TelemetryFlowClient) -> None:
        """Test record_gauge fails when not initialized."""
        with pytest.raises(NotInitializedError):
            client.record_gauge("test.gauge", 42.0)

    def test_record_histogram_not_initialized(self, client: TelemetryFlowClient) -> None:
        """Test record_histogram fails when not initialized."""
        with pytest.raises(NotInitializedError):
            client.record_histogram("test.histogram", 0.125)

    def test_log_not_initialized(self, client: TelemetryFlowClient) -> None:
        """Test log fails when not initialized."""
        with pytest.raises(NotInitializedError):
            client.log_info("Test message")

    def test_log_warn_not_initialized(self, client: TelemetryFlowClient) -> None:
        """Test log_warn fails when not initialized."""
        with pytest.raises(NotInitializedError):
            client.log_warn("Warning message")

    def test_log_error_not_initialized(self, client: TelemetryFlowClient) -> None:
        """Test log_error fails when not initialized."""
        with pytest.raises(NotInitializedError):
            client.log_error("Error message")

    def test_start_span_not_initialized(self, client: TelemetryFlowClient) -> None:
        """Test start_span fails when not initialized."""
        with pytest.raises(NotInitializedError):
            client.start_span("test.span")

    def test_end_span_not_initialized(self, client: TelemetryFlowClient) -> None:
        """Test end_span fails when not initialized."""
        with pytest.raises(NotInitializedError):
            client.end_span("span-123")

    def test_add_span_event_not_initialized(self, client: TelemetryFlowClient) -> None:
        """Test add_span_event fails when not initialized."""
        with pytest.raises(NotInitializedError):
            client.add_span_event("span-123", "event")

    def test_flush_not_initialized(self, client: TelemetryFlowClient) -> None:
        """Test flush fails when not initialized."""
        with pytest.raises(NotInitializedError):
            client.flush()

    def test_shutdown_not_initialized(self, client: TelemetryFlowClient) -> None:
        """Test shutdown does nothing when not initialized."""
        # Should not raise
        client.shutdown()

    def test_config_property(self, client: TelemetryFlowClient, valid_config: TelemetryConfig) -> None:
        """Test config property."""
        assert client.config == valid_config
        assert client.config.service_name == "test-service"

    def test_repr(self, client: TelemetryFlowClient) -> None:
        """Test string representation."""
        repr_str = repr(client)

        assert "TelemetryFlowClient" in repr_str
        assert "test-service" in repr_str
        assert "not initialized" in repr_str


class TestTelemetryFlowClientInitialized:
    """Test suite for initialized TelemetryFlowClient.

    Note: These tests require mocking the OpenTelemetry SDK
    to avoid actual network connections.
    """

    def test_initialize_sets_flag(self, client: TelemetryFlowClient) -> None:
        """Test that initialize sets the initialized flag."""
        client.initialize()

        assert client.is_initialized() is True

        # Clean up
        client.shutdown()

    def test_double_initialize(self, client: TelemetryFlowClient) -> None:
        """Test that double initialize is safe."""
        client.initialize()
        client.initialize()  # Should not raise

        assert client.is_initialized() is True

        # Clean up
        client.shutdown()

    def test_shutdown_clears_flag(self, client: TelemetryFlowClient) -> None:
        """Test that shutdown clears the initialized flag."""
        client.initialize()
        client.shutdown()

        assert client.is_initialized() is False

    def test_get_status(self, client: TelemetryFlowClient) -> None:
        """Test get_status returns correct info."""
        client.initialize()

        status = client.get_status()

        assert status["initialized"] is True
        assert status["service_name"] == "test-service"
        assert status["endpoint"] == "localhost:4317"
        assert status["protocol"] == "grpc"
        assert "metrics" in status["signals_enabled"]
        assert "logs" in status["signals_enabled"]
        assert "traces" in status["signals_enabled"]

        # Clean up
        client.shutdown()

    def test_context_manager(self, valid_config: TelemetryConfig) -> None:
        """Test client as context manager."""
        with TelemetryFlowClient(valid_config) as client:
            assert client.is_initialized() is True

        assert client.is_initialized() is False

    def test_increment_counter(self, client: TelemetryFlowClient) -> None:
        """Test increment_counter method."""
        client.initialize()

        # Should not raise
        client.increment_counter("test.counter", 1, {"key": "value"})

        client.shutdown()

    def test_record_gauge(self, client: TelemetryFlowClient) -> None:
        """Test record_gauge method."""
        client.initialize()

        # Should not raise
        client.record_gauge("test.gauge", 42.0, {"key": "value"})

        client.shutdown()

    def test_record_histogram(self, client: TelemetryFlowClient) -> None:
        """Test record_histogram method."""
        client.initialize()

        # Should not raise
        client.record_histogram("test.histogram", 0.125, "s", {"key": "value"})

        client.shutdown()

    def test_log_methods(self, client: TelemetryFlowClient) -> None:
        """Test all log methods."""
        client.initialize()

        # Should not raise
        client.log_info("Info message", {"key": "value"})
        client.log_warn("Warn message")
        client.log_error("Error message")
        client.log_debug("Debug message")

        client.shutdown()

    def test_span_lifecycle(self, client: TelemetryFlowClient) -> None:
        """Test span start/end lifecycle."""
        client.initialize()

        span_id = client.start_span("test.span", SpanKind.INTERNAL, {"key": "value"})

        assert span_id is not None
        assert isinstance(span_id, str)

        # Add event
        client.add_span_event(span_id, "checkpoint", {"progress": 50})

        # End span
        client.end_span(span_id)

        client.shutdown()

    def test_span_context_manager(self, client: TelemetryFlowClient) -> None:
        """Test span context manager."""
        client.initialize()

        with client.span("test.span", SpanKind.SERVER, {"key": "value"}) as span_id:
            assert span_id is not None
            client.add_span_event(span_id, "event")

        client.shutdown()

    def test_span_context_manager_with_error(self, client: TelemetryFlowClient) -> None:
        """Test span context manager handles errors."""
        client.initialize()

        with pytest.raises(ValueError):
            with client.span("test.span") as span_id:
                raise ValueError("Test error")

        client.shutdown()

    def test_flush(self, client: TelemetryFlowClient) -> None:
        """Test flush method."""
        client.initialize()

        # Should not raise
        client.flush()

        client.shutdown()
