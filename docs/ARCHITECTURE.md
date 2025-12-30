# Architecture Guide

This document provides a comprehensive overview of the TelemetryFlow Python SDK architecture, including design patterns, layer responsibilities, and data flows.

## Table of Contents

- [Overview](#overview)
- [Design Principles](#design-principles)
- [DDD Architecture](#ddd-architecture)
- [Layer Details](#layer-details)
- [CQRS Pattern](#cqrs-pattern)
- [Data Flow](#data-flow)
- [Error Handling](#error-handling)
- [Thread Safety](#thread-safety)
- [Extension Points](#extension-points)

## Overview

The TelemetryFlow Python SDK is built using **Domain-Driven Design (DDD)** principles with the **CQRS (Command Query Responsibility Segregation)** pattern. This architecture ensures clean separation of concerns, testability, and maintainability.

```mermaid
graph TB
    subgraph "Public API"
        A[TelemetryFlowClient]
        B[TelemetryFlowBuilder]
    end

    subgraph "Application Layer"
        C[Commands]
        D[Queries]
        E[CommandBus]
        F[QueryBus]
    end

    subgraph "Domain Layer"
        G[TelemetryConfig]
        H[Credentials]
        I[Protocol]
        J[SignalType]
    end

    subgraph "Infrastructure Layer"
        K[TelemetryCommandHandler]
        L[OTLPExporterFactory]
        M[OpenTelemetry SDK]
    end

    subgraph "External"
        N[TelemetryFlow Backend]
    end

    A --> C
    A --> D
    B --> G
    G --> H
    G --> I
    G --> J
    C --> E
    D --> F
    E --> K
    K --> L
    L --> M
    M --> N

    style A fill:#4CAF50
    style B fill:#4CAF50
    style G fill:#2196F3
    style H fill:#2196F3
    style K fill:#FF9800
    style M fill:#9C27B0
```

## Design Principles

### 1. Domain-Driven Design (DDD)

The SDK follows DDD tactical patterns:

| Pattern | Implementation | Purpose |
|---------|---------------|---------|
| **Aggregate Root** | `TelemetryConfig` | Encapsulates all configuration |
| **Value Object** | `Credentials` | Immutable API key pair |
| **Entity** | N/A | Not needed for SDK use case |
| **Repository** | N/A | Telemetry is write-only |

### 2. CQRS Pattern

Commands and queries are strictly separated:

```mermaid
graph LR
    subgraph "Write Path (Commands)"
        A1[RecordMetricCommand]
        A2[EmitLogCommand]
        A3[StartSpanCommand]
    end

    subgraph "Read Path (Queries)"
        B1[GetHealthQuery]
        B2[GetSDKStatusQuery]
    end

    subgraph "Handlers"
        C[TelemetryCommandHandler]
        D[QueryHandler]
    end

    A1 --> C
    A2 --> C
    A3 --> C
    B1 --> D
    B2 --> D
```

### 3. Builder Pattern

Fluent configuration API for ease of use:

```python
client = (
    TelemetryFlowBuilder()
    .with_api_key("tfk_...", "tfs_...")
    .with_endpoint("api.telemetryflow.id:4317")
    .with_service("my-service", "1.0.0")
    .with_grpc()
    .with_signals(metrics=True, logs=True, traces=True)
    .build()
)
```

### 4. Dependency Inversion

Higher-level modules don't depend on lower-level modules:

```mermaid
graph TB
    subgraph "High Level"
        A[Client]
    end

    subgraph "Abstractions"
        B[CommandHandler Protocol]
        C[QueryHandler Protocol]
    end

    subgraph "Low Level"
        D[TelemetryCommandHandler]
        E[OTLPExporterFactory]
    end

    A --> B
    A --> C
    D -.implements.-> B
    E -.used by.-> D
```

## DDD Architecture

### Bounded Contexts

```mermaid
graph TB
    subgraph "Telemetry Context"
        subgraph "Domain"
            A[TelemetryConfig]
            B[Credentials]
            C[Protocol]
            D[SignalType]
        end

        subgraph "Application"
            E[Commands]
            F[Queries]
        end

        subgraph "Infrastructure"
            G[Exporters]
            H[Handlers]
        end
    end

    subgraph "Middleware Context"
        I[FlaskMiddleware]
        J[FastAPIMiddleware]
    end

    subgraph "CLI Context"
        K[Generator]
    end
```

### Layer Dependencies

```mermaid
graph TB
    A[Interface Layer<br/>client.py, builder.py] --> B[Application Layer<br/>commands.py, queries.py]
    A --> C[Domain Layer<br/>config.py, credentials.py]
    B --> C
    B --> D[Infrastructure Layer<br/>handlers.py, exporters.py]
    D --> C
    D --> E[External<br/>OpenTelemetry SDK]

    style A fill:#4CAF50,color:#fff
    style B fill:#2196F3,color:#fff
    style C fill:#FF9800,color:#fff
    style D fill:#9C27B0,color:#fff
    style E fill:#607D8B,color:#fff
```

## Layer Details

### Domain Layer

**Location:** `src/telemetryflow/domain/`

The domain layer contains the core business logic and is completely independent of external frameworks.

#### Credentials (Value Object)

```python
@dataclass(frozen=True)
class Credentials:
    """Immutable API key credentials."""
    key_id: str      # Must start with 'tfk_'
    key_secret: str  # Must start with 'tfs_'

    def authorization_header(self) -> str:
        """Generate Bearer token."""
        return f"Bearer {self.key_id}:{self.key_secret}"
```

#### TelemetryConfig (Aggregate Root)

```mermaid
classDiagram
    class TelemetryConfig {
        +Credentials credentials
        +str endpoint
        +str service_name
        +Protocol protocol
        +bool enable_metrics
        +bool enable_logs
        +bool enable_traces
        +with_grpc() TelemetryConfig
        +with_http() TelemetryConfig
        +with_signals() TelemetryConfig
        +get_auth_headers() dict
    }

    class Credentials {
        +str key_id
        +str key_secret
        +authorization_header() str
        +auth_headers() dict
    }

    class Protocol {
        <<enumeration>>
        GRPC
        HTTP
    }

    class SignalType {
        <<enumeration>>
        METRICS
        LOGS
        TRACES
    }

    TelemetryConfig --> Credentials
    TelemetryConfig --> Protocol
    TelemetryConfig --> SignalType
```

### Application Layer

**Location:** `src/telemetryflow/application/`

The application layer implements the CQRS pattern with commands and queries.

#### Commands

```mermaid
classDiagram
    class Command {
        <<abstract>>
        +datetime timestamp
    }

    class InitializeSDKCommand {
        +TelemetryConfig config
    }

    class ShutdownSDKCommand {
        +float timeout_seconds
    }

    class RecordMetricCommand {
        +str name
        +float value
        +str unit
        +dict attributes
    }

    class RecordCounterCommand {
        +str name
        +int value
        +dict attributes
    }

    class RecordGaugeCommand {
        +str name
        +float value
        +dict attributes
    }

    class RecordHistogramCommand {
        +str name
        +float value
        +str unit
        +dict attributes
    }

    class EmitLogCommand {
        +str message
        +SeverityLevel severity
        +dict attributes
    }

    class StartSpanCommand {
        +str name
        +SpanKind kind
        +dict attributes
    }

    class EndSpanCommand {
        +str span_id
        +Exception error
    }

    class AddSpanEventCommand {
        +str span_id
        +str name
        +dict attributes
    }

    Command <|-- InitializeSDKCommand
    Command <|-- ShutdownSDKCommand
    Command <|-- RecordMetricCommand
    Command <|-- RecordCounterCommand
    Command <|-- RecordGaugeCommand
    Command <|-- RecordHistogramCommand
    Command <|-- EmitLogCommand
    Command <|-- StartSpanCommand
    Command <|-- EndSpanCommand
    Command <|-- AddSpanEventCommand
```

#### Command Bus

```python
class CommandBus:
    """Dispatches commands to registered handlers."""

    def register(self, command_type: type[Command], handler: CommandHandler) -> None:
        """Register a handler for a command type."""

    def dispatch(self, command: Command) -> Any:
        """Dispatch command to handler."""
```

### Infrastructure Layer

**Location:** `src/telemetryflow/infrastructure/`

The infrastructure layer handles external integrations and OpenTelemetry SDK interaction.

#### OTLP Exporter Factory

```mermaid
graph TB
    A[OTLPExporterFactory] --> B{Protocol?}
    B -->|gRPC| C[OTLPSpanExporter<br/>gRPC]
    B -->|HTTP| D[HTTPSpanExporter]
    B -->|gRPC| E[OTLPMetricExporter<br/>gRPC]
    B -->|HTTP| F[HTTPMetricExporter]

    C --> G[TelemetryFlow Backend]
    D --> G
    E --> G
    F --> G
```

#### Command Handler

```mermaid
flowchart TB
    A[TelemetryCommandHandler] --> B{Command Type}

    B -->|InitializeSDKCommand| C[Initialize Providers]
    B -->|ShutdownSDKCommand| D[Shutdown Providers]
    B -->|FlushTelemetryCommand| E[Force Flush]

    B -->|RecordCounterCommand| F[Record Counter]
    B -->|RecordGaugeCommand| G[Record Gauge]
    B -->|RecordHistogramCommand| H[Record Histogram]

    B -->|EmitLogCommand| I[Emit Log]

    B -->|StartSpanCommand| J[Start Span]
    B -->|EndSpanCommand| K[End Span]
    B -->|AddSpanEventCommand| L[Add Event]

    C --> M[TracerProvider]
    C --> N[MeterProvider]

    F --> N
    G --> N
    H --> N

    J --> M
    K --> M
    L --> M
```

### Interface Layer

**Location:** `src/telemetryflow/client.py`, `src/telemetryflow/builder.py`

The interface layer provides the public API for SDK users.

```mermaid
classDiagram
    class TelemetryFlowClient {
        -TelemetryConfig _config
        -TelemetryCommandHandler _handler
        -bool _initialized
        +initialize()
        +shutdown()
        +flush()
        +increment_counter()
        +record_gauge()
        +record_histogram()
        +log_info()
        +log_warn()
        +log_error()
        +start_span()
        +end_span()
        +span() contextmanager
        +get_status() dict
    }

    class TelemetryFlowBuilder {
        -str _api_key_id
        -str _api_key_secret
        -str _endpoint
        -str _service_name
        +with_api_key() Builder
        +with_endpoint() Builder
        +with_service() Builder
        +with_grpc() Builder
        +with_http() Builder
        +with_auto_configuration() Builder
        +build() Client
    }

    TelemetryFlowBuilder --> TelemetryFlowClient : creates
```

## CQRS Pattern

### Command Flow (Write Path)

```mermaid
sequenceDiagram
    participant App as Application
    participant Client as TelemetryFlowClient
    participant Handler as CommandHandler
    participant OTEL as OpenTelemetry
    participant Backend as TelemetryFlow

    App->>Client: increment_counter("metric", 1)
    Client->>Client: _ensure_initialized()
    Client->>Handler: handle(RecordCounterCommand)
    Handler->>OTEL: counter.add(value, attrs)
    OTEL-->>Handler: OK

    Note over OTEL: Batch & Schedule Export

    OTEL->>Backend: OTLP Export
    Backend-->>OTEL: Ack
```

### Query Flow (Read Path)

```mermaid
sequenceDiagram
    participant App as Application
    participant Client as TelemetryFlowClient
    participant Handler as CommandHandler

    App->>Client: get_status()
    Client->>Handler: Query status
    Handler-->>Client: SDKStatusResult
    Client-->>App: status dict
```

## Data Flow

### Metrics Data Flow

```mermaid
flowchart LR
    subgraph "Application"
        A[Your Code]
    end

    subgraph "TelemetryFlow SDK"
        B[Client API]
        C[RecordMetricCommand]
        D[CommandHandler]
        E[MeterProvider]
    end

    subgraph "OpenTelemetry"
        F[MetricReader]
        G[MetricExporter]
    end

    subgraph "Backend"
        H[TelemetryFlow]
    end

    A -->|record_histogram| B
    B -->|dispatch| C
    C --> D
    D -->|meter.create_histogram| E
    E -->|periodic export| F
    F --> G
    G -->|OTLP| H
```

### Traces Data Flow

```mermaid
flowchart LR
    subgraph "Application"
        A[Your Code]
    end

    subgraph "TelemetryFlow SDK"
        B[Client API]
        C[StartSpanCommand]
        D[CommandHandler]
        E[TracerProvider]
    end

    subgraph "OpenTelemetry"
        F[SpanProcessor]
        G[SpanExporter]
    end

    subgraph "Backend"
        H[TelemetryFlow]
    end

    A -->|span context| B
    B -->|dispatch| C
    C --> D
    D -->|tracer.start_span| E
    E -->|on_end| F
    F -->|batch export| G
    G -->|OTLP| H
```

### Initialization Flow

```mermaid
sequenceDiagram
    participant App as Application
    participant Builder as TelemetryFlowBuilder
    participant Client as TelemetryFlowClient
    participant Handler as CommandHandler
    participant Factory as ExporterFactory
    participant OTEL as OpenTelemetry

    App->>Builder: with_auto_configuration()
    Builder->>Builder: Load env vars
    App->>Builder: build()
    Builder->>Client: new TelemetryFlowClient(config)

    App->>Client: initialize()
    Client->>Handler: handle(InitializeSDKCommand)
    Handler->>Factory: create_trace_exporter()
    Factory-->>Handler: SpanExporter
    Handler->>Factory: create_metric_exporter()
    Factory-->>Handler: MetricExporter
    Handler->>OTEL: Set up TracerProvider
    Handler->>OTEL: Set up MeterProvider
    Handler-->>Client: Initialized
    Client-->>App: Ready
```

### Shutdown Flow

```mermaid
sequenceDiagram
    participant App as Application
    participant Client as TelemetryFlowClient
    participant Handler as CommandHandler
    participant OTEL as OpenTelemetry
    participant Backend as TelemetryFlow

    App->>Client: shutdown()
    Client->>Handler: handle(ShutdownSDKCommand)

    Handler->>OTEL: TracerProvider.force_flush()
    OTEL->>Backend: Export pending spans
    Backend-->>OTEL: Ack

    Handler->>OTEL: MeterProvider.force_flush()
    OTEL->>Backend: Export pending metrics
    Backend-->>OTEL: Ack

    Handler->>OTEL: TracerProvider.shutdown()
    Handler->>OTEL: MeterProvider.shutdown()

    Handler-->>Client: Shutdown complete
    Client-->>App: Done
```

## Error Handling

### Error Hierarchy

```mermaid
graph TB
    A[Exception] --> B[TelemetryFlowError]
    B --> C[NotInitializedError]
    B --> D[ConfigError]
    B --> E[CredentialsError]
    B --> F[BuilderError]
```

### Error Handling Flow

```mermaid
flowchart TB
    A[API Call] --> B{Initialized?}
    B -->|No| C[Raise NotInitializedError]
    B -->|Yes| D[Create Command]
    D --> E[Dispatch to Handler]
    E --> F{Handler Error?}
    F -->|Yes| G[Log Error]
    G --> H[Propagate Exception]
    F -->|No| I[Success]
```

### Validation Points

| Layer | Validation | Error Type |
|-------|------------|------------|
| Domain | Credentials format | `CredentialsError` |
| Domain | Config completeness | `ConfigError` |
| Builder | Required fields | `BuilderError` |
| Client | Initialization state | `NotInitializedError` |
| Infrastructure | Export errors | Logged, may retry |

## Thread Safety

The SDK is designed to be thread-safe:

```mermaid
graph TB
    subgraph "Thread-Safe Components"
        A[TelemetryFlowClient]
        B[TelemetryCommandHandler]
        C[Active Spans Dict]
        D[Instruments Cache]
    end

    subgraph "Synchronization"
        E[threading.RLock]
        F[threading.Lock]
    end

    A --> E
    B --> E
    C --> F
    D --> F
```

### Thread Safety Mechanisms

| Component | Mechanism | Protected Operations |
|-----------|-----------|---------------------|
| Client | `RLock` | initialize, shutdown |
| Handler | `RLock` | initialization state |
| Active Spans | `Lock` | span tracking dict |
| Instruments | `Lock` | metric instruments cache |

## Extension Points

### Custom Middleware

```mermaid
flowchart TB
    A[TelemetryMiddleware] --> B[FlaskTelemetryMiddleware]
    A --> C[FastAPITelemetryMiddleware]
    A --> D[Your Custom Middleware]

    B --> E[Flask App]
    C --> F[FastAPI App]
    D --> G[Other Framework]
```

### Implementing Custom Middleware

```python
from telemetryflow.middleware.base import TelemetryMiddleware

class CustomMiddleware(TelemetryMiddleware):
    def __call__(self, request):
        span_id, start_time = self.start_request(
            method=request.method,
            path=request.path,
        )

        try:
            response = self.handle_request(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise
        finally:
            self.end_request(
                span_id, start_time,
                request.method, request.path,
                status_code
            )

        return response
```

## Performance Considerations

### Batching

```mermaid
mindmap
  root((Performance))
    Batching
      Span batching
      Metric aggregation
      Configurable intervals
    Async Export
      Background threads
      Non-blocking API
    Resource Pooling
      Connection reuse
      gRPC channels
    Memory
      Bounded queues
      Instrument caching
```

### Configuration Tuning

| Parameter | Default | Tuning Guide |
|-----------|---------|--------------|
| `batch_timeout` | 10s | Lower for real-time, higher for efficiency |
| `batch_max_size` | 512 | Higher for throughput, lower for latency |
| `timeout` | 30s | Based on network conditions |
| `compression` | true | Disable for low CPU environments |

## Best Practices

### 1. Initialize Once

```python
# Good: Single initialization
client = TelemetryFlowBuilder().with_auto_configuration().build()
client.initialize()

# Bad: Multiple initializations
for request in requests:
    client = TelemetryFlowBuilder()...  # Don't do this!
```

### 2. Use Context Managers for Spans

```python
# Good: Automatic cleanup
with client.span("operation") as span_id:
    # work...

# Avoid: Manual cleanup (error-prone)
span_id = client.start_span("operation")
# ... if exception occurs, span may not be ended
client.end_span(span_id)
```

### 3. Graceful Shutdown

```python
# Good: Ensure shutdown
try:
    client.initialize()
    # application logic
finally:
    client.shutdown()

# Better: Use context manager
with TelemetryFlowBuilder()...build() as client:
    # application logic
```

### 4. Meaningful Attributes

```python
# Good: Structured attributes
client.increment_counter(
    "http.requests",
    attributes={
        "http.method": "POST",
        "http.route": "/api/users",
        "http.status_code": 200,
    }
)

# Avoid: Unstructured or high-cardinality
client.increment_counter(
    "request",
    attributes={"url": request.full_url}  # High cardinality!
)
```

## Summary

The TelemetryFlow Python SDK architecture provides:

- **Clean Separation**: DDD layers isolate concerns
- **Flexibility**: CQRS allows independent scaling
- **Testability**: Each layer can be tested in isolation
- **Extensibility**: Easy to add new commands, exporters, or middleware
- **Thread Safety**: Safe for concurrent use
- **Performance**: Async export with batching
