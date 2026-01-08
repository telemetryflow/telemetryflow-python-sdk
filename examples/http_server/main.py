"""HTTP Server with TelemetryFlow instrumentation example.

This example demonstrates how to instrument a simple HTTP server with
the TelemetryFlow SDK for automatic request tracing and metrics.

Usage:
    export TELEMETRYFLOW_API_KEY_ID=tfk_your_key_id
    export TELEMETRYFLOW_API_KEY_SECRET=tfs_your_key_secret
    export TELEMETRYFLOW_SERVICE_NAME=http-server-example
    python main.py

Then make requests to:
    curl http://localhost:8080/
    curl http://localhost:8080/api/users
    curl http://localhost:8080/api/orders
"""

import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from telemetryflow import TelemetryFlowBuilder
from telemetryflow.application.commands import SpanKind
from telemetryflow.client import TelemetryFlowClient

# Global client instance
client: TelemetryFlowClient | None = None


class InstrumentedHandler(BaseHTTPRequestHandler):
    """HTTP handler with automatic telemetry instrumentation."""

    def _get_headers(self) -> dict[str, str]:
        """Extract headers as a dictionary."""
        return {k.lower(): v for k, v in self.headers.items()}

    def _send_json_response(self, data: dict[str, Any], status: int = 200) -> None:
        """Send a JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _instrument_request(self, method: str) -> tuple[str, float]:
        """Start instrumentation for a request."""
        assert client is not None

        span_id = client.start_span(
            f"HTTP {method} {self.path}",
            SpanKind.SERVER,
            {
                "http.method": method,
                "http.url": self.path,
                "http.user_agent": self.headers.get("User-Agent", ""),
                "http.host": self.headers.get("Host", ""),
            },
        )

        client.increment_counter(
            "http.requests.total",
            attributes={"method": method, "path": self.path},
        )

        return span_id, time.time()

    def _finish_request(
        self,
        span_id: str,
        start_time: float,
        method: str,
        status_code: int,
        error: Exception | None = None,
    ) -> None:
        """Finish instrumentation for a request."""
        assert client is not None

        duration = time.time() - start_time

        # Record duration histogram
        client.record_histogram(
            "http.request.duration",
            duration,
            unit="s",
            attributes={
                "method": method,
                "path": self.path,
                "status_code": status_code,
            },
        )

        # Record errors
        if status_code >= 400:
            client.increment_counter(
                "http.errors.total",
                attributes={
                    "method": method,
                    "path": self.path,
                    "status_code": status_code,
                },
            )

        # Add response event and end span
        client.add_span_event(
            span_id,
            "response_sent",
            {"http.status_code": status_code, "duration_ms": duration * 1000},
        )
        client.end_span(span_id, error)

    def do_GET(self) -> None:  # noqa: N802
        """Handle GET requests."""
        assert client is not None

        span_id, start_time = self._instrument_request("GET")
        status_code = 200
        error: Exception | None = None

        try:
            if self.path == "/":
                self._send_json_response({"message": "Welcome to TelemetryFlow HTTP Server!"})
            elif self.path == "/api/users":
                self._handle_users(span_id)
            elif self.path == "/api/orders":
                self._handle_orders(span_id)
            elif self.path == "/health":
                self._send_json_response({"status": "healthy"})
            elif self.path == "/status":
                self._send_json_response(client.get_status())
            elif self.path == "/error":
                # Simulate an error
                status_code = 500
                error = ValueError("Simulated error")
                self._send_json_response({"error": "Internal server error"}, 500)
                client.log_error("Simulated error occurred", {"path": self.path})
            else:
                status_code = 404
                self._send_json_response({"error": "Not found"}, 404)

        except Exception as e:
            status_code = 500
            error = e
            self._send_json_response({"error": str(e)}, 500)
            client.log_error(f"Request failed: {e}", {"path": self.path})

        finally:
            self._finish_request(span_id, start_time, "GET", status_code, error)

    def _handle_users(self, parent_span_id: str) -> None:
        """Handle /api/users endpoint with nested spans."""
        assert client is not None

        # Database query span
        with client.span("database.query.users", SpanKind.CLIENT) as db_span:
            # Simulate database query
            time.sleep(0.05)
            client.add_span_event(db_span, "query_executed", {"table": "users"})

            users = [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
            ]

        client.add_span_event(parent_span_id, "users_fetched", {"count": len(users)})
        self._send_json_response({"users": users})

    def _handle_orders(self, parent_span_id: str) -> None:
        """Handle /api/orders endpoint with nested spans."""
        assert client is not None

        # Cache lookup span
        with client.span("cache.lookup.orders", SpanKind.CLIENT) as cache_span:
            time.sleep(0.01)
            cache_hit = True
            client.add_span_event(cache_span, "cache_checked", {"hit": cache_hit})

        if not cache_hit:
            # Database query span (only if cache miss)
            with client.span("database.query.orders", SpanKind.CLIENT) as db_span:
                time.sleep(0.08)
                client.add_span_event(db_span, "query_executed", {"table": "orders"})

        orders = [
            {"id": 101, "user_id": 1, "total": 99.99, "status": "shipped"},
            {"id": 102, "user_id": 2, "total": 149.99, "status": "pending"},
        ]

        client.add_span_event(
            parent_span_id,
            "orders_fetched",
            {"count": len(orders), "cached": cache_hit},
        )
        self._send_json_response({"orders": orders})

    def log_message(self, format: str, *args: Any) -> None:
        """Override to suppress default logging."""
        pass


def main() -> None:
    """Start the HTTP server with telemetry."""
    global client

    # Initialize TelemetryFlow client
    client = TelemetryFlowBuilder().with_auto_configuration().build()
    client.initialize()

    print("TelemetryFlow SDK initialized!")
    print(f"Service: {client.config.service_name}")
    print(f"Endpoint: {client.config.endpoint}")

    # Log server start
    client.log_info("HTTP server starting", {"port": 8080})

    # Start HTTP server
    server_address = ("", 8080)
    httpd = HTTPServer(server_address, InstrumentedHandler)

    print("\nServer running on http://localhost:8080")
    print("\nAvailable endpoints:")
    print("  GET /           - Welcome message")
    print("  GET /api/users  - List users (with DB span)")
    print("  GET /api/orders - List orders (with cache span)")
    print("  GET /health     - Health check")
    print("  GET /status     - SDK status")
    print("  GET /error      - Simulate error")
    print("\nPress Ctrl+C to stop")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        client.log_info("HTTP server stopping")
        httpd.shutdown()
        client.flush()
        client.shutdown()
        print("Server stopped.")


if __name__ == "__main__":
    main()
