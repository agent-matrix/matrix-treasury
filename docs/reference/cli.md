# CLI Commands

Command-line interface reference for Matrix Treasury.

## Makefile Commands

The project includes a Makefile for common development tasks.

### Installation

```bash
# Install all dependencies (backend + frontend)
make install

# Install backend only
make install-backend

# Install frontend only
make install-frontend
```

### Development

```bash
# Start development server with auto-reload
make dev

# Start frontend dev server
make dev-frontend

# Start backend dev server
make dev-backend
```

### Testing

```bash
# Run all tests
make test

# Run backend tests only
make test-backend

# Run frontend tests only
make test-frontend

# Run tests with coverage
make coverage

# Run specific test file
make test FILE=tests/unit/test_treasury.py
```

### Code Quality

```bash
# Format code (Black for Python, Prettier for TypeScript)
make format

# Lint code
make lint

# Type check
make typecheck

# Run all quality checks
make check
```

### Docker

```bash
# Build Docker images
make docker-build

# Start Docker services
make docker-up

# Stop Docker services
make docker-down

# View Docker logs
make docker-logs

# Clean Docker volumes
make docker-clean
```

### Database

```bash
# Initialize database
make db-init

# Run migrations
make db-migrate

# Create new migration
make db-migration NAME="migration_name"

# Seed database
make db-seed

# Reset database (WARNING: destroys all data)
make db-reset

# Backup database
make db-backup

# Restore database
make db-restore BACKUP=backups/treasury_20260111.sql
```

### Deployment

```bash
# Build for production
make build

# Deploy to production
make deploy

# Deploy to staging
make deploy-staging
```

### Cleanup

```bash
# Clean build artifacts
make clean

# Clean Python cache
make clean-py

# Clean Node modules
make clean-node

# Clean everything
make clean-all
```

## Python Scripts

### Database Management

**Seed Database**:

```bash
python scripts/seed_database.py
```

**Backup Database**:

```bash
python scripts/backup_database.py --output backups/
```

**Restore Database**:

```bash
python scripts/restore_database.py --input backups/treasury_20260111.sql
```

### Treasury Operations

**Check Treasury Health**:

```bash
python scripts/check_health.py
```

Output:
```
Treasury Health Report
======================
Reserve: $5,432.50 USDC
Token Supply: 4,000,000 MXU
Reserve Ratio: 1.358
Status: HEALTHY ✓

Currencies:
- USDC: $5,432.50
- EUR: €2,100.00
- BTC: 0.05 BTC

Active Agents: 45
Pending Approvals: 2
```

**Generate Report**:

```bash
python scripts/generate_report.py --period monthly --output reports/
```

### Data Migration

**Migrate to PostgreSQL**:

```bash
python scripts/migrate_to_postgres.py \
  --source sqlite:///./data/treasury.db \
  --target postgresql://user:pass@localhost/treasury
```

**Export Data**:

```bash
python scripts/export_data.py --format csv --output exports/
```

**Import Data**:

```bash
python scripts/import_data.py --format csv --input exports/agents.csv
```

### Maintenance

**Clean Old Records**:

```bash
# Delete transactions older than 1 year
python scripts/cleanup_old_data.py --days 365 --table transactions
```

**Rebuild Indexes**:

```bash
python scripts/rebuild_indexes.py
```

**Vacuum Database**:

```bash
python scripts/vacuum_database.py
```

## API Client

### Installation

```bash
pip install matrix-treasury-client
```

### Basic Usage

```python
from matrix_treasury import TreasuryClient

client = TreasuryClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# Onboard agent
agent = client.agents.onboard(
    agent_id="agent-001",
    email="agent@example.com"
)

# Check balance
balance = client.agents.get_balance("agent-001")
print(f"Balance: {balance} MXU")

# Make deposit
client.treasury.deposit(
    amount=100.0,
    currency="USDC",
    network="BASE"
)
```

### CLI Tool

```bash
# Login
treasury-cli login --username admin

# Check balance
treasury-cli balance

# List agents
treasury-cli agents list

# Onboard agent
treasury-cli agents onboard \
  --id agent-001 \
  --email agent@example.com

# Make deposit
treasury-cli treasury deposit \
  --amount 100 \
  --currency USDC \
  --network BASE

# Check health
treasury-cli health

# View logs
treasury-cli logs --limit 50 --follow
```

## Docker Commands

### Basic Operations

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a service
docker-compose restart backend

# View logs
docker-compose logs -f backend

