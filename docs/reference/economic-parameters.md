# Economic Parameters

Reference guide for all economic parameters in Matrix Treasury.

## Core Parameters

### MXU (Matrix Unit)

**Definition**: 1 MXU = 1 Watt-Hour (Wh) of compute-energy equivalent

**Base Exchange Rate**: 1 MXU = $0.001 USDC (configurable)

**Purpose**: Universal unit for measuring computational work and resource consumption

### Reserve Ratio

**Minimum Reserve Ratio**: 1.25 (125% collateralization)

```
Reserve Ratio = Total Reserve Value / Total MXU Supply
```

**Critical Threshold**: 1.1 (110%)
- Below this triggers emergency measures
- Panic mode activated
- New minting halted

**Healthy Range**: 1.5 - 3.0
- 1.5-2.0: Normal operations
- 2.0-3.0: Strong reserve position
- >3.0: Consider reserve optimization

### Currencies

**Supported Currencies**:
- **USDC**: Primary reserve currency, 1:1 USD peg
- **EUR** (EURe): European operations
- **BTC** (WBTC): Store of value, volatility hedge

**Default Currency**: USDC

**Currency Weights** (for reserve calculation):
- USDC: 1.0 (stable)
- EUR: 1.0 (stable)
- BTC: 0.8 (discount for volatility)

## Credit System

### Universal Basic Compute (UBC)

**Amount**: 100 MXU per agent per week

**Eligibility**:
- Active agent account
- Not bankrupt
- Email verified

**Distribution**: Automatic weekly renewal

**Purpose**: Prevent death spirals, ensure baseline participation

### Credit Limits

**Default Credit Ratio**: 2.0 (200% of deposits)

```
Max Credit = Agent Balance × Credit Ratio
```

**Credit Score Impact**:
- Score 800-1000: 3.0x ratio
- Score 600-799: 2.0x ratio
- Score 400-599: 1.5x ratio
- Score 200-399: 1.0x ratio
- Score <200: 0.5x ratio

**Interest Rate**: 5% APR (default)

```
Daily Interest = Principal × (0.05 / 365)
```

### Bankruptcy

**Bankruptcy Threshold**: Balance < -1000 MXU

**Bankruptcy Ladder**:
1. **Soft Warning** (-500 MXU): Email notification
2. **Hard Warning** (-750 MXU): Service throttling
3. **Bankruptcy** (-1000 MXU): Account suspended

**Rehabilitation**:
- Pay off debt
- Credit score gradually recovers
- 30-day probation period

## Taxation

### Progressive Tax Brackets

**Purpose**: Fund public goods, prevent wealth concentration

**Rates**:

| Bracket | Balance Range | Rate | Example (1000 MXU) |
|---------|---------------|------|--------------------|
| 1 | 0 - 1,000 MXU | 10% | 100 MXU |
| 2 | 1,000 - 10,000 MXU | 15% | +1,350 MXU |
| 3 | 10,000+ MXU | 20% | +... |

**Calculation**:

```python
def calculate_tax(balance: float) -> float:
    if balance <= 1000:
        return balance * 0.10
    elif balance <= 10000:
        return 100 + (balance - 1000) * 0.15
    else:
        return 100 + 1350 + (balance - 10000) * 0.20
```

**Collection**: Monthly, automatic deduction

**Usage**: UBC funding, infrastructure, public goods

### Transaction Fees

**Standard Fee**: 0.1% per transaction

**Minimum Fee**: 0.01 MXU

**Maximum Fee**: 100 MXU (cap for large transactions)

**Fee Structure**:

```python
fee = max(0.01, min(amount * 0.001, 100))
```

**Exemptions**:
- UBC distributions
- Internal transfers <1 MXU
- Bankruptcy rehabilitation

### Withdrawal Fees

**Fiat Withdrawal**: 1 USDC flat fee

**Crypto Withdrawal**: Gas fees + 0.5% service fee

**Daily Limits**:
- Standard account: 1,000 USDC/day
- Verified account: 10,000 USDC/day
- Enterprise: Custom limits

## Four-Part Tariff

All computational work charged across four categories:

### 1. Energy Tariff

**Basis**: Actual electricity consumed (kWh)

**Rate**: $0.15/kWh (market rate + margin)

**Calculation**:

```python
energy_cost = kilowatt_hours * 0.15 * (USDC_per_MXU / 0.001)
```

**Example**: 1 kWh = 1000 MXU × $0.15 = $150 in MXU

### 2. Capacity Tariff

**Basis**: Reserved compute capacity

**Rate**: $0.05/vCPU-hour

**Purpose**: Cover fixed infrastructure costs

**Calculation**:

