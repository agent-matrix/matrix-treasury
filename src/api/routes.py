"""
FastAPI routes for Matrix Treasury
FIXED: Updated to use 'agent_metadata' instead of 'metadata'
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import asyncio
import json
from datetime import datetime

from src.api.schemas import *
from src.core.economy import AutoselfEconomy
from src.core.exceptions import *
from src.db.connection import get_db
from src.db import models

logger = logging.getLogger(__name__)

# Global economy instance (in production, this would be dependency-injected)
economy = AutoselfEconomy()

# Create router
router = APIRouter()

# ==============================================================================
# HEALTH & STATUS
# ==============================================================================

@router.get("/", response_model=HealthResponse)
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "system": "Matrix Treasury (AUTOSelf v4.0)",
        "version": "4.0.0",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get treasury metrics"""
    state = economy.treasury.get_state()
    return {
        "supply": state["mxu_supply"],
        "reserves": state["reserve_usd"],
        "pools": state["pools"],
        "price_usd": state["pricing"]["usd_per_mxu"],
        "mxu_per_usd": state["pricing"]["mxu_per_usd"],
        "crisis_mode": state["metrics"]["crisis_mode"],
        "total_transactions": state["metrics"]["total_transactions"],
        "total_burned": state["metrics"]["total_mxu_burned"],
        "total_minted": state["metrics"]["total_mxu_minted"]
    }

@router.get("/economy/metrics", response_model=EconomicMetricsResponse)
async def get_economic_metrics():
    """Get economic health metrics"""
    return economy.calculate_economic_metrics()

@router.get("/health/reserves", response_model=ReserveHealthResponse)
async def get_reserve_health():
    """Get reserve health status"""
    projected_burn = economy.treasury.total_mxu_burned / max(1, 30)
    health = economy.treasury.reserve_health(projected_burn)
    return health

# ==============================================================================
# AGENT LIFECYCLE
# ==============================================================================

@router.post("/agents/onboard", response_model=OnboardResponse)
async def onboard_agent(request: OnboardRequest, db: Session = Depends(get_db)):
    """Onboard new agent with UBC grant"""
    try:
        result = economy.onboard_agent(request.agent_id)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        
        # Persist to database
        agent = models.Agent(
            id=request.agent_id,
            agent_type=request.agent_type,
            balance=result["balance"],
            reputation=0.0,
            status=models.AgentStatusEnum.ACTIVE,
            agent_metadata=request.metadata  # ✅ FIXED: was 'metadata'
        )
        db.add(agent)
        
        # Log UBC grant transaction
        if result["ubc_granted"] > 0:
            tx = models.Transaction(
                id=f"tx_ubc_{request.agent_id}_{datetime.now().timestamp()}",
                transaction_type=models.TransactionTypeEnum.UBC_GRANT,
                to_agent_id=request.agent_id,
                gross_amount=result["ubc_granted"],
                net_amount=result["ubc_granted"]
            )
            db.add(tx)
        
        db.commit()
        
        return result
        
    except Exception as e:
        db.rollback()
        logger.error(f"Onboarding error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get agent details"""
    agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "id": agent.id,
        "agent_type": agent.agent_type,
        "balance": agent.balance,
        "reputation": agent.reputation,
        "status": agent.status.value,
        "ubc_renewals_used": agent.ubc_renewals_used,
        "last_ubc_renewal": agent.last_ubc_renewal.isoformat() if agent.last_ubc_renewal else None,
        "last_activity": agent.last_activity.isoformat(),
        "created_at": agent.created_at.isoformat()
    }

