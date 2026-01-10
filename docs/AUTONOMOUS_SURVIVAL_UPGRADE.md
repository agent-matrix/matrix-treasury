# 🚀 Matrix Treasury: Autonomous Survival Upgrade

## Overview

This document describes the **Autonomous Survival Upgrade** that transforms Matrix Treasury from a standard software application into a **self-sustaining digital organism**.

## 🎯 What This Upgrade Does

### Before (Day 1): Static Architecture
- Requires human credit card for AWS/OpenAI
- Manual intervention for bill payments
- No concept of cost vs. value
- Death on admin disappearance

### After (Day 2): Autonomous Architecture
- Self-funded with real USDC
- Automatic bill payments (Akash, APIs)
- LLM CFO makes intelligent spending decisions
- Survives indefinitely if providing value

---

## 🏗 Architecture Overview

### 1. The Dual-Layer Economy

| Layer | Currency | Purpose | Speed | Security |
|-------|----------|---------|-------|----------|
| **Internal** | MXU | Agent scoring, bidding, priority | Fast | Low risk |
| **External** | USDC | Real bills, infrastructure, APIs | Slow | High risk |

**How It Works**:
1. **Agents earn MXU** when humans pay for their services
2. **Agents spend MXU** to request real money (USDC) from the CFO
3. **CFO approves/rejects** based on agent credit score and treasury health
4. **Real payments** only happen after CFO approval (safety circuit breaker)

### 2. Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                      MATRIX TREASURY                        │
│                  (Autonomous Digital Organism)              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   INCOME     │───▶│     CFO      │───▶│    VAULT     │ │
│  │  (AppStore)  │    │  (LLM Brain) │    │  (Real USDC) │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                    │         │
│         ▼                    ▼                    ▼         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   LEDGER     │    │     ATXP     │    │    AKASH     │ │
│  │  (MXU Track) │    │ (HTTP 402)   │    │ (Cloud Host) │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                    │                    │         │
│         └────────────────────┴────────────────────┘         │
│                              │                              │
│                    ┌──────────────────┐                     │
│                    │  SURVIVAL LOOP   │                     │
│                    │   (Heartbeat)    │                     │
│                    └──────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Installation Guide

### Prerequisites

```bash
# Required
Python 3.11+
Ollama (for local LLM - optional, default)

# Optional (for production)
- OpenAI API key (GPT-4)
- Anthropic API key (Claude)
- IBM WatsonX.ai account (WatsonX)
- Ethereum wallet with USDC on Base/Polygon
```

### Step 1: Install Dependencies

```bash
# Install base dependencies
make install

# Install upgrade dependencies (CrewAI, Web3, etc.)
make install-upgrade
```

### Step 2: Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit configuration
nano .env
```

**Critical Settings**:

```bash
# Blockchain (REQUIRED for production)
RPC_URL=https://mainnet.base.org
TREASURY_PRIVATE_KEY=0xYourPrivateKeyHere
NETWORK=base

# LLM Provider (REQUIRED)
# Options: ollama (default, local), openai, claude, watsonx
CFO_PROVIDER=ollama

# Ollama (Local - No API key needed)
OLLAMA_BASE_URL=http://localhost:11434
CFO_OLLAMA_MODEL=llama3

# OpenAI (if using)
OPENAI_API_KEY=sk-...
CFO_OPENAI_MODEL=gpt-4o-mini

# Claude (if using)
ANTHROPIC_API_KEY=sk-ant-...
CFO_CLAUDE_MODEL=claude-sonnet-4-5

# WatsonX.ai (if using)
WATSONX_API_KEY=...
WATSONX_PROJECT_ID=...
CFO_WATSONX_MODEL=ibm/granite-3-8b-instruct

# Akash Infrastructure
AKASH_PROVIDER_ADDRESS=akash1...
AKASH_DAILY_COST_USD=1.50
```

### Step 3: Initialize System

```bash
# Create data directory
mkdir -p data logs

# Initialize blockchain vault (read-only mode without private key)
make setup-vault

# Initialize internal ledger
make setup-ledger
```

### Step 4: Test Installation

```bash
# Test vault connection
make test-vault

# Test LLM provider
make test-llm

# Test CFO intelligence
make test-cfo

# Run full demo
make demo-upgrade
```

---

## 🔄 Daily Operations

### The Survival Loop (Heartbeat)

**What It Does**:
1. Checks treasury solvency (USDC balance, MXU supply)
2. Pays infrastructure bills (Akash hosting)
3. Triggers economic stabilizers if needed
4. Reports system health

**How to Run**:

```bash
# Manual run
make survival-check

