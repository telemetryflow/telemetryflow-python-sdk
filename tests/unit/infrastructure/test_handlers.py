"""Unit tests for TelemetryCommandHandler."""

from unittest import mock

import pytest

from telemetryflow.application.commands import (
    AddSpanEventCommand,
    EmitBatchLogsCommand,
    EmitLogCommand,
    EndSpanCommand,
    FlushTelemetryCommand,
    InitializeSDKCommand,
    RecordCounterCommand,
    RecordGaugeCommand,
    RecordHistogramCommand,
    RecordMetricCommand,
    SeverityLevel,
    ShutdownSDKCommand,
    SpanKind,
    StartSpanCommand,
)
from telemetryflow.domain.config import TelemetryConfig
from telemetryflow.domain.credentials import Credentials
from telemetryflow.infrastructure.handlers import TelemetryCommandHandler


@pytest.fixture
def valid_credentials() -> Credentials:
    """Create valid credentials for testing."""
    return Credentials.create("tfk_test_key", "tfs_test_secret")


@pytest.fixture
def valid_config(valid_credentials: Credentials) -> TelemetryConfig:
    """Create valid config for testing."""
    return TelemetryConfig(
        credentials=valid_credentials,
        endpoint="localhost:4317",
        service_name="test-service",
        insecure=True,
    )


@pytest.fixture
def handler() -> TelemetryCommandHandler:
    """Create a fresh handler for testing."""
    return TelemetryCommandHandler()


class TestTelemetryCommandHandlerInit:
    """Tests for TelemetryCommandHandler initialization."""

    def test_initial_state(self, handler: TelemetryCommandHandler) -> None:
        """Test initial handler state."""
        assert handler.is_initialized is False
        assert handler.config is None
        assert handler.start_time is None
        assert handler.metrics_sent == 0
        assert handler.logs_sent == 0
        assert handler.spans_sent == 0


class TestHandleInitialize:
    """Tests for _handle_initialize method."""

    def test_initialize_success(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test successful initialization."""
        cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(cmd)

        assert handler.is_initialized is True
        assert handler.config == valid_config
        assert handler.start_time is not None

    def test_initialize_already_initialized(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test initialization when already initialized."""
        cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(cmd)

        # Second initialization should be a no-op
        handler.handle(cmd)

        assert handler.is_initialized is True

    def test_initialize_with_traces_disabled(
        self, handler: TelemetryCommandHandler, valid_credentials: Credentials
    ) -> None:
        """Test initialization with traces disabled."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
            enable_traces=False,
            enable_metrics=True,
            insecure=True,
        )
        cmd = InitializeSDKCommand(config=config)
        handler.handle(cmd)

        assert handler.is_initialized is True

    def test_initialize_with_metrics_disabled(
        self, handler: TelemetryCommandHandler, valid_credentials: Credentials
    ) -> None:
        """Test initialization with metrics disabled."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
            enable_traces=True,
            enable_metrics=False,
            insecure=True,
        )
        cmd = InitializeSDKCommand(config=config)
        handler.handle(cmd)

        assert handler.is_initialized is True


