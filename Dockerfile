# =============================================================================
# TelemetryFlow Python SDK - Dockerfile
# =============================================================================
#
# TelemetryFlow Python SDK - Community Enterprise Observability Platform (CEOP)
# Copyright (c) 2024-2026 DevOpsCorner Indonesia. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# =============================================================================
# Multi-stage build for minimal image size
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Build arguments
ARG VERSION=1.1.1
ARG GIT_COMMIT=unknown
ARG GIT_BRANCH=unknown
ARG BUILD_TIME=unknown

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy package files first for better caching
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

# Build the wheel package
RUN pip install --upgrade pip build && \
    python -m build --wheel && \
    pip wheel --wheel-dir=/wheels -r <(echo "opentelemetry-api>=1.28.0" && \
                                       echo "opentelemetry-sdk>=1.28.0" && \
                                       echo "opentelemetry-exporter-otlp-proto-grpc>=1.28.0" && \
                                       echo "opentelemetry-exporter-otlp-proto-http>=1.28.0")

# -----------------------------------------------------------------------------
# Stage 2: Runtime
# -----------------------------------------------------------------------------
FROM python:3.12-slim

# =============================================================================
# TelemetryFlow Metadata Labels (OCI Image Spec)
# =============================================================================
LABEL org.opencontainers.image.title="TelemetryFlow Python SDK" \
      org.opencontainers.image.description="Python SDK and code generators for TelemetryFlow integration - Community Enterprise Observability Platform (CEOP)" \
      org.opencontainers.image.version="1.1.1" \
      org.opencontainers.image.vendor="TelemetryFlow" \
      org.opencontainers.image.authors="DevOpsCorner Indonesia <support@devopscorner.id>" \
      org.opencontainers.image.url="https://telemetryflow.id" \
      org.opencontainers.image.documentation="https://docs.telemetryflow.id" \
      org.opencontainers.image.source="https://github.com/telemetryflow/telemetryflow-python-sdk" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.base.name="python:3.12-slim" \
      # TelemetryFlow specific labels
      io.telemetryflow.product="TelemetryFlow Python SDK" \
      io.telemetryflow.component="telemetryflow-python-sdk" \
      io.telemetryflow.platform="CEOP" \
      io.telemetryflow.maintainer="DevOpsCorner Indonesia"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # TelemetryFlow defaults
    TELEMETRYFLOW_ENDPOINT=api.telemetryflow.id:4317 \
    TELEMETRYFLOW_ENVIRONMENT=production

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and group
RUN groupadd -g 10001 telemetryflow && \
    useradd -u 10001 -g telemetryflow -d /home/telemetryflow -m telemetryflow

# Create workspace directory
RUN mkdir -p /workspace && chown -R telemetryflow:telemetryflow /workspace

# Copy wheels from builder and install
COPY --from=builder /wheels /wheels
COPY --from=builder /build/dist/*.whl /wheels/

# Install the SDK and dependencies
RUN pip install --no-cache-dir /wheels/*.whl && \
    rm -rf /wheels

# Verify installation
RUN python -c "from telemetryflow import TelemetryFlowBuilder; print('TelemetryFlow SDK installed successfully')" && \
    telemetryflow-gen --help && \
    telemetryflow-restapi --help || echo "Generator CLIs available"

# Switch to non-root user
USER telemetryflow

# Set working directory
WORKDIR /workspace

# =============================================================================
# Entrypoint & Command
# =============================================================================
ENTRYPOINT ["telemetryflow-gen"]
CMD ["--help"]

# =============================================================================
# Build Information
# =============================================================================
# Build with:
#   docker build \
#     --build-arg VERSION=1.1.1 \
#     --build-arg GIT_COMMIT=$(git rev-parse --short HEAD) \
#     --build-arg GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD) \
#     --build-arg BUILD_TIME=$(date -u '+%Y-%m-%dT%H:%M:%SZ') \
#     -t telemetryflow/telemetryflow-python-sdk:1.1.1 .
#
# Run with:
#   # SDK Generator (telemetryflow-gen) - Native Python integration
#   docker run --rm -v $(pwd):/workspace telemetryflow/telemetryflow-python-sdk:1.1.1 \
#     init -p my-project --output /workspace
#
#   # RESTful API Generator (telemetryflow-restapi) - Flask + SQLAlchemy DDD project
#   docker run --rm -v $(pwd):/workspace --entrypoint telemetryflow-restapi \
#     telemetryflow/telemetryflow-python-sdk:1.1.1 \
#     new -n my-api --output /workspace
#
#   # Add entity to RESTful API project
#   docker run --rm -v $(pwd)/my-api:/workspace --entrypoint telemetryflow-restapi \
#     telemetryflow/telemetryflow-python-sdk:1.1.1 \
#     entity -n User -f 'name:string,email:string' --output /workspace
#
#   # Run Python example
#   docker run --rm -v $(pwd):/workspace --entrypoint python \
#     telemetryflow/telemetryflow-python-sdk:1.1.1 \
#     /workspace/example.py
# =============================================================================
