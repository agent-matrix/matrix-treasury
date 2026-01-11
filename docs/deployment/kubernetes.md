# Kubernetes Deployment Guide

Complete Kubernetes deployment guide for Matrix Treasury enterprise platform.

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Cluster Setup](#cluster-setup)
- [Namespace Configuration](#namespace-configuration)
- [Secrets Management](#secrets-management)
- [Database Deployment](#database-deployment)
- [Redis Deployment](#redis-deployment)
- [API Deployment](#api-deployment)
- [Frontend Deployment](#frontend-deployment)
- [Monitoring Stack](#monitoring-stack)
- [Ingress Configuration](#ingress-configuration)
- [Autoscaling](#autoscaling)
- [Persistent Storage](#persistent-storage)
- [Helm Charts](#helm-charts)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

---

## Overview

Matrix Treasury on Kubernetes provides:

- **High Availability**: Multi-replica deployments with automatic failover
- **Auto-Scaling**: Horizontal Pod Autoscaling (HPA) based on CPU/memory
- **Rolling Updates**: Zero-downtime deployments
- **Resource Management**: CPU/memory limits and requests
- **Service Discovery**: Internal DNS-based service discovery
- **Load Balancing**: Automatic load distribution
- **Persistent Storage**: StatefulSets for database workloads

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Ingress (HTTPS)                  │
│         (nginx-ingress / Traefik / ALB)             │
└─────────────────┬───────────────────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
┌───────▼────────┐   ┌──────▼──────────┐
│  Frontend UI   │   │   Backend API   │
│  (Deployment)  │   │  (Deployment)   │
│   3 replicas   │   │   5 replicas    │
└────────────────┘   └────────┬────────┘
                              │
                ┌─────────────┴────────────┐
                │                          │
        ┌───────▼────────┐        ┌───────▼────────┐
        │   PostgreSQL   │        │     Redis      │
        │ (StatefulSet)  │        │  (StatefulSet) │
        └────────────────┘        └────────────────┘
```

---

## Prerequisites

### Required Tools

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
kubectl version --client

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version

# Install k9s (optional but recommended)
curl -sS https://webinstall.dev/k9s | bash
```

### Cluster Requirements

**Minimum** (Development):
- 3 nodes
- 2 CPU, 4GB RAM per node
- 50GB storage

**Recommended** (Production):
- 5+ nodes
- 4 CPU, 16GB RAM per node
- 200GB SSD storage per node
- Multi-zone deployment

### Kubernetes Version

- Kubernetes 1.24+ required
- Kubernetes 1.27+ recommended

---

## Cluster Setup

### Local Development (Minikube)

```bash
# Install minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Start cluster
minikube start --cpus=4 --memory=8192 --disk-size=50g

# Enable addons
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable dashboard
```

### Production Cluster Options

#### AWS EKS

```bash
# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Create cluster
eksctl create cluster \
  --name matrix-treasury \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.xlarge \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 10 \
  --managed
```

#### GCP GKE

```bash
# Create cluster
gcloud container clusters create matrix-treasury \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-4 \
  --enable-autoscaling \
  --min-nodes 3 \
  --max-nodes 10
```

#### Azure AKS

```bash
# Create cluster
az aks create \
  --resource-group matrix-treasury-rg \
  --name matrix-treasury-cluster \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --enable-cluster-autoscaler \
  --min-count 3 \
  --max-count 10
```

---

## Namespace Configuration

Create dedicated namespace for Matrix Treasury:

### namespace.yaml

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: matrix-treasury
  labels:
    name: matrix-treasury
    environment: production

---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: treasury-quota
  namespace: matrix-treasury
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    persistentvolumeclaims: "10"

---
apiVersion: v1
kind: LimitRange
metadata:
  name: treasury-limits
  namespace: matrix-treasury
spec:
  limits:
  - max:
      cpu: "4"
      memory: 8Gi
    min:
      cpu: "100m"
      memory: 128Mi
    default:
      cpu: "500m"
      memory: 512Mi
    defaultRequest:
      cpu: "250m"
      memory: 256Mi
    type: Container
```

Apply configuration:

```bash
kubectl apply -f namespace.yaml
kubectl get namespace matrix-treasury
```

---

## Secrets Management

### Create Secrets

Generate secure secrets:

```bash
# Generate secrets
export DB_PASSWORD=$(openssl rand -base64 32)
export REDIS_PASSWORD=$(openssl rand -base64 32)
export JWT_SECRET=$(openssl rand -hex 32)
export SECRET_KEY=$(openssl rand -hex 32)
export ADMIN_ENCRYPTION_KEY=$(openssl rand -base64 32)
```

### secrets.yaml

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: treasury-secrets
  namespace: matrix-treasury
type: Opaque
stringData:
  # Database
  DB_PASSWORD: "your_secure_db_password"
  DATABASE_URL: "postgresql://matrix:your_secure_db_password@postgres-service:5432/matrix_treasury"

  # Redis
  REDIS_PASSWORD: "your_secure_redis_password"
  REDIS_URL: "redis://:your_secure_redis_password@redis-service:6379/0"

  # Security
  SECRET_KEY: "your_32_byte_secret_key"
  JWT_SECRET_KEY: "your_jwt_secret_key"
  ADMIN_ENCRYPTION_KEY: "your_encryption_key"

---
apiVersion: v1
kind: Secret
metadata:
  name: blockchain-secrets
  namespace: matrix-treasury
type: Opaque
stringData:
  BASE_RPC_URL: "https://mainnet.base.org"
  BASE_PRIVATE_KEY: "0x_your_private_key_here"
  POLYGON_RPC_URL: "https://polygon-rpc.com"
  ARBITRUM_RPC_URL: "https://arb1.arbitrum.io/rpc"

---
apiVersion: v1
kind: Secret
metadata:
  name: llm-api-keys
  namespace: matrix-treasury
type: Opaque
stringData:
  OPENAI_API_KEY: "sk-your_openai_key"
  ANTHROPIC_API_KEY: "sk-ant-your_anthropic_key"
```

Apply secrets:

```bash
kubectl apply -f secrets.yaml

# Verify (values are base64 encoded)
kubectl get secrets -n matrix-treasury
kubectl describe secret treasury-secrets -n matrix-treasury
```

### Using External Secrets Operator (Production)

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: matrix-treasury
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: matrix-treasury-sa

---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: treasury-external-secrets
  namespace: matrix-treasury
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: treasury-secrets
  data:
  - secretKey: DB_PASSWORD
    remoteRef:
      key: matrix-treasury/db-password
  - secretKey: JWT_SECRET_KEY
    remoteRef:
      key: matrix-treasury/jwt-secret
```

---

## Database Deployment

### PostgreSQL StatefulSet

Create `postgres.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: matrix-treasury
  labels:
    app: postgres
spec:
  ports:
  - port: 5432
    name: postgres
  clusterIP: None
  selector:
    app: postgres

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: matrix-treasury
spec:
  serviceName: postgres-service
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
          name: postgres
        env:
        - name: POSTGRES_DB
          value: matrix_treasury
        - name: POSTGRES_USER
          value: matrix
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: treasury-secrets
              key: DB_PASSWORD
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - matrix
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - matrix
          initialDelaySeconds: 5
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: gp3  # AWS EBS gp3, adjust for your provider
      resources:
        requests:
          storage: 100Gi
```

### PostgreSQL with High Availability (Production)

For production, consider using PostgreSQL operators:

```bash
# Install CloudNativePG operator
kubectl apply -f \
  https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.21/releases/cnpg-1.21.0.yaml

# Create PostgreSQL cluster
kubectl apply -f postgres-ha.yaml
```

`postgres-ha.yaml`:

```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-ha
  namespace: matrix-treasury
spec:
  instances: 3
  primaryUpdateStrategy: unsupervised

  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "2GB"
      effective_cache_size: "6GB"
      work_mem: "16MB"

  bootstrap:
    initdb:
      database: matrix_treasury
      owner: matrix
      secret:
        name: treasury-secrets

  storage:
    size: 100Gi
    storageClass: gp3

  resources:
    requests:
      memory: "2Gi"
      cpu: 1
    limits:
      memory: "4Gi"
      cpu: 2

  backup:
    barmanObjectStore:
      destinationPath: s3://matrix-treasury-backups/postgres
      s3Credentials:
        accessKeyId:
          name: aws-creds
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: aws-creds
          key: ACCESS_SECRET_KEY
      wal:
        compression: gzip
    retentionPolicy: "30d"
```

Apply:

```bash
kubectl apply -f postgres.yaml
kubectl get statefulset -n matrix-treasury
kubectl get pods -n matrix-treasury -l app=postgres
```

---

## Redis Deployment

### redis.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: matrix-treasury
  labels:
    app: redis
spec:
  ports:
  - port: 6379
    name: redis
  clusterIP: None
  selector:
    app: redis

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
  namespace: matrix-treasury
data:
  redis.conf: |
    maxmemory 512mb
    maxmemory-policy allkeys-lru
    save 900 1
    save 300 10
    save 60 10000
    appendonly yes
    appendfsync everysec

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  namespace: matrix-treasury
spec:
  serviceName: redis-service
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
          name: redis
        command:
        - redis-server
        - /usr/local/etc/redis/redis.conf
        - --requirepass
        - $(REDIS_PASSWORD)
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: treasury-secrets
              key: REDIS_PASSWORD
        volumeMounts:
        - name: redis-config
          mountPath: /usr/local/etc/redis
        - name: redis-storage
          mountPath: /data
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          exec:
            command:
            - redis-cli
            - --no-auth-warning
            - -a
            - $(REDIS_PASSWORD)
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - --no-auth-warning
            - -a
            - $(REDIS_PASSWORD)
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: redis-config
        configMap:
          name: redis-config
  volumeClaimTemplates:
  - metadata:
      name: redis-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: gp3
      resources:
        requests:
          storage: 20Gi
```

Apply:

```bash
kubectl apply -f redis.yaml
kubectl get statefulset -n matrix-treasury
kubectl get pods -n matrix-treasury -l app=redis
```

---

## API Deployment

### api-deployment.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: treasury-api-service
  namespace: matrix-treasury
  labels:
    app: treasury-api
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
    name: http
  selector:
    app: treasury-api

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: treasury-api
  namespace: matrix-treasury
  labels:
    app: treasury-api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: treasury-api
  template:
    metadata:
      labels:
        app: treasury-api
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: treasury-api-sa

      # Init container for database migrations
      initContainers:
      - name: migration
        image: registry.example.com/matrix-treasury/api:v1.0.0
        command: ["alembic", "upgrade", "head"]
        envFrom:
        - secretRef:
            name: treasury-secrets
        - secretRef:
            name: blockchain-secrets
        - secretRef:
            name: llm-api-keys

      containers:
      - name: api
        image: registry.example.com/matrix-treasury/api:v1.0.0
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DB_HOST
          value: "postgres-service"
        - name: DB_PORT
          value: "5432"
        - name: DB_NAME
          value: "matrix_treasury"
        - name: DB_USER
          value: "matrix"
        - name: REDIS_HOST
          value: "redis-service"
        - name: REDIS_PORT
          value: "6379"
        - name: API_HOST
          value: "0.0.0.0"
        - name: API_PORT
          value: "8000"
        - name: API_WORKERS
          value: "4"
        - name: LOG_LEVEL
          value: "info"
        envFrom:
        - secretRef:
            name: treasury-secrets
        - secretRef:
            name: blockchain-secrets
        - secretRef:
            name: llm-api-keys

        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi

        livenessProbe:
          httpGet:
            path: /api/v1/
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /api/v1/
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3

        volumeMounts:
        - name: logs
          mountPath: /app/logs
        - name: data
          mountPath: /app/data

      volumes:
      - name: logs
        emptyDir: {}
      - name: data
        persistentVolumeClaim:
          claimName: treasury-data-pvc

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: treasury-api-sa
  namespace: matrix-treasury
```

Apply:

```bash
kubectl apply -f api-deployment.yaml
kubectl get deployment -n matrix-treasury
kubectl get pods -n matrix-treasury -l app=treasury-api
```

---

## Frontend Deployment

### ui-deployment.yaml

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ui-config
  namespace: matrix-treasury
data:
  VITE_API_URL: "https://api.matrix-treasury.com"

---
apiVersion: v1
kind: Service
metadata:
  name: treasury-ui-service
  namespace: matrix-treasury
  labels:
    app: treasury-ui
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 80
    protocol: TCP
    name: http
  selector:
    app: treasury-ui

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: treasury-ui
  namespace: matrix-treasury
  labels:
    app: treasury-ui
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: treasury-ui
  template:
    metadata:
      labels:
        app: treasury-ui
    spec:
      containers:
      - name: ui
        image: registry.example.com/matrix-treasury/ui:v1.0.0
        imagePullPolicy: Always
        ports:
        - containerPort: 80
          name: http
        envFrom:
        - configMapRef:
            name: ui-config
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 10
```

Apply:

```bash
kubectl apply -f ui-deployment.yaml
kubectl get deployment -n matrix-treasury
kubectl get pods -n matrix-treasury -l app=treasury-ui
```

---

## Monitoring Stack

### Prometheus

```yaml
apiVersion: v1
kind: Service
metadata:
  name: prometheus-service
  namespace: matrix-treasury
spec:
  type: ClusterIP
  ports:
  - port: 9090
    targetPort: 9090
  selector:
    app: prometheus

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: matrix-treasury
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        args:
        - '--config.file=/etc/prometheus/prometheus.yml'
        - '--storage.tsdb.path=/prometheus'
        - '--storage.tsdb.retention.time=30d'
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: prometheus-config
          mountPath: /etc/prometheus
        - name: prometheus-storage
          mountPath: /prometheus
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1000m
            memory: 2Gi
      volumes:
      - name: prometheus-config
        configMap:
          name: prometheus-config
      - name: prometheus-storage
        persistentVolumeClaim:
          claimName: prometheus-pvc
```

### Grafana

```yaml
apiVersion: v1
kind: Service
metadata:
  name: grafana-service
  namespace: matrix-treasury
spec:
  type: ClusterIP
  ports:
  - port: 3000
    targetPort: 3000
  selector:
    app: grafana

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: matrix-treasury
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_USER
          value: admin
        - name: GF_SECURITY_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: treasury-secrets
              key: GRAFANA_PASSWORD
        - name: GF_USERS_ALLOW_SIGN_UP
          value: "false"
        volumeMounts:
        - name: grafana-storage
          mountPath: /var/lib/grafana
        - name: grafana-dashboards
          mountPath: /etc/grafana/provisioning/dashboards
        - name: grafana-datasources
          mountPath: /etc/grafana/provisioning/datasources
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 500m
            memory: 1Gi
      volumes:
      - name: grafana-storage
        persistentVolumeClaim:
          claimName: grafana-pvc
      - name: grafana-dashboards
        configMap:
          name: grafana-dashboards
      - name: grafana-datasources
        configMap:
          name: grafana-datasources
```

---

## Ingress Configuration

### ingress.yaml

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: matrix-treasury-ingress
  namespace: matrix-treasury
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - matrix-treasury.com
    - api.matrix-treasury.com
    secretName: treasury-tls-cert
  rules:
  - host: matrix-treasury.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: treasury-ui-service
            port:
              number: 80
  - host: api.matrix-treasury.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: treasury-api-service
            port:
              number: 8000
```

### Install Cert-Manager for TLS

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@matrix-treasury.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

Apply ingress:

```bash
kubectl apply -f ingress.yaml
kubectl get ingress -n matrix-treasury
```

---

## Autoscaling

### Horizontal Pod Autoscaler (HPA)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: treasury-api-hpa
  namespace: matrix-treasury
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: treasury-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 4
        periodSeconds: 30
      selectPolicy: Max
```

### Vertical Pod Autoscaler (VPA)

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: treasury-api-vpa
  namespace: matrix-treasury
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: treasury-api
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: api
      minAllowed:
        cpu: 250m
        memory: 256Mi
      maxAllowed:
        cpu: 4000m
        memory: 8Gi
```

Apply autoscaling:

```bash
kubectl apply -f hpa.yaml
kubectl get hpa -n matrix-treasury
kubectl describe hpa treasury-api-hpa -n matrix-treasury
```

---

## Persistent Storage

### StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs  # Change for your provider
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
allowVolumeExpansion: true
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer
```

### PersistentVolumeClaims

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: treasury-data-pvc
  namespace: matrix-treasury
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 50Gi

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: prometheus-pvc
  namespace: matrix-treasury
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 100Gi

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: grafana-pvc
  namespace: matrix-treasury
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 20Gi
```

---

## Helm Charts

### Create Helm Chart

```bash
# Create chart structure
helm create matrix-treasury

# Directory structure
matrix-treasury/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── secrets.yaml
│   ├── configmap.yaml
│   └── hpa.yaml
└── charts/
```

### Chart.yaml

```yaml
apiVersion: v2
name: matrix-treasury
description: A Helm chart for Matrix Treasury
type: application
version: 1.0.0
appVersion: "1.0.0"
keywords:
  - treasury
  - defi
  - agent
maintainers:
  - name: Matrix Treasury Team
    email: ops@matrix-treasury.com
```

### values.yaml

```yaml
replicaCount: 3

image:
  repository: registry.example.com/matrix-treasury/api
  tag: v1.0.0
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8000

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: api.matrix-treasury.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: treasury-tls
      hosts:
        - api.matrix-treasury.com

resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 2000m
    memory: 2Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

postgresql:
  enabled: true
  auth:
    username: matrix
    password: ""
    database: matrix_treasury
  primary:
    persistence:
      size: 100Gi

redis:
  enabled: true
  auth:
    password: ""
  master:
    persistence:
      size: 20Gi
```

### Install Chart

```bash
# Lint chart
helm lint ./matrix-treasury

# Dry run
helm install matrix-treasury ./matrix-treasury \
  --namespace matrix-treasury \
  --dry-run --debug

# Install
helm install matrix-treasury ./matrix-treasury \
  --namespace matrix-treasury \
  --create-namespace \
  --set postgresql.auth.password=secure_password \
  --set redis.auth.password=secure_password

# Upgrade
helm upgrade matrix-treasury ./matrix-treasury \
  --namespace matrix-treasury \
  --reuse-values

# Rollback
helm rollback matrix-treasury 1 -n matrix-treasury
```

---

## CI/CD Integration

### GitHub Actions

`.github/workflows/deploy.yml`:

```yaml
name: Deploy to Kubernetes

on:
  push:
    branches: [main]
    tags:
      - 'v*'

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}

    - name: Build and push
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - name: Set up kubectl
      uses: azure/setup-kubectl@v3

    - name: Configure kubectl
      run: |
        echo "${{ secrets.KUBE_CONFIG }}" | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig

    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/treasury-api \
          api=${{ steps.meta.outputs.tags }} \
          -n matrix-treasury

        kubectl rollout status deployment/treasury-api \
          -n matrix-treasury \
          --timeout=5m
```

---

## Troubleshooting

### Check Pod Status

```bash
# List all pods
kubectl get pods -n matrix-treasury

# Describe pod
kubectl describe pod <pod-name> -n matrix-treasury

# View logs
kubectl logs <pod-name> -n matrix-treasury

# Follow logs
kubectl logs -f <pod-name> -n matrix-treasury

# Previous container logs
kubectl logs <pod-name> --previous -n matrix-treasury
```

### Debug Running Container

```bash
# Execute shell
kubectl exec -it <pod-name> -n matrix-treasury -- /bin/bash

# Run command
kubectl exec <pod-name> -n matrix-treasury -- env

# Port forward
kubectl port-forward <pod-name> 8000:8000 -n matrix-treasury
```

### Network Issues

```bash
# Test service connectivity
kubectl run -it --rm debug --image=alpine --restart=Never -n matrix-treasury -- sh
> apk add curl
> curl http://treasury-api-service:8000/api/v1/

# DNS debugging
kubectl run -it --rm debug --image=tutum/dnsutils --restart=Never -n matrix-treasury -- sh
> nslookup treasury-api-service
> dig treasury-api-service.matrix-treasury.svc.cluster.local
```

### Resource Issues

```bash
# Check resource usage
kubectl top pods -n matrix-treasury
kubectl top nodes

# Check events
kubectl get events -n matrix-treasury --sort-by='.lastTimestamp'

# Check resource quotas
kubectl describe resourcequota -n matrix-treasury
```

### Rollback Deployment

```bash
# View rollout history
kubectl rollout history deployment/treasury-api -n matrix-treasury

# Rollback to previous version
kubectl rollout undo deployment/treasury-api -n matrix-treasury

# Rollback to specific revision
kubectl rollout undo deployment/treasury-api --to-revision=2 -n matrix-treasury
```

---

## Production Best Practices

1. **Use separate namespaces** for different environments
2. **Implement RBAC** for service accounts
3. **Enable Pod Security Standards**
4. **Use NetworkPolicies** to restrict traffic
5. **Configure resource quotas** and limits
6. **Enable audit logging**
7. **Implement backup strategies** for persistent data
8. **Monitor cluster health** with Prometheus/Grafana
9. **Use Helm charts** for consistent deployments
10. **Implement GitOps** with ArgoCD or Flux

---

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Matrix Treasury Docker Guide](/docs/deployment/docker.md)
- [Monitoring Guide](/docs/deployment/monitoring.md)
