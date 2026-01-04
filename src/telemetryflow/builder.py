"""TelemetryFlow Builder - Fluent interface for client configuration."""

from __future__ import annotations

import contextlib
import os
from datetime import timedelta
from typing import TYPE_CHECKING

from telemetryflow.client import TelemetryFlowClient
from telemetryflow.domain.config import Protocol, TelemetryConfig
from telemetryflow.domain.credentials import Credentials, CredentialsError

if TYPE_CHECKING:
    pass


class BuilderError(Exception):
    """Exception raised for builder configuration errors."""

    pass


class TelemetryFlowBuilder:
    """
    Fluent builder for creating TelemetryFlow clients.

    This builder provides a chainable API for configuring all aspects
    of the TelemetryFlow SDK before building the client.

    Example:
        >>> client = (
        ...     TelemetryFlowBuilder()
        ...     .with_api_key("tfk_xxx", "tfs_xxx")
        ...     .with_endpoint("api.telemetryflow.id:4317")
        ...     .with_service("my-service", "1.0.0")
        ...     .with_environment("production")
        ...     .with_grpc()
        ...     .build()
        ... )
    """

    # Environment variable names - Core Settings
    ENV_API_KEY_ID = "TELEMETRYFLOW_API_KEY_ID"
    ENV_API_KEY_SECRET = "TELEMETRYFLOW_API_KEY_SECRET"
    ENV_ENDPOINT = "TELEMETRYFLOW_ENDPOINT"
    ENV_SERVICE_NAME = "TELEMETRYFLOW_SERVICE_NAME"
    ENV_SERVICE_VERSION = "TELEMETRYFLOW_SERVICE_VERSION"
    ENV_SERVICE_NAMESPACE = "TELEMETRYFLOW_SERVICE_NAMESPACE"
    ENV_ENVIRONMENT = "TELEMETRYFLOW_ENVIRONMENT"
    ENV_INSECURE = "TELEMETRYFLOW_INSECURE"

    # Environment variable names - TFO v2 API Settings
    ENV_USE_V2_API = "TELEMETRYFLOW_USE_V2_API"
    ENV_V2_ONLY = "TELEMETRYFLOW_V2_ONLY"

    # Environment variable names - Collector Identity
    ENV_COLLECTOR_ID = "TELEMETRYFLOW_COLLECTOR_ID"
    ENV_COLLECTOR_NAME = "TELEMETRYFLOW_COLLECTOR_NAME"
    ENV_COLLECTOR_HOSTNAME = "TELEMETRYFLOW_COLLECTOR_HOSTNAME"
    ENV_DATACENTER = "TELEMETRYFLOW_DATACENTER"
    ENV_ENRICH_RESOURCES = "TELEMETRYFLOW_ENRICH_RESOURCES"

    # Environment variable names - Protocol Settings
    ENV_PROTOCOL = "TELEMETRYFLOW_PROTOCOL"
    ENV_COMPRESSION = "TELEMETRYFLOW_COMPRESSION"
    ENV_TIMEOUT = "TELEMETRYFLOW_TIMEOUT"

    # Environment variable names - Retry Settings
    ENV_RETRY_ENABLED = "TELEMETRYFLOW_RETRY_ENABLED"
    ENV_MAX_RETRIES = "TELEMETRYFLOW_MAX_RETRIES"
    ENV_RETRY_BACKOFF = "TELEMETRYFLOW_RETRY_BACKOFF"

    # Environment variable names - Batch Settings
    ENV_BATCH_TIMEOUT = "TELEMETRYFLOW_BATCH_TIMEOUT"
    ENV_BATCH_MAX_SIZE = "TELEMETRYFLOW_BATCH_MAX_SIZE"

    # Environment variable names - Signals
    ENV_ENABLE_TRACES = "TELEMETRYFLOW_ENABLE_TRACES"
    ENV_ENABLE_METRICS = "TELEMETRYFLOW_ENABLE_METRICS"
    ENV_ENABLE_LOGS = "TELEMETRYFLOW_ENABLE_LOGS"
    ENV_ENABLE_EXEMPLARS = "TELEMETRYFLOW_ENABLE_EXEMPLARS"

    # Environment variable names - Rate Limiting
    ENV_RATE_LIMIT = "TELEMETRYFLOW_RATE_LIMIT"

    # Default values
    DEFAULT_ENDPOINT = "api.telemetryflow.id:4317"
    DEFAULT_SERVICE_VERSION = "1.0.0"
    DEFAULT_SERVICE_NAMESPACE = "telemetryflow"
    DEFAULT_ENVIRONMENT = "production"

    def __init__(self) -> None:
        """Initialize the builder with default values."""
        self._api_key_id: str | None = None
        self._api_key_secret: str | None = None
        self._endpoint: str = self.DEFAULT_ENDPOINT
        self._service_name: str | None = None
        self._service_version: str = self.DEFAULT_SERVICE_VERSION
        self._service_namespace: str = self.DEFAULT_SERVICE_NAMESPACE
        self._environment: str = self.DEFAULT_ENVIRONMENT
        self._protocol: Protocol = Protocol.GRPC
        self._insecure: bool = False
        self._timeout: timedelta = timedelta(seconds=30)
        self._enable_metrics: bool = True
        self._enable_logs: bool = True
        self._enable_traces: bool = True
        self._exemplars_enabled: bool = True
        self._collector_id: str | None = None
        self._custom_attributes: dict[str, str] = {}
        self._compression: bool = True
        self._retry_enabled: bool = True
        self._max_retries: int = 3
        self._retry_backoff: timedelta = timedelta(seconds=5)
        self._batch_timeout: timedelta = timedelta(seconds=10)
        self._batch_max_size: int = 512
        self._rate_limit: int = 1000
        self._errors: list[str] = []

    # API Key Configuration

    def with_api_key(self, key_id: str, key_secret: str) -> TelemetryFlowBuilder:
        """
        Set the API key credentials.

        Args:
            key_id: API key ID (must start with 'tfk_')
            key_secret: API key secret (must start with 'tfs_')

        Returns:
            Self for method chaining
        """
        self._api_key_id = key_id
        self._api_key_secret = key_secret
        return self

    def with_api_key_from_env(self) -> TelemetryFlowBuilder:
        """
        Load API key from environment variables.

        Uses TELEMETRYFLOW_API_KEY_ID and TELEMETRYFLOW_API_KEY_SECRET.

        Returns:
            Self for method chaining
        """
        self._api_key_id = os.environ.get(self.ENV_API_KEY_ID)
        self._api_key_secret = os.environ.get(self.ENV_API_KEY_SECRET)
        return self

    # Endpoint Configuration

    def with_endpoint(self, endpoint: str) -> TelemetryFlowBuilder:
        """
        Set the TelemetryFlow collector endpoint.

        Args:
            endpoint: Endpoint address (host:port)

        Returns:
            Self for method chaining
        """
        self._endpoint = endpoint
        return self

    def with_endpoint_from_env(self) -> TelemetryFlowBuilder:
        """
        Load endpoint from environment variable.

        Uses TELEMETRYFLOW_ENDPOINT, falls back to default if not set.

        Returns:
            Self for method chaining
        """
        self._endpoint = os.environ.get(self.ENV_ENDPOINT, self.DEFAULT_ENDPOINT)
        return self

    # Service Configuration

    def with_service(self, name: str, version: str | None = None) -> TelemetryFlowBuilder:
        """
        Set the service name and optional version.

        Args:
            name: Service name
            version: Service version (optional)

        Returns:
            Self for method chaining
        """
        self._service_name = name
        if version:
            self._service_version = version
        return self

    def with_service_from_env(self) -> TelemetryFlowBuilder:
        """
        Load service configuration from environment variables.

        Uses TELEMETRYFLOW_SERVICE_NAME and TELEMETRYFLOW_SERVICE_VERSION.

        Returns:
            Self for method chaining
        """
        self._service_name = os.environ.get(self.ENV_SERVICE_NAME)
        self._service_version = os.environ.get(
            self.ENV_SERVICE_VERSION, self.DEFAULT_SERVICE_VERSION
        )
        return self

    def with_service_namespace(self, namespace: str) -> TelemetryFlowBuilder:
        """
        Set the service namespace.

        Args:
            namespace: Service namespace for multi-tenant support

        Returns:
            Self for method chaining
        """
        self._service_namespace = namespace
        return self

    def with_service_namespace_from_env(self) -> TelemetryFlowBuilder:
        """
        Load service namespace from environment variable.

        Returns:
            Self for method chaining
        """
        self._service_namespace = os.environ.get(
            self.ENV_SERVICE_NAMESPACE, self.DEFAULT_SERVICE_NAMESPACE
        )
        return self

    # Environment Configuration

    def with_environment(self, environment: str) -> TelemetryFlowBuilder:
        """
        Set the deployment environment.

        Args:
            environment: Environment name (e.g., 'production', 'staging')

        Returns:
            Self for method chaining
        """
        self._environment = environment
        return self

    def with_environment_from_env(self) -> TelemetryFlowBuilder:
        """
        Load environment from environment variables.

        Checks TELEMETRYFLOW_ENVIRONMENT, ENV, and ENVIRONMENT in order.

        Returns:
            Self for method chaining
        """
        self._environment = (
            os.environ.get(self.ENV_ENVIRONMENT)
            or os.environ.get("ENV")
            or os.environ.get("ENVIRONMENT")
            or self.DEFAULT_ENVIRONMENT
        )
        return self

    # Protocol Configuration

    def with_protocol(self, protocol: Protocol) -> TelemetryFlowBuilder:
        """
        Set the OTLP protocol.

        Args:
            protocol: Protocol type (GRPC or HTTP)

        Returns:
            Self for method chaining
        """
        self._protocol = protocol
        return self

    def with_grpc(self) -> TelemetryFlowBuilder:
        """
        Use gRPC protocol (default).

        Returns:
            Self for method chaining
        """
        return self.with_protocol(Protocol.GRPC)

    def with_http(self) -> TelemetryFlowBuilder:
        """
        Use HTTP protocol.

        Returns:
            Self for method chaining
        """
        return self.with_protocol(Protocol.HTTP)

    def with_insecure(self, insecure: bool = True) -> TelemetryFlowBuilder:
        """
        Enable or disable TLS verification.

        Args:
            insecure: Whether to disable TLS verification

        Returns:
            Self for method chaining
        """
        self._insecure = insecure
        return self

    # Signal Configuration

    def with_signals(
        self, metrics: bool = True, logs: bool = True, traces: bool = True
    ) -> TelemetryFlowBuilder:
        """
        Configure which signals to enable.

        Args:
            metrics: Enable metrics
            logs: Enable logs
            traces: Enable traces

        Returns:
            Self for method chaining
        """
        self._enable_metrics = metrics
        self._enable_logs = logs
        self._enable_traces = traces
        return self

    def with_metrics_only(self) -> TelemetryFlowBuilder:
        """
        Enable only metrics signal.

        Returns:
            Self for method chaining
        """
        return self.with_signals(metrics=True, logs=False, traces=False)

    def with_logs_only(self) -> TelemetryFlowBuilder:
        """
        Enable only logs signal.

        Returns:
            Self for method chaining
        """
        return self.with_signals(metrics=False, logs=True, traces=False)

    def with_traces_only(self) -> TelemetryFlowBuilder:
        """
        Enable only traces signal.

        Returns:
            Self for method chaining
        """
        return self.with_signals(metrics=False, logs=False, traces=True)

    def with_exemplars(self, enabled: bool = True) -> TelemetryFlowBuilder:
        """
        Enable or disable exemplars for metrics-to-traces correlation.

        Args:
            enabled: Whether to enable exemplars

        Returns:
            Self for method chaining
        """
        self._exemplars_enabled = enabled
        return self

    # Advanced Configuration

    def with_timeout(self, timeout: timedelta) -> TelemetryFlowBuilder:
        """
        Set the connection timeout.

        Args:
            timeout: Connection timeout

        Returns:
            Self for method chaining
        """
        self._timeout = timeout
        return self

    def with_collector_id(self, collector_id: str) -> TelemetryFlowBuilder:
        """
        Set the collector ID.

        Args:
            collector_id: Unique collector identifier

        Returns:
            Self for method chaining
        """
        self._collector_id = collector_id
        return self

    def with_collector_id_from_env(self) -> TelemetryFlowBuilder:
        """
        Load collector ID from environment variable.

        Returns:
            Self for method chaining
        """
        self._collector_id = os.environ.get(self.ENV_COLLECTOR_ID)
        return self

    def with_custom_attribute(self, key: str, value: str) -> TelemetryFlowBuilder:
        """
        Add a custom resource attribute.

        Args:
            key: Attribute key
            value: Attribute value

        Returns:
            Self for method chaining
        """
        self._custom_attributes[key] = value
        return self

    def with_custom_attributes(self, attributes: dict[str, str]) -> TelemetryFlowBuilder:
        """
        Add multiple custom resource attributes.

        Args:
            attributes: Dictionary of attributes

        Returns:
            Self for method chaining
        """
        self._custom_attributes.update(attributes)
        return self

    def with_compression(self, enabled: bool = True) -> TelemetryFlowBuilder:
        """
        Enable or disable compression.

        Args:
            enabled: Whether to enable compression

        Returns:
            Self for method chaining
        """
        self._compression = enabled
        return self

    def with_retry(
        self,
        enabled: bool = True,
        max_retries: int = 3,
        backoff: timedelta | None = None,
    ) -> TelemetryFlowBuilder:
        """
        Configure retry settings.

        Args:
            enabled: Enable retries
            max_retries: Maximum retry attempts
            backoff: Backoff duration between retries

        Returns:
            Self for method chaining
        """
        self._retry_enabled = enabled
        self._max_retries = max_retries
        if backoff:
            self._retry_backoff = backoff
        return self

    def with_batch_settings(
        self, timeout: timedelta | None = None, max_size: int | None = None
    ) -> TelemetryFlowBuilder:
        """
        Configure batch export settings.

        Args:
            timeout: Batch export timeout
            max_size: Maximum batch size

        Returns:
            Self for method chaining
        """
        if timeout:
            self._batch_timeout = timeout
        if max_size:
            self._batch_max_size = max_size
        return self

    def with_rate_limit(self, rate_limit: int) -> TelemetryFlowBuilder:
        """
        Set the rate limit.

        Args:
            rate_limit: Requests per minute

        Returns:
            Self for method chaining
        """
        self._rate_limit = rate_limit
        return self

    # Auto Configuration

    def with_auto_configuration(self) -> TelemetryFlowBuilder:
        """
        Load all configuration from environment variables.

        This is a convenience method that loads all supported TELEMETRYFLOW_*
        environment variables for TFO-Collector v1.1.2 compatibility.

        Returns:
            Self for method chaining
        """
        # Core settings
        self.with_api_key_from_env()
        self.with_endpoint_from_env()
        self.with_service_from_env()
        self.with_service_namespace_from_env()
        self.with_environment_from_env()
        self.with_collector_id_from_env()

        # Insecure mode
        insecure_str = os.environ.get(self.ENV_INSECURE, "false")
        self._insecure = insecure_str.lower() == "true"

        # Protocol settings
        protocol_str = os.environ.get(self.ENV_PROTOCOL, "grpc")
        if protocol_str.lower() == "http":
            self._protocol = Protocol.HTTP
        else:
            self._protocol = Protocol.GRPC

        # Compression
        compression_str = os.environ.get(self.ENV_COMPRESSION, "false")
        self._compression = compression_str.lower() == "true"

        # Timeout (in seconds)
        timeout_str = os.environ.get(self.ENV_TIMEOUT, "10")
        with contextlib.suppress(ValueError):
            self._timeout = timedelta(seconds=int(timeout_str))

        # Retry settings
        retry_enabled_str = os.environ.get(self.ENV_RETRY_ENABLED, "true")
        self._retry_enabled = retry_enabled_str.lower() == "true"

        max_retries_str = os.environ.get(self.ENV_MAX_RETRIES, "3")
        with contextlib.suppress(ValueError):
            self._max_retries = int(max_retries_str)

        retry_backoff_str = os.environ.get(self.ENV_RETRY_BACKOFF, "500")
        with contextlib.suppress(ValueError):
            self._retry_backoff = timedelta(milliseconds=int(retry_backoff_str))

        # Batch settings
        batch_timeout_str = os.environ.get(self.ENV_BATCH_TIMEOUT, "5000")
        with contextlib.suppress(ValueError):
            self._batch_timeout = timedelta(milliseconds=int(batch_timeout_str))

        batch_max_size_str = os.environ.get(self.ENV_BATCH_MAX_SIZE, "512")
        with contextlib.suppress(ValueError):
            self._batch_max_size = int(batch_max_size_str)

        # Signal settings
        enable_traces_str = os.environ.get(self.ENV_ENABLE_TRACES, "true")
        self._enable_traces = enable_traces_str.lower() == "true"

        enable_metrics_str = os.environ.get(self.ENV_ENABLE_METRICS, "true")
        self._enable_metrics = enable_metrics_str.lower() == "true"

        enable_logs_str = os.environ.get(self.ENV_ENABLE_LOGS, "true")
        self._enable_logs = enable_logs_str.lower() == "true"

        enable_exemplars_str = os.environ.get(self.ENV_ENABLE_EXEMPLARS, "true")
        self._exemplars_enabled = enable_exemplars_str.lower() == "true"

        # Rate limit (0 = unlimited)
        rate_limit_str = os.environ.get(self.ENV_RATE_LIMIT, "0")
        try:
            rate_limit = int(rate_limit_str)
            if rate_limit > 0:
                self._rate_limit = rate_limit
        except ValueError:
            pass

        return self

    # Build Methods

    def build(self) -> TelemetryFlowClient:
        """
        Build the TelemetryFlow client.

        Returns:
            Configured TelemetryFlowClient instance

        Raises:
            BuilderError: If configuration is invalid
        """
        self._validate()

        if self._errors:
            raise BuilderError("; ".join(self._errors))

        # Create credentials
        try:
            credentials = Credentials.create(
                key_id=self._api_key_id or "",
                key_secret=self._api_key_secret or "",
            )
        except CredentialsError as e:
            raise BuilderError(str(e)) from e

        # Create configuration
        config = TelemetryConfig(
            credentials=credentials,
            endpoint=self._endpoint,
            service_name=self._service_name or "",
            protocol=self._protocol,
            insecure=self._insecure,
            timeout=self._timeout,
            compression=self._compression,
            retry_enabled=self._retry_enabled,
            max_retries=self._max_retries,
            retry_backoff=self._retry_backoff,
            enable_metrics=self._enable_metrics,
            enable_logs=self._enable_logs,
            enable_traces=self._enable_traces,
            exemplars_enabled=self._exemplars_enabled,
            service_version=self._service_version,
            service_namespace=self._service_namespace,
            environment=self._environment,
            custom_attributes=self._custom_attributes,
            batch_timeout=self._batch_timeout,
            batch_max_size=self._batch_max_size,
            collector_id=self._collector_id,
            rate_limit=self._rate_limit,
        )

        return TelemetryFlowClient(config)

    def must_build(self) -> TelemetryFlowClient:
        """
        Build the client, raising an exception on failure.

        This is an alias for build() that makes intent clearer.

        Returns:
            Configured TelemetryFlowClient instance

        Raises:
            BuilderError: If configuration is invalid
        """
        return self.build()

    def _validate(self) -> None:
        """Validate the configuration."""
        self._errors = []

        if not self._api_key_id:
            self._errors.append("API key ID is required")
        if not self._api_key_secret:
            self._errors.append("API key secret is required")
        if not self._endpoint:
            self._errors.append("Endpoint is required")
        if not self._service_name:
            self._errors.append("Service name is required")


# Convenience functions


def new_builder() -> TelemetryFlowBuilder:
    """Create a new TelemetryFlow builder."""
    return TelemetryFlowBuilder()


def new_from_env() -> TelemetryFlowClient:
    """Create a new client from environment variables."""
    return TelemetryFlowBuilder().with_auto_configuration().build()


def must_new_from_env() -> TelemetryFlowClient:
    """Create a new client from environment variables, raising on failure."""
    return new_from_env()


def new_simple(
    api_key_id: str,
    api_key_secret: str,
    endpoint: str,
    service_name: str,
) -> TelemetryFlowClient:
    """Create a new client with minimal configuration."""
    return (
        TelemetryFlowBuilder()
        .with_api_key(api_key_id, api_key_secret)
        .with_endpoint(endpoint)
        .with_service(service_name)
        .build()
    )


def must_new_simple(
    api_key_id: str,
    api_key_secret: str,
    endpoint: str,
    service_name: str,
) -> TelemetryFlowClient:
    """Create a new client with minimal configuration, raising on failure."""
    return new_simple(api_key_id, api_key_secret, endpoint, service_name)
