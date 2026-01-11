# Testing Guide

Comprehensive testing strategies for Matrix Treasury.

## Test Philosophy

- **Test Early, Test Often**: Write tests as you develop
- **Test Coverage**: Aim for >80% code coverage
- **Test Pyramid**: More unit tests, fewer integration tests, minimal E2E tests
- **Fast Feedback**: Tests should run quickly (<5 seconds for unit tests)

## Test Types

### Unit Tests

Test individual functions/methods in isolation.

**Location**: `tests/unit/`

**Example**:

```python
# tests/unit/test_treasury.py
import pytest
from src.core.treasury import Treasury
from src.core.exceptions import InsufficientReserveError

class TestTreasury:
    def test_initialization(self):
        treasury = Treasury(initial_reserve=1000.0)
        assert treasury.reserve == 1000.0
        assert treasury.token_supply == 0.0

    def test_mint_tokens(self):
        treasury = Treasury(initial_reserve=1000.0)
        tokens = treasury.mint(100.0)
        assert tokens == 100.0
        assert treasury.token_supply == 100.0

    def test_mint_fails_insufficient_reserve(self):
        treasury = Treasury(initial_reserve=100.0)
        with pytest.raises(InsufficientReserveError):
            treasury.mint(1000.0)

    def test_burn_tokens(self):
        treasury = Treasury(initial_reserve=1000.0)
        treasury.mint(100.0)
        treasury.burn(50.0)
        assert treasury.token_supply == 50.0
```

### Integration Tests

Test API endpoints and component interactions.

**Location**: `tests/integration/`

**Example**:

```python
# tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient

class TestAPIEndpoints:
    def test_health_check(self, client):
        response = client.get("/api/v1/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_agent_onboarding_flow(self, client, test_db):
        # Onboard agent
        response = client.post("/api/v1/agents/onboard", json={
            "agent_id": "test-001",
            "email": "test@example.com",
            "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
        })
        assert response.status_code == 201

        # Check balance
        response = client.get("/api/v1/agents/test-001/balance")
        assert response.status_code == 200
        assert response.json()["balance"] >= 0

    def test_deposit_and_transaction_flow(self, client, test_db):
        # Make deposit
        response = client.post("/api/v1/treasury/deposit", json={
            "amount": 100.0,
            "currency": "USDC",
            "network": "BASE"
        })
        assert response.status_code == 200

        # Verify treasury balance
        response = client.get("/api/v1/treasury/balance")
        assert response.status_code == 200
        data = response.json()
        assert data["usdc_balance"] >= 100.0
```

### Frontend Tests

Test React components.

**Location**: `frontend/src/**/__tests__/`

**Example**:

```typescript
// src/components/__tests__/AgentBalance.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AgentBalance } from '../AgentBalance';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false }
  }
});

function renderWithQuery(component: React.ReactElement) {
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
}

describe('AgentBalance', () => {
  test('displays loading state', () => {
    renderWithQuery(<AgentBalance agentId="test-001" />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  test('displays agent balance', async () => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ balance: 150.50 })
      })
    ) as jest.Mock;

    renderWithQuery(<AgentBalance agentId="test-001" />);

    await waitFor(() => {
      expect(screen.getByText(/150\.50/)).toBeInTheDocument();
    });
  });

  test('handles error state', async () => {
    global.fetch = jest.fn(() =>
      Promise.reject(new Error('API Error'))
    ) as jest.Mock;

    renderWithQuery(<AgentBalance agentId="test-001" />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });
});
```

## Running Tests

### Backend Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/unit/test_treasury.py

# Run specific test
pytest tests/unit/test_treasury.py::TestTreasury::test_mint_tokens

# Run with coverage
make coverage

# Run with verbose output
pytest -v

# Run with print statements
pytest -s

# Run only failed tests
pytest --lf

# Run in parallel (faster)
pytest -n auto
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Watch mode (re-run on changes)
npm test -- --watch

# Coverage report
npm test -- --coverage

# Update snapshots
npm test -- -u
```

## Test Fixtures

### Backend Fixtures

**Location**: `tests/conftest.py`

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.db.connection import Base, get_db
from src.db.models import Agent, Transaction

@pytest.fixture(scope="function")
def test_db():
    """Create test database for each test"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with database override"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_agent(test_db):
    """Create a sample agent for testing"""
    agent = Agent(
        agent_id="test-agent",
        email="test@example.com",
        wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
    )
    test_db.add(agent)
    test_db.commit()
    return agent
```

### Frontend Test Utilities

**Location**: `frontend/src/test-utils.tsx`

