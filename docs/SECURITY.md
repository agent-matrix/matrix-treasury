# Security Best Practices

Security guidelines for deploying and operating Matrix Treasury in production.

---

## Overview

Matrix Treasury handles real money across multiple currencies and blockchain networks. Security is paramount for protecting funds, preventing fraud, and ensuring system integrity.

---

## Blockchain Security

### Private Key Management

**Critical Rules**:
1. ✅ **Never commit private keys to Git**
2. ✅ **Use environment variables only**
3. ✅ **Rotate keys every 90 days**
4. ✅ **Use different keys per network**
5. ✅ **Store keys in secure vault (production)**

**Bad Practice** ❌:
```python
private_key = "0x1234567890abcdef..."  # NEVER DO THIS
```

**Good Practice** ✅:
```python
private_key = os.getenv("ADMIN_PRIVATE_KEY")
if not private_key:
    raise ValueError("ADMIN_PRIVATE_KEY not set")
```

### Multi-Signature Wallets

For treasuries over $100,000:

```python
# Use Gnosis Safe or similar multi-sig
MULTISIG_THRESHOLD = 3  # Require 3 of 5 signatures
MULTISIG_OWNERS = [
    "0xOwner1...",
    "0xOwner2...",
    "0xOwner3...",
    "0xOwner4...",
    "0xOwner5..."
]
```

**Benefits**:
- No single point of failure
- Protection against compromised keys
- Audit trail for all transactions
- Time delays for large transfers

### Network Segregation

Use separate wallets for different purposes:

| Network | Purpose | Funding Level |
|---------|---------|---------------|
| Base | Hot wallet (daily ops) | $10,000 max |
| Polygon | Medium security | $50,000 max |
| Arbitrum | Cold storage | Unlimited |
| Optimism | Reserve funds | $100,000 max |

### Gas Management

Prevent gas attacks:

```python
# Set maximum gas price
MAX_GAS_PRICE = Web3.to_wei(100, 'gwei')

if gas_price > MAX_GAS_PRICE:
    raise ValueError("Gas price too high, possible attack")

# Set gas limit caps
GAS_LIMITS = {
    "USDC_transfer": 100000,
    "EUR_transfer": 150000,
    "BTC_transfer": 200000
}
```

---

## Application Security

### Environment Variables

**Required Variables**:
```bash
# Blockchain (separate per network)
BASE_PRIVATE_KEY=0x...
POLYGON_PRIVATE_KEY=0x...
ARBITRUM_PRIVATE_KEY=0x...
OPTIMISM_PRIVATE_KEY=0x...

# Encryption
ADMIN_ENCRYPTION_KEY=...  # 32-byte key for Fernet

# Database
DATABASE_URL=postgresql://user:password@localhost/treasury

# API Keys (encrypted at rest)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

**Security Measures**:
- Use `.env` file (never commit)
- Restrict file permissions: `chmod 600 .env`
- Use secret management in production (AWS Secrets Manager, HashiCorp Vault)
- Rotate keys quarterly

### Encryption

All sensitive data encrypted with AES-256:

```python
from cryptography.fernet import Fernet

# Generate encryption key (one time)
key = Fernet.generate_key()
# Save securely: export ADMIN_ENCRYPTION_KEY=key

# Encrypt sensitive data
cipher = Fernet(os.getenv("ADMIN_ENCRYPTION_KEY"))
encrypted = cipher.encrypt(b"sensitive_data")

# Decrypt when needed
decrypted = cipher.decrypt(encrypted)
```

**What We Encrypt**:
- Bank account numbers
- Routing numbers
- SWIFT codes
- Crypto wallet addresses
- API keys in database
- Private configuration

### Database Security

**PostgreSQL Configuration**:
```sql
-- Use SSL connections
ALTER SYSTEM SET ssl = on;

-- Require encrypted connections
ALTER SYSTEM SET ssl_prefer_server_ciphers = on;

-- Set password encryption
ALTER SYSTEM SET password_encryption = 'scram-sha-256';

-- Enable audit logging
ALTER SYSTEM SET log_statement = 'mod';
ALTER SYSTEM SET log_connections = on;
```

**Connection Security**:
```python
DATABASE_URL = "postgresql://user:pass@host:5432/db?sslmode=require"
```

**Access Control**:
```sql
-- Read-only user for analytics
CREATE USER analytics WITH PASSWORD 'secure_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics;

