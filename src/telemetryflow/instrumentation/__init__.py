"""TelemetryFlow Auto-Instrumentation Module.

This module provides auto-instrumentation capabilities for common Python frameworks
and libraries, allowing automatic collection of traces, metrics, and logs without
manual code changes.

Usage:
    from telemetryflow import TelemetryFlowBuilder
    from telemetryflow.instrumentation import auto_instrument

    # Initialize TelemetryFlow
    client = TelemetryFlowBuilder().with_auto_configuration().build()
    client.initialize()

    # Enable auto-instrumentation for all supported libraries
    auto_instrument()

    # Or selectively instrument specific libraries
    from telemetryflow.instrumentation import (
        instrument_flask,
        instrument_fastapi,
        instrument_sqlalchemy,
        instrument_requests,
    )
    instrument_flask()
    instrument_requests()
"""

from __future__ import annotations

import importlib.util
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from opentelemetry.metrics import MeterProvider
    from opentelemetry.trace import TracerProvider

# Export symbols
__all__ = [
    "auto_instrument",
    "instrument_flask",
    "instrument_fastapi",
    "instrument_sqlalchemy",
    "instrument_requests",
    "instrument_httpx",
    "instrument_logging",
    "instrument_psycopg2",
    "instrument_redis",
    "InstrumentationConfig",
    "get_available_instrumentations",
    "is_instrumentation_available",
]


class InstrumentationConfig:
    """Configuration for auto-instrumentation."""

    def __init__(
        self,
        tracer_provider: TracerProvider | None = None,
        meter_provider: MeterProvider | None = None,
        service_name: str | None = None,
        service_version: str | None = None,
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
    ) -> None:
        """Initialize instrumentation configuration.

        Args:
            tracer_provider: OpenTelemetry TracerProvider to use
            meter_provider: OpenTelemetry MeterProvider to use
            service_name: Service name for resource attributes
            service_version: Service version for resource attributes
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
        """
        self.tracer_provider = tracer_provider
        self.meter_provider = meter_provider
        self.service_name = service_name
        self.service_version = service_version
        self.enable_flask = enable_flask
        self.enable_fastapi = enable_fastapi
        self.enable_sqlalchemy = enable_sqlalchemy
        self.enable_requests = enable_requests
        self.enable_httpx = enable_httpx
        self.enable_logging = enable_logging
        self.enable_psycopg2 = enable_psycopg2
        self.enable_redis = enable_redis
        self.excluded_urls = excluded_urls or []
        self.excluded_hosts = excluded_hosts or []


def _is_package_available(package_name: str) -> bool:
    """Check if a package is available."""
    return importlib.util.find_spec(package_name) is not None


def is_instrumentation_available(name: str) -> bool:
    """Check if a specific instrumentation is available.

    Args:
        name: Name of the instrumentation (flask, fastapi, sqlalchemy, etc.)

    Returns:
        True if the instrumentation package is installed
    """
    instrumentation_packages = {
        "flask": "opentelemetry.instrumentation.flask",
        "fastapi": "opentelemetry.instrumentation.fastapi",
        "sqlalchemy": "opentelemetry.instrumentation.sqlalchemy",
        "requests": "opentelemetry.instrumentation.requests",
        "httpx": "opentelemetry.instrumentation.httpx",
        "logging": "opentelemetry.instrumentation.logging",
        "psycopg2": "opentelemetry.instrumentation.psycopg2",
        "redis": "opentelemetry.instrumentation.redis",
    }
    pkg = instrumentation_packages.get(name.lower())
    if pkg is None:
        return False
    return _is_package_available(pkg)


def get_available_instrumentations() -> list[str]:
    """Get a list of available instrumentations.

    Returns:
        List of instrumentation names that are available
    """
    instrumentations = [
        "flask",
        "fastapi",
        "sqlalchemy",
        "requests",
        "httpx",
        "logging",
        "psycopg2",
        "redis",
    ]
    return [name for name in instrumentations if is_instrumentation_available(name)]


