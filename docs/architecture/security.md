# Security Architecture

## Threat Model

### Assets to Protect
1. **USD Reserves** - Real money backing MXU
2. **Agent Balances** - Financial accounts
3. **Metering Integrity** - Billing accuracy
4. **System Availability** - Service uptime

### Threat Actors
- **Malicious Agents** - Try to steal/inflate MXU
- **External Attackers** - DDoS, injection attacks
- **Compromised Guardians** - Fake metering events
- **Insider Threats** - Operator abuse

## Defense Layers

### Layer 1: Network Security

**TLS/HTTPS Everywhere**
```
All traffic encrypted in transit
Minimum TLS 1.3
Certificate pinning for critical connections
```

**Firewall Rules**
```
Ingress: Only ports 80, 443 from internet
Internal: Service mesh with mTLS
Egress: Whitelist external APIs only
```

**DDoS Protection**
```
CloudFlare / AWS Shield
Rate limiting: 1000 req/min per IP
Connection limits: 100 concurrent per IP
```

### Layer 2: Application Security

**Authentication**
```python
# JWT tokens with short expiry
Access Token: 1 hour expiry
Refresh Token: 30 days expiry
Algorithm: HS256 with secret rotation

# Service accounts
Guardian: Long-lived API keys (rotated monthly)
Admin: MFA required
```

**Authorization**
```python
# Role-based access control
Roles:
  - admin: Full access
  - guardian: Metering submission only
  - agent: Own wallet operations only
  - readonly: Metrics/queries only

# Policy enforcement
def check_permission(user, action, resource):
    if action == "charge_agent":
        return user.role == "guardian"
    if action == "withdraw":
        return user.id == resource.agent_id
    # ... etc
```

**Input Validation**
```python
# Pydantic models enforce schemas
class TransactionRequest(BaseModel):
    from_id: str = Field(..., regex=r'^[a-zA-Z0-9_-]{1,255}$')
    to_id: str = Field(..., regex=r'^[a-zA-Z0-9_-]{1,255}$')
    amount_mxu: float = Field(..., gt=0, lt=1000000)
    
# SQL injection prevention
# Always use parameterized queries via SQLAlchemy ORM
```

**Rate Limiting**
```python
# Per endpoint, per user
@app.post("/api/v1/transactions")
@limiter.limit("10 per minute")
async def transaction(request: TransactionRequest):
    ...

# Adaptive rate limiting
if user.reputation < 0.5:
    limit = "5 per minute"
else:
    limit = "20 per minute"
```

### Layer 3: Data Security

**Encryption at Rest**
```
Database: Transparent Data Encryption (TDE)
Backups: AES-256 encryption
Secrets: AWS Secrets Manager / HashiCorp Vault
```

**Sensitive Data Handling**
```python
# Never log sensitive data
logger.info(f"Transaction processed: {tx_id}")  # Good
logger.info(f"Balance: {balance}")  # Bad!

# Mask in responses
{
    "agent_id": "agent_123",
    "balance": 1000.0,
    "api_key": "sk_****7890"  # Masked
}
```

**Audit Logging**
```python
# All significant actions logged
@audit_log
def charge_agent(agent_id, amount):
    # Logs: timestamp, user, action, resource, result
    ...

# Immutable audit logs
# Append-only table with no UPDATE/DELETE permissions
```

### Layer 4: Metering Integrity

**Guardian Authentication**
```python
# Only authorized guardians can submit metering
def validate_metering(metering: Dict):
    # Check signature
    if not verify_guardian_signature(metering):
        raise MeteringError("Invalid guardian signature")
    
    # Check source
    if metering["metering_source"] != "GUARDIAN":
        raise MeteringError("Invalid metering source")
    
    # Check timestamp (prevent replay)
    if abs(now() - metering["timestamp"]) > 300:  # 5 min
        raise MeteringError("Stale metering event")
```

**Billing Validation**
```python
# Sanity checks on metering
def validate_resource_usage(metering):
    # GPU seconds reasonable?
    if metering["gpu_seconds"] > 86400:  # 24 hours
        flag_for_review(metering)
    
    # Watts reasonable?
    if metering["avg_watts"] > 1000:  # Max GPU watts
        raise MeteringError("Invalid wattage")
    
    # Check historical patterns
    if deviation_from_history(agent_id, metering) > 3σ:
        require_manual_approval(metering)
```

### Layer 5: Economic Integrity

**Constitutional Enforcement**
```python
# Hard-coded limits
MAX_SUPPLY_CONCENTRATION = 0.05  # 5%
MAX_TRANSACTION = 1_000_000  # MXU
MIN_RESERVE_COVERAGE = 1.0

def enforce_constitution(transaction):
    # Check concentration
    new_balance = get_balance(to_id) + amount
    if new_balance / total_supply > MAX_SUPPLY_CONCENTRATION:
        raise ConstitutionalViolation("Supply concentration")
    
    # Check reserves
    if coverage_ratio < MIN_RESERVE_COVERAGE:
        raise ConstitutionalViolation("Reserve depletion")
```

**Sybil Detection**
```python
# Behavioral similarity analysis
def detect_sybil(agent_ids):
    for i, j in combinations(agent_ids, 2):
        similarity = compare_behavior(i, j)
        
        if similarity > SYBIL_THRESHOLD:
            flag_agents([i, j], reason="sybil_suspicion")
            revoke_ubc_eligibility([i, j])

# Graph analysis
def analyze_transaction_graph():
    # Detect circular flows
    # Identify collusion clusters
    # Flag suspicious patterns
```

## Incident Response

### Severity Levels

**P0 - Critical**
- Reserve breach (unauthorized withdrawal)
- Mass balance corruption
- Complete service outage

**P1 - High**
- Single agent balance theft
- Guardian compromise
- Partial service outage

**P2 - Medium**
- Failed authentication attempts (>100/min)
- Unusual transaction patterns
- Performance degradation

**P3 - Low**
- Documentation issues
- Non-critical bugs
- Feature requests

### Response Procedures

**Detection**
```
1. Automated monitoring alerts
2. User reports via support
3. Scheduled security scans
```

**Containment**
```
1. Identify affected systems/users
2. Isolate compromised components
3. Enable emergency mode if needed
4. Preserve forensic evidence
```

**Eradication**
```
1. Remove attacker access
2. Patch vulnerabilities
3. Rotate all credentials
4. Update firewall rules
```

**Recovery**
```
1. Restore from clean backup
2. Verify data integrity
3. Gradually restore service
4. Monitor for reinfection
```

**Post-Mortem**
```
1. Root cause analysis
2. Timeline documentation
3. Impact assessment
4. Prevention measures
5. Update runbooks
```

## Security Checklist

### Development
- [ ] All dependencies scanned (Snyk/Trivy)
- [ ] SAST analysis passed (SonarQube)
- [ ] No secrets in code (git-secrets)
- [ ] Peer review completed

### Deployment
- [ ] Secrets in vault, not env vars
- [ ] TLS certificates valid
- [ ] Firewall rules applied
- [ ] Monitoring alerts configured
- [ ] Backup/restore tested

### Operations
- [ ] Logs monitored (SIEM)
- [ ] Access reviews (quarterly)
- [ ] Penetration test (annually)
- [ ] Credential rotation (monthly)
- [ ] Incident drills (quarterly)

## Compliance

### Data Protection
- GDPR compliant (EU users)
- CCPA compliant (CA users)
- PCI-DSS (if handling cards)

### Financial
- AML/KYC procedures
- Transaction monitoring
- Suspicious activity reporting

### Audit Trail
- All financial transactions logged
- Logs retained 7 years
- Tamper-proof storage
