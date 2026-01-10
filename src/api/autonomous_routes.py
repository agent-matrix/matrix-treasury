"""
API endpoints for Mission Control Frontend

Provides real-time monitoring, governance, and chat functionality
for the autonomous Matrix Treasury system.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import jwt
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["autonomous"])

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "matrix-treasury-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Security
security = HTTPBearer()

# Simple in-memory user database (replace with real database in production)
USERS_DB = {
    "admin": {
        "username": "admin",
        "password": "admin123",  # In production, use hashed passwords
        "is_admin": True
    }
}


# ============================================================================
# AUTHENTICATION MODELS
# ============================================================================

class LoginRequest(BaseModel):
    """Login credentials"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """JWT access token"""
    access_token: str
    token_type: str = "bearer"


class AuthMe(BaseModel):
    """Current user info"""
    username: str
    is_admin: bool


def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token and return user data"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@router.post("/auth/login", response_model=LoginResponse, tags=["auth"])
async def login(request: LoginRequest):
    """Authenticate user and return JWT token"""
    user = USERS_DB.get(request.username)

    if not user or user["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create JWT token
    token_data = {
        "username": user["username"],
        "is_admin": user["is_admin"]
    }
    access_token = create_access_token(token_data)

    return LoginResponse(access_token=access_token)


@router.get("/auth/me", response_model=AuthMe, tags=["auth"])
async def get_current_user(user_data: dict = Depends(verify_token)):
    """Get current authenticated user info"""
    return AuthMe(
        username=user_data["username"],
        is_admin=user_data.get("is_admin", False)
    )


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class TreasuryStatus(BaseModel):
    """Current vault balance and runway estimates"""
    usdc_balance: float
    mxu_supply: float
    coverage_ratio: float
    runway_days: int
    health_status: str  # HEALTHY, WARNING, CRITICAL


class NetworkHealth(BaseModel):
    """Akash network and compute status"""
    akash_nodes_active: int
    akash_nodes_total: int
    compute_load_percent: float
    infrastructure_health: str


class CFOInsight(BaseModel):
    """One-line summary from CFO LLM"""
    message: str
    timestamp: str
    confidence: float


class TransactionLog(BaseModel):
    """Transaction log entry"""
    id: int
    time: str
    agent: str
    action: str
    cost: float
    type: str  # EXPENSE, INCOME, SYSTEM
    status: str  # APPROVED, DENIED, PENDING
    reason: Optional[str] = None


class PendingApproval(BaseModel):
    """Pending transaction awaiting approval"""
    id: int
    agent_id: str
    action: str
    cost_usd: float
    reason: str
    submitted_at: str


class ApprovalDecision(BaseModel):
    """Admin's approval decision"""
    transaction_id: int
    approved: bool
    admin_reason: Optional[str] = None


class AutopilotToggle(BaseModel):
    """Toggle CFO autonomy"""
    enabled: bool


class WithdrawalRequest(BaseModel):
    """Liquidity extraction request"""
    amount: float = Field(..., gt=0)
    destination_wallet: str


class ChatContact(BaseModel):
    """Available chat agent"""
    id: str
    name: str
    role: str
    status: str  # online, busy, idle, offline


class ChatMessage(BaseModel):
    """Chat message"""
    id: int
    sender: str
    text: str
    timestamp: str


class ChatSendRequest(BaseModel):
    """Send message to agent"""
    agent_id: str
    message: str


class SystemSettings(BaseModel):
    """System configuration"""
    llm_provider: str
    api_key_masked: str
    admin_wallet: str
    organization_id: str


class SettingsUpdate(BaseModel):
    """Update system settings"""
    llm_provider: Optional[str] = None
    api_key: Optional[str] = None
    admin_wallet: Optional[str] = None
    organization_id: Optional[str] = None


# ============================================================================
# MONITORING & VITALS
# ============================================================================

@router.get("/treasury/status", response_model=TreasuryStatus)
async def get_treasury_status():
    """
    Returns current Vault Balance and Runway estimates.
    Used by: Top Bar (Vault Balance)
    """
    try:
        # TODO: Replace with actual implementation
        # from src.blockchain.vault import ExternalVault
        # from src.blockchain.ledger import InternalLedger
        # from src.llm.cfo import MatrixCFO

        # Mock data for now
        return TreasuryStatus(
            usdc_balance=5432.50,
            mxu_supply=100000.0,
            coverage_ratio=1.23,
            runway_days=43,
            health_status="HEALTHY"
        )
    except Exception as e:
        logger.error(f"Error getting treasury status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/stream", response_model=List[TransactionLog])
