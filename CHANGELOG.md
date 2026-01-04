<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/telemetryflow/.github/raw/main/docs/assets/tfo-logo-sdk-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://github.com/telemetryflow/.github/raw/main/docs/assets/tfo-logo-sdk-light.svg">
    <img src="https://github.com/telemetryflow/.github/raw/main/docs/assets/tfo-logo-sdk-light.svg" alt="TelemetryFlow Logo" width="80%">
  </picture>

  <h3>TelemetryFlow Python SDK</h3>

[![Version](https://img.shields.io/badge/Version-1.1.2-orange.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![OTEL SDK](https://img.shields.io/badge/OpenTelemetry_SDK-1.28.0-blueviolet)](https://opentelemetry.io/)
[![OpenTelemetry](https://img.shields.io/badge/OTLP-100%25%20Compliant-success?logo=opentelemetry)](https://opentelemetry.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker)](https://hub.docker.com/r/telemetryflow/telemetryflow-python-sdk)

<p align="center">
  Enterprise-grade Python SDK for <a href="https://telemetryflow.id">TelemetryFlow</a> - the observability platform that provides unified metrics, logs, and traces collection following OpenTelemetry standards.
</p>

</div>

---

# Changelog


All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.2] - 2025-01-04

### Added

- **Build Package in Dev Dependencies**: Added `build>=1.0.0` to dev dependencies for local package building
- **gRPC Header Lowercase Support**: Added `_get_grpc_headers()` method in `OTLPExporterFactory` to ensure gRPC metadata keys are lowercase (required by gRPC specification)
- **Comprehensive Unit Tests**: Added `TestGetGrpcHeaders` test class for gRPC header handling

- **TFO v2 API Configuration Alignment**: Updated SDK configuration to align with TFO-Collector v1.1.2 (OCB-native)
  - Added `v2_api` configuration section with `enabled` and `v2_only` options
  - Added custom endpoint paths support (`traces_endpoint`, `metrics_endpoint`, `logs_endpoint`)
  - Aligned with `tfoexporter` component for consistent API versioning

- **Collector Identity Support**: Added collector identity configuration aligned with `tfoidentityextension`
  - Collector ID, name, description, hostname, and datacenter settings
  - Custom tags support for collector identification
  - Resource attribute enrichment toggle

- **SDK Configuration Files**: Added default configuration files for different use cases
  - `configs/sdk-default.yaml` - Full SDK configuration with all options
  - `configs/sdk-v2-only.yaml` - Production-optimized v2-only mode
  - `configs/sdk-minimal.yaml` - Quick-start minimal configuration

- **Enhanced Environment Variables**: Updated `.env.example` with TFO v2 API settings
  - `TELEMETRYFLOW_USE_V2_API` - Enable/disable v2 API endpoints
  - `TELEMETRYFLOW_V2_ONLY` - Enable v2-only mode
  - `TELEMETRYFLOW_COLLECTOR_NAME` - Human-readable collector name
  - `TELEMETRYFLOW_DATACENTER` - Datacenter/region identifier
  - `TELEMETRYFLOW_ENRICH_RESOURCES` - Resource attribute enrichment

- **Command Generator Updates**: Updated `telemetryflow-gen` CLI with TFO v2 API support
  - Added `--use-v2-api`, `--v2-only`, `--collector-name`, `--datacenter`, `--protocol` CLI options
  - Updated `TemplateData` class with TFO v2 API fields
  - Updated all templates (`env.tpl`, `init.py.tpl`, `example_basic.py.tpl`, `README.md.tpl`) for v2 API
  - Added `init_v2_only()` convenience function in generated code
  - Templates now include SDK version and TFO-Collector version metadata

- **Unit Tests**: Added comprehensive unit tests for TFO v2 API features
  - Tests for `TemplateData` v2 API fields and serialization
  - Tests for CLI v2 API options (`--v2-only`, `--collector-name`, etc.)
  - Tests for template rendering with v2 API variables

- **Examples**: Updated examples with TFO v2 API documentation
  - Updated `examples/basic/main.py` with v2 API usage

### Changed

- **CI Python Version Matrix**: Updated CI workflow to test on Python 3.12 and 3.13 only (aligned with `requires-python = ">=3.12"`)
- Updated version to 1.1.2 to align with TFO-Collector v1.1.2 release
- Default endpoint changed from `api.telemetryflow.id:4317` to `localhost:4317` for development
- Added `TELEMETRYFLOW_PROTOCOL` and `TELEMETRYFLOW_TIMEOUT` environment variables

### Fixed

- **gRPC Header Case Sensitivity**: Fixed gRPC exporter to use lowercase header keys (gRPC metadata specification requires lowercase keys)

### SDK Configuration Structure

```yaml
# TFO v2 API Configuration
v2_api:
  enabled: true
  v2_only: false
  traces_endpoint: "/v2/traces"
  metrics_endpoint: "/v2/metrics"
  logs_endpoint: "/v2/logs"

# Collector Identity
collector:
  id: "${TELEMETRYFLOW_COLLECTOR_ID:}"
  name: "TelemetryFlow Python SDK"
  datacenter: "default"
  enrich_resources: true
  tags:
    sdk_version: "1.1.2"
    sdk_language: "python"
```

---

## [1.1.1] - 2024-12-30

### Added

- **Dual Endpoint Ingestion Support**: Updated docker-compose and OTEL collector configs for TFO-Collector dual ingestion
  - v1 endpoints: Standard OTEL community format (`/v1/traces`, `/v1/metrics`, `/v1/logs`)
  - v2 endpoints: TelemetryFlow enhanced format (`/v2/traces`, `/v2/metrics`, `/v2/logs`)
  - gRPC endpoint: Same port (4317) for both v1 and v2
- **TFO-Collector as Default**: Docker-compose now uses `telemetryflow/telemetryflow-collector` as default image
  - Commented alternatives for TFO-Collector-OCB and OTEL Collector Contrib
  - Separate volume mounts for each collector type
- **Enhanced Port Configuration**: Added additional ports for observability
  - zPages (55679) for debugging
  - pprof (1777) for profiling
  - Prometheus exporter (8889)
- **Connectors for Exemplars**: Added spanmetrics and servicegraph connectors
  - Metrics-to-traces correlation with exemplars enabled
  - Service dependency graph generation
- Template-based code generation for `telemetryflow-gen` CLI
- Template-based code generation for `telemetryflow-restapi` CLI
- External `.tpl` template files for all generated code
- `--template-dir` CLI option for custom templates
- Comprehensive unit tests for CLI generators

### Changed

- Refactored `generator.py` to use external template files (reduced inline code by ~70%)
- Refactored `generator_restapi.py` to use external template files (reduced from 2326 to 843 lines)
- Templates now loaded via `importlib.resources` for package portability
- Improved template organization with subdirectories (project, infrastructure, domain, application, entity)

### Template Structure

```text
templates/
├── native/                    # telemetryflow-gen templates
│   ├── env.tpl
│   ├── init.py.tpl
│   ├── metrics.py.tpl
│   ├── logs.py.tpl
│   ├── traces.py.tpl
│   ├── README.md.tpl
│   └── example_*.py.tpl
└── restapi/                   # telemetryflow-restapi templates
    ├── project/               # Project scaffolding
    ├── infrastructure/        # Infrastructure layer
    ├── domain/                # Domain layer (DDD)
    ├── application/           # Application layer (CQRS)
    └── entity/                # Entity CRUD generation
```

---

## [1.1.0] - 2024-12-29

### Added
- Initial release of TelemetryFlow Python SDK
- Full OpenTelemetry support with OTLP export
- Metrics support (counter, gauge, histogram)
- Logs support with severity levels
- Traces support with span management
- gRPC and HTTP protocol support
- Builder pattern for client configuration
- Environment variable configuration
- Flask middleware integration
- FastAPI middleware integration
- CLI generator for project scaffolding
- Comprehensive test suite
- Type hints with mypy support
- DDD architecture with CQRS pattern

### Features
- `TelemetryFlowClient` - Main SDK client
- `TelemetryFlowBuilder` - Fluent configuration builder
- `Credentials` - Immutable API key value object
- `TelemetryConfig` - Configuration aggregate root
- Framework middleware for Flask and FastAPI
- Context manager support for spans
- Exemplars support for metrics-to-traces correlation
- Collector ID and service namespace support
- Custom resource attributes

### Documentation
- Comprehensive README with examples
- API reference documentation
- Integration guides
- Example applications (basic, HTTP server, worker, gRPC)

### Planned
- AsyncIO support
- Django middleware
- Batch log emission
- More framework integrations
