# Development Guide

Guide for developers contributing to Matrix Treasury.

## Development Environment Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git
- Docker (optional)
- PostgreSQL (optional, for production testing)

### Clone Repository

```bash
git clone https://github.com/agent-matrix/matrix-treasury.git
cd matrix-treasury
```

### Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-upgrade.txt

# Install development tools
pip install pytest pytest-cov pytest-asyncio black flake8 mypy

# Initialize database
make install

# Run backend
make dev
```

Backend runs on http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Install development tools
npm install --save-dev @types/react @types/node eslint prettier

# Start dev server
npm run dev
```

Frontend runs on http://localhost:5173

## Project Structure

```
matrix-treasury/
├── src/                    # Backend Python code
│   ├── api/               # API routes
│   │   ├── routes.py     # Core treasury routes
│   │   ├── autonomous_routes.py  # Legacy autonomous routes
│   │   └── mission_control_routes.py  # Mission Control routes
│   ├── core/              # Core business logic
│   │   ├── economy.py    # Economic engine
│   │   ├── treasury.py   # Treasury management
│   │   ├── credit_system.py  # Credit/debt system
│   │   └── metering.py   # Usage metering
│   ├── db/                # Database layer
│   │   ├── models.py     # SQLAlchemy models
│   │   ├── connection.py # Database connection
│   │   └── seed.py       # Database seeding
│   ├── security/          # Security modules
│   │   ├── jwt_auth.py   # JWT authentication
│   │   └── sybil_detection.py  # ML-based sybil detection
│   ├── blockchain/        # Blockchain integration
│   │   ├── multi_currency_vault.py  # Multi-currency vault
│   │   └── ledger.py     # Blockchain ledger
│   └── main.py           # FastAPI application
├── frontend/              # React frontend
│   ├── src/
│   │   ├── pages/        # Page components
│   │   ├── components/   # Reusable components
│   │   ├── hooks/        # Custom React hooks
│   │   └── lib/          # Utilities
│   └── package.json
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── docs/                  # Documentation
├── Makefile              # Development commands
└── docker-compose.yml    # Docker configuration
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Edit code following our coding standards (see below).

### 3. Run Tests

```bash
# Backend tests
make test

# With coverage
make coverage

# Frontend tests
cd frontend && npm test
```

### 4. Format Code

```bash
# Python formatting
black src/ tests/
flake8 src/ tests/

# TypeScript formatting
cd frontend
npm run lint
npm run format
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: Add new feature description"
```

Use conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Coding Standards

### Python (Backend)

**Style Guide**: PEP 8

```python
# Good
def calculate_balance(agent_id: str, currency: str = "USDC") -> float:
    """Calculate agent balance in specified currency.

    Args:
        agent_id: Unique agent identifier
        currency: Currency code (default: USDC)

    Returns:
        float: Current balance

    Raises:
        AgentNotFoundError: If agent doesn't exist
    """
    agent = get_agent(agent_id)
    if not agent:
        raise AgentNotFoundError(f"Agent {agent_id} not found")
    return agent.balance

# Bad
def calc_bal(id, curr="USDC"):
    a = get_agent(id)
    return a.balance
```

**Type Hints**: Always use type hints

```python
from typing import Optional, List, Dict

def process_transaction(
    agent_id: str,
    amount: float,
    tx_type: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Transaction:
    ...
```

**Error Handling**: Use specific exceptions

```python
from src.core.exceptions import InsufficientBalanceError

def charge_agent(agent_id: str, amount: float):
    if agent.balance < amount:
        raise InsufficientBalanceError(
            f"Insufficient balance: required {amount}, available {agent.balance}"
        )
```

### TypeScript (Frontend)

**Style Guide**: Airbnb TypeScript Style Guide

```typescript
// Good
interface Agent {
  id: string;
  email: string;
  balance: number;
  createdAt: Date;
}

function getAgentBalance(agentId: string): Promise<number> {
  return fetch(`/api/v1/agents/${agentId}/balance`)
    .then(res => res.json())
    .then(data => data.balance);
}

// Bad
function getBalance(id) {
  return fetch('/api/v1/agents/' + id + '/balance')
    .then(res => res.json())
    .then(data => data.balance);
}
```

**React Components**: Use functional components with hooks

```typescript
import { useState, useEffect } from 'react';

interface Props {
  agentId: string;
}

export function AgentBalance({ agentId }: Props) {
  const [balance, setBalance] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBalance(agentId)
      .then(setBalance)
      .finally(() => setLoading(false));
  }, [agentId]);

  if (loading) return <Spinner />;
  return <div>Balance: ${balance}</div>;
}
```

## Testing

### Backend Tests

**Unit Tests**: Test individual functions

```python
# tests/unit/test_treasury.py
import pytest
from src.core.treasury import Treasury

def test_mint_tokens():
    treasury = Treasury(initial_reserve=1000.0)
    treasury.mint(100.0)
    assert treasury.token_supply == 100.0