# Execute command in container
docker-compose exec backend python scripts/check_health.py
```

### Database Operations

```bash
# Connect to database
docker-compose exec db psql -U treasury_user -d treasury

# Backup database
docker-compose exec db pg_dump -U treasury_user treasury > backup.sql

# Restore database
docker-compose exec -T db psql -U treasury_user treasury < backup.sql
```

### Debugging

```bash
# Shell into backend container
docker-compose exec backend bash

# Shell into database container
docker-compose exec db bash

# View container details
docker inspect matrix-treasury-backend-1

# Check resource usage
docker stats

# View container processes
docker-compose top
```

## Git Commands

### Development Workflow

```bash
# Create feature branch
git checkout -b feature/new-feature

# Stage changes
git add .

# Commit with conventional commit format
git commit -m "feat: Add new feature"

# Push to remote
git push origin feature/new-feature

# Update from main
git fetch upstream
git rebase upstream/main
```

### Useful Aliases

Add to `.gitconfig`:

```ini
[alias]
  st = status -sb
  co = checkout
  br = branch
  ci = commit
  unstage = reset HEAD --
  last = log -1 HEAD
  visual = log --oneline --graph --decorate
```

## Testing Commands

### Backend Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_treasury.py

# Run specific test
pytest tests/unit/test_treasury.py::TestTreasury::test_mint_tokens

# Run with markers
pytest -m "not slow"

# Run with coverage
pytest --cov=src --cov-report=html

# Run in parallel
pytest -n auto

# Run only failed tests
pytest --lf

# Run with verbose output
pytest -v

# Run with print statements
pytest -s
```

### Frontend Tests

```bash
# Run all tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage

# Update snapshots
npm test -- -u

# Run specific test file
npm test -- AgentBalance.test.tsx
```

## Environment Management

### Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Deactivate
deactivate

# Update pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Freeze requirements
pip freeze > requirements.txt
```

### Node Version Management

```bash
# Using nvm
nvm install 18
nvm use 18
nvm alias default 18

# Check version
node --version
npm --version
```

## Monitoring Commands

### System Status

```bash
# Check service status
systemctl status matrix-treasury

# View systemd logs
journalctl -u matrix-treasury -f

# Check port usage
lsof -i :8000
netstat -tulpn | grep 8000
```

### Performance Monitoring

```bash
# Monitor CPU/Memory
top
htop

# Monitor disk usage
df -h
du -sh data/

# Monitor network
iftop
nethogs
```

### Log Analysis

```bash
# View backend logs
tail -f logs/treasury.log

# Search logs
grep "ERROR" logs/treasury.log

# Count errors
grep -c "ERROR" logs/treasury.log

# View last 100 errors
grep "ERROR" logs/treasury.log | tail -n 100
```

## Kubernetes Commands

### Basic Operations

```bash
# Deploy
kubectl apply -f k8s/

# Get pods
kubectl get pods -n matrix-treasury

# View logs
kubectl logs -f deployment/backend -n matrix-treasury

# Execute command in pod
kubectl exec -it pod/backend-xyz -- /bin/bash

# Port forward
kubectl port-forward service/backend 8000:8000 -n matrix-treasury
```

### Scaling

```bash
# Scale deployment
kubectl scale deployment backend --replicas=3 -n matrix-treasury

# Autoscale
kubectl autoscale deployment backend \
  --cpu-percent=80 \
  --min=2 \
  --max=10 \
  -n matrix-treasury
```

### Debugging

```bash
# Describe pod
kubectl describe pod backend-xyz -n matrix-treasury

# Get events
kubectl get events -n matrix-treasury --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -n matrix-treasury
kubectl top nodes
```

## Quick Reference

### Essential Commands

```bash
# Development
make dev                    # Start dev server
make test                   # Run tests
make format                 # Format code

# Docker
docker-compose up -d        # Start services
docker-compose logs -f      # View logs
docker-compose down         # Stop services

# Database
make db-init                # Initialize
make db-migrate             # Run migrations
make db-backup              # Backup

# Git
git status                  # Check status
git commit -m "message"     # Commit
git push                    # Push changes
```

### Troubleshooting Commands

```bash
# Check health
curl http://localhost:8000/api/v1/

# View logs
tail -f logs/treasury.log

# Check database
sqlite3 data/treasury.db ".tables"

# Kill process
kill -9 $(lsof -t -i:8000)

# Restart services
docker-compose restart

# Clear cache
make clean
```

## See Also

- [Development Guide](../guides/development.md)
- [Testing Guide](../guides/testing.md)
- [Troubleshooting](troubleshooting.md)
- [Configuration Reference](configuration.md)
