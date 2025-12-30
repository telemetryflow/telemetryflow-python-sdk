"""Flask middleware for TelemetryFlow instrumentation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from telemetryflow.middleware.base import TelemetryMiddleware

if TYPE_CHECKING:
    from flask import Flask, Response

    from telemetryflow.client import TelemetryFlowClient


class FlaskTelemetryMiddleware(TelemetryMiddleware):
    """
    Flask middleware for automatic request instrumentation.

    Example:
        >>> from flask import Flask
        >>> from telemetryflow import TelemetryFlowBuilder
        >>> from telemetryflow.middleware import FlaskTelemetryMiddleware
        >>>
        >>> app = Flask(__name__)
        >>> client = TelemetryFlowBuilder().with_auto_configuration().build()
        >>> client.initialize()
        >>>
        >>> middleware = FlaskTelemetryMiddleware(client)
        >>> middleware.init_app(app)
    """

    def __init__(
        self,
        client: TelemetryFlowClient,
        app: Flask | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Flask middleware.

        Args:
            client: TelemetryFlow client instance
            app: Optional Flask app to initialize immediately
            **kwargs: Additional options passed to base middleware
        """
        super().__init__(client, **kwargs)
        self._app = app

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """
        Initialize the middleware with a Flask app.

        Args:
            app: Flask application instance
        """
        self._app = app

        # Store span info in Flask's g object
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_request(self._teardown_request)

    def _before_request(self) -> None:
        """Called before each request."""
        from flask import g, request

        if not self.should_instrument(request.path):
            g._telemetry_skip = True
            return

        g._telemetry_skip = False
        headers = dict(request.headers)
        span_id, start_time = self.start_request(
            request.method,
            request.path,
            {k.lower(): v for k, v in headers.items()},
        )
        g._telemetry_span_id = span_id
        g._telemetry_start_time = start_time

    def _after_request(self, response: Response) -> Response:
        """Called after each request."""
        from flask import g, request

        if getattr(g, "_telemetry_skip", True):
            return response

        span_id = getattr(g, "_telemetry_span_id", None)
        start_time = getattr(g, "_telemetry_start_time", None)

        if span_id and start_time:
            self.end_request(
                span_id,
                start_time,
                request.method,
                request.path,
                response.status_code,
            )

        return response

    def _teardown_request(self, exception: BaseException | None) -> None:
        """Called when request context is torn down."""
        from flask import g, request

        if getattr(g, "_telemetry_skip", True):
            return

        # If we have an exception and span wasn't ended in after_request
        if exception:
            span_id = getattr(g, "_telemetry_span_id", None)
            start_time = getattr(g, "_telemetry_start_time", None)

            if span_id and start_time:
                self.end_request(
                    span_id,
                    start_time,
                    request.method,
                    request.path,
                    500,
                    exception if isinstance(exception, Exception) else None,
                )

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Not used for Flask - uses before/after request hooks instead."""
        pass
