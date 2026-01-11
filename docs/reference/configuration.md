# Configuration Reference

Complete reference for all configuration options in Matrix Treasury.

## Environment Variables

All configuration is done through environment variables. Create a `.env` file in the project root.

### Core Configuration

#### Database

```env
# SQLite (development)
DATABASE_URL=sqlite:///./data/treasury.db

# PostgreSQL (production)
DATABASE_URL=postgresql://user:password@host:5432/database

# Connection pool settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

#### Server Settings

```env
# Server host and port
HOST=0.0.0.0
PORT=8000

# Environment
ENVIRONMENT=production  # development | staging | production

# CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:5173,https://yourdomain.com

# API versioning
API_VERSION=v1
```

### Authentication & Security

#### Admin Credentials

```env
# Admin user configuration
ADMIN_USERNAME=admin
ADMIN_PASSWORD=SecurePassword123!
ADMIN_WALLET=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1

# Default values
# ADMIN_USERNAME=admin (if not set)
# ADMIN_PASSWORD=admin123 (if not set)
```

⚠️ **CRITICAL**: Change default credentials in production!

#### JWT Configuration

```env
# JWT secret key (REQUIRED in production)
JWT_SECRET=your-super-secret-key-min-32-chars

# Token expiration (hours)
JWT_EXPIRATION_HOURS=24

# JWT algorithm
JWT_ALGORITHM=HS256

# Default values
# JWT_SECRET=matrix-treasury-secret-change-in-production
# JWT_EXPIRATION_HOURS=24
```

**Generate secure JWT secret**:

```bash
# Using openssl
openssl rand -hex 32

# Using Python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Organization

```env
# Organization identifier
ORGANIZATION_ID=ORG-8821

# Default withdrawal wallet
DEFAULT_WITHDRAWAL_WALLET=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1
```

### LLM Configuration

#### Provider Selection

```env
# Active LLM provider
LLM_PROVIDER=openai  # openai | claude | watsonx | ollama
```

#### OpenAI

```env
# OpenAI API key
OPENAI_API_KEY=sk-your-openai-api-key

# Model selection
OPENAI_MODEL=gpt-4o  # gpt-4o | gpt-4-turbo | gpt-3.5-turbo

# API endpoint (optional, for proxies)
OPENAI_API_BASE=https://api.openai.com/v1

# Timeout (seconds)
OPENAI_TIMEOUT=60

# Max retries
OPENAI_MAX_RETRIES=3
```

**Available OpenAI models**:
- `gpt-4o` - Latest GPT-4 with optimizations (recommended)
- `gpt-4-turbo` - Fast GPT-4 variant
- `gpt-3.5-turbo` - Cost-effective option

#### Claude (Anthropic)

```env
# Claude API key
CLAUDE_API_KEY=sk-ant-your-claude-api-key

# Model selection
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# API endpoint
CLAUDE_API_BASE=https://api.anthropic.com

# Timeout (seconds)
CLAUDE_TIMEOUT=60

# Max retries
CLAUDE_MAX_RETRIES=3
```

**Available Claude models**:
- `claude-3-5-sonnet-20241022` - Latest Claude 3.5 (recommended)
- `claude-3-opus-20240229` - Most capable
- `claude-3-sonnet-20240229` - Balanced performance

#### WatsonX.ai (IBM)

```env
# WatsonX API key
WATSONX_API_KEY=your-watsonx-api-key

# Project ID
WATSONX_PROJECT_ID=your-project-id

# Model selection
WATSONX_MODEL_ID=meta-llama/llama-3-70b-instruct

# API endpoint
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# Timeout
WATSONX_TIMEOUT=60
```

**Available WatsonX models**:
- `meta-llama/llama-3-70b-instruct` - Llama 3 70B
- `mistralai/mixtral-8x7b-instruct-v01` - Mixtral
- `ibm/granite-13b-chat-v2` - IBM Granite

#### Ollama (Local)

```env
# Ollama base URL
OLLAMA_BASE_URL=http://localhost:11434

# Model name
OLLAMA_MODEL=llama3  # llama3 | mistral | codellama

# Timeout (seconds)
OLLAMA_TIMEOUT=120

# Temperature
OLLAMA_TEMPERATURE=0.7
```

**Setup Ollama**:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull llama3

