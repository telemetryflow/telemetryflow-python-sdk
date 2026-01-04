"""Unit tests for TelemetryFlow Native Generator (telemetryflow-gen)."""

import tempfile
from pathlib import Path

import pytest

from telemetryflow.cli.generator import (
    TemplateData,
    get_template_dir,
    load_template,
    main,
    render_template,
    render_template_file,
)


class TestTemplateData:
    """Test suite for TemplateData."""

    def test_create_template_data(self) -> None:
        """Test creating template data with defaults."""
        data = TemplateData(
            api_key_id="tfk_test",
            api_key_secret="tfs_test",
            service_name="test-service",
        )

        assert data.api_key_id == "tfk_test"
        assert data.api_key_secret == "tfs_test"
        assert data.service_name == "test-service"
        assert data.service_version == "1.0.0"
        assert data.environment == "production"
        assert data.endpoint == "localhost:4317"
        assert data.enable_metrics is True
        assert data.enable_logs is True
        assert data.enable_traces is True
        # TFO v2 API defaults
        assert data.use_v2_api is True
        assert data.v2_only is False
        assert data.collector_name == "TelemetryFlow Python SDK"
        assert data.datacenter == "default"
        assert data.enrich_resources is True
        assert data.protocol == "grpc"

    def test_template_data_custom_values(self) -> None:
        """Test creating template data with custom values."""
        data = TemplateData(
            api_key_id="tfk_custom",
            api_key_secret="tfs_custom",
            service_name="custom-service",
            service_version="2.0.0",
            environment="staging",
            endpoint="custom.endpoint:4317",
            enable_metrics=False,
            enable_logs=True,
            enable_traces=False,
        )

        assert data.service_version == "2.0.0"
        assert data.environment == "staging"
        assert data.endpoint == "custom.endpoint:4317"
        assert data.enable_metrics is False
        assert data.enable_traces is False

    def test_template_data_v2_api_settings(self) -> None:
        """Test TFO v2 API configuration settings."""
        data = TemplateData(
            api_key_id="tfk_v2",
            api_key_secret="tfs_v2",
            service_name="v2-service",
            use_v2_api=True,
            v2_only=True,
            collector_name="My Custom Collector",
            datacenter="us-east-1",
            enrich_resources=False,
            protocol="http",
        )

        assert data.use_v2_api is True
        assert data.v2_only is True
        assert data.collector_name == "My Custom Collector"
        assert data.datacenter == "us-east-1"
        assert data.enrich_resources is False
        assert data.protocol == "http"

    def test_template_data_to_dict(self) -> None:
        """Test converting template data to dictionary."""
        data = TemplateData(
            api_key_id="tfk_test",
            api_key_secret="tfs_test",
            service_name="test-service",
        )
        result = data.to_dict()

        assert isinstance(result, dict)
        assert result["api_key_id"] == "tfk_test"
        assert result["service_name"] == "test-service"
        # Check that boolean values are converted to strings
        assert result["enable_metrics"] == "true"
        assert result["enable_logs"] == "true"
        # TFO v2 API fields in dict
        assert result["use_v2_api"] == "true"
        assert result["v2_only"] == "false"
        assert result["collector_name"] == "TelemetryFlow Python SDK"
        assert result["datacenter"] == "default"
        assert result["enrich_resources"] == "true"
        assert result["protocol"] == "grpc"
        assert "sdk_version" in result
        assert result["tfo_collector_version"] == "1.1.2"

    def test_template_data_service_name_defaults_to_project(self) -> None:
        """Test that service_name defaults to project_name."""
        data = TemplateData(project_name="my-project")

        assert data.service_name == "my-project"


