"""Unit tests for TelemetryFlowBuilder."""

import os
from datetime import timedelta
from unittest import mock

import pytest

from telemetryflow.builder import (
    BuilderError,
    TelemetryFlowBuilder,
    must_new_from_env,
    must_new_simple,
    new_builder,
    new_from_env,
    new_simple,
)
from telemetryflow.domain.config import Protocol


class TestTelemetryFlowBuilder:
    """Test suite for TelemetryFlowBuilder."""

    def test_create_builder(self) -> None:
        """Test creating a builder with default values."""
        builder = TelemetryFlowBuilder()

        assert builder._endpoint == TelemetryFlowBuilder.DEFAULT_ENDPOINT
        assert builder._service_version == TelemetryFlowBuilder.DEFAULT_SERVICE_VERSION
        assert builder._protocol == Protocol.GRPC
        assert builder._enable_metrics is True
        assert builder._enable_logs is True
        assert builder._enable_traces is True

    def test_with_api_key(self) -> None:
        """Test setting API key."""
        builder = TelemetryFlowBuilder().with_api_key("tfk_key", "tfs_secret")

        assert builder._api_key_id == "tfk_key"
        assert builder._api_key_secret == "tfs_secret"

    def test_with_endpoint(self) -> None:
        """Test setting endpoint."""
        builder = TelemetryFlowBuilder().with_endpoint("localhost:4317")

        assert builder._endpoint == "localhost:4317"

    def test_with_service(self) -> None:
        """Test setting service name and version."""
        builder = TelemetryFlowBuilder().with_service("my-service", "2.0.0")

        assert builder._service_name == "my-service"
        assert builder._service_version == "2.0.0"

    def test_with_service_name_only(self) -> None:
        """Test setting service name without version."""
        builder = TelemetryFlowBuilder().with_service("my-service")

        assert builder._service_name == "my-service"
        assert builder._service_version == TelemetryFlowBuilder.DEFAULT_SERVICE_VERSION

    def test_with_environment(self) -> None:
        """Test setting environment."""
        builder = TelemetryFlowBuilder().with_environment("staging")

        assert builder._environment == "staging"

    def test_with_protocol(self) -> None:
        """Test setting protocol."""
        builder = TelemetryFlowBuilder().with_protocol(Protocol.HTTP)

        assert builder._protocol == Protocol.HTTP

    def test_with_grpc(self) -> None:
        """Test with_grpc shorthand."""
        builder = TelemetryFlowBuilder().with_http().with_grpc()

        assert builder._protocol == Protocol.GRPC

    def test_with_http(self) -> None:
        """Test with_http shorthand."""
        builder = TelemetryFlowBuilder().with_http()

        assert builder._protocol == Protocol.HTTP

    def test_with_insecure(self) -> None:
        """Test setting insecure flag."""
        builder = TelemetryFlowBuilder().with_insecure(True)

        assert builder._insecure is True

    def test_with_signals(self) -> None:
        """Test setting signal configuration."""
        builder = TelemetryFlowBuilder().with_signals(metrics=True, logs=False, traces=True)

        assert builder._enable_metrics is True
        assert builder._enable_logs is False
        assert builder._enable_traces is True

    def test_with_metrics_only(self) -> None:
        """Test with_metrics_only shorthand."""
        builder = TelemetryFlowBuilder().with_metrics_only()

        assert builder._enable_metrics is True
        assert builder._enable_logs is False
        assert builder._enable_traces is False

    def test_with_logs_only(self) -> None:
        """Test with_logs_only shorthand."""
        builder = TelemetryFlowBuilder().with_logs_only()

        assert builder._enable_metrics is False
        assert builder._enable_logs is True
        assert builder._enable_traces is False

    def test_with_traces_only(self) -> None:
        """Test with_traces_only shorthand."""
        builder = TelemetryFlowBuilder().with_traces_only()

        assert builder._enable_metrics is False
        assert builder._enable_logs is False
        assert builder._enable_traces is True

    def test_with_exemplars(self) -> None:
        """Test setting exemplars flag."""
        builder = TelemetryFlowBuilder().with_exemplars(False)

        assert builder._exemplars_enabled is False

    def test_with_timeout(self) -> None:
        """Test setting timeout."""
        builder = TelemetryFlowBuilder().with_timeout(timedelta(seconds=60))

        assert builder._timeout == timedelta(seconds=60)

    def test_with_collector_id(self) -> None:
        """Test setting collector ID."""
        builder = TelemetryFlowBuilder().with_collector_id("collector-1")

        assert builder._collector_id == "collector-1"

    def test_with_custom_attribute(self) -> None:
        """Test adding custom attribute."""
        builder = TelemetryFlowBuilder().with_custom_attribute("team", "platform")

        assert builder._custom_attributes["team"] == "platform"

    def test_with_custom_attributes(self) -> None:
        """Test adding multiple custom attributes."""
        builder = TelemetryFlowBuilder().with_custom_attributes(
            {"team": "platform", "region": "us-east"}
        )

        assert builder._custom_attributes["team"] == "platform"
        assert builder._custom_attributes["region"] == "us-east"

    def test_with_compression(self) -> None:
        """Test setting compression flag."""
        builder = TelemetryFlowBuilder().with_compression(False)

        assert builder._compression is False

    def test_with_retry(self) -> None:
        """Test setting retry configuration."""
        builder = TelemetryFlowBuilder().with_retry(
            enabled=True, max_retries=5, backoff=timedelta(seconds=10)
        )

        assert builder._retry_enabled is True
        assert builder._max_retries == 5
        assert builder._retry_backoff == timedelta(seconds=10)

    def test_with_batch_settings(self) -> None:
        """Test setting batch configuration."""
        builder = TelemetryFlowBuilder().with_batch_settings(
            timeout=timedelta(seconds=15), max_size=1024
        )

        assert builder._batch_timeout == timedelta(seconds=15)
        assert builder._batch_max_size == 1024

    def test_with_rate_limit(self) -> None:
        """Test setting rate limit."""
        builder = TelemetryFlowBuilder().with_rate_limit(500)

        assert builder._rate_limit == 500

    def test_with_service_namespace(self) -> None:
        """Test setting service namespace."""
        builder = TelemetryFlowBuilder().with_service_namespace("my-namespace")

        assert builder._service_namespace == "my-namespace"

    def test_method_chaining(self) -> None:
        """Test method chaining."""
        builder = (
            TelemetryFlowBuilder()
            .with_api_key("tfk_key", "tfs_secret")
            .with_endpoint("localhost:4317")
            .with_service("my-service", "1.0.0")
            .with_environment("production")
            .with_grpc()
            .with_insecure(False)
            .with_signals(metrics=True, logs=True, traces=True)
            .with_collector_id("collector-1")
            .with_custom_attribute("team", "platform")
        )

        assert builder._api_key_id == "tfk_key"
        assert builder._endpoint == "localhost:4317"
        assert builder._service_name == "my-service"
        assert builder._environment == "production"
        assert builder._protocol == Protocol.GRPC
        assert builder._collector_id == "collector-1"

    def test_build_success(self) -> None:
        """Test successful build."""
        client = (
            TelemetryFlowBuilder()
            .with_api_key("tfk_key", "tfs_secret")
            .with_endpoint("localhost:4317")
            .with_service("my-service")
            .build()
        )

        assert client is not None
        assert client.config.service_name == "my-service"
        assert client.config.endpoint == "localhost:4317"

    def test_build_missing_api_key_id(self) -> None:
        """Test build fails without API key ID."""
        with pytest.raises(BuilderError, match="API key ID is required"):
            (
                TelemetryFlowBuilder()
                .with_api_key("", "tfs_secret")
                .with_endpoint("localhost:4317")
                .with_service("my-service")
                .build()
            )

    def test_build_missing_api_key_secret(self) -> None:
        """Test build fails without API key secret."""
        with pytest.raises(BuilderError, match="API key secret is required"):
            (
                TelemetryFlowBuilder()
                .with_api_key("tfk_key", "")
                .with_endpoint("localhost:4317")
                .with_service("my-service")
                .build()
            )

    def test_build_missing_service_name(self) -> None:
        """Test build fails without service name."""
        with pytest.raises(BuilderError, match="Service name is required"):
            (
                TelemetryFlowBuilder()
                .with_api_key("tfk_key", "tfs_secret")
                .with_endpoint("localhost:4317")
                .build()
            )

    def test_must_build(self) -> None:
        """Test must_build method."""
        client = (
            TelemetryFlowBuilder()
            .with_api_key("tfk_key", "tfs_secret")
            .with_endpoint("localhost:4317")
            .with_service("my-service")
            .must_build()
        )

        assert client is not None


