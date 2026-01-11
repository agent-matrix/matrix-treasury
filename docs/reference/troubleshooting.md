# Troubleshooting Guide

Common issues and solutions for Matrix Treasury.

## Backend Issues

### Server Won't Start

**Problem**: Backend fails to start

```bash
Error: Address already in use
```

**Solution**:

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change port in .env
PORT=8001
```

**Problem**: Import errors

```bash
ModuleNotFoundError: No module named 'src'
```

**Solution**:

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt -r requirements-upgrade.txt

# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Database Issues

**Problem**: Database locked

```bash
sqlite3.OperationalError: database is locked
```

**Solution**:

```bash
# Stop all processes
docker-compose down

# Remove lock files
rm data/treasury.db-wal data/treasury.db-shm

# Restart
docker-compose up -d
```

**Problem**: Table doesn't exist

```bash
sqlalchemy.exc.OperationalError: no such table: agents
```

**Solution**:

```bash
# Initialize database
make db-init

# Or run migrations
alembic upgrade head
```

**Problem**: Database connection failed

```bash
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution**:

```bash
# Check DATABASE_URL in .env
echo $DATABASE_URL

# Test PostgreSQL connection
psql $DATABASE_URL

# Verify PostgreSQL is running
docker-compose ps db
```

### Authentication Issues

**Problem**: JWT token expired

```bash
401 Unauthorized: JWT token has expired
```

**Solution**:

```bash
# Login again to get new token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Problem**: Invalid credentials

```bash
401 Unauthorized: Invalid credentials
```

**Solution**:

```bash
# Check admin credentials in .env
cat .env | grep ADMIN

# Reset admin password
python scripts/reset_admin_password.py

# Or manually update database
sqlite3 data/treasury.db "UPDATE admin_users SET password_hash='...' WHERE username='admin'"
```

## Frontend Issues

### Build Failures

**Problem**: npm install fails

```bash
npm ERR! code ERESOLVE
npm ERR! ERESOLVE could not resolve
```

**Solution**:

```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall
npm install

# Or use legacy peer deps
npm install --legacy-peer-deps
```

**Problem**: Vite build fails

```bash
Error: Build failed with errors
```

**Solution**:

```bash
# Check Node version (requires 18+)
node --version

# Update Node
nvm install 18
nvm use 18

# Clear Vite cache
rm -rf node_modules/.vite

# Rebuild
npm run build
```

### Runtime Errors

**Problem**: White screen / blank page

**Solution**:

```javascript
// Check browser console for errors
// Common causes:

// 1. API endpoint wrong
// Check VITE_API_URL in .env
VITE_API_URL=http://localhost:8000

// 2. CORS issues
// Enable CORS in backend (src/main.py)

// 3. Bundle size issues
// Check for large imports
```

**Problem**: API calls failing

```bash
Failed to fetch: TypeError: NetworkError
```

**Solution**:

```javascript
// Check backend is running
curl http://localhost:8000/api/v1/

// Check API URL in frontend
console.log(import.meta.env.VITE_API_URL)

// Check CORS headers
// Should include: Access-Control-Allow-Origin
```

## Docker Issues

### Container Issues

**Problem**: Container won't start

```bash
docker-compose up -d
Error: Container exited with code 1
```

**Solution**:

```bash
# View container logs
docker-compose logs backend

# Check for common issues:
# - Port conflicts
# - Missing environment variables
# - Database connection failures

# Rebuild container
docker-compose build --no-cache backend
docker-compose up -d
```

**Problem**: Out of disk space

```bash
Error: No space left on device
```

**Solution**:

```bash
# Check disk usage
df -h

# Clean Docker system
docker system prune -a

# Remove unused volumes
docker volume prune

# Remove specific images
docker rmi $(docker images -q)
```

**Problem**: Container health check failing

```bash
Container backend is unhealthy
```

**Solution**:

```bash
# Check health check logs
docker inspect matrix-treasury-backend-1 | grep -A 20 Health