def instrument_flask(
    tracer_provider: TracerProvider | None = None,
    meter_provider: MeterProvider | None = None,
    excluded_urls: str | None = None,
    **kwargs: Any,
) -> bool:
    """Instrument Flask application.

    Args:
        tracer_provider: OpenTelemetry TracerProvider
        meter_provider: OpenTelemetry MeterProvider
        excluded_urls: Comma-separated URL patterns to exclude
        **kwargs: Additional arguments passed to the instrumentor

    Returns:
        True if instrumentation was successful
    """
    if not _is_package_available("opentelemetry.instrumentation.flask"):
        return False

    if not _is_package_available("flask"):
        return False

    try:
        from opentelemetry.instrumentation.flask import FlaskInstrumentor

        FlaskInstrumentor().instrument(
            tracer_provider=tracer_provider,
            meter_provider=meter_provider,
            excluded_urls=excluded_urls,
            **kwargs,
        )
        return True
    except Exception:
        return False


def instrument_fastapi(
    tracer_provider: TracerProvider | None = None,
    meter_provider: MeterProvider | None = None,
    excluded_urls: str | None = None,
    **kwargs: Any,
) -> bool:
    """Instrument FastAPI application.

    Args:
        tracer_provider: OpenTelemetry TracerProvider
        meter_provider: OpenTelemetry MeterProvider
        excluded_urls: Comma-separated URL patterns to exclude
        **kwargs: Additional arguments passed to the instrumentor

    Returns:
        True if instrumentation was successful
    """
    if not _is_package_available("opentelemetry.instrumentation.fastapi"):
        return False

    if not _is_package_available("fastapi"):
        return False

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor().instrument(
            tracer_provider=tracer_provider,
            meter_provider=meter_provider,
            excluded_urls=excluded_urls,
            **kwargs,
        )
        return True
    except Exception:
        return False


def instrument_sqlalchemy(
    tracer_provider: TracerProvider | None = None,
    engine: Any | None = None,
    enable_commenter: bool = True,
    **kwargs: Any,
) -> bool:
    """Instrument SQLAlchemy.

    Args:
        tracer_provider: OpenTelemetry TracerProvider
        engine: SQLAlchemy engine to instrument (optional)
        enable_commenter: Enable SQL commenter for trace correlation
        **kwargs: Additional arguments passed to the instrumentor

    Returns:
        True if instrumentation was successful
    """
    if not _is_package_available("opentelemetry.instrumentation.sqlalchemy"):
        return False

    if not _is_package_available("sqlalchemy"):
        return False

    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument(
            tracer_provider=tracer_provider,
            engine=engine,
            enable_commenter=enable_commenter,
            **kwargs,
        )
        return True
    except Exception:
        return False


def instrument_requests(
    tracer_provider: TracerProvider | None = None,
    excluded_urls: str | None = None,
    **kwargs: Any,
) -> bool:
    """Instrument requests library.

    Args:
        tracer_provider: OpenTelemetry TracerProvider
        excluded_urls: Comma-separated URL patterns to exclude
        **kwargs: Additional arguments passed to the instrumentor

    Returns:
        True if instrumentation was successful
    """
    if not _is_package_available("opentelemetry.instrumentation.requests"):
        return False

    if not _is_package_available("requests"):
        return False

    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor

        RequestsInstrumentor().instrument(
            tracer_provider=tracer_provider,
            excluded_urls=excluded_urls,
            **kwargs,
        )
        return True
    except Exception:
        return False


def instrument_httpx(
    tracer_provider: TracerProvider | None = None,
    **kwargs: Any,
) -> bool:
    """Instrument httpx library.

    Args:
        tracer_provider: OpenTelemetry TracerProvider
        **kwargs: Additional arguments passed to the instrumentor

    Returns:
        True if instrumentation was successful
    """
    if not _is_package_available("opentelemetry.instrumentation.httpx"):
        return False

    if not _is_package_available("httpx"):
        return False

    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument(
            tracer_provider=tracer_provider,
            **kwargs,
        )
        return True
    except Exception:
        return False


def instrument_logging(
    tracer_provider: TracerProvider | None = None,
    set_logging_format: bool = True,
    log_level: int | None = None,
    **kwargs: Any,
) -> bool:
    """Instrument Python logging.

    Args:
        tracer_provider: OpenTelemetry TracerProvider
        set_logging_format: Set logging format to include trace context
        log_level: Minimum log level to capture
        **kwargs: Additional arguments passed to the instrumentor

    Returns:
        True if instrumentation was successful
    """
    if not _is_package_available("opentelemetry.instrumentation.logging"):
        return False

    try:
        from opentelemetry.instrumentation.logging import LoggingInstrumentor

        LoggingInstrumentor().instrument(
            tracer_provider=tracer_provider,
            set_logging_format=set_logging_format,
            log_level=log_level,
            **kwargs,
        )
        return True
    except Exception:
        return False


