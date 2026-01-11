# Monitoring Guide

Comprehensive monitoring and observability guide for Matrix Treasury production environments.

---

## Table of Contents

- [Overview](#overview)
- [Metrics Collection](#metrics-collection)
  - [Prometheus Setup](#prometheus-setup)
  - [Application Metrics](#application-metrics)
  - [Infrastructure Metrics](#infrastructure-metrics)
- [Visualization](#visualization)
  - [Grafana Setup](#grafana-setup)
  - [Dashboards](#dashboards)
- [Alerting](#alerting)
  - [Alert Rules](#alert-rules)
  - [Notification Channels](#notification-channels)
- [Logging](#logging)
  - [Application Logging](#application-logging)
  - [Log Aggregation](#log-aggregation)
- [Distributed Tracing](#distributed-tracing)
- [Health Checks](#health-checks)
- [Performance Monitoring](#performance-monitoring)
- [Security Monitoring](#security-monitoring)
- [Business Metrics](#business-metrics)
- [Troubleshooting](#troubleshooting)

---

## Overview

Matrix Treasury monitoring stack provides comprehensive observability across all system components:

```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Backend API  │  │  Frontend UI │  │  Database    │  │
│  │  (FastAPI)   │  │   (React)    │  │ (PostgreSQL) │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                  │           │
│         └─────────────────┴──────────────────┘           │
│                           │                              │
└───────────────────────────┼──────────────────────────────┘
                            │
                ┌───────────▼───────────┐
                │   Metrics Exporters    │
                │ - prometheus_client    │
                │ - postgres_exporter    │
                │ - redis_exporter       │
                │ - node_exporter        │
                └───────────┬───────────┘
                            │
                ┌───────────▼───────────┐
                │      Prometheus       │
                │  (Metrics Storage)    │
                └───────────┬───────────┘
                            │
           ┌────────────────┼────────────────┐
           │                │                │
  ┌────────▼────────┐  ┌───▼────┐  ┌───────▼────────┐
  │    Grafana      │  │ Alerts │  │  Alertmanager  │
  │  (Dashboards)   │  └────────┘  │ (Notifications)│
  └─────────────────┘               └────────────────┘
```

### Monitoring Goals

1. **Availability**: Track uptime and service health
2. **Performance**: Monitor response times and throughput
3. **Capacity**: Track resource utilization and growth
4. **Security**: Detect anomalies and security events
5. **Business**: Monitor treasury metrics and agent activity

---

## Metrics Collection

### Prometheus Setup

#### Installation

The Prometheus service is included in `docker-compose.yml`:

```yaml
prometheus:
  image: prom/prometheus:latest
  container_name: matrix-treasury-prometheus
  volumes:
    - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    - ./monitoring/prometheus/alerts.yml:/etc/prometheus/alerts.yml
    - prometheus_data:/prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
    - '--storage.tsdb.retention.time=30d'
    - '--web.console.libraries=/usr/share/prometheus/console_libraries'
    - '--web.console.templates=/usr/share/prometheus/consoles'
    - '--web.enable-lifecycle'
  ports:
    - "9090:9090"
  networks:
    - matrix-network
  restart: unless-stopped
```

Start Prometheus:

```bash
docker compose up -d prometheus

# Verify Prometheus is running
curl http://localhost:9090/-/healthy

# Check configuration
curl http://localhost:9090/api/v1/status/config
```

#### Configuration

`monitoring/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'matrix-treasury'
    environment: 'production'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

# Load alert rules
rule_files:
  - 'alerts.yml'

# Scrape configurations
scrape_configs:
  # Matrix Treasury API
  - job_name: 'matrix-treasury-api'
    static_configs:
      - targets: ['treasury-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s

  # PostgreSQL
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Redis
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Node/Container metrics
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

#### Service Discovery (Kubernetes)

For Kubernetes deployments, use service discovery:

```yaml
scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - matrix-treasury
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
```

### Application Metrics

#### FastAPI Metrics

Add Prometheus metrics to the FastAPI application:

```python
# src/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request
import time

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# Treasury metrics
treasury_usdc_balance = Gauge(
    'treasury_usdc_balance',
    'Current USDC balance'
)

treasury_mxu_supply = Gauge(
    'treasury_mxu_supply',
    'Total MXU supply'
)

treasury_coverage_ratio = Gauge(
    'treasury_coverage_ratio',
    'Reserve coverage ratio'
)

treasury_runway_days = Gauge(
    'treasury_runway_days',
    'Estimated runway in days'
)

# Agent metrics
active_agents = Gauge(
    'active_agents',
    'Number of active agents'
)

agent_transactions_total = Counter(
    'agent_transactions_total',
    'Total agent transactions',
    ['agent_id', 'type']
)

# Credit system metrics
active_loans = Gauge(
    'active_loans',
    'Number of active loans'
)

total_debt = Gauge(
    'total_debt',
    'Total outstanding debt'
)

# Security metrics
failed_login_attempts = Counter(
    'failed_login_attempts_total',
    'Total failed login attempts',
    ['username']
)

sybil_detections = Counter(
    'sybil_detections_total',
    'Total sybil attack detections',
    ['agent_id']
)

# Multi-currency metrics
currency_balance = Gauge(
    'currency_balance',
    'Balance by currency',
    ['currency', 'network']
)
```

#### Metrics Endpoint

```python
# src/main.py
from fastapi import FastAPI, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from src.monitoring.metrics import *

app = FastAPI()

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# Middleware to track request metrics
@app.middleware("http")
async def track_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    return response
```

#### Update Business Metrics

```python
# src/services/treasury_service.py
from src.monitoring.metrics import (
    treasury_usdc_balance,
    treasury_mxu_supply,
    treasury_coverage_ratio,
    treasury_runway_days
)

async def update_treasury_metrics():
    """Update treasury metrics for Prometheus"""
    status = await get_treasury_status()

    treasury_usdc_balance.set(status['usdc_balance'])
    treasury_mxu_supply.set(status['mxu_supply'])
    treasury_coverage_ratio.set(status['coverage_ratio'])
    treasury_runway_days.set(status['runway_days'])

# Update metrics periodically
from fastapi_utils.tasks import repeat_every

@app.on_event("startup")
@repeat_every(seconds=60)  # Update every minute
async def update_metrics():
    await update_treasury_metrics()
    # Update other metrics...
```

### Infrastructure Metrics

#### PostgreSQL Exporter

Add to `docker-compose.yml`:

```yaml
postgres-exporter:
  image: prometheuscommunity/postgres-exporter
  container_name: matrix-treasury-postgres-exporter
  environment:
    DATA_SOURCE_NAME: "postgresql://matrix:${DB_PASSWORD}@postgres:5432/matrix_treasury?sslmode=disable"
  ports:
    - "9187:9187"
  networks:
    - matrix-network
  depends_on:
    - postgres
  restart: unless-stopped
```

#### Redis Exporter

```yaml
redis-exporter:
  image: oliver006/redis_exporter
  container_name: matrix-treasury-redis-exporter
  environment:
    REDIS_ADDR: redis:6379
    REDIS_PASSWORD: ${REDIS_PASSWORD}
  ports:
    - "9121:9121"
  networks:
    - matrix-network
  depends_on:
    - redis
  restart: unless-stopped
```

#### Node Exporter

```yaml
node-exporter:
  image: prom/node-exporter:latest
  container_name: matrix-treasury-node-exporter
  command:
    - '--path.rootfs=/host'
  volumes:
    - '/:/host:ro,rslave'
  ports:
    - "9100:9100"
  networks:
    - matrix-network
  restart: unless-stopped
```

---

## Visualization

### Grafana Setup

#### Installation

Grafana is included in `docker-compose.yml`:

```yaml
grafana:
  image: grafana/grafana:latest
  container_name: matrix-treasury-grafana
  environment:
    - GF_SECURITY_ADMIN_USER=${GRAFANA_USER:-admin}
    - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin_change_me}
    - GF_USERS_ALLOW_SIGN_UP=false
    - GF_SERVER_ROOT_URL=http://localhost:3000
    - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource,grafana-piechart-panel
  volumes:
    - grafana_data:/var/lib/grafana
    - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
    - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
  ports:
    - "3000:3000"
  depends_on:
    - prometheus
  networks:
    - matrix-network
  restart: unless-stopped
```

Start Grafana:

```bash
docker compose up -d grafana

# Access Grafana
open http://localhost:3000

# Default credentials (change these!)
# Username: admin
# Password: admin_change_me
```

#### Data Source Configuration

Create `monitoring/grafana/datasources/prometheus.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
    jsonData:
      timeInterval: "15s"
      queryTimeout: "60s"
```

### Dashboards

#### Treasury Overview Dashboard

Create `monitoring/grafana/dashboards/treasury-overview.json`:

```json
{
  "dashboard": {
    "title": "Matrix Treasury - Overview",
    "panels": [
      {
        "title": "USDC Balance",
        "type": "stat",
        "targets": [
          {
            "expr": "treasury_usdc_balance",
            "legendFormat": "USDC Balance"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "currencyUSD",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 1000, "color": "yellow"},
                {"value": 5000, "color": "green"}
              ]
            }
          }
        }
      },
      {
        "title": "Coverage Ratio",
        "type": "gauge",
        "targets": [
          {
            "expr": "treasury_coverage_ratio",
            "legendFormat": "Coverage Ratio"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 1.0, "color": "yellow"},
                {"value": 1.5, "color": "green"}
              ]
            },
            "min": 0,
            "max": 2
          }
        }
      },
      {
        "title": "Runway Days",
        "type": "stat",
        "targets": [
          {
            "expr": "treasury_runway_days",
            "legendFormat": "Days"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "days",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 30, "color": "yellow"},
                {"value": 60, "color": "green"}
              ]
            }
          }
        }
      },
      {
        "title": "Active Agents",
        "type": "graph",
        "targets": [
          {
            "expr": "active_agents",
            "legendFormat": "Active Agents"
          }
        ]
      },
      {
        "title": "Transaction Volume (24h)",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(agent_transactions_total[24h]))",
            "legendFormat": "Transactions/sec"
          }
        ]
      },
      {
        "title": "Multi-Currency Balances",
        "type": "piechart",
        "targets": [
          {
            "expr": "currency_balance",
            "legendFormat": "{{currency}}"
          }
        ]
      }
    ]
  }
}
```

#### API Performance Dashboard

```json
{
  "dashboard": {
    "title": "Matrix Treasury - API Performance",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (endpoint)",
            "legendFormat": "{{endpoint}}"
          }
        ]
      },
      {
        "title": "Request Latency (p50, p90, p99)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "p50"
          },
          {
            "expr": "histogram_quantile(0.90, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "p90"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "p99"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))",
            "legendFormat": "Error Rate"
          }
        ]
      },
      {
        "title": "Requests by Status Code",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (status)",
            "legendFormat": "{{status}}"
          }
        ]
      }
    ]
  }
}
```

#### System Resources Dashboard

```json
{
  "dashboard": {
    "title": "Matrix Treasury - System Resources",
    "panels": [
      {
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100",
            "legendFormat": "Memory %"
          }
        ]
      },
      {
        "title": "Disk Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "(node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100",
            "legendFormat": "{{mountpoint}}"
          }
        ]
      },
      {
        "title": "Network I/O",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(node_network_receive_bytes_total[5m])",
            "legendFormat": "RX {{device}}"
          },
          {
            "expr": "rate(node_network_transmit_bytes_total[5m])",
            "legendFormat": "TX {{device}}"
          }
        ]
      }
    ]
  }
}
```

#### Database Dashboard

```json
{
  "dashboard": {
    "title": "Matrix Treasury - Database",
    "panels": [
      {
        "title": "Active Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_activity_count",
            "legendFormat": "Connections"
          }
        ]
      },
      {
        "title": "Transaction Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(pg_stat_database_xact_commit[5m])",
            "legendFormat": "Commits"
          },
          {
            "expr": "rate(pg_stat_database_xact_rollback[5m])",
            "legendFormat": "Rollbacks"
          }
        ]
      },
      {
        "title": "Query Duration (p99)",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_statements_mean_exec_time_seconds{quantile=\"0.99\"}",
            "legendFormat": "{{query}}"
          }
        ]
      },
      {
        "title": "Database Size",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_database_size_bytes{datname=\"matrix_treasury\"}",
            "legendFormat": "Size"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "bytes"
          }
        }
      }
    ]
  }
}
```

---

## Alerting

### Alert Rules

Create `monitoring/prometheus/alerts.yml`:

```yaml
groups:
  - name: treasury_critical
    interval: 30s
    rules:
      # Treasury health alerts
      - alert: CriticalReserveDepletion
        expr: treasury_coverage_ratio < 1.0
        for: 5m
        labels:
          severity: critical
          component: treasury
        annotations:
          summary: "Critical reserve depletion"
          description: "Coverage ratio is {{ $value | humanize }} (threshold: 1.0)"
          action: "Immediate funding required"

      - alert: LowRunway
        expr: treasury_runway_days < 7
        for: 10m
        labels:
          severity: critical
          component: treasury
        annotations:
          summary: "Low runway detected"
          description: "Only {{ $value | humanize }} days of runway remaining"
          action: "Urgent: Secure additional funding"

      - alert: WarningReserveDepletion
        expr: treasury_coverage_ratio < 1.5 and treasury_coverage_ratio >= 1.0
        for: 15m
        labels:
          severity: warning
          component: treasury
        annotations:
          summary: "Reserve coverage low"
          description: "Coverage ratio is {{ $value | humanize }} (threshold: 1.5)"
          action: "Monitor closely and prepare funding"

  - name: api_performance
    interval: 30s
    rules:
      # API performance alerts
      - alert: HighAPILatency
        expr: histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 1.0
        for: 5m
        labels:
          severity: warning
          component: api
        annotations:
          summary: "High API latency"
          description: "99th percentile latency is {{ $value | humanizePercentage }}s"
          action: "Investigate slow queries and optimize"

      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.01
        for: 5m
        labels:
          severity: critical
          component: api
        annotations:
          summary: "High error rate"
          description: "Error rate is {{ $value | humanizePercentage }}"
          action: "Check application logs immediately"

      - alert: APIDown
        expr: up{job="matrix-treasury-api"} == 0
        for: 1m
        labels:
          severity: critical
          component: api
        annotations:
          summary: "API is down"
          description: "Matrix Treasury API is not responding"
          action: "Restart service and investigate"

  - name: database_alerts
    interval: 30s
    rules:
      # Database alerts
      - alert: HighDatabaseConnections
        expr: pg_stat_activity_count / pg_settings_max_connections > 0.8
        for: 5m
        labels:
          severity: warning
          component: database
        annotations:
          summary: "High database connection usage"
          description: "Using {{ $value | humanizePercentage }} of max connections"
          action: "Investigate connection leaks"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
          component: database
        annotations:
          summary: "Database is down"
          description: "PostgreSQL is not responding"
          action: "Restart database immediately"

      - alert: SlowQueries
        expr: pg_stat_statements_mean_exec_time_seconds{quantile="0.99"} > 5
        for: 10m
        labels:
          severity: warning
          component: database
        annotations:
          summary: "Slow database queries detected"
          description: "99th percentile query time is {{ $value }}s"
          action: "Optimize slow queries"

  - name: system_resources
    interval: 30s
    rules:
      # Resource alerts
      - alert: HighCPUUsage
        expr: 100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 90
        for: 10m
        labels:
          severity: warning
          component: system
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value | humanize }}%"
          action: "Scale up or optimize workload"

      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 90
        for: 10m
        labels:
          severity: warning
          component: system
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanize }}%"
          action: "Scale up or investigate memory leaks"

      - alert: DiskSpaceLow
        expr: (node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100 > 80
        for: 5m
        labels:
          severity: warning
          component: system
        annotations:
          summary: "Low disk space"
          description: "Disk usage is {{ $value | humanize }}%"
          action: "Clean up disk or expand storage"

      - alert: DiskSpaceCritical
        expr: (node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100 > 95
        for: 1m
        labels:
          severity: critical
          component: system
        annotations:
          summary: "Critical disk space"
          description: "Disk usage is {{ $value | humanize }}%"
          action: "Immediate action required to free space"

  - name: security_alerts
    interval: 30s
    rules:
      # Security alerts
      - alert: HighFailedLogins
        expr: rate(failed_login_attempts_total[5m]) > 10
        for: 5m
        labels:
          severity: warning
          component: security
        annotations:
          summary: "High rate of failed login attempts"
          description: "{{ $value }} failed logins per second"
          action: "Possible brute force attack - investigate"

      - alert: SybilAttackDetected
        expr: rate(sybil_detections_total[5m]) > 0
        for: 1m
        labels:
          severity: critical
          component: security
        annotations:
          summary: "Sybil attack detected"
          description: "Suspicious agent behavior detected"
          action: "Review flagged agents immediately"

  - name: business_metrics
    interval: 60s
    rules:
      # Business alerts
      - alert: HighUnemploymentRate
        expr: (1 - active_agents / total_agents) > 0.5
        for: 30m
        labels:
          severity: warning
          component: business
        annotations:
          summary: "High agent unemployment"
          description: "{{ $value | humanizePercentage }} of agents are inactive"
          action: "Investigate agent incentives"

      - alert: LoanDefaultRisk
        expr: sum(loan_past_due_days > 30) / sum(active_loans) > 0.1
        for: 1h
        labels:
          severity: warning
          component: business
        annotations:
          summary: "High loan default risk"
          description: "{{ $value | humanizePercentage }} of loans are overdue"
          action: "Review credit policies"
```

### Notification Channels

#### Alertmanager Configuration

Add to `docker-compose.yml`:

```yaml
alertmanager:
  image: prom/alertmanager:latest
  container_name: matrix-treasury-alertmanager
  volumes:
    - ./monitoring/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml
    - alertmanager_data:/alertmanager
  command:
    - '--config.file=/etc/alertmanager/alertmanager.yml'
    - '--storage.path=/alertmanager'
  ports:
    - "9093:9093"
  networks:
    - matrix-network
  restart: unless-stopped
```

Create `monitoring/alertmanager/alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@matrix-treasury.com'
  smtp_auth_username: 'alerts@matrix-treasury.com'
  smtp_auth_password: 'your_password'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'

  routes:
    # Critical alerts go to all channels
    - match:
        severity: critical
      receiver: 'critical-alerts'
      continue: true

    # Warning alerts to email only
    - match:
        severity: warning
      receiver: 'warning-alerts'

receivers:
  - name: 'default'
    email_configs:
      - to: 'team@matrix-treasury.com'

  - name: 'critical-alerts'
    email_configs:
      - to: 'oncall@matrix-treasury.com'
        headers:
          Subject: '[CRITICAL] {{ .GroupLabels.alertname }}'

    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts-critical'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

    pagerduty_configs:
      - service_key: 'your_pagerduty_key'
        description: '{{ .GroupLabels.alertname }}: {{ .GroupLabels.instance }}'

  - name: 'warning-alerts'
    email_configs:
      - to: 'team@matrix-treasury.com'
        headers:
          Subject: '[WARNING] {{ .GroupLabels.alertname }}'

    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts-warning'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']
```

#### Slack Integration

```yaml
slack_configs:
  - api_url: 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX'
    channel: '#treasury-alerts'
    username: 'Matrix Treasury Alerting'
    icon_emoji: ':warning:'
    title: '{{ .GroupLabels.alertname }}'
    text: |
      {{ range .Alerts }}
      *Alert:* {{ .Labels.alertname }}
      *Severity:* {{ .Labels.severity }}
      *Description:* {{ .Annotations.description }}
      *Action:* {{ .Annotations.action }}
      {{ end }}
```

#### Discord Integration

```yaml
webhook_configs:
  - url: 'https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN'
    send_resolved: true
```

---

## Logging

### Application Logging

#### Structured Logging

Configure structured JSON logging:

```python
# src/core/logging_config.py
import logging
import json
from datetime import datetime
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['service'] = 'matrix-treasury-api'

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': CustomJsonFormatter,
            'format': '%(timestamp)s %(level)s %(name)s %(message)s'
        },
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/treasury.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'json'
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/error.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'json',
            'level': 'ERROR'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file', 'error_file', 'console']
    },
    'loggers': {
        'uvicorn': {
            'level': 'INFO'
        },
        'sqlalchemy': {
            'level': 'WARNING'
        }
    }
}
```

#### Log Context

Add context to logs:

```python
import logging
from contextvars import ContextVar

