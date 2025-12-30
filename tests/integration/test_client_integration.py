"""Integration tests for TelemetryFlow client.

These tests verify the full integration of the SDK components.
Skip these tests in CI if no OTLP collector is available.
"""

import os
import time

import pytest

from telemetryflow import TelemetryFlowBuilder
from telemetryflow.application.commands import SpanKind
from telemetryflow.domain.config import Protocol


# Skip integration tests if running in short mode or no collector available
pytestmark = pytest.mark.integration


def collector_available() -> bool:
    """Check if OTLP collector is available."""
    # In a real scenario, you'd check if the collector is reachable
    return os.environ.get("TELEMETRYFLOW_INTEGRATION_TEST", "").lower() == "true"


@pytest.fixture
def client():
    """Create and initialize a client for testing."""
    client = (
        TelemetryFlowBuilder()
        .with_api_key("tfk_test_key", "tfs_test_secret")
        .with_endpoint("localhost:4317")
        .with_service("integration-test", "1.0.0")
        .with_environment("test")
        .with_grpc()
        .with_insecure(True)
        .build()
    )
    client.initialize()
    yield client
    client.shutdown()


class TestClientIntegration:
    """Integration tests for the TelemetryFlow client."""

    def test_client_lifecycle(self) -> None:
        """Test full client lifecycle."""
        client = (
            TelemetryFlowBuilder()
            .with_api_key("tfk_test", "tfs_test")
            .with_endpoint("localhost:4317")
            .with_service("lifecycle-test")
            .with_insecure(True)
            .build()
        )

        assert not client.is_initialized()

        client.initialize()
        assert client.is_initialized()

        status = client.get_status()
        assert status["initialized"] is True
        assert status["service_name"] == "lifecycle-test"

        client.shutdown()
        assert not client.is_initialized()

    def test_metrics_recording(self, client) -> None:
        """Test recording various metrics."""
        # Counter
        client.increment_counter("test.counter", 1, {"test": "true"})
        client.increment_counter("test.counter", 5, {"test": "true"})

        # Gauge
        client.record_gauge("test.gauge", 42.5, {"test": "true"})

        # Histogram
        client.record_histogram("test.histogram", 0.125, "s", {"test": "true"})
        client.record_histogram("test.histogram", 0.250, "s", {"test": "true"})

        # Generic metric
        client.record_metric("test.metric", 100.0, "count", {"test": "true"})

        # Check status
        status = client.get_status()
        assert status["metrics_sent"] > 0

    def test_logging(self, client) -> None:
        """Test log emission."""
        client.log_info("Info message", {"level": "info"})
        client.log_warn("Warning message", {"level": "warn"})
        client.log_error("Error message", {"level": "error"})
        client.log_debug("Debug message", {"level": "debug"})

        # Check status
        status = client.get_status()
        assert status["logs_sent"] > 0

    def test_tracing(self, client) -> None:
        """Test trace span creation."""
        # Manual span management
        span_id = client.start_span(
            "test.span",
            SpanKind.INTERNAL,
            {"test": "true"},
        )
        assert span_id is not None

        client.add_span_event(span_id, "checkpoint", {"progress": 50})
        client.end_span(span_id)

        # Check status
        status = client.get_status()
        assert status["spans_sent"] > 0

    def test_nested_spans(self, client) -> None:
        """Test nested span creation using context manager."""
        with client.span("parent.span", SpanKind.SERVER) as parent_id:
            client.add_span_event(parent_id, "parent_event")

            with client.span("child.span", SpanKind.CLIENT) as child_id:
                client.add_span_event(child_id, "child_event")

                with client.span("grandchild.span", SpanKind.INTERNAL) as grandchild_id:
                    client.add_span_event(grandchild_id, "grandchild_event")

        status = client.get_status()
        assert status["spans_sent"] >= 3

    def test_span_with_error(self, client) -> None:
        """Test span with error recording."""
        span_id = client.start_span("error.span", SpanKind.INTERNAL)

        error = ValueError("Test error")
        client.end_span(span_id, error)

        status = client.get_status()
        assert status["spans_sent"] > 0

    def test_context_manager_with_error(self, client) -> None:
        """Test span context manager handles errors properly."""
        with pytest.raises(ValueError):
            with client.span("error.span", SpanKind.INTERNAL):
                raise ValueError("Test error")

        status = client.get_status()
        assert status["spans_sent"] > 0

    def test_flush(self, client) -> None:
        """Test explicit flush."""
        client.increment_counter("flush.test")
        client.log_info("Flush test message")

        # Should not raise
        client.flush()

    def test_signals_configuration(self) -> None:
        """Test signal configuration."""
        # Metrics only
        client = (
            TelemetryFlowBuilder()
            .with_api_key("tfk_test", "tfs_test")
            .with_endpoint("localhost:4317")
            .with_service("signals-test")
            .with_metrics_only()
            .with_insecure(True)
            .build()
        )

        assert client.config.enable_metrics is True
        assert client.config.enable_logs is False
        assert client.config.enable_traces is False

    def test_protocol_configuration(self) -> None:
        """Test protocol configuration."""
        # gRPC
        grpc_client = (
            TelemetryFlowBuilder()
            .with_api_key("tfk_test", "tfs_test")
            .with_endpoint("localhost:4317")
            .with_service("grpc-test")
            .with_grpc()
            .build()
        )
        assert grpc_client.config.protocol == Protocol.GRPC

        # HTTP
        http_client = (
            TelemetryFlowBuilder()
            .with_api_key("tfk_test", "tfs_test")
            .with_endpoint("localhost:4318")
            .with_service("http-test")
            .with_http()
            .build()
        )
        assert http_client.config.protocol == Protocol.HTTP

    def test_context_manager_client(self) -> None:
        """Test using client as context manager."""
        with (
            TelemetryFlowBuilder()
            .with_api_key("tfk_test", "tfs_test")
            .with_endpoint("localhost:4317")
            .with_service("context-test")
            .with_insecure(True)
            .build()
        ) as client:
            assert client.is_initialized()
            client.increment_counter("context.test")

        assert not client.is_initialized()

    @pytest.mark.skipif(not collector_available(), reason="Collector not available")
    def test_actual_export(self, client) -> None:
        """Test actual export to collector (requires running collector)."""
        # Record some data
        for i in range(10):
            client.increment_counter("export.test", 1, {"iteration": str(i)})

        with client.span("export.span", SpanKind.INTERNAL) as span_id:
            client.log_info("Export test log")
            time.sleep(0.1)

        # Flush to ensure data is sent
        client.flush()

        # Give some time for export
        time.sleep(1)

        status = client.get_status()
        assert status["metrics_sent"] >= 10
        assert status["logs_sent"] >= 1
        assert status["spans_sent"] >= 1
