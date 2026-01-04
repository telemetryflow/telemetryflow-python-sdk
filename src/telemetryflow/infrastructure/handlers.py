"""Telemetry Command Handler - Infrastructure layer implementation."""

from __future__ import annotations

import logging
import threading
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from opentelemetry import trace
from opentelemetry.metrics import get_meter_provider, set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import SpanKind as OTELSpanKind
from opentelemetry.trace import Status, StatusCode

from telemetryflow.application.commands import (
    AddSpanEventCommand,
    Command,
    EmitBatchLogsCommand,
    EmitLogCommand,
    EndSpanCommand,
    FlushTelemetryCommand,
    InitializeSDKCommand,
    RecordCounterCommand,
    RecordGaugeCommand,
    RecordHistogramCommand,
    RecordMetricCommand,
    ShutdownSDKCommand,
    SpanKind,
    StartSpanCommand,
)
from telemetryflow.infrastructure.exporters import OTLPExporterFactory

if TYPE_CHECKING:
    from opentelemetry.metrics import Meter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.trace import Span, Tracer

    from telemetryflow.domain.config import TelemetryConfig


logger = logging.getLogger(__name__)


class TelemetryCommandHandler:
    """
    Central command handler for all telemetry operations.

    This handler implements the command handling for metrics, logs, and traces,
    delegating to OpenTelemetry SDK components.
    """

    def __init__(self) -> None:
        """Initialize the command handler."""
        self._config: TelemetryConfig | None = None
        self._initialized: bool = False
        self._init_lock = threading.RLock()

        # OpenTelemetry providers
        self._tracer_provider: TracerProvider | None = None
        self._meter_provider: MeterProvider | None = None
        self._tracer: Tracer | None = None
        self._meter: Meter | None = None

        # Exporters and processors
        self._exporter_factory: OTLPExporterFactory | None = None
        self._span_processor: BatchSpanProcessor | None = None
        self._metric_reader: PeriodicExportingMetricReader | None = None

        # Active spans tracking
        self._active_spans: dict[str, Span] = {}
        self._spans_lock = threading.Lock()

        # Metrics instruments cache
        self._counters: dict[str, Any] = {}
        self._histograms: dict[str, Any] = {}
        self._gauges: dict[str, Any] = {}
        self._instruments_lock = threading.Lock()

        # Statistics
        self._start_time: datetime | None = None
        self._metrics_sent: int = 0
        self._logs_sent: int = 0
        self._spans_sent: int = 0

    def handle(self, command: Command) -> Any:
        """
        Handle a command by dispatching to the appropriate handler method.

        Args:
            command: The command to handle

        Returns:
            Command-specific result
        """
        handlers = {
            InitializeSDKCommand: self._handle_initialize,
            ShutdownSDKCommand: self._handle_shutdown,
            FlushTelemetryCommand: self._handle_flush,
            RecordMetricCommand: self._handle_record_metric,
            RecordCounterCommand: self._handle_record_counter,
            RecordGaugeCommand: self._handle_record_gauge,
            RecordHistogramCommand: self._handle_record_histogram,
            EmitLogCommand: self._handle_emit_log,
            EmitBatchLogsCommand: self._handle_emit_batch_logs,
            StartSpanCommand: self._handle_start_span,
            EndSpanCommand: self._handle_end_span,
            AddSpanEventCommand: self._handle_add_span_event,
        }

        handler = handlers.get(type(command))
        if handler is None:
            raise ValueError(f"Unknown command type: {type(command).__name__}")

        return handler(command)  # type: ignore[operator]

    def _handle_initialize(self, command: InitializeSDKCommand) -> None:
        """Initialize the SDK with the given configuration."""
        with self._init_lock:
            if self._initialized:
                logger.warning("SDK already initialized")
                return

            self._config = command.config
            self._exporter_factory = OTLPExporterFactory(self._config)
            resource = self._exporter_factory.create_resource()

            # Initialize trace provider if traces are enabled
            if self._config.enable_traces:
                self._init_tracer(resource)

            # Initialize meter provider if metrics are enabled
            if self._config.enable_metrics:
                self._init_meter(resource)

            self._initialized = True
            self._start_time = datetime.now(UTC)
            logger.info(f"TelemetryFlow SDK initialized for service '{self._config.service_name}'")

    def _init_tracer(self, resource: Resource) -> None:
        """Initialize the tracer provider."""
        if self._exporter_factory is None or self._config is None:
            return

        trace_exporter = self._exporter_factory.create_trace_exporter()
        self._span_processor = BatchSpanProcessor(
            trace_exporter,
            max_queue_size=self._config.batch_max_size,
            schedule_delay_millis=int(self._config.batch_timeout.total_seconds() * 1000),
        )

        self._tracer_provider = TracerProvider(resource=resource)
        self._tracer_provider.add_span_processor(self._span_processor)
        trace.set_tracer_provider(self._tracer_provider)
        self._tracer = trace.get_tracer(
            "telemetryflow",
            self._config.service_version,
        )

    def _init_meter(self, resource: Resource) -> None:
        """Initialize the meter provider."""
        if self._exporter_factory is None or self._config is None:
            return

        metric_exporter = self._exporter_factory.create_metric_exporter()
        self._metric_reader = PeriodicExportingMetricReader(
            metric_exporter,
            export_interval_millis=int(self._config.batch_timeout.total_seconds() * 1000),
        )

        self._meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[self._metric_reader],
        )
        set_meter_provider(self._meter_provider)
        self._meter = get_meter_provider().get_meter(
            "telemetryflow",
            self._config.service_version,
        )

    def _handle_shutdown(self, command: ShutdownSDKCommand) -> None:
        """Shut down the SDK gracefully."""
        with self._init_lock:
            if not self._initialized:
                return

            errors: list[Exception] = []

            # Flush and shutdown tracer provider
            if self._tracer_provider is not None:
                try:
                    self._tracer_provider.force_flush(
                        timeout_millis=int(command.timeout_seconds * 1000)
                    )
                    self._tracer_provider.shutdown()
                except Exception as e:
                    errors.append(e)
                    logger.error(f"Error shutting down tracer provider: {e}")

            # Shutdown meter provider
            if self._meter_provider is not None:
                try:
                    self._meter_provider.shutdown(
                        timeout_millis=int(command.timeout_seconds * 1000)
                    )
                except Exception as e:
                    errors.append(e)
                    logger.error(f"Error shutting down meter provider: {e}")

            # Clear active spans
            with self._spans_lock:
                self._active_spans.clear()

            self._initialized = False
            logger.info("TelemetryFlow SDK shut down")

            if errors:
                raise RuntimeError(f"Shutdown completed with {len(errors)} error(s)")

    def _handle_flush(self, _command: FlushTelemetryCommand) -> None:
        """Force flush all pending telemetry data."""
        if not self._initialized:
            return

        if self._tracer_provider is not None:
            self._tracer_provider.force_flush()

        if self._meter_provider is not None:
            self._meter_provider.force_flush()

    def _handle_record_metric(self, command: RecordMetricCommand) -> None:
        """Record a generic metric (as gauge)."""
        if not self._initialized or self._meter is None:
            return

        # Use gauge for generic metrics
        self._handle_record_gauge(
            RecordGaugeCommand(
                name=command.name,
                value=command.value,
                attributes=command.attributes,
            )
        )
        self._metrics_sent += 1

    def _handle_record_counter(self, command: RecordCounterCommand) -> None:
        """Record a counter metric."""
        if not self._initialized or self._meter is None:
            return

        with self._instruments_lock:
            if command.name not in self._counters:
                self._counters[command.name] = self._meter.create_counter(
                    command.name,
                    description=f"Counter for {command.name}",
                )

            counter = self._counters[command.name]

        attrs = self._convert_attributes(command.attributes)
        counter.add(command.value, attrs)
        self._metrics_sent += 1

    def _handle_record_gauge(self, command: RecordGaugeCommand) -> None:
        """Record a gauge metric."""
        if not self._initialized or self._meter is None:
            return

        with self._instruments_lock:
            if command.name not in self._gauges:
                self._gauges[command.name] = self._meter.create_up_down_counter(
                    command.name,
                    description=f"Gauge for {command.name}",
                )

            gauge = self._gauges[command.name]

        attrs = self._convert_attributes(command.attributes)
        # For UpDownCounter, we need to track the delta
        # In a real implementation, you might want to use ObservableGauge
        gauge.add(command.value, attrs)
        self._metrics_sent += 1

    def _handle_record_histogram(self, command: RecordHistogramCommand) -> None:
        """Record a histogram metric."""
        if not self._initialized or self._meter is None:
            return

        with self._instruments_lock:
            if command.name not in self._histograms:
                self._histograms[command.name] = self._meter.create_histogram(
                    command.name,
                    unit=command.unit or "1",
                    description=f"Histogram for {command.name}",
                )

            histogram = self._histograms[command.name]

        attrs = self._convert_attributes(command.attributes)
        histogram.record(command.value, attrs)
        self._metrics_sent += 1

    def _handle_emit_log(self, command: EmitLogCommand) -> None:
        """Emit a log entry."""
        if not self._initialized:
            return

        # For now, use span events as log implementation
        # A full log implementation would use OTEL log SDK
        if self._tracer is not None:
            current_span = trace.get_current_span()
            if current_span.is_recording():
                attrs = self._convert_attributes(command.attributes)
                attrs["log.severity"] = command.severity.value
                current_span.add_event(command.message, attrs)

        self._logs_sent += 1

    def _handle_emit_batch_logs(self, command: EmitBatchLogsCommand) -> None:
        """Emit multiple log entries."""
        for log_cmd in command.logs:
            self._handle_emit_log(log_cmd)

    def _handle_start_span(self, command: StartSpanCommand) -> str:
        """Start a new trace span and return its ID."""
        if not self._initialized or self._tracer is None:
            return ""

        # Convert span kind
        otel_kind = self._convert_span_kind(command.kind)

        # Start the span
        span = self._tracer.start_span(
            command.name,
            kind=otel_kind,
            attributes=self._convert_attributes(command.attributes),
        )

        # Generate and store span ID
        span_id = str(uuid.uuid4())
        with self._spans_lock:
            self._active_spans[span_id] = span

        self._spans_sent += 1
        return span_id

    def _handle_end_span(self, command: EndSpanCommand) -> None:
        """End a trace span."""
        with self._spans_lock:
            span = self._active_spans.pop(command.span_id, None)

        if span is None:
            logger.warning(f"Span not found: {command.span_id}")
            return

        if command.error:
            span.set_status(Status(StatusCode.ERROR, str(command.error)))
            span.record_exception(command.error)
        else:
            span.set_status(Status(StatusCode.OK))

        span.end()

    def _handle_add_span_event(self, command: AddSpanEventCommand) -> None:
        """Add an event to an active span."""
        with self._spans_lock:
            span = self._active_spans.get(command.span_id)

        if span is None:
            logger.warning(f"Span not found: {command.span_id}")
            return

        attrs = self._convert_attributes(command.attributes)
        span.add_event(command.name, attrs)

    def _convert_span_kind(self, kind: SpanKind) -> OTELSpanKind:
        """Convert SDK SpanKind to OpenTelemetry SpanKind."""
        mapping = {
            SpanKind.INTERNAL: OTELSpanKind.INTERNAL,
            SpanKind.SERVER: OTELSpanKind.SERVER,
            SpanKind.CLIENT: OTELSpanKind.CLIENT,
            SpanKind.PRODUCER: OTELSpanKind.PRODUCER,
            SpanKind.CONSUMER: OTELSpanKind.CONSUMER,
        }
        return mapping.get(kind, OTELSpanKind.INTERNAL)

    def _convert_attributes(self, attributes: dict[str, Any]) -> dict[str, Any]:
        """Convert attributes to OpenTelemetry compatible format."""
        result: dict[str, Any] = {}
        for key, value in attributes.items():
            # OpenTelemetry supports: str, bool, int, float, and sequences of these
            if isinstance(value, (str, bool, int, float)):
                result[key] = value
            elif isinstance(value, (list, tuple)):
                # Ensure all items in sequence are valid types
                result[key] = [v for v in value if isinstance(v, (str, bool, int, float))]
            else:
                # Convert other types to string
                result[key] = str(value)
        return result

    @property
    def is_initialized(self) -> bool:
        """Check if the handler is initialized."""
        return self._initialized

    @property
    def config(self) -> TelemetryConfig | None:
        """Get the current configuration."""
        return self._config

    @property
    def start_time(self) -> datetime | None:
        """Get the SDK start time."""
        return self._start_time

    @property
    def metrics_sent(self) -> int:
        """Get the number of metrics sent."""
        return self._metrics_sent

    @property
    def logs_sent(self) -> int:
        """Get the number of logs sent."""
        return self._logs_sent

    @property
    def spans_sent(self) -> int:
        """Get the number of spans sent."""
        return self._spans_sent
