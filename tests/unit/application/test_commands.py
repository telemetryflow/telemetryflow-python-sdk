"""Unit tests for CQRS Commands."""

from datetime import datetime

import pytest

from telemetryflow.application.commands import (
    AddSpanEventCommand,
    Command,
    CommandBus,
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


@pytest.fixture
def valid_config() -> TelemetryConfig:
    """Create valid config for testing."""
    return TelemetryConfig(
        credentials=Credentials.create("tfk_test", "tfs_test"),
        endpoint="localhost:4317",
        service_name="test-service",
    )


class TestSeverityLevel:
    """Test suite for SeverityLevel enum."""

    def test_severity_values(self) -> None:
        """Test SeverityLevel enum values."""
        assert SeverityLevel.TRACE.value == "trace"
        assert SeverityLevel.DEBUG.value == "debug"
        assert SeverityLevel.INFO.value == "info"
        assert SeverityLevel.WARN.value == "warn"
        assert SeverityLevel.ERROR.value == "error"
        assert SeverityLevel.FATAL.value == "fatal"


class TestSpanKind:
    """Test suite for SpanKind enum."""

    def test_span_kind_values(self) -> None:
        """Test SpanKind enum values."""
        assert SpanKind.INTERNAL.value == "internal"
        assert SpanKind.SERVER.value == "server"
        assert SpanKind.CLIENT.value == "client"
        assert SpanKind.PRODUCER.value == "producer"
        assert SpanKind.CONSUMER.value == "consumer"


class TestInitializeSDKCommand:
    """Test suite for InitializeSDKCommand."""

    def test_create_command(self, valid_config: TelemetryConfig) -> None:
        """Test creating InitializeSDKCommand."""
        cmd = InitializeSDKCommand(config=valid_config)

        assert cmd.config == valid_config
        assert isinstance(cmd.timestamp, datetime)

    def test_timestamp_auto_set(self, valid_config: TelemetryConfig) -> None:
        """Test that timestamp is automatically set."""
        cmd = InitializeSDKCommand(config=valid_config)

        assert cmd.timestamp is not None
        assert isinstance(cmd.timestamp, datetime)


class TestShutdownSDKCommand:
    """Test suite for ShutdownSDKCommand."""

    def test_default_timeout(self) -> None:
        """Test default timeout value."""
        cmd = ShutdownSDKCommand()

        assert cmd.timeout_seconds == 30.0

    def test_custom_timeout(self) -> None:
        """Test custom timeout value."""
        cmd = ShutdownSDKCommand(timeout_seconds=60.0)

        assert cmd.timeout_seconds == 60.0


class TestFlushTelemetryCommand:
    """Test suite for FlushTelemetryCommand."""

    def test_create_command(self) -> None:
        """Test creating FlushTelemetryCommand."""
        cmd = FlushTelemetryCommand()

        assert isinstance(cmd.timestamp, datetime)


class TestRecordMetricCommand:
    """Test suite for RecordMetricCommand."""

    def test_create_command(self) -> None:
        """Test creating RecordMetricCommand."""
        cmd = RecordMetricCommand(
            name="test.metric",
            value=42.0,
            unit="ms",
            attributes={"key": "value"},
        )

        assert cmd.name == "test.metric"
        assert cmd.value == 42.0
        assert cmd.unit == "ms"
        assert cmd.attributes == {"key": "value"}

    def test_default_values(self) -> None:
        """Test default values."""
        cmd = RecordMetricCommand(name="test.metric", value=1.0)

        assert cmd.unit == ""
        assert cmd.attributes == {}


class TestRecordCounterCommand:
    """Test suite for RecordCounterCommand."""

    def test_create_command(self) -> None:
        """Test creating RecordCounterCommand."""
        cmd = RecordCounterCommand(
            name="test.counter",
            value=5,
            attributes={"endpoint": "/api"},
        )

        assert cmd.name == "test.counter"
        assert cmd.value == 5
        assert cmd.attributes == {"endpoint": "/api"}

    def test_default_value(self) -> None:
        """Test default value is 1."""
        cmd = RecordCounterCommand(name="test.counter")

        assert cmd.value == 1


class TestRecordGaugeCommand:
    """Test suite for RecordGaugeCommand."""

    def test_create_command(self) -> None:
        """Test creating RecordGaugeCommand."""
        cmd = RecordGaugeCommand(
            name="test.gauge",
            value=42.5,
            attributes={"pool": "default"},
        )

        assert cmd.name == "test.gauge"
        assert cmd.value == 42.5
        assert cmd.attributes == {"pool": "default"}


class TestRecordHistogramCommand:
    """Test suite for RecordHistogramCommand."""

    def test_create_command(self) -> None:
        """Test creating RecordHistogramCommand."""
        cmd = RecordHistogramCommand(
            name="test.histogram",
            value=0.125,
            unit="s",
            attributes={"method": "GET"},
        )

        assert cmd.name == "test.histogram"
        assert cmd.value == 0.125
        assert cmd.unit == "s"
        assert cmd.attributes == {"method": "GET"}


class TestEmitLogCommand:
    """Test suite for EmitLogCommand."""

    def test_create_command(self) -> None:
        """Test creating EmitLogCommand."""
        cmd = EmitLogCommand(
            message="Test log message",
            severity=SeverityLevel.INFO,
            attributes={"user_id": "123"},
        )

        assert cmd.message == "Test log message"
        assert cmd.severity == SeverityLevel.INFO
        assert cmd.attributes == {"user_id": "123"}

    def test_default_severity(self) -> None:
        """Test default severity is INFO."""
        cmd = EmitLogCommand(message="Test")

        assert cmd.severity == SeverityLevel.INFO

    def test_with_trace_correlation(self) -> None:
        """Test command with trace correlation."""
        cmd = EmitLogCommand(
            message="Correlated log",
            trace_id="abc123",
            span_id="xyz789",
        )

        assert cmd.trace_id == "abc123"
        assert cmd.span_id == "xyz789"


class TestStartSpanCommand:
    """Test suite for StartSpanCommand."""

    def test_create_command(self) -> None:
        """Test creating StartSpanCommand."""
        cmd = StartSpanCommand(
            name="test.span",
            kind=SpanKind.SERVER,
            attributes={"http.method": "GET"},
        )

        assert cmd.name == "test.span"
        assert cmd.kind == SpanKind.SERVER
        assert cmd.attributes == {"http.method": "GET"}

    def test_default_kind(self) -> None:
        """Test default span kind is INTERNAL."""
        cmd = StartSpanCommand(name="test.span")

        assert cmd.kind == SpanKind.INTERNAL

    def test_with_parent_span(self) -> None:
        """Test command with parent span."""
        cmd = StartSpanCommand(
            name="child.span",
            parent_span_id="parent-123",
        )

        assert cmd.parent_span_id == "parent-123"


class TestEndSpanCommand:
    """Test suite for EndSpanCommand."""

    def test_create_command(self) -> None:
        """Test creating EndSpanCommand."""
        cmd = EndSpanCommand(span_id="span-123")

        assert cmd.span_id == "span-123"
        assert cmd.error is None

    def test_with_error(self) -> None:
        """Test command with error."""
        error = ValueError("Test error")
        cmd = EndSpanCommand(span_id="span-123", error=error)

        assert cmd.span_id == "span-123"
        assert cmd.error == error


class TestAddSpanEventCommand:
    """Test suite for AddSpanEventCommand."""

    def test_create_command(self) -> None:
        """Test creating AddSpanEventCommand."""
        cmd = AddSpanEventCommand(
            span_id="span-123",
            name="checkpoint",
            attributes={"progress": 50},
        )

        assert cmd.span_id == "span-123"
        assert cmd.name == "checkpoint"
        assert cmd.attributes == {"progress": 50}


class TestCommandBus:
    """Test suite for CommandBus."""

    def test_register_and_dispatch(self) -> None:
        """Test registering and dispatching commands."""
        bus = CommandBus()
        results: list[str] = []

        class TestHandler:
            def handle(self, command: Command) -> str:
                results.append(command.__class__.__name__)
                return "handled"

        handler = TestHandler()
        bus.register(FlushTelemetryCommand, handler)

        result = bus.dispatch(FlushTelemetryCommand())

        assert result == "handled"
        assert results == ["FlushTelemetryCommand"]

    def test_dispatch_unregistered_command(self) -> None:
        """Test dispatching an unregistered command raises error."""
        bus = CommandBus()

        with pytest.raises(ValueError, match="No handler registered"):
            bus.dispatch(FlushTelemetryCommand())
