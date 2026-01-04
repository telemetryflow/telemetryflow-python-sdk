"""OTLP Exporter Factory for TelemetryFlow SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
    OTLPMetricExporter as HTTPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as HTTPSpanExporter,
)
from opentelemetry.sdk.metrics.export import MetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import SpanExporter

if TYPE_CHECKING:
    from telemetryflow.domain.config import TelemetryConfig


class OTLPExporterFactory:
    """
    Factory for creating OTLP exporters based on configuration.

    This factory creates OpenTelemetry exporters (trace, metric) based on
    the protocol and settings specified in the TelemetryConfig.
    """

    def __init__(self, config: TelemetryConfig) -> None:
        """
        Initialize the exporter factory.

        Args:
            config: TelemetryFlow configuration
        """
        self._config = config
        self._headers = self._build_headers()

    def _build_headers(self) -> dict[str, str]:
        """Build authentication headers."""
        headers = self._config.get_auth_headers()
        headers["Content-Type"] = "application/x-protobuf"
        return headers

    def _get_grpc_headers(self) -> tuple[tuple[str, str], ...]:
        """
        Get headers formatted for gRPC metadata.

        gRPC requires metadata keys to be lowercase.

        Returns:
            Tuple of (key, value) pairs with lowercase keys
        """
        return tuple((k.lower(), v) for k, v in self._headers.items())

    def create_resource(self) -> Resource:
        """
        Create an OpenTelemetry Resource with service metadata.

        Returns:
            Configured Resource instance
        """
        attributes = self._config.get_resource_attributes()
        return Resource.create(attributes)

    def create_trace_exporter(self) -> SpanExporter:
        """
        Create a trace exporter based on protocol configuration.

        Returns:
            Configured SpanExporter instance
        """
        from telemetryflow.domain.config import Protocol

        if self._config.protocol == Protocol.GRPC:
            return self._create_grpc_trace_exporter()
        else:
            return self._create_http_trace_exporter()

    def create_metric_exporter(self) -> MetricExporter:
        """
        Create a metric exporter based on protocol configuration.

        Returns:
            Configured MetricExporter instance
        """
        from telemetryflow.domain.config import Protocol

        if self._config.protocol == Protocol.GRPC:
            return self._create_grpc_metric_exporter()
        else:
            return self._create_http_metric_exporter()

    def _create_grpc_trace_exporter(self) -> OTLPSpanExporter:
        """Create a gRPC trace exporter."""
        kwargs: dict[str, Any] = {
            "endpoint": self._config.endpoint,
            "headers": self._get_grpc_headers(),
            "insecure": self._config.insecure,
            "timeout": int(self._config.timeout.total_seconds()),
        }

        if self._config.compression:
            from opentelemetry.exporter.otlp.proto.grpc.exporter import Compression

            kwargs["compression"] = Compression.Gzip

        return OTLPSpanExporter(**kwargs)

    def _create_http_trace_exporter(self) -> HTTPSpanExporter:
        """Create an HTTP trace exporter."""
        endpoint = self._get_http_endpoint("/v1/traces")

        kwargs: dict[str, Any] = {
            "endpoint": endpoint,
            "headers": self._headers,
            "timeout": int(self._config.timeout.total_seconds()),
        }

        if self._config.compression:
            from opentelemetry.exporter.otlp.proto.http.exporter import Compression

            kwargs["compression"] = Compression.Gzip

        return HTTPSpanExporter(**kwargs)

    def _create_grpc_metric_exporter(self) -> OTLPMetricExporter:
        """Create a gRPC metric exporter."""
        kwargs: dict[str, Any] = {
            "endpoint": self._config.endpoint,
            "headers": self._get_grpc_headers(),
            "insecure": self._config.insecure,
            "timeout": int(self._config.timeout.total_seconds()),
        }

        if self._config.compression:
            from opentelemetry.exporter.otlp.proto.grpc.exporter import Compression

            kwargs["compression"] = Compression.Gzip

        return OTLPMetricExporter(**kwargs)

    def _create_http_metric_exporter(self) -> HTTPMetricExporter:
        """Create an HTTP metric exporter."""
        endpoint = self._get_http_endpoint("/v1/metrics")

        kwargs: dict[str, Any] = {
            "endpoint": endpoint,
            "headers": self._headers,
            "timeout": int(self._config.timeout.total_seconds()),
        }

        if self._config.compression:
            from opentelemetry.exporter.otlp.proto.http.exporter import Compression

            kwargs["compression"] = Compression.Gzip

        return HTTPMetricExporter(**kwargs)

    def _get_http_endpoint(self, path: str) -> str:
        """
        Get the full HTTP endpoint URL.

        Args:
            path: The API path (e.g., "/v1/traces")

        Returns:
            Full endpoint URL
        """
        base = self._config.get_endpoint_url()
        # Remove trailing slash if present
        if base.endswith("/"):
            base = base[:-1]
        return f"{base}{path}"

    def get_headers(self) -> dict[str, str]:
        """Get the configured authentication headers."""
        return self._headers.copy()