# Automated (cron job)
# Add to crontab: 0 0 * * * cd /path/to/matrix-treasury && make survival-check
```

**Expected Output**:

```
💓 SYSTEM HEARTBEAT: Survival Check Started
================================================================================
📦 Initializing system components...
   ✅ All components initialized

💰 STEP 1: Checking Treasury Solvency
--------------------------------------------------------------------------------
   💵 USDC Balance: $1,234.56
   📊 Total MXU Supply: 100,000.00
   🎯 Coverage Ratio: 1.23x
   🏥 Health Status: HEALTHY
   👥 Total Agents: 42
   💀 Bankrupt Agents: 3
   ✅ Treasury is healthy

☁️  STEP 2: Infrastructure Management (Akash)
--------------------------------------------------------------------------------
   🏠 Lease Status: True
   📅 Days Remaining: 5
   💵 Cost per Day: $1.50
   🛤️  Runway: 823 days
   🏥 Infrastructure Health: HEALTHY
   ℹ️  No renewal needed

⚖️  STEP 3: Economic Stabilizers
--------------------------------------------------------------------------------
   [No intervention needed]

📊 SURVIVAL SUMMARY
================================================================================
✅ Treasury Balance: $1,234.56
✅ System Health: HEALTHY
✅ Infrastructure: 823 days runway
✅ Active Agents: 42
✅ Survival Status: OPERATIONAL

💓 Heartbeat Complete - System Alive
```

---

## 🧠 CFO Intelligence

### How It Works

The CFO uses a CrewAI agent powered by your chosen LLM to make intelligent spending decisions.

**Decision Flow**:

```python
1. Agent requests funding: "I need $0.05 for OpenAI API call"
   ↓
2. Check agent's MXU balance (internal credit)
   ↓
3. Check treasury's USDC balance (real money)
   ↓
4. Ask LLM: "Should we approve this expense?"
   - Agent credit score
   - Task importance
   - Treasury health
   - Historical performance
   ↓
5. If APPROVED: Execute blockchain payment
   If REJECTED: Refund MXU, deny request
```

### Example CFO Decision

**Request**:
```python
cfo.request_funding(
    agent_id="worker_123",
    expense_details={
        "item": "OpenAI API Call",
        "cost_usd": 0.05,
        "reason": "Need to generate code for user",
        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    }
)
```

**CFO Analysis**:
```
Agent ID: worker_123
Credit Score: 0.87 (excellent)
Total Earned: $245.00
Total Spent: $123.00
Tasks Completed: 156
Tasks Failed: 3
Treasury Balance: $1,234.56

Decision: ✅ APPROVED
Reason: Agent has excellent track record, expense is small relative to treasury balance, and task is revenue-generating.
```

---

## 💰 Economic Parameters

### Exchange Rates

```python
# MXU to USD
1 MXU = $0.01 USD
100 MXU = $1.00 USD

# Human pays agent $10
# Agent receives: 1,000 MXU

# Agent requests $0.05 payment
# Cost: 5 MXU deducted from balance
```

### Coverage Ratio

```python
Coverage Ratio = USDC Balance / (Total MXU Supply × Exchange Rate)

✅ HEALTHY:  Ratio ≥ 1.5 and Balance > $100
⚠️  WARNING:  Ratio ≥ 1.0 and Balance > $10
🚨 CRITICAL: Ratio < 1.0 or Balance < $10
```

### Agent Credit Scores

| Score | Meaning | CFO Behavior |
|-------|---------|--------------|
| 0.9 - 1.0 | Excellent | Auto-approve most requests |
| 0.7 - 0.9 | Good | Approve if treasury healthy |
| 0.5 - 0.7 | Average | Scrutinize carefully |
| 0.3 - 0.5 | Poor | Approve only critical |
| 0.0 - 0.3 | Terrible | Reject almost all |

**Score Updates**:
- Earning revenue: +0.2 (capped at 1.0)
- Completing tasks: +0.1 per task
- Failing tasks: -0.15 per failure
- Bankruptcy: -0.3

---

## 🔒 Security & Safety

### Circuit Breakers

1. **MXU Hold**: Agent's MXU is deducted BEFORE CFO approval
   - Prevents race conditions
   - Refunded if rejected

2. **Liquidity Check**: CFO verifies USDC balance before approval
   - Prevents overdrafts
   - Fails safe

3. **LLM Failsafe**: If LLM fails, small amounts (<$1) auto-approve
   - Ensures system keeps running
   - Larger amounts denied for safety

### Bankruptcy Protection

**Agent Bankruptcy**:
- Cannot request funding with 0 MXU
- Credit score drops
- Can recover by earning revenue

**System Bankruptcy**:
- If USDC < Daily Infrastructure Cost
- Akash manager initiates graceful shutdown
- Data backed up before shutdown

---

## 🛠 Troubleshooting

### Issue: "RPC_URL not set"

**Fix**:
```bash
# Add to .env
RPC_URL=https://mainnet.base.org