# Run Ollama server
ollama serve
```

### Blockchain Configuration

#### Network Settings

```env
# Default network
DEFAULT_NETWORK=BASE  # BASE | POLYGON | ARBITRUM | OPTIMISM

# Network RPC endpoints
BASE_RPC_URL=https://mainnet.base.org
POLYGON_RPC_URL=https://polygon-rpc.com
ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc
OPTIMISM_RPC_URL=https://mainnet.optimism.io

# Chain IDs
BASE_CHAIN_ID=8453
POLYGON_CHAIN_ID=137
ARBITRUM_CHAIN_ID=42161
OPTIMISM_CHAIN_ID=10
```

#### Wallet Configuration

```env
# Private key for treasury operations (KEEP SECURE!)
TREASURY_PRIVATE_KEY=0x...

# Or use mnemonic
TREASURY_MNEMONIC=word1 word2 ... word12

# Wallet derivation path
WALLET_DERIVATION_PATH=m/44'/60'/0'/0/0
```

⚠️ **CRITICAL**: Never commit private keys to version control!

#### Token Contracts

```env
# USDC addresses per network
USDC_BASE=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
USDC_POLYGON=0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174
USDC_ARBITRUM=0xaf88d065e77c8cC2239327C5EDb3A432268e5831
USDC_OPTIMISM=0x7F5c764cBc14f9669B88837ca1490cCa17c31607

# EUR (EURe) addresses
EURE_BASE=0x...
EURE_POLYGON=0x...

# WBTC addresses
WBTC_BASE=0x...
WBTC_POLYGON=0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6
```

#### Gas Settings

```env
# Gas price strategy
GAS_PRICE_STRATEGY=medium  # slow | medium | fast | aggressive

# Manual gas settings (optional)
GAS_PRICE_GWEI=20
GAS_LIMIT=500000

# Max fee per gas (EIP-1559)
MAX_FEE_PER_GAS=100
MAX_PRIORITY_FEE_PER_GAS=2
```

### Economic Parameters

#### Treasury Settings

```env
# Initial reserve (USDC)
INITIAL_RESERVE=10000.0

# MXU exchange rate (USDC per MXU)
MXU_EXCHANGE_RATE=0.001

# Reserve ratio (minimum collateral %)
MIN_RESERVE_RATIO=1.25

# Critical solvency threshold
CRITICAL_SOLVENCY_RATIO=1.1
```

#### Credit System

```env
# Universal Basic Compute (UBC)
UBC_AMOUNT=100.0  # MXU per week
UBC_INTERVAL_DAYS=7

# Credit limits
MAX_CREDIT_RATIO=2.0  # 2x collateral
DEFAULT_INTEREST_RATE=0.05  # 5% APR

# Liquidation settings
LIQUIDATION_THRESHOLD=0.8  # 80% of collateral value
LIQUIDATION_PENALTY=0.1  # 10% penalty
```

#### Taxation & Fees

```env
# Progressive tax brackets (rates)
TAX_BRACKET_1_RATE=0.10  # 10% up to 1000 MXU
TAX_BRACKET_2_RATE=0.15  # 15% from 1000-10000 MXU
TAX_BRACKET_3_RATE=0.20  # 20% above 10000 MXU

# Transaction fees
TRANSACTION_FEE_PERCENT=0.001  # 0.1%
WITHDRAWAL_FEE_FIXED=1.0  # 1 USDC
```

### Monitoring & Analytics

```env
# Enable detailed logging
LOG_LEVEL=INFO  # DEBUG | INFO | WARNING | ERROR | CRITICAL

# Structured logging format
LOG_FORMAT=json  # json | text

# Log file location
LOG_FILE=logs/treasury.log

# Metrics collection
ENABLE_METRICS=true
METRICS_PORT=9090

# Prometheus endpoint
PROMETHEUS_ENABLED=true
PROMETHEUS_PATH=/metrics
```

### External Services

#### Wire Transfer Settings

```env
# Wire transfer provider
WIRE_TRANSFER_PROVIDER=plaid  # plaid | stripe | manual

# Plaid configuration
PLAID_CLIENT_ID=your-client-id
PLAID_SECRET=your-secret
PLAID_ENV=sandbox  # sandbox | development | production

# Stripe configuration
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

#### Email Notifications

