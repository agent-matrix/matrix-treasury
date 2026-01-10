"""
Pydantic schemas for API request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class AgentStatusEnum(str, Enum):
    ACTIVE = "active"
    THROTTLED = "throttled"
    HIBERNATED = "hibernated"
    ARCHIVED = "archived"
    DELETED = "deleted"

# ==============================================================================
# REQUEST SCHEMAS
# ==============================================================================

class DepositRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=255)
    amount_usd: float = Field(..., gt=0, description="USD amount to deposit")

class OnboardRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=255)
    agent_type: str = Field(default="agent", description="Type: agent, human, service")
    metadata: Optional[Dict[str, Any]] = None

class BillingRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=255)
    metering: Dict[str, float] = Field(..., description="Resource usage metrics")
    
    @validator('metering')
    def validate_metering(cls, v):
        required_fields = ["metering_source", "timestamp"]
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Missing required metering field: {field}")
        return v

class TransactionRequest(BaseModel):
    from_id: str = Field(..., min_length=1, max_length=255)
    to_id: str = Field(..., min_length=1, max_length=255)
    amount_mxu: float = Field(..., gt=0, description="MXU amount to transfer")
    quality_score: float = Field(default=1.0, ge=0.0, le=1.0)
    description: Optional[str] = None

class UBCRenewalRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=255)

class CostEstimateRequest(BaseModel):
    gpu_hours: float = Field(default=0.0, ge=0)
    ram_gb_hours: float = Field(default=0.0, ge=0)
    storage_gb_days: float = Field(default=0.0, ge=0)

# ==============================================================================
# RESPONSE SCHEMAS
# ==============================================================================

class HealthResponse(BaseModel):
    status: str
    system: str
    version: str
    timestamp: str

class DepositResponse(BaseModel):
    status: str
    usd_deposited: float
    mxu_received: float
    commons_contribution: float
    exchange_rate: float
    new_balance: float

class OnboardResponse(BaseModel):
    status: str
    agent_id: str
    ubc_granted: float
    grant_type: str
    balance: float
    agent_status: str

class BillingResponse(BaseModel):
    status: str
    billed: float
    breakdown: Dict[str, Any]
    new_balance: float
    agent_status: str

class TransactionResponse(BaseModel):
    status: str
    gross: float
    tax: float
    tax_rate: float
    net: float
    agent_new_balance: float
    agent_reputation: float

class MetricsResponse(BaseModel):
    supply: float
    reserves: float
    pools: Dict[str, float]
    price_usd: float
    mxu_per_usd: float
    crisis_mode: bool
    total_transactions: int
    total_burned: float
    total_minted: float

class EconomicMetricsResponse(BaseModel):
    total_agents: int
    active_agents: int
    idle_agents: int
    unemployment_rate: float
    velocity: float
    concentration: float
    avg_reputation: float
    status_distribution: Dict[str, int]

class ReserveHealthResponse(BaseModel):
    reserve_usd: float
    coverage_ratio: float
    coverage_days: float
    crisis_mode: bool
    daily_cost_usd: float
    target_usd: float

class StabilizerResponse(BaseModel):
    health: Dict[str, Any]
    metrics: Dict[str, Any]
    actions: List[Dict[str, Any]]
    timestamp: str

class AgentDetailResponse(BaseModel):
    id: str
    agent_type: str
    balance: float
    reputation: float
    status: str
    ubc_renewals_used: int
    last_ubc_renewal: Optional[str]
    last_activity: str
    created_at: str

class TransactionHistoryItem(BaseModel):
    id: str
    transaction_type: str
    from_agent_id: Optional[str]
    to_agent_id: Optional[str]
    gross_amount: float
    net_amount: float
    created_at: str

class TransactionHistoryResponse(BaseModel):
    transactions: List[TransactionHistoryItem]
    total: int
    page: int
    page_size: int
