"""Middleware integrations for TelemetryFlow SDK."""

import importlib.util

from telemetryflow.middleware.base import TelemetryMiddleware

__all__ = ["TelemetryMiddleware"]

# Optional framework integrations - import only if framework is available
# Using redundant aliases (as X) to mark as intentional re-exports
if importlib.util.find_spec("flask") is not None:
    from telemetryflow.middleware.flask import FlaskTelemetryMiddleware as FlaskTelemetryMiddleware

    __all__.append("FlaskTelemetryMiddleware")

if importlib.util.find_spec("fastapi") is not None:
    from telemetryflow.middleware.fastapi import (
        FastAPITelemetryMiddleware as FastAPITelemetryMiddleware,
    )

    __all__.append("FastAPITelemetryMiddleware")
