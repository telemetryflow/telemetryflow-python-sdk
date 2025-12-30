"""Middleware integrations for TelemetryFlow SDK."""

from telemetryflow.middleware.base import TelemetryMiddleware

__all__ = ["TelemetryMiddleware"]

# Optional framework integrations - import only if framework is available
try:
    from telemetryflow.middleware.flask import FlaskTelemetryMiddleware
    __all__.append("FlaskTelemetryMiddleware")
except ImportError:
    pass

try:
    from telemetryflow.middleware.fastapi import FastAPITelemetryMiddleware
    __all__.append("FastAPITelemetryMiddleware")
except ImportError:
    pass
