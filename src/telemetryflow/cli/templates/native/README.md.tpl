# TelemetryFlow Integration

This directory contains the TelemetryFlow SDK integration for **${project_name}**.

## Overview

TelemetryFlow provides unified observability with:
- **Metrics**: Counters, gauges, histograms
- **Logs**: Structured logging with context
- **Traces**: Distributed tracing with spans

## Quick Start

1. Set up environment variables:
   ```bash
   source .env.telemetryflow
   ```

2. Initialize in your application:
   ```python
   from telemetry import init, get_client

   # Initialize once at startup
   init()

   # Get client anywhere in your code
   client = get_client()
   ```

3. Use telemetry features:
   ```python
   # Metrics
   client.increment_counter("requests.total")
   client.record_histogram("request.duration", 0.125, unit="s")

   # Logs
   client.log_info("User logged in", {"user_id": "123"})

   # Traces
   with client.span("process_order", SpanKind.SERVER) as span_id:
       # Your code here
       client.add_span_event(span_id, "order_validated")
   ```

## Module Structure

```
telemetry/
    __init__.py     # Main module with init/shutdown
    metrics.py      # Metric helpers
    logs.py         # Logging helpers
    traces.py       # Tracing helpers
```

## Configuration

Configure via environment variables (see `.env.telemetryflow`):

| Variable | Description | Default |
|----------|-------------|---------|
| TELEMETRYFLOW_API_KEY_ID | API Key ID | Required |
| TELEMETRYFLOW_API_KEY_SECRET | API Key Secret | Required |
| TELEMETRYFLOW_SERVICE_NAME | Service name | Required |
| TELEMETRYFLOW_ENDPOINT | OTLP endpoint | api.telemetryflow.id:4317 |
| TELEMETRYFLOW_ENVIRONMENT | Environment | production |

## Documentation

- [TelemetryFlow Documentation](https://docs.telemetryflow.id)
- [Python SDK Reference](https://docs.telemetryflow.id/sdk/python)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