class TestBuilderEnvironmentVariables:
    """Test suite for environment variable loading."""

    def test_with_api_key_from_env(self) -> None:
        """Test loading API key from environment."""
        with mock.patch.dict(
            os.environ,
            {
                "TELEMETRYFLOW_API_KEY_ID": "tfk_env_key",
                "TELEMETRYFLOW_API_KEY_SECRET": "tfs_env_secret",
            },
        ):
            builder = TelemetryFlowBuilder().with_api_key_from_env()

            assert builder._api_key_id == "tfk_env_key"
            assert builder._api_key_secret == "tfs_env_secret"

    def test_with_endpoint_from_env(self) -> None:
        """Test loading endpoint from environment."""
        with mock.patch.dict(os.environ, {"TELEMETRYFLOW_ENDPOINT": "custom.endpoint:4317"}):
            builder = TelemetryFlowBuilder().with_endpoint_from_env()

            assert builder._endpoint == "custom.endpoint:4317"

    def test_with_endpoint_from_env_default(self) -> None:
        """Test loading endpoint falls back to default."""
        with mock.patch.dict(os.environ, {}, clear=True):
            # Remove the env var if it exists
            os.environ.pop("TELEMETRYFLOW_ENDPOINT", None)
            builder = TelemetryFlowBuilder().with_endpoint_from_env()

            assert builder._endpoint == TelemetryFlowBuilder.DEFAULT_ENDPOINT

    def test_with_service_from_env(self) -> None:
        """Test loading service config from environment."""
        with mock.patch.dict(
            os.environ,
            {
                "TELEMETRYFLOW_SERVICE_NAME": "env-service",
                "TELEMETRYFLOW_SERVICE_VERSION": "2.0.0",
            },
        ):
            builder = TelemetryFlowBuilder().with_service_from_env()

            assert builder._service_name == "env-service"
            assert builder._service_version == "2.0.0"

    def test_with_environment_from_env(self) -> None:
        """Test loading environment from environment variable."""
        with mock.patch.dict(os.environ, {"TELEMETRYFLOW_ENVIRONMENT": "staging"}):
            builder = TelemetryFlowBuilder().with_environment_from_env()

            assert builder._environment == "staging"

    def test_with_environment_from_env_fallback(self) -> None:
        """Test environment falls back to ENV variable."""
        with mock.patch.dict(os.environ, {"ENV": "development"}, clear=True):
            os.environ.pop("TELEMETRYFLOW_ENVIRONMENT", None)
            builder = TelemetryFlowBuilder().with_environment_from_env()

            assert builder._environment == "development"

    def test_with_collector_id_from_env(self) -> None:
        """Test loading collector ID from environment."""
        with mock.patch.dict(os.environ, {"TELEMETRYFLOW_COLLECTOR_ID": "collector-env"}):
            builder = TelemetryFlowBuilder().with_collector_id_from_env()

            assert builder._collector_id == "collector-env"

    def test_with_auto_configuration(self) -> None:
        """Test auto configuration from environment."""
        with mock.patch.dict(
            os.environ,
            {
                "TELEMETRYFLOW_API_KEY_ID": "tfk_auto",
                "TELEMETRYFLOW_API_KEY_SECRET": "tfs_auto",
                "TELEMETRYFLOW_SERVICE_NAME": "auto-service",
                "TELEMETRYFLOW_ENVIRONMENT": "auto-env",
            },
        ):
            builder = TelemetryFlowBuilder().with_auto_configuration()

            assert builder._api_key_id == "tfk_auto"
            assert builder._api_key_secret == "tfs_auto"
            assert builder._service_name == "auto-service"
            assert builder._environment == "auto-env"


