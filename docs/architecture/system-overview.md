# System Architecture Overview

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent-Matrix Ecosystem                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────┐                   │
│  │ Matrix Hub   │◄────►│ Agent Runtime│                   │
│  │ (Orchestrate)│      │  (Execute)   │                   │
│  └──────┬───────┘      └──────┬───────┘                   │
│         │                     │                            │
│         │    ┌────────────────▼─────────┐                 │
│         └───►│  Matrix Treasury (This)  │                 │
│              │   Economic Engine        │                 │
│              └────────────┬─────────────┘                 │
│                           │                                │
│              ┌────────────▼──────────────┐                │
│              │  Persistent Storage       │                │
│              │  (PostgreSQL + Redis)     │                │
│              └───────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Treasury (Central Bank)
**Location:** `src/core/treasury.py`

Responsibilities:
- MXU minting & burning
- Price calculation (USD/MXU)
- Reserve management
- Tax collection
- Health monitoring

### 2. Economy (Society Layer)
**Location:** `src/core/economy.py`

Responsibilities:
- Agent lifecycle management
- Wallet operations
- UBC grants & renewals
- Transaction processing
- Automatic stabilizers

### 3. Metering System
**Location:** `src/core/metering.py`

Responsibilities:
- Resource usage measurement
- Billing calculation
- Four-part tariff application
- Validation & authorization

### 4. API Layer
**Location:** `src/api/`

Responsibilities:
- RESTful endpoints
- WebSocket streams
- Request validation
- Authentication & authorization
- Rate limiting

### 5. Database Layer
**Location:** `src/db/`

Responsibilities:
- Persistent storage (PostgreSQL)
- Caching (Redis)
- Transaction history
- Agent state
- Audit logs

## Data Flow

### Minting Flow (Outer Loop)
```
Human deposits USD
    ↓
Treasury calculates exchange rate
    ↓
Mint MXU (70% to user, 30% to commons)
    ↓
Update reserves & supply
    ↓
Return MXU to user wallet
```

### Billing Flow (Inner Loop)
```
Agent performs work
    ↓
Guardian emits metering event
    ↓
Metering system calculates bill
    ↓
Debit agent wallet
    ↓
Burn MXU from supply
    ↓
Reduce reserves by USD equivalent
```

### Payment Flow
```
Client pays agent
    ↓
Calculate progressive tax
    ↓
Debit client wallet (gross)
    ↓
Allocate tax to pools
    ↓
Credit agent wallet (net)
    ↓
Update reputation
```

## Scalability Considerations

### Horizontal Scaling
- API layer: Multiple instances behind load balancer
- Workers: Separate processes for stabilizers
- Database: Read replicas for queries

### Caching Strategy
- Redis for: Exchange rates, agent balances, recent transactions
- Cache invalidation: Event-driven updates
- TTL: 60 seconds for prices, 300 seconds for balances

### Performance Targets
- API latency: p99 < 100ms
- Transaction throughput: 1000+ TPS
- WebSocket concurrent connections: 10,000+

## Security Layers

1. **Network**: HTTPS/TLS, VPC isolation
2. **Application**: JWT auth, rate limiting, input validation
3. **Database**: Connection pooling, prepared statements
4. **Infrastructure**: Container security, secrets management

## Monitoring & Observability

- **Metrics**: Prometheus (reserves, supply, rates)
- **Logs**: Structured JSON logging
- **Tracing**: OpenTelemetry (optional)
- **Dashboards**: Grafana
- **Alerts**: Prometheus Alertmanager

## Disaster Recovery

- **Database Backups**: Hourly incremental, daily full
- **Recovery Time Objective (RTO)**: 15 minutes
- **Recovery Point Objective (RPO)**: 1 hour
- **Backup Storage**: S3 + Glacier

## Integration Points

### Matrix Hub
- Endpoint: POST `/api/v1/billing/charge`
- Auth: Service account JWT
- Purpose: Bill agents for work

### Agent Runtime
- Endpoint: GET `/api/v1/agents/{id}`
- Auth: Agent JWT
- Purpose: Check balance

### Matrix Router
- Endpoint: WS `/api/v1/ws/metrics`
- Auth: API key
- Purpose: Real-time updates
