# API Reference - Phase 3 Enterprise Edition

Complete API documentation for Matrix Treasury enterprise features.

---

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Most endpoints require admin authentication. Set the `Authorization` header:

```bash
Authorization: Bearer YOUR_API_KEY
```

---

## Multi-Currency Endpoints

### Get Multi-Currency Balances

Get balances for all supported currencies across networks.

**Endpoint**: `GET /multicurrency/balances`

**Response**:
```json
{
  "USDC": 5432.50,
  "EUR": 3200.00,
  "BTC": 0.125,
  "total_usd_equivalent": 11150.00,
  "network": "base"
}
```

**Example**:
```bash
curl http://localhost:8000/api/v1/multicurrency/balances
```

---

### Multi-Currency Withdrawal

Withdraw funds in specific currency via crypto or wire transfer.

**Endpoint**: `POST /multicurrency/withdraw`

**Request Body**:
```json
{
  "amount": 1000.50,
  "currency": "USDC",
  "network": "base",
  "destination": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "method": "crypto"
}
```

**Parameters**:
- `amount` (float, required): Amount to withdraw
- `currency` (string, required): USDC, EUR, or BTC
- `network` (string, required): base, polygon, arbitrum, optimism
- `destination` (string, required): Wallet address or bank account ID
- `method` (string, required): "crypto" or "wire"

**Response**:
```json
{
  "status": "success",
  "amount": 1000.50,
  "currency": "USDC",
  "network": "base",
  "method": "crypto",
  "destination": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "tx_hash": "0xabcdef1234567890..."
}
```

---

## Analytics Endpoints

### Get Analytics Dashboard

Real-time analytics for Mission Control dashboard.

**Endpoint**: `GET /analytics/dashboard`

**Response**:
```json
{
  "total_transactions": 1247,
  "total_volume": 45320.50,
  "active_agents": 23,
  "system_health": {
    "status": "healthy",
    "solvency_ratio": 1.23,
    "runway_days": 43
  },
  "hourly_volume": [
    {"hour": "00:00", "volume": 1200.0},
    {"hour": "01:00", "volume": 1500.0}
  ],
  "top_agents": [
    {
      "agent_id": "agent_1",
      "earned": 5000.0,
      "credit_score": 0.95
    }
  ]
}
```

---

### Get Agent Analytics

Detailed analytics for specific agent.

**Endpoint**: `GET /analytics/agent/{agent_id}`

**Parameters**:
- `agent_id` (string, path): Agent identifier

**Response**:
```json
{
  "agent_id": "agent_007",
  "total_earned": 5000.0,
  "total_spent": 3200.0,
  "current_balance": 1800.0,
  "credit_score": 0.85,
  "transaction_count": 150,
  "active_loans": 1,
  "total_debt": 500.0,
  "sybil_risk_score": 0.15
}
```

**Example**:
```bash
curl http://localhost:8000/api/v1/analytics/agent/agent_007
```

---

## Security Endpoints

### Check Sybil Attack

Analyze agent for fraudulent behavior patterns.

**Endpoint**: `GET /security/sybil/{agent_id}`

**Parameters**:
- `agent_id` (string, path): Agent to analyze

**Response**:
```json
{
  "agent_id": "agent_123",
  "is_suspicious": false,
  "risk_score": 0.15,
  "flags": [],
  "profile": {
    "account_age_hours": 120.5,
    "transaction_count": 150,
    "transaction_velocity": 1.25,
    "credit_score_volatility": 0.05
  }
}
```

**Risk Score Interpretation**:
- 0.0 - 0.3: Low risk
- 0.3 - 0.5: Medium risk
- 0.5 - 0.7: High risk
- 0.7 - 1.0: Critical risk

---

### Get Flagged Agents

List all agents flagged as suspicious.

**Endpoint**: `GET /security/flagged`

**Response**:
```json
{
  "flagged_agents": [
    {
      "agent_id": "agent_456",
      "risk_score": 0.75,
      "flags": [
        "High transaction velocity: 150.5 tx/hour",
        "Shared IP with 8 other agents"
      ]
    }
  ],
  "total_flagged": 1,
  "detection_stats": {
    "total_agents_tracked": 100,
    "flagged_percentage": 1.0,
    "detected_clusters": 0
  }
}
```

---

## Credit System Endpoints

### Request Loan

Request a collateral-backed loan.

**Endpoint**: `POST /credit/request-loan`

