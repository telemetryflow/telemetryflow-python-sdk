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

# Contributing to TelemetryFlow Python SDK

Thank you for your interest in contributing to the TelemetryFlow Python SDK! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Style Guide](#style-guide)
- [Architecture Guidelines](#architecture-guidelines)
- [CLI Generators](#cli-generators)
- [Release Process](#release-process)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. We expect all contributors to:

- Be respectful and constructive in discussions
- Welcome newcomers and help them learn
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.12 or higher (minimum supported version)
- Git
- Make (optional, for using Makefile commands)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/telemetryflow-python-sdk.git
cd telemetryflow-python-sdk
```

3. Add the upstream remote:

```bash
git remote add upstream https://github.com/telemetryflow/telemetryflow-python-sdk.git
```

## Development Setup

### Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

### Install Dependencies

```bash
# Install package in development mode with dev dependencies
pip install -e ".[dev]"
```

### Verify Setup

```bash
# Run tests
pytest tests/ -v

# Run linter
ruff check src/ tests/

# Run formatter check
ruff format --check src/ tests/

# Run type checker
mypy src/ --ignore-missing-imports
```

### IDE Setup

We recommend using an IDE with Python support:

- **VS Code** with the Python extension
- **PyCharm** by JetBrains
- **Vim/Neovim** with pylsp or pyright

## Project Structure

The SDK follows Domain-Driven Design (DDD) and CQRS patterns:

```
telemetryflow-python-sdk/
├── src/telemetryflow/
│   ├── __init__.py              # Public exports
│   ├── client.py                # TelemetryFlow client
│   ├── builder.py               # Builder pattern for configuration
│   ├── domain/                  # Domain layer (entities, value objects)
│   │   ├── config.py            # TelemetryConfig entity
│   │   └── credentials.py       # Credentials value object
│   ├── application/             # Application layer (CQRS)
│   │   ├── commands.py          # Command definitions
│   │   └── queries.py           # Query definitions
│   ├── infrastructure/          # Infrastructure layer
│   │   ├── exporters.py         # OTLP exporter factory
│   │   └── handlers.py          # Command handlers
│   └── cli/                     # CLI generators
│       ├── generator.py         # telemetryflow-gen
│       ├── generator_restapi.py # telemetryflow-restapi
│       └── templates/           # Template files for code generation
│           ├── gen/             # Basic SDK templates
│           └── restapi/         # RESTful API templates
│               ├── project/     # Project structure templates
│               ├── domain/      # Domain layer templates
│               ├── application/ # Application layer templates
│               ├── infrastructure/ # Infrastructure templates
│               ├── entity/      # Entity generation templates
│               └── docs/        # Documentation templates
├── tests/
│   ├── unit/                    # Unit tests
│   │   └── cli/                 # CLI generator tests
│   ├── integration/             # Integration tests
│   └── e2e/                     # End-to-end tests
├── docs/
│   ├── ARCHITECTURE.md          # Architecture documentation
│   └── QUICKSTART.md            # Quickstart guide
├── examples/                    # Usage examples
├── pyproject.toml               # Project configuration
├── CHANGELOG.md                 # Version history
└── README.md                    # Project overview
```

### Layer Responsibilities

| Layer | Responsibility | Dependencies |
|-------|---------------|--------------|
| **Domain** | Business logic, entities, value objects | None (pure Python) |
| **Application** | Use cases, commands, queries | Domain only |
| **Infrastructure** | Technical implementations, exporters | Domain, Application |
| **Interface** | Public API (Client, Builder) | All layers |
| **CLI** | Code generators | All layers |

## Making Changes

### Branch Naming

Use descriptive branch names:

- `feature/add-custom-metric-types`
- `fix/connection-timeout-handling`
- `docs/update-api-reference`
- `refactor/simplify-command-handlers`

### Creating a Branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

### Commit Messages

Follow conventional commits format:

```
type(scope): short description

Longer description if needed.

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

**Examples:**

```
feat(metrics): add support for exponential histograms

Implement exponential histogram recording for more efficient
distribution tracking of high-cardinality data.

Fixes #45
```

```
fix(exporter): handle connection timeout gracefully

Added proper timeout handling and retry logic when the
OTLP endpoint is temporarily unavailable.
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run only unit tests
pytest tests/unit/ -v

# Run tests with coverage
pytest tests/ -v --cov=src/telemetryflow --cov-report=html

# Run specific test file
pytest tests/unit/cli/test_generator.py -v

# Run tests matching a pattern
pytest tests/ -v -k "test_credentials"
```

### Writing Tests

Follow these guidelines for tests:

1. **Unit Tests**: Test individual functions and methods in isolation
2. **Integration Tests**: Test interactions between layers
3. **Parametrized Tests**: Use pytest parametrize for multiple scenarios

Example test structure:

```python
import pytest
from telemetryflow.domain import Credentials


class TestCredentials:
    """Tests for Credentials value object."""

    @pytest.mark.parametrize("key_id,key_secret,should_raise", [
        ("tfk_valid_key", "tfs_valid_secret", False),
        ("", "tfs_valid_secret", True),
        ("tfk_valid_key", "", True),
        ("invalid", "tfs_valid_secret", True),
    ])
    def test_credentials_validation(
        self,
        key_id: str,
        key_secret: str,
        should_raise: bool,
    ) -> None:
        """Test credentials validation with various inputs."""
        if should_raise:
            with pytest.raises(ValueError):
                Credentials(key_id, key_secret)
        else:
            creds = Credentials(key_id, key_secret)
            assert creds.key_id == key_id
            assert creds.key_secret == key_secret
```

### Test Coverage

We aim for high test coverage, especially in:

- Domain layer: 90%+
- Application layer: 85%+
- Infrastructure layer: 80%+
- CLI generators: 85%+

## Submitting Changes

### Before Submitting

1. **Run tests**: `pytest tests/ -v`
2. **Run linter**: `ruff check src/ tests/`
3. **Run formatter**: `ruff format src/ tests/`
4. **Run type checker**: `mypy src/ --ignore-missing-imports`
5. **Update documentation** if needed
6. **Add tests** for new functionality

### Pull Request Process

1. Push your branch to your fork:

```bash
git push origin feature/your-feature-name
```

2. Create a Pull Request on GitHub

3. Fill in the PR template with:
   - Description of changes
   - Related issue numbers
   - Testing performed
   - Checklist items

4. Wait for review and address feedback

### PR Title Format

Use the same format as commit messages:

```
feat(metrics): add exponential histogram support
fix(exporter): handle connection timeouts
docs(api): update method signatures
```

## Style Guide

### Python Style

Follow PEP 8 and modern Python conventions:

- Use `ruff` for linting and formatting
- Use type hints for all public functions and methods
- Use dataclasses or Pydantic for data structures
- Prefer f-strings over string formatting

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Modules | lowercase, underscores | `domain`, `application` |
| Classes | PascalCase | `TelemetryConfig`, `Credentials` |
| Functions | snake_case | `new_credentials`, `handle_command` |
| Constants | UPPER_SNAKE_CASE | `PROTOCOL_GRPC`, `SIGNAL_METRICS` |
| Private | leading underscore | `_validate_config`, `_internal_state` |

### Error Handling

- Use custom exceptions for domain-specific errors
- Always include helpful error messages
- Use exception chaining with `from`

```python
# Good
class InvalidCredentialsError(ValueError):
    """Raised when credentials are invalid."""
    pass

def validate_credentials(key_id: str, key_secret: str) -> None:
    if not key_id.startswith("tfk_"):
        raise InvalidCredentialsError(
            f"Invalid key ID format: must start with 'tfk_', got '{key_id[:10]}...'"
        )

# With exception chaining
try:
    result = external_api_call()
except ExternalAPIError as e:
    raise ConnectionError("Failed to connect to telemetry endpoint") from e
```

### Documentation

- Document all public types, functions, and methods
- Use Google-style docstrings
- Include type hints in signatures

```python
def new_credentials(key_id: str, key_secret: str) -> Credentials:
    """Create a new Credentials value object.

    Creates and validates new credentials for authenticating with
    the TelemetryFlow API.

    Args:
        key_id: The API key ID, must start with 'tfk_'.
        key_secret: The API key secret, must start with 'tfs_'.

    Returns:
        A validated Credentials object.

    Raises:
        InvalidCredentialsError: If either key_id or key_secret is invalid.

    Example:
        >>> creds = new_credentials("tfk_example", "tfs_secret")
        >>> print(creds.key_id)
        'tfk_example'
    """
    # Implementation...
```

## Architecture Guidelines

When contributing, maintain the architectural principles:

### Domain-Driven Design

1. **Value Objects**: Immutable, validate on creation
2. **Entities**: Have identity, can change state through methods
3. **Aggregate Roots**: Entry point for accessing aggregates

### CQRS Pattern

1. **Commands**: Represent intentions to change state
2. **Queries**: Represent requests for data
3. **Handlers**: Execute commands and queries

### SOLID Principles

1. **Single Responsibility**: One reason to change per type
2. **Open/Closed**: Open for extension, closed for modification
3. **Liskov Substitution**: Subtypes must be substitutable
4. **Interface Segregation**: Small, focused interfaces (protocols)
5. **Dependency Inversion**: Depend on abstractions (protocols)

### Adding New Features

When adding new features:

1. Define domain concepts first (if applicable)
2. Create commands/queries in the application layer
3. Implement handlers in the infrastructure layer
4. Expose through the public API (Client)
5. Add comprehensive tests

## CLI Generators

The SDK includes two CLI generators that use template-based code generation:

### telemetryflow-gen

Basic SDK code generator:

```bash
# Generate example project
telemetryflow-gen example basic -o ./my-project

# Generate configuration file
telemetryflow-gen config -k tfk_key -s tfs_secret -o .env
```

### telemetryflow-restapi

DDD + CQRS RESTful API generator using Flask:

```bash
# Create new project
telemetryflow-restapi new -n my-api -o ./

# Add entity to existing project
telemetryflow-restapi entity -n User -f 'name:string,email:string' -o ./my-api
```

### Template System

Templates are stored in `src/telemetryflow/cli/templates/` and use Python's `string.Template` for substitution:

- Templates use `${variable_name}` syntax
- Templates are loaded via `importlib.resources`
- Each generator has its own template subdirectory

### Adding Templates

1. Create `.tpl` template file in appropriate directory
2. Use `${variable}` for substitutions
3. Update generator to load and render template
4. Add tests for new templates

## Release Process

Releases follow semantic versioning (SemVer):

- **MAJOR**: Breaking API changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### CI/CD Workflows

The project uses GitHub Actions for CI/CD:

| Workflow       | Trigger           | Purpose                                 |
| -------------- | ----------------- | --------------------------------------- |
| `ci.yml`       | Push/PR           | Lint, test, build verification          |
| `docker.yml`   | Push to main/tags | Build Docker images                     |
| `release.yml`  | Tags (v*.*.*)     | Publish to PyPI, create GitHub release  |

### Changelog

Update CHANGELOG.md with your changes under the "Unreleased" section.

### Creating a Release

1. Update version in `pyproject.toml`
2. Update version badge in `README.md` and `CONTRIBUTING.md`
3. Move "Unreleased" section in CHANGELOG.md to new version
4. Create and push tag:

```bash
git tag v1.2.0
git push origin v1.2.0
```

GitHub Actions will automatically:

- Run tests
- Build packages
- Publish to PyPI
- Create GitHub release

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue with the bug template
- **Features**: Open a GitHub Issue with the feature request template
- **Security**: Email security@telemetryflow.id (do not open public issues)

## Recognition

Contributors are recognized in:

- GitHub Contributors page
- CHANGELOG.md for significant contributions
- README.md acknowledgments section

Thank you for contributing to TelemetryFlow Python SDK!

---

Built with care by the **DevOpsCorner Indonesia** community
