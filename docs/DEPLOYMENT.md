# Deployment Guide

Production deployment guide for Matrix Treasury enterprise platform.

---

## Prerequisites

### System Requirements

**Minimum** (Development/Testing):
- 2 CPU cores
- 4GB RAM
- 20GB storage
- Ubuntu 20.04+ or similar Linux

**Recommended** (Production < 100 agents):
- 4 CPU cores
- 8GB RAM
- 100GB SSD storage
- Ubuntu 22.04 LTS

**Enterprise** (Production > 100 agents):
- 8+ CPU cores
- 16GB+ RAM
- 500GB SSD storage
- Kubernetes cluster
- Load balancer
- PostgreSQL cluster

### Software Dependencies

```bash
# System packages
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip
sudo apt install -y nodejs npm postgresql-14 redis nginx

# Python 3.11
python3.11 --version

# Node.js 18+
node --version

# PostgreSQL
psql --version
```

---

## Local Development

### Quick Start

```bash
# Clone repository
git clone https://github.com/agent-matrix/matrix-treasury.git
cd matrix-treasury

# Install dependencies
make install

# Configure environment
cp .env.example .env
# Edit .env with your keys

# Run tests
make test

# Start backend
make run

# Start frontend (new terminal)
make serve
```

### Environment Configuration

Create `.env` file:

```bash
# Blockchain Networks
BASE_RPC_URL=https://mainnet.base.org
POLYGON_RPC_URL=https://polygon-rpc.com
ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc
OPTIMISM_RPC_URL=https://mainnet.optimism.io

# Private Keys (use separate keys per network)
BASE_PRIVATE_KEY=0x...
POLYGON_PRIVATE_KEY=0x...
ARBITRUM_PRIVATE_KEY=0x...
OPTIMISM_PRIVATE_KEY=0x...

# Admin & Security
ADMIN_ENCRYPTION_KEY=your_32_byte_encryption_key
JWT_SECRET_KEY=your_jwt_secret

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/treasury

# LLM Providers (choose one or more)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
WATSONX_API_KEY=...
OLLAMA_HOST=http://localhost:11434

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

---

## Production Deployment

### Option 1: Docker Compose

**1. Create docker-compose.yml**:

```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: treasury
      POSTGRES_USER: treasury
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: always

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: always

  api:
    build: .
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://treasury:${DB_PASSWORD}@db:5432/treasury
      - REDIS_URL=redis://redis:6379
    env_file:
      - .env
    depends_on:
      - db
      - redis
    restart: always

  frontend:
    build:
      context: ./ui
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
      - frontend
    restart: always

volumes:
  postgres_data:
```

**2. Create Dockerfile**:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements-upgrade.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-upgrade.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 treasury && chown -R treasury:treasury /app
USER treasury

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**3. Deploy**:

```bash
# Build and start
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api

# Scale API servers
docker-compose up -d --scale api=3
```

---

### Option 2: Kubernetes

**1. Create namespace**:

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: matrix-treasury
```

**2. Create secrets**:

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: treasury-secrets
  namespace: matrix-treasury
type: Opaque
stringData:
  DATABASE_URL: postgresql://user:pass@postgres:5432/treasury
  BASE_PRIVATE_KEY: "0x..."
  ADMIN_ENCRYPTION_KEY: "..."
  OPENAI_API_KEY: "sk-..."
```

**3. Deploy PostgreSQL**:

```yaml
# postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: matrix-treasury
spec:
  serviceName: postgres
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
        image: postgres:14
        env:
        - name: POSTGRES_DB
          value: treasury
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: treasury-secrets
              key: DB_PASSWORD
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
```

**4. Deploy API**:

```yaml
# api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: treasury-api
  namespace: matrix-treasury
spec:
  replicas: 3
  selector:
    matchLabels:
      app: treasury-api
  template:
    metadata:
      labels:
        app: treasury-api
    spec:
      containers:
      - name: api
        image: matrix-treasury:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: treasury-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: treasury-api
  namespace: matrix-treasury
spec:
  selector:
    app: treasury-api
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

**5. Deploy**:

```bash
# Apply configurations
kubectl apply -f namespace.yaml
kubectl apply -f secrets.yaml
kubectl apply -f postgres.yaml
kubectl apply -f api-deployment.yaml

# Check status
kubectl get pods -n matrix-treasury
kubectl get svc -n matrix-treasury

# View logs
kubectl logs -f deployment/treasury-api -n matrix-treasury

# Scale
kubectl scale deployment/treasury-api --replicas=5 -n matrix-treasury
```

---

### Option 3: Traditional Server

**1. Setup server**:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv postgresql-14 nginx redis

# Create user
sudo useradd -m -s /bin/bash treasury
sudo su - treasury
```

**2. Deploy application**:

```bash
# Clone and setup
git clone https://github.com/agent-matrix/matrix-treasury.git
cd matrix-treasury

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-upgrade.txt

# Configure
cp .env.example .env
nano .env  # Edit configuration
```

**3. Setup database**:

```bash
# Create database
sudo -u postgres psql
CREATE DATABASE treasury;
CREATE USER treasury WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE treasury TO treasury;
\q

