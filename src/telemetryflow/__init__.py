"""
TelemetryFlow Python SDK - OpenTelemetry-based observability SDK.

This SDK provides a simple and intuitive interface for instrumenting your
Python applications with metrics, logs, and traces using OpenTelemetry.
"""

from telemetryflow.builder import TelemetryFlowBuilder
from telemetryflow.client import TelemetryFlowClient
from telemetryflow.domain.config import Protocol, SignalType, TelemetryConfig
from telemetryflow.domain.credentials import Credentials
from telemetryflow.version import __version__

__all__ = [
    # Main classes
    "TelemetryFlowClient",
    "TelemetryFlowBuilder",
    # Domain
    "TelemetryConfig",
    "Credentials",
    "Protocol",
    "SignalType",
    # Version
    "__version__",
]

# Convenience constructors
def new_client(config: TelemetryConfig) -> TelemetryFlowClient:
    """Create a new TelemetryFlow client with the given configuration."""
    return TelemetryFlowClient(config)


def new_from_env() -> TelemetryFlowClient:
    """Create a new TelemetryFlow client from environment variables."""
    return TelemetryFlowBuilder().with_auto_configuration().build()


def new_simple(
    api_key_id: str,
    api_key_secret: str,
    endpoint: str,
    service_name: str,
) -> TelemetryFlowClient:
    """Create a new TelemetryFlow client with minimal configuration."""
    return (
        TelemetryFlowBuilder()
        .with_api_key(api_key_id, api_key_secret)
        .with_endpoint(endpoint)
        .with_service(service_name)
        .build()
    )