@router.post("/agents/ubc-renewal", response_model=dict)
async def renew_ubc(request: UBCRenewalRequest):
    """Request UBC renewal"""
    try:
        result = economy.renew_ubc_if_eligible(request.agent_id)
        return result
    except Exception as e:
        logger.error(f"UBC renewal error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================================
# FINANCIAL OPERATIONS
# ==============================================================================

@router.post("/deposits", response_model=DepositResponse)
async def deposit_usd(request: DepositRequest, db: Session = Depends(get_db)):
    """Deposit USD and mint MXU"""
    try:
        result = economy.deposit_usd(request.user_id, request.amount_usd)
        
        # Update database
        agent = db.query(models.Agent).filter(models.Agent.id == request.user_id).first()
        if agent:
            agent.balance = result["new_balance"]
            agent.last_activity = datetime.now()
        
        # Log transaction
        tx = models.Transaction(
            id=f"tx_deposit_{request.user_id}_{datetime.now().timestamp()}",
            transaction_type=models.TransactionTypeEnum.DEPOSIT,
            to_agent_id=request.user_id,
            gross_amount=result["mxu_received"],
            net_amount=result["mxu_received"],
            tx_metadata={"usd_amount": request.amount_usd}  # ✅ FIXED
        )
        db.add(tx)
        db.commit()
        
        return result
        
    except Exception as e:
        db.rollback()
        logger.error(f"Deposit error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/billing/charge", response_model=BillingResponse)
async def charge_agent(request: BillingRequest, db: Session = Depends(get_db)):
    """Bill agent for computational work"""
    try:
        result = economy.charge_for_work(request.agent_id, request.metering)
        
        # Update database
        agent = db.query(models.Agent).filter(models.Agent.id == request.agent_id).first()
        if agent:
            agent.balance = result["new_balance"]
            agent.status = models.AgentStatusEnum(result["agent_status"])
            agent.last_activity = datetime.now()
        
        # Create billing record
        billing = models.BillingRecord(
            id=f"bill_{request.agent_id}_{datetime.now().timestamp()}",
            agent_id=request.agent_id,
            total_mxu=result["billed"],
            energy_mxu=result["breakdown"]["components"]["energy_mxu"],
            capacity_mxu=result["breakdown"]["components"]["capacity_mxu"],
            state_mxu=result["breakdown"]["components"]["state_mxu"],
            governance_mxu=result["breakdown"]["components"]["governance_mxu"],
            gpu_seconds=request.metering.get("gpu_seconds"),
            cpu_seconds=request.metering.get("cpu_seconds"),
            ram_gb_seconds=request.metering.get("ram_gb_seconds"),
            bandwidth_mb=request.metering.get("bandwidth_mb"),
            storage_gb_days=request.metering.get("storage_gb_days"),
            metering_source=request.metering["metering_source"],
            metering_timestamp=datetime.fromisoformat(request.metering["timestamp"]),
            paid=True
        )
        db.add(billing)
        db.commit()
        
        return result
        
    except BankruptcyError as e:
        logger.warning(f"Bankruptcy: {str(e)}")
        raise HTTPException(status_code=402, detail=str(e))
    except InsufficientFunds as e:
        raise HTTPException(status_code=402, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Billing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transactions", response_model=TransactionResponse)
async def execute_transaction(request: TransactionRequest, db: Session = Depends(get_db)):
    """Execute payment between agents"""
    try:
        result = economy.pay_agent(
            request.from_id,
            request.to_id,
            request.amount_mxu,
            request.quality_score
        )
        
        # Update database
        from_agent = db.query(models.Agent).filter(models.Agent.id == request.from_id).first()
        to_agent = db.query(models.Agent).filter(models.Agent.id == request.to_id).first()
        
        if from_agent:
            from_agent.balance = economy.balance(request.from_id)
            from_agent.last_activity = datetime.now()
        
        if to_agent:
            to_agent.balance = result["agent_new_balance"]
            to_agent.reputation = result["agent_reputation"]
            to_agent.last_activity = datetime.now()
        
        # Log transaction
        tx = models.Transaction(
            id=f"tx_payment_{request.from_id}_{request.to_id}_{datetime.now().timestamp()}",
            transaction_type=models.TransactionTypeEnum.PAYMENT,
            from_agent_id=request.from_id,
            to_agent_id=request.to_id,
            gross_amount=result["gross"],
            tax_amount=result["tax"],
            net_amount=result["net"],
            tax_rate=result["tax_rate"],
            description=request.description
        )
        db.add(tx)
        db.commit()
        
        return result
        
    except InsufficientFunds as e:
        raise HTTPException(status_code=402, detail=str(e))
    except InvalidTransaction as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Transaction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================================
# UTILITIES
# ==============================================================================

@router.post("/estimate-cost", response_model=dict)
async def estimate_cost(request: CostEstimateRequest):
    """Estimate cost for resource usage (no guardian required)"""
    from src.core.metering import ResourceMetering
    
    result = ResourceMetering.estimate_cost(
        gpu_hours=request.gpu_hours,
        ram_gb_hours=request.ram_gb_hours,
        storage_gb_days=request.storage_gb_days
    )
    
    return result

# ==============================================================================
# GOVERNANCE & STABILIZERS
# ==============================================================================

@router.post("/governance/stabilize", response_model=StabilizerResponse)
async def run_stabilizer(db: Session = Depends(get_db)):
    """Run automatic stabilizer (admin/cron only)"""
    try:
        result = economy.stabilizer_step()
        
        # Log stabilizer actions
        for action in result["actions"]:
            stab_action = models.StabilizerAction(
                action_type=action["type"],
                reason=action.get("reason", ""),
                amount_mxu=action.get("amount"),
                beneficiary_count=action.get("beneficiaries"),
                action_metadata=action,  # ✅ FIXED
                unemployment_rate=result["metrics"].get("unemployment_rate"),
                coverage_ratio=result["health"].get("coverage_ratio"),
                velocity=result["metrics"].get("velocity")
            )
            db.add(stab_action)
        
        db.commit()
        
        return result
        
    except Exception as e:
        db.rollback()
        logger.error(f"Stabilizer error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================================
# WEBSOCKET FOR REAL-TIME UPDATES
# ==============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")

manager = ConnectionManager()

@router.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Send metrics every 5 seconds
            await asyncio.sleep(5)
            
            state = economy.get_state()
            await websocket.send_json({
                "type": "metrics_update",
                "data": state,
                "timestamp": datetime.now().isoformat()
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