-- App user with limited permissions
CREATE USER app_user WITH PASSWORD 'secure_password';
GRANT SELECT, INSERT, UPDATE ON transactions TO app_user;
GRANT SELECT, UPDATE ON agents TO app_user;
```

---

## Fraud Prevention

### Sybil Detection

Monitor these metrics daily:

**High-Risk Indicators**:
- Transaction velocity > 100 tx/hour
- Credit score volatility > 0.3
- Spending > 2x earning ratio
- Multiple bankruptcies (> 2)
- New accounts with immediate high-value activity
- IP address shared by 5+ agents

**Automated Actions**:
```python
from src.security.sybil_detection import SybilDetector

detector = SybilDetector()

# Run daily check
for agent_id in active_agents:
    result = detector.detect_sybil_attack(agent_id)

    if result["risk_score"] > 0.7:
        # CRITICAL: Freeze account
        freeze_agent(agent_id)
        send_alert("Critical sybil risk", agent_id)

    elif result["risk_score"] > 0.5:
        # HIGH: Flag for manual review
        flag_for_review(agent_id)
        send_alert("High sybil risk", agent_id)
```

### Transaction Limits

Implement rate limiting:

```python
# Per agent limits
AGENT_LIMITS = {
    "hourly_transactions": 50,
    "hourly_volume": Decimal("1000.0"),
    "daily_volume": Decimal("10000.0")
}

# Treasury limits
TREASURY_LIMITS = {
    "daily_withdrawals": Decimal("50000.0"),
    "monthly_withdrawals": Decimal("500000.0"),
    "per_transaction_max": Decimal("10000.0")
}

# Approval thresholds
APPROVAL_REQUIRED = {
    "admin_withdrawal": Decimal("5000.0"),
    "agent_loan": Decimal("1000.0"),
    "infrastructure_payment": Decimal("500.0")
}
```

### Audit Logging

Log all sensitive operations:

```python
import logging

audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Log format: timestamp, user, action, details
audit_logger.info(f"WITHDRAWAL: admin withdrew {amount} {currency} to {destination}")
audit_logger.warning(f"SYBIL_FLAG: agent {agent_id} flagged with risk {risk_score}")
audit_logger.critical(f"KILLSWITCH: Emergency stop activated by {admin_id}")
```

**What to Log**:
- All withdrawals
- Loan approvals/denials
- Sybil detections
- Configuration changes
- Failed authentication attempts
- Emergency actions

---

## API Security

### Authentication

Use API keys with rate limiting:

```python
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key not in valid_api_keys:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key
```

**Best Practices**:
- Rotate API keys monthly
- Use different keys for different services
- Implement key expiration
- Log all API key usage
- Revoke compromised keys immediately

### CORS Configuration

Restrict to known origins:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://treasury.yourdomain.com",
        "https://admin.yourdomain.com"
    ],  # NEVER use ["*"] in production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### Rate Limiting

Prevent abuse:

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

# Apply to endpoints
@router.get("/analytics/dashboard",
    dependencies=[Depends(RateLimiter(times=30, minutes=1))])
async def get_analytics():
    ...

# Stricter for admin endpoints
@router.post("/admin/add-bank-account",
    dependencies=[Depends(RateLimiter(times=5, minutes=1))])
async def add_bank_account():
    ...
```

### Input Validation

Validate all inputs:

```python
from pydantic import BaseModel, Field, validator
from decimal import Decimal

class WithdrawalRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, le=10000)
    currency: str = Field(..., regex="^(USDC|EUR|BTC)$")
    destination: str = Field(..., min_length=42, max_length=42)

    @validator("destination")
    def validate_address(cls, v):
        if not v.startswith("0x"):
            raise ValueError("Invalid Ethereum address")
        return v.lower()
```

---

## Infrastructure Security

### Firewall Rules

Restrict access to critical services:

```bash
# Allow only necessary ports
ufw default deny incoming
ufw default allow outgoing

# API server
ufw allow 8000/tcp

# Frontend (if hosting)
ufw allow 3000/tcp

# PostgreSQL (only from app server)
ufw allow from APP_SERVER_IP to any port 5432

# SSH (change default port)
ufw allow 2222/tcp

ufw enable
```

### Docker Security

Run containers as non-root:

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 treasury
USER treasury