# Test health endpoint manually
docker-compose exec backend curl http://localhost:8000/api/v1/

# Adjust health check in docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/"]
  interval: 30s
  timeout: 10s
  retries: 5
  start_period: 40s
```

### Network Issues

**Problem**: Services can't communicate

```bash
backend | Could not connect to database
```

**Solution**:

```bash
# Check network
docker network ls
docker network inspect matrix-treasury_default

# Verify service names match
# Use service name from docker-compose.yml as hostname
# e.g., DATABASE_URL=postgresql://user:pass@db:5432/treasury
```

## Performance Issues

### Slow API Responses

**Problem**: API endpoints taking >1 second

**Solution**:

```python
# 1. Add database indexes
from sqlalchemy import Index

Index('idx_agent_id', Agent.agent_id)
Index('idx_transaction_created', Transaction.created_at)

# 2. Use eager loading
from sqlalchemy.orm import joinedload

agents = db.query(Agent).options(
    joinedload(Agent.transactions)
).all()

# 3. Enable query caching
from functools import lru_cache

@lru_cache(maxsize=100)
def get_agent_balance(agent_id: str):
    return db.query(Agent).filter_by(agent_id=agent_id).first().balance

# 4. Use connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20
)
```

### High Memory Usage

**Problem**: Backend using >1GB RAM

**Solution**:

```python
# 1. Limit query results
agents = db.query(Agent).limit(100).all()

# 2. Use pagination
def get_agents(page: int = 1, per_page: int = 50):
    offset = (page - 1) * per_page
    return db.query(Agent).offset(offset).limit(per_page).all()

# 3. Close database sessions
try:
    db = next(get_db())
    # ... operations
finally:
    db.close()

# 4. Stream large responses
from fastapi.responses import StreamingResponse

@router.get("/export")
def export_data():
    def generate():
        for row in db.query(Transaction).yield_per(100):
            yield json.dumps(row.to_dict()) + "\n"
    return StreamingResponse(generate())
```

### Slow Frontend

**Problem**: Page load time >3 seconds

**Solution**:

```typescript
// 1. Code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings = lazy(() => import('./pages/Settings'));

// 2. Memoization
const expensiveValue = useMemo(() => {
  return computeExpensiveValue(data);
}, [data]);

// 3. Virtualization for long lists
import { FixedSizeList } from 'react-window';

// 4. Optimize images
// Use WebP format
// Lazy load images
<img loading="lazy" src="..." />

// 5. Reduce bundle size
// Check bundle analyzer
npm run build -- --analyze
```

## Blockchain Issues

### Transaction Failures

**Problem**: On-chain transaction failed

```bash
Error: insufficient funds for gas
```

**Solution**:

```bash
# Check wallet balance
curl http://localhost:8000/api/v1/wallet/balance

# Fund wallet with gas token (ETH, MATIC, etc.)
# Use testnet faucet for testing

# Adjust gas settings
GAS_PRICE_GWEI=20
MAX_FEE_PER_GAS=100
```

**Problem**: Transaction stuck/pending

**Solution**:

```bash
# Check transaction status
curl http://localhost:8000/api/v1/transactions/<tx_id>

# Speed up transaction (replace with higher gas)
# Or wait for network congestion to clear

# Cancel transaction (replace with 0 value, same nonce)
```

### Network Issues

**Problem**: Cannot connect to blockchain node

```bash
Error: ConnectionError: RPC endpoint unreachable
```

**Solution**:

```bash
# Check RPC endpoint
curl $BASE_RPC_URL

# Try alternative RPC
BASE_RPC_URL=https://mainnet.base.org

# Use public RPC as fallback
# - Alchemy
# - Infura
# - QuickNode
```

## Testing Issues

### Tests Failing

**Problem**: Tests pass locally but fail in CI

**Solution**:

```python
# 1. Ensure consistent test environment
@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    # ...

# 2. Mock external dependencies
@patch('requests.get')
def test_external_api(mock_get):
    mock_get.return_value.json.return_value = {"price": 1.0}
    # ...

