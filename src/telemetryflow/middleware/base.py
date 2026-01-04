"""Base middleware for HTTP instrumentation."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from telemetryflow.application.commands import SpanKind

if TYPE_CHECKING:
    from telemetryflow.client import TelemetryFlowClient


class TelemetryMiddleware(ABC):
    """
    Base class for HTTP middleware with telemetry instrumentation.

    This provides common functionality for instrumenting HTTP requests
    across different web frameworks.
    """

    def __init__(
        self,
        client: TelemetryFlowClient,
        *,
        record_request_duration: bool = True,
        record_request_count: bool = True,
        record_error_count: bool = True,
        excluded_paths: list[str] | None = None,
    ) -> None:
        """
        Initialize the middleware.

        Args:
            client: TelemetryFlow client instance
            record_request_duration: Whether to record request duration histogram
            record_request_count: Whether to record request counter
            record_error_count: Whether to record error counter
            excluded_paths: List of paths to exclude from instrumentation
        """
        self._client = client
        self._record_duration = record_request_duration
        self._record_count = record_request_count
        self._record_errors = record_error_count
        self._excluded_paths = set(excluded_paths or [])

    def should_instrument(self, path: str) -> bool:
        """
        Check if a path should be instrumented.

        Args:
            path: The request path

        Returns:
            True if the path should be instrumented
        """
        # Check exact matches
        if path in self._excluded_paths:
            return False

        # Check prefix matches for paths ending with *
        for excluded in self._excluded_paths:
            if excluded.endswith("*") and path.startswith(excluded[:-1]):
                return False

        return True

    def start_request(
        self,
        method: str,
        path: str,
        headers: dict[str, str] | None = None,
    ) -> tuple[str, float]:
        """
        Start instrumenting a request.

        Args:
            method: HTTP method
            path: Request path
            headers: Request headers

        Returns:
            Tuple of (span_id, start_time)
        """
        start_time = time.time()

        attributes: dict[str, Any] = {
            "http.method": method,
            "http.url": path,
        }

        if headers:
            if "user-agent" in headers:
                attributes["http.user_agent"] = headers["user-agent"]
            if "host" in headers:
                attributes["http.host"] = headers["host"]

        span_id = self._client.start_span(
            f"HTTP {method} {path}",
            SpanKind.SERVER,
            attributes,
        )

        if self._record_count:
            self._client.increment_counter(
                "http.requests.total",
                attributes={"method": method, "path": path},
            )

        return span_id, start_time

    def end_request(
        self,
        span_id: str,
        start_time: float,
        method: str,
        path: str,
        status_code: int,
        error: Exception | None = None,
    ) -> None:
        """
        End instrumenting a request.

        Args:
            span_id: The span ID from start_request
            start_time: The start time from start_request
            method: HTTP method
            path: Request path
            status_code: Response status code
            error: Optional exception if request failed
        """
        duration = time.time() - start_time

        # Record duration
        if self._record_duration:
            self._client.record_histogram(
                "http.request.duration",
                duration,
                unit="s",
                attributes={
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                },
            )

        # Record errors
        if self._record_errors and status_code >= 400:
            self._client.increment_counter(
                "http.errors.total",
                attributes={
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                },
            )

            if status_code >= 500:
                self._client.log_error(
                    f"HTTP {status_code} error on {method} {path}",
                    {"duration_s": duration},
                )

        # Add span event and end span
        self._client.add_span_event(
            span_id,
            "response_sent",
            {"http.status_code": status_code},
        )

        self._client.end_span(span_id, error)

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Process a request through the middleware."""
        pass
