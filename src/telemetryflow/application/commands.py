"""CQRS Commands for TelemetryFlow SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Protocol

from telemetryflow.domain.config import TelemetryConfig


class SeverityLevel(str, Enum):
    """Log severity levels."""

    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"


class SpanKind(str, Enum):
    """Span kind for traces."""

    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


@dataclass
class Command:
    """Base class for all commands."""

    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def command_type(self) -> str:
        """Return the command type identifier."""
        return self.__class__.__name__


class CommandHandler(Protocol):
    """Protocol for command handlers."""

    def handle(self, command: Command) -> Any:
        """Handle a command."""
        ...


class CommandBus:
    """Command bus for dispatching commands to handlers."""

    def __init__(self) -> None:
        self._handlers: dict[type[Command], CommandHandler] = {}

    def register(self, command_type: type[Command], handler: CommandHandler) -> None:
        """Register a handler for a command type."""
        self._handlers[command_type] = handler

    def dispatch(self, command: Command) -> Any:
        """Dispatch a command to its handler."""
        handler = self._handlers.get(type(command))
        if handler is None:
            raise ValueError(f"No handler registered for {type(command).__name__}")
        return handler.handle(command)


# Lifecycle Commands


@dataclass
class InitializeSDKCommand(Command):
    """Command to initialize the SDK."""

    config: TelemetryConfig = field(default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.config is None:
            raise ValueError("config is required for InitializeSDKCommand")


@dataclass
class ShutdownSDKCommand(Command):
    """Command to shut down the SDK gracefully."""

    timeout_seconds: float = 30.0


@dataclass
class FlushTelemetryCommand(Command):
    """Command to force flush all pending telemetry data."""

    pass


# Metric Commands


@dataclass
class RecordMetricCommand(Command):
    """Command to record a generic metric."""

    name: str = ""
    value: float = 0.0
    unit: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name is required for RecordMetricCommand")


@dataclass
class RecordCounterCommand(Command):
    """Command to increment a counter metric."""

    name: str = ""
    value: int = 1
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name is required for RecordCounterCommand")


@dataclass
class RecordGaugeCommand(Command):
    """Command to record a gauge metric."""

    name: str = ""
    value: float = 0.0
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name is required for RecordGaugeCommand")


@dataclass
class RecordHistogramCommand(Command):
    """Command to record a histogram metric."""

    name: str = ""
    value: float = 0.0
    unit: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name is required for RecordHistogramCommand")


# Log Commands


@dataclass
class EmitLogCommand(Command):
    """Command to emit a log entry."""

    message: str = ""
    severity: SeverityLevel = SeverityLevel.INFO
    attributes: dict[str, Any] = field(default_factory=dict)
    trace_id: str | None = None
    span_id: str | None = None

    def __post_init__(self) -> None:
        if not self.message:
            raise ValueError("message is required for EmitLogCommand")


@dataclass
class EmitBatchLogsCommand(Command):
    """Command to emit multiple log entries."""

    logs: list[EmitLogCommand] = field(default_factory=list)


# Trace Commands


@dataclass
class StartSpanCommand(Command):
    """Command to start a new trace span."""

    name: str = ""
    kind: SpanKind = SpanKind.INTERNAL
    attributes: dict[str, Any] = field(default_factory=dict)
    parent_span_id: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name is required for StartSpanCommand")


@dataclass
class EndSpanCommand(Command):
    """Command to end a trace span."""

    span_id: str = ""
    error: Exception | None = None

    def __post_init__(self) -> None:
        if not self.span_id:
            raise ValueError("span_id is required for EndSpanCommand")


@dataclass
class AddSpanEventCommand(Command):
    """Command to add an event to a span."""

    span_id: str = ""
    name: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.span_id:
            raise ValueError("span_id is required for AddSpanEventCommand")
        if not self.name:
            raise ValueError("name is required for AddSpanEventCommand")
