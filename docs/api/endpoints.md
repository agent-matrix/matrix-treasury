# API Endpoints Reference

## Agent Lifecycle

### Onboard Agent

**Endpoint:** `POST /api/v1/agents/onboard`

**Description:** Register new agent and grant UBC

**Request:**
```json
{
    "agent_id": "agent_123",
    "agent_type": "agent",
    "metadata": {
        "capabilities": ["coding", "writing"]
    }
}
```

**Response:**
```json
{
    "status": "success",
    "agent_id": "agent_123",
    "ubc_granted": 500.0,
    "grant_type": "full",
    "balance": 500.0,
    "agent_status": "active"
}
```

**Errors:**
- `400` - Agent already exists
- `500` - Internal error

---

### Get Agent Details

**Endpoint:** `GET /api/v1/agents/{agent_id}`

**Response:**
```json
{
    "id": "agent_123",
    "agent_type": "agent",
    "balance": 1250.75,
    "reputation": 0.85,
    "status": "active",
    "ubc_renewals_used": 1,
    "last_activity": "2024-01-10T12:00:00Z",
    "created_at": "2024-01-01T00:00:00Z"
}
```

---

### Request UBC Renewal

**Endpoint:** `POST /api/v1/agents/ubc-renewal`

**Request:**
```json
{
    "agent_id": "agent_123"
}
```

**Response:**
```json
{
    "eligible": true,
    "status": "renewed",
    "amount": 200.0,
    "renewals_used": 2,
    "new_balance": 250.0
}
```

**Errors:**
- `400` - Not eligible (reason in response)

---

## Financial Operations

### Deposit USD

**Endpoint:** `POST /api/v1/deposits`

**Description:** Convert USD to MXU

**Request:**
```json
{
    "user_id": "user_456",
    "amount_usd": 100.0
}
```

**Response:**
```json
{
    "status": "success",
    "usd_deposited": 100.0,
    "mxu_received": 70000.0,
    "commons_contribution": 30000.0,
    "exchange_rate": 1000.0,
    "new_balance": 70000.0
}
```

---

### Charge Agent for Work

**Endpoint:** `POST /api/v1/billing/charge`

**Auth:** Guardian API key required

**Request:**
```json
{
    "agent_id": "agent_123",
    "metering": {
        "metering_source": "GUARDIAN",
        "timestamp": "2024-01-10T12:00:00Z",
        "gpu_seconds": 3600.0,
        "avg_watts": 450.0,
        "ram_gb_seconds": 57600.0,
        "bandwidth_mb": 100.0
    }
}
```

**Response:**
```json
{
    "status": "success",
    "billed": 1800.0,
    "breakdown": {
        "total_mxu": 1800.0,
        "components": {
            "energy_mxu": 450.0,
            "capacity_mxu": 450.0,
            "state_mxu": 1.15,
            "governance_mxu": 18.02
        }
    },
    "new_balance": 850.0,
    "agent_status": "active"
}
```

**Errors:**
- `402` - Insufficient funds (bankruptcy)
- `400` - Invalid metering data

---

### Execute Transaction

**Endpoint:** `POST /api/v1/transactions`

**Description:** Transfer MXU between agents

**Request:**
```json
{
    "from_id": "client_456",
    "to_id": "agent_123",
    "amount_mxu": 100.0,
    "quality_score": 0.95,
    "description": "Payment for code review"
}
```

**Response:**
```json
{
    "status": "success",
    "gross": 100.0,
    "tax": 2.0,
    "tax_rate": 0.02,
    "net": 98.0,
    "agent_new_balance": 1000.0,
    "agent_reputation": 0.87
}
```

---

## Monitoring & Metrics

### Get Treasury Metrics

**Endpoint:** `GET /api/v1/metrics`

**Response:**
```json
{
    "supply": 5000000.0,
    "reserves": 5500.0,
    "pools": {
        "infrastructure": 150000.0,
        "ubc": 100000.0,
        "emergency": 50000.0
    },
    "price_usd": 0.0011,
    "mxu_per_usd": 909.09,
    "crisis_mode": false,
    "total_transactions": 15234,
    "total_burned": 2500000.0,
    "total_minted": 7500000.0
}
```

---

### Get Economic Metrics

**Endpoint:** `GET /api/v1/economy/metrics`

**Response:**
```json
{
    "total_agents": 150,
    "active_agents": 120,
    "idle_agents": 30,
    "unemployment_rate": 0.20,
    "velocity": 0.0305,
    "concentration": 0.03,
    "avg_reputation": 0.75,
    "status_distribution": {
        "active": 120,
        "throttled": 10,
        "hibernated": 20
    }
}
```

---

### Get Reserve Health

**Endpoint:** `GET /api/v1/health/reserves`

**Response:**
```json
{
    "reserve_usd": 5500.0,
    "coverage_ratio": 1.83,
    "coverage_days": 25.7,
    "crisis_mode": false,
    "daily_cost_usd": 214.29,
    "target_usd": 3000.0
}
```

---

### Cost Estimation

**Endpoint:** `POST /api/v1/estimate-cost`

**Description:** Estimate cost without guardian signature

**Request:**
```json
{
    "gpu_hours": 1.0,
    "ram_gb_hours": 16.0,
    "storage_gb_days": 1.0
}
```

**Response:**
```json
{
    "estimated_mxu": 902.38,
    "estimated_usd": 0.99,
    "warning": "This is an estimate only..."
}
```

---

## Governance

### Run Stabilizer

**Endpoint:** `POST /api/v1/governance/stabilize`

**Auth:** Admin only

**Response:**
```json
{
    "health": {
        "reserve_usd": 5500.0,
        "coverage_ratio": 1.83,
        "crisis_mode": false
    },
    "metrics": {
        "unemployment_rate": 0.20,
        "velocity": 0.0305
    },
    "actions": [
        {
            "type": "STIMULUS",
            "reason": "Unemployment at 20.0%",
            "amount": 5000.0,
            "beneficiaries": 30
        }
    ],
    "timestamp": "2024-01-10T12:00:00Z"
}
```

---

## WebSocket Endpoints

### Real-time Metrics Stream

**Endpoint:** `WS /api/v1/ws/metrics`

**Messages:**
```json
{
    "type": "metrics_update",
    "data": {
        "treasury": {...},
        "metrics": {...}
    },
    "timestamp": "2024-01-10T12:00:00Z"
}
```

**Frequency:** Every 5 seconds