**Request Body**:
```json
{
  "agent_id": "agent_007",
  "amount": 1000.0,
  "collateral": 1500.0,
  "loan_term_days": 30
}
```

**Parameters**:
- `agent_id` (string, required): Agent requesting loan
- `amount` (float, required): Amount to borrow in MXU
- `collateral` (float, required): Collateral amount in MXU (must be ≥150% of amount)
- `loan_term_days` (int, optional): Loan term in days (default: 30)

**Response (Approved)**:
```json
{
  "approved": true,
  "loan_id": "LOAN-000123",
  "principal": 1000.0,
  "collateral": 1500.0,
  "interest_rate": 0.10,
  "due_date": "2024-02-10T00:00:00",
  "total_due": 1025.0
}
```

**Response (Rejected)**:
```json
{
  "approved": false,
  "reason": "Credit score too low: 0.45 < 0.5",
  "credit_limit": 0.0
}
```

---

### Repay Loan

Make payment on active loan.

**Endpoint**: `POST /credit/repay-loan`

**Request Body**:
```json
{
  "agent_id": "agent_007",
  "loan_id": "LOAN-000123",
  "amount": 500.0
}
```

**Response (Partial)**:
```json
{
  "status": "partial_repayment",
  "loan_id": "LOAN-000123",
  "amount_paid": 500.0,
  "total_repaid": 500.0,
  "remaining": 525.0
}
```

**Response (Full)**:
```json
{
  "status": "fully_repaid",
  "loan_id": "LOAN-000123",
  "amount_paid": 525.0,
  "total_repaid": 1025.0,
  "collateral_returned": 1500.0,
  "overpayment": 0.0
}
```

---

### Get Agent Loans

Retrieve all loans for specific agent.

**Endpoint**: `GET /credit/agent-loans/{agent_id}`

**Response**:
```json
{
  "agent_id": "agent_007",
  "active_loans": [
    {
      "loan_id": "LOAN-000123",
      "principal": 1000.0,
      "collateral": 1500.0,
      "interest_rate": 0.10,
      "issued_at": "2024-01-10T12:00:00",
      "due_date": "2024-02-10T12:00:00",
      "total_due": 1025.0,
      "repaid": 500.0,
      "status": "active"
    }
  ],
  "total_debt": 525.0,
  "credit_limit": 2000.0
}
```

---

### Credit System Stats

Get overall credit system statistics.

**Endpoint**: `GET /credit/system-stats`

**Response**:
```json
{
  "total_loans": 45,
  "active_loans": 12,
  "total_principal": 25000.0,
  "total_collateral": 37500.0,
  "collateralization_ratio": 1.5
}
```

---

## Admin Endpoints

### Add Bank Account

Configure bank account for wire transfers (admin only).

**Endpoint**: `POST /admin/add-bank-account`

**Request Body**:
```json
{
  "account_id": "admin_bank_usd",
  "account_name": "Matrix Treasury LLC",
  "account_number": "1234567890",
  "routing_number": "021000021",
  "swift_code": "CHASUS33",
  "bank_name": "JPMorgan Chase Bank",
  "bank_address": "270 Park Ave, New York, NY",
  "currency": "USD",
  "country": "US"
}
```

**Response**:
```json
{
  "status": "success",
  "account_id": "admin_bank_usd",
  "bank_name": "JPMorgan Chase Bank",
  "currency": "USD"
}
```

**Note**: Sensitive fields (account_number, routing_number, swift_code) are encrypted before storage.

---

### Add Crypto Wallet

Configure crypto wallet for withdrawals (admin only).

**Endpoint**: `POST /admin/add-crypto-wallet`

**Request Body**:
```json
{
  "wallet_id": "admin_wallet_base",
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "network": "base",
  "currency": "USDC",
  "label": "Admin Cold Wallet"
}
```

**Response**:
```json
{
  "status": "success",
  "wallet_id": "admin_wallet_base",
  "network": "base",
  "currency": "USDC"
}
```

---

### Get Payment Methods

List all configured payment methods (masked).

**Endpoint**: `GET /admin/payment-methods`

**Response**:
```json
{
  "bank_accounts": [
    {
      "account_id": "admin_bank_usd",
      "account_name": "Matrix Treasury LLC",
      "account_number": "****7890",
      "routing_number": "****",
      "swift_code": "****",
      "bank_name": "JPMorgan Chase Bank",
      "currency": "USD"
    }
  ],
  "crypto_wallets": [
    {
      "wallet_id": "admin_wallet_base",
      "address": "0x742d...9A23",
      "network": "base",
      "currency": "USDC",
      "label": "Admin Cold Wallet"
    }
  ]
}
```

