"""
API endpoints for Mission Control Frontend

Provides real-time monitoring, governance, and chat functionality
for the autonomous Matrix Treasury system.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["autonomous"])


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
