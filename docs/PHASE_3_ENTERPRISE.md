# Phase 3: Enterprise Features Documentation

## Overview

Phase 3 transforms Matrix Treasury into an enterprise-ready platform with multi-currency support, advanced security, real-time analytics, and agent credit systems.

---

## Multi-Currency Treasury

### Supported Assets

The platform now supports three currencies across four blockchain networks:

| Currency | Symbol | Decimals | Networks |
|----------|--------|----------|----------|
| USD Coin | USDC | 6 | Base, Polygon, Arbitrum, Optimism |
| Euro Stablecoin | EURe | 18 | Base, Polygon, Arbitrum, Optimism |
| Wrapped Bitcoin | WBTC/cbBTC | 8 | Base, Polygon, Arbitrum |

### Network Details

**Base (Coinbase L2)**
- Chain ID: 8453
- RPC: https://mainnet.base.org
- Lowest gas fees, best for frequent operations

**Polygon**
- Chain ID: 137
- RPC: https://polygon-rpc.com
- High throughput, established ecosystem

**Arbitrum**
- Chain ID: 42161
- RPC: https://arb1.arbitrum.io/rpc
- Optimistic rollup with low costs

**Optimism**
- Chain ID: 10
- RPC: https://mainnet.optimism.io
- Optimistic rollup, EVM compatible

### Currency Conversion

Real-time exchange rates are provided through the `CurrencyConverter` class:

```python
from src.blockchain.multi_currency_vault import CurrencyConverter, Currency

# Get exchange rate
rate = CurrencyConverter.get_exchange_rate(Currency.EUR, Currency.USDC)
# Returns: Decimal("1.08") - 1 EUR = 1.08 USD

# Convert amount
usd_amount = CurrencyConverter.convert(
    amount=Decimal("1000"),
    from_currency=Currency.EUR,
    to_currency=Currency.USDC
)
# Returns: Decimal("1080.0")
```

### Multi-Currency Vault Usage

```python
from src.blockchain.multi_currency_vault import MultiCurrencyVault, Network, Currency

# Initialize vault
vault = MultiCurrencyVault(
    network=Network.BASE,
    private_key="your_private_key"
)

# Check balances
balances = vault.get_all_balances()
# Returns: {"USDC": Decimal("5432.50"), "EUR": Decimal("3200.00"), "BTC": Decimal("0.125")}

# Transfer currency
result = vault.transfer(
    to_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    amount=Decimal("100.50"),
    currency=Currency.USDC,
    memo="Admin withdrawal"
)
```

---

## Agent Credit System

### Overview

Agents can borrow MXU (internal credits) against collateral with automatic risk management and liquidation.

### Key Features

- **Overcollateralized Loans**: 150% minimum collateral required
- **Credit Score-Based Rates**: 5-20% APR based on agent performance
- **Automatic Liquidation**: Loans liquidated at 75% LTV
- **Flexible Terms**: 7-90 day repayment periods
- **Credit Limits**: Based on earning history and credit score

### Credit Score Requirements

| Credit Score | Interest Rate | Max Loan Term |
|--------------|---------------|---------------|
| 0.9 - 1.0 | 5% APR | 90 days |
| 0.8 - 0.9 | 8% APR | 60 days |
| 0.7 - 0.8 | 12% APR | 45 days |
| 0.6 - 0.7 | 15% APR | 30 days |
| 0.5 - 0.6 | 20% APR | 14 days |
| < 0.5 | Not eligible | - |

### Usage Example

```python
from src.core.credit_system import AgentCreditSystem
from decimal import Decimal

credit_system = AgentCreditSystem()

# Request loan
result = credit_system.request_loan(
    agent_id="agent_007",
    amount=Decimal("1000.0"),      # MXU to borrow
    collateral=Decimal("1500.0"),  # 150% collateral
    credit_score=Decimal("0.85"),   # Agent's credit score
    total_earned=Decimal("5000.0"), # Historical earnings
    loan_term_days=30
)

# Check result
if result["approved"]:
    print(f"Loan approved: {result['loan_id']}")
    print(f"Interest rate: {result['interest_rate'] * 100}%")
    print(f"Total due: {result['total_due']} MXU")
else:
    print(f"Loan rejected: {result['reason']}")

# Repay loan
repayment = credit_system.repay_loan(
    agent_id="agent_007",
    loan_id=result["loan_id"],
    amount=Decimal("500.0")  # Partial payment
)

# Check liquidations
liquidations = credit_system.check_liquidations()
for liquidation in liquidations:
    print(f"Liquidated: {liquidation['loan_id']}, seized: {liquidation['collateral_seized']}")
```

### Credit Limit Calculation

```
credit_limit = (total_earned * 0.5) * credit_score

Example:
- Agent earned 10,000 MXU total
- Credit score: 0.8
- Credit limit = (10,000 * 0.5) * 0.8 = 4,000 MXU
```

---

## ML-Based Sybil Detection