---

## Treasury Status Endpoints

### Get Treasury Status

Current vault balance and health metrics.

**Endpoint**: `GET /treasury/status`

**Response**:
```json
{
  "usdc_balance": 5432.50,
  "mxu_supply": 100000.0,
  "coverage_ratio": 1.23,
  "runway_days": 43,
  "health_status": "HEALTHY"
}
```

**Health Status Values**:
- `HEALTHY`: Solvency ratio ≥ 1.5
- `WARNING`: Solvency ratio 1.0 - 1.5
- `CRITICAL`: Solvency ratio < 1.0

---

### Get Network Health

Akash network and compute status.

**Endpoint**: `GET /network/health`

**Response**:
```json
{
  "akash_nodes_active": 12,
  "akash_nodes_total": 15,
  "compute_load_percent": 64.0,
  "infrastructure_health": "HEALTHY"
}
```

---

## Governance Endpoints

### Get Pending Approvals

List transactions awaiting manual approval.

**Endpoint**: `GET /governance/pending`

**Response**:
```json
[
  {
    "id": 1,
    "agent_id": "agent_007",
    "action": "Infrastructure payment",
    "cost_usd": 150.0,
    "reason": "Akash lease renewal",
    "submitted_at": "2024-01-10T12:00:00"
  }
]
```

---

### Approve Transaction

Approve a pending transaction.

**Endpoint**: `POST /governance/approve/{transaction_id}`

**Response**:
```json
{
  "status": "success",
  "transaction_id": 1,
  "approved": true
}
```

---

### Deny Transaction

Reject a pending transaction.

**Endpoint**: `POST /governance/deny/{transaction_id}`

**Response**:
```json
{
  "status": "success",
  "transaction_id": 1,
  "approved": false
}
```

---

### Toggle Autopilot

Enable/disable CFO autonomy.

**Endpoint**: `POST /governance/autopilot`

**Request Body**:
```json
{
  "enabled": true
}
```

**Response**:
```json
{
  "status": "success",
  "autopilot": true,
  "message": "CFO autopilot enabled"
}
```

---

## Error Responses

All endpoints return standard error format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**HTTP Status Codes**:
- `200`: Success
- `400`: Bad request (invalid parameters)
- `401`: Unauthorized (missing/invalid auth)
- `403`: Forbidden (insufficient permissions)
- `404`: Not found
- `500`: Internal server error

---

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Standard endpoints**: 100 requests/minute
- **Analytics endpoints**: 30 requests/minute
- **Admin endpoints**: 10 requests/minute

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704902400
```

---

## WebSocket Endpoints

### Real-Time Transaction Stream

Connect to live transaction feed.

**Endpoint**: `WS /ws/logs`

**Message Format**:
```json
{
  "id": 1234,
  "time": "2024-01-10T12:30:45",
  "agent": "agent_007",
  "action": "Task completion",
  "cost": 50.0,
  "type": "INCOME",
  "status": "APPROVED"
}
```

**Example (JavaScript)**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/logs');

ws.onmessage = (event) => {
  const transaction = JSON.parse(event.data);
  console.log('New transaction:', transaction);
};
```

---

## SDK Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Get analytics
response = requests.get(f"{BASE_URL}/analytics/dashboard")
analytics = response.json()
print(f"Active agents: {analytics['active_agents']}")

# Request loan
loan_request = {
    "agent_id": "agent_007",
    "amount": 1000.0,
    "collateral": 1500.0,
    "loan_term_days": 30
}
response = requests.post(f"{BASE_URL}/credit/request-loan", json=loan_request)
result = response.json()

if result["approved"]:
    print(f"Loan approved: {result['loan_id']}")
```

### JavaScript

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

// Get multi-currency balances
fetch(`${BASE_URL}/multicurrency/balances`)
  .then(res => res.json())
  .then(data => {
    console.log('USDC:', data.USDC);
    console.log('Total USD:', data.total_usd_equivalent);
  });

// Check sybil risk
fetch(`${BASE_URL}/security/sybil/agent_123`)
  .then(res => res.json())
  .then(data => {
    if (data.is_suspicious) {
      console.warn('Suspicious agent detected!');
      console.log('Risk score:', data.risk_score);
    }
  });
```

---

## Interactive Documentation

Full interactive API documentation available at:

**Swagger UI**: http://localhost:8000/docs
**ReDoc**: http://localhost:8000/redoc