request_id: ContextVar[str] = ContextVar('request_id', default='')

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    req_id = str(uuid.uuid4())
    request_id.set(req_id)

    logger.info(
        "Request started",
        extra={
            "request_id": req_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host
        }
    )

    response = await call_next(request)

    logger.info(
        "Request completed",
        extra={
            "request_id": req_id,
            "status_code": response.status_code
        }
    )

    return response
```

### Log Aggregation

#### ELK Stack (Elasticsearch, Logstash, Kibana)

Add to `docker-compose.yml`:

```yaml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
  container_name: matrix-treasury-elasticsearch
  environment:
    - discovery.type=single-node
    - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    - xpack.security.enabled=false
  volumes:
    - elasticsearch_data:/usr/share/elasticsearch/data
  ports:
    - "9200:9200"
  networks:
    - matrix-network

logstash:
  image: docker.elastic.co/logstash/logstash:8.11.0
  container_name: matrix-treasury-logstash
  volumes:
    - ./monitoring/logstash/logstash.conf:/usr/share/logstash/pipeline/logstash.conf
  ports:
    - "5000:5000"
  networks:
    - matrix-network
  depends_on:
    - elasticsearch

kibana:
  image: docker.elastic.co/kibana/kibana:8.11.0
  container_name: matrix-treasury-kibana
  environment:
    - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
  ports:
    - "5601:5601"
  networks:
    - matrix-network
  depends_on:
    - elasticsearch