class TestTemplateLoading:
    """Test suite for template loading functions."""

    def test_get_template_dir(self) -> None:
        """Test getting template directory."""
        template_dir = get_template_dir()

        assert template_dir.exists()
        assert template_dir.is_dir()
        assert (template_dir / "env.tpl").exists()

    def test_load_template_env(self) -> None:
        """Test loading env.tpl template."""
        content = load_template("env.tpl")

        assert "TELEMETRYFLOW_API_KEY_ID" in content
        assert "TELEMETRYFLOW_SERVICE_NAME" in content
        assert "${api_key_id}" in content
        # TFO v2 API fields
        assert "TELEMETRYFLOW_USE_V2_API" in content
        assert "TELEMETRYFLOW_V2_ONLY" in content
        assert "TELEMETRYFLOW_COLLECTOR_NAME" in content
        assert "TELEMETRYFLOW_DATACENTER" in content
        assert "TELEMETRYFLOW_PROTOCOL" in content

    def test_load_template_init(self) -> None:
        """Test loading init.py.tpl template."""
        content = load_template("init.py.tpl")

        assert "TelemetryFlow" in content
        assert "def init(" in content
        assert "def get_client(" in content
        # TFO v2 API support
        assert "def init_v2_only(" in content
        assert "use_v2_api" in content
        assert "v2_only" in content

    def test_load_template_metrics(self) -> None:
        """Test loading metrics.py.tpl template."""
        content = load_template("metrics.py.tpl")

        assert "increment_counter" in content
        assert "record_gauge" in content
        assert "record_histogram" in content

    def test_load_template_logs(self) -> None:
        """Test loading logs.py.tpl template."""
        content = load_template("logs.py.tpl")

        assert "log_debug" in content
        assert "log_info" in content
        assert "log_warning" in content
        assert "log_error" in content

    def test_load_template_traces(self) -> None:
        """Test loading traces.py.tpl template."""
        content = load_template("traces.py.tpl")

        assert "span" in content
        assert "SpanKind" in content

    def test_load_template_readme(self) -> None:
        """Test loading README.md.tpl template."""
        content = load_template("README.md.tpl")

        assert "TelemetryFlow" in content
        assert "${project_name}" in content
        # TFO v2 API documentation
        assert "TFO v2 API" in content
        assert "init_v2_only" in content
        assert "/v2/traces" in content

    def test_load_template_not_found(self) -> None:
        """Test loading non-existent template raises error."""
        with pytest.raises(FileNotFoundError):
            load_template("nonexistent.tpl")

    def test_load_template_custom_dir(self) -> None:
        """Test loading template from custom directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir)
            custom_template = custom_dir / "custom.tpl"
            custom_template.write_text("Custom template: ${service_name}")

            content = load_template("custom.tpl", custom_dir)

            assert "Custom template" in content


class TestTemplateRendering:
    """Test suite for template rendering functions."""

    def test_render_template_simple(self) -> None:
        """Test rendering a simple template."""
        template = "Service: ${service_name}, Version: ${service_version}"
        data = TemplateData(
            api_key_id="tfk_test",
            api_key_secret="tfs_test",
            service_name="my-service",
            service_version="1.2.3",
        )

        result = render_template(template, data)

        assert result == "Service: my-service, Version: 1.2.3"

    def test_render_template_with_all_vars(self) -> None:
        """Test rendering template with all variables."""
        template = """
