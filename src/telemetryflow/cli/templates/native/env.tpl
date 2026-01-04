# =============================================================================
# TelemetryFlow Configuration
# =============================================================================
#
# TelemetryFlow Python SDK - Community Enterprise Observability Platform (CEOP)
# Copyright (c) 2024-2026 DevOpsCorner Indonesia. All rights reserved.
#
# Compatible with TFO-Collector v${tfo_collector_version} (OCB-native)
# SDK Version: ${sdk_version}
#
# See https://docs.telemetryflow.id for more information.
#
# =============================================================================

# -----------------------------------------------------------------------------
# TelemetryFlow API Credentials (REQUIRED for v2 endpoints)
# -----------------------------------------------------------------------------
# Get your API keys from https://app.telemetryflow.id
# API Key format:
#   - Key ID: tfk_<unique_identifier>
#   - Key Secret: tfs_<secret_value>
TELEMETRYFLOW_API_KEY_ID=${api_key_id}
TELEMETRYFLOW_API_KEY_SECRET=${api_key_secret}

# -----------------------------------------------------------------------------
# Service Configuration
# -----------------------------------------------------------------------------
TELEMETRYFLOW_SERVICE_NAME=${service_name}
TELEMETRYFLOW_SERVICE_VERSION=${service_version}
TELEMETRYFLOW_SERVICE_NAMESPACE=telemetryflow

# -----------------------------------------------------------------------------
# Connection Settings
# -----------------------------------------------------------------------------
# OTLP endpoint (gRPC default: 4317, HTTP default: 4318)
TELEMETRYFLOW_ENDPOINT=${endpoint}

# Protocol: grpc or http
TELEMETRYFLOW_PROTOCOL=${protocol}

# Use insecure connection (for local development)
TELEMETRYFLOW_INSECURE=true

# Request timeout
TELEMETRYFLOW_TIMEOUT=10s

# Deployment environment (production, staging, development)
TELEMETRYFLOW_ENVIRONMENT=${environment}

# -----------------------------------------------------------------------------
# TFO v2 API Configuration (aligned with TFO-Collector v1.1.2)
# -----------------------------------------------------------------------------
# TFO v2 API provides enhanced endpoint paths for TelemetryFlow Platform
# Endpoints:
#   - v2: /v2/traces, /v2/metrics, /v2/logs (authenticated)
#   - v1: /v1/traces, /v1/metrics, /v1/logs (community)

# Enable TFO v2 API endpoints (default: true)
TELEMETRYFLOW_USE_V2_API=${use_v2_api}

# v2-only mode: disable v1 endpoints entirely (default: false)
TELEMETRYFLOW_V2_ONLY=${v2_only}

# -----------------------------------------------------------------------------
# Collector Identity (aligned with tfoidentityextension)
# -----------------------------------------------------------------------------
# Identity information sent to TFO-Collector for tracking and correlation

# Unique collector ID (auto-generated if empty)
# TELEMETRYFLOW_COLLECTOR_ID=sdk-python-001

# Human-readable collector name
TELEMETRYFLOW_COLLECTOR_NAME=${collector_name}

# Datacenter/region identifier
TELEMETRYFLOW_DATACENTER=${datacenter}

# Enable resource attribute enrichment
TELEMETRYFLOW_ENRICH_RESOURCES=${enrich_resources}

# -----------------------------------------------------------------------------
# Signal Configuration
# -----------------------------------------------------------------------------
TELEMETRYFLOW_ENABLE_METRICS=${enable_metrics}
TELEMETRYFLOW_ENABLE_LOGS=${enable_logs}
TELEMETRYFLOW_ENABLE_TRACES=${enable_traces}