```

#### Loki + Grafana

Alternative lightweight logging:

```yaml
loki:
  image: grafana/loki:latest
  container_name: matrix-treasury-loki
  ports:
    - "3100:3100"
  volumes:
    - ./monitoring/loki/loki-config.yml:/etc/loki/local-config.yaml
    - loki_data:/loki
  networks:
    - matrix-network
  command: -config.file=/etc/loki/local-config.yaml

promtail:
  image: grafana/promtail:latest
  container_name: matrix-treasury-promtail
  volumes:
    - ./logs:/var/log/treasury
    - ./monitoring/promtail/promtail-config.yml:/etc/promtail/config.yml
  networks:
    - matrix-network
  command: -config.file=/etc/promtail/config.yml
```

---

## Distributed Tracing

### OpenTelemetry

Install OpenTelemetry:

```bash
pip install opentelemetry-api opentelemetry-sdk \
  opentelemetry-instrumentation-fastapi \
  opentelemetry-exporter-jaeger
```

Configure tracing:

```python
# src/core/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def setup_tracing(app):
    trace.set_tracer_provider(TracerProvider())

    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",
        agent_port=6831,
    )

    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )

    FastAPIInstrumentor.instrument_app(app)
```

---

## Health Checks

### Comprehensive Health Endpoint

```python
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    checks = {
        "api": "ok",
        "database": await check_database(),
        "redis": await check_redis(),
        "blockchain": await check_blockchain(),
        "disk_space": check_disk_space(),
        "memory": check_memory()
    }

    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"

    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": checks
    }