```env
# Email service
EMAIL_PROVIDER=sendgrid  # sendgrid | mailgun | smtp

# SendGrid
SENDGRID_API_KEY=SG....

# SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@matrix-treasury.com
```

#### Monitoring Services

```env
# Sentry error tracking
SENTRY_DSN=https://...@sentry.io/...
SENTRY_ENVIRONMENT=production

# DataDog APM
DATADOG_API_KEY=...
DATADOG_APP_KEY=...

# New Relic
NEW_RELIC_LICENSE_KEY=...
NEW_RELIC_APP_NAME=Matrix Treasury
```

### Feature Flags

```env
# Enable/disable features
ENABLE_SYBIL_DETECTION=true
ENABLE_AUTOPILOT=true
ENABLE_CREDIT_SYSTEM=true
ENABLE_UBC=true
ENABLE_WIRE_TRANSFERS=true
ENABLE_MULTI_CURRENCY=true

# Experimental features
ENABLE_ML_CFO=false
ENABLE_CROSS_CHAIN_BRIDGE=false
```

### Rate Limiting

```env
# API rate limits (requests per minute)
RATE_LIMIT_GLOBAL=100
RATE_LIMIT_PER_IP=60
RATE_LIMIT_PER_USER=30

# Burst allowance
RATE_LIMIT_BURST=20
```

## Configuration Files

### Mission Control Settings

Frontend dashboard settings are stored in the database but can be initialized via environment:

```env
# Default LLM provider for dashboard
DASHBOARD_LLM_PROVIDER=openai

# Admin wallet for withdrawals
DASHBOARD_ADMIN_WALLET=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1
```

Managed through Mission Control UI:
- Settings → LLM Configuration
- Settings → Admin Wallet

### Docker Compose

Override settings in `docker-compose.override.yml`:

```yaml
version: '3.8'

services:
  backend:
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/treasury
      - LOG_LEVEL=DEBUG
    volumes:
      - ./custom-config:/app/config
```

## Security Best Practices

### Production Checklist

✅ Change default admin password
✅ Generate secure JWT secret (32+ characters)
✅ Use PostgreSQL instead of SQLite
✅ Enable HTTPS/TLS
✅ Set strong database password
✅ Secure private keys (use secrets manager)
✅ Configure firewall rules
✅ Enable audit logging
✅ Set up backup strategy
✅ Configure monitoring alerts

### Secrets Management

**Never** store secrets in:
- Version control (`.env` in `.gitignore`)
- Docker images
- Log files
- Error messages

**Use**:
- Environment variables
- Docker secrets
- Kubernetes secrets
- Vault (HashiCorp)
- AWS Secrets Manager
- Azure Key Vault

**Example with Docker Secrets**:

```yaml
version: '3.8'

services:
  backend:
    secrets:
      - jwt_secret
      - db_password

secrets:
  jwt_secret:
    external: true
  db_password:
    external: true
```

## Validation

### Check Configuration

```bash
# Validate environment variables
python3 << EOF
from src.core.config import settings
print(f"Database: {settings.DATABASE_URL}")
print(f"JWT Secret: {'✓' if len(settings.JWT_SECRET) >= 32 else '✗ TOO SHORT'}")
print(f"Admin configured: {'✓' if settings.ADMIN_PASSWORD != 'admin123' else '✗ DEFAULT PASSWORD'}")
EOF
```

### Test Database Connection

```bash
python3 << EOF
from src.db.connection import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print("Database connection: ✓")
EOF
```

### Test LLM Provider

```bash
curl -X POST http://localhost:8000/api/v1/neural/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Test message"}'
```

## Troubleshooting

### Common Issues

**Issue**: Database connection failed

```bash
# Check DATABASE_URL format
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

**Issue**: JWT token invalid

```bash
# JWT secret changed? Tokens are invalidated
# Users must login again
# Check JWT_SECRET is consistent across restarts
```

**Issue**: LLM API errors

```bash
# Check API key
echo $OPENAI_API_KEY | wc -c  # Should be ~50 chars

# Test directly
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

## See Also

- [Installation Guide](../deployment/installation.md)
- [Production Checklist](../deployment/production-checklist.md)
- [Security Architecture](../architecture/security.md)
- [Troubleshooting](troubleshooting.md)
