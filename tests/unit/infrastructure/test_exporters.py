"""Unit tests for the OTLP exporter factory."""

from datetime import timedelta
from unittest import mock

import pytest
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

from telemetryflow.domain.config import Protocol, TelemetryConfig
from telemetryflow.domain.credentials import Credentials
from telemetryflow.infrastructure.exporters import OTLPExporterFactory


@pytest.fixture
def valid_credentials() -> Credentials:
    """Create valid credentials for testing."""
    return Credentials.create("tfk_test_key", "tfs_test_secret")


@pytest.fixture
def grpc_config(valid_credentials: Credentials) -> TelemetryConfig:
    """Create gRPC config for testing."""
    return TelemetryConfig(
        credentials=valid_credentials,
        endpoint="localhost:4317",
        service_name="test-service",
        protocol=Protocol.GRPC,
    )


@pytest.fixture
def http_config(valid_credentials: Credentials) -> TelemetryConfig:
    """Create HTTP config for testing."""
    return TelemetryConfig(
        credentials=valid_credentials,
        endpoint="http://localhost:4318",
        service_name="test-service",
        protocol=Protocol.HTTP,
    )


class TestOTLPExporterFactoryInit:
    """Tests for OTLPExporterFactory initialization."""

    def test_init(self, grpc_config: TelemetryConfig) -> None:
        """Test factory initialization."""
        factory = OTLPExporterFactory(grpc_config)

        assert factory._config == grpc_config
        assert factory._headers is not None

    def test_builds_headers(self, grpc_config: TelemetryConfig) -> None:
        """Test that headers are built on initialization."""
        factory = OTLPExporterFactory(grpc_config)

        headers = factory.get_headers()
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/x-protobuf"

    def test_includes_auth_headers(self, grpc_config: TelemetryConfig) -> None:
        """Test that auth headers are included."""
        factory = OTLPExporterFactory(grpc_config)

        headers = factory.get_headers()
        # Auth headers should be present (from credentials)
        assert len(headers) > 1  # At least Content-Type + auth


class TestCreateResource:
    """Tests for create_resource method."""

    def test_creates_resource(self, grpc_config: TelemetryConfig) -> None:
        """Test that a Resource is created."""
        factory = OTLPExporterFactory(grpc_config)

        resource = factory.create_resource()

        assert isinstance(resource, Resource)

    def test_resource_has_service_name(self, grpc_config: TelemetryConfig) -> None:
        """Test that resource has service name."""
        factory = OTLPExporterFactory(grpc_config)

        resource = factory.create_resource()

        assert resource.attributes.get("service.name") == "test-service"


class TestCreateTraceExporter:
    """Tests for create_trace_exporter method."""

    def test_creates_grpc_exporter_for_grpc_protocol(self, grpc_config: TelemetryConfig) -> None:
        """Test that gRPC exporter is created for gRPC protocol."""
        factory = OTLPExporterFactory(grpc_config)

        exporter = factory.create_trace_exporter()

        assert isinstance(exporter, OTLPSpanExporter)


class TestCreateMetricExporter:
    """Tests for create_metric_exporter method."""

    def test_creates_grpc_exporter_for_grpc_protocol(self, grpc_config: TelemetryConfig) -> None:
        """Test that gRPC metric exporter is created for gRPC protocol."""
        factory = OTLPExporterFactory(grpc_config)

        exporter = factory.create_metric_exporter()

        assert isinstance(exporter, OTLPMetricExporter)


class TestGrpcTraceExporter:
    """Tests for gRPC trace exporter creation."""

    def test_uses_endpoint(self, valid_credentials: Credentials) -> None:
        """Test that endpoint is used."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="custom-host:4317",
            service_name="test",
            protocol=Protocol.GRPC,
        )
        factory = OTLPExporterFactory(config)

        with mock.patch("telemetryflow.infrastructure.exporters.OTLPSpanExporter") as mock_exporter:
            factory._create_grpc_trace_exporter()

            call_kwargs = mock_exporter.call_args[1]
            assert call_kwargs["endpoint"] == "custom-host:4317"

    def test_uses_timeout(self, valid_credentials: Credentials) -> None:
        """Test that timeout is used."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test",
            protocol=Protocol.GRPC,
            timeout=timedelta(seconds=60),
        )
        factory = OTLPExporterFactory(config)

        with mock.patch("telemetryflow.infrastructure.exporters.OTLPSpanExporter") as mock_exporter:
            factory._create_grpc_trace_exporter()

            call_kwargs = mock_exporter.call_args[1]
            assert call_kwargs["timeout"] == 60

    def test_sets_insecure_flag(self, valid_credentials: Credentials) -> None:
        """Test that insecure flag is set."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test",
            protocol=Protocol.GRPC,
            insecure=True,
        )
        factory = OTLPExporterFactory(config)

        with mock.patch("telemetryflow.infrastructure.exporters.OTLPSpanExporter") as mock_exporter:
            factory._create_grpc_trace_exporter()

            call_kwargs = mock_exporter.call_args[1]
            assert call_kwargs["insecure"] is True

    def test_adds_compression_when_enabled(self, valid_credentials: Credentials) -> None:
        """Test that compression is added when enabled."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test",
            protocol=Protocol.GRPC,
            compression=True,
        )
        factory = OTLPExporterFactory(config)

        with mock.patch("telemetryflow.infrastructure.exporters.OTLPSpanExporter") as mock_exporter:
            factory._create_grpc_trace_exporter()

            call_kwargs = mock_exporter.call_args[1]
            assert "compression" in call_kwargs