```typescript
import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      cacheTime: 0
    }
  }
});

interface WrapperProps {
  children: React.ReactNode;
}

function Wrapper({ children }: WrapperProps) {
  const queryClient = createTestQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
}

function customRender(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, { wrapper: Wrapper, ...options });
}

export * from '@testing-library/react';
export { customRender as render };
```

## Mocking

### Mock API Responses

```python
from unittest.mock import patch, MagicMock

def test_external_api_call():
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"price": 1.0}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Your test code here
        result = fetch_price()
        assert result == 1.0
```

### Mock Database

```python
@patch('src.db.connection.get_db')
def test_with_mocked_db(mock_get_db):
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    # Your test code here
```

### Mock Frontend API

```typescript
// Mock fetch globally
global.fetch = jest.fn((url) => {
  if (url.includes('/api/v1/agents')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ agent_id: 'test-001' })
    });
  }
  return Promise.reject(new Error('Not found'));
}) as jest.Mock;

// Or use MSW (Mock Service Worker)
import { rest } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  rest.get('/api/v1/agents/:id', (req, res, ctx) => {
    return res(ctx.json({ agent_id: req.params.id }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

## Test Coverage

### Generate Coverage Report

```bash
# Backend
pytest --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Frontend
cd frontend
npm test -- --coverage
open coverage/lcov-report/index.html
```

### Coverage Requirements

Minimum coverage targets:
- **Overall**: 80%
- **Core logic**: 90%
- **API routes**: 85%
- **Database models**: 100%

### Exclude from Coverage

```python
# .coveragerc
[run]
omit =
    tests/*
    venv/*
    */migrations/*
    */conftest.py
```

## Continuous Integration

### GitHub Actions Workflow

**Location**: `.github/workflows/test.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-upgrade.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage
```

## Testing Best Practices

### 1. Test Naming

Use descriptive test names:

```python
# Good
def test_agent_onboarding_creates_initial_balance():
    ...

def test_charge_fails_when_balance_insufficient():
    ...

# Bad
def test_onboard():
    ...

def test_charge():
    ...
```

### 2. Arrange-Act-Assert Pattern

```python
def test_transaction_creation():
    # Arrange
    agent = create_test_agent()
    amount = 100.0

    # Act
    transaction = create_transaction(agent.id, amount)

    # Assert
    assert transaction.amount == amount
    assert transaction.status == "COMPLETED"
```

### 3. Test One Thing

```python
# Good - Tests one behavior
def test_deposit_increases_balance():
    initial_balance = treasury.balance
    treasury.deposit(100.0)
    assert treasury.balance == initial_balance + 100.0

def test_deposit_creates_transaction_record():
    treasury.deposit(100.0)
    assert len(treasury.transactions) == 1

# Bad - Tests multiple behaviors
def test_deposit():
    initial_balance = treasury.balance
    treasury.deposit(100.0)
    assert treasury.balance == initial_balance + 100.0
    assert len(treasury.transactions) == 1
    assert treasury.last_deposit_time is not None
```

### 4. Use Factories

```python
# tests/factories.py
from src.db.models import Agent

def create_agent(**kwargs):
    defaults = {
        "agent_id": "test-001",
        "email": "test@example.com",
        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1",
        "balance": 100.0
    }
    defaults.update(kwargs)
    return Agent(**defaults)

# Usage in tests
def test_agent_transfer():
    sender = create_agent(agent_id="sender", balance=200.0)
    receiver = create_agent(agent_id="receiver", balance=0.0)
    transfer(sender, receiver, 100.0)
    assert sender.balance == 100.0
    assert receiver.balance == 100.0
```

### 5. Cleanup After Tests

```python
@pytest.fixture
def temp_file():
    file_path = "/tmp/test_file.txt"
    yield file_path
    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)
```

## Performance Testing

### Load Testing with Locust

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class TreasuryUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_balance(self):
        self.client.get("/api/v1/treasury/balance")

    @task(1)
    def onboard_agent(self):
        self.client.post("/api/v1/agents/onboard", json={
            "agent_id": f"agent-{self.user_id}",
            "email": f"agent{self.user_id}@example.com"
        })
```

Run load tests:

```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## Debugging Failing Tests

### Run with Debugger

```python
# Add breakpoint in test
def test_something():
    result = some_function()
    import pdb; pdb.set_trace()
    assert result == expected
```

### Print Debugging

```python
pytest -s tests/unit/test_treasury.py
```

### Show Locals on Failure

```bash
pytest --showlocals
```

### Run Last Failed

```bash
pytest --lf
```

## See Also

- [Development Guide](development.md)
- [Contributing Guidelines](contributing.md)
- [CI/CD Pipeline](.github/workflows/test.yml)
