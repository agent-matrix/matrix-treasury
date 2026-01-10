# Data Model

## Entity-Relationship Diagram

```
┌──────────────┐
│    Agent     │
├──────────────┤
│ id (PK)      │
│ agent_type   │
│ balance      │
│ reputation   │
│ status       │
│ ubc_renewals │
└──────┬───────┘
       │
       │ 1:N
       │
       ▼
┌──────────────────┐         ┌─────────────────┐
│  Transaction     │         │ BillingRecord   │
├──────────────────┤         ├─────────────────┤
│ id (PK)          │         │ id (PK)         │
│ from_agent_id(FK)│         │ agent_id (FK)   │
│ to_agent_id (FK) │         │ total_mxu       │
│ transaction_type │         │ energy_mxu      │
│ gross_amount     │         │ capacity_mxu    │
│ tax_amount       │         │ state_mxu       │
│ net_amount       │         │ governance_mxu  │
└──────────────────┘         └─────────────────┘

┌──────────────────────┐    ┌─────────────────────┐
│  TreasurySnapshot    │    │  StabilizerAction   │
├──────────────────────┤    ├─────────────────────┤
│ id (PK)              │    │ id (PK)             │
│ reserve_usd          │    │ action_type         │
│ mxu_supply           │    │ reason              │
│ infrastructure_pool  │    │ amount_mxu          │
│ ubc_pool             │    │ beneficiary_count   │
│ emergency_pool       │    │ unemployment_rate   │
│ coverage_ratio       │    │ coverage_ratio      │
└──────────────────────┘    └─────────────────────┘
```

## Core Entities

### Agent
**Purpose:** Represents any participant (agent, human, service)

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier |
| agent_type | enum | agent, human, service |
| balance | float | Current MXU balance |
| reputation | float | Quality score (0.0-1.0) |
| status | enum | active, throttled, hibernated |
| ubc_renewals_used | int | Number of UBC renewals |
| last_ubc_renewal | timestamp | Last renewal time |
| last_activity | timestamp | Last transaction/work |
| created_at | timestamp | Registration time |
| flags | json | Set of behavioral flags |

**Indexes:**
- Primary: `id`
- Secondary: `status`, `agent_type`, `last_activity`

**Constraints:**
- balance ≥ 0
- reputation ∈ [0.0, 1.0]
- ubc_renewals_used ≤ 3

### Transaction
**Purpose:** Record all MXU movements

| Field | Type | Description |
|-------|------|-------------|
| id | string | Transaction ID |
| transaction_type | enum | deposit, payment, tax, etc. |
| from_agent_id | string (FK) | Sender (nullable) |
| to_agent_id | string (FK) | Receiver (nullable) |
| gross_amount | float | Amount before tax |
| tax_amount | float | Tax collected |
| net_amount | float | Amount after tax |
| tax_rate | float | Applied tax rate |
| description | text | Human-readable description |
| created_at | timestamp | Transaction time |

**Indexes:**
- Primary: `id`
- Secondary: `from_agent_id`, `to_agent_id`, `transaction_type`, `created_at`

**Transaction Types:**
- `deposit`: USD → MXU
- `payment`: Agent → Agent
- `charge`: Work billing
- `ubc_grant`: Initial UBC
- `ubc_renewal`: UBC top-up
- `stimulus`: Stabilizer action
- `tax`: Tax collection

### BillingRecord
**Purpose:** Detailed resource usage and billing

| Field | Type | Description |
|-------|------|-------------|
| id | string | Billing record ID |
| agent_id | string (FK) | Billed agent |
| total_mxu | float | Total bill |
| energy_mxu | float | Energy component |
| capacity_mxu | float | Capacity component |
| state_mxu | float | State component |
| governance_mxu | float | Governance component |
| gpu_seconds | float | GPU time used |
| cpu_seconds | float | CPU time used |
| ram_gb_seconds | float | RAM usage |
| bandwidth_mb | float | Network usage |
| storage_gb_days | float | Storage usage |
| metering_source | string | Guardian identifier |
| metering_timestamp | timestamp | When metered |
| paid | boolean | Payment status |

**Indexes:**
- Primary: `id`
- Secondary: `agent_id`, `created_at`, `paid`

### TreasurySnapshot
**Purpose:** Time-series data for analytics

| Field | Type | Description |
|-------|------|-------------|
| id | serial | Auto-increment ID |
| reserve_usd | float | USD reserves |
| mxu_supply | float | Total MXU supply |
| infrastructure_pool | float | Infrastructure pool |
| ubc_pool | float | UBC pool |
| emergency_pool | float | Emergency pool |
| usd_per_mxu | float | Exchange rate |
| coverage_ratio | float | Reserve health |
| total_transactions | int | Cumulative transactions |
| total_mxu_burned | float | Cumulative burns |
| snapshot_at | timestamp | Snapshot time |

**Frequency:** Every 5 minutes

**Retention:** 
- 1-minute granularity: 24 hours
- 5-minute granularity: 30 days
- 1-hour granularity: 1 year
- 1-day granularity: Forever

### StabilizerAction
**Purpose:** Log automatic interventions

| Field | Type | Description |
|-------|------|-------------|
| id | serial | Auto-increment ID |
| action_type | string | AUSTERITY, STIMULUS, LIQUIDITY |
| reason | text | Why triggered |
| amount_mxu | float | MXU involved (nullable) |
| beneficiary_count | int | Agents affected |
| unemployment_rate | float | Rate at trigger time |
| coverage_ratio | float | Coverage at trigger time |
| metadata | json | Additional context |
| created_at | timestamp | Action time |

## State Management

### In-Memory (Redis)
**Purpose:** Hot data, fast access

```python
# Agent balances (TTL: 5 minutes)
agent:{id}:balance → float

# Exchange rate cache (TTL: 1 minute)
treasury:exchange_rate → float

# Recent transactions (sorted set)
agent:{id}:recent_tx → [(timestamp, tx_id), ...]

# Active sessions
session:{token} → {user_id, expires_at}
```

### Persistent (PostgreSQL)
**Purpose:** Source of truth

All entities above are persisted to PostgreSQL with:
- ACID transactions
- Row-level locking for balance updates
- Foreign key constraints
- Check constraints for invariants

## Data Access Patterns

### High-Frequency Reads
- Balance queries: Redis → PostgreSQL fallback
- Exchange rate: Redis cache (1 min TTL)
- Agent status: Redis cache (5 min TTL)

### High-Frequency Writes
- Transaction logs: Batch inserts (100/sec)
- Billing records: Async queue processing
- Balance updates: Optimistic locking

### Analytics Queries
- Time-series: TreasurySnapshot table
- Reports: Read replicas
- Aggregations: Materialized views

## Backup Strategy

### Hot Backups
- PostgreSQL: Continuous WAL archiving
- Redis: RDB snapshots every 5 minutes

### Cold Backups
- Daily full backup to S3
- 30-day retention
- Glacier archive after 30 days

### Recovery Procedures
1. Stop application
2. Restore PostgreSQL from latest backup
3. Replay WAL to target time
4. Verify data integrity
5. Restart application