API Key: ${api_key_id}
Service: ${service_name}
Environment: ${environment}
Endpoint: ${endpoint}
"""
        data = TemplateData(
            api_key_id="tfk_test",
            api_key_secret="tfs_test",
            service_name="test-service",
            environment="staging",
            endpoint="localhost:4317",
        )

        result = render_template(template, data)

        assert "tfk_test" in result
        assert "test-service" in result
        assert "staging" in result
        assert "localhost:4317" in result

    def test_render_template_file(self) -> None:
        """Test rendering a template file."""
        data = TemplateData(
            api_key_id="tfk_file",
            api_key_secret="tfs_file",
            service_name="file-service",
        )

        result = render_template_file("env.tpl", data)

        assert "tfk_file" in result
        assert "file-service" in result


class TestCLI:
    """Test suite for CLI main function."""

    def test_cli_version(self) -> None:
        """Test CLI version command."""
        result = main(["version"])
        assert result == 0

    def test_cli_help(self) -> None:
        """Test CLI help (no command)."""
        result = main([])
        assert result == 0

    def test_cli_init_creates_files(self) -> None:
        """Test CLI init command creates files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = main(
                [
                    "--no-banner",
                    "init",
                    "-k",
                    "tfk_test",
                    "-s",
                    "tfs_test",
                    "-n",
                    "test-service",
                    "-o",
                    tmpdir,
                ]
            )

            assert result == 0

            # Check files were created
            output_dir = Path(tmpdir)
            assert (output_dir / ".env.telemetryflow").exists()
            assert (output_dir / "telemetry" / "__init__.py").exists()
            assert (output_dir / "telemetry" / "metrics.py").exists()
            assert (output_dir / "telemetry" / "logs.py").exists()
            assert (output_dir / "telemetry" / "traces.py").exists()

    def test_cli_init_force_overwrite(self) -> None:
        """Test CLI init command with force flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create initial files
            main(
                [
                    "--no-banner",
                    "init",
                    "-k",
                    "tfk_first",
                    "-s",
                    "tfs_first",
                    "-n",
                    "first-service",
                    "-o",
                    tmpdir,
                ]
            )

            # Overwrite with force
            result = main(
                [
                    "--no-banner",
                    "init",
                    "-k",
                    "tfk_second",
                    "-s",
                    "tfs_second",
                    "-n",
                    "second-service",
                    "-o",
                    tmpdir,
                    "--force",
                ]
            )

            assert result == 0

            # Check file contains new content
            env_content = (Path(tmpdir) / ".env.telemetryflow").read_text()
            assert "tfk_second" in env_content
            assert "second-service" in env_content

    def test_cli_example_basic(self) -> None:
        """Test CLI example command generates basic example."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = main(
                [
                    "--no-banner",
                    "example",
                    "basic",
                    "-o",
                    tmpdir,
                ]
            )

            assert result == 0
            assert (Path(tmpdir) / "example_basic.py").exists()

    def test_cli_example_http_server(self) -> None:
        """Test CLI example command generates HTTP server example."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = main(
                [
                    "--no-banner",
                    "example",
                    "http-server",
                    "-o",
                    tmpdir,
                ]
            )

            assert result == 0
            assert (Path(tmpdir) / "example_http_server.py").exists()

    def test_cli_config_generates_env(self) -> None:
        """Test CLI config command generates .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = main(
                [
                    "--no-banner",
                    "config",
                    "-k",
                    "tfk_config",
                    "-s",
                    "tfs_config",
                    "-n",
                    "config-service",
                    "-o",
                    tmpdir,
                ]
            )

            assert result == 0

            env_content = (Path(tmpdir) / ".env.telemetryflow").read_text()
            assert "tfk_config" in env_content
            assert "config-service" in env_content
            # TFO v2 API fields should be in generated config
            assert "TELEMETRYFLOW_USE_V2_API" in env_content
            assert "TELEMETRYFLOW_V2_ONLY" in env_content

    def test_cli_init_with_v2_options(self) -> None:
        """Test CLI init command with TFO v2 API options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = main(
                [
                    "--no-banner",
                    "init",
                    "-k",
                    "tfk_v2test",
                    "-s",
                    "tfs_v2test",
                    "-n",
                    "v2-test-service",
                    "-o",
                    tmpdir,
                    "--v2-only",
                    "--collector-name",
                    "My V2 Collector",
                    "--datacenter",
                    "us-west-2",
                    "--protocol",
                    "http",
                ]
            )

            assert result == 0

            # Check env file contains v2 API settings
            env_content = (Path(tmpdir) / ".env.telemetryflow").read_text()
            assert "TELEMETRYFLOW_USE_V2_API=true" in env_content
            assert "TELEMETRYFLOW_V2_ONLY=true" in env_content
            assert "My V2 Collector" in env_content
            assert "us-west-2" in env_content
            assert "http" in env_content


class TestExampleTemplates:
    """Test suite for example templates."""

    def test_example_basic_template(self) -> None:
        """Test loading basic example template."""
        content = load_template("example_basic.py.tpl")

        assert "init()" in content
        assert "get_client()" in content
        # TFO v2 API support
        assert "init_v2_only" in content
        assert "TFO v2 API" in content

    def test_example_http_server_template(self) -> None:
        """Test loading HTTP server example template."""
        content = load_template("example_http_server.py.tpl")

        assert "Flask" in content or "http" in content.lower()

    def test_example_worker_template(self) -> None:
        """Test loading worker example template."""
        content = load_template("example_worker.py.tpl")

        assert "Worker" in content or "worker" in content
