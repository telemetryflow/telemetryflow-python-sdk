"""FastAPI/Starlette middleware for TelemetryFlow instrumentation."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from telemetryflow.middleware.base import TelemetryMiddleware

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

    from telemetryflow.client import TelemetryFlowClient


class FastAPITelemetryMiddleware(TelemetryMiddleware):
    """
    FastAPI/Starlette middleware for automatic request instrumentation.

    This middleware works with both FastAPI and Starlette applications.

    Example:
        >>> from fastapi import FastAPI
        >>> from telemetryflow import TelemetryFlowBuilder
        >>> from telemetryflow.middleware import FastAPITelemetryMiddleware
        >>>
        >>> app = FastAPI()
        >>> client = TelemetryFlowBuilder().with_auto_configuration().build()
        >>> client.initialize()
        >>>
        >>> app.add_middleware(FastAPITelemetryMiddleware, client=client)
    """

    def __init__(
        self,
        app: ASGIApp,
        client: TelemetryFlowClient,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the FastAPI middleware.

        Args:
            app: The ASGI application
            client: TelemetryFlow client instance
            **kwargs: Additional options passed to base middleware
        """
        super().__init__(client, **kwargs)
        self._asgi_app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """
        Process an ASGI request.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] != "http":
            await self._asgi_app(scope, receive, send)
            return

        path = scope.get("path", "/")
        method = scope.get("method", "GET")

        if not self.should_instrument(path):
            await self._asgi_app(scope, receive, send)
            return

        # Extract headers
        headers = {}
        for key, value in scope.get("headers", []):
            headers[key.decode("latin1").lower()] = value.decode("latin1")

        # Start instrumentation
        span_id, start_time = self.start_request(method, path, headers)

        status_code = 500
        error: Exception | None = None

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)

            await send(message)

        try:
            await self._asgi_app(scope, receive, send_wrapper)
        except Exception as e:
            error = e
            raise
        finally:
            self.end_request(
                span_id,
                start_time,
                method,
                path,
                status_code,
                error,
            )


def create_fastapi_middleware(
    client: TelemetryFlowClient,
    **kwargs: Any,
) -> Callable[[ASGIApp], FastAPITelemetryMiddleware]:
    """
    Create a FastAPI middleware factory.

    This is useful when you want to pass options to the middleware.

    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> middleware = create_fastapi_middleware(
        ...     client,
        ...     excluded_paths=["/health", "/metrics"],
        ... )
        >>> app.add_middleware(middleware)

    Args:
        client: TelemetryFlow client instance
        **kwargs: Options passed to the middleware

    Returns:
        Middleware factory callable
    """

    def middleware_factory(app: ASGIApp) -> FastAPITelemetryMiddleware:
        return FastAPITelemetryMiddleware(app, client, **kwargs)

    return middleware_factory