# Copy application
WORKDIR /app
COPY --chown=treasury:treasury . .

# Run as non-root
CMD ["python", "-m", "uvicorn", "src.main:app"]
```

**Docker Compose**:
```yaml
services:
  api:
    image: matrix-treasury:latest
    user: "1000:1000"
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
```

### SSL/TLS

Always use HTTPS in production:

```nginx
server {
    listen 443 ssl http2;
    server_name treasury.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Incident Response

### Emergency Procedures

**Killswitch Activation**:
```bash
# Freeze all transactions immediately
curl -X POST http://localhost:8000/api/v1/emergency/killswitch
```

**What the Killswitch Does**:
1. Stops all agent transactions
2. Blocks new withdrawals
3. Pauses CFO approvals
4. Locks treasury operations
5. Sends alerts to all admins

**Recovery Steps**:
1. Identify the threat
2. Secure compromised accounts
3. Rotate all keys
4. Audit recent transactions
5. Resume operations gradually

### Backup Procedures

**Daily Backups**:
```bash
# Database backup
pg_dump treasury > backup_$(date +%Y%m%d).sql

# Encrypt backup
gpg --encrypt --recipient admin@company.com backup_$(date +%Y%m%d).sql

# Upload to secure storage
aws s3 cp backup_$(date +%Y%m%d).sql.gpg s3://backups/treasury/
```

**What to Backup**:
- Database (daily)
- Configuration files (on change)
- Private keys (encrypted, offline)
- Admin settings (encrypted)
- Audit logs (continuous)

### Monitoring & Alerts

Set up alerts for:

```python
# Critical alerts (immediate)
CRITICAL_ALERTS = [
    "treasury_balance_below_threshold",
    "sybil_attack_detected",
    "large_withdrawal_pending",
    "multiple_failed_auth_attempts",
    "killswitch_activated"
]

# Warning alerts (hourly digest)
WARNING_ALERTS = [
    "high_transaction_velocity",
    "approaching_withdrawal_limit",
    "low_gas_balance",
    "failed_blockchain_transaction"
]
```

**Alert Channels**:
- Email (all severity levels)
- SMS (critical only)
- Slack/Discord (warnings)
- PagerDuty (critical, 24/7)

---

## Compliance

### Data Privacy

**GDPR Compliance**:
- Encrypt all PII
- Provide data export functionality
- Implement right to deletion
- Log consent for data processing
- Designate data protection officer

**Data Retention**:
```python
RETENTION_POLICY = {
    "transactions": "7 years",  # Financial regulation
    "audit_logs": "10 years",   # Compliance requirement
    "agent_data": "Until account closure + 1 year",
    "sybil_flags": "5 years"
}
```

### Financial Regulations

**AML/KYC Requirements**:
- Verify agent identities for large transactions
- Monitor for suspicious patterns
- Report transactions above thresholds
- Maintain transaction records

**Tax Reporting**:
- Log all fiat conversions
- Track capital gains/losses
- Generate annual tax reports
- Maintain audit trail

---

## Security Checklist

### Before Deployment

- [ ] All private keys stored in environment variables
- [ ] Encryption key generated and secured
- [ ] Database using SSL connections
- [ ] HTTPS enabled with valid certificate
- [ ] Firewall rules configured
- [ ] Rate limiting enabled
- [ ] CORS restricted to known origins
- [ ] Input validation on all endpoints
- [ ] Audit logging configured
- [ ] Backup system tested
- [ ] Monitoring and alerts set up
- [ ] Incident response plan documented
- [ ] Emergency contacts updated

### Monthly Security Audit

- [ ] Review sybil detection reports
- [ ] Check for failed authentication attempts
- [ ] Audit large transactions
- [ ] Review API key usage
- [ ] Check system logs for anomalies
- [ ] Test backup restoration
- [ ] Update dependencies
- [ ] Rotate API keys
- [ ] Review access permissions

### Quarterly Tasks

- [ ] Rotate blockchain private keys
- [ ] Penetration testing
- [ ] Security training for team
- [ ] Update incident response procedures
- [ ] Review and update access controls
- [ ] Audit third-party integrations
- [ ] Disaster recovery drill

---

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** open a public GitHub issue
2. Email: security@matrix-treasury.com
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

**Bug Bounty**: We reward responsible disclosure.

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [Blockchain Security Best Practices](https://consensys.github.io/smart-contract-best-practices/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
