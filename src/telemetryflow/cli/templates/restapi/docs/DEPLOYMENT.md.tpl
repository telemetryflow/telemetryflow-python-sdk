# ${project_name} Deployment Guide

## Overview

This guide covers deploying ${project_name} to various environments.

## Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrations ready
- [ ] Secret keys generated (not default values!)
- [ ] TelemetryFlow API keys configured
- [ ] Health check endpoints verified

## Docker Deployment

### Build Production Image

```bash
docker build -t ${module_name}:latest .
```

### Run Container

```bash
docker run -d \
  --name ${module_name} \
  -p ${server_port}:${server_port} \
  -e ${env_prefix}_DB_HOST=db.example.com \
  -e ${env_prefix}_DB_PASSWORD=secure_password \
  -e ${env_prefix}_SECRET_KEY=your_secret_key \
  -e ${env_prefix}_JWT_SECRET_KEY=your_jwt_secret \
  ${module_name}:latest
```

### Docker Compose (Production)

Create `docker-compose.prod.yml`:

```yaml
services:
  app:
    image: ${module_name}:latest
    ports:
      - "${server_port}:${server_port}"
    environment:
      - ${env_prefix}_DB_HOST=postgres
      - ${env_prefix}_DB_PASSWORD=$${DB_PASSWORD}
      - ${env_prefix}_SECRET_KEY=$${SECRET_KEY}
      - ${env_prefix}_JWT_SECRET_KEY=$${JWT_SECRET_KEY}
      - ${env_prefix}_ENVIRONMENT=production
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:${server_port}/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${db_user}
      POSTGRES_PASSWORD: $${DB_PASSWORD}
      POSTGRES_DB: ${db_name}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${db_user}"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres-data:
```

Run with:

```bash
DB_PASSWORD=secure_password \
SECRET_KEY=your_secret_key \
JWT_SECRET_KEY=your_jwt_secret \
docker compose -f docker-compose.prod.yml up -d
```

## Kubernetes Deployment

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ${module_name}-config
data:
  ${env_prefix}_ENVIRONMENT: "production"
  ${env_prefix}_DB_HOST: "postgres-service"
  ${env_prefix}_DB_PORT: "${db_port}"
  ${env_prefix}_DB_NAME: "${db_name}"
  ${env_prefix}_DB_USER: "${db_user}"
```

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ${module_name}-secret
type: Opaque
stringData:
  ${env_prefix}_DB_PASSWORD: "your_db_password"
  ${env_prefix}_SECRET_KEY: "your_secret_key"
  ${env_prefix}_JWT_SECRET_KEY: "your_jwt_secret"
  TELEMETRYFLOW_API_KEY_ID: "your_api_key_id"
  TELEMETRYFLOW_API_KEY_SECRET: "your_api_key_secret"
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${module_name}
  labels:
    app: ${module_name}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ${module_name}
  template:
    metadata:
      labels:
        app: ${module_name}
    spec:
      containers:
      - name: ${module_name}
        image: ${module_name}:latest
        ports:
        - containerPort: ${server_port}
        envFrom:
        - configMapRef:
            name: ${module_name}-config
        - secretRef:
            name: ${module_name}-secret
        livenessProbe:
          httpGet:
            path: /api/v1/live
            port: ${server_port}
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/v1/ready
            port: ${server_port}
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ${module_name}-service
spec:
  selector:
    app: ${module_name}
  ports:
  - protocol: TCP
    port: 80
    targetPort: ${server_port}
  type: ClusterIP
```

### Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ${module_name}-ingress
  annotations:
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ${module_name}-service
            port:
              number: 80
```

## Database Migration

### Before Deployment

```bash
# Run migrations
alembic upgrade head
```

### CI/CD Migration

Include in your deployment pipeline:

```yaml
# GitHub Actions example
- name: Run Migrations
  run: |
    alembic upgrade head
  env:
    ${env_prefix}_DB_HOST: $${{ secrets.DB_HOST }}
    ${env_prefix}_DB_PASSWORD: $${{ secrets.DB_PASSWORD }}
```

## Health Checks

### Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `/api/v1/health` | Overall health | `{"status": "healthy"}` |
| `/api/v1/ready` | Readiness | `{"status": "ready"}` |
| `/api/v1/live` | Liveness | `{"status": "alive"}` |

### Load Balancer Configuration

Configure your load balancer to use `/api/v1/health` for health checks.

## Monitoring

### TelemetryFlow

Configure TelemetryFlow for production monitoring:

```bash
TELEMETRYFLOW_API_KEY_ID=prod_key_id
TELEMETRYFLOW_API_KEY_SECRET=prod_key_secret
TELEMETRYFLOW_SERVICE_NAME=${service_name}
TELEMETRYFLOW_ENVIRONMENT=production
```

### Metrics

Key metrics to monitor:

- Request latency (p50, p95, p99)
- Error rate
- Active connections
- Database connection pool usage

## Security Considerations

1. **Never use default secret keys in production**
2. **Use HTTPS in production**
3. **Enable rate limiting**
4. **Rotate JWT secrets periodically**
5. **Use secrets management (Vault, AWS Secrets Manager)**
6. **Keep dependencies updated**

## Rollback Procedure

### Docker

```bash
# Tag current as backup
docker tag ${module_name}:latest ${module_name}:backup

# Pull previous version
docker pull ${module_name}:previous

# Restart with previous version
docker stop ${module_name}
docker run -d --name ${module_name} ${module_name}:previous
```

### Kubernetes

```bash
# Rollback deployment
kubectl rollout undo deployment/${module_name}

# Check rollout status
kubectl rollout status deployment/${module_name}
```

### Database

```bash
# Rollback last migration
alembic downgrade -1
```

---

*Generated by TelemetryFlow RESTful API Generator*
