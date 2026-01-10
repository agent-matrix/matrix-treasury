"""
Database models for Matrix Treasury
Uses SQLAlchemy ORM for persistence
FIXED: Renamed 'metadata' to 'agent_metadata' to avoid SQLAlchemy conflict
"""

from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Boolean,
    ForeignKey, Enum, Text, JSON, Index
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class AgentStatusEnum(PyEnum):
    ACTIVE = "active"
    THROTTLED = "throttled"
    HIBERNATED = "hibernated"
    ARCHIVED = "archived"
    DELETED = "deleted"

class TransactionTypeEnum(PyEnum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    PAYMENT = "payment"
    CHARGE = "charge"
    TAX = "tax"
    UBC_GRANT = "ubc_grant"
    UBC_RENEWAL = "ubc_renewal"
    STIMULUS = "stimulus"
    BURN = "burn"

# ==============================================================================
# CORE ENTITIES
# ==============================================================================

class Agent(Base):
    """Agent/User entity"""
    __tablename__ = "agents"
    
    id = Column(String(255), primary_key=True)
    agent_type = Column(String(50), nullable=False, default="agent")
    
    # Financial state
    balance = Column(Float, nullable=False, default=0.0)
    reputation = Column(Float, nullable=False, default=0.0)
    status = Column(Enum(AgentStatusEnum), nullable=False, default=AgentStatusEnum.ACTIVE)
    
    # UBC tracking
    ubc_renewals_used = Column(Integer, nullable=False, default=0)
    last_ubc_renewal = Column(DateTime, nullable=True)
    
    # Activity tracking
    last_activity = Column(DateTime, nullable=False, default=func.now())
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Metadata (RENAMED from 'metadata' to avoid SQLAlchemy conflict)
    flags = Column(JSON, nullable=True)
    agent_metadata = Column(JSON, nullable=True)  # ✅ FIXED: was 'metadata'
    
    # Relationships
    transactions_sent = relationship(
        "Transaction",
        foreign_keys="Transaction.from_agent_id",
        back_populates="from_agent"
    )
    transactions_received = relationship(
        "Transaction",
        foreign_keys="Transaction.to_agent_id",
        back_populates="to_agent"
    )
    billing_records = relationship("BillingRecord", back_populates="agent")
    
    # Indexes
    __table_args__ = (
        Index('idx_agent_status', 'status'),
        Index('idx_agent_type', 'agent_type'),
        Index('idx_agent_last_activity', 'last_activity'),
    )

class Transaction(Base):
    """Transaction history"""
    __tablename__ = "transactions"
    
    id = Column(String(255), primary_key=True)
    transaction_type = Column(Enum(TransactionTypeEnum), nullable=False)
    
    # Parties
    from_agent_id = Column(String(255), ForeignKey("agents.id"), nullable=True)
    to_agent_id = Column(String(255), ForeignKey("agents.id"), nullable=True)
    
    # Amounts
    gross_amount = Column(Float, nullable=False)
    tax_amount = Column(Float, nullable=False, default=0.0)
    net_amount = Column(Float, nullable=False)
    
    # Context
    tax_rate = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    tx_metadata = Column(JSON, nullable=True)  # ✅ FIXED: was 'metadata'
    
    # Timestamp
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    from_agent = relationship(
        "Agent",
        foreign_keys=[from_agent_id],
        back_populates="transactions_sent"
    )
    to_agent = relationship(
        "Agent",
        foreign_keys=[to_agent_id],
        back_populates="transactions_received"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_tx_from_agent', 'from_agent_id'),
        Index('idx_tx_to_agent', 'to_agent_id'),
        Index('idx_tx_type', 'transaction_type'),
        Index('idx_tx_created', 'created_at'),
    )

class BillingRecord(Base):
    """Resource usage billing records"""
    __tablename__ = "billing_records"
    
    id = Column(String(255), primary_key=True)
    agent_id = Column(String(255), ForeignKey("agents.id"), nullable=False)
    
    # Billing breakdown
    total_mxu = Column(Float, nullable=False)
    energy_mxu = Column(Float, nullable=False, default=0.0)
    capacity_mxu = Column(Float, nullable=False, default=0.0)
    state_mxu = Column(Float, nullable=False, default=0.0)
    governance_mxu = Column(Float, nullable=False, default=0.0)
    
    # Resource metrics
    gpu_seconds = Column(Float, nullable=True)
    cpu_seconds = Column(Float, nullable=True)
    ram_gb_seconds = Column(Float, nullable=True)
    bandwidth_mb = Column(Float, nullable=True)
    storage_gb_days = Column(Float, nullable=True)
    
    # Metering metadata
    metering_source = Column(String(100), nullable=False)
    metering_timestamp = Column(DateTime, nullable=False)
    metering_metadata = Column(JSON, nullable=True)  # ✅ FIXED: was 'metadata'
    
    # Status
    paid = Column(Boolean, nullable=False, default=False)
    payment_transaction_id = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    agent = relationship("Agent", back_populates="billing_records")
    
    # Indexes
    __table_args__ = (
        Index('idx_billing_agent', 'agent_id'),
        Index('idx_billing_created', 'created_at'),
        Index('idx_billing_paid', 'paid'),
    )

class TreasurySnapshot(Base):
    """Periodic snapshots of treasury state for analytics"""
    __tablename__ = "treasury_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Economic state
    reserve_usd = Column(Float, nullable=False)
    mxu_supply = Column(Float, nullable=False)
    infrastructure_pool = Column(Float, nullable=False)
    ubc_pool = Column(Float, nullable=False)
    emergency_pool = Column(Float, nullable=False)
    
    # Pricing
    usd_per_mxu = Column(Float, nullable=False)
    raw_price = Column(Float, nullable=False)
    
    # Metrics
    total_transactions = Column(Integer, nullable=False)
    total_mxu_burned = Column(Float, nullable=False)
    total_mxu_minted = Column(Float, nullable=False)
    crisis_mode = Column(Boolean, nullable=False)
    
    # Economic health
    coverage_ratio = Column(Float, nullable=True)
    coverage_days = Column(Float, nullable=True)
    
    # Timestamp
    snapshot_at = Column(DateTime, nullable=False, default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_snapshot_time', 'snapshot_at'),
    )

class StabilizerAction(Base):
    """Log of automatic stabilizer actions"""
    __tablename__ = "stabilizer_actions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    action_type = Column(String(100), nullable=False)
    reason = Column(Text, nullable=False)
    
    # Action details
    amount_mxu = Column(Float, nullable=True)
    beneficiary_count = Column(Integer, nullable=True)
    action_metadata = Column(JSON, nullable=True)  # ✅ FIXED: was 'metadata'
    
    # Economic context at time of action
    unemployment_rate = Column(Float, nullable=True)
    coverage_ratio = Column(Float, nullable=True)
    velocity = Column(Float, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_stabilizer_type', 'action_type'),
        Index('idx_stabilizer_created', 'created_at'),
    )

class AuditLog(Base):
    """Audit log for all significant system events"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(100), nullable=False)
    agent_id = Column(String(255), nullable=True)

    # Event details
    description = Column(Text, nullable=False)
    event_metadata = Column(JSON, nullable=True)  # ✅ FIXED: was 'metadata'

    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_audit_type', 'event_type'),
        Index('idx_audit_agent', 'agent_id'),
        Index('idx_audit_created', 'created_at'),
    )


# ==============================================================================
# MISSION CONTROL MODELS
# ==============================================================================

class AdminUser(Base):
    """Admin users for Mission Control authentication"""
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    # Role and permissions
    role = Column(String(50), nullable=False, default="admin")
    is_active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    last_login = Column(DateTime, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_admin_username', 'username'),
        Index('idx_admin_active', 'is_active'),
    )


class SystemState(Base):
    """Singleton table for system-wide state (autopilot, panic mode)"""
    __tablename__ = "system_state"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Control flags
    autopilot_enabled = Column(Boolean, nullable=False, default=True)
    panic_mode = Column(Boolean, nullable=False, default=False)

    # Timestamps
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())


class AppSettings(Base):
    """Singleton table for Mission Control UI settings"""
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Settings stored as JSON blob
    data = Column(JSON, nullable=False, default=dict)

    # Timestamps
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())


class PendingApproval(Base):
    """Queue of transactions awaiting admin approval"""
    __tablename__ = "pending_approvals"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Transaction details
    agent = Column(String(255), nullable=False)
    action = Column(String(255), nullable=False)
    cost = Column(Float, nullable=False)
    tx_kind = Column(String(50), nullable=False, default="EXPENSE")  # EXPENSE, INCOME, SYSTEM

    # Status
    status = Column(String(50), nullable=False, default="PENDING")  # PENDING, APPROVED, DENIED
    reason = Column(Text, nullable=True)
    admin_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    decided_at = Column(DateTime, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_approval_status', 'status'),
        Index('idx_approval_created', 'created_at'),
        Index('idx_approval_agent', 'agent'),
    )


class ChatMessage(Base):
    """Chat message history for Neural Link"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Message details
    contact_id = Column(String(255), nullable=False)  # cfo, alpha, beta, sys
    sender = Column(String(255), nullable=False)  # USER or contact name
    text = Column(Text, nullable=False)

    # Timestamp
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_chat_contact', 'contact_id'),
        Index('idx_chat_created', 'created_at'),
    )
