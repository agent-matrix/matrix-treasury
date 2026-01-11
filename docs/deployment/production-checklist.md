# Production Deployment Checklist

Comprehensive pre-deployment and post-deployment checklist for Matrix Treasury production environments.

---

## Table of Contents

- [Pre-Deployment](#pre-deployment)
  - [Security](#security)
  - [Infrastructure](#infrastructure)
  - [Application Configuration](#application-configuration)
  - [Database](#database)
  - [Monitoring & Logging](#monitoring--logging)
- [Deployment](#deployment)
- [Post-Deployment](#post-deployment)
- [Ongoing Operations](#ongoing-operations)
- [Emergency Procedures](#emergency-procedures)

---

## Pre-Deployment

### Security

#### Secrets & Credentials

- [ ] **Generate strong secrets** for all services
  ```bash
  # Database password (min 32 characters)
  openssl rand -base64 32

  # JWT secret key (min 32 bytes)
  openssl rand -hex 32

  # Encryption key (32 bytes for AES-256)
  openssl rand -base64 32
  ```

- [ ] **Store secrets securely**
  - [ ] Use environment variables, never hardcode
  - [ ] Use secret management system (AWS Secrets Manager, HashiCorp Vault, etc.)
  - [ ] Rotate secrets regularly (every 90 days minimum)
  - [ ] Document secret rotation procedure

- [ ] **Configure blockchain private keys**
  - [ ] Use separate keys per network (Base, Polygon, Arbitrum)
  - [ ] Store in hardware wallet or KMS for production
  - [ ] Never commit private keys to version control
  - [ ] Implement key rotation strategy
  - [ ] Configure wallet monitoring and alerts

- [ ] **Set up JWT authentication**
  - [ ] Generate secure JWT secret (min 256 bits)
  - [ ] Configure token expiration (recommended: 24 hours)
  - [ ] Implement refresh token mechanism
  - [ ] Configure CORS properly
  - [ ] Test authentication flow end-to-end

#### Access Control

- [ ] **Database access**
  - [ ] Create separate database users for services
  - [ ] Grant minimum required privileges
  - [ ] Disable default/admin accounts
  - [ ] Enable SSL/TLS connections
  - [ ] Configure IP whitelisting
  - [ ] Set up connection pooling limits

- [ ] **API access**
  - [ ] Implement rate limiting (100 req/min standard, 30 req/min analytics)
  - [ ] Configure CORS allowlist
  - [ ] Enable request authentication
  - [ ] Set up API key rotation
  - [ ] Implement request signing for sensitive operations

- [ ] **Admin access**
  - [ ] Change default admin credentials
  - [ ] Enable multi-factor authentication
  - [ ] Configure role-based access control (RBAC)
  - [ ] Implement session management
  - [ ] Set up audit logging for admin actions

#### SSL/TLS

- [ ] **Certificate setup**
  - [ ] Obtain SSL certificates (Let's Encrypt or commercial CA)
  - [ ] Configure automatic renewal
  - [ ] Use TLS 1.2 or higher
  - [ ] Implement HSTS headers
  - [ ] Configure certificate pinning for mobile apps

- [ ] **Verify SSL configuration**
  ```bash
  # Test SSL configuration
  openssl s_client -connect api.matrix-treasury.com:443

  # Check certificate expiration
  echo | openssl s_client -servername api.matrix-treasury.com \
    -connect api.matrix-treasury.com:443 2>/dev/null | \
    openssl x509 -noout -dates
  ```

#### Network Security

- [ ] **Firewall configuration**
  - [ ] Close all unnecessary ports
  - [ ] Allow only required inbound traffic
  - [ ] Configure security groups (cloud) or iptables (on-prem)
  - [ ] Implement DDoS protection
  - [ ] Set up VPN for admin access

- [ ] **Container security**
  - [ ] Run containers as non-root user
  - [ ] Use minimal base images
  - [ ] Scan images for vulnerabilities
  - [ ] Implement network policies (Kubernetes)
  - [ ] Configure resource limits

#### Data Protection

- [ ] **Encryption**
  - [ ] Enable encryption at rest for databases
  - [ ] Enable encryption in transit (TLS)
  - [ ] Encrypt sensitive data in application (PII, credentials)
  - [ ] Implement field-level encryption for critical data
  - [ ] Configure encryption key rotation

- [ ] **Data retention**
  - [ ] Define data retention policies
  - [ ] Implement automated data purging
  - [ ] Configure log rotation
  - [ ] Set up backup retention schedules
  - [ ] Document compliance requirements (GDPR, etc.)

---

### Infrastructure

#### Server Requirements

- [ ] **Production servers meet minimum specs**
  - [ ] 4+ CPU cores
  - [ ] 8GB+ RAM
  - [ ] 100GB+ SSD storage
  - [ ] Ubuntu 22.04 LTS or equivalent
  - [ ] Docker 24.0+ installed

- [ ] **High availability setup** (if required)
  - [ ] Multiple availability zones
  - [ ] Load balancer configured
  - [ ] Database replication enabled
  - [ ] Redis clustering configured
  - [ ] Failover procedures tested

#### DNS Configuration

- [ ] **Domain setup**
  - [ ] Domain registered and renewed
  - [ ] DNS records configured
    - [ ] A record for main domain
    - [ ] A record for api subdomain
    - [ ] CNAME for www subdomain
    - [ ] TXT records for domain verification
  - [ ] TTL set appropriately (300s for production)
  - [ ] Configure DNS monitoring

Example DNS records:
```
matrix-treasury.com.        300 IN A     203.0.113.10
api.matrix-treasury.com.    300 IN A     203.0.113.11
www.matrix-treasury.com.    300 IN CNAME matrix-treasury.com.
```

#### Load Balancer

- [ ] **Load balancer configured**
  - [ ] Health checks enabled
  - [ ] SSL termination configured
  - [ ] Session affinity set (if needed)
  - [ ] Timeout values tuned
  - [ ] DDoS protection enabled

- [ ] **Backend pools configured**
  - [ ] API servers registered
  - [ ] Health check endpoints verified
  - [ ] Drain timeout set appropriately
  - [ ] Auto-scaling rules defined

#### Container Orchestration

- [ ] **Docker Compose** (for smaller deployments)
  - [ ] docker-compose.yml validated
  - [ ] Volumes configured
  - [ ] Networks defined
  - [ ] Health checks enabled
  - [ ] Restart policies set

- [ ] **Kubernetes** (for larger deployments)
  - [ ] Cluster provisioned and configured
  - [ ] Namespaces created
  - [ ] Resource quotas set
  - [ ] Network policies configured
  - [ ] Ingress controller installed
  - [ ] Cert-manager configured
  - [ ] Storage classes defined

---

### Application Configuration

#### Environment Variables

- [ ] **Backend configuration**
  ```bash
  # Required variables
  ENVIRONMENT=production
  DEBUG=false
  LOG_LEVEL=info

  # Database
  DB_HOST=postgres
  DB_PORT=5432
  DB_NAME=matrix_treasury
  DB_USER=matrix
  DB_PASSWORD=***SECURE***

  # Redis
  REDIS_HOST=redis
  REDIS_PORT=6379
  REDIS_PASSWORD=***SECURE***

  # Security
  SECRET_KEY=***SECURE***
  JWT_SECRET_KEY=***SECURE***
  ADMIN_ENCRYPTION_KEY=***SECURE***

  # Blockchain
  BASE_RPC_URL=https://mainnet.base.org
  BASE_PRIVATE_KEY=***SECURE***

  # API
  API_HOST=0.0.0.0
  API_PORT=8000
  API_WORKERS=4
  ```

- [ ] **Frontend configuration**
  ```bash
  VITE_API_URL=https://api.matrix-treasury.com
  NODE_ENV=production
  ```

- [ ] **Verify no debug modes enabled**
  ```bash
  # Check for debug flags
  grep -r "DEBUG=true" .env
  grep -r "development" .env
  ```

#### API Configuration

- [ ] **Rate limiting configured**
  - [ ] Standard endpoints: 100 req/min
  - [ ] Analytics endpoints: 30 req/min
  - [ ] Admin endpoints: 10 req/min
  - [ ] Authentication endpoints: 5 req/min

- [ ] **CORS properly configured**
  ```python
  ALLOWED_ORIGINS = [
      "https://matrix-treasury.com",
      "https://www.matrix-treasury.com"
  ]
  ```

- [ ] **Request size limits**
  - [ ] Max body size: 10MB
  - [ ] Max upload size: 5MB
  - [ ] Timeout: 30 seconds

#### Multi-Currency Support

- [ ] **RPC endpoints configured**
  - [ ] Base RPC URL verified
  - [ ] Polygon RPC URL verified
  - [ ] Arbitrum RPC URL verified
  - [ ] Optimism RPC URL verified
  - [ ] Backup RPC URLs configured

- [ ] **Wallet addresses verified**
  - [ ] USDC wallet funded and accessible
  - [ ] EUR wallet configured
  - [ ] BTC wallet configured
  - [ ] Multi-sig wallets set up (if required)

- [ ] **Exchange rate feeds**
  - [ ] Price oracle configured
  - [ ] Fallback price sources enabled
  - [ ] Update frequency set (recommended: 1 minute)

---

### Database

#### PostgreSQL Setup

- [ ] **Database initialized**
  ```bash
  # Create database
  CREATE DATABASE matrix_treasury;
  CREATE USER matrix WITH PASSWORD 'secure_password';
  GRANT ALL PRIVILEGES ON DATABASE matrix_treasury TO matrix;
  ```

- [ ] **Run migrations**
  ```bash
  # Apply all migrations
  alembic upgrade head

  # Verify migration status
  alembic current
  alembic history
  ```

- [ ] **Performance tuning**
  ```sql
  -- Recommended PostgreSQL settings for production
  ALTER SYSTEM SET max_connections = 200;
  ALTER SYSTEM SET shared_buffers = '2GB';
  ALTER SYSTEM SET effective_cache_size = '6GB';
  ALTER SYSTEM SET maintenance_work_mem = '512MB';
  ALTER SYSTEM SET checkpoint_completion_target = 0.9;
  ALTER SYSTEM SET wal_buffers = '16MB';
  ALTER SYSTEM SET default_statistics_target = 100;
  ALTER SYSTEM SET random_page_cost = 1.1;
  ALTER SYSTEM SET effective_io_concurrency = 200;
  ALTER SYSTEM SET work_mem = '16MB';
  ALTER SYSTEM SET min_wal_size = '1GB';
  ALTER SYSTEM SET max_wal_size = '4GB';

  -- Reload configuration
  SELECT pg_reload_conf();
  ```

- [ ] **Indexes created**
  ```sql
  -- Critical indexes
  CREATE INDEX idx_transactions_agent_id ON transactions(agent_id);
  CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);
  CREATE INDEX idx_transactions_status ON transactions(status);
  CREATE INDEX idx_loans_agent_id ON loans(agent_id);
  CREATE INDEX idx_loans_status ON loans(status);
  CREATE INDEX idx_agents_wallet_address ON agents(wallet_address);

  -- Analyze tables
  ANALYZE transactions;
  ANALYZE agents;
  ANALYZE loans;
  ```

- [ ] **Connection pooling configured**
  ```python
  # SQLAlchemy connection pool
  engine = create_engine(
      DATABASE_URL,
      pool_size=20,
      max_overflow=40,
      pool_pre_ping=True,
      pool_recycle=3600
  )
  ```

#### Database Backup

- [ ] **Backup strategy implemented**
  - [ ] Automated daily backups configured
  - [ ] Backup retention policy: 30 days
  - [ ] Backups encrypted
  - [ ] Backups stored off-site
  - [ ] Backup restoration tested

- [ ] **Backup script**
  ```bash
  #!/bin/bash
  # /usr/local/bin/backup-treasury.sh

  DATE=$(date +%Y%m%d_%H%M%S)
  BACKUP_DIR="/backups/treasury"
  DB_NAME="matrix_treasury"

  # Create backup
  pg_dump $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

  # Encrypt backup
  gpg --encrypt --recipient admin@company.com $BACKUP_DIR/db_$DATE.sql.gz

  # Upload to S3/cloud storage
  aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz.gpg s3://backups/treasury/

  # Keep only last 30 days
  find $BACKUP_DIR -type f -mtime +30 -delete
  ```

- [ ] **Backup schedule** (cron)
  ```bash
  # Daily at 2 AM
  0 2 * * * /usr/local/bin/backup-treasury.sh

  # Weekly full backup
  0 3 * * 0 /usr/local/bin/backup-treasury-full.sh
  ```

- [ ] **Test restore procedure**
  ```bash
  # Restore from backup
  gunzip < backup.sql.gz | psql matrix_treasury

  # Verify data integrity
  psql matrix_treasury -c "SELECT COUNT(*) FROM transactions;"
  ```

#### Database Security

- [ ] **Access controls configured**
  - [ ] Disable remote root access
  - [ ] Create service-specific users
  - [ ] Enable SSL connections
  - [ ] Configure pg_hba.conf
  - [ ] Enable query logging for auditing

- [ ] **pg_hba.conf example**
  ```
  # TYPE  DATABASE        USER            ADDRESS                 METHOD
  local   all             postgres                                peer
  host    matrix_treasury matrix          10.0.0.0/8              md5
  hostssl matrix_treasury matrix          0.0.0.0/0               md5
  ```

---

### Monitoring & Logging

#### Prometheus Setup

- [ ] **Prometheus installed and configured**
  - [ ] Scrape configs defined
  - [ ] Retention period set (30 days)
  - [ ] Storage configured
  - [ ] Alert rules loaded

- [ ] **prometheus.yml configured**
  ```yaml
  global:
    scrape_interval: 15s
    evaluation_interval: 15s

  scrape_configs:
    - job_name: 'matrix-treasury-api'
      static_configs:
        - targets: ['treasury-api:8000']
      metrics_path: '/metrics'

    - job_name: 'postgres'
      static_configs:
        - targets: ['postgres-exporter:9187']

    - job_name: 'redis'
      static_configs:
        - targets: ['redis-exporter:9121']
  ```

#### Grafana Dashboards

- [ ] **Grafana installed**
  - [ ] Admin password changed
  - [ ] Prometheus data source configured
  - [ ] Dashboards imported
  - [ ] User access configured

- [ ] **Key dashboards created**
  - [ ] Treasury Overview (balance, coverage ratio, runway)
  - [ ] API Performance (latency, throughput, error rates)
  - [ ] System Resources (CPU, memory, disk)
  - [ ] Database Metrics (connections, query time, locks)
  - [ ] Multi-Currency Balances (USDC, EUR, BTC)
  - [ ] Agent Activity (active agents, transaction volume)

#### Alert Configuration

- [ ] **Critical alerts configured**
  - [ ] Reserve coverage ratio < 1.0
  - [ ] API latency > 1 second
  - [ ] Error rate > 1%
  - [ ] Database connections > 80%
  - [ ] Disk usage > 80%
  - [ ] Memory usage > 90%
  - [ ] Service down/unreachable

- [ ] **alerts.yml example**
  ```yaml
  groups:
    - name: matrix_treasury_alerts
      interval: 30s
      rules:
        - alert: HighReserveDepletion
          expr: matrix_treasury_reserve_coverage_ratio < 1.0
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Reserve coverage critical"
            description: "Coverage ratio is {{ $value }}"

        - alert: APIHighLatency
          expr: http_request_duration_seconds{quantile="0.99"} > 1.0
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "API latency high"
            description: "99th percentile latency is {{ $value }}s"

        - alert: HighErrorRate
          expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High error rate detected"
  ```

- [ ] **Alert channels configured**
  - [ ] Email notifications
  - [ ] Slack/Discord webhooks
  - [ ] PagerDuty integration
  - [ ] SMS alerts for critical issues

#### Logging

- [ ] **Application logging configured**
  ```python
  # logging_config.py
  LOGGING_CONFIG = {
      'version': 1,
      'disable_existing_loggers': False,
      'formatters': {
          'default': {
              'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
          },
          'json': {
              'class': 'pythonjsonlogger.jsonlogger.JsonFormatter'
          }
      },
      'handlers': {
          'file': {
              'class': 'logging.handlers.RotatingFileHandler',
              'filename': 'logs/treasury.log',
              'maxBytes': 10485760,  # 10MB
              'backupCount': 10,
              'formatter': 'json'
          }
      },
      'root': {
          'level': 'INFO',
          'handlers': ['file']
      }
  }
  ```

- [ ] **Log aggregation** (optional but recommended)
  - [ ] ELK Stack (Elasticsearch, Logstash, Kibana)
  - [ ] Loki + Grafana
  - [ ] Cloud logging (CloudWatch, Stackdriver)

- [ ] **Log retention policy**
  - [ ] Application logs: 30 days
  - [ ] Access logs: 90 days
  - [ ] Audit logs: 1 year
  - [ ] Error logs: 90 days

---

## Deployment

### Pre-Deployment Testing

- [ ] **Run full test suite**
  ```bash
  # Unit tests
  pytest tests/unit -v

  # Integration tests
  pytest tests/integration -v

  # Coverage report
  pytest --cov=src --cov-report=html
  ```

- [ ] **Security scanning**
  ```bash
  # Dependency vulnerability scan
  pip-audit

  # Docker image scan
  docker scan matrix-treasury:latest

  # Code security scan
  bandit -r src/
  ```

- [ ] **Load testing**
  ```bash
  # API load test
  ab -n 10000 -c 100 http://localhost:8000/api/v1/

  # Or use k6
  k6 run loadtest.js
  ```

### Deployment Steps

- [ ] **Backup current production**
  ```bash
  # Database backup
  pg_dump matrix_treasury > backup-pre-deploy.sql

  # Volume backup (Docker)
  docker run --rm \
    -v matrix-treasury_postgres_data:/data \
    -v $(pwd):/backup \
    alpine tar czf /backup/postgres-backup.tar.gz /data
  ```

- [ ] **Build images**
  ```bash
  # Build backend
  docker build -t matrix-treasury-api:v1.0.0 .

  # Build frontend
  docker build -t matrix-treasury-ui:v1.0.0 ./ui

  # Tag and push to registry
  docker tag matrix-treasury-api:v1.0.0 registry.example.com/treasury/api:v1.0.0
  docker push registry.example.com/treasury/api:v1.0.0
  ```

- [ ] **Deploy services**

  **Docker Compose:**
  ```bash
  # Pull latest images
  docker compose pull

  # Start services
  docker compose up -d

  # Check status
  docker compose ps
  ```

  **Kubernetes:**
  ```bash
  # Apply configurations
  kubectl apply -f namespace.yaml
  kubectl apply -f secrets.yaml
  kubectl apply -f postgres.yaml
  kubectl apply -f redis.yaml
  kubectl apply -f api-deployment.yaml
  kubectl apply -f ui-deployment.yaml
  kubectl apply -f ingress.yaml

  # Watch rollout
  kubectl rollout status deployment/treasury-api -n matrix-treasury
  ```

- [ ] **Run database migrations**
  ```bash
  # Docker Compose
  docker compose exec treasury-api alembic upgrade head

  # Kubernetes
  kubectl exec -it deployment/treasury-api -n matrix-treasury -- alembic upgrade head
  ```

- [ ] **Verify deployment**
  ```bash
  # Check all services running
  docker compose ps  # or kubectl get pods

  # Health check
  curl http://localhost:8000/api/v1/

  # Test authentication
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}'
  ```

---

## Post-Deployment

### Smoke Testing

- [ ] **API endpoints functional**
  ```bash
  # Health check
  curl https://api.matrix-treasury.com/api/v1/

  # Authentication
  TOKEN=$(curl -X POST https://api.matrix-treasury.com/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"***"}' | jq -r .access_token)

  # Get vitals
  curl https://api.matrix-treasury.com/api/v1/analytics/vitals \
    -H "Authorization: Bearer $TOKEN"

  # Multi-currency balances
  curl https://api.matrix-treasury.com/api/v1/multicurrency/balances
  ```

- [ ] **Frontend accessible**
  - [ ] Homepage loads
  - [ ] Login works
  - [ ] Mission Control dashboard displays
  - [ ] Charts render correctly
  - [ ] WebSocket connections work

- [ ] **Database connectivity**
  ```bash
  # Check connections
  docker compose exec postgres psql -U matrix -c \
    "SELECT count(*) FROM pg_stat_activity;"

  # Verify data
  docker compose exec postgres psql -U matrix matrix_treasury -c \
    "SELECT COUNT(*) FROM transactions;"
  ```

- [ ] **Blockchain connectivity**
  - [ ] RPC endpoints responding
  - [ ] Wallet balances readable
  - [ ] Transaction submission works
  - [ ] Multi-network support verified

### Performance Verification

- [ ] **Response times acceptable**
  - [ ] Homepage: < 2 seconds
  - [ ] API endpoints: < 500ms
  - [ ] Database queries: < 100ms
  - [ ] WebSocket latency: < 100ms

- [ ] **Resource utilization**
  ```bash
  # Check resource usage
  docker stats  # or kubectl top pods

  # Verify within limits
  # CPU: < 70%
  # Memory: < 80%
  # Disk: < 80%
  ```

- [ ] **Concurrent users**
  - [ ] Test with expected load
  - [ ] Verify auto-scaling triggers
  - [ ] Check response times under load

### Monitoring Verification

- [ ] **Metrics collecting**
  - [ ] Prometheus scraping targets
  - [ ] Grafana dashboards updating
  - [ ] Custom metrics visible

- [ ] **Alerts functioning**
  - [ ] Test alert triggers
  - [ ] Verify notification delivery
  - [ ] Check alert routing

- [ ] **Logs aggregating**
  - [ ] Application logs flowing
  - [ ] Access logs captured
  - [ ] Error logs visible
  - [ ] Log search working

### Security Verification

- [ ] **SSL/TLS working**
  ```bash
  # Test SSL
  curl -I https://api.matrix-treasury.com

  # Check SSL rating
  # Use https://www.ssllabs.com/ssltest/
  ```

- [ ] **Security headers present**
  ```bash
  curl -I https://api.matrix-treasury.com | grep -E \
    'Strict-Transport-Security|X-Frame-Options|X-Content-Type-Options'
  ```

- [ ] **Authentication enforced**
  - [ ] Unauthenticated requests rejected
  - [ ] Invalid tokens rejected
  - [ ] Expired tokens rejected
  - [ ] Admin endpoints protected

- [ ] **Rate limiting active**
  ```bash
  # Test rate limit
  for i in {1..150}; do
    curl https://api.matrix-treasury.com/api/v1/analytics/vitals
  done
  # Should see 429 Too Many Requests
  ```

### Documentation

- [ ] **Update documentation**
  - [ ] Deployment date and version
  - [ ] Configuration changes
  - [ ] Known issues
  - [ ] Rollback procedures

- [ ] **Runbook updated**
  - [ ] Emergency contacts
  - [ ] Troubleshooting steps
  - [ ] Common issues and solutions

- [ ] **Team notification**
  - [ ] Deployment announcement
  - [ ] New features communicated
  - [ ] Breaking changes highlighted
  - [ ] Support team briefed

---

## Ongoing Operations

### Daily Tasks

- [ ] **Monitor dashboards**
  - [ ] Check Grafana for anomalies
  - [ ] Review error rates
  - [ ] Verify backup completion
  - [ ] Check alert status

- [ ] **Review logs**
  - [ ] Check for errors
  - [ ] Investigate warnings
  - [ ] Monitor security events

- [ ] **Health checks**
  ```bash
  # Service health
  curl https://api.matrix-treasury.com/api/v1/

  # Database health
  docker compose exec postgres pg_isready

  # Redis health
  docker compose exec redis redis-cli ping
  ```

### Weekly Tasks

- [ ] **Performance review**
  - [ ] Review response times
  - [ ] Check resource utilization
  - [ ] Analyze slow queries
  - [ ] Review scaling events

- [ ] **Security audit**
  - [ ] Review access logs
  - [ ] Check failed login attempts
  - [ ] Verify SSL certificate validity
  - [ ] Review user permissions

- [ ] **Backup verification**
  - [ ] Verify backup completion
  - [ ] Test restore procedure
  - [ ] Check backup integrity

### Monthly Tasks

- [ ] **Security updates**
  - [ ] Update system packages
  - [ ] Update Docker images
  - [ ] Update dependencies
  - [ ] Run security scans

- [ ] **Performance optimization**
  - [ ] Database maintenance (VACUUM, ANALYZE)
  - [ ] Review and optimize slow queries
  - [ ] Clear old logs and data
  - [ ] Review and tune caching

- [ ] **Capacity planning**
  - [ ] Review growth trends
  - [ ] Project future resource needs
  - [ ] Plan scaling activities
  - [ ] Review costs

### Quarterly Tasks

- [ ] **Disaster recovery test**
  - [ ] Full system restore from backup
  - [ ] Failover testing
  - [ ] Document lessons learned

- [ ] **Security review**
  - [ ] Penetration testing
  - [ ] Vulnerability assessment
  - [ ] Access control review
  - [ ] Secret rotation

- [ ] **Documentation review**
  - [ ] Update runbooks
  - [ ] Review procedures
  - [ ] Update architecture diagrams

---

## Emergency Procedures

### Service Down

```bash
# 1. Check service status
docker compose ps  # or kubectl get pods

# 2. View logs
docker compose logs treasury-api --tail=100

# 3. Restart service
docker compose restart treasury-api

# 4. If still down, rollback
docker compose down
docker compose up -d --force-recreate
```

### Database Issues

```bash
# 1. Check connections
docker compose exec postgres psql -U matrix -c \
  "SELECT count(*) FROM pg_stat_activity;"

# 2. Kill long-running queries
docker compose exec postgres psql -U matrix -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity \
   WHERE state = 'active' AND now() - query_start > interval '5 minutes';"

# 3. Restart database (last resort)
docker compose restart postgres
```

### High Memory/CPU

```bash
# 1. Identify culprit
docker stats

# 2. Scale down if needed
docker compose up -d --scale treasury-api=2

# 3. Restart high-usage containers
docker compose restart treasury-api

# 4. Check for memory leaks
docker compose logs treasury-api | grep -i "memory\|oom"
```

### Rollback Deployment

```bash
# 1. Stop current version
docker compose down

# 2. Restore database
gunzip < backup-pre-deploy.sql.gz | \
  docker compose exec -T postgres psql -U matrix matrix_treasury

# 3. Deploy previous version
git checkout v0.9.0
docker compose up -d

# 4. Verify
curl http://localhost:8000/api/v1/
```

### Data Breach Response

1. **Immediate actions**
   - [ ] Isolate affected systems
   - [ ] Preserve logs and evidence
   - [ ] Notify security team
   - [ ] Activate incident response plan

2. **Investigation**
   - [ ] Identify scope of breach
   - [ ] Determine data accessed
   - [ ] Trace attack vector
   - [ ] Document findings

3. **Remediation**
   - [ ] Patch vulnerabilities
   - [ ] Reset compromised credentials
   - [ ] Implement additional controls
   - [ ] Monitor for further activity

4. **Communication**
   - [ ] Notify affected users
   - [ ] Report to authorities (if required)
   - [ ] Public disclosure (if needed)

---

## Compliance & Audit

### Regulatory Compliance

- [ ] **GDPR** (if applicable)
  - [ ] User data handling procedures
  - [ ] Right to deletion implemented
  - [ ] Data portability supported
  - [ ] Privacy policy updated

- [ ] **SOC 2** (if applicable)
  - [ ] Access controls documented
  - [ ] Audit logging enabled
  - [ ] Incident response plan
  - [ ] Regular security assessments

- [ ] **Financial regulations**
  - [ ] Transaction logging
  - [ ] AML/KYC procedures
  - [ ] Audit trail maintenance

### Audit Logging

- [ ] **Critical events logged**
  - [ ] User authentication
  - [ ] Admin actions
  - [ ] Configuration changes
  - [ ] Financial transactions
  - [ ] Access control changes

- [ ] **Log retention**
  - [ ] Audit logs: 1 year minimum
  - [ ] Immutable storage
  - [ ] Regular integrity checks

---

## Support Contacts

### Emergency Contacts

- **On-Call Engineer**: [Phone/Email]
- **Database Admin**: [Phone/Email]
- **Security Team**: [Phone/Email]
- **DevOps Lead**: [Phone/Email]

### Escalation Path

1. On-Call Engineer
2. Engineering Manager
3. CTO
4. CEO (for critical incidents)

### External Support

- **Cloud Provider**: [Support link/phone]
- **Database Support**: [Contact info]
- **Security Vendor**: [Contact info]

---

## Version History

| Version | Date | Changes | Approved By |
|---------|------|---------|-------------|
| 1.0.0   | 2026-01-11 | Initial production deployment | [Name] |

---

## Sign-Off

Production deployment checklist completed by:

- **DevOps Engineer**: ___________________ Date: ___________
- **Security Officer**: ___________________ Date: ___________
- **Engineering Manager**: _______________ Date: ___________
- **Product Owner**: _____________________ Date: ___________

---

**Note**: This checklist should be reviewed and updated regularly. Not all items may apply to every deployment. Use professional judgment and adapt as needed for your specific environment.
