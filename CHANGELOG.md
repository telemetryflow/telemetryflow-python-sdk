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
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker)](https://hub.docker.com/r/telemetryflow/telemetryflow-sdk)

<p align="center">
  Enterprise-grade Python SDK for <a href="https://telemetryflow.id">TelemetryFlow</a> - the observability platform that provides unified metrics, logs, and traces collection following OpenTelemetry standards.
</p>

</div>

---

# Changelog


All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2024-12-30

### Added

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