class TestConvenienceFunctions:
    """Test suite for convenience functions."""

    def test_new_builder(self) -> None:
        """Test new_builder function."""
        builder = new_builder()

        assert isinstance(builder, TelemetryFlowBuilder)

    def test_new_simple(self) -> None:
        """Test new_simple function."""
        client = new_simple("tfk_key", "tfs_secret", "localhost:4317", "my-service")

        assert client.config.service_name == "my-service"

    def test_must_new_simple(self) -> None:
        """Test must_new_simple function."""
        client = must_new_simple("tfk_key", "tfs_secret", "localhost:4317", "my-service")

        assert client.config.service_name == "my-service"

    def test_new_from_env(self) -> None:
        """Test new_from_env function."""
        with mock.patch.dict(
            os.environ,
            {
                "TELEMETRYFLOW_API_KEY_ID": "tfk_env",
                "TELEMETRYFLOW_API_KEY_SECRET": "tfs_env",
                "TELEMETRYFLOW_SERVICE_NAME": "env-service",
            },
        ):
            client = new_from_env()

            assert client.config.service_name == "env-service"

    def test_must_new_from_env(self) -> None:
        """Test must_new_from_env function."""
        with mock.patch.dict(
            os.environ,
            {
                "TELEMETRYFLOW_API_KEY_ID": "tfk_env",
                "TELEMETRYFLOW_API_KEY_SECRET": "tfs_env",
                "TELEMETRYFLOW_SERVICE_NAME": "env-service",
            },
        ):
            client = must_new_from_env()

            assert client.config.service_name == "env-service"
