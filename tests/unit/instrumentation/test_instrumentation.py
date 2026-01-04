"""Unit tests for the instrumentation module."""

from unittest import mock

from telemetryflow.instrumentation import (
    InstrumentationConfig,
    auto_instrument,
    get_available_instrumentations,
    instrument_fastapi,
    instrument_flask,
    instrument_httpx,
    instrument_logging,
    instrument_psycopg2,
    instrument_redis,
    instrument_requests,
    instrument_sqlalchemy,
    is_instrumentation_available,
)


class TestInstrumentationConfig:
    """Tests for InstrumentationConfig class."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = InstrumentationConfig()

        assert config.tracer_provider is None
        assert config.meter_provider is None
        assert config.service_name is None
        assert config.service_version is None
        assert config.enable_flask is True
        assert config.enable_fastapi is True
        assert config.enable_sqlalchemy is True
        assert config.enable_requests is True
        assert config.enable_httpx is True
        assert config.enable_logging is True
        assert config.enable_psycopg2 is True
        assert config.enable_redis is True
        assert config.excluded_urls == []
        assert config.excluded_hosts == []

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        mock_tracer = mock.Mock()
        mock_meter = mock.Mock()

        config = InstrumentationConfig(
            tracer_provider=mock_tracer,
            meter_provider=mock_meter,
            service_name="test-service",
            service_version="1.0.0",
            enable_flask=False,
            enable_fastapi=False,
            excluded_urls=["health", "metrics"],
            excluded_hosts=["localhost"],
        )

        assert config.tracer_provider == mock_tracer
        assert config.meter_provider == mock_meter
        assert config.service_name == "test-service"
        assert config.service_version == "1.0.0"
        assert config.enable_flask is False
        assert config.enable_fastapi is False
        assert config.excluded_urls == ["health", "metrics"]
        assert config.excluded_hosts == ["localhost"]

    def test_excluded_urls_defaults_to_empty_list(self) -> None:
        """Test that excluded_urls defaults to empty list."""
        config = InstrumentationConfig(excluded_urls=None)
        assert config.excluded_urls == []

    def test_excluded_hosts_defaults_to_empty_list(self) -> None:
        """Test that excluded_hosts defaults to empty list."""
        config = InstrumentationConfig(excluded_hosts=None)
        assert config.excluded_hosts == []


class TestIsInstrumentationAvailable:
    """Tests for is_instrumentation_available function."""

    def test_unknown_instrumentation(self) -> None:
        """Test with unknown instrumentation name."""
        result = is_instrumentation_available("unknown")
        assert result is False

    @mock.patch("telemetryflow.instrumentation._is_package_available")
    def test_available_instrumentation(self, mock_is_available: mock.Mock) -> None:
        """Test with available instrumentation."""
        mock_is_available.return_value = True

        result = is_instrumentation_available("flask")

        assert result is True
        mock_is_available.assert_called_with("opentelemetry.instrumentation.flask")

    @mock.patch("telemetryflow.instrumentation._is_package_available")
    def test_unavailable_instrumentation(self, mock_is_available: mock.Mock) -> None:
        """Test with unavailable instrumentation."""
        mock_is_available.return_value = False

        result = is_instrumentation_available("flask")

        assert result is False


class TestGetAvailableInstrumentations:
    """Tests for get_available_instrumentations function."""

    @mock.patch("telemetryflow.instrumentation.is_instrumentation_available")
    def test_returns_available_only(self, mock_is_available: mock.Mock) -> None:
        """Test that only available instrumentations are returned."""
        mock_is_available.side_effect = lambda name: name in ["flask", "requests"]

        result = get_available_instrumentations()

        assert "flask" in result
        assert "requests" in result
        assert "fastapi" not in result
        assert "sqlalchemy" not in result

    @mock.patch("telemetryflow.instrumentation.is_instrumentation_available")
    def test_returns_empty_when_none_available(self, mock_is_available: mock.Mock) -> None:
        """Test returns empty list when no instrumentations available."""
        mock_is_available.return_value = False

        result = get_available_instrumentations()

        assert result == []

    @mock.patch("telemetryflow.instrumentation.is_instrumentation_available")
    def test_returns_all_when_all_available(self, mock_is_available: mock.Mock) -> None:
        """Test returns all instrumentations when all available."""
        mock_is_available.return_value = True

        result = get_available_instrumentations()

        expected = [
            "flask",
            "fastapi",
            "sqlalchemy",
            "requests",
            "httpx",
            "logging",
            "psycopg2",
            "redis",
        ]
        assert result == expected


class TestInstrumentFlask:
    """Tests for instrument_flask function."""

    @mock.patch("telemetryflow.instrumentation._is_package_available")
    def test_returns_false_when_instrumentation_not_available(
        self, mock_is_available: mock.Mock
    ) -> None:
        """Test returns False when instrumentation package not available."""
        mock_is_available.return_value = False

        result = instrument_flask()

        assert result is False

    @mock.patch("telemetryflow.instrumentation._is_package_available")
    def test_returns_false_when_flask_not_installed(self, mock_is_available: mock.Mock) -> None:
        """Test returns False when Flask is not installed."""
        mock_is_available.side_effect = lambda pkg: pkg == "opentelemetry.instrumentation.flask"

        result = instrument_flask()

        assert result is False


class TestInstrumentFastAPI:
    """Tests for instrument_fastapi function."""

    @mock.patch("telemetryflow.instrumentation._is_package_available")
    def test_returns_false_when_instrumentation_not_available(
        self, mock_is_available: mock.Mock
    ) -> None:
        """Test returns False when instrumentation package not available."""
        mock_is_available.return_value = False

        result = instrument_fastapi()

        assert result is False

    @mock.patch("telemetryflow.instrumentation._is_package_available")
    def test_returns_false_when_fastapi_not_installed(self, mock_is_available: mock.Mock) -> None:
        """Test returns False when FastAPI is not installed."""
        mock_is_available.side_effect = lambda pkg: pkg == "opentelemetry.instrumentation.fastapi"

        result = instrument_fastapi()

        assert result is False


class TestInstrumentSQLAlchemy:
    """Tests for instrument_sqlalchemy function."""

    @mock.patch("telemetryflow.instrumentation._is_package_available")
    def test_returns_false_when_instrumentation_not_available(
        self, mock_is_available: mock.Mock
    ) -> None:
        """Test returns False when instrumentation package not available."""
        mock_is_available.return_value = False

        result = instrument_sqlalchemy()

        assert result is False

    @mock.patch("telemetryflow.instrumentation._is_package_available")
    def test_returns_false_when_sqlalchemy_not_installed(
        self, mock_is_available: mock.Mock
    ) -> None:
        """Test returns False when SQLAlchemy is not installed."""
        mock_is_available.side_effect = (
            lambda pkg: pkg == "opentelemetry.instrumentation.sqlalchemy"
        )

        result = instrument_sqlalchemy()

        assert result is False


class TestInstrumentRequests:
    """Tests for instrument_requests function."""

    @mock.patch("telemetryflow.instrumentation._is_package_available")
    def test_returns_false_when_instrumentation_not_available(
        self, mock_is_available: mock.Mock
    ) -> None:
        """Test returns False when instrumentation package not available."""
        mock_is_available.return_value = False

        result = instrument_requests()

        assert result is False

    @mock.patch("telemetryflow.instrumentation._is_package_available")
    def test_returns_false_when_requests_not_installed(self, mock_is_available: mock.Mock) -> None:
        """Test returns False when requests is not installed."""
        mock_is_available.side_effect = lambda pkg: pkg == "opentelemetry.instrumentation.requests"

        result = instrument_requests()

        assert result is False


class TestInstrumentHttpx:
    """Tests for instrument_httpx function."""

    @mock.patch("telemetryflow.instrumentation._is_package_available")
    def test_returns_false_when_instrumentation_not_available(
        self, mock_is_available: mock.Mock
    ) -> None:
        """Test returns False when instrumentation package not available."""
        mock_is_available.return_value = False

        result = instrument_httpx()

        assert result is False

    @mock.patch("telemetryflow.instrumentation._is_package_available")
    def test_returns_false_when_httpx_not_installed(self, mock_is_available: mock.Mock) -> None:
        """Test returns False when httpx is not installed."""
        mock_is_available.side_effect = lambda pkg: pkg == "opentelemetry.instrumentation.httpx"

        result = instrument_httpx()

        assert result is False


class TestInstrumentLogging:
    """Tests for instrument_logging function."""

    @mock.patch("telemetryflow.instrumentation._is_package_available")
    def test_returns_false_when_instrumentation_not_available(
        self, mock_is_available: mock.Mock
    ) -> None:
        """Test returns False when instrumentation package not available."""
        mock_is_available.return_value = False

        result = instrument_logging()

        assert result is False


class TestInstrumentPsycopg2:
    """Tests for instrument_psycopg2 function."""

    @mock.patch("telemetryflow.instrumentation._is_package_available")
    def test_returns_false_when_instrumentation_not_available(
        self, mock_is_available: mock.Mock
    ) -> None:
        """Test returns False when instrumentation package not available."""
        mock_is_available.return_value = False

        result = instrument_psycopg2()

        assert result is False

    @mock.patch("telemetryflow.instrumentation._is_package_available")
    def test_returns_false_when_psycopg2_not_installed(self, mock_is_available: mock.Mock) -> None:
        """Test returns False when psycopg2 is not installed."""
        mock_is_available.side_effect = lambda pkg: pkg == "opentelemetry.instrumentation.psycopg2"

        result = instrument_psycopg2()

        assert result is False


class TestInstrumentRedis:
    """Tests for instrument_redis function."""

    @mock.patch("telemetryflow.instrumentation._is_package_available")
    def test_returns_false_when_instrumentation_not_available(
        self, mock_is_available: mock.Mock
    ) -> None:
        """Test returns False when instrumentation package not available."""
        mock_is_available.return_value = False

        result = instrument_redis()

        assert result is False

    @mock.patch("telemetryflow.instrumentation._is_package_available")
    def test_returns_false_when_redis_not_installed(self, mock_is_available: mock.Mock) -> None:
        """Test returns False when redis is not installed."""
        mock_is_available.side_effect = lambda pkg: pkg == "opentelemetry.instrumentation.redis"

        result = instrument_redis()

        assert result is False


class TestAutoInstrument:
    """Tests for auto_instrument function."""

    @mock.patch("telemetryflow.instrumentation.instrument_redis")
    @mock.patch("telemetryflow.instrumentation.instrument_psycopg2")
    @mock.patch("telemetryflow.instrumentation.instrument_logging")
    @mock.patch("telemetryflow.instrumentation.instrument_httpx")
    @mock.patch("telemetryflow.instrumentation.instrument_requests")
    @mock.patch("telemetryflow.instrumentation.instrument_sqlalchemy")
    @mock.patch("telemetryflow.instrumentation.instrument_fastapi")
    @mock.patch("telemetryflow.instrumentation.instrument_flask")
    def test_calls_all_instrumentors_by_default(
        self,
        mock_flask: mock.Mock,
        mock_fastapi: mock.Mock,
        mock_sqlalchemy: mock.Mock,
        mock_requests: mock.Mock,
        mock_httpx: mock.Mock,
        mock_logging: mock.Mock,
        mock_psycopg2: mock.Mock,
        mock_redis: mock.Mock,
    ) -> None:
        """Test that all instrumentors are called by default."""
        mock_flask.return_value = True
        mock_fastapi.return_value = True
        mock_sqlalchemy.return_value = True
        mock_requests.return_value = True
        mock_httpx.return_value = True
        mock_logging.return_value = True
        mock_psycopg2.return_value = True
        mock_redis.return_value = True

        results = auto_instrument()

        assert results["flask"] is True
        assert results["fastapi"] is True
        assert results["sqlalchemy"] is True
        assert results["requests"] is True
        assert results["httpx"] is True
        assert results["logging"] is True
        assert results["psycopg2"] is True
        assert results["redis"] is True

    @mock.patch("telemetryflow.instrumentation.instrument_redis")
    @mock.patch("telemetryflow.instrumentation.instrument_psycopg2")
    @mock.patch("telemetryflow.instrumentation.instrument_logging")
    @mock.patch("telemetryflow.instrumentation.instrument_httpx")
    @mock.patch("telemetryflow.instrumentation.instrument_requests")
    @mock.patch("telemetryflow.instrumentation.instrument_sqlalchemy")
    @mock.patch("telemetryflow.instrumentation.instrument_fastapi")
    @mock.patch("telemetryflow.instrumentation.instrument_flask")
    def test_respects_config_disabled_instrumentors(
        self,
        mock_flask: mock.Mock,
        mock_fastapi: mock.Mock,
        _mock_sqlalchemy: mock.Mock,
        _mock_requests: mock.Mock,
        _mock_httpx: mock.Mock,
        _mock_logging: mock.Mock,
        _mock_psycopg2: mock.Mock,
        _mock_redis: mock.Mock,
    ) -> None:
        """Test that disabled instrumentors are not called."""
        config = InstrumentationConfig(
            enable_flask=False,
            enable_fastapi=False,
        )

        results = auto_instrument(config=config)

        mock_flask.assert_not_called()
        mock_fastapi.assert_not_called()
        assert "flask" not in results
        assert "fastapi" not in results

    @mock.patch("telemetryflow.instrumentation.instrument_flask")
    def test_passes_tracer_provider_to_instrumentors(self, mock_flask: mock.Mock) -> None:
        """Test that tracer_provider is passed to instrumentors."""
        mock_tracer = mock.Mock()
        mock_flask.return_value = True

        config = InstrumentationConfig(
            tracer_provider=mock_tracer,
            enable_flask=True,
            enable_fastapi=False,
            enable_sqlalchemy=False,
            enable_requests=False,
            enable_httpx=False,
            enable_logging=False,
            enable_psycopg2=False,
            enable_redis=False,
        )

        auto_instrument(config=config)

        mock_flask.assert_called_once()
        call_kwargs = mock_flask.call_args[1]
        assert call_kwargs["tracer_provider"] == mock_tracer

    @mock.patch("telemetryflow.instrumentation.instrument_flask")
    def test_tracer_provider_override(self, mock_flask: mock.Mock) -> None:
        """Test that tracer_provider parameter overrides config."""
        config_tracer = mock.Mock()
        override_tracer = mock.Mock()
        mock_flask.return_value = True

        config = InstrumentationConfig(
            tracer_provider=config_tracer,
            enable_flask=True,
            enable_fastapi=False,
            enable_sqlalchemy=False,
            enable_requests=False,
            enable_httpx=False,
            enable_logging=False,
            enable_psycopg2=False,
            enable_redis=False,
        )

        auto_instrument(config=config, tracer_provider=override_tracer)

        call_kwargs = mock_flask.call_args[1]
        assert call_kwargs["tracer_provider"] == override_tracer

    @mock.patch("telemetryflow.instrumentation.instrument_flask")
    def test_meter_provider_override(self, mock_flask: mock.Mock) -> None:
        """Test that meter_provider parameter overrides config."""
        config_meter = mock.Mock()
        override_meter = mock.Mock()
        mock_flask.return_value = True

        config = InstrumentationConfig(
            meter_provider=config_meter,
            enable_flask=True,
            enable_fastapi=False,
            enable_sqlalchemy=False,
            enable_requests=False,
            enable_httpx=False,
            enable_logging=False,
            enable_psycopg2=False,
            enable_redis=False,
        )

        auto_instrument(config=config, meter_provider=override_meter)

        call_kwargs = mock_flask.call_args[1]
        assert call_kwargs["meter_provider"] == override_meter

    @mock.patch("telemetryflow.instrumentation.instrument_flask")
    def test_excluded_urls_joined(self, mock_flask: mock.Mock) -> None:
        """Test that excluded_urls are joined with comma."""
        mock_flask.return_value = True

        config = InstrumentationConfig(
            excluded_urls=["health", "metrics", "ready"],
            enable_flask=True,
            enable_fastapi=False,
            enable_sqlalchemy=False,
            enable_requests=False,
            enable_httpx=False,
            enable_logging=False,
            enable_psycopg2=False,
            enable_redis=False,
        )

        auto_instrument(config=config)

        call_kwargs = mock_flask.call_args[1]
        assert call_kwargs["excluded_urls"] == "health,metrics,ready"

    @mock.patch("telemetryflow.instrumentation.instrument_flask")
    def test_empty_excluded_urls(self, mock_flask: mock.Mock) -> None:
        """Test that empty excluded_urls results in None."""
        mock_flask.return_value = True

        config = InstrumentationConfig(
            excluded_urls=[],
            enable_flask=True,
            enable_fastapi=False,
            enable_sqlalchemy=False,
            enable_requests=False,
            enable_httpx=False,
            enable_logging=False,
            enable_psycopg2=False,
            enable_redis=False,
        )

        auto_instrument(config=config)

        call_kwargs = mock_flask.call_args[1]
        assert call_kwargs["excluded_urls"] is None

    @mock.patch("telemetryflow.instrumentation.instrument_flask")
    def test_creates_default_config_when_none(self, mock_flask: mock.Mock) -> None:
        """Test that default config is created when none provided."""
        mock_flask.return_value = True
        mock_tracer = mock.Mock()
        mock_meter = mock.Mock()

        with mock.patch.multiple(
            "telemetryflow.instrumentation",
            instrument_fastapi=mock.Mock(return_value=True),
            instrument_sqlalchemy=mock.Mock(return_value=True),
            instrument_requests=mock.Mock(return_value=True),
            instrument_httpx=mock.Mock(return_value=True),
            instrument_logging=mock.Mock(return_value=True),
            instrument_psycopg2=mock.Mock(return_value=True),
            instrument_redis=mock.Mock(return_value=True),
        ):
            results = auto_instrument(tracer_provider=mock_tracer, meter_provider=mock_meter)

        assert "flask" in results
        call_kwargs = mock_flask.call_args[1]
        assert call_kwargs["tracer_provider"] == mock_tracer
        assert call_kwargs["meter_provider"] == mock_meter


class TestInstrumentFlaskSuccess:
    """Tests for instrument_flask success paths using sys.modules mocking."""

    def test_flask_instrumentation_success(self) -> None:
        """Test successful Flask instrumentation."""
        import sys

        # Create mock instrumentor
        mock_instrumentor = mock.Mock()
        mock_flask_module = mock.Mock()
        mock_flask_module.FlaskInstrumentor = mock.Mock(return_value=mock_instrumentor)

        with (
            mock.patch.dict(
                sys.modules,
                {
                    "opentelemetry.instrumentation.flask": mock_flask_module,
                    "flask": mock.Mock(),
                },
            ),
            mock.patch("telemetryflow.instrumentation._is_package_available", return_value=True),
        ):
            result = instrument_flask(tracer_provider=mock.Mock())

            assert result is True
            mock_instrumentor.instrument.assert_called_once()

    def test_flask_instrumentation_exception(self) -> None:
        """Test Flask instrumentation when exception occurs."""
        import sys

        # Create mock that raises exception
        mock_instrumentor = mock.Mock()
        mock_instrumentor.instrument.side_effect = Exception("Test error")
        mock_flask_module = mock.Mock()
        mock_flask_module.FlaskInstrumentor = mock.Mock(return_value=mock_instrumentor)

        with (
            mock.patch.dict(
                sys.modules,
                {
                    "opentelemetry.instrumentation.flask": mock_flask_module,
                    "flask": mock.Mock(),
                },
            ),
            mock.patch("telemetryflow.instrumentation._is_package_available", return_value=True),
        ):
            result = instrument_flask()

            assert result is False


class TestInstrumentFastAPISuccess:
    """Tests for instrument_fastapi success paths."""

    def test_fastapi_instrumentation_success(self) -> None:
        """Test successful FastAPI instrumentation."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_fastapi_module = mock.Mock()
        mock_fastapi_module.FastAPIInstrumentor = mock.Mock(return_value=mock_instrumentor)

        with (
            mock.patch.dict(
                sys.modules,
                {
                    "opentelemetry.instrumentation.fastapi": mock_fastapi_module,
                    "fastapi": mock.Mock(),
                },
            ),
            mock.patch("telemetryflow.instrumentation._is_package_available", return_value=True),
        ):
            result = instrument_fastapi(tracer_provider=mock.Mock())

            assert result is True
            mock_instrumentor.instrument.assert_called_once()

    def test_fastapi_instrumentation_exception(self) -> None:
        """Test FastAPI instrumentation when exception occurs."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_instrumentor.instrument.side_effect = Exception("Test error")
        mock_fastapi_module = mock.Mock()
        mock_fastapi_module.FastAPIInstrumentor = mock.Mock(return_value=mock_instrumentor)

        with (
            mock.patch.dict(
                sys.modules,
                {
                    "opentelemetry.instrumentation.fastapi": mock_fastapi_module,
                    "fastapi": mock.Mock(),
                },
            ),
            mock.patch("telemetryflow.instrumentation._is_package_available", return_value=True),
        ):
            result = instrument_fastapi()

            assert result is False


class TestInstrumentSQLAlchemySuccess:
    """Tests for instrument_sqlalchemy success paths."""

    def test_sqlalchemy_instrumentation_success(self) -> None:
        """Test successful SQLAlchemy instrumentation."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_sqlalchemy_module = mock.Mock()
        mock_sqlalchemy_module.SQLAlchemyInstrumentor = mock.Mock(return_value=mock_instrumentor)

        with (
            mock.patch.dict(
                sys.modules,
                {
                    "opentelemetry.instrumentation.sqlalchemy": mock_sqlalchemy_module,
                    "sqlalchemy": mock.Mock(),
                },
            ),
            mock.patch("telemetryflow.instrumentation._is_package_available", return_value=True),
        ):
            result = instrument_sqlalchemy(tracer_provider=mock.Mock())

            assert result is True
            mock_instrumentor.instrument.assert_called_once()

    def test_sqlalchemy_instrumentation_exception(self) -> None:
        """Test SQLAlchemy instrumentation when exception occurs."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_instrumentor.instrument.side_effect = Exception("Test error")
        mock_sqlalchemy_module = mock.Mock()
        mock_sqlalchemy_module.SQLAlchemyInstrumentor = mock.Mock(return_value=mock_instrumentor)

        with (
            mock.patch.dict(
                sys.modules,
                {
                    "opentelemetry.instrumentation.sqlalchemy": mock_sqlalchemy_module,
                    "sqlalchemy": mock.Mock(),
                },
            ),
            mock.patch("telemetryflow.instrumentation._is_package_available", return_value=True),
        ):
            result = instrument_sqlalchemy()

            assert result is False


class TestInstrumentRequestsSuccess:
    """Tests for instrument_requests success paths."""

    def test_requests_instrumentation_success(self) -> None:
        """Test successful requests instrumentation."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_requests_module = mock.Mock()
        mock_requests_module.RequestsInstrumentor = mock.Mock(return_value=mock_instrumentor)

        with (
            mock.patch.dict(
                sys.modules,
                {
                    "opentelemetry.instrumentation.requests": mock_requests_module,
                    "requests": mock.Mock(),
                },
            ),
            mock.patch("telemetryflow.instrumentation._is_package_available", return_value=True),
        ):
            result = instrument_requests(tracer_provider=mock.Mock())

            assert result is True
            mock_instrumentor.instrument.assert_called_once()

    def test_requests_instrumentation_exception(self) -> None:
        """Test requests instrumentation when exception occurs."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_instrumentor.instrument.side_effect = Exception("Test error")
        mock_requests_module = mock.Mock()
        mock_requests_module.RequestsInstrumentor = mock.Mock(return_value=mock_instrumentor)

        with (
            mock.patch.dict(
                sys.modules,
                {
                    "opentelemetry.instrumentation.requests": mock_requests_module,
                    "requests": mock.Mock(),
                },
            ),
            mock.patch("telemetryflow.instrumentation._is_package_available", return_value=True),
        ):
            result = instrument_requests()

            assert result is False


class TestInstrumentHttpxSuccess:
    """Tests for instrument_httpx success paths."""

    def test_httpx_instrumentation_success(self) -> None:
        """Test successful httpx instrumentation."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_httpx_module = mock.Mock()
        mock_httpx_module.HTTPXClientInstrumentor = mock.Mock(return_value=mock_instrumentor)

        with (
            mock.patch.dict(
                sys.modules,
                {
                    "opentelemetry.instrumentation.httpx": mock_httpx_module,
                    "httpx": mock.Mock(),
                },
            ),
            mock.patch("telemetryflow.instrumentation._is_package_available", return_value=True),
        ):
            result = instrument_httpx(tracer_provider=mock.Mock())

            assert result is True
            mock_instrumentor.instrument.assert_called_once()

    def test_httpx_instrumentation_exception(self) -> None:
        """Test httpx instrumentation when exception occurs."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_instrumentor.instrument.side_effect = Exception("Test error")
        mock_httpx_module = mock.Mock()
        mock_httpx_module.HTTPXClientInstrumentor = mock.Mock(return_value=mock_instrumentor)

        with (
            mock.patch.dict(
                sys.modules,
                {
                    "opentelemetry.instrumentation.httpx": mock_httpx_module,
                    "httpx": mock.Mock(),
                },
            ),
            mock.patch("telemetryflow.instrumentation._is_package_available", return_value=True),
        ):
            result = instrument_httpx()

            assert result is False


class TestInstrumentLoggingSuccess:
    """Tests for instrument_logging success paths."""

    def test_logging_instrumentation_success(self) -> None:
        """Test successful logging instrumentation."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_logging_module = mock.Mock()
        mock_logging_module.LoggingInstrumentor = mock.Mock(return_value=mock_instrumentor)

        with (
            mock.patch.dict(
                sys.modules,
                {
                    "opentelemetry.instrumentation.logging": mock_logging_module,
                },
            ),
            mock.patch("telemetryflow.instrumentation._is_package_available", return_value=True),
        ):
            result = instrument_logging()

            assert result is True
            mock_instrumentor.instrument.assert_called_once()

    def test_logging_instrumentation_exception(self) -> None:
        """Test logging instrumentation when exception occurs."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_instrumentor.instrument.side_effect = Exception("Test error")
        mock_logging_module = mock.Mock()
        mock_logging_module.LoggingInstrumentor = mock.Mock(return_value=mock_instrumentor)

        with (
            mock.patch.dict(
                sys.modules,
                {
                    "opentelemetry.instrumentation.logging": mock_logging_module,
                },
            ),
            mock.patch("telemetryflow.instrumentation._is_package_available", return_value=True),
        ):
            result = instrument_logging()

            assert result is False


class TestInstrumentPsycopg2Success:
    """Tests for instrument_psycopg2 success paths."""

    def test_psycopg2_instrumentation_success(self) -> None:
        """Test successful psycopg2 instrumentation."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_psycopg2_module = mock.Mock()
        mock_psycopg2_module.Psycopg2Instrumentor = mock.Mock(return_value=mock_instrumentor)

        with (
            mock.patch.dict(
                sys.modules,
                {
                    "opentelemetry.instrumentation.psycopg2": mock_psycopg2_module,
                    "psycopg2": mock.Mock(),
                },
            ),
            mock.patch("telemetryflow.instrumentation._is_package_available", return_value=True),
        ):
            result = instrument_psycopg2(tracer_provider=mock.Mock())

            assert result is True
            mock_instrumentor.instrument.assert_called_once()

    def test_psycopg2_instrumentation_exception(self) -> None:
        """Test psycopg2 instrumentation when exception occurs."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_instrumentor.instrument.side_effect = Exception("Test error")
        mock_psycopg2_module = mock.Mock()
        mock_psycopg2_module.Psycopg2Instrumentor = mock.Mock(return_value=mock_instrumentor)

        with (
            mock.patch.dict(
                sys.modules,
                {
                    "opentelemetry.instrumentation.psycopg2": mock_psycopg2_module,
                    "psycopg2": mock.Mock(),
                },
            ),
            mock.patch("telemetryflow.instrumentation._is_package_available", return_value=True),
        ):
            result = instrument_psycopg2()

            assert result is False


class TestInstrumentRedisSuccess:
    """Tests for instrument_redis success paths."""

    def test_redis_instrumentation_success(self) -> None:
        """Test successful redis instrumentation."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_redis_module = mock.Mock()
        mock_redis_module.RedisInstrumentor = mock.Mock(return_value=mock_instrumentor)

        with (
            mock.patch.dict(
                sys.modules,
                {
                    "opentelemetry.instrumentation.redis": mock_redis_module,
                    "redis": mock.Mock(),
                },
            ),
            mock.patch("telemetryflow.instrumentation._is_package_available", return_value=True),
        ):
            result = instrument_redis(tracer_provider=mock.Mock())

            assert result is True
            mock_instrumentor.instrument.assert_called_once()

    def test_redis_instrumentation_exception(self) -> None:
        """Test redis instrumentation when exception occurs."""
        import sys

        mock_instrumentor = mock.Mock()
        mock_instrumentor.instrument.side_effect = Exception("Test error")
        mock_redis_module = mock.Mock()
        mock_redis_module.RedisInstrumentor = mock.Mock(return_value=mock_instrumentor)

        with (
            mock.patch.dict(
                sys.modules,
                {
                    "opentelemetry.instrumentation.redis": mock_redis_module,
                    "redis": mock.Mock(),
                },
            ),
            mock.patch("telemetryflow.instrumentation._is_package_available", return_value=True),
        ):
            result = instrument_redis()

            assert result is False
