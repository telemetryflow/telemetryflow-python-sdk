"""TelemetryFlow Integration Helpers.

This module provides easy integration between TelemetryFlow SDK and
OpenTelemetry auto-instrumentation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from telemetryflow.client import TelemetryFlowClient

from telemetryflow.instrumentation import (
    InstrumentationConfig,
    auto_instrument,
    get_available_instrumentations,
)


def setup_auto_instrumentation(
    client: TelemetryFlowClient | None = None,
    enable_flask: bool = True,
    enable_fastapi: bool = True,
    enable_sqlalchemy: bool = True,
    enable_requests: bool = True,
    enable_httpx: bool = True,
    enable_logging: bool = True,
    enable_psycopg2: bool = True,
    enable_redis: bool = True,
    excluded_urls: list[str] | None = None,
    excluded_hosts: list[str] | None = None,
) -> dict[str, bool]:
    """Set up auto-instrumentation with TelemetryFlow SDK.

    This is a convenience function that configures auto-instrumentation
    to work seamlessly with the TelemetryFlow SDK.

    Args:
        client: TelemetryFlowClient instance (optional, uses global provider if None)
        enable_flask: Enable Flask instrumentation
        enable_fastapi: Enable FastAPI instrumentation
        enable_sqlalchemy: Enable SQLAlchemy instrumentation
        enable_requests: Enable requests library instrumentation
        enable_httpx: Enable httpx library instrumentation
        enable_logging: Enable logging instrumentation
        enable_psycopg2: Enable psycopg2 instrumentation
        enable_redis: Enable redis instrumentation
        excluded_urls: URL patterns to exclude from tracing
        excluded_hosts: Hostnames to exclude from tracing

    Returns:
        Dictionary mapping instrumentation names to success status

    Example:
        >>> from telemetryflow import TelemetryFlowBuilder
        >>> from telemetryflow.instrumentation.integration import setup_auto_instrumentation
        >>>
        >>> client = TelemetryFlowBuilder().with_auto_configuration().build()
        >>> client.initialize()
        >>>
        >>> results = setup_auto_instrumentation(client)
        >>> print(f"Instrumented: {[k for k, v in results.items() if v]}")
    """
    tracer_provider = None
    meter_provider = None

    # If client is provided and initialized, get providers from it
    if client is not None and client.is_initialized():
        # The client uses global providers after initialization
        from opentelemetry import trace
        from opentelemetry.metrics import get_meter_provider

        tracer_provider = trace.get_tracer_provider()
        meter_provider = get_meter_provider()

    config = InstrumentationConfig(
        tracer_provider=tracer_provider,
        meter_provider=meter_provider,
        enable_flask=enable_flask,
        enable_fastapi=enable_fastapi,
        enable_sqlalchemy=enable_sqlalchemy,
        enable_requests=enable_requests,
        enable_httpx=enable_httpx,
        enable_logging=enable_logging,
        enable_psycopg2=enable_psycopg2,
        enable_redis=enable_redis,
        excluded_urls=excluded_urls,
        excluded_hosts=excluded_hosts,
    )

    return auto_instrument(config=config)


def get_instrumentation_status() -> dict[str, Any]:
    """Get the current instrumentation status.

    Returns:
        Dictionary with instrumentation status information
    """
    available = get_available_instrumentations()

    return {
        "available_instrumentations": available,
        "total_available": len(available),
    }


class TelemetryFlowInstrumentor:
    """A class-based instrumentor for TelemetryFlow SDK.

    This class provides a convenient way to manage auto-instrumentation
    lifecycle with context managers.

    Example:
        >>> from telemetryflow import TelemetryFlowBuilder
        >>> from telemetryflow.instrumentation.integration import TelemetryFlowInstrumentor
        >>>
        >>> client = TelemetryFlowBuilder().with_auto_configuration().build()
        >>>
        >>> with TelemetryFlowInstrumentor(client) as instrumentor:
        ...     # Your application code here
        ...     print(f"Active instrumentations: {instrumentor.active}")
    """

    def __init__(
        self,
        client: TelemetryFlowClient | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the instrumentor.

        Args:
            client: TelemetryFlowClient instance
            **kwargs: Additional arguments passed to setup_auto_instrumentation
        """
        self._client = client
        self._kwargs = kwargs
        self._results: dict[str, bool] = {}
        self._initialized = False

    def instrument(self) -> dict[str, bool]:
        """Enable auto-instrumentation.

        Returns:
            Dictionary mapping instrumentation names to success status
        """
        if self._client is not None and not self._client.is_initialized():
            self._client.initialize()

        self._results = setup_auto_instrumentation(
            client=self._client,
            **self._kwargs,
        )
        self._initialized = True
        return self._results

    def uninstrument(self) -> None:
        """Disable auto-instrumentation.

        Note: Some instrumentors may not support uninstrumentation.
        """
        if not self._initialized:
            return

        # Try to uninstrument each library
        try:
            if self._results.get("flask"):
                from opentelemetry.instrumentation.flask import FlaskInstrumentor

                FlaskInstrumentor().uninstrument()
        except Exception:
            pass

        try:
            if self._results.get("fastapi"):
                from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

                FastAPIInstrumentor().uninstrument()
        except Exception:
            pass

        try:
            if self._results.get("sqlalchemy"):
                from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

                SQLAlchemyInstrumentor().uninstrument()
        except Exception:
            pass

        try:
            if self._results.get("requests"):
                from opentelemetry.instrumentation.requests import RequestsInstrumentor

                RequestsInstrumentor().uninstrument()
        except Exception:
            pass

        try:
            if self._results.get("httpx"):
                from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

                HTTPXClientInstrumentor().uninstrument()
        except Exception:
            pass

        try:
            if self._results.get("logging"):
                from opentelemetry.instrumentation.logging import LoggingInstrumentor

                LoggingInstrumentor().uninstrument()
        except Exception:
            pass

        try:
            if self._results.get("psycopg2"):
                from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

                Psycopg2Instrumentor().uninstrument()
        except Exception:
            pass

        try:
            if self._results.get("redis"):
                from opentelemetry.instrumentation.redis import RedisInstrumentor

                RedisInstrumentor().uninstrument()
        except Exception:
            pass

        self._initialized = False

    @property
    def active(self) -> list[str]:
        """Get list of active instrumentations."""
        return [name for name, success in self._results.items() if success]

    @property
    def results(self) -> dict[str, bool]:
        """Get instrumentation results."""
        return self._results.copy()

    def __enter__(self) -> TelemetryFlowInstrumentor:
        """Context manager entry."""
        self.instrument()
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Context manager exit."""
        self.uninstrument()
        if self._client is not None:
            self._client.shutdown()
