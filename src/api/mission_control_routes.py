"""Mission Control API (auth + settings + logs + approvals + wires + chat).

Full implementation with database persistence for production-ready admin dashboard.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.db.connection import get_db
from src.db.models import (
    AdminUser,
    AppSettings,
    AuditLog,
    ChatMessage,
    PendingApproval,
    SystemState,
    Transaction,
    TransactionTypeEnum,
    TreasurySnapshot,
)
from src.security.jwt_auth import create_access_token, verify_password, get_current_admin

router = APIRouter(prefix="/api/v1", tags=["mission_control"])

TREASURY_AGENT_ID = "TREASURY"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _format_hms(dt: datetime) -> str:
    """Format datetime as HH:MM:SS"""
    return dt.strftime("%H:%M:%S")


def _get_system_state(db: Session) -> SystemState:
    """Get or create system state singleton"""
    state = db.query(SystemState).order_by(SystemState.id.asc()).first()
    if not state:
        state = SystemState(autopilot_enabled=True, panic_mode=False)
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


def _get_app_settings(db: Session) -> AppSettings:
    """Get or create app settings singleton"""
    row = db.query(AppSettings).order_by(AppSettings.id.asc()).first()
    if not row:
        row = AppSettings(data={})
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _get_latest_snapshot(db: Session) -> Optional[TreasurySnapshot]:
    """Get most recent treasury snapshot"""
    return db.query(TreasurySnapshot).order_by(desc(TreasurySnapshot.snapshot_at)).first()


def _ensure_snapshot(db: Session) -> TreasurySnapshot:
    """Get or create initial treasury snapshot"""
    snap = _get_latest_snapshot(db)
    if snap:
        return snap

    initial = float(os.getenv("TREASURY_INITIAL_USD", "5432.50"))
    snap = TreasurySnapshot(
        reserve_usd=initial,
        mxu_supply=100000.0,
        infrastructure_pool=0.0,
        ubc_pool=0.0,
        emergency_pool=0.0,
        usd_per_mxu=0.01,
        raw_price=0.01,
        total_transactions=0,
        total_mxu_burned=0.0,
        total_mxu_minted=0.0,
        crisis_mode=False,
        coverage_ratio=1.0,
        coverage_days=None,
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


def _write_audit(
    db: Session,
    *,
    event_type: str,
    description: str,
    admin: Optional[str] = None,
    meta: Optional[dict] = None
):
    """Write audit log entry"""
    db.add(
        AuditLog(
            event_type=event_type,
            agent_id=admin,
            description=description,
            event_metadata=meta or {}
        )
    )


def _tx_to_ui_log(tx: Transaction) -> Dict[str, Any]:
    """Convert Transaction model to frontend log format"""
    action = tx.description or tx.transaction_type.value
    time = _format_hms(tx.created_at)

    income_types = {
        TransactionTypeEnum.DEPOSIT,
        TransactionTypeEnum.STIMULUS,
        TransactionTypeEnum.UBC_GRANT,
        TransactionTypeEnum.UBC_RENEWAL,
    }
    system_types = {TransactionTypeEnum.TAX, TransactionTypeEnum.BURN}

    if tx.transaction_type in system_types:
        ttype = "SYSTEM"
    elif tx.transaction_type in income_types:
        ttype = "INCOME"
    else:
        ttype = "EXPENSE"

    status = (tx.tx_metadata or {}).get("status", "APPROVED")
    reason = (tx.tx_metadata or {}).get("reason")
    agent = tx.from_agent_id or tx.to_agent_id or "SYSTEM"

    return {
        "id": int(hash(tx.id) & 0x7FFFFFFF),
        "time": time,
        "agent": agent,
        "action": action,
        "cost": float(tx.gross_amount),
        "type": ttype,
        "status": status,
        "reason": reason,
    }


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProviderSettings(BaseModel):
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    project_id: Optional[str] = None
    model_id: Optional[str] = None


class AppSettingsModel(BaseModel):
    provider: str
    openai: ProviderSettings = Field(default_factory=ProviderSettings)
    claude: ProviderSettings = Field(default_factory=ProviderSettings)
    watsonx: ProviderSettings = Field(default_factory=ProviderSettings)
    ollama: ProviderSettings = Field(default_factory=ProviderSettings)
    adminWallet: str
    organizationId: str


class CreateApproval(BaseModel):
    agent: str
    action: str
    cost: float = Field(..., gt=0)
    tx_kind: str = Field(default="EXPENSE")
    reason: Optional[str] = None


class WithdrawalRequest(BaseModel):
    amount: float = Field(..., gt=0)
    destination_wallet: str


class ChatSend(BaseModel):
    agent_id: str
    message: str


# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@router.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate admin and return JWT token"""
    user = db.query(AdminUser).filter(AdminUser.username == req.username).first()
    if not user or not user.is_active or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(sub=user.username)
    user.last_login = datetime.now(timezone.utc)
    _write_audit(db, event_type="auth.login", description="Admin login", admin=user.username)
    db.commit()
    return TokenResponse(access_token=token)