class TestGrpcMetricExporter:
    """Tests for gRPC metric exporter creation."""

    def test_uses_endpoint(self, valid_credentials: Credentials) -> None:
        """Test that endpoint is used."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="metrics-host:4317",
            service_name="test",
            protocol=Protocol.GRPC,
        )
        factory = OTLPExporterFactory(config)

        with mock.patch(
            "telemetryflow.infrastructure.exporters.OTLPMetricExporter"
        ) as mock_exporter:
            factory._create_grpc_metric_exporter()

            call_kwargs = mock_exporter.call_args[1]
            assert call_kwargs["endpoint"] == "metrics-host:4317"

    def test_adds_compression_when_enabled(self, valid_credentials: Credentials) -> None:
        """Test that compression is added when enabled."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="localhost:4317",
            service_name="test",
            protocol=Protocol.GRPC,
            compression=True,
        )
        factory = OTLPExporterFactory(config)

        with mock.patch(
            "telemetryflow.infrastructure.exporters.OTLPMetricExporter"
        ) as mock_exporter:
            factory._create_grpc_metric_exporter()

            call_kwargs = mock_exporter.call_args[1]
            assert "compression" in call_kwargs


class TestGetHttpEndpoint:
    """Tests for _get_http_endpoint method."""

    def test_appends_path(self, http_config: TelemetryConfig) -> None:
        """Test that path is appended."""
        factory = OTLPExporterFactory(http_config)

        endpoint = factory._get_http_endpoint("/v1/traces")

        assert endpoint.endswith("/v1/traces")

    def test_removes_trailing_slash(self, valid_credentials: Credentials) -> None:
        """Test that trailing slash is removed from base."""
        config = TelemetryConfig(
            credentials=valid_credentials,
            endpoint="http://localhost:4318/",
            service_name="test",
            protocol=Protocol.HTTP,
        )
        factory = OTLPExporterFactory(config)

        endpoint = factory._get_http_endpoint("/v1/traces")

        assert "//v1" not in endpoint


class TestCreateExporterDispatch:
    """Tests for exporter creation dispatch logic."""

    def test_create_trace_exporter_http(self, http_config: TelemetryConfig) -> None:
        """Test that HTTP trace exporter is created for HTTP protocol."""
        factory = OTLPExporterFactory(http_config)

        with mock.patch.object(factory, "_create_http_trace_exporter") as mock_create:
            mock_create.return_value = mock.Mock()
            factory.create_trace_exporter()

            mock_create.assert_called_once()

    def test_create_metric_exporter_http(self, http_config: TelemetryConfig) -> None:
        """Test that HTTP metric exporter is created for HTTP protocol."""
        factory = OTLPExporterFactory(http_config)

        with mock.patch.object(factory, "_create_http_metric_exporter") as mock_create:
            mock_create.return_value = mock.Mock()
            factory.create_metric_exporter()

            mock_create.assert_called_once()


class TestGetHeaders:
    """Tests for get_headers method."""

    def test_returns_copy(self, grpc_config: TelemetryConfig) -> None:
        """Test that a copy of headers is returned."""
        factory = OTLPExporterFactory(grpc_config)

        headers1 = factory.get_headers()
        headers2 = factory.get_headers()

        assert headers1 == headers2
        assert headers1 is not headers2

    def test_modifications_dont_affect_original(self, grpc_config: TelemetryConfig) -> None:
        """Test that modifications to returned headers don't affect original."""
        factory = OTLPExporterFactory(grpc_config)

        headers = factory.get_headers()
        headers["X-Custom"] = "value"

        assert "X-Custom" not in factory.get_headers()


class TestGetGrpcHeaders:
    """Tests for _get_grpc_headers method."""

    def test_returns_tuple_of_tuples(self, grpc_config: TelemetryConfig) -> None:
        """Test that gRPC headers are returned as tuple of tuples."""
        factory = OTLPExporterFactory(grpc_config)

        headers = factory._get_grpc_headers()

        assert isinstance(headers, tuple)
        assert all(isinstance(h, tuple) for h in headers)

    def test_lowercases_header_keys(self, grpc_config: TelemetryConfig) -> None:
        """Test that header keys are lowercased for gRPC."""
        factory = OTLPExporterFactory(grpc_config)

        headers = factory._get_grpc_headers()

        # Check all keys are lowercase
        for key, _value in headers:
            assert key == key.lower(), f"Header key '{key}' is not lowercase"

    def test_preserves_header_values(self, grpc_config: TelemetryConfig) -> None:
        """Test that header values are preserved."""
        factory = OTLPExporterFactory(grpc_config)

        grpc_headers = factory._get_grpc_headers()
        http_headers = factory.get_headers()

        # Values should match (comparing lowercase keys)
        grpc_dict = dict(grpc_headers)
        for key, value in http_headers.items():
            assert grpc_dict.get(key.lower()) == value

    def test_includes_content_type(self, grpc_config: TelemetryConfig) -> None:
        """Test that content-type is included with lowercase key."""
        factory = OTLPExporterFactory(grpc_config)

        headers = factory._get_grpc_headers()
        headers_dict = dict(headers)

        assert "content-type" in headers_dict
        assert headers_dict["content-type"] == "application/x-protobuf"

    def test_includes_authorization(self, grpc_config: TelemetryConfig) -> None:
        """Test that authorization header is included with lowercase key."""
        factory = OTLPExporterFactory(grpc_config)

        headers = factory._get_grpc_headers()
        headers_dict = dict(headers)

        assert "authorization" in headers_dict
        assert "Bearer" in headers_dict["authorization"]