class TestHandleShutdown:
    """Tests for _handle_shutdown method."""

    def test_shutdown_when_not_initialized(self, handler: TelemetryCommandHandler) -> None:
        """Test shutdown when not initialized."""
        cmd = ShutdownSDKCommand()
        # Should not raise
        handler.handle(cmd)

        assert handler.is_initialized is False

    def test_shutdown_success(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test successful shutdown."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        shutdown_cmd = ShutdownSDKCommand(timeout_seconds=5.0)
        handler.handle(shutdown_cmd)

        assert handler.is_initialized is False

    def test_shutdown_clears_active_spans(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test that shutdown clears active spans."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        # Start a span
        span_cmd = StartSpanCommand(name="test-span")
        handler.handle(span_cmd)

        # Shutdown
        shutdown_cmd = ShutdownSDKCommand()
        handler.handle(shutdown_cmd)

        assert handler.is_initialized is False


class TestHandleFlush:
    """Tests for _handle_flush method."""

    def test_flush_when_not_initialized(self, handler: TelemetryCommandHandler) -> None:
        """Test flush when not initialized."""
        cmd = FlushTelemetryCommand()
        # Should not raise
        handler.handle(cmd)

    def test_flush_success(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test successful flush."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        flush_cmd = FlushTelemetryCommand()
        # Should not raise
        handler.handle(flush_cmd)


class TestHandleRecordMetric:
    """Tests for _handle_record_metric method."""

    def test_record_metric_when_not_initialized(self, handler: TelemetryCommandHandler) -> None:
        """Test recording metric when not initialized."""
        cmd = RecordMetricCommand(name="test.metric", value=42.0)
        # Should not raise
        handler.handle(cmd)

    def test_record_metric_success(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test successful metric recording."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        metric_cmd = RecordMetricCommand(
            name="test.metric",
            value=42.0,
            attributes={"key": "value"},
        )
        handler.handle(metric_cmd)

        # RecordMetricCommand calls RecordGaugeCommand which increments, then increments itself
        assert handler.metrics_sent == 2


class TestHandleRecordCounter:
    """Tests for _handle_record_counter method."""

    def test_record_counter_when_not_initialized(self, handler: TelemetryCommandHandler) -> None:
        """Test recording counter when not initialized."""
        cmd = RecordCounterCommand(name="test.counter", value=1)
        # Should not raise
        handler.handle(cmd)

    def test_record_counter_success(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test successful counter recording."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        counter_cmd = RecordCounterCommand(
            name="test.counter",
            value=5,
            attributes={"method": "GET"},
        )
        handler.handle(counter_cmd)

        assert handler.metrics_sent == 1

    def test_record_counter_reuses_instrument(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test that counter instrument is reused."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        for _ in range(3):
            counter_cmd = RecordCounterCommand(name="test.counter", value=1)
            handler.handle(counter_cmd)

        assert handler.metrics_sent == 3


class TestHandleRecordGauge:
    """Tests for _handle_record_gauge method."""

    def test_record_gauge_when_not_initialized(self, handler: TelemetryCommandHandler) -> None:
        """Test recording gauge when not initialized."""
        cmd = RecordGaugeCommand(name="test.gauge", value=42.0)
        # Should not raise
        handler.handle(cmd)

    def test_record_gauge_success(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test successful gauge recording."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        gauge_cmd = RecordGaugeCommand(
            name="test.gauge",
            value=42.5,
            attributes={"pool": "default"},
        )
        handler.handle(gauge_cmd)

        assert handler.metrics_sent == 1


class TestHandleRecordHistogram:
    """Tests for _handle_record_histogram method."""

    def test_record_histogram_when_not_initialized(self, handler: TelemetryCommandHandler) -> None:
        """Test recording histogram when not initialized."""
        cmd = RecordHistogramCommand(name="test.histogram", value=0.5)
        # Should not raise
        handler.handle(cmd)

    def test_record_histogram_success(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test successful histogram recording."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        histogram_cmd = RecordHistogramCommand(
            name="test.histogram",
            value=0.125,
            unit="s",
            attributes={"endpoint": "/api"},
        )
        handler.handle(histogram_cmd)

        assert handler.metrics_sent == 1

    def test_record_histogram_without_unit(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test histogram recording without unit."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        histogram_cmd = RecordHistogramCommand(
            name="test.histogram",
            value=100.0,
        )
        handler.handle(histogram_cmd)

        assert handler.metrics_sent == 1


class TestHandleEmitLog:
    """Tests for _handle_emit_log method."""

    def test_emit_log_when_not_initialized(self, handler: TelemetryCommandHandler) -> None:
        """Test emitting log when not initialized."""
        cmd = EmitLogCommand(message="Test log")
        # Should not raise
        handler.handle(cmd)

    def test_emit_log_success(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test successful log emission."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        log_cmd = EmitLogCommand(
            message="Test log message",
            severity=SeverityLevel.INFO,
            attributes={"user_id": "123"},
        )
        handler.handle(log_cmd)

        assert handler.logs_sent == 1


class TestHandleEmitBatchLogs:
    """Tests for _handle_emit_batch_logs method."""

    def test_emit_batch_logs(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test batch log emission."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        logs = [
            EmitLogCommand(message="Log 1"),
            EmitLogCommand(message="Log 2"),
            EmitLogCommand(message="Log 3"),
        ]
        batch_cmd = EmitBatchLogsCommand(logs=logs)
        handler.handle(batch_cmd)

        assert handler.logs_sent == 3


class TestHandleStartSpan:
    """Tests for _handle_start_span method."""

    def test_start_span_when_not_initialized(self, handler: TelemetryCommandHandler) -> None:
        """Test starting span when not initialized."""
        cmd = StartSpanCommand(name="test-span")
        result = handler.handle(cmd)

        assert result == ""

    def test_start_span_success(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test successful span start."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        span_cmd = StartSpanCommand(
            name="test-span",
            kind=SpanKind.SERVER,
            attributes={"http.method": "GET"},
        )
        span_id = handler.handle(span_cmd)

        assert span_id != ""
        assert handler.spans_sent == 1

    def test_start_span_all_kinds(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test starting spans with all kinds."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        for kind in [
            SpanKind.INTERNAL,
            SpanKind.SERVER,
            SpanKind.CLIENT,
            SpanKind.PRODUCER,
            SpanKind.CONSUMER,
        ]:
            span_cmd = StartSpanCommand(name=f"span-{kind.value}", kind=kind)
            span_id = handler.handle(span_cmd)
            assert span_id != ""


class TestHandleEndSpan:
    """Tests for _handle_end_span method."""

    def test_end_span_not_found(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test ending a span that doesn't exist."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        end_cmd = EndSpanCommand(span_id="non-existent")
        # Should not raise, just log warning
        handler.handle(end_cmd)

    def test_end_span_success(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test successful span end."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        start_cmd = StartSpanCommand(name="test-span")
        span_id = handler.handle(start_cmd)

        end_cmd = EndSpanCommand(span_id=span_id)
        handler.handle(end_cmd)

    def test_end_span_with_error(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test ending span with error."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        start_cmd = StartSpanCommand(name="test-span")
        span_id = handler.handle(start_cmd)

        error = ValueError("Test error")
        end_cmd = EndSpanCommand(span_id=span_id, error=error)
        handler.handle(end_cmd)


class TestHandleAddSpanEvent:
    """Tests for _handle_add_span_event method."""

    def test_add_event_span_not_found(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test adding event to non-existent span."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        event_cmd = AddSpanEventCommand(
            span_id="non-existent",
            name="checkpoint",
        )
        # Should not raise, just log warning
        handler.handle(event_cmd)

    def test_add_event_success(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test successful event addition."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        start_cmd = StartSpanCommand(name="test-span")
        span_id = handler.handle(start_cmd)

        event_cmd = AddSpanEventCommand(
            span_id=span_id,
            name="checkpoint",
            attributes={"progress": 50},
        )
        handler.handle(event_cmd)


class TestHandleUnknownCommand:
    """Tests for handling unknown commands."""

    def test_unknown_command_raises_error(self, handler: TelemetryCommandHandler) -> None:
        """Test that unknown command raises ValueError."""
        from telemetryflow.application.commands import Command

        # Create a custom command type
        class UnknownCommand(Command):
            pass

        with pytest.raises(ValueError, match="Unknown command type"):
            handler.handle(UnknownCommand())


class TestShutdownWithErrors:
    """Tests for shutdown error handling."""

    def test_shutdown_with_tracer_error(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test shutdown when tracer provider raises error."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        # Mock tracer provider to raise an error
        handler._tracer_provider.force_flush = mock.Mock(
            side_effect=Exception("Tracer flush error")
        )

        shutdown_cmd = ShutdownSDKCommand(timeout_seconds=1.0)
        with pytest.raises(RuntimeError, match="Shutdown completed with 1 error"):
            handler.handle(shutdown_cmd)

    def test_shutdown_with_meter_error(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test shutdown when meter provider raises error."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        # Mock meter provider to raise an error
        handler._meter_provider.shutdown = mock.Mock(side_effect=Exception("Meter shutdown error"))

        shutdown_cmd = ShutdownSDKCommand(timeout_seconds=1.0)
        with pytest.raises(RuntimeError, match="Shutdown completed with 1 error"):
            handler.handle(shutdown_cmd)

    def test_shutdown_with_multiple_errors(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test shutdown when both providers raise errors."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        # Mock both providers to raise errors
        handler._tracer_provider.force_flush = mock.Mock(side_effect=Exception("Tracer error"))
        handler._meter_provider.shutdown = mock.Mock(side_effect=Exception("Meter error"))

        shutdown_cmd = ShutdownSDKCommand(timeout_seconds=1.0)
        with pytest.raises(RuntimeError, match="Shutdown completed with 2 error"):
            handler.handle(shutdown_cmd)


class TestConvertAttributes:
    """Tests for _convert_attributes method."""

    def test_convert_primitive_types(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test converting primitive attribute types."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        attrs = {
            "string": "value",
            "bool": True,
            "int": 42,
            "float": 3.14,
        }

        result = handler._convert_attributes(attrs)

        assert result["string"] == "value"
        assert result["bool"] is True
        assert result["int"] == 42
        assert result["float"] == 3.14

    def test_convert_list_attributes(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test converting list attributes."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        attrs = {
            "list": [1, 2, 3],
            "mixed": ["a", 1, True],
        }

        result = handler._convert_attributes(attrs)

        assert result["list"] == [1, 2, 3]
        assert result["mixed"] == ["a", 1, True]

    def test_convert_non_primitive_types(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test converting non-primitive types to strings."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        attrs = {
            "dict": {"nested": "value"},
            "none": None,
        }

        result = handler._convert_attributes(attrs)

        # Non-primitive types are converted to strings
        assert isinstance(result["dict"], str)
        assert result["none"] == "None"

    def test_filter_invalid_list_items(
        self, handler: TelemetryCommandHandler, valid_config: TelemetryConfig
    ) -> None:
        """Test that invalid list items are filtered."""
        init_cmd = InitializeSDKCommand(config=valid_config)
        handler.handle(init_cmd)

        attrs = {
            "mixed": [1, "a", {"invalid": "dict"}, 2.0],
        }

        result = handler._convert_attributes(attrs)

        # Dict should be filtered out
        assert result["mixed"] == [1, "a", 2.0]