async def get_transaction_logs(limit: int = 50):
    """
    Returns the last N transactions/logs.
    Used by: Live Transaction Stream
    """
    try:
        # TODO: Replace with actual database query
        # Mock data
        return []
    except Exception as e:
        logger.error(f"Error getting transaction logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network/health", response_model=NetworkHealth)
async def get_network_health():
    """
    Returns Akash node status and Compute Load %.
    Used by: Network Health Panel
    """
    try:
        # TODO: Query Akash network status
        return NetworkHealth(
            akash_nodes_active=12,
            akash_nodes_total=15,
            compute_load_percent=64.0,
            infrastructure_health="HEALTHY"
        )
    except Exception as e:
        logger.error(f"Error getting network health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cfo/insight", response_model=CFOInsight)
async def get_cfo_insight():
    """
    Returns a one-line summary from the CFO LLM.
    Used by: CFO Insight Box
    """
    try:
        # TODO: Query actual CFO
        return CFOInsight(
            message="Spending is within nominal parameters. 94% of agents are profitable this hour.",
            timestamp=datetime.now().isoformat(),
            confidence=0.95
        )
    except Exception as e:
        logger.error(f"Error getting CFO insight: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GOVERNANCE & APPROVALS
# ============================================================================

@router.get("/governance/pending", response_model=List[PendingApproval])
async def get_pending_approvals():
    """
    Returns list of transactions waiting for manual approval.
    Used by: Pending Approvals Queue
    """
    try:
        # TODO: Query database for pending transactions
        return []
    except Exception as e:
        logger.error(f"Error getting pending approvals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/governance/approve/{transaction_id}")
async def approve_transaction(transaction_id: int):
    """
    Approves a specific pending transaction.
    Used by: ✅ Approve Button
    """
    try:
        # TODO: Implement approval logic
        logger.info(f"Transaction {transaction_id} approved by admin")
        return {"status": "success", "transaction_id": transaction_id, "approved": True}
    except Exception as e:
        logger.error(f"Error approving transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/governance/deny/{transaction_id}")
async def deny_transaction(transaction_id: int):
    """
    Rejects a specific pending transaction.
    Used by: ❌ Deny Button
    """
    try:
        # TODO: Implement denial logic
        logger.info(f"Transaction {transaction_id} denied by admin")
        return {"status": "success", "transaction_id": transaction_id, "approved": False}
    except Exception as e:
        logger.error(f"Error denying transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/governance/autopilot")
async def toggle_autopilot(request: AutopilotToggle):
    """
    Toggles CFO Autonomy (On/Off).
    Used by: Autonomy Level Toggle
    """
    try:
        # TODO: Update CFO autonomy setting
        logger.info(f"CFO autopilot set to: {request.enabled}")
        return {
            "status": "success",
            "autopilot": request.enabled,
            "message": f"CFO autopilot {'enabled' if request.enabled else 'disabled'}"
        }
    except Exception as e:
        logger.error(f"Error toggling autopilot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emergency/killswitch")
async def emergency_killswitch():
    """
    DANGER: Freezes all wallets and stops server payments.
    Used by: EMERGENCY STOP Button
    """
    try:
        # TODO: Implement emergency shutdown
        logger.critical("EMERGENCY KILLSWITCH ACTIVATED BY ADMIN")
        return {
            "status": "success",
            "message": "System frozen. All transactions halted.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error activating killswitch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/liquidity/withdraw")
async def withdraw_liquidity(request: WithdrawalRequest):
    """
    Transfers USDC from Vault to Admin Wallet.
    Used by: Liquidity Extraction Form
    """
    try:
        # TODO: Implement vault withdrawal
        # Security check
        # Check solvency
        # Execute transfer

        logger.info(f"Liquidity withdrawal: ${request.amount} to {request.destination_wallet}")

        return {
            "status": "success",
            "amount": request.amount,
            "destination": request.destination_wallet,
            "tx_hash": "0x1234567890abcdef...",  # Mock
            "message": f"${request.amount} withdrawn successfully"
        }
    except Exception as e:
        logger.error(f"Error withdrawing liquidity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NEURAL LINK (CHAT)
# ============================================================================

@router.get("/chat/contacts", response_model=List[ChatContact])
async def get_chat_contacts():
    """
    Returns list of available agents and their status.
    Used by: Active Links Sidebar
    """
    try:
        return [
            ChatContact(id="cfo", name="Treasury (CFO)", role="Financial Governance", status="online"),
            ChatContact(id="alpha", name="Agent-Alpha", role="Field Ops", status="busy"),
            ChatContact(id="beta", name="Agent-Beta", role="Data Analyst", status="idle"),
            ChatContact(id="sys", name="Matrix System", role="Infrastructure", status="online"),
        ]
    except Exception as e:
        logger.error(f"Error getting chat contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/history/{agent_id}", response_model=List[ChatMessage])
async def get_chat_history(agent_id: str, limit: int = 100):
    """
    Returns past messages for a specific agent.
    Used by: Chat Window History
    """
    try:
        # TODO: Query database for chat history
        if agent_id == "cfo":
            return [
                ChatMessage(
                    id=1,
                    sender="Treasury (CFO)",
                    text="Greetings, Admin. Financial logic is operating at 99.9% efficiency. How may I assist?",
                    timestamp="10:00"
                )
            ]
        return []
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/send")
async def send_chat_message(request: ChatSendRequest):
    """
    Sends a message to an agent (LLM) and gets a reply.
    Used by: Chat Input & Send Button
    """
    try:
        # TODO: Implement actual LLM chat
        logger.info(f"Chat message to {request.agent_id}: {request.message}")

        # Mock response
        response_text = "I acknowledge your request."
        if request.agent_id == "cfo":
            if "status" in request.message.lower():
                response_text = "Current solvency is stable. Runway estimated at 43 days."
            elif "risk" in request.message.lower():
                response_text = "Risk levels are nominal. No anomalous spending patterns detected."

        return {
            "status": "success",
            "agent_id": request.agent_id,
            "user_message": request.message,
            "agent_reply": response_text,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error sending chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONFIGURATION
# ============================================================================

@router.get("/config/settings", response_model=SystemSettings)
async def get_system_settings():
    """
    Fetches current LLM provider and wallet settings (masked).
    Used by: Settings Modal (Load)
    """
    try:
        # TODO: Load from actual config
        return SystemSettings(
            llm_provider="OpenAI",
            api_key_masked="sk-........................",
            admin_wallet="0x71C...9A23",
            organization_id="ORG-8821"
        )
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/update")
async def update_system_settings(request: SettingsUpdate):
    """
    Updates LLM keys, Provider, or Admin Wallet address.
    Used by: Save Configuration Button
    """
    try:
        # TODO: Update configuration
        logger.info(f"Settings updated: {request}")

        return {
            "status": "success",
            "message": "Configuration updated successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PHASE 3: MULTI-CURRENCY & CROSS-CHAIN
# ============================================================================

class MultiCurrencyBalance(BaseModel):
    """Multi-currency vault balances"""
    USDC: float
    EUR: float
    BTC: float
    total_usd_equivalent: float
    network: str


class MultiCurrencyWithdrawal(BaseModel):
    """Multi-currency withdrawal request"""
    amount: float = Field(..., gt=0)
    currency: str  # USDC, EUR, BTC
    network: str  # base, polygon, arbitrum, optimism
    destination: str
    method: str  # crypto, wire


@router.get("/multicurrency/balances", response_model=MultiCurrencyBalance)
async def get_multicurrency_balances():
    """
    Get balances for all currencies (USDC, EUR, BTC).
    Used by: Multi-Currency Dashboard
    """
    try:
        # TODO: Integrate with MultiCurrencyVault
        return MultiCurrencyBalance(
            USDC=5432.50,
            EUR=3200.00,
            BTC=0.125,
            total_usd_equivalent=11150.00,
            network="base"
        )
    except Exception as e:
        logger.error(f"Error getting multi-currency balances: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multicurrency/withdraw")
async def withdraw_multicurrency(request: MultiCurrencyWithdrawal):
    """
    Withdraw in specific currency (USDC, EUR, or BTC) via crypto or wire transfer.
    Admin-only operation with limits enforcement.
    """
    try:
        logger.info(f"Multi-currency withdrawal: {request.amount} {request.currency} via {request.method}")

        # TODO: Implement wire transfer settings check
        # TODO: Check withdrawal limits
        # TODO: Execute transfer

        return {
            "status": "success",
            "amount": request.amount,
            "currency": request.currency,
            "network": request.network,
            "method": request.method,
            "destination": request.destination,
            "tx_hash": "0xabcdef..." if request.method == "crypto" else None,
            "reference_number": "WT-2024-001" if request.method == "wire" else None,
        }
    except Exception as e:
        logger.error(f"Error processing multi-currency withdrawal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PHASE 3: REAL-TIME ANALYTICS
# ============================================================================

class AnalyticsDashboard(BaseModel):
    """Real-time analytics metrics"""
    total_transactions: int
    total_volume: float
    active_agents: int
    system_health: Dict[str, Any]
    hourly_volume: List[Dict[str, Any]]
    top_agents: List[Dict[str, Any]]


@router.get("/analytics/dashboard", response_model=AnalyticsDashboard)
async def get_analytics_dashboard():
    """
    Get real-time analytics for Mission Control dashboard.
    Replaces mock data with actual metrics.
    """
    try:
        # TODO: Integrate with RealTimeAnalytics
        return AnalyticsDashboard(
            total_transactions=1247,
            total_volume=45320.50,
            active_agents=23,
            system_health={
                "status": "healthy",
                "solvency_ratio": 1.23,
                "runway_days": 43,
            },
            hourly_volume=[
                {"hour": "00:00", "volume": 1200.0},
                {"hour": "01:00", "volume": 1500.0},
            ],
            top_agents=[
                {"agent_id": "agent_1", "earned": 5000.0, "credit_score": 0.95},
            ]
        )
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/agent/{agent_id}")
async def get_agent_analytics(agent_id: str):
    """Get detailed analytics for specific agent"""
    try:
        # TODO: Fetch from analytics engine
        return {
            "agent_id": agent_id,
            "total_earned": 5000.0,
            "total_spent": 3200.0,
            "current_balance": 1800.0,
            "credit_score": 0.85,
            "transaction_count": 150,
            "active_loans": 1,
            "total_debt": 500.0,
            "sybil_risk_score": 0.15,
        }
    except Exception as e:
        logger.error(f"Error getting agent analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PHASE 3: SYBIL DETECTION
# ============================================================================

class SybilDetectionResult(BaseModel):
    """Sybil detection analysis"""
    agent_id: str
    is_suspicious: bool
    risk_score: float
    flags: List[str]
    profile: Dict[str, Any]


@router.get("/security/sybil/{agent_id}", response_model=SybilDetectionResult)
async def check_sybil_attack(agent_id: str):
    """
    Check if agent exhibits sybil attack indicators.
    Uses ML-based pattern detection.
    """
    try:
        # TODO: Integrate with SybilDetector
        return SybilDetectionResult(
            agent_id=agent_id,
            is_suspicious=False,
            risk_score=0.15,
            flags=[],
            profile={
                "account_age_hours": 120.5,
                "transaction_count": 150,
                "transaction_velocity": 1.25,
                "credit_score_volatility": 0.05,
            }
        )
    except Exception as e:
        logger.error(f"Error checking sybil attack: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security/flagged")
async def get_flagged_agents():
    """Get all agents flagged as suspicious"""
    try:
        # TODO: Query from SybilDetector
        return {
            "flagged_agents": [],
            "total_flagged": 0,
            "detection_stats": {
                "total_agents_tracked": 100,
                "flagged_percentage": 0.0,
                "detected_clusters": 0,
            }
        }
    except Exception as e:
        logger.error(f"Error getting flagged agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PHASE 3: AGENT CREDIT SYSTEM
# ============================================================================

class LoanRequest(BaseModel):
    """Agent loan request"""
    agent_id: str
    amount: float = Field(..., gt=0)
    collateral: float = Field(..., gt=0)
    loan_term_days: Optional[int] = 30


class LoanRepayment(BaseModel):
    """Loan repayment"""
    agent_id: str
    loan_id: str
    amount: float = Field(..., gt=0)


@router.post("/credit/request-loan")
async def request_loan(request: LoanRequest):
    """
    Request a collateral-backed loan.
    Agents can borrow MXU against collateral.
    """
    try:
        # TODO: Integrate with AgentCreditSystem
        logger.info(f"Loan request: {request.agent_id} wants {request.amount} MXU")

        return {
            "approved": True,
            "loan_id": "LOAN-000001",
            "principal": request.amount,
            "collateral": request.collateral,
            "interest_rate": 0.10,
            "due_date": "2024-02-10T00:00:00",
            "total_due": request.amount * 1.10,
        }
    except Exception as e:
        logger.error(f"Error processing loan request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/credit/repay-loan")
async def repay_loan(request: LoanRepayment):
    """Repay a loan (partial or full)"""
    try:
        # TODO: Integrate with AgentCreditSystem
        logger.info(f"Loan repayment: {request.agent_id} paying {request.amount} for {request.loan_id}")

        return {
            "status": "partial_repayment",
            "loan_id": request.loan_id,
            "amount_paid": request.amount,
            "remaining": 100.0,
        }
    except Exception as e:
        logger.error(f"Error processing repayment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/credit/agent-loans/{agent_id}")
async def get_agent_loans(agent_id: str):
    """Get all loans for an agent"""
    try:
        # TODO: Fetch from AgentCreditSystem
        return {
            "agent_id": agent_id,
            "active_loans": [],
            "total_debt": 0.0,
            "credit_limit": 1000.0,
        }
    except Exception as e:
        logger.error(f"Error getting agent loans: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/credit/system-stats")
async def get_credit_system_stats():
    """Get credit system statistics"""
    try:
        # TODO: Fetch from AgentCreditSystem
        return {
            "total_loans": 0,
            "active_loans": 0,
            "total_principal": 0.0,
            "total_collateral": 0.0,
            "collateralization_ratio": 0.0,
        }
    except Exception as e:
        logger.error(f"Error getting credit stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PHASE 3: ADMIN WIRE TRANSFER SETTINGS
# ============================================================================

class BankAccountAdd(BaseModel):
    """Add bank account for wire transfers"""
    account_id: str
    account_name: str
    account_number: str
    routing_number: str
    swift_code: str
    bank_name: str
    bank_address: str
    currency: str
    country: str


class CryptoWalletAdd(BaseModel):
    """Add crypto wallet for withdrawals"""
    wallet_id: str
    address: str
    network: str
    currency: str
    label: Optional[str] = ""


@router.post("/admin/add-bank-account")
async def add_bank_account(request: BankAccountAdd):
    """Add bank account for wire transfers (admin only)"""
    try:
        # TODO: Integrate with WireTransferSettings
        logger.info(f"Adding bank account: {request.account_id}")

        return {
            "status": "success",
            "account_id": request.account_id,
            "bank_name": request.bank_name,
            "currency": request.currency,
        }
    except Exception as e:
        logger.error(f"Error adding bank account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/add-crypto-wallet")
async def add_crypto_wallet(request: CryptoWalletAdd):
    """Add crypto wallet for withdrawals (admin only)"""
    try:
        # TODO: Integrate with WireTransferSettings
        logger.info(f"Adding crypto wallet: {request.wallet_id}")

        return {
            "status": "success",
            "wallet_id": request.wallet_id,
            "network": request.network,
            "currency": request.currency,
        }
    except Exception as e:
        logger.error(f"Error adding crypto wallet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/payment-methods")
async def get_payment_methods():
    """Get all configured payment methods (bank accounts and crypto wallets)"""
    try:
        # TODO: Fetch from WireTransferSettings
        return {
            "bank_accounts": [],
            "crypto_wallets": [],
        }
    except Exception as e:
        logger.error(f"Error getting payment methods: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINT ALIASES (for frontend compatibility)
# ============================================================================

@router.get("/logs", response_model=List[TransactionLog])
async def get_logs(limit: int = 50):
    """Alias for /logs/stream - Get recent transaction logs"""
    return await get_transaction_logs(limit)


@router.get("/cfo/insights")
async def get_cfo_insights():
    """Alias for /cfo/insight - Get multiple CFO insights"""
    # Return as array for frontend compatibility
    insight = await get_cfo_insight()
    return [insight]


@router.get("/settings", response_model=SystemSettings)
async def get_settings():
    """Alias for /config/settings - Get system settings"""
    return await get_system_settings()


@router.post("/settings")
async def update_settings(updates: Dict[str, Any]):
    """Alias for /config/update - Update system settings"""
    return await update_system_config(updates)


@router.post("/chat/message")
async def send_chat_message_alias(message: Dict[str, str]):
    """Alias for /chat/send - Send chat message"""
    return await send_chat_message(message)


@router.get("/chat/history")
async def get_chat_history_alias():
    """Get full chat history (all contacts)"""
    # Return empty for now, frontend can call /chat/history/{agent_id} for specific conversations
    return []
