"""Basic TelemetryFlow SDK usage example.

This example demonstrates the core functionality of the TelemetryFlow SDK:
- Client initialization and shutdown
- Recording metrics (counters, gauges, histograms)
- Emitting logs (info, warn, error)
- Creating trace spans with events

Usage:
    export TELEMETRYFLOW_API_KEY_ID=tfk_your_key_id
    export TELEMETRYFLOW_API_KEY_SECRET=tfs_your_key_secret
    export TELEMETRYFLOW_SERVICE_NAME=basic-example
    python main.py
"""

import time

from telemetryflow import TelemetryFlowBuilder
from telemetryflow.application.commands import SpanKind


def main() -> None:
    """Main function demonstrating SDK usage."""
    # Create the client using the builder pattern
    # with_auto_configuration() loads settings from environment variables
    client = TelemetryFlowBuilder().with_auto_configuration().build()

    # Initialize the SDK - this connects to the TelemetryFlow backend
    client.initialize()
    print("TelemetryFlow SDK initialized!")
    print(f"Client status: {client.get_status()}")

    try:
        # ============================================
        # METRICS EXAMPLES
        # ============================================
        print("\n--- Recording Metrics ---")

        # Increment a counter - great for tracking events
        client.increment_counter(
            "app.requests.total",
            attributes={"endpoint": "/api/users", "method": "GET"},
        )
        print("Recorded counter: app.requests.total")

        # Record a gauge - great for current values like active connections
        client.record_gauge(
            "app.active_connections",
            42.0,
            attributes={"pool": "default"},
        )
        print("Recorded gauge: app.active_connections = 42")

        # Record a histogram - great for distributions like latencies
        client.record_histogram(
            "app.request.duration",
            0.125,
            unit="s",
            attributes={"endpoint": "/api/users"},
        )
        print("Recorded histogram: app.request.duration = 0.125s")

        # ============================================
        # LOGS EXAMPLES
        # ============================================
        print("\n--- Emitting Logs ---")

        # Info level log
        client.log_info(
            "Application started successfully",
            {"version": "1.0.0", "environment": "development"},
        )
        print("Logged: INFO - Application started")

        # Warning level log
        client.log_warn(
            "Cache miss rate is high",
            {"cache_hit_rate": 0.65, "threshold": 0.80},
        )
        print("Logged: WARN - Cache miss rate")

        # Error level log
        client.log_error(
            "Failed to connect to database",
            {"database": "users_db", "retry_count": 3},
        )
        print("Logged: ERROR - Database connection failed")

        # Debug level log
        client.log_debug(
            "Processing request",
            {"request_id": "req-123", "user_id": "user-456"},
        )
        print("Logged: DEBUG - Processing request")

        # ============================================
        # TRACES EXAMPLES
        # ============================================
        print("\n--- Creating Traces ---")

        # Manual span management
        span_id = client.start_span(
            "manual_operation",
            SpanKind.INTERNAL,
            {"operation_type": "manual"},
        )
        print(f"Started span: {span_id}")

        # Simulate some work
        time.sleep(0.1)

        # Add events to the span
        client.add_span_event(span_id, "checkpoint_1", {"progress": 50})
        client.add_span_event(span_id, "checkpoint_2", {"progress": 100})

        # End the span
        client.end_span(span_id)
        print("Ended manual span")

        # Using context manager for automatic span management (recommended)
        print("\n--- Using Context Manager for Spans ---")

        with client.span("process_request", SpanKind.SERVER) as request_span:
            print(f"Processing request (span: {request_span})")
            time.sleep(0.05)

            # Nested span for database operation
            with client.span("database_query", SpanKind.CLIENT) as db_span:
                print(f"Executing database query (span: {db_span})")
                time.sleep(0.03)
                client.add_span_event(db_span, "query_executed", {"rows_returned": 10})

            # Nested span for cache operation
            with client.span("cache_lookup", SpanKind.CLIENT) as cache_span:
                print(f"Looking up cache (span: {cache_span})")
                time.sleep(0.01)
                client.add_span_event(cache_span, "cache_hit", {"key": "user:123"})

            client.add_span_event(request_span, "processing_complete")

        print("\n--- Final Status ---")
        status = client.get_status()
        print(f"Metrics sent: {status['metrics_sent']}")
        print(f"Logs sent: {status['logs_sent']}")
        print(f"Spans sent: {status['spans_sent']}")

    except Exception as e:
        client.log_error(f"Unexpected error: {e}")
        raise

    finally:
        # Always shutdown the client to flush pending data
        print("\n--- Shutting Down ---")
        client.shutdown()
        print("TelemetryFlow SDK shut down successfully!")


if __name__ == "__main__":
    main()
