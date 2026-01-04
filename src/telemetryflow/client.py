"""TelemetryFlow Client - Main SDK entry point."""

from __future__ import annotations

import threading
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from telemetryflow.application.commands import (
    AddSpanEventCommand,
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
from telemetryflow.infrastructure.handlers import TelemetryCommandHandler

if TYPE_CHECKING:
    from telemetryflow.domain.config import TelemetryConfig


class TelemetryFlowError(Exception):
    """Base exception for TelemetryFlow SDK errors."""

    pass


class NotInitializedError(TelemetryFlowError):
    """Raised when attempting to use an uninitialized client."""

    pass


class TelemetryFlowClient:
    """
    Main TelemetryFlow SDK client.

    This client provides a simple interface for recording metrics, emitting logs,
    and creating trace spans. It wraps the OpenTelemetry SDK and handles all
    the complexity of exporter configuration and telemetry transmission.

    Example:
        >>> from telemetryflow import TelemetryFlowBuilder
        >>> client = (
        ...     TelemetryFlowBuilder()
        ...     .with_api_key("tfk_xxx", "tfs_xxx")
        ...     .with_endpoint("api.telemetryflow.id:4317")
        ...     .with_service("my-service")
        ...     .build()
        ... )
        >>> client.initialize()
        >>> client.increment_counter("requests.total")
        >>> client.shutdown()
    """

    def __init__(self, config: TelemetryConfig) -> None:
        """
        Initialize the TelemetryFlow client.

        Args:
            config: The SDK configuration
        """
        self._config = config
        self._handler = TelemetryCommandHandler()
        self._lock = threading.RLock()
        self._initialized = False

    def initialize(self) -> None:
        """
        Initialize the SDK and connect to the TelemetryFlow backend.

        This must be called before recording any telemetry data.

        Raises:
            TelemetryFlowError: If initialization fails
        """
        with self._lock:
            if self._initialized:
                return

            try:
                command = InitializeSDKCommand(config=self._config)
                self._handler.handle(command)
                self._initialized = True
            except Exception as e:
                raise TelemetryFlowError(f"Failed to initialize SDK: {e}") from e

    def shutdown(self, timeout: float = 30.0) -> None:
        """
        Shut down the SDK gracefully.

        This flushes any pending telemetry data and releases resources.

        Args:
            timeout: Maximum time to wait for shutdown in seconds
        """
        with self._lock:
            if not self._initialized:
                return

            try:
                command = ShutdownSDKCommand(timeout_seconds=timeout)
                self._handler.handle(command)
            finally:
                self._initialized = False

    def flush(self) -> None:
        """
        Force flush all pending telemetry data.

        This is useful before application shutdown or when you need
        to ensure data is sent immediately.
        """
        self._ensure_initialized()
        command = FlushTelemetryCommand()
        self._handler.handle(command)

    def is_initialized(self) -> bool:
        """Check if the client is initialized."""
        return self._initialized

    @property
    def config(self) -> TelemetryConfig:
        """Get the SDK configuration."""
        return self._config

    # Metrics API

    def record_metric(
        self,
        name: str,
        value: float,
        unit: str = "",
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """
        Record a generic metric value.

        Args:
            name: Metric name
            value: Metric value
            unit: Unit of measurement
            attributes: Additional attributes
        """
        self._ensure_initialized()
        command = RecordMetricCommand(
            name=name,
            value=value,
            unit=unit,
            attributes=attributes or {},
        )
        self._handler.handle(command)

    def increment_counter(
        self,
        name: str,
        value: int = 1,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """
        Increment a counter metric.

        Args:
            name: Counter name
            value: Amount to increment (default: 1)
            attributes: Additional attributes
        """
        self._ensure_initialized()
        command = RecordCounterCommand(
            name=name,
            value=value,
            attributes=attributes or {},
        )
        self._handler.handle(command)

    def record_gauge(
        self,
        name: str,
        value: float,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """
        Record a gauge metric value.

        Args:
            name: Gauge name
            value: Current value
            attributes: Additional attributes
        """
        self._ensure_initialized()
        command = RecordGaugeCommand(
            name=name,
            value=value,
            attributes=attributes or {},
        )
        self._handler.handle(command)

    def record_histogram(
        self,
        name: str,
        value: float,
        unit: str = "",
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """
        Record a histogram metric value.

        Args:
            name: Histogram name
            value: Value to record
            unit: Unit of measurement
            attributes: Additional attributes
        """
        self._ensure_initialized()
        command = RecordHistogramCommand(
            name=name,
            value=value,
            unit=unit,
            attributes=attributes or {},
        )
        self._handler.handle(command)

    # Logs API

    def log(
        self,
        message: str,
        severity: SeverityLevel = SeverityLevel.INFO,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """
        Emit a log entry.

        Args:
            message: Log message
            severity: Log severity level
            attributes: Additional attributes
        """
        self._ensure_initialized()
        command = EmitLogCommand(
            message=message,
            severity=severity,
            attributes=attributes or {},
        )
        self._handler.handle(command)

    def log_info(
        self,
        message: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """
        Emit an info-level log entry.

        Args:
            message: Log message
            attributes: Additional attributes
        """
        self.log(message, SeverityLevel.INFO, attributes)

    def log_warn(
        self,
        message: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """
        Emit a warning-level log entry.

        Args:
            message: Log message
            attributes: Additional attributes
        """
        self.log(message, SeverityLevel.WARN, attributes)

    def log_error(
        self,
        message: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """
        Emit an error-level log entry.

        Args:
            message: Log message
            attributes: Additional attributes
        """
        self.log(message, SeverityLevel.ERROR, attributes)

    def log_debug(
        self,
        message: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """
        Emit a debug-level log entry.

        Args:
            message: Log message
            attributes: Additional attributes
        """
        self.log(message, SeverityLevel.DEBUG, attributes)

    # Traces API

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: dict[str, Any] | None = None,
    ) -> str:
        """
        Start a new trace span.

        Args:
            name: Span name
            kind: Span kind (internal, server, client, producer, consumer)
            attributes: Span attributes

        Returns:
            Span ID for use with end_span and add_span_event
        """
        self._ensure_initialized()
        command = StartSpanCommand(
            name=name,
            kind=kind,
            attributes=attributes or {},
        )
        result: str = self._handler.handle(command)
        return result

    def end_span(
        self,
        span_id: str,
        error: Exception | None = None,
    ) -> None:
        """
        End a trace span.

        Args:
            span_id: The span ID returned by start_span
            error: Optional exception if the span represents a failure
        """
        self._ensure_initialized()
        command = EndSpanCommand(
            span_id=span_id,
            error=error,
        )
        self._handler.handle(command)

    def add_span_event(
        self,
        span_id: str,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """
        Add an event to an active span.

        Args:
            span_id: The span ID
            name: Event name
            attributes: Event attributes
        """
        self._ensure_initialized()
        command = AddSpanEventCommand(
            span_id=span_id,
            name=name,
            attributes=attributes or {},
        )
        self._handler.handle(command)

    @contextmanager
    def span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: dict[str, Any] | None = None,
    ) -> Generator[str, None, None]:
        """
        Context manager for creating a span.

        This is the recommended way to create spans as it ensures
        proper cleanup even if an exception occurs.

        Args:
            name: Span name
            kind: Span kind
            attributes: Span attributes

        Yields:
            Span ID

        Example:
            >>> with client.span("process_request", SpanKind.SERVER) as span_id:
            ...     # Do work
            ...     client.add_span_event(span_id, "checkpoint")
        """
        span_id = self.start_span(name, kind, attributes)
        error: Exception | None = None
        try:
            yield span_id
        except Exception as e:
            error = e
            raise
        finally:
            self.end_span(span_id, error)

    # Status API

    def get_status(self) -> dict[str, Any]:
        """
        Get the current SDK status.

        Returns:
            Dictionary with SDK status information
        """
        handler = self._handler
        uptime = None
        if handler.start_time:
            uptime = datetime.now(UTC) - handler.start_time

        return {
            "initialized": self._initialized,
            "version": self._get_version(),
            "service_name": self._config.service_name,
            "endpoint": self._config.endpoint,
            "protocol": self._config.protocol.value,
            "signals_enabled": [s.value for s in self._config.get_enabled_signals()],
            "uptime_seconds": uptime.total_seconds() if uptime else None,
            "metrics_sent": handler.metrics_sent,
            "logs_sent": handler.logs_sent,
            "spans_sent": handler.spans_sent,
        }

    def _ensure_initialized(self) -> None:
        """Ensure the client is initialized."""
        if not self._initialized:
            raise NotInitializedError("Client is not initialized. Call initialize() first.")

    def _get_version(self) -> str:
        """Get the SDK version."""
        from telemetryflow.version import __version__

        return __version__

    def __enter__(self) -> TelemetryFlowClient:
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.shutdown()

    def __repr__(self) -> str:
        """Return string representation."""
        status = "initialized" if self._initialized else "not initialized"
        return f"TelemetryFlowClient(service={self._config.service_name}, {status})"
