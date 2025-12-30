"""TelemetryConfig - Aggregate root for SDK configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum
from typing import Any

from telemetryflow.domain.credentials import Credentials


class Protocol(str, Enum):
    """OTLP protocol type."""

    GRPC = "grpc"
    HTTP = "http"


class SignalType(str, Enum):
    """Telemetry signal type."""

    METRICS = "metrics"
    LOGS = "logs"
    TRACES = "traces"


class ConfigError(Exception):
    """Exception raised for configuration validation errors."""

    pass


@dataclass
class GRPCKeepaliveConfig:
    """gRPC keepalive configuration."""

    time: timedelta = field(default_factory=lambda: timedelta(seconds=10))
    timeout: timedelta = field(default_factory=lambda: timedelta(seconds=5))
    permit_without_stream: bool = True


@dataclass
class TelemetryConfig:
    """
    Aggregate root for TelemetryFlow SDK configuration.

    This class contains all configuration options for the SDK, including
    connection settings, authentication, signal enablement, and advanced options.
    """

    # Required fields
    credentials: Credentials
    endpoint: str
    service_name: str

    # Connection settings
    protocol: Protocol = Protocol.GRPC
    insecure: bool = False
    timeout: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    compression: bool = True

    # Retry settings
    retry_enabled: bool = True
    max_retries: int = 3
    retry_backoff: timedelta = field(default_factory=lambda: timedelta(seconds=5))

    # gRPC settings
    grpc_keepalive: GRPCKeepaliveConfig = field(default_factory=GRPCKeepaliveConfig)
    grpc_max_recv_msg_size: int = 4 * 1024 * 1024  # 4 MiB
    grpc_max_send_msg_size: int = 4 * 1024 * 1024  # 4 MiB
    grpc_read_buffer_size: int = 512 * 1024  # 512 KB
    grpc_write_buffer_size: int = 512 * 1024  # 512 KB

    # Signal configuration
    enable_metrics: bool = True
    enable_logs: bool = True
    enable_traces: bool = True
    exemplars_enabled: bool = True

    # Resource configuration
    service_version: str = "1.0.0"
    service_namespace: str = "telemetryflow"
    environment: str = "production"
    custom_attributes: dict[str, str] = field(default_factory=dict)

    # Batch settings
    batch_timeout: timedelta = field(default_factory=lambda: timedelta(seconds=10))
    batch_max_size: int = 512

    # Advanced settings
    collector_id: str | None = None
    rate_limit: int = 1000  # requests per minute

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate the configuration."""
        errors: list[str] = []

        if not self.endpoint:
            errors.append("Endpoint is required")
        if not self.service_name:
            errors.append("Service name is required")
        if self.timeout.total_seconds() <= 0:
            errors.append("Timeout must be positive")
        if self.max_retries < 0:
            errors.append("Max retries must be non-negative")
        if self.batch_max_size <= 0:
            errors.append("Batch max size must be positive")
        if self.rate_limit <= 0:
            errors.append("Rate limit must be positive")

        if errors:
            raise ConfigError("; ".join(errors))

    # Fluent configuration methods
    def with_protocol(self, protocol: Protocol) -> TelemetryConfig:
        """Set the OTLP protocol."""
        self.protocol = protocol
        return self

    def with_grpc(self) -> TelemetryConfig:
        """Use gRPC protocol."""
        return self.with_protocol(Protocol.GRPC)

    def with_http(self) -> TelemetryConfig:
        """Use HTTP protocol."""
        return self.with_protocol(Protocol.HTTP)

    def with_signals(
        self, metrics: bool = True, logs: bool = True, traces: bool = True
    ) -> TelemetryConfig:
        """Configure which signals to enable."""
        self.enable_metrics = metrics
        self.enable_logs = logs
        self.enable_traces = traces
        return self

    def with_metrics_only(self) -> TelemetryConfig:
        """Enable only metrics signal."""
        return self.with_signals(metrics=True, logs=False, traces=False)

    def with_logs_only(self) -> TelemetryConfig:
        """Enable only logs signal."""
        return self.with_signals(metrics=False, logs=True, traces=False)

    def with_traces_only(self) -> TelemetryConfig:
        """Enable only traces signal."""
        return self.with_signals(metrics=False, logs=False, traces=True)

    def with_exemplars(self, enabled: bool) -> TelemetryConfig:
        """Enable or disable exemplars for metrics-to-traces correlation."""
        self.exemplars_enabled = enabled
        return self

    def with_insecure(self, insecure: bool) -> TelemetryConfig:
        """Enable or disable TLS verification."""
        self.insecure = insecure
        return self

    def with_timeout(self, timeout: timedelta) -> TelemetryConfig:
        """Set the connection timeout."""
        self.timeout = timeout
        return self

    def with_retry(
        self,
        enabled: bool = True,
        max_retries: int = 3,
        backoff: timedelta | None = None,
    ) -> TelemetryConfig:
        """Configure retry settings."""
        self.retry_enabled = enabled
        self.max_retries = max_retries
        if backoff:
            self.retry_backoff = backoff
        return self

    def with_environment(self, environment: str) -> TelemetryConfig:
        """Set the deployment environment."""
        self.environment = environment
        return self

    def with_service_namespace(self, namespace: str) -> TelemetryConfig:
        """Set the service namespace."""
        self.service_namespace = namespace
        return self

    def with_collector_id(self, collector_id: str) -> TelemetryConfig:
        """Set the collector ID."""
        self.collector_id = collector_id
        return self

    def with_custom_attribute(self, key: str, value: str) -> TelemetryConfig:
        """Add a custom resource attribute."""
        self.custom_attributes[key] = value
        return self

    def with_custom_attributes(self, attributes: dict[str, str]) -> TelemetryConfig:
        """Add multiple custom resource attributes."""
        self.custom_attributes.update(attributes)
        return self

    def with_batch_settings(
        self, timeout: timedelta | None = None, max_size: int | None = None
    ) -> TelemetryConfig:
        """Configure batch export settings."""
        if timeout:
            self.batch_timeout = timeout
        if max_size:
            self.batch_max_size = max_size
        return self

    def with_rate_limit(self, rate_limit: int) -> TelemetryConfig:
        """Set the rate limit (requests per minute)."""
        self.rate_limit = rate_limit
        return self

    def with_compression(self, enabled: bool) -> TelemetryConfig:
        """Enable or disable compression."""
        self.compression = enabled
        return self

    # Getters for computed values
    def get_endpoint_url(self) -> str:
        """Get the full endpoint URL based on protocol."""
        if self.protocol == Protocol.HTTP:
            scheme = "http" if self.insecure else "https"
            return f"{scheme}://{self.endpoint}"
        return self.endpoint

    def get_enabled_signals(self) -> list[SignalType]:
        """Get list of enabled signals."""
        signals = []
        if self.enable_metrics:
            signals.append(SignalType.METRICS)
        if self.enable_logs:
            signals.append(SignalType.LOGS)
        if self.enable_traces:
            signals.append(SignalType.TRACES)
        return signals

    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers including collector ID."""
        headers = self.credentials.auth_headers()
        if self.collector_id:
            headers["X-TelemetryFlow-Collector-ID"] = self.collector_id
        return headers

    def get_resource_attributes(self) -> dict[str, Any]:
        """Get all resource attributes."""
        attrs = {
            "service.name": self.service_name,
            "service.version": self.service_version,
            "service.namespace": self.service_namespace,
            "deployment.environment": self.environment,
        }
        attrs.update(self.custom_attributes)
        return attrs

    def is_signal_enabled(self, signal: SignalType) -> bool:
        """Check if a specific signal is enabled."""
        if signal == SignalType.METRICS:
            return self.enable_metrics
        elif signal == SignalType.LOGS:
            return self.enable_logs
        elif signal == SignalType.TRACES:
            return self.enable_traces
        return False

    @classmethod
    def create(
        cls,
        credentials: Credentials,
        endpoint: str,
        service_name: str,
        **kwargs: Any,
    ) -> TelemetryConfig:
        """
        Factory method to create TelemetryConfig with validation.

        Args:
            credentials: API credentials
            endpoint: OTLP collector endpoint
            service_name: Name of the service
            **kwargs: Additional configuration options

        Returns:
            A new TelemetryConfig instance
        """
        return cls(
            credentials=credentials,
            endpoint=endpoint,
            service_name=service_name,
            **kwargs,
        )