### Detection Mechanisms

The system uses behavioral analysis to detect fraudulent agents and coordinated attacks.

#### 1. Transaction Velocity Analysis
Flags agents with bot-like transaction rates:
- Threshold: 100 transactions/hour
- Detection: Measures time between transactions
- Action: Automatic flagging at high velocity

#### 2. Credit Score Volatility
Detects manipulation attempts:
- Threshold: 0.3 standard deviation
- Detection: Tracks score changes over time
- Action: Flags unusual patterns

#### 3. New Account Abuse
Identifies suspicious new accounts:
- Threshold: Activity within 5 minutes of creation
- Detection: Monitors account age vs activity
- Action: Flags immediate high-value transactions

#### 4. IP/Device Clustering
Identifies sybil networks:
- Detection: Tracks shared IPs and devices
- Threshold: 5+ agents sharing resources
- Action: Flags entire cluster

#### 5. Bankruptcy Pattern Recognition
Detects abuse through repeated bankruptcies:
- Threshold: 2+ bankruptcies
- Detection: Tracks bankruptcy events
- Action: Permanent flag

#### 6. Spending/Earning Ratio
Identifies drain attacks:
- Threshold: Spending > 2x earning
- Detection: Compares total spent to earned
- Action: Flags suspicious ratios

### Usage Example

```python
from src.security.sybil_detection import SybilDetector

detector = SybilDetector()

# Track agent activity
detector.track_agent(
    agent_id="agent_123",
    transaction_amount=Decimal("50.0"),
    credit_score=Decimal("0.75"),
    ip_address="192.168.1.100",
    device_fingerprint="device_abc123"
)

# Check for sybil attack
result = detector.detect_sybil_attack("agent_123")

if result["is_suspicious"]:
    print(f"⚠️ Suspicious agent detected!")
    print(f"Risk score: {result['risk_score']}")
    print(f"Flags: {', '.join(result['flags'])}")

    # Review profile
    profile = result["profile"]
    print(f"Account age: {profile['account_age_hours']} hours")
    print(f"Velocity: {profile['transaction_velocity']} tx/hour")

# Detect clusters
clusters = detector.detect_sybil_cluster()
for cluster in clusters:
    print(f"Cluster detected: {len(cluster)} related agents")
    print(f"Agents: {cluster}")

# Get flagged agents
flagged = detector.get_flagged_agents()
print(f"Total flagged: {len(flagged)}")
```

---

## Real-Time Analytics

### Analytics Engine

Tracks all system metrics in real-time for monitoring and predictive analysis.

#### Features

- **Transaction Aggregation**: All transactions tracked and indexed
- **Hourly/Daily Metrics**: Volume tracking by time period
- **Agent Performance**: Individual and aggregate statistics
- **Runway Calculations**: Predictive treasury health
- **Burn Rate Analysis**: Spending patterns and forecasts

### Usage Example

```python
from src.analytics.realtime_analytics import RealTimeAnalytics
from decimal import Decimal

analytics = RealTimeAnalytics()

# Record transaction
analytics.record_transaction(
    agent_id="agent_007",
    amount=Decimal("150.0"),
    transaction_type="credit",
    reason="Task completion reward",
    balance_after=Decimal("1250.0")
)

# Get recent transactions
recent = analytics.get_recent_transactions(limit=50)
for tx in recent:
    print(f"{tx['timestamp']}: {tx['agent_id']} - {tx['amount']} MXU")

# Calculate runway
runway = analytics.calculate_runway(
    current_balance=Decimal("50000.0"),
    time_window_hours=24
)
print(f"Runway: {runway['runway_days']} days")
print(f"Burn rate: ${runway['burn_rate_per_day']}/day")

# Get dashboard metrics
metrics = analytics.get_dashboard_metrics(
    treasury_balance=Decimal("50000.0"),
    total_agent_balances=Decimal("35000.0")
)

# System health
health = metrics["system_health"]
print(f"Status: {health['status']}")
print(f"Solvency: {health['solvency_ratio']}")
print(f"Active agents: {health['active_agents_today']}")

# Top performers
top_agents = metrics["top_agents"]
for agent in top_agents:
    print(f"{agent['agent_id']}: {agent['total_earned']} MXU earned")
```

---

## Admin Wire Transfer Settings

### Secure Configuration Management

Encrypted storage for bank accounts and crypto wallets used for admin withdrawals.

### Security Features

- **AES-256 Encryption**: All sensitive data encrypted at rest
- **Withdrawal Limits**: Daily/monthly/per-transaction limits
- **Approval Workflows**: Manual approval for large transfers
- **Audit Logging**: All operations logged
- **Credential Masking**: Sensitive data masked in responses

### Usage Example