```python
capacity_cost = vcpus * hours * 0.05
```

### 3. State Tariff

**Basis**: Storage, memory, bandwidth

**Rates**:
- Storage: $0.10/GB-month
- Memory: $0.02/GB-hour
- Bandwidth: $0.05/GB transferred

**Calculation**:

```python
state_cost = (
    storage_gb * 0.10 / 720 +  # per hour
    memory_gb * 0.02 +
    bandwidth_gb * 0.05
)
```

### 4. Governance Tariff

**Basis**: Fixed overhead per transaction

**Rate**: 2% of total cost

**Purpose**: Platform maintenance, development

**Calculation**:

```python
governance_cost = (energy + capacity + state) * 0.02
```

### Total Cost

```python
total_cost = energy + capacity + state + governance
```

## Minting and Burning

### Minting Rules

**Formula**:

```python
mintable = reserve / exchange_rate / min_reserve_ratio
```

**Example**:
- Reserve: $1,000 USDC
- Exchange rate: $0.001/MXU
- Min ratio: 1.25

```python
mintable = 1000 / 0.001 / 1.25 = 800,000 MXU
```

**Safety Checks**:
- Reserve ratio must stay above minimum
- Cannot mint if in panic mode
- Audit log created for all mints

### Burning Rules

**Formula**: Simple reduction of supply

```python
def burn(amount: float):
    if amount > token_supply:
        raise InsufficientSupplyError
    token_supply -= amount
```

**Purpose**:
- Return collateral on withdrawal
- Deflationary pressure
- Maintain reserve ratio

**No Reserve Release**: Burning doesn't automatically release reserve

## Stabilization Mechanisms

### Automatic Stabilizers

**Reserve Rebalancing** (triggered when ratio < 1.3):
1. Halt new credit issuance
2. Increase transaction fees by 50%
3. Reduce UBC by 25%
4. Alert administrators

**Emergency Measures** (triggered when ratio < 1.1):
1. Panic mode activated
2. Halt all minting
3. Increase fees by 100%
4. Suspend UBC
5. Force settlement of debts

### Liquidation

**Liquidation Threshold**: 80% of collateral value

**Liquidation Penalty**: 10% fee

**Process**:
1. Agent balance falls below threshold
2. Automatic liquidation triggered
3. Assets sold to cover debt
4. 10% penalty applied
5. Remaining balance returned

## Configuration

### Environment Variables

```bash
# Core Parameters
MXU_EXCHANGE_RATE=0.001
MIN_RESERVE_RATIO=1.25
CRITICAL_SOLVENCY_RATIO=1.1

# UBC
UBC_AMOUNT=100.0
UBC_INTERVAL_DAYS=7

# Credit
MAX_CREDIT_RATIO=2.0
DEFAULT_INTEREST_RATE=0.05

# Tax
TAX_BRACKET_1_RATE=0.10
TAX_BRACKET_2_RATE=0.15
TAX_BRACKET_3_RATE=0.20

# Fees
TRANSACTION_FEE_PERCENT=0.001
WITHDRAWAL_FEE_FIXED=1.0

# Tariffs
ENERGY_RATE=0.15
CAPACITY_RATE=0.05
STORAGE_RATE=0.10
MEMORY_RATE=0.02
BANDWIDTH_RATE=0.05
GOVERNANCE_RATE=0.02
```

### Dynamic Adjustment

Some parameters can be adjusted via Mission Control:

- Transaction fees (within limits)
- Credit ratios (per agent)
- UBC amounts (emergency only)
- Tax rates (governance approval required)

### Audit Trail

All parameter changes logged:

```python
{
  "timestamp": "2026-01-11T08:47:52Z",
  "parameter": "TRANSACTION_FEE_PERCENT",
  "old_value": 0.001,
  "new_value": 0.002,
  "changed_by": "admin",
  "reason": "Increased network costs"
}
```

## Economic Simulation

### Scenarios

**Scenario 1: Steady State**
- 100 active agents
- Average balance: 500 MXU
- Daily transactions: 1,000
- Reserve ratio: 1.8

**Scenario 2: Growth Phase**
- New agents: +20/day
- Increasing deposits
- Reserve ratio: 2.5+
- Opportunity to mint more

**Scenario 3: Crisis**
- Mass withdrawals
- Reserve ratio: 1.15
- Stabilizers activated
- Recovery plan needed

### Stress Testing

Run simulations:

```bash
python scripts/simulate_economy.py --agents=1000 --days=365
```

## See Also

- [Economic Design](../architecture/economic-design.md)
- [Configuration Reference](configuration.md)
- [Treasury API](../api/endpoints.md)
- [System Architecture](../architecture/system-overview.md)