def test_mint_fails_insufficient_reserve():
    treasury = Treasury(initial_reserve=100.0)
    with pytest.raises(InsufficientReserveError):
        treasury.mint(1000.0)
```

**Integration Tests**: Test API endpoints

```python
# tests/integration/test_api.py
def test_agent_onboarding(client):
    response = client.post("/api/v1/agents/onboard", json={
        "agent_id": "test-agent",
        "email": "test@example.com",
        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["agent_id"] == "test-agent"
```

### Frontend Tests

**Component Tests**: Test React components

```typescript
import { render, screen } from '@testing-library/react';
import { AgentBalance } from './AgentBalance';

test('renders agent balance', async () => {
  render(<AgentBalance agentId="agent-001" />);

  expect(screen.getByText(/loading/i)).toBeInTheDocument();

  const balance = await screen.findByText(/balance: \$100/i);
  expect(balance).toBeInTheDocument();
});
```

### Running Tests

```bash
# All backend tests
make test

# Specific test file
pytest tests/unit/test_treasury.py

# With coverage
make coverage

# Frontend tests
cd frontend
npm test

# Watch mode
npm test -- --watch
```

## Debugging

### Backend Debugging

**Using Print Statements**:

```python
print(f"Agent balance: {agent.balance}")
```

**Using Logging**:

```python
import logging
logger = logging.getLogger(__name__)

logger.debug(f"Processing transaction: {tx_id}")
logger.info(f"Agent {agent_id} onboarded successfully")
logger.warning(f"Low balance: {agent.balance}")
logger.error(f"Transaction failed: {error}")
```

**Using Debugger**:

```python
import pdb; pdb.set_trace()  # Set breakpoint

# Or use ipdb for better experience
import ipdb; ipdb.set_trace()
```

**VS Code Debug Configuration** (`.vscode/launch.json`):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "src.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true
    }
  ]
}
```

### Frontend Debugging

**Browser DevTools**: Use React DevTools extension

**Console Logging**:

```typescript
console.log('Agent data:', agent);
console.error('Failed to fetch:', error);
```

**React Query DevTools**:

```typescript
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <YourApp />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

## Database Management

### Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Database Shell

```bash
# SQLite
sqlite3 data/treasury.db

# PostgreSQL
psql -U treasury_user -d treasury
```

### Seed Development Data

```python
# scripts/seed_dev_data.py
from src.db.connection import get_db
from src.db.models import Agent, Transaction

db = next(get_db())

# Create test agents
agent1 = Agent(agent_id="dev-001", email="dev1@test.com")
db.add(agent1)
db.commit()
```

## Performance Optimization

### Backend

**Database Queries**: Use eager loading

```python
# Bad - N+1 query problem
agents = db.query(Agent).all()
for agent in agents:
    print(agent.transactions)  # Triggers new query each time

# Good - Eager loading
from sqlalchemy.orm import joinedload
agents = db.query(Agent).options(joinedload(Agent.transactions)).all()
```

**Caching**: Use Redis for frequently accessed data

```python
import redis
cache = redis.Redis(host='localhost', port=6379)

def get_agent_balance(agent_id: str) -> float:
    # Check cache first
    cached = cache.get(f"balance:{agent_id}")
    if cached:
        return float(cached)

    # Fetch from database
    balance = db.query(Agent).filter_by(agent_id=agent_id).first().balance

    # Cache for 5 minutes
    cache.setex(f"balance:{agent_id}", 300, str(balance))
    return balance
```

### Frontend

**Code Splitting**: Lazy load routes

```typescript
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings = lazy(() => import('./pages/Settings'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
}
```

**Memoization**: Prevent unnecessary re-renders

```typescript
import { useMemo, useCallback } from 'react';

function AgentList({ agents }: Props) {
  const sortedAgents = useMemo(
    () => agents.sort((a, b) => b.balance - a.balance),
    [agents]
  );

  const handleClick = useCallback((agentId: string) => {
    console.log('Clicked:', agentId);
  }, []);

  return <>{/* render */}</>;
}
```

## Common Development Tasks

### Add New API Endpoint

1. Define route in `src/api/routes.py`:

```python
@router.post("/agents/{agent_id}/charge")
def charge_agent(agent_id: str, amount: float, db: Session = Depends(get_db)):
    # Implementation
    return {"status": "success"}
```

2. Add tests in `tests/integration/test_api.py`
3. Update API documentation

### Add Database Model

1. Define model in `src/db/models.py`:

```python
class NewModel(Base):
    __tablename__ = "new_models"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
```

2. Create migration:

```bash
alembic revision --autogenerate -m "Add NewModel"
alembic upgrade head
```

### Add Frontend Component

1. Create component file:

```typescript
// src/components/NewComponent.tsx
export function NewComponent() {
  return <div>New Component</div>;
}
```

2. Add tests
3. Export from index
4. Use in pages

## See Also

- [Testing Guide](testing.md)
- [Contributing Guidelines](contributing.md)
- [API Reference](../API_REFERENCE.md)
- [Architecture Overview](../architecture/system-overview.md)