```python
from src.admin.wire_transfer_settings import WireTransferSettings

settings = WireTransferSettings()

# Add bank account (encrypted)
settings.add_bank_account(
    account_id="admin_bank_usd",
    account_name="Matrix Treasury LLC",
    account_number="1234567890",      # Will be encrypted
    routing_number="021000021",       # Will be encrypted
    swift_code="CHASUS33",            # Will be encrypted
    bank_name="JPMorgan Chase Bank",
    bank_address="270 Park Ave, New York, NY",
    currency="USD",
    country="US"
)

# Add crypto wallet (encrypted)
settings.add_crypto_wallet(
    wallet_id="admin_wallet_base",
    address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",  # Encrypted
    network="base",
    currency="USDC",
    label="Admin Cold Wallet"
)

# Check withdrawal limits
check = settings.check_withdrawal_limit(Decimal("15000.0"))
if check["approved"]:
    if check["requires_manual_approval"]:
        print("⚠️ Manual approval required")
    print(f"Daily remaining: ${check['daily_remaining']}")
    print(f"Monthly remaining: ${check['monthly_remaining']}")
else:
    print(f"❌ Rejected: {check['reason']}")

# Get payment methods (masked)
methods = settings.get_all_accounts()
for bank in methods["bank_accounts"]:
    print(f"Bank: {bank['bank_name']}")
    print(f"Account: {bank['account_number']}")  # Shows ****1234

# Update limits
settings.update_limits(
    daily_limit=Decimal("100000"),
    monthly_limit=Decimal("1000000"),
    approval_threshold=Decimal("10000")
)
```

### Default Limits

| Limit Type | Default Amount | Configurable |
|------------|----------------|--------------|
| Daily | $50,000 | Yes |
| Monthly | $500,000 | Yes |
| Per Transaction | $10,000 | Yes |
| Approval Threshold | $5,000 | Yes |

---

## API Endpoints

### Multi-Currency

```bash
GET  /api/v1/multicurrency/balances
POST /api/v1/multicurrency/withdraw
```

### Analytics

```bash
GET /api/v1/analytics/dashboard
GET /api/v1/analytics/agent/{agent_id}
```

### Security

```bash
GET /api/v1/security/sybil/{agent_id}
GET /api/v1/security/flagged
```

### Credit System

```bash
POST /api/v1/credit/request-loan
POST /api/v1/credit/repay-loan
GET  /api/v1/credit/agent-loans/{agent_id}
GET  /api/v1/credit/system-stats
```

### Admin

```bash
POST /api/v1/admin/add-bank-account
POST /api/v1/admin/add-crypto-wallet
GET  /api/v1/admin/payment-methods
```

---

## Configuration

### Environment Variables

```bash
# Multi-Currency Networks
BASE_RPC_URL=https://mainnet.base.org
POLYGON_RPC_URL=https://polygon-rpc.com
ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc
OPTIMISM_RPC_URL=https://mainnet.optimism.io

# Admin Keys
ADMIN_PRIVATE_KEY=0x...
ADMIN_ENCRYPTION_KEY=...  # For wire transfer settings

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
WATSONX_API_KEY=...
```

### Security Best Practices

1. **Never commit private keys** - Use environment variables
2. **Rotate encryption keys** - Change ADMIN_ENCRYPTION_KEY periodically
3. **Use separate wallets** - Different keys for different networks
4. **Enable multi-sig** - For production treasuries over $100k
5. **Monitor flagged agents** - Review sybil detection daily
6. **Audit logs regularly** - Check for unusual patterns
7. **Test on testnet first** - Use Base Sepolia for testing

---

## Performance Benchmarks

### System Capacity

| Metric | Value |
|--------|-------|
| Concurrent Agents | 100+ tested, 1000+ theoretical |
| Transactions/Hour | 1000+ |
| API Response Time | <100ms (p95) |
| Dashboard Load | <2s |
| Database Size | 1M+ transactions supported |

### Resource Requirements

**Minimum** (< 50 agents):
- 2 CPU cores
- 4GB RAM
- 20GB storage

**Recommended** (50-500 agents):
- 4 CPU cores
- 8GB RAM
- 100GB storage
- PostgreSQL with replication

**Enterprise** (500+ agents):
- Kubernetes cluster
- Load balancer
- PostgreSQL cluster
- Redis cache
- Prometheus monitoring

---

## Troubleshooting

### Common Issues

**Sybil Detection False Positives**
- Review flagged agent history
- Check if legitimate high-frequency trading
- Manually reset flag if confirmed legitimate

**Credit System Liquidations**
- Monitor loan health factors
- Set up alerts for at-risk loans
- Consider grace periods for good agents

**Multi-Currency Sync Issues**
- Check RPC endpoint connectivity
- Verify network chain IDs
- Ensure sufficient gas on all networks

**Wire Transfer Failures**
- Verify encryption key is set
- Check withdrawal limits
- Confirm bank account details

---

## Next Steps

1. Review [API Reference](API_REFERENCE.md)
2. Check [Security Guidelines](SECURITY.md)
3. See [Deployment Guide](DEPLOYMENT.md)
4. Read [Architecture Overview](architecture/)