# 3. Fix race conditions
import time
time.sleep(0.1)  # Wait for async operations

# Or use proper async testing
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
```

**Problem**: Intermittent test failures

**Solution**:

```python
# 1. Add retries for flaky tests
@pytest.mark.flaky(reruns=3)
def test_flaky():
    # ...

# 2. Fix timing issues
# Use polling instead of sleep
def wait_for_condition(condition, timeout=5):
    start = time.time()
    while time.time() - start < timeout:
        if condition():
            return True
        time.sleep(0.1)
    return False

# 3. Isolate tests
# Ensure each test cleans up after itself
@pytest.fixture
def cleanup():
    yield
    # Cleanup code
```

## Production Issues

### High CPU Usage

**Problem**: CPU usage >80%

**Solution**:

```bash
# 1. Check process
top -p $(pidof python)

# 2. Profile code
python -m cProfile -o profile.stats src/main.py

# 3. Optimize hot paths
# Use caching
# Reduce unnecessary computation
# Use async where applicable

# 4. Scale horizontally
# Add more workers
uvicorn src.main:app --workers 4
```

### Memory Leaks

**Problem**: Memory usage grows over time

**Solution**:

```python
# 1. Profile memory
import tracemalloc
tracemalloc.start()
# ... run code
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

# 2. Close database connections
# Use context managers
with get_db() as db:
    # ... operations

# 3. Clear caches periodically
cache.clear()

# 4. Restart workers periodically
# Gunicorn: --max-requests 1000
# Uvicorn: --limit-max-requests 1000
```

### Database Performance

**Problem**: Slow queries

**Solution**:

```sql
-- 1. Analyze query
EXPLAIN ANALYZE SELECT * FROM agents WHERE email = 'test@example.com';

-- 2. Add indexes
CREATE INDEX idx_agents_email ON agents(email);

-- 3. Optimize query
-- Before: SELECT *
-- After: SELECT id, email, balance

-- 4. Use query caching
-- PostgreSQL: pg_stat_statements
-- Redis caching layer
```

## Monitoring & Alerts

### Set Up Alerts

```python
# Sentry for error tracking
import sentry_sdk
sentry_sdk.init(dsn="...")

# Custom alerts
def check_treasury_health():
    if treasury.reserve_ratio < 1.1:
        send_alert("Critical: Low reserve ratio")

# Prometheus metrics
from prometheus_client import Counter, Histogram

request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')
```

### Log Analysis

```bash
# Find errors
grep "ERROR" logs/treasury.log | tail -n 20

# Count error types
grep "ERROR" logs/treasury.log | cut -d: -f2 | sort | uniq -c

# Monitor logs in real-time
tail -f logs/treasury.log | grep --color=auto "ERROR\|WARNING"
```

## Getting Help

### Self-Service

1. Check this troubleshooting guide
2. Search [GitHub Issues](https://github.com/agent-matrix/matrix-treasury/issues)
3. Review [documentation](../README.md)
4. Check logs for error messages

### Community Support

- **Discord**: https://discord.gg/AJUnEerk
- **GitHub Discussions**: Start a discussion
- **Stack Overflow**: Tag with `matrix-treasury`

### Report a Bug

Open an issue with:

1. **Description**: What happened?
2. **Expected Behavior**: What should happen?
3. **Steps to Reproduce**: How to replicate?
4. **Environment**:
   - OS: Ubuntu 22.04
   - Python: 3.11.0
   - Node: 18.0.0
   - Docker: 20.10.0
5. **Logs**: Relevant error messages
6. **Screenshots**: If applicable

### Emergency Contact

For critical production issues:

- **Email**: contact@ruslanmv.com
- **Priority**: Use [URGENT] in subject line

## See Also

- [Configuration Reference](configuration.md)
- [CLI Commands](cli.md)
- [Development Guide](../guides/development.md)
- [Production Checklist](../deployment/production-checklist.md)