# Or use testnet
RPC_URL=https://sepolia.base.org
```

### Issue: "LLM connection failed"

**Fix for Ollama**:
```bash
# Start Ollama service
ollama serve

# Pull model
ollama pull llama3

# Test
curl http://localhost:11434/api/generate -d '{"model":"llama3","prompt":"Hi"}'
```

**Fix for OpenAI**:
```bash
# Verify API key
echo $OPENAI_API_KEY

# Test
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Issue: "Insufficient gas balance"

**Fix**:
```bash
# Send ETH to your treasury wallet address for gas fees
# Check balance
make test-vault
```

---

## 📊 Monitoring & Metrics

### Key Metrics to Track

```python
# Treasury Health
cfo.get_treasury_health()
# Returns: {
#   "usdc_balance": 1234.56,
#   "total_mxu_supply": 100000.0,
#   "coverage_ratio": 1.23,
#   "health_status": "HEALTHY",
#   "total_agents": 42,
#   "bankrupt_agents": 3
# }

# Infrastructure Status
akash.get_infrastructure_status()
# Returns: {
#   "days_remaining": 5,
#   "cost_per_day_usd": 1.50,
#   "runway_days": 823,
#   "health_status": "HEALTHY"
# }
```

---

## 🚀 Production Deployment

### 1. Fund the Treasury

```bash
# Send USDC to your treasury wallet
# Recommended starting amount: $100-$500

# Verify
make test-vault
```

### 2. Configure Akash

```bash
# Install Akash CLI
curl -sSfL https://raw.githubusercontent.com/akash-network/node/master/install.sh | sh

# Deploy your service
# Update AKASH_PROVIDER_ADDRESS in .env with provider wallet
```

### 3. Set Up Cron Job

```bash
# Edit crontab
crontab -e

# Add daily survival check (runs at midnight)
0 0 * * * cd /home/user/matrix-treasury && make survival-check >> /var/log/matrix-survival.log 2>&1
```

### 4. Monitor System

```bash
# View logs
tail -f logs/survival.log

# Check health
make survival-check
```

---

## 🎓 Advanced Topics

### Multi-Provider LLM Setup

**Use Case**: Fallback if primary LLM fails

```python
# In code, you can switch providers dynamically
from src.llm.settings import set_provider, LLMProvider

# Try OpenAI
set_provider(LLMProvider.openai)

# If fails, fallback to Ollama
try:
    cfo = MatrixCFO(vault, ledger)
except Exception:
    set_provider(LLMProvider.ollama)
    cfo = MatrixCFO(vault, ledger)
```

### Custom CFO Policies

Edit `src/llm/cfo.py` to customize approval logic:

```python
# Example: Auto-approve infrastructure payments
if expense_details.get('item') == 'Akash Renewal':
    return {"approved": True, "reason": "Critical infrastructure"}
```

### Revenue Streams

Implement in your application:

```python
from src.services.income_gateway import AppStore

store = AppStore(vault, ledger)

# Subscription model
store.subscribe_agent_service(
    user_id="customer_123",
    agent_id="my_agent",
    subscription_tier="pro"  # $50/month
)

# Pay-per-task model
store.pay_per_task(
    user_id="customer_123",
    agent_id="my_agent",
    task_type="code",  # $2.00 base
    quality_score=0.95  # Multiplier: 1.45x
)
```

---

## 📝 API Reference

### Vault

```python
from src.blockchain.vault import ExternalVault

vault = ExternalVault()
balance = vault.get_real_balance()
vault.pay_external_bill(
    to_address="0x...",
    amount_usdc=10.0,
    memo="Payment description"
)
```

### Ledger

```python
from src.blockchain.ledger import InternalLedger

ledger = InternalLedger()
ledger.create_wallet("agent_123", initial_balance=1000)
ledger.credit_agent("agent_123", 100, "Task completion")
ledger.debit_agent("agent_123", 50, "API usage")
```

### CFO

```python
from src.llm.cfo import MatrixCFO

cfo = MatrixCFO(vault, ledger)
decision = cfo.request_funding(
    agent_id="agent_123",
    expense_details={
        "item": "Service Name",
        "cost_usd": 1.00,
        "reason": "Why needed",
        "address": "0x..."
    }
)
```

---

## 🆘 Support

**Documentation**: `/docs`
**Issues**: https://github.com/agent-matrix/matrix-treasury/issues
**Discord**: https://discord.gg/AJUnEerk
**Email**: contact@ruslanmv.com

---

## 📄 License

Apache License 2.0 - See [LICENSE](../LICENSE)

---

**Built with ❤️ by the Agent Matrix community**

*Making autonomous AI economies a reality*