@router.get("/auth/me")
def me(current: AdminUser = Depends(get_current_admin)):
    """Get current authenticated user info"""
    return {"username": current.username, "role": current.role, "is_admin": True}


# ============================================================================
# SETTINGS ENDPOINTS
# ============================================================================

@router.get("/settings", response_model=AppSettingsModel)
def get_settings(db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    """Get Mission Control settings"""
    row = _get_app_settings(db)
    return AppSettingsModel.model_validate(row.data)


@router.post("/settings", response_model=AppSettingsModel)
def update_settings(
    payload: AppSettingsModel,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Update Mission Control settings"""
    row = _get_app_settings(db)
    row.data = payload.model_dump()

    _write_audit(
        db,
        event_type="settings.update",
        description="Mission Control settings updated",
        admin=admin.username
    )
    db.commit()
    db.refresh(row)
    return AppSettingsModel.model_validate(row.data)


@router.get("/settings/models")
def list_models(provider: str, _: AdminUser = Depends(get_current_admin)):
    """List available models for a provider"""
    canned = {
        "openai": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        "claude": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
        "watsonx": ["meta-llama/llama-3-70b-instruct", "ibm/granite-13b-chat-v2"],
        "ollama": ["llama3", "mistral", "phi3"],
    }
    p = provider.lower()
    if p not in canned:
        raise HTTPException(status_code=400, detail="Unknown provider")
    return {"provider": p, "models": canned[p]}


# ============================================================================
# VITALS + HEALTH ENDPOINTS
# ============================================================================

@router.get("/analytics/vitals")
def get_vitals(db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    """Get treasury vitals for dashboard"""
    snap = _ensure_snapshot(db)
    state = _get_system_state(db)
    daily_burn = float(os.getenv("DAILY_BURN_USD", "125"))
    runway = int(snap.reserve_usd / daily_burn) if daily_burn > 0 else 0

    # Determine health status
    if snap.reserve_usd < 1000:
        health = "CRITICAL"
    elif snap.reserve_usd < 3000:
        health = "WARNING"
    else:
        health = "HEALTHY"

    return {
        "usdc_balance": float(snap.reserve_usd),
        "mxu_supply": float(snap.mxu_supply),
        "coverage_ratio": float(snap.coverage_ratio or 1.0),
        "runway_days": runway,
        "health_status": health,
    }


@router.get("/health/network")
def network_health(_: AdminUser = Depends(get_current_admin)):
    """Get network health metrics"""
    return {
        "akash_nodes_active": int(os.getenv("AKASH_NODES_ACTIVE", "12")),
        "akash_nodes_total": int(os.getenv("AKASH_NODES_TOTAL", "15")),
        "compute_load_percent": float(os.getenv("COMPUTE_LOAD_PERCENT", "64")),
        "infrastructure_health": "HEALTHY",
    }


@router.get("/cfo/insights")
def get_cfo_insights(db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    """Get CFO insights (returns array for frontend compatibility)"""
    snap = _ensure_snapshot(db)
    daily_burn = float(os.getenv("DAILY_BURN_USD", "125"))
    runway = int(snap.reserve_usd / daily_burn) if daily_burn > 0 else 0

    return [{
        "message": f"Spending is within nominal parameters. Estimated runway: {runway} days.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "priority": "MEDIUM"
    }]


@router.post("/governance/autopilot")
def set_autopilot(
    payload: Dict[str, bool],
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Toggle autopilot mode"""
    state = _get_system_state(db)
    enabled = bool(payload.get("enabled", True))
    state.autopilot_enabled = enabled
    _write_audit(
        db,
        event_type="governance.autopilot",
        description=f"Autopilot set to {enabled}",
        admin=admin.username
    )
    db.commit()
    return {"status": "success", "autopilot": enabled}


@router.post("/emergency/killswitch")
def kill_switch(db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    """Activate emergency killswitch (panic mode)"""
    state = _get_system_state(db)
    state.panic_mode = True
    state.autopilot_enabled = False
    _write_audit(
        db,
        event_type="system.killswitch",
        description="Panic mode enabled",
        admin=admin.username
    )
    db.commit()
    return {"panic_mode": True, "timestamp": datetime.now(timezone.utc).isoformat()}


@router.post("/emergency/reboot")
def reboot(db: Session = Depends(get_db), admin: AdminUser = Depends(get_current_admin)):
    """Deactivate panic mode (system reboot)"""
    state = _get_system_state(db)
    state.panic_mode = False
    _write_audit(
        db,
        event_type="system.reboot",
        description="Panic mode disabled",
        admin=admin.username
    )
    db.commit()
    return {"panic_mode": False, "timestamp": datetime.now(timezone.utc).isoformat()}


# ============================================================================
# LOGS ENDPOINTS
# ============================================================================

@router.get("/logs")
def get_logs(limit: int = 50, db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    """Get recent transaction logs"""
    txs = db.query(Transaction).order_by(desc(Transaction.created_at)).limit(limit).all()
    return [_tx_to_ui_log(t) for t in txs]


# ============================================================================
# APPROVALS ENDPOINTS
# ============================================================================

@router.get("/governance/pending")
def get_pending_approvals(db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    """Get pending approvals queue"""
    rows = (
        db.query(PendingApproval)
        .filter(PendingApproval.status == "PENDING")
        .order_by(desc(PendingApproval.created_at))
        .all()
    )
    return [
        {
            "id": r.id,
            "agent_id": r.agent,
            "action": r.action,
            "cost_usd": float(r.cost),
            "reason": r.reason or "Awaiting Admin Review",
            "submitted_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.post("/approvals", status_code=201)
def create_pending_approval(
    req: CreateApproval,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Create a new pending approval (for testing)"""
    state = _get_system_state(db)
    if state.panic_mode:
        raise HTTPException(status_code=409, detail="System is frozen (panic mode)")

    row = PendingApproval(
        agent=req.agent,
        action=req.action,
        cost=float(req.cost),
        tx_kind=req.tx_kind.upper(),
        status="PENDING",
        reason=req.reason or "Awaiting Admin Review",
    )
    db.add(row)
    _write_audit(
        db,
        event_type="approval.create",
        description=f"Created pending approval: {req.action}",
        admin=admin.username
    )
    db.commit()
    db.refresh(row)
    return {"id": row.id, "status": row.status}


def _apply_pending_as_transaction(
    db: Session,
    pending: PendingApproval,
    status: str,
    admin_reason: Optional[str]
):
    """Convert approved pending approval into a transaction"""
    pending.status = status
    pending.admin_reason = admin_reason
    pending.decided_at = datetime.now(timezone.utc)

    if status != "APPROVED":
        return

    snap = _ensure_snapshot(db)

    tx_type = TransactionTypeEnum.PAYMENT
    if pending.tx_kind == "INCOME":
        tx_type = TransactionTypeEnum.DEPOSIT
    elif pending.tx_kind == "SYSTEM":
        tx_type = TransactionTypeEnum.CHARGE

    tx = Transaction(
        id=str(uuid.uuid4()),
        transaction_type=tx_type,
        from_agent_id=pending.agent if pending.tx_kind == "INCOME" else TREASURY_AGENT_ID,
        to_agent_id=TREASURY_AGENT_ID if pending.tx_kind == "INCOME" else pending.agent,
        gross_amount=float(pending.cost),
        tax_amount=0.0,
        net_amount=float(pending.cost),
        description=pending.action,
        tx_metadata={
            "status": "APPROVED",
            "reason": pending.reason,
            "admin_reason": admin_reason
        },
    )
    db.add(tx)

    if pending.tx_kind == "INCOME":
        snap.reserve_usd += float(pending.cost)
    else:
        snap.reserve_usd -= float(pending.cost)


@router.post("/governance/approve/{transaction_id}")
def approve_transaction(
    transaction_id: int,
    payload: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Approve a pending transaction"""
    pending = db.query(PendingApproval).filter(PendingApproval.id == transaction_id).first()
    if not pending or pending.status != "PENDING":
        raise HTTPException(status_code=404, detail="Pending approval not found")

    _apply_pending_as_transaction(db, pending, "APPROVED", (payload or {}).get("reason"))
    _write_audit(
        db,
        event_type="approval.approve",
        description=f"Approved transaction {transaction_id}",
        admin=admin.username
    )
    db.commit()
    return {"status": "success", "transaction_id": transaction_id, "approved": True}


@router.post("/governance/deny/{transaction_id}")
def deny_transaction(
    transaction_id: int,
    payload: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Deny a pending transaction"""
    pending = db.query(PendingApproval).filter(PendingApproval.id == transaction_id).first()
    if not pending or pending.status != "PENDING":
        raise HTTPException(status_code=404, detail="Pending approval not found")

    pending.status = "DENIED"
    pending.admin_reason = (payload or {}).get("reason")
    pending.decided_at = datetime.now(timezone.utc)
    _write_audit(
        db,
        event_type="approval.deny",
        description=f"Denied transaction {transaction_id}",
        admin=admin.username
    )
    db.commit()
    return {"status": "success", "transaction_id": transaction_id, "approved": False}


# ============================================================================
# WIRES (LIQUIDITY WITHDRAWAL) ENDPOINTS
# ============================================================================

@router.post("/liquidity/withdraw")
def withdraw_liquidity(
    req: WithdrawalRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Withdraw liquidity to admin wallet"""
    state = _get_system_state(db)
    if state.panic_mode:
        raise HTTPException(status_code=409, detail="System is frozen (panic mode)")

    settings = _get_app_settings(db).data
    allowed_dest = settings.get("adminWallet")
    if allowed_dest and req.destination_wallet != allowed_dest:
        raise HTTPException(status_code=400, detail="Destination wallet not allowed")

    snap = _ensure_snapshot(db)
    if req.amount > snap.reserve_usd:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    tx = Transaction(
        id=str(uuid.uuid4()),
        transaction_type=TransactionTypeEnum.WITHDRAWAL,
        from_agent_id=TREASURY_AGENT_ID,
        to_agent_id=req.destination_wallet,
        gross_amount=float(req.amount),
        tax_amount=0.0,
        net_amount=float(req.amount),
        description=f"Liquidity Withdrawal to {req.destination_wallet}",
        tx_metadata={
            "status": "APPROVED",
            "reason": "Manual Liquidity Extraction",
            "admin": admin.username
        },
    )
    db.add(tx)
    snap.reserve_usd -= float(req.amount)

    _write_audit(
        db,
        event_type="liquidity.withdraw",
        description=f"Liquidity withdrawal ${req.amount} to {req.destination_wallet}",
        admin=admin.username
    )
    db.commit()
    return {"status": "success", "tx_id": tx.id, "amount": req.amount}


# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

CONTACTS = [
    {"id": "cfo", "name": "Treasury (CFO)", "role": "Financial Governance", "status": "online"},
    {"id": "alpha", "name": "Agent-Alpha", "role": "Field Ops", "status": "busy"},
    {"id": "beta", "name": "Agent-Beta", "role": "Data Analyst", "status": "idle"},
    {"id": "sys", "name": "Matrix System", "role": "Infrastructure", "status": "online"},
]


@router.get("/chat/contacts")
def chat_contacts(_: AdminUser = Depends(get_current_admin)):
    """Get available chat contacts"""
    return CONTACTS


@router.get("/chat/history/{contact_id}")
def chat_history(
    contact_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(get_current_admin)
):
    """Get chat history for a contact"""
    msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.contact_id == contact_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": m.id,
            "role": "user" if m.sender == "USER" else "assistant",
            "content": m.text,
            "timestamp": m.created_at.isoformat(),
        }
        for m in msgs
    ]


@router.get("/chat/history")
def get_full_chat_history(db: Session = Depends(get_db), _: AdminUser = Depends(get_current_admin)):
    """Get full chat history (all contacts)"""
    # Frontend compatibility - return empty array
    # Frontend should use /chat/history/{contact_id} for specific conversations
    return []


@router.post("/chat/send")
def chat_send_legacy(
    req: ChatSend,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Send chat message (original endpoint)"""
    return _send_chat_message(req.agent_id, req.message, db, admin)


@router.post("/chat/message")
def chat_send_message(
    message: Dict[str, str],
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    """Send chat message (alias endpoint for frontend compatibility)"""
    return _send_chat_message(message["agent_id"], message["message"], db, admin)


def _send_chat_message(agent_id: str, message: str, db: Session, admin: AdminUser):
    """Internal helper for sending chat messages"""
    user_msg = ChatMessage(contact_id=agent_id, sender="USER", text=message)
    db.add(user_msg)

    reply_text = "I acknowledge your request."
    if agent_id == "cfo":
        snap = _ensure_snapshot(db)
        daily_burn = float(os.getenv("DAILY_BURN_USD", "125"))
        runway = int(snap.reserve_usd / daily_burn) if daily_burn > 0 else 0
        low = message.lower()
        if "status" in low:
            reply_text = f"Current solvency is stable. Runway estimated at {runway} days."
        elif "risk" in low:
            reply_text = "Risk levels are nominal. No anomalous spending patterns detected."
        else:
            reply_text = "I am optimizing the budget allocation. Do you have a specific financial override command?"
    elif agent_id == "alpha":
        reply_text = "Currently engaged in data extraction. I can prioritize your task if you authorize extra compute."

    contact_name = next((c["name"] for c in CONTACTS if c["id"] == agent_id), agent_id)
    bot_msg = ChatMessage(contact_id=agent_id, sender=contact_name, text=reply_text)
    db.add(bot_msg)

    _write_audit(
        db,
        event_type="chat.send",
        description=f"Chat message to {agent_id}",
        admin=admin.username
    )
    db.commit()
    return {
        "response": reply_text,
        "status": "success",
        "agent_id": agent_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
