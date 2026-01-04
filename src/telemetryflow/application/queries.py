"""CQRS Queries for TelemetryFlow SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Protocol


class HealthStatus(str, Enum):
    """Health status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class Query:
    """Base class for all queries."""

    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def query_type(self) -> str:
        """Return the query type identifier."""
        return self.__class__.__name__


class QueryHandler(Protocol):
    """Protocol for query handlers."""

    def handle(self, query: Query) -> Any:
        """Handle a query and return results."""
        ...


class QueryBus:
    """Query bus for dispatching queries to handlers."""

    def __init__(self) -> None:
        self._handlers: dict[type[Query], QueryHandler] = {}

    def register(self, query_type: type[Query], handler: QueryHandler) -> None:
        """Register a handler for a query type."""
        self._handlers[query_type] = handler

    def dispatch(self, query: Query) -> Any:
        """Dispatch a query to its handler and return results."""
        handler = self._handlers.get(type(query))
        if handler is None:
            raise ValueError(f"No handler registered for {type(query).__name__}")
        return handler.handle(query)


# Query Result Types


@dataclass
class MetricQueryResult:
    """Result of a metric query."""

    name: str
    value: float
    unit: str
    timestamp: datetime
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedMetricResult:
    """Result of an aggregated metric query."""

    name: str
    min: float
    max: float
    sum: float
    count: int
    avg: float
    unit: str
    start_time: datetime
    end_time: datetime


@dataclass
class LogEntry:
    """A single log entry."""

    message: str
    severity: str
    timestamp: datetime
    trace_id: str | None = None
    span_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class LogsQueryResult:
    """Result of a logs query."""

    logs: list[LogEntry] = field(default_factory=list)
    total_count: int = 0
    has_more: bool = False


@dataclass
class SpanInfo:
    """Information about a trace span."""

    span_id: str
    trace_id: str
    name: str
    start_time: datetime
    end_time: datetime | None
    duration_ms: float | None
    kind: str
    status: str
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TraceQueryResult:
    """Result of a trace query."""

    trace_id: str
    spans: list[SpanInfo] = field(default_factory=list)
    duration_ms: float | None = None


@dataclass
class HealthQueryResult:
    """Result of a health query."""

    status: HealthStatus
    message: str
    components: dict[str, HealthStatus] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SDKStatusResult:
    """Result of an SDK status query."""

    initialized: bool
    version: str
    service_name: str
    endpoint: str
    protocol: str
    signals_enabled: list[str] = field(default_factory=list)
    uptime: timedelta | None = None
    metrics_sent: int = 0
    logs_sent: int = 0
    spans_sent: int = 0


# Queries


@dataclass
class GetMetricQuery(Query):
    """Query to get a specific metric."""

    name: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name is required for GetMetricQuery")


@dataclass
class AggregateMetricsQuery(Query):
    """Query to get aggregated metrics."""

    name: str = ""
    start_time: datetime | None = None
    end_time: datetime | None = None
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name is required for AggregateMetricsQuery")


@dataclass
class GetLogsQuery(Query):
    """Query to get logs."""

    severity: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    limit: int = 100
    offset: int = 0
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class GetTraceQuery(Query):
    """Query to get a specific trace."""

    trace_id: str = ""

    def __post_init__(self) -> None:
        if not self.trace_id:
            raise ValueError("trace_id is required for GetTraceQuery")


@dataclass
class SearchTracesQuery(Query):
    """Query to search traces."""

    service_name: str | None = None
    operation_name: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    min_duration_ms: float | None = None
    max_duration_ms: float | None = None
    limit: int = 100
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class GetHealthQuery(Query):
    """Query to get health status."""

    include_components: bool = True


@dataclass
class GetSDKStatusQuery(Query):
    """Query to get SDK status."""

    pass
