"""gRPC Server with TelemetryFlow instrumentation example.

This example demonstrates how to instrument a gRPC server with
the TelemetryFlow SDK. It requires grpcio to be installed.

Usage:
    pip install grpcio
    export TELEMETRYFLOW_API_KEY_ID=tfk_your_key_id
    export TELEMETRYFLOW_API_KEY_SECRET=tfs_your_key_secret
    export TELEMETRYFLOW_SERVICE_NAME=grpc-server-example
    python main.py
"""

import time
from concurrent import futures
from typing import Any

from telemetryflow import TelemetryFlowBuilder
from telemetryflow.application.commands import SpanKind
from telemetryflow.client import TelemetryFlowClient

try:
    import grpc
    from grpc import ServicerContext
except ImportError:
    print("grpcio is required for this example. Install it with: pip install grpcio")
    exit(1)


# Global client instance
client: TelemetryFlowClient | None = None


class TelemetryInterceptor(grpc.ServerInterceptor):
    """gRPC server interceptor for TelemetryFlow instrumentation."""

    def __init__(self, telemetry_client: TelemetryFlowClient) -> None:
        """Initialize the interceptor."""
        self._client = telemetry_client

    def intercept_service(
        self,
        continuation: Any,
        handler_call_details: grpc.HandlerCallDetails,
    ) -> Any:
        """Intercept gRPC calls for instrumentation."""
        method = handler_call_details.method

        # Start span for the call
        span_id = self._client.start_span(
            f"gRPC {method}",
            SpanKind.SERVER,
            {
                "rpc.system": "grpc",
                "rpc.method": method,
            },
        )

        # Increment call counter
        self._client.increment_counter(
            "grpc.calls.total",
            attributes={"method": method},
        )

        start_time = time.time()

        # Store span info for the handler
        handler_call_details._telemetry_span_id = span_id  # type: ignore
        handler_call_details._telemetry_start_time = start_time  # type: ignore

        try:
            return continuation(handler_call_details)
        finally:
            duration = time.time() - start_time
            self._client.record_histogram(
                "grpc.call.duration",
                duration,
                unit="s",
                attributes={"method": method},
            )
            self._client.end_span(span_id)


class GreeterServicer:
    """Example gRPC servicer with telemetry."""

    def __init__(self, telemetry_client: TelemetryFlowClient) -> None:
        """Initialize the servicer."""
        self._client = telemetry_client

    def say_hello(self, name: str, context: ServicerContext) -> str:
        """Handle SayHello RPC."""
        with self._client.span("grpc.handler.say_hello", SpanKind.INTERNAL) as span_id:
            self._client.log_info(
                f"SayHello called with name: {name}",
                {"name": name},
            )

            # Simulate some work
            time.sleep(0.05)

            response = f"Hello, {name}!"

            self._client.add_span_event(
                span_id,
                "response_prepared",
                {"response_length": len(response)},
            )

            return response

    def say_goodbye(self, name: str, context: ServicerContext) -> str:
        """Handle SayGoodbye RPC."""
        with self._client.span("grpc.handler.say_goodbye", SpanKind.INTERNAL) as span_id:
            self._client.log_info(
                f"SayGoodbye called with name: {name}",
                {"name": name},
            )

            # Simulate database lookup
            with self._client.span("database.user_lookup", SpanKind.CLIENT):
                time.sleep(0.03)

            response = f"Goodbye, {name}! See you soon!"

            self._client.add_span_event(
                span_id,
                "response_prepared",
                {"response_length": len(response)},
            )

            return response


def main() -> None:
    """Main function to run the gRPC server example."""
    global client

    # Initialize TelemetryFlow client
    client = TelemetryFlowBuilder().with_auto_configuration().build()
    client.initialize()

    print("TelemetryFlow SDK initialized!")
    print(f"Service: {client.config.service_name}")

    # Create the gRPC server with telemetry interceptor
    interceptor = TelemetryInterceptor(client)
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[interceptor],
    )

    # Create servicer
    servicer = GreeterServicer(client)

    # Since we don't have protobuf definitions, we'll simulate the server
    print("\ngRPC Server Example")
    print("=" * 50)
    print("\nThis example demonstrates gRPC instrumentation patterns.")
    print("In a real application, you would:")
    print("1. Define your proto files")
    print("2. Generate Python stubs")
    print("3. Implement your servicers")
    print("4. Add the TelemetryInterceptor to your server")
    print()

    # Simulate some gRPC calls
    print("Simulating gRPC calls...\n")

    # Simulate SayHello calls
    for name in ["Alice", "Bob", "Charlie"]:
        span_id = client.start_span(
            f"gRPC /greeter.Greeter/SayHello",
            SpanKind.SERVER,
            {"rpc.system": "grpc", "rpc.method": "/greeter.Greeter/SayHello"},
        )

        client.increment_counter(
            "grpc.calls.total",
            attributes={"method": "/greeter.Greeter/SayHello"},
        )

        start_time = time.time()

        try:
            # Simulate handler
            response = servicer.say_hello(name, None)  # type: ignore
            print(f"SayHello({name}) -> {response}")

            duration = time.time() - start_time
            client.record_histogram(
                "grpc.call.duration",
                duration,
                unit="s",
                attributes={"method": "/greeter.Greeter/SayHello"},
            )
        finally:
            client.end_span(span_id)

        time.sleep(0.1)

    # Simulate SayGoodbye calls
    for name in ["Alice", "Bob"]:
        span_id = client.start_span(
            f"gRPC /greeter.Greeter/SayGoodbye",
            SpanKind.SERVER,
            {"rpc.system": "grpc", "rpc.method": "/greeter.Greeter/SayGoodbye"},
        )

        client.increment_counter(
            "grpc.calls.total",
            attributes={"method": "/greeter.Greeter/SayGoodbye"},
        )

        start_time = time.time()

        try:
            # Simulate handler
            response = servicer.say_goodbye(name, None)  # type: ignore
            print(f"SayGoodbye({name}) -> {response}")

            duration = time.time() - start_time
            client.record_histogram(
                "grpc.call.duration",
                duration,
                unit="s",
                attributes={"method": "/greeter.Greeter/SayGoodbye"},
            )
        finally:
            client.end_span(span_id)

        time.sleep(0.1)

    # Print final status
    print("\n--- Final Status ---")
    status = client.get_status()
    print(f"Metrics sent: {status['metrics_sent']}")
    print(f"Logs sent: {status['logs_sent']}")
    print(f"Spans sent: {status['spans_sent']}")

    # Shutdown
    client.shutdown()
    print("\nTelemetryFlow SDK shut down!")


if __name__ == "__main__":
    main()