# Run migrations
alembic upgrade head
```

**4. Setup systemd service**:

```ini
# /etc/systemd/system/matrix-treasury.service
[Unit]
Description=Matrix Treasury API
After=network.target postgresql.service

[Service]
Type=simple
User=treasury
WorkingDirectory=/home/treasury/matrix-treasury
Environment="PATH=/home/treasury/matrix-treasury/venv/bin"
ExecStart=/home/treasury/matrix-treasury/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**5. Configure nginx**:

```nginx
# /etc/nginx/sites-available/matrix-treasury
server {
    listen 80;
    server_name treasury.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name treasury.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/treasury.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/treasury.yourdomain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**6. Start services**:

```bash
# Enable and start
sudo systemctl enable matrix-treasury
sudo systemctl start matrix-treasury

# Enable nginx
sudo ln -s /etc/nginx/sites-available/matrix-treasury /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Check status
sudo systemctl status matrix-treasury
```

---

## SSL/TLS Setup

### Using Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d treasury.yourdomain.com

# Auto-renewal (runs twice daily)
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## Database Management

### Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Backups

```bash
# Automated backup script
#!/bin/bash
# /usr/local/bin/backup-treasury.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/treasury"
DB_NAME="treasury"

# Database backup
pg_dump $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Encrypt backup
gpg --encrypt --recipient admin@company.com $BACKUP_DIR/db_$DATE.sql.gz

# Upload to S3
aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz.gpg s3://backups/treasury/

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete
```

**Cron schedule**:
```bash
# Daily at 2 AM
0 2 * * * /usr/local/bin/backup-treasury.sh
```

---

## Monitoring

### Prometheus + Grafana

**1. Install Prometheus**:

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'matrix-treasury'
    static_configs:
      - targets: ['localhost:8000']
```

**2. Add metrics to API**:

```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
transaction_counter = Counter('transactions_total', 'Total transactions')
response_time = Histogram('response_time_seconds', 'Response time')
active_agents = Gauge('active_agents', 'Number of active agents')

# In endpoints
@app.get("/api/v1/transaction")
async def transaction():
    with response_time.time():
        transaction_counter.inc()
        # ... handle transaction
```

**3. Grafana dashboards**:
- Treasury balance over time
- Transaction volume
- Active agents
- API response times
- Error rates

### Logging

**1. Configure logging**:

```python
# logging_config.py
import logging
from logging.handlers import RotatingFileHandler

# File handler
file_handler = RotatingFileHandler(
    'logs/treasury.log',
    maxBytes=10_000_000,  # 10MB
    backupCount=10
)

# Format
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)

# Configure logger
logger = logging.getLogger()
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)
```

**2. Log aggregation (ELK Stack)**:

```yaml
# filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/treasury/*.log
    fields:
      service: matrix-treasury

output.elasticsearch:
  hosts: ["localhost:9200"]
```

---

## Performance Tuning

### Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_transactions_agent_id ON transactions(agent_id);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);
CREATE INDEX idx_loans_agent_id ON loans(agent_id);
CREATE INDEX idx_loans_status ON loans(status);

-- Analyze tables
ANALYZE transactions;
ANALYZE agents;
ANALYZE loans;

-- Enable connection pooling
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '6GB';
```

### API Optimization

```python
# Use connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)

# Add caching
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="treasury:")

# Cache expensive queries
@app.get("/analytics/dashboard")
@cache(expire=60)  # Cache for 60 seconds
async def get_analytics():
    ...
```

---

## Health Checks

**Endpoint**:

```python
@app.get("/health")
async def health_check():
    checks = {
        "api": "ok",
        "database": check_database(),
        "redis": check_redis(),
        "blockchain": check_blockchain_connection()
    }

    status = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"

    return {
        "status": status,
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }
```

---

## Troubleshooting

### Common Issues

**Database connection errors**:
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Increase connections
sudo nano /etc/postgresql/14/main/postgresql.conf
# max_connections = 200
sudo systemctl restart postgresql
```

**High memory usage**:
```bash
# Check memory
free -h

# Find memory hogs
ps aux --sort=-%mem | head

# Restart services
sudo systemctl restart matrix-treasury
```

**Slow API responses**:
```bash
# Check database queries
sudo -u postgres psql treasury
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '1 second';

# Check API logs
tail -f /var/log/treasury/api.log | grep -i "slow"
```

---

## Rollback Procedures

**If deployment fails**:

```bash
# 1. Stop new version
docker-compose down
# or
sudo systemctl stop matrix-treasury

# 2. Restore database
gunzip < backup_latest.sql.gz | psql treasury

# 3. Checkout previous version
git checkout previous-tag

# 4. Rebuild and start
docker-compose up -d
# or
sudo systemctl start matrix-treasury

# 5. Verify
curl http://localhost:8000/health
```

---

## Post-Deployment Checklist

- [ ] All services running
- [ ] Health check passes
- [ ] Database migrations applied
- [ ] SSL certificate valid
- [ ] Monitoring active
- [ ] Backups configured
- [ ] Logs aggregating
- [ ] Alerts configured
- [ ] Documentation updated
- [ ] Team notified

---

## Support

For deployment issues:
- Email: ops@matrix-treasury.com
- Slack: #deployments
- Docs: https://docs.matrix-treasury.com
