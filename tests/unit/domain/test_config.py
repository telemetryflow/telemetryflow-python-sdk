"""Unit tests for TelemetryConfig."""

from datetime import timedelta

import pytest

from telemetryflow.domain.config import (
    ConfigError,
    Protocol,
    SignalType,
    TelemetryConfig,
)
from telemetryflow.domain.credentials import Credentials


@pytest.fixture
def valid_credentials() -> Credentials:
    """Create valid credentials for testing."""
    return Credentials.create("tfk_test_key", "tfs_test_secret")


class TestTelemetryConfig:
    """Test suite for TelemetryConfig class."""

    def test_create_valid_config(self, valid_credentials: Credentials) -> None:
        """Test creating valid configuration."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
        )

        assert config.credentials == valid_credentials
        assert config.endpoint == "localhost:4317"
        assert config.service_name == "test-service"

    def test_default_values(self, valid_credentials: Credentials) -> None:
        """Test default configuration values."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
        )

        assert config.protocol == Protocol.GRPC
        assert config.insecure is False
        assert config.timeout == timedelta(seconds=30)
        assert config.compression is True
        assert config.retry_enabled is True
        assert config.max_retries == 3
        assert config.enable_metrics is True
        assert config.enable_logs is True
        assert config.enable_traces is True
        assert config.exemplars_enabled is True
        assert config.service_version == "1.0.0"
        assert config.service_namespace == "telemetryflow"
        assert config.environment == "production"
        assert config.batch_max_size == 512

    def test_empty_endpoint_raises_error(self, valid_credentials: Credentials) -> None:
        """Test that empty endpoint raises ConfigError."""
        with pytest.raises(ConfigError, match="Endpoint is required"):
            TelemetryConfig(
                credentials=valid_credentials,
                endpoint="",
                service_name="test-service",
            )

    def test_empty_service_name_raises_error(self, valid_credentials: Credentials) -> None:
        """Test that empty service name raises ConfigError."""
        with pytest.raises(ConfigError, match="Service name is required"):
            TelemetryConfig(
                credentials=valid_credentials,
                endpoint="localhost:4317",
                service_name="",
            )

    def test_negative_timeout_raises_error(self, valid_credentials: Credentials) -> None:
        """Test that negative timeout raises ConfigError."""
        with pytest.raises(ConfigError, match="Timeout must be positive"):
            TelemetryConfig(
                credentials=valid_credentials,
                endpoint="localhost:4317",
                service_name="test-service",
                timeout=timedelta(seconds=-1),
            )

    def test_negative_max_retries_raises_error(self, valid_credentials: Credentials) -> None:
        """Test that negative max retries raises ConfigError."""
        with pytest.raises(ConfigError, match="Max retries must be non-negative"):
            TelemetryConfig(
                credentials=valid_credentials,
                endpoint="localhost:4317",
                service_name="test-service",
                max_retries=-1,
            )

    def test_zero_batch_size_raises_error(self, valid_credentials: Credentials) -> None:
        """Test that zero batch size raises ConfigError."""
        with pytest.raises(ConfigError, match="Batch max size must be positive"):
            TelemetryConfig(
                credentials=valid_credentials,
                endpoint="localhost:4317",
                service_name="test-service",
                batch_max_size=0,
            )

    def test_with_protocol(self, valid_credentials: Credentials) -> None:
        """Test with_protocol method."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
        )

        config.with_protocol(Protocol.HTTP)
        assert config.protocol == Protocol.HTTP

        config.with_protocol(Protocol.GRPC)
        assert config.protocol == Protocol.GRPC

    def test_with_grpc(self, valid_credentials: Credentials) -> None:
        """Test with_grpc method."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
            protocol=Protocol.HTTP,
        )

        config.with_grpc()
        assert config.protocol == Protocol.GRPC

    def test_with_http(self, valid_credentials: Credentials) -> None:
        """Test with_http method."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
        )

        config.with_http()
        assert config.protocol == Protocol.HTTP

    def test_with_signals(self, valid_credentials: Credentials) -> None:
        """Test with_signals method."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
        )

        config.with_signals(metrics=True, logs=False, traces=True)

        assert config.enable_metrics is True
        assert config.enable_logs is False
        assert config.enable_traces is True

    def test_with_metrics_only(self, valid_credentials: Credentials) -> None:
        """Test with_metrics_only method."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
        )

        config.with_metrics_only()

        assert config.enable_metrics is True
        assert config.enable_logs is False
        assert config.enable_traces is False

    def test_with_logs_only(self, valid_credentials: Credentials) -> None:
        """Test with_logs_only method."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
        )

        config.with_logs_only()

        assert config.enable_metrics is False
        assert config.enable_logs is True
        assert config.enable_traces is False

    def test_with_traces_only(self, valid_credentials: Credentials) -> None:
        """Test with_traces_only method."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
        )

        config.with_traces_only()

        assert config.enable_metrics is False
        assert config.enable_logs is False
        assert config.enable_traces is True

    def test_with_exemplars(self, valid_credentials: Credentials) -> None:
        """Test with_exemplars method."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
        )

        config.with_exemplars(False)
        assert config.exemplars_enabled is False

        config.with_exemplars(True)
        assert config.exemplars_enabled is True

    def test_with_environment(self, valid_credentials: Credentials) -> None:
        """Test with_environment method."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
        )

        config.with_environment("staging")
        assert config.environment == "staging"

    def test_with_collector_id(self, valid_credentials: Credentials) -> None:
        """Test with_collector_id method."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
        )

        config.with_collector_id("collector-1")
        assert config.collector_id == "collector-1"

    def test_with_custom_attribute(self, valid_credentials: Credentials) -> None:
        """Test with_custom_attribute method."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
        )

        config.with_custom_attribute("team", "platform")
        assert config.custom_attributes["team"] == "platform"

    def test_with_custom_attributes(self, valid_credentials: Credentials) -> None:
        """Test with_custom_attributes method."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
        )

        config.with_custom_attributes({"team": "platform", "region": "us-east"})

        assert config.custom_attributes["team"] == "platform"
        assert config.custom_attributes["region"] == "us-east"

    def test_get_endpoint_url_grpc(self, valid_credentials: Credentials) -> None:
        """Test get_endpoint_url for gRPC."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
            protocol=Protocol.GRPC,
        )

        assert config.get_endpoint_url() == "localhost:4317"

    def test_get_endpoint_url_http(self, valid_credentials: Credentials) -> None:
        """Test get_endpoint_url for HTTP."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4318",
            service_name="test-service",
            protocol=Protocol.HTTP,
            insecure=False,
        )

        assert config.get_endpoint_url() == "https://localhost:4318"

    def test_get_endpoint_url_http_insecure(self, valid_credentials: Credentials) -> None:
        """Test get_endpoint_url for HTTP insecure."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4318",
            service_name="test-service",
            protocol=Protocol.HTTP,
            insecure=True,
        )

        assert config.get_endpoint_url() == "http://localhost:4318"

    def test_get_enabled_signals(self, valid_credentials: Credentials) -> None:
        """Test get_enabled_signals method."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
        )

        signals = config.get_enabled_signals()

        assert SignalType.METRICS in signals
        assert SignalType.LOGS in signals
        assert SignalType.TRACES in signals

    def test_get_enabled_signals_metrics_only(self, valid_credentials: Credentials) -> None:
        """Test get_enabled_signals with metrics only."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
        ).with_metrics_only()

        signals = config.get_enabled_signals()

        assert signals == [SignalType.METRICS]

    def test_get_auth_headers(self, valid_credentials: Credentials) -> None:
        """Test get_auth_headers method."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
        )

        headers = config.get_auth_headers()

        assert "Authorization" in headers
        assert "X-TelemetryFlow-Key-ID" in headers
        assert "X-TelemetryFlow-Key-Secret" in headers

    def test_get_auth_headers_with_collector_id(self, valid_credentials: Credentials) -> None:
        """Test get_auth_headers with collector ID."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
        ).with_collector_id("collector-1")

        headers = config.get_auth_headers()

        assert headers["X-TelemetryFlow-Collector-ID"] == "collector-1"

    def test_get_resource_attributes(self, valid_credentials: Credentials) -> None:
        """Test get_resource_attributes method."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
            service_version="2.0.0",
            environment="staging",
        ).with_custom_attribute("team", "platform")

        attrs = config.get_resource_attributes()

        assert attrs["service.name"] == "test-service"
        assert attrs["service.version"] == "2.0.0"
        assert attrs["deployment.environment"] == "staging"
        assert attrs["team"] == "platform"

    def test_is_signal_enabled(self, valid_credentials: Credentials) -> None:
        """Test is_signal_enabled method."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test-service",
        ).with_metrics_only()

        assert config.is_signal_enabled(SignalType.METRICS) is True
        assert config.is_signal_enabled(SignalType.LOGS) is False
        assert config.is_signal_enabled(SignalType.TRACES) is False

    def test_method_chaining(self, valid_credentials: Credentials) -> None:
        """Test method chaining."""
        config = (
            TelemetryConfig(
                credentials=valid_credentials,
                endpoint="localhost:4317",
                service_name="test-service",
            )
            .with_grpc()
            .with_insecure(True)
            .with_environment("staging")
            .with_collector_id("collector-1")
            .with_exemplars(False)
        )

        assert config.protocol == Protocol.GRPC
        assert config.insecure is True
        assert config.environment == "staging"
        assert config.collector_id == "collector-1"
        assert config.exemplars_enabled is False


class TestProtocol:
    """Test suite for Protocol enum."""

    def test_protocol_values(self) -> None:
        """Test Protocol enum values."""
        assert Protocol.GRPC.value == "grpc"
        assert Protocol.HTTP.value == "http"


class TestSignalType:
    """Test suite for SignalType enum."""

    def test_signal_type_values(self) -> None:
        """Test SignalType enum values."""
        assert SignalType.METRICS.value == "metrics"
        assert SignalType.LOGS.value == "logs"
        assert SignalType.TRACES.value == "traces"
