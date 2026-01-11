# Docker Deployment Guide

Complete Docker deployment guide for Matrix Treasury production environments.

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Multi-Stage Dockerfile](#multi-stage-dockerfile)
- [Docker Compose Setup](#docker-compose-setup)
- [Environment Configuration](#environment-configuration)
- [Building Images](#building-images)
- [Running Services](#running-services)
- [Networking](#networking)
- [Volume Management](#volume-management)
- [Health Checks](#health-checks)
- [Scaling Services](#scaling-services)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

Matrix Treasury uses a microservices architecture deployed via Docker containers:

- **Backend API**: FastAPI application on port 8000
- **Frontend**: React + Vite application on port 5173
- **PostgreSQL**: Database on port 5432
- **Redis**: Cache layer on port 6379
- **Prometheus**: Metrics collection on port 9090
- **Grafana**: Dashboards on port 3000

---

## Prerequisites

### System Requirements

**Minimum** (Development):
- Docker 24.0+
- Docker Compose 2.20+
- 4GB RAM
- 20GB storage

**Recommended** (Production):
- Docker 24.0+
- Docker Compose 2.20+
- 8GB RAM
- 100GB SSD storage
- Ubuntu 22.04 LTS or similar

### Install Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

---

## Multi-Stage Dockerfile

The project uses optimized multi-stage builds for production efficiency.

### Backend Dockerfile

Located at `/Dockerfile`:

```dockerfile
# Multi-stage build for production optimization
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements-upgrade.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt && \
    pip install --no-cache-dir --user -r requirements-upgrade.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src ./src
COPY scripts ./scripts
COPY alembic.ini ./

# Create non-root user
RUN useradd -m -u 1000 treasury && \
    mkdir -p /app/logs /app/data && \
    chown -R treasury:treasury /app

USER treasury

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/ || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Frontend Dockerfile

Create `ui/Dockerfile`:

```dockerfile
# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy source
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Frontend Nginx Configuration

Create `ui/nginx.conf`:

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Cache static assets
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api {
        proxy_pass http://treasury-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://treasury-api:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## Docker Compose Setup

### Production docker-compose.yml

The existing `docker-compose.yml` provides a complete production setup:

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: matrix-treasury-db
    environment:
      POSTGRES_USER: matrix
      POSTGRES_PASSWORD: ${DB_PASSWORD:-matrix_password_change_me}
      POSTGRES_DB: matrix_treasury
      POSTGRES_INITDB_ARGS: "-E UTF8"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U matrix"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - matrix-network
    restart: unless-stopped

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: matrix-treasury-redis
    command: redis-server --requirepass ${REDIS_PASSWORD:-redis_password_change_me} --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "--no-auth-warning", "-a", "${REDIS_PASSWORD:-redis_password_change_me}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - matrix-network
    restart: unless-stopped

  # Treasury API
  treasury-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: matrix-treasury-api
    environment:
      - ENVIRONMENT=production
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=matrix_treasury
      - DB_USER=matrix
      - DB_PASSWORD=${DB_PASSWORD:-matrix_password_change_me}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD:-redis_password_change_me}
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - API_WORKERS=4
      - LOG_LEVEL=${LOG_LEVEL:-info}
      - SECRET_KEY=${SECRET_KEY:-change_this_secret_key_in_production}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-change_this_jwt_secret}
      - ADMIN_ENCRYPTION_KEY=${ADMIN_ENCRYPTION_KEY}
      - BASE_RPC_URL=${BASE_RPC_URL}
      - BASE_PRIVATE_KEY=${BASE_PRIVATE_KEY}
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - matrix-network
    restart: unless-stopped

  # Frontend UI
  treasury-ui:
    build:
      context: ./ui
      dockerfile: Dockerfile
    container_name: matrix-treasury-ui
    environment:
      - VITE_API_URL=http://localhost:8000
    ports:
      - "5173:80"
    depends_on:
      - treasury-api
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:80/"]
      interval: 30s
      timeout: 3s
      retries: 3
    networks:
      - matrix-network
    restart: unless-stopped

  # Prometheus
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

  # Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: matrix-treasury-grafana
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_USER:-admin}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin_change_me}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SERVER_ROOT_URL=http://localhost:3000
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource
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

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local

networks:
  matrix-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

### Development docker-compose.dev.yml

For local development with hot-reload:

```yaml
version: '3.8'

services:
  postgres:
    extends:
      file: docker-compose.yml
      service: postgres

  redis:
    extends:
      file: docker-compose.yml
      service: redis

  treasury-api:
    build:
      context: .
      dockerfile: Dockerfile
      target: builder
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - LOG_LEVEL=debug
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis

  treasury-ui:
    build:
      context: ./ui
      dockerfile: Dockerfile.dev
    command: npm run dev -- --host
    volumes:
      - ./ui:/app
      - /app/node_modules
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
```

---

## Environment Configuration

### Create .env File

```bash
# Copy example environment file
cp .env.example .env

# Generate secure secrets
export SECRET_KEY=$(openssl rand -hex 32)
export JWT_SECRET_KEY=$(openssl rand -hex 32)
export DB_PASSWORD=$(openssl rand -hex 16)
export REDIS_PASSWORD=$(openssl rand -hex 16)
export GRAFANA_PASSWORD=$(openssl rand -hex 12)
```

### .env Template

```bash
# Database
DB_PASSWORD=your_secure_db_password
DATABASE_URL=postgresql://matrix:${DB_PASSWORD}@postgres:5432/matrix_treasury

# Redis
REDIS_PASSWORD=your_secure_redis_password
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# Security
SECRET_KEY=your_32_byte_secret_key
JWT_SECRET_KEY=your_jwt_secret_key
ADMIN_ENCRYPTION_KEY=your_encryption_key

# Blockchain
BASE_RPC_URL=https://mainnet.base.org
BASE_PRIVATE_KEY=0x_your_private_key

# Monitoring
GRAFANA_USER=admin
GRAFANA_PASSWORD=your_grafana_password

# Application
ENVIRONMENT=production
LOG_LEVEL=info
DEBUG=false
```

---

## Building Images

### Build All Services

```bash
# Build all images
docker compose build

# Build with no cache (clean build)
docker compose build --no-cache

# Build specific service
docker compose build treasury-api

# Build with progress output
docker compose build --progress=plain
```

### Tag Images for Registry

```bash
# Tag backend image
docker tag matrix-treasury-treasury-api:latest \
  registry.example.com/matrix-treasury/api:v1.0.0

# Tag frontend image
docker tag matrix-treasury-treasury-ui:latest \
  registry.example.com/matrix-treasury/ui:v1.0.0

# Push to registry
docker push registry.example.com/matrix-treasury/api:v1.0.0
docker push registry.example.com/matrix-treasury/ui:v1.0.0
```

---

## Running Services

### Start All Services

```bash
# Start in detached mode
docker compose up -d

# Start and view logs
docker compose up

# Start specific services
docker compose up -d postgres redis treasury-api

# Start with custom compose file
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### View Logs

```bash
# View all logs
docker compose logs

# Follow logs
docker compose logs -f

# View specific service logs
docker compose logs -f treasury-api

# View last 100 lines
docker compose logs --tail=100 treasury-api

# View logs with timestamps
docker compose logs -t
```

### Stop Services

```bash
# Stop all services
docker compose stop

# Stop specific service
docker compose stop treasury-api

# Stop and remove containers
docker compose down

# Stop and remove with volumes
docker compose down -v
```

---

## Networking

### Network Configuration

Docker Compose creates a bridge network for service communication:

```bash
# List networks
docker network ls

# Inspect network
docker network inspect matrix-treasury_matrix-network

# Connect additional container
docker network connect matrix-treasury_matrix-network my-container
```

### Service Communication

Services communicate using service names:

- API connects to database: `postgresql://matrix:password@postgres:5432/matrix_treasury`
- API connects to Redis: `redis://:password@redis:6379`
- Frontend connects to API: `http://treasury-api:8000`

### External Access

Ports exposed to host:

- **8000**: API endpoint
- **5173**: Frontend UI
- **5432**: PostgreSQL (development only)
- **6379**: Redis (development only)
- **9090**: Prometheus
- **3000**: Grafana

---

## Volume Management

### Persistent Data

Volumes store persistent data:

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect matrix-treasury_postgres_data

# Backup volume
docker run --rm \
  -v matrix-treasury_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres-backup-$(date +%Y%m%d).tar.gz /data

# Restore volume
docker run --rm \
  -v matrix-treasury_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/postgres-backup-20260111.tar.gz -C /
```

### Volume Cleanup

```bash
# Remove specific volume
docker volume rm matrix-treasury_postgres_data

# Remove all unused volumes
docker volume prune

# Remove all project volumes
docker compose down -v
```

---

## Health Checks

### Check Service Health

```bash
# View container health status
docker compose ps

# Inspect health check
docker inspect --format='{{json .State.Health}}' matrix-treasury-api | jq

# View health check logs
docker inspect matrix-treasury-api | jq '.[0].State.Health'
```

### Manual Health Checks

```bash
# API health
curl http://localhost:8000/api/v1/

# Database health
docker compose exec postgres pg_isready -U matrix

# Redis health
docker compose exec redis redis-cli -a your_password ping

# Prometheus health
curl http://localhost:9090/-/healthy

# Grafana health
curl http://localhost:3000/api/health
```

---

## Scaling Services

### Horizontal Scaling

```bash
# Scale API to 4 instances
docker compose up -d --scale treasury-api=4

# Scale with load balancer
docker compose -f docker-compose.yml -f docker-compose.scale.yml up -d
```

### Load Balancer Configuration

Create `docker-compose.scale.yml`:

```yaml
version: '3.8'

services:
  nginx-lb:
    image: nginx:alpine
    container_name: matrix-treasury-lb
    volumes:
      - ./nginx-lb.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
    depends_on:
      - treasury-api
    networks:
      - matrix-network
```

Create `nginx-lb.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream api_backend {
        least_conn;
        server treasury-api-1:8000;
        server treasury-api-2:8000;
        server treasury-api-3:8000;
        server treasury-api-4:8000;
    }

    server {
        listen 80;

        location / {
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

---

## Security Best Practices

### Container Security

```bash
# Run as non-root user (already configured in Dockerfile)
USER treasury

# Use read-only root filesystem
docker compose up -d --read-only treasury-api

# Drop capabilities
docker compose run --cap-drop=ALL --cap-add=NET_BIND_SERVICE treasury-api

# Limit resources
docker compose run --memory=512m --cpus=0.5 treasury-api
```

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  treasury-api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Secrets Management

Use Docker secrets for sensitive data:

```bash
# Create secret
echo "your_secret_key" | docker secret create jwt_secret -

# Use in compose file
docker compose -f docker-compose.yml -f docker-compose.secrets.yml up -d
```

### Network Security

```yaml
services:
  postgres:
    networks:
      - backend_only
    # Don't expose port in production
    # ports:
    #   - "5432:5432"

networks:
  backend_only:
    driver: bridge
    internal: true  # No external access
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs treasury-api

# Inspect container
docker inspect matrix-treasury-api

# Check exit code
docker compose ps -a

# Start in interactive mode
docker compose run --rm treasury-api sh
```

### Database Connection Issues

```bash
# Check database is running
docker compose ps postgres

# Test database connection
docker compose exec postgres psql -U matrix -d matrix_treasury

# Check network connectivity
docker compose exec treasury-api ping postgres

# View database logs
docker compose logs postgres
```

### High Memory Usage

```bash
# Check container stats
docker stats

# Check specific container
docker stats matrix-treasury-api

# Limit memory
docker compose up -d --scale treasury-api=1 --memory=1g
```

### Port Conflicts

```bash
# Check port usage
sudo lsof -i :8000

# Change port mapping in docker-compose.yml
ports:
  - "8001:8000"
```

### Reset Everything

```bash
# Stop and remove all containers, volumes, networks
docker compose down -v

# Remove all images
docker compose down --rmi all

# Clean build and restart
docker compose build --no-cache
docker compose up -d
```

### Debug Mode

```bash
# Run with debug logging
docker compose run --rm \
  -e LOG_LEVEL=debug \
  -e DEBUG=true \
  treasury-api

# Interactive shell
docker compose exec treasury-api bash

# Check environment variables
docker compose exec treasury-api env
```

---

## Useful Commands

### Container Management

```bash
# List running containers
docker compose ps

# Restart service
docker compose restart treasury-api

# Execute command in container
docker compose exec treasury-api python -c "print('Hello')"

# Copy files
docker cp matrix-treasury-api:/app/logs/app.log ./local-logs/
```

### Cleanup

```bash
# Remove stopped containers
docker compose rm

# Prune unused images
docker image prune

# System-wide cleanup
docker system prune -a --volumes
```

### Performance Monitoring

```bash
# Real-time stats
docker stats

# Export metrics
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Container processes
docker compose top treasury-api
```

---

## Production Deployment Checklist

- [ ] Environment variables configured in `.env`
- [ ] Secrets generated and secured
- [ ] Database password changed from default
- [ ] Redis password set
- [ ] JWT secret keys configured
- [ ] Resource limits defined
- [ ] Health checks configured
- [ ] Volumes backed up
- [ ] Monitoring enabled
- [ ] Logs aggregated
- [ ] SSL/TLS configured (if using nginx)
- [ ] Firewall rules applied
- [ ] Backup strategy implemented
- [ ] Recovery procedures tested

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Matrix Treasury API Reference](/docs/API_REFERENCE.md)
- [Monitoring Guide](/docs/deployment/monitoring.md)
