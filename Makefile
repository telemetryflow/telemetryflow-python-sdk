# TelemetryFlow Python SDK - Makefile
#
# TelemetryFlow Python SDK - Community Enterprise Observability Platform (CEOP)
# Copyright (c) 2024-2026 DevOpsCorner Indonesia. All rights reserved.
#
# Build and development commands for TelemetryFlow Python SDK

# Build configuration
PRODUCT_NAME := TelemetryFlow Python SDK
VERSION ?= 1.1.2
TFO_COLLECTOR_VERSION := 1.1.2
OTEL_VERSION := 0.142.0
OTEL_PYTHON_SDK_VERSION := 1.29.0
GIT_COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
BUILD_TIME := $(shell date -u '+%Y-%m-%dT%H:%M:%SZ')
PYTHON_VERSION := $(shell python3 --version 2>/dev/null | cut -d ' ' -f 2)

# Python configuration
PYTHON ?= python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
MYPY := $(PYTHON) -m mypy
RUFF := $(PYTHON) -m ruff
BLACK := $(PYTHON) -m black
ISORT := $(PYTHON) -m isort
BUILD := $(PYTHON) -m build
TWINE := $(PYTHON) -m twine

# Directories
SRC_DIR := src
TESTS_DIR := tests
EXAMPLES_DIR := examples
DOCS_DIR := docs
BUILD_DIR := build
DIST_DIR := dist
COVERAGE_DIR := htmlcov

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
BLUE := \033[0;34m
NC := \033[0m

.PHONY: all build build-wheel build-sdist clean test test-unit test-integration test-coverage test-fast test-short bench deps deps-update lint lint-fix fmt fmt-check vet typecheck run-example run-http run-worker run-grpc install install-dev uninstall help version check ci release-check docs security venv verify

# Default target
all: build

# Help target
help:
	@echo "$(GREEN)$(PRODUCT_NAME) - Build System$(NC)"
	@echo ""
	@echo "$(YELLOW)Build Commands:$(NC)"
	@echo "  make                  - Build distribution packages (default)"
	@echo "  make build            - Build wheel and sdist packages"
	@echo "  make build-wheel      - Build wheel package only"
	@echo "  make build-sdist      - Build source distribution only"
	@echo "  make clean            - Clean build artifacts"
	@echo ""
	@echo "$(YELLOW)Development Commands:$(NC)"
	@echo "  make run-example      - Run basic example"
	@echo "  make run-http         - Run HTTP server example"
	@echo "  make run-worker       - Run worker example"
	@echo "  make run-grpc         - Run gRPC server example"
	@echo "  make generate-example - Generate SDK example project"
	@echo ""
	@echo "$(YELLOW)Testing Commands:$(NC)"
	@echo "  make test             - Run unit and integration tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-coverage    - Run tests with coverage report"
	@echo "  make test-fast        - Run tests in parallel"
	@echo "  make test-short       - Run short tests"
	@echo "  make bench            - Run benchmarks"
	@echo ""
	@echo "$(YELLOW)Code Quality:$(NC)"
	@echo "  make lint             - Run linter (ruff)"
	@echo "  make lint-fix         - Run linter with auto-fix"
	@echo "  make fmt              - Format code (black, isort)"
	@echo "  make fmt-check        - Check code formatting"
	@echo "  make typecheck        - Run type checking (mypy)"
	@echo "  make check            - Run all checks (fmt, lint, typecheck, test)"
	@echo "  make security         - Run security scan (bandit)"
	@echo ""
	@echo "$(YELLOW)Dependencies:$(NC)"
	@echo "  make deps             - Install dependencies"
	@echo "  make deps-update      - Update dependencies"
	@echo "  make venv             - Create virtual environment"
	@echo "  make verify           - Verify dependencies"
	@echo ""
	@echo "$(YELLOW)Installation:$(NC)"
	@echo "  make install          - Install package in production mode"
	@echo "  make install-dev      - Install package in development mode"
	@echo "  make uninstall        - Uninstall package"
	@echo ""
	@echo "$(YELLOW)Publishing:$(NC)"
	@echo "  make publish          - Publish to PyPI"
	@echo "  make publish-test     - Publish to Test PyPI"
	@echo ""
	@echo "$(YELLOW)Other Commands:$(NC)"
	@echo "  make version          - Show version information"
	@echo "  make ci               - Run CI pipeline"
	@echo "  make release-check    - Check release readiness"
	@echo "  make docs             - Show documentation locations"
	@echo ""
	@echo "$(YELLOW)TFO v2 API Features:$(NC)"
	@echo "  - v2 endpoints: /v2/traces, /v2/metrics, /v2/logs"
	@echo "  - Collector identity (tfoidentityextension)"
	@echo "  - Auth headers (tfoauthextension)"
	@echo ""
	@echo "$(YELLOW)Configuration:$(NC)"
	@echo "  VERSION=$(VERSION)"
	@echo "  TFO_COLLECTOR_VERSION=$(TFO_COLLECTOR_VERSION)"
	@echo "  OTEL_VERSION=$(OTEL_VERSION)"
	@echo "  OTEL_PYTHON_SDK_VERSION=$(OTEL_PYTHON_SDK_VERSION)"
	@echo "  GIT_COMMIT=$(GIT_COMMIT)"
	@echo "  GIT_BRANCH=$(GIT_BRANCH)"
	@echo "  BUILD_TIME=$(BUILD_TIME)"
	@echo "  PYTHON_VERSION=$(PYTHON_VERSION)"

## Build commands
build: clean build-wheel build-sdist
	@echo "$(GREEN)Build complete$(NC)"
	@ls -la $(DIST_DIR)/

build-wheel:
	@echo "$(GREEN)Building wheel package...$(NC)"
	@$(BUILD) --wheel
	@echo "$(GREEN)Wheel build complete$(NC)"

build-sdist:
	@echo "$(GREEN)Building source distribution...$(NC)"
	@$(BUILD) --sdist
	@echo "$(GREEN)Source distribution build complete$(NC)"

## Development commands
run-example:
	@echo "$(YELLOW)Make sure to set environment variables first$(NC)"
	@echo "$(GREEN)Running basic example...$(NC)"
	@$(PYTHON) $(EXAMPLES_DIR)/basic/main.py

run-http:
	@echo "$(YELLOW)Make sure to set environment variables first$(NC)"
	@echo "$(GREEN)Running HTTP server example...$(NC)"
	@$(PYTHON) $(EXAMPLES_DIR)/http_server/main.py

run-worker:
	@echo "$(YELLOW)Make sure to set environment variables first$(NC)"
	@echo "$(GREEN)Running worker example...$(NC)"
	@$(PYTHON) $(EXAMPLES_DIR)/worker/main.py

run-grpc:
	@echo "$(YELLOW)Make sure to set environment variables first$(NC)"
	@echo "$(GREEN)Running gRPC server example...$(NC)"
	@$(PYTHON) $(EXAMPLES_DIR)/grpc_server/main.py

generate-example:
	@echo "$(GREEN)Generating SDK example project...$(NC)"
	@mkdir -p _generated
	@telemetryflow-gen init -o _generated
	@echo "$(GREEN)Example generated in _generated/$(NC)"

## Test commands
test: test-unit test-integration
	@echo "$(GREEN)All tests completed$(NC)"

test-unit:
	@echo "$(GREEN)Running unit tests...$(NC)"
	@$(PYTEST) $(TESTS_DIR)/unit/ -v --tb=short
	@echo "$(GREEN)Unit tests complete$(NC)"

test-integration:
	@echo "$(GREEN)Running integration tests...$(NC)"
	@$(PYTEST) $(TESTS_DIR)/integration/ -v -m integration --tb=short
	@echo "$(GREEN)Integration tests complete$(NC)"

test-coverage: test-coverage-unit test-coverage-integration coverage-report
	@echo "$(GREEN)All tests with coverage completed$(NC)"

test-coverage-unit:
	@echo "$(GREEN)Running unit tests with coverage...$(NC)"
	@$(PYTEST) $(TESTS_DIR)/unit/ -v --cov=$(SRC_DIR)/telemetryflow --cov-report=xml:coverage-unit.xml --cov-report=term-missing
	@echo "$(GREEN)Unit test coverage complete$(NC)"

test-coverage-integration:
	@echo "$(GREEN)Running integration tests with coverage...$(NC)"
	@$(PYTEST) $(TESTS_DIR)/integration/ -v -m integration --cov=$(SRC_DIR)/telemetryflow --cov-append --cov-report=xml:coverage-integration.xml --cov-report=term-missing || true
	@echo "$(GREEN)Integration test coverage complete$(NC)"

coverage-report:
	@echo "$(GREEN)Generating HTML coverage report...$(NC)"
	@$(PYTEST) $(TESTS_DIR)/ --cov=$(SRC_DIR)/telemetryflow --cov-report=html:$(COVERAGE_DIR) --cov-report=term-missing -q || true
	@echo "$(GREEN)Coverage report available at $(COVERAGE_DIR)/index.html$(NC)"

test-fast:
	@echo "$(GREEN)Running tests in parallel...$(NC)"
	@$(PYTEST) -n auto -v
	@echo "$(GREEN)Parallel tests complete$(NC)"

test-short:
	@echo "$(GREEN)Running short tests...$(NC)"
	@$(PYTEST) -v --tb=short -x
	@echo "$(GREEN)Short tests complete$(NC)"

bench:
	@echo "$(GREEN)Running benchmarks...$(NC)"
	@$(PYTEST) --benchmark-only 2>/dev/null || echo "$(YELLOW)Install pytest-benchmark for benchmarks$(NC)"

## Dependencies
deps:
	@echo "$(GREEN)Installing dependencies...$(NC)"
	@$(PIP) install -e .
	@echo "$(GREEN)Dependencies installed$(NC)"

deps-update:
	@echo "$(GREEN)Updating dependencies...$(NC)"
	@$(PIP) install --upgrade pip
	@$(PIP) install -e ".[dev,http,grpc]" --upgrade
	@echo "$(GREEN)Dependencies updated$(NC)"

venv:
	@echo "$(GREEN)Creating virtual environment...$(NC)"
	@$(PYTHON) -m venv venv
	@echo "$(GREEN)Virtual environment created$(NC)"
	@echo "$(YELLOW)Activate with: source venv/bin/activate$(NC)"

verify:
	@echo "$(GREEN)Verifying dependencies...$(NC)"
	@$(PIP) check
	@echo "$(GREEN)Dependencies verified$(NC)"

## Code quality
lint:
	@echo "$(GREEN)Running linter...$(NC)"
	@$(RUFF) check $(SRC_DIR)/ $(TESTS_DIR)/
	@echo "$(GREEN)Lint complete$(NC)"

lint-fix:
	@echo "$(GREEN)Running linter with auto-fix...$(NC)"
	@$(RUFF) check $(SRC_DIR)/ $(TESTS_DIR)/ --fix
	@echo "$(GREEN)Lint fix complete$(NC)"

fmt:
	@echo "$(GREEN)Formatting code...$(NC)"
	@$(BLACK) $(SRC_DIR)/ $(TESTS_DIR)/
	@$(ISORT) $(SRC_DIR)/ $(TESTS_DIR)/
	@echo "$(GREEN)Code formatted$(NC)"

fmt-check:
	@echo "$(GREEN)Checking code formatting...$(NC)"
	@$(BLACK) $(SRC_DIR)/ $(TESTS_DIR)/ --check
	@$(ISORT) $(SRC_DIR)/ $(TESTS_DIR)/ --check-only
	@echo "$(GREEN)Format check complete$(NC)"

vet:
	@echo "$(GREEN)Running code analysis...$(NC)"
	@$(RUFF) check $(SRC_DIR)/ --select=E,W,F
	@echo "$(GREEN)Vet complete$(NC)"

typecheck:
	@echo "$(GREEN)Running type checker...$(NC)"
	@$(MYPY) $(SRC_DIR)/
	@echo "$(GREEN)Type check complete$(NC)"

security:
	@echo "$(GREEN)Running security scan...$(NC)"
	@if command -v bandit >/dev/null 2>&1; then \
		bandit -r $(SRC_DIR)/ -ll; \
	else \
		echo "$(YELLOW)bandit not installed. Install with: pip install bandit$(NC)"; \
	fi
	@echo "$(GREEN)Security scan complete$(NC)"

check: fmt-check lint typecheck test
	@echo "$(GREEN)All checks passed$(NC)"

## Cleanup
clean:
	@echo "$(GREEN)Cleaning build artifacts...$(NC)"
	@rm -rf $(BUILD_DIR)/
	@rm -rf $(DIST_DIR)/
	@rm -rf *.egg-info/
	@rm -rf $(SRC_DIR)/*.egg-info/
	@rm -rf .pytest_cache/
	@rm -rf .mypy_cache/
	@rm -rf .ruff_cache/
	@rm -rf $(COVERAGE_DIR)/
	@rm -rf .coverage
	@rm -rf coverage*.xml
	@rm -rf _generated/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name ".coverage.*" -delete 2>/dev/null || true
	@echo "$(GREEN)Clean complete$(NC)"

## Installation
install:
	@echo "$(GREEN)Installing package...$(NC)"
	@$(PIP) install .
	@echo "$(GREEN)Package installed$(NC)"

install-dev:
	@echo "$(GREEN)Installing package in development mode...$(NC)"
	@$(PIP) install -e ".[dev,http,grpc]"
	@pre-commit install 2>/dev/null || true
	@echo "$(GREEN)Development installation complete$(NC)"

uninstall:
	@echo "$(GREEN)Uninstalling package...$(NC)"
	@$(PIP) uninstall -y telemetryflow-python-sdk
	@echo "$(GREEN)Package uninstalled$(NC)"

## Publishing
publish: build
	@echo "$(GREEN)Publishing to PyPI...$(NC)"
	@$(TWINE) upload $(DIST_DIR)/*
	@echo "$(GREEN)Published to PyPI$(NC)"

publish-test: build
	@echo "$(GREEN)Publishing to Test PyPI...$(NC)"
	@$(TWINE) upload --repository testpypi $(DIST_DIR)/*
	@echo "$(GREEN)Published to Test PyPI$(NC)"

## CI pipeline
ci: deps-update check
	@echo "$(GREEN)CI pipeline completed$(NC)"

release-check:
	@echo "$(GREEN)Checking release readiness...$(NC)"
	@echo "$(BLUE)1. Running format check...$(NC)"
	@$(MAKE) fmt-check
	@echo "$(BLUE)2. Running linter...$(NC)"
	@$(MAKE) lint
	@echo "$(BLUE)3. Running type checker...$(NC)"
	@$(MAKE) typecheck
	@echo "$(BLUE)4. Running tests...$(NC)"
	@$(MAKE) test
	@echo "$(BLUE)5. Building...$(NC)"
	@$(MAKE) build
	@echo "$(GREEN)Release checks passed$(NC)"

## Documentation
docs:
	@echo "$(GREEN)Documentation locations:$(NC)"
	@echo "  - Architecture: $(DOCS_DIR)/ARCHITECTURE.md"
	@echo "  - Quick Start: $(DOCS_DIR)/QUICKSTART.md"
	@echo "  - API Reference: $(DOCS_DIR)/API_REFERENCE.md"
	@echo "  - Generator: $(DOCS_DIR)/GENERATOR.md"
	@echo "  - Testing: $(DOCS_DIR)/TESTING.md"
	@echo "  - Build System: $(DOCS_DIR)/BUILD-SYSTEM.md"
	@echo "  - Contributing: CONTRIBUTING.md"

## Docker
docker-build:
	@echo "$(GREEN)Building Docker image...$(NC)"
	@docker build -t telemetryflow-python-sdk:latest .
	@echo "$(GREEN)Docker image built$(NC)"

docker-push: docker-build
	@echo "$(GREEN)Pushing Docker image...$(NC)"
	@docker push telemetryflow/telemetryflow-python-sdk:$(VERSION)
	@docker push telemetryflow/telemetryflow-python-sdk:latest

# ===========================================================================
# CI-Specific Targets
# ===========================================================================
# These targets are optimized for CI environments with coverage output
# and proper exit codes for CI systems.

.PHONY: ci-deps ci-lint ci-test ci-test-unit ci-test-integration ci-build ci-security ci-coverage

## CI: Install dependencies
ci-deps:
	@echo "$(GREEN)Installing CI dependencies...$(NC)"
	@$(PIP) install --upgrade pip
	@$(PIP) install -e ".[dev,http,grpc]"
	@echo "$(GREEN)CI dependencies installed$(NC)"

## CI: Run full lint suite
ci-lint: fmt-check lint typecheck
	@echo "$(GREEN)CI lint suite complete$(NC)"

## CI: Run unit tests with coverage
ci-test-unit:
	@echo "$(GREEN)Running unit tests (CI mode)...$(NC)"
	@$(PYTEST) $(TESTS_DIR)/unit/ -v --tb=short --cov=$(SRC_DIR)/telemetryflow --cov-report=xml:coverage-unit.xml --cov-report=term-missing --junitxml=junit-unit.xml
	@echo "$(GREEN)Unit tests complete$(NC)"

## CI: Run integration tests with coverage
ci-test-integration:
	@echo "$(GREEN)Running integration tests (CI mode)...$(NC)"
	@$(PYTEST) $(TESTS_DIR)/integration/ -v -m integration --tb=short --cov=$(SRC_DIR)/telemetryflow --cov-append --cov-report=xml:coverage-integration.xml --junitxml=junit-integration.xml || true
	@echo "$(GREEN)Integration tests complete$(NC)"

## CI: Run all tests
ci-test: ci-test-unit ci-test-integration
	@echo "$(GREEN)CI test suite complete$(NC)"

## CI: Build packages
ci-build: clean
	@echo "$(GREEN)Building packages (CI mode)...$(NC)"
	@$(BUILD)
	@echo "$(GREEN)CI build complete$(NC)"
	@ls -la $(DIST_DIR)/

## CI: Security scan
ci-security:
	@echo "$(GREEN)Running security scan (CI mode)...$(NC)"
	@$(PIP) install bandit bandit-sarif-formatter safety 2>/dev/null || true
	@bandit -r $(SRC_DIR)/ --format sarif --output bandit-results.sarif || true
	@safety check --json > safety-results.json 2>/dev/null || true
	@echo "$(GREEN)Security scan complete$(NC)"

## CI: Generate coverage reports
ci-coverage:
	@echo "$(GREEN)Generating coverage reports (CI mode)...$(NC)"
	@$(PYTEST) $(TESTS_DIR)/ --cov=$(SRC_DIR)/telemetryflow --cov-report=xml:coverage.xml --cov-report=html:$(COVERAGE_DIR) --cov-report=term-missing -q
	@echo "$(GREEN)Coverage reports generated$(NC)"

## Version info
version:
	@echo "$(GREEN)$(PRODUCT_NAME)$(NC)"
	@echo "  Version:            $(VERSION)"
	@echo "  TFO-Collector:      $(TFO_COLLECTOR_VERSION)"
	@echo "  OTEL Collector:     $(OTEL_VERSION)"
	@echo "  OTEL Python SDK:    $(OTEL_PYTHON_SDK_VERSION)"
	@echo "  Git Commit:         $(GIT_COMMIT)"
	@echo "  Git Branch:         $(GIT_BRANCH)"
	@echo "  Build Time:         $(BUILD_TIME)"
	@echo "  Python Version:     $(PYTHON_VERSION)"
	@echo ""
	@echo "$(YELLOW)TFO v2 API Features:$(NC)"
	@echo "  - v2 endpoints: /v2/traces, /v2/metrics, /v2/logs"
	@echo "  - Collector identity (aligned with tfoidentityextension)"
	@echo "  - Auth headers (aligned with tfoauthextension)"
	@echo "  - Custom endpoint paths (aligned with tfoexporter)"
	@echo ""
	@echo "$(BLUE)SDK Version Info:$(NC)"
	@$(PYTHON) -c "from telemetryflow.version import info; print(info())" 2>/dev/null || echo "  (SDK not installed)"

.DEFAULT_GOAL := help
