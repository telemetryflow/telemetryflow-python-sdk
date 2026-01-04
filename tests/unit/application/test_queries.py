"""Unit tests for CQRS Queries."""

from datetime import datetime, timedelta

import pytest

from telemetryflow.application.queries import (
    AggregatedMetricResult,
    AggregateMetricsQuery,
    GetHealthQuery,
    GetLogsQuery,
    GetMetricQuery,
    GetSDKStatusQuery,
    GetTraceQuery,
    HealthQueryResult,
    HealthStatus,
    LogEntry,
    LogsQueryResult,
    MetricQueryResult,
    Query,
    QueryBus,
    SDKStatusResult,
    SearchTracesQuery,
    SpanInfo,
    TraceQueryResult,
)


class TestHealthStatus:
    """Tests for HealthStatus enum."""

    def test_health_status_values(self) -> None:
        """Test HealthStatus enum values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"


class TestQueryBaseClass:
    """Tests for Query base class."""

    def test_query_type_property(self) -> None:
        """Test that query_type returns class name."""
        query = GetHealthQuery()
        assert query.query_type == "GetHealthQuery"

    def test_timestamp_is_datetime(self) -> None:
        """Test that timestamp is a datetime."""
        query = GetHealthQuery()
        assert isinstance(query.timestamp, datetime)


class TestQueryBus:
    """Tests for QueryBus."""

    def test_register_and_dispatch(self) -> None:
        """Test registering and dispatching queries."""
        bus = QueryBus()
        results = []

        class TestHandler:
            def handle(self, query: Query) -> str:
                results.append(query.__class__.__name__)
                return "result"

        handler = TestHandler()
        bus.register(GetHealthQuery, handler)

        result = bus.dispatch(GetHealthQuery())

        assert result == "result"
        assert results == ["GetHealthQuery"]

    def test_dispatch_unregistered_query(self) -> None:
        """Test dispatching an unregistered query raises error."""
        bus = QueryBus()

        with pytest.raises(ValueError, match="No handler registered"):
            bus.dispatch(GetHealthQuery())


class TestGetMetricQuery:
    """Tests for GetMetricQuery."""

    def test_create_query(self) -> None:
        """Test creating GetMetricQuery."""
        query = GetMetricQuery(
            name="cpu.usage",
            attributes={"host": "server1"},
        )

        assert query.name == "cpu.usage"
        assert query.attributes == {"host": "server1"}

    def test_requires_name(self) -> None:
        """Test that name is required."""
        with pytest.raises(ValueError, match="name is required"):
            GetMetricQuery(name="")


class TestAggregateMetricsQuery:
    """Tests for AggregateMetricsQuery."""

    def test_create_query(self) -> None:
        """Test creating AggregateMetricsQuery."""
        now = datetime.now()
        query = AggregateMetricsQuery(
            name="request.latency",
            start_time=now - timedelta(hours=1),
            end_time=now,
        )

        assert query.name == "request.latency"
        assert query.start_time is not None
        assert query.end_time is not None

    def test_requires_name(self) -> None:
        """Test that name is required."""
        with pytest.raises(ValueError, match="name is required"):
            AggregateMetricsQuery(name="")


class TestGetLogsQuery:
    """Tests for GetLogsQuery."""

    def test_default_values(self) -> None:
        """Test default query values."""
        query = GetLogsQuery()

        assert query.severity is None
        assert query.limit == 100
        assert query.offset == 0
        assert query.attributes == {}

    def test_with_parameters(self) -> None:
        """Test query with parameters."""
        query = GetLogsQuery(
            severity="error",
            limit=50,
            offset=100,
            attributes={"service": "api"},
        )

        assert query.severity == "error"
        assert query.limit == 50
        assert query.offset == 100


class TestGetTraceQuery:
    """Tests for GetTraceQuery."""

    def test_create_query(self) -> None:
        """Test creating GetTraceQuery."""
        query = GetTraceQuery(trace_id="abc123")

        assert query.trace_id == "abc123"

    def test_requires_trace_id(self) -> None:
        """Test that trace_id is required."""
        with pytest.raises(ValueError, match="trace_id is required"):
            GetTraceQuery(trace_id="")


class TestSearchTracesQuery:
    """Tests for SearchTracesQuery."""

    def test_default_values(self) -> None:
        """Test default query values."""
        query = SearchTracesQuery()

        assert query.service_name is None
        assert query.operation_name is None
        assert query.limit == 100
        assert query.attributes == {}

    def test_with_parameters(self) -> None:
        """Test query with parameters."""
        query = SearchTracesQuery(
            service_name="api-gateway",
            operation_name="GET /users",
            min_duration_ms=100.0,
            max_duration_ms=1000.0,
        )

        assert query.service_name == "api-gateway"
        assert query.operation_name == "GET /users"
        assert query.min_duration_ms == 100.0
        assert query.max_duration_ms == 1000.0


class TestGetHealthQuery:
    """Tests for GetHealthQuery."""

    def test_default_include_components(self) -> None:
        """Test default include_components value."""
        query = GetHealthQuery()

        assert query.include_components is True

    def test_exclude_components(self) -> None:
        """Test with include_components disabled."""
        query = GetHealthQuery(include_components=False)

        assert query.include_components is False


class TestGetSDKStatusQuery:
    """Tests for GetSDKStatusQuery."""

    def test_create_query(self) -> None:
        """Test creating GetSDKStatusQuery."""
        query = GetSDKStatusQuery()

        assert isinstance(query.timestamp, datetime)


class TestMetricQueryResult:
    """Tests for MetricQueryResult."""

    def test_create_result(self) -> None:
        """Test creating MetricQueryResult."""
        now = datetime.now()
        result = MetricQueryResult(
            name="cpu.usage",
            value=75.5,
            unit="%",
            timestamp=now,
            attributes={"host": "server1"},
        )

        assert result.name == "cpu.usage"
        assert result.value == 75.5
        assert result.unit == "%"
        assert result.timestamp == now
        assert result.attributes == {"host": "server1"}


class TestAggregatedMetricResult:
    """Tests for AggregatedMetricResult."""

    def test_create_result(self) -> None:
        """Test creating AggregatedMetricResult."""
        now = datetime.now()
        result = AggregatedMetricResult(
            name="request.latency",
            min=10.0,
            max=500.0,
            sum=5000.0,
            count=100,
            avg=50.0,
            unit="ms",
            start_time=now - timedelta(hours=1),
            end_time=now,
        )

        assert result.name == "request.latency"
        assert result.min == 10.0
        assert result.max == 500.0
        assert result.sum == 5000.0
        assert result.count == 100
        assert result.avg == 50.0


class TestLogEntry:
    """Tests for LogEntry."""

    def test_create_entry(self) -> None:
        """Test creating LogEntry."""
        now = datetime.now()
        entry = LogEntry(
            message="Test log message",
            severity="info",
            timestamp=now,
            trace_id="trace-123",
            span_id="span-456",
        )

        assert entry.message == "Test log message"
        assert entry.severity == "info"
        assert entry.trace_id == "trace-123"
        assert entry.span_id == "span-456"


class TestLogsQueryResult:
    """Tests for LogsQueryResult."""

    def test_default_values(self) -> None:
        """Test default result values."""
        result = LogsQueryResult()

        assert result.logs == []
        assert result.total_count == 0
        assert result.has_more is False

    def test_with_logs(self) -> None:
        """Test result with logs."""
        now = datetime.now()
        logs = [
            LogEntry(message="Log 1", severity="info", timestamp=now),
            LogEntry(message="Log 2", severity="error", timestamp=now),
        ]
        result = LogsQueryResult(logs=logs, total_count=100, has_more=True)

        assert len(result.logs) == 2
        assert result.total_count == 100
        assert result.has_more is True


class TestSpanInfo:
    """Tests for SpanInfo."""

    def test_create_span_info(self) -> None:
        """Test creating SpanInfo."""
        now = datetime.now()
        span = SpanInfo(
            span_id="span-123",
            trace_id="trace-456",
            name="GET /users",
            start_time=now,
            end_time=now + timedelta(milliseconds=100),
            duration_ms=100.0,
            kind="server",
            status="ok",
        )

        assert span.span_id == "span-123"
        assert span.trace_id == "trace-456"
        assert span.name == "GET /users"
        assert span.duration_ms == 100.0


class TestTraceQueryResult:
    """Tests for TraceQueryResult."""

    def test_create_result(self) -> None:
        """Test creating TraceQueryResult."""
        result = TraceQueryResult(
            trace_id="trace-123",
            spans=[],
            duration_ms=500.0,
        )

        assert result.trace_id == "trace-123"
        assert result.spans == []
        assert result.duration_ms == 500.0


class TestHealthQueryResult:
    """Tests for HealthQueryResult."""

    def test_create_result(self) -> None:
        """Test creating HealthQueryResult."""
        result = HealthQueryResult(
            status=HealthStatus.HEALTHY,
            message="All systems operational",
            components={
                "database": HealthStatus.HEALTHY,
                "cache": HealthStatus.DEGRADED,
            },
        )

        assert result.status == HealthStatus.HEALTHY
        assert result.message == "All systems operational"
        assert len(result.components) == 2


class TestSDKStatusResult:
    """Tests for SDKStatusResult."""

    def test_create_result(self) -> None:
        """Test creating SDKStatusResult."""
        result = SDKStatusResult(
            initialized=True,
            version="1.0.0",
            service_name="test-service",
            endpoint="localhost:4317",
            protocol="grpc",
            signals_enabled=["metrics", "traces"],
            uptime=timedelta(hours=2),
            metrics_sent=1000,
            logs_sent=500,
            spans_sent=200,
        )

        assert result.initialized is True
        assert result.version == "1.0.0"
        assert result.service_name == "test-service"
        assert result.metrics_sent == 1000
        assert result.logs_sent == 500
        assert result.spans_sent == 200