def instrument_psycopg2(
    tracer_provider: TracerProvider | None = None,
    enable_commenter: bool = True,
    **kwargs: Any,
) -> bool:
    """Instrument psycopg2 PostgreSQL driver.

    Args:
        tracer_provider: OpenTelemetry TracerProvider
        enable_commenter: Enable SQL commenter for trace correlation
        **kwargs: Additional arguments passed to the instrumentor

    Returns:
        True if instrumentation was successful
    """
    if not _is_package_available("opentelemetry.instrumentation.psycopg2"):
        return False

    if not _is_package_available("psycopg2"):
        return False

    try:
        from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

        Psycopg2Instrumentor().instrument(
            tracer_provider=tracer_provider,
            enable_commenter=enable_commenter,
            **kwargs,
        )
        return True
    except Exception:
        return False


def instrument_redis(
    tracer_provider: TracerProvider | None = None,
    **kwargs: Any,
) -> bool:
    """Instrument Redis client.

    Args:
        tracer_provider: OpenTelemetry TracerProvider
        **kwargs: Additional arguments passed to the instrumentor

    Returns:
        True if instrumentation was successful
    """
    if not _is_package_available("opentelemetry.instrumentation.redis"):
        return False

    if not _is_package_available("redis"):
        return False

    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        RedisInstrumentor().instrument(
            tracer_provider=tracer_provider,
            **kwargs,
        )
        return True
    except Exception:
        return False


def auto_instrument(
    config: InstrumentationConfig | None = None,
    tracer_provider: TracerProvider | None = None,
    meter_provider: MeterProvider | None = None,
) -> dict[str, bool]:
    """Auto-instrument all available libraries.

    This function automatically instruments all supported libraries that are
    installed in the environment. It's the easiest way to enable observability
    for your application.

    Args:
        config: Optional InstrumentationConfig for fine-grained control
        tracer_provider: OpenTelemetry TracerProvider (overrides config)
        meter_provider: OpenTelemetry MeterProvider (overrides config)

    Returns:
        Dictionary mapping instrumentation names to success status

    Example:
        >>> from telemetryflow.instrumentation import auto_instrument
        >>> results = auto_instrument()
        >>> print(results)
        {'flask': True, 'requests': True, 'sqlalchemy': True, ...}
    """
    if config is None:
        config = InstrumentationConfig(
            tracer_provider=tracer_provider,
            meter_provider=meter_provider,
        )
    else:
        if tracer_provider is not None:
            config.tracer_provider = tracer_provider
        if meter_provider is not None:
            config.meter_provider = meter_provider

    results: dict[str, bool] = {}

    excluded_urls_str = ",".join(config.excluded_urls) if config.excluded_urls else None

    if config.enable_flask:
        results["flask"] = instrument_flask(
            tracer_provider=config.tracer_provider,
            meter_provider=config.meter_provider,
            excluded_urls=excluded_urls_str,
        )

    if config.enable_fastapi:
        results["fastapi"] = instrument_fastapi(
            tracer_provider=config.tracer_provider,
            meter_provider=config.meter_provider,
            excluded_urls=excluded_urls_str,
        )

    if config.enable_sqlalchemy:
        results["sqlalchemy"] = instrument_sqlalchemy(
            tracer_provider=config.tracer_provider,
        )

    if config.enable_requests:
        results["requests"] = instrument_requests(
            tracer_provider=config.tracer_provider,
            excluded_urls=excluded_urls_str,
        )

    if config.enable_httpx:
        results["httpx"] = instrument_httpx(
            tracer_provider=config.tracer_provider,
        )

    if config.enable_logging:
        results["logging"] = instrument_logging(
            tracer_provider=config.tracer_provider,
        )

    if config.enable_psycopg2:
        results["psycopg2"] = instrument_psycopg2(
            tracer_provider=config.tracer_provider,
        )

    if config.enable_redis:
        results["redis"] = instrument_redis(
            tracer_provider=config.tracer_provider,
        )

    return results
