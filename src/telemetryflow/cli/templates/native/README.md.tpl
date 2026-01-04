# TelemetryFlow Integration

This directory contains the TelemetryFlow SDK integration for **${project_name}**.

Compatible with TFO-Collector v${tfo_collector_version} (OCB-native)
SDK Version: ${sdk_version}

## Overview

TelemetryFlow provides unified observability with:
- **Metrics**: Counters, gauges, histograms
- **Logs**: Structured logging with context
- **Traces**: Distributed tracing with spans
- **TFO v2 API**: Enhanced endpoints with authentication

## Quick Start

1. Set up environment variables:
   ```bash
   source .env.telemetryflow
   ```

2. Initialize in your application:
   ```python
   from telemetry import init, init_v2_only, get_client

   # Initialize with TFO v2 API (default)
   init()

   # Or for production with v2-only mode
   init_v2_only()

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

## TFO v2 API Configuration

The SDK supports TFO v2 API endpoints aligned with TFO-Collector v${tfo_collector_version}:

| Endpoint | v1 (Community) | v2 (Authenticated) |
|----------|----------------|---------------------|
| Traces | `/v1/traces` | `/v2/traces` |
| Metrics | `/v1/metrics` | `/v2/metrics` |
| Logs | `/v1/logs` | `/v2/logs` |

### Environment Variables

Configure via environment variables (see `.env.telemetryflow`):

| Variable | Description | Default |
|----------|-------------|---------|
| TELEMETRYFLOW_API_KEY_ID | API Key ID (tfk_xxx) | Required |
| TELEMETRYFLOW_API_KEY_SECRET | API Key Secret (tfs_xxx) | Required |
| TELEMETRYFLOW_SERVICE_NAME | Service name | Required |
| TELEMETRYFLOW_ENDPOINT | OTLP endpoint | localhost:4317 |
| TELEMETRYFLOW_PROTOCOL | Protocol (grpc/http) | grpc |
| TELEMETRYFLOW_ENVIRONMENT | Environment | production |
| TELEMETRYFLOW_USE_V2_API | Enable v2 API | true |
| TELEMETRYFLOW_V2_ONLY | v2-only mode | false |
| TELEMETRYFLOW_COLLECTOR_NAME | Collector identity name | TelemetryFlow Python SDK |
| TELEMETRYFLOW_DATACENTER | Datacenter/region | default |

## Documentation

- [TelemetryFlow Documentation](https://docs.telemetryflow.id)
- [Python SDK Reference](https://docs.telemetryflow.id/sdk/python)
- [TFO v2 API Reference](https://docs.telemetryflow.id/api/v2)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