async def check_database():
    try:
        async with db.async_session() as session:
            await session.execute("SELECT 1")
        return "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return "error"

async def check_redis():
    try:
        await redis_client.ping()
        return "ok"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return "error"
```

---

## Performance Monitoring

### Query Performance

Monitor slow database queries:

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > 0.1:  # Log queries slower than 100ms
        logger.warning(
            "Slow query detected",
            extra={
                "duration": total,
                "query": statement[:200]
            }
        )
```

### APM (Application Performance Monitoring)

Consider integrating APM tools:

- **New Relic**
- **Datadog**
- **Sentry** (for error tracking)
- **Elastic APM**

---

## Security Monitoring

### Audit Logging

Log all security-relevant events:

```python
def log_security_event(event_type, user, details):
    logger.info(
        "Security event",
        extra={
            "event_type": event_type,
            "user": user,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
            "ip_address": request.client.host
        }
    )

# Usage
log_security_event("login_success", username, {"method": "password"})
log_security_event("permission_denied", username, {"resource": "/admin"})
log_security_event("config_change", username, {"setting": "autopilot", "value": True})
```

---

## Business Metrics

### Custom Dashboards

Track business KPIs:

- Treasury health score
- Agent productivity
- Transaction success rate
- Revenue/costs
- User growth

---

## Troubleshooting

### Common Issues

**Prometheus not scraping targets:**
```bash
# Check targets
curl http://localhost:9090/api/v1/targets

# Verify service is exposing metrics
curl http://treasury-api:8000/metrics
```

**Grafana dashboard not showing data:**
```bash
# Test Prometheus query
curl 'http://localhost:9090/api/v1/query?query=treasury_usdc_balance'

# Check Grafana data source connection
# Grafana > Configuration > Data Sources > Test
```

**High cardinality issues:**
```python
# Avoid labels with high cardinality (e.g., user IDs)
# BAD:
metric.labels(user_id=user_id).inc()

# GOOD:
metric.labels(user_type=user_type).inc()
```

---

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Matrix Treasury API Reference](/docs/API_REFERENCE.md)
- [Production Checklist](/docs/deployment/production-checklist.md)
