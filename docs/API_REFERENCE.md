# API Reference

Complete API documentation for the TelemetryFlow Python SDK.

## Table of Contents

- [Client API](#client-api)
- [Builder API](#builder-api)
- [Domain API](#domain-api)
- [Commands](#commands)
- [Queries](#queries)
- [Middleware](#middleware)
- [Exceptions](#exceptions)

## Client API

### TelemetryFlowClient

The main SDK client for recording telemetry data.

```python
from telemetryflow import TelemetryFlowClient
from telemetryflow.domain.config import TelemetryConfig
```

#### Constructor

```python
TelemetryFlowClient(config: TelemetryConfig)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `config` | `TelemetryConfig` | SDK configuration |

#### Lifecycle Methods

##### initialize()

Initialize the SDK and connect to the TelemetryFlow backend.

```python
def initialize(self) -> None
```

**Raises:**
- `TelemetryFlowError`: If initialization fails

**Example:**
```python
client = TelemetryFlowBuilder().with_auto_configuration().build()
client.initialize()
```

##### shutdown()

Shut down the SDK gracefully, flushing pending data.

```python
def shutdown(self, timeout: float = 30.0) -> None
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeout` | `float` | `30.0` | Maximum wait time in seconds |

**Example:**
```python
client.shutdown(timeout=60.0)
```

##### flush()

Force flush all pending telemetry data.

```python
def flush(self) -> None
```

**Raises:**
- `NotInitializedError`: If client is not initialized

##### is_initialized()

Check if the client is initialized.

```python
def is_initialized(self) -> bool
```

**Returns:** `True` if initialized, `False` otherwise

##### config

Property to get the SDK configuration.

```python
@property
def config(self) -> TelemetryConfig
```

#### Metrics Methods

##### increment_counter()

Increment a counter metric.

```python
def increment_counter(
    self,
    name: str,
    value: int = 1,
    attributes: dict[str, Any] | None = None,
) -> None
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Counter name |
| `value` | `int` | `1` | Increment value |
| `attributes` | `dict` | `None` | Metric attributes |

**Example:**
```python
client.increment_counter("http.requests.total", attributes={"method": "GET"})
client.increment_counter("cache.hits", value=5)
```

##### record_gauge()

Record a gauge metric value.

```python
def record_gauge(
    self,
    name: str,
    value: float,
    attributes: dict[str, Any] | None = None,
) -> None
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Gauge name |
| `value` | `float` | Required | Current value |
| `attributes` | `dict` | `None` | Metric attributes |

**Example:**
```python
client.record_gauge("connections.active", 42)
client.record_gauge("memory.usage_bytes", 1024*1024*512)
```

##### record_histogram()

Record a histogram metric value.

```python
def record_histogram(
    self,
    name: str,
    value: float,
    unit: str = "",
    attributes: dict[str, Any] | None = None,
) -> None
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Histogram name |
| `value` | `float` | Required | Value to record |
| `unit` | `str` | `""` | Unit of measurement |
| `attributes` | `dict` | `None` | Metric attributes |

**Example:**
```python
client.record_histogram("http.request.duration", 0.125, unit="s")
client.record_histogram("db.query.rows", 1000)
```

##### record_metric()

Record a generic metric value.

```python
def record_metric(
    self,
    name: str,
    value: float,
    unit: str = "",
    attributes: dict[str, Any] | None = None,
) -> None
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Metric name |
| `value` | `float` | Required | Metric value |
| `unit` | `str` | `""` | Unit of measurement |
| `attributes` | `dict` | `None` | Metric attributes |

#### Logs Methods

##### log()

Emit a log entry with custom severity.

```python
def log(
    self,
    message: str,
    severity: SeverityLevel = SeverityLevel.INFO,
    attributes: dict[str, Any] | None = None,
) -> None
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | `str` | Required | Log message |
| `severity` | `SeverityLevel` | `INFO` | Log severity |
| `attributes` | `dict` | `None` | Log attributes |

**Example:**
```python
from telemetryflow.application.commands import SeverityLevel

client.log("Custom message", SeverityLevel.WARN, {"key": "value"})
```

##### log_debug()

Emit a debug-level log.

```python
def log_debug(self, message: str, attributes: dict[str, Any] | None = None) -> None
```

##### log_info()

Emit an info-level log.

```python
def log_info(self, message: str, attributes: dict[str, Any] | None = None) -> None
```

**Example:**
```python
client.log_info("User logged in", {"user_id": "123"})
```

##### log_warn()

Emit a warning-level log.

```python
def log_warn(self, message: str, attributes: dict[str, Any] | None = None) -> None
```

##### log_error()

Emit an error-level log.

```python
def log_error(self, message: str, attributes: dict[str, Any] | None = None) -> None
```

**Example:**
```python
client.log_error("Database connection failed", {"database": "users_db"})
```

#### Traces Methods

##### start_span()

Start a new trace span.

```python
def start_span(
    self,
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: dict[str, Any] | None = None,
) -> str
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Span name |
| `kind` | `SpanKind` | `INTERNAL` | Span kind |
| `attributes` | `dict` | `None` | Span attributes |

**Returns:** Span ID string

**Example:**
```python
from telemetryflow.application.commands import SpanKind

span_id = client.start_span("http.request", SpanKind.SERVER)
```

##### end_span()

End a trace span.

```python
def end_span(self, span_id: str, error: Exception | None = None) -> None
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `span_id` | `str` | Required | Span ID from start_span |
| `error` | `Exception` | `None` | Exception if span failed |

**Example:**
```python
try:
    # work...
except Exception as e:
    client.end_span(span_id, error=e)
    raise
else:
    client.end_span(span_id)
```

##### add_span_event()

Add an event to an active span.

```python
def add_span_event(
    self,
    span_id: str,
    name: str,
    attributes: dict[str, Any] | None = None,
) -> None
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `span_id` | `str` | Required | Span ID |
| `name` | `str` | Required | Event name |
| `attributes` | `dict` | `None` | Event attributes |

**Example:**
```python
client.add_span_event(span_id, "query_executed", {"rows": 100})
```

##### span()

Context manager for span lifecycle.

```python
@contextmanager
def span(
    self,
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: dict[str, Any] | None = None,
) -> Generator[str, None, None]
```

**Yields:** Span ID string

**Example:**
```python
with client.span("process_request", SpanKind.SERVER) as span_id:
    client.add_span_event(span_id, "started")
    # work...
    client.add_span_event(span_id, "completed")
```

#### Status Methods

##### get_status()

Get the current SDK status.

```python
def get_status(self) -> dict[str, Any]
```

**Returns:** Dictionary with status information:
- `initialized`: bool
- `version`: str
- `service_name`: str
- `endpoint`: str
- `protocol`: str
- `signals_enabled`: list[str]
- `uptime_seconds`: float | None
- `metrics_sent`: int
- `logs_sent`: int
- `spans_sent`: int

#### Context Manager

The client can be used as a context manager:

```python
with TelemetryFlowBuilder().with_auto_configuration().build() as client:
    client.increment_counter("app.started")
# Client automatically initialized and shut down
```

---

## Builder API

### TelemetryFlowBuilder

Fluent builder for creating TelemetryFlow clients.

```python
from telemetryflow import TelemetryFlowBuilder
```

#### Constructor

```python
TelemetryFlowBuilder()
```

#### API Key Configuration

##### with_api_key()

Set API key credentials.

```python
def with_api_key(self, key_id: str, key_secret: str) -> TelemetryFlowBuilder
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `key_id` | `str` | API key ID (must start with 'tfk_') |
| `key_secret` | `str` | API key secret (must start with 'tfs_') |

##### with_api_key_from_env()

Load API key from environment variables.

```python
def with_api_key_from_env(self) -> TelemetryFlowBuilder
```

Uses: `TELEMETRYFLOW_API_KEY_ID`, `TELEMETRYFLOW_API_KEY_SECRET`

#### Endpoint Configuration

##### with_endpoint()

Set the collector endpoint.

```python
def with_endpoint(self, endpoint: str) -> TelemetryFlowBuilder
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `endpoint` | `str` | Endpoint address (host:port) |

##### with_endpoint_from_env()

Load endpoint from environment variable.

```python
def with_endpoint_from_env(self) -> TelemetryFlowBuilder
```

Uses: `TELEMETRYFLOW_ENDPOINT` (default: `api.telemetryflow.id:4317`)

#### Service Configuration

##### with_service()

Set service name and optional version.

```python
def with_service(self, name: str, version: str | None = None) -> TelemetryFlowBuilder
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Service name |
| `version` | `str` | `None` | Service version |

##### with_service_from_env()

Load service configuration from environment.

```python
def with_service_from_env(self) -> TelemetryFlowBuilder
```

Uses: `TELEMETRYFLOW_SERVICE_NAME`, `TELEMETRYFLOW_SERVICE_VERSION`

##### with_service_namespace()

Set service namespace.

```python
def with_service_namespace(self, namespace: str) -> TelemetryFlowBuilder
```

##### with_service_namespace_from_env()

Load service namespace from environment.

```python
def with_service_namespace_from_env(self) -> TelemetryFlowBuilder
```

Uses: `TELEMETRYFLOW_SERVICE_NAMESPACE`

#### Environment Configuration

##### with_environment()

Set deployment environment.

```python
def with_environment(self, environment: str) -> TelemetryFlowBuilder
```

##### with_environment_from_env()

Load environment from environment variable.

```python
def with_environment_from_env(self) -> TelemetryFlowBuilder
```

Uses: `TELEMETRYFLOW_ENVIRONMENT`, `ENV`, `ENVIRONMENT` (in order)

#### Protocol Configuration

##### with_protocol()

Set OTLP protocol.

```python
def with_protocol(self, protocol: Protocol) -> TelemetryFlowBuilder
```

##### with_grpc()

Use gRPC protocol (default).

```python
def with_grpc(self) -> TelemetryFlowBuilder
```

##### with_http()

Use HTTP protocol.

```python
def with_http(self) -> TelemetryFlowBuilder
```

##### with_insecure()

Enable/disable TLS verification.

```python
def with_insecure(self, insecure: bool = True) -> TelemetryFlowBuilder
```

#### Signal Configuration

##### with_signals()

Configure which signals to enable.

```python
def with_signals(
    self,
    metrics: bool = True,
    logs: bool = True,
    traces: bool = True,
) -> TelemetryFlowBuilder
```

##### with_metrics_only()

Enable only metrics.

```python
def with_metrics_only(self) -> TelemetryFlowBuilder
```

##### with_logs_only()

Enable only logs.

```python
def with_logs_only(self) -> TelemetryFlowBuilder
```

##### with_traces_only()

Enable only traces.

```python
def with_traces_only(self) -> TelemetryFlowBuilder
```

##### with_exemplars()

Enable/disable exemplars.

```python
def with_exemplars(self, enabled: bool = True) -> TelemetryFlowBuilder
```

#### Advanced Configuration

##### with_timeout()

Set connection timeout.

```python
def with_timeout(self, timeout: timedelta) -> TelemetryFlowBuilder
```

##### with_collector_id()

Set collector ID.

```python
def with_collector_id(self, collector_id: str) -> TelemetryFlowBuilder
```

##### with_collector_id_from_env()

Load collector ID from environment.

```python
def with_collector_id_from_env(self) -> TelemetryFlowBuilder
```

Uses: `TELEMETRYFLOW_COLLECTOR_ID`

##### with_custom_attribute()

Add custom resource attribute.

```python
def with_custom_attribute(self, key: str, value: str) -> TelemetryFlowBuilder
```

##### with_custom_attributes()

Add multiple custom attributes.

```python
def with_custom_attributes(self, attributes: dict[str, str]) -> TelemetryFlowBuilder
```

##### with_compression()

Enable/disable compression.

```python
def with_compression(self, enabled: bool = True) -> TelemetryFlowBuilder
```

##### with_retry()

Configure retry settings.

```python
def with_retry(
    self,
    enabled: bool = True,
    max_retries: int = 3,
    backoff: timedelta | None = None,
) -> TelemetryFlowBuilder
```

##### with_batch_settings()

Configure batch export settings.

```python
def with_batch_settings(
    self,
    timeout: timedelta | None = None,
    max_size: int | None = None,
) -> TelemetryFlowBuilder
```

##### with_rate_limit()

Set rate limit.

```python
def with_rate_limit(self, rate_limit: int) -> TelemetryFlowBuilder
```

#### Auto Configuration

##### with_auto_configuration()

Load all configuration from environment variables.

```python
def with_auto_configuration(self) -> TelemetryFlowBuilder
```

Equivalent to calling all `*_from_env()` methods.

#### Build Methods

##### build()

Build the TelemetryFlow client.

```python
def build(self) -> TelemetryFlowClient
```

**Raises:**
- `BuilderError`: If configuration is invalid

##### must_build()

Build client (alias for build()).

```python
def must_build(self) -> TelemetryFlowClient
```

---

## Domain API

### Credentials

Immutable value object for API credentials.

```python
from telemetryflow.domain.credentials import Credentials
```

#### Constructor

```python
Credentials(key_id: str, key_secret: str)
```

**Raises:**
- `CredentialsError`: If validation fails

#### Class Method

##### create()

Factory method to create credentials.

```python
@classmethod
def create(cls, key_id: str, key_secret: str) -> Credentials
```

#### Methods

##### authorization_header()

Generate Authorization header value.

```python
def authorization_header(self) -> str
```

**Returns:** `"Bearer {key_id}:{key_secret}"`

##### auth_headers()

Generate all authentication headers.

```python
def auth_headers(self) -> dict[str, str]
```

**Returns:** Dictionary with Authorization, X-TelemetryFlow-Key-ID, X-TelemetryFlow-Key-Secret

##### equals()

Check equality with another Credentials.

```python
def equals(self, other: Credentials | None) -> bool
```

### TelemetryConfig

Configuration aggregate root.

```python
from telemetryflow.domain.config import TelemetryConfig, Protocol, SignalType
```

#### Constructor

```python
TelemetryConfig(
    credentials: Credentials,
    endpoint: str,
    service_name: str,
    protocol: Protocol = Protocol.GRPC,
    # ... many more options
)
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for full configuration options.

### Protocol

OTLP protocol enumeration.

```python
class Protocol(str, Enum):
    GRPC = "grpc"
    HTTP = "http"
```

### SignalType

Telemetry signal enumeration.

```python
class SignalType(str, Enum):
    METRICS = "metrics"
    LOGS = "logs"
    TRACES = "traces"
```

---

## Commands

### SeverityLevel

Log severity levels.

```python
from telemetryflow.application.commands import SeverityLevel

class SeverityLevel(str, Enum):
    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"
```

### SpanKind

Span kind for traces.

```python
from telemetryflow.application.commands import SpanKind

class SpanKind(str, Enum):
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"
```

| Kind | Description |
|------|-------------|
| `INTERNAL` | Default, internal operations |
| `SERVER` | Server-side request handling |
| `CLIENT` | Client-side outgoing requests |
| `PRODUCER` | Message queue producer |
| `CONSUMER` | Message queue consumer |

---

## Middleware

### FlaskTelemetryMiddleware

Flask middleware for automatic request instrumentation.

```python
from telemetryflow.middleware import FlaskTelemetryMiddleware

middleware = FlaskTelemetryMiddleware(
    client,
    app=None,  # Optional, can call init_app later
    record_request_duration=True,
    record_request_count=True,
    record_error_count=True,
    excluded_paths=["/health", "/metrics"],
)
middleware.init_app(app)
```

### FastAPITelemetryMiddleware

FastAPI/Starlette middleware for automatic request instrumentation.

```python
from telemetryflow.middleware import FastAPITelemetryMiddleware

app.add_middleware(
    FastAPITelemetryMiddleware,
    client=client,
    excluded_paths=["/health"],
)
```

---

## Exceptions

### TelemetryFlowError

Base exception for SDK errors.

```python
from telemetryflow.client import TelemetryFlowError
```

### NotInitializedError

Raised when using uninitialized client.

```python
from telemetryflow.client import NotInitializedError
```

### ConfigError

Raised for configuration validation errors.

```python
from telemetryflow.domain.config import ConfigError
```

### CredentialsError

Raised for credential validation errors.

```python
from telemetryflow.domain.credentials import CredentialsError
```

### BuilderError

Raised for builder configuration errors.

```python
from telemetryflow.builder import BuilderError
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEMETRYFLOW_API_KEY_ID` | Yes | - | API key ID (tfk_*) |
| `TELEMETRYFLOW_API_KEY_SECRET` | Yes | - | API key secret (tfs_*) |
| `TELEMETRYFLOW_ENDPOINT` | No | api.telemetryflow.id:4317 | Collector endpoint |
| `TELEMETRYFLOW_SERVICE_NAME` | Yes | - | Service name |
| `TELEMETRYFLOW_SERVICE_VERSION` | No | 1.0.0 | Service version |
| `TELEMETRYFLOW_SERVICE_NAMESPACE` | No | telemetryflow | Service namespace |
| `TELEMETRYFLOW_ENVIRONMENT` | No | production | Environment |
| `TELEMETRYFLOW_COLLECTOR_ID` | No | - | Collector ID |
| `ENV` | No | - | Fallback for environment |
| `ENVIRONMENT` | No | - | Fallback for environment |
