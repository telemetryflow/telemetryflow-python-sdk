# =============================================================================
# TelemetryFlow Configuration
# =============================================================================
#
# TelemetryFlow Python SDK - Community Enterprise Observability Platform (CEOP)
# Copyright (c) 2024-2026 DevOpsCorner Indonesia. All rights reserved.
#
# See https://docs.telemetryflow.id for more information.
#
# =============================================================================

# Required: API Key credentials
TELEMETRYFLOW_API_KEY_ID=${api_key_id}
TELEMETRYFLOW_API_KEY_SECRET=${api_key_secret}

# Required: Service configuration
TELEMETRYFLOW_SERVICE_NAME=${service_name}
TELEMETRYFLOW_SERVICE_VERSION=${service_version}

# Optional: Endpoint (default: api.telemetryflow.id:4317)
TELEMETRYFLOW_ENDPOINT=${endpoint}

# Optional: Environment (default: production)
TELEMETRYFLOW_ENVIRONMENT=${environment}

# Optional: Service namespace for multi-tenant support
TELEMETRYFLOW_SERVICE_NAMESPACE=telemetryflow

# Optional: Collector ID for distributed collectors
# TELEMETRYFLOW_COLLECTOR_ID=collector-1

# Optional: Enable/disable telemetry types
TELEMETRYFLOW_ENABLE_METRICS=${enable_metrics}
TELEMETRYFLOW_ENABLE_LOGS=${enable_logs}
TELEMETRYFLOW_ENABLE_TRACES=${enable_traces}
