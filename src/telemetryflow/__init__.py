"""TelemetryFlow Python SDK - OpenTelemetry-based observability SDK.

TelemetryFlow Python SDK - Community Enterprise Observability Platform
Copyright (c) 2024-2026 Telemetri Data Indonesia. All rights reserved.
Open Source Software built by Telemetri Data Indonesia.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from typing import Any

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
    # Convenience functions
    "new_client",
    "new_from_env",
    "new_simple",
    "auto_instrument",
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


def auto_instrument(
    client: TelemetryFlowClient | None = None,
    **kwargs: Any,
) -> dict[str, bool]:
    """Auto-instrument all available libraries.

    This function automatically instruments all supported libraries that are
    installed in the environment. It's the easiest way to enable observability
    for your application.

    Args:
        client: Optional TelemetryFlowClient to use for instrumentation
        **kwargs: Additional arguments passed to setup_auto_instrumentation

    Returns:
        Dictionary mapping instrumentation names to success status

    Example:
        >>> from telemetryflow import TelemetryFlowBuilder, auto_instrument
        >>> client = TelemetryFlowBuilder().with_auto_configuration().build()
        >>> client.initialize()
        >>> results = auto_instrument(client)
        >>> print(f"Instrumented: {[k for k, v in results.items() if v]}")
    """
    from telemetryflow.instrumentation.integration import setup_auto_instrumentation

    return setup_auto_instrumentation(client=client, **kwargs)
