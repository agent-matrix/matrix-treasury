"""
Matrix Economy - The Society Layer
Implements agent lifecycle, wallets, transactions, UBC, and automatic stabilizers.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from enum import Enum
import logging

from src.core.config import CostOracle, SystemPolicy
from src.core.treasury import MatrixTreasury
from src.core.metering import ResourceMetering
from src.core.exceptions import (
    InsufficientFunds,
    AgentNotFound,
    InvalidTransaction,
    BankruptcyError
)

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """Agent operational status"""
    ACTIVE = "active"
    THROTTLED = "throttled"
    HIBERNATED = "hibernated"
    ARCHIVED = "archived"
    DELETED = "deleted"

class AutoselfEconomy:
    """
    The complete economic operating system for Matrix agents.
    
    Features:
    - Universal Basic Compute (UBC)
    - Reputation system
    - Bankruptcy ladder
    - Automatic stabilizers
    - Constitutional enforcement
    """
    
    def __init__(
        self,
        oracle: Optional[CostOracle] = None,
        policy: Optional[SystemPolicy] = None
    ):
        self.oracle = oracle or CostOracle()
        self.policy = policy or SystemPolicy()
        self.treasury = MatrixTreasury(self.oracle, self.policy)
        
        # Agent state (in-memory for now, will be DB-backed in production)
        self.wallets: Dict[str, float] = {}
        self.reputation: Dict[str, float] = {}
        self.status: Dict[str, AgentStatus] = {}
        self.ubc_renewals: Dict[str, int] = {}
        self.last_ubc_renewal: Dict[str, datetime] = {}
        self.last_activity: Dict[str, datetime] = {}
        self.flags: Dict[str, Set[str]] = {}
        
        # Metrics
        self.agent_count = 0
        self.active_jobs = 0
        
        logger.info("Economy initialized with UBC and stabilizers")
    
    # =========================================================================
    # WALLET OPERATIONS
    # =========================================================================
    
    def balance(self, agent_id: str) -> float:
        """Get agent balance"""
        return self.wallets.get(agent_id, 0.0)
    
    def credit(self, agent_id: str, amount: float, source: str = "") -> None:
        """Credit agent wallet"""
        if agent_id not in self.wallets:
            raise AgentNotFound(f"Agent {agent_id} not found")
        
        self.wallets[agent_id] += amount
        logger.debug(f"Credited {agent_id}: +{amount:.4f} MXU (source: {source})")
    
    def debit(self, agent_id: str, amount: float, reason: str = "") -> None:
        """Debit agent wallet with insufficient funds check"""
        if agent_id not in self.wallets:
            raise AgentNotFound(f"Agent {agent_id} not found")
        
        current_balance = self.wallets[agent_id]
        if current_balance < amount:
            raise InsufficientFunds(
                f"Agent {agent_id} has {current_balance:.4f} MXU, "
                f"needs {amount:.4f} MXU"
            )
        
        self.wallets[agent_id] -= amount
        logger.debug(f"Debited {agent_id}: -{amount:.4f} MXU (reason: {reason})")
    
    # =========================================================================
    # AGENT LIFECYCLE
    # =========================================================================
    
    def onboard_agent(self, agent_id: str) -> Dict[str, any]:
        """
        Onboard new agent with UBC grant.
        This prevents the death spiral for new agents.
        """
        if agent_id in self.wallets:
            return {
                "status": "error",
                "message": "Agent already exists"
            }
        
        # Initialize agent state
        self.wallets[agent_id] = 0.0
        self.reputation[agent_id] = 0.0
        self.status[agent_id] = AgentStatus.ACTIVE
        self.ubc_renewals[agent_id] = 0
        self.last_activity[agent_id] = datetime.now()
        self.flags[agent_id] = set()
        self.agent_count += 1
        
        # Grant UBC (if pool has funds)
        grant = self.policy.ubc_grant_mxu
        granted_amount = 0.0
        
        if self.treasury.ubc_pool_mxu >= grant:
            self.treasury.ubc_pool_mxu -= grant
            self.wallets[agent_id] = grant
            granted_amount = grant
            grant_type = "full"
        else:
            # Fallback: minimal grant
            minimal = grant * 0.2
            if self.treasury.ubc_pool_mxu >= minimal:
                self.treasury.ubc_pool_mxu -= minimal
                self.wallets[agent_id] = minimal
                granted_amount = minimal
                grant_type = "minimal"
            else:
                grant_type = "none"
        
        logger.info(
            f"Onboarded {agent_id} with {granted_amount:.2f} MXU "
            f"UBC grant ({grant_type})"
        )
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "ubc_granted": granted_amount,
            "grant_type": grant_type,
            "balance": self.wallets[agent_id],
            "agent_status": self.status[agent_id].value
        }
    
    def renew_ubc_if_eligible(self, agent_id: str) -> Dict[str, any]:
        """
        Safety net: renew UBC for active but broke agents.
        
        Eligibility:
        - Balance < 50 MXU
        - Has completed at least 1 task (reputation > 0)
        - Hasn't exceeded max renewals
        - Cooldown period passed
        """
        if agent_id not in self.wallets:
            return {
                "eligible": False,
                "reason": "agent_not_found"
            }
        
        balance = self.balance(agent_id)
        rep = self.reputation[agent_id]
        renewals = self.ubc_renewals[agent_id]
        
        # Check balance threshold
        if balance >= 50:
            return {
                "eligible": False,
                "reason": "sufficient_balance",
                "balance": balance
            }
        
        # Check reputation (must have worked before)
        if rep <= 0:
            return {
                "eligible": False,
                "reason": "no_reputation"
            }
        
        # Check renewal limit
        if renewals >= self.policy.ubc_max_renewals:
            return {
                "eligible": False,
                "reason": "max_renewals_exceeded",
                "renewals_used": renewals
            }
        
        # Check cooldown
        if agent_id in self.last_ubc_renewal:
            last_renewal = self.last_ubc_renewal[agent_id]
            cooldown = timedelta(hours=self.policy.ubc_renewal_cooldown_hours)
            if datetime.now() - last_renewal < cooldown:
                return {
                    "eligible": False,
                    "reason": "cooldown_active",
                    "last_renewal": last_renewal.isoformat()
                }
        
        # Grant renewal
        renewal_amount = self.policy.ubc_renew_mxu
        
        if self.treasury.ubc_pool_mxu >= renewal_amount:
            self.treasury.ubc_pool_mxu -= renewal_amount
            self.wallets[agent_id] += renewal_amount
            self.ubc_renewals[agent_id] += 1
            self.last_ubc_renewal[agent_id] = datetime.now()
            
            logger.info(
                f"Renewed UBC for {agent_id}: "
                f"{renewal_amount:.2f} MXU (renewal {renewals + 1})"
            )
            
            return {
                "eligible": True,
                "status": "renewed",
                "amount": renewal_amount,
                "renewals_used": self.ubc_renewals[agent_id],
                "new_balance": self.wallets[agent_id]
            }
        
        return {
            "eligible": True,
            "status": "pool_depleted",
            "reason": "ubc_pool_empty"
        }
    
    # =========================================================================
    # WORK & PAYMENT
    # =========================================================================
    
    def charge_for_work(
        self,
        agent_id: str,
        metering: Dict[str, float]
    ) -> Dict[str, any]:
        """
        Bill agent for computational work based on metering.
        Implements bankruptcy ladder if insufficient funds.
        """
        if agent_id not in self.wallets:
            raise AgentNotFound(f"Agent {agent_id} not found")
        
        # Calculate bill
        bill = ResourceMetering.bill_from_metering(
            metering, self.oracle, self.policy
        )
        total_mxu = bill["total_mxu"]
        
        balance = self.balance(agent_id)
        
        # Bankruptcy ladder logic
        if balance < total_mxu:
            shortage_ratio = balance / total_mxu if total_mxu > 0 else 0
            
            if shortage_ratio < self.policy.hibernate_threshold:
                # < 1% of bill: hibernate
                self.status[agent_id] = AgentStatus.HIBERNATED
                raise BankruptcyError(
                    f"Agent {agent_id} hibernated: "
                    f"balance {balance:.4f} < {total_mxu:.4f} MXU needed"
                )
            elif shortage_ratio < self.policy.throttle_threshold:
                # < 10% of bill: throttle
                self.status[agent_id] = AgentStatus.THROTTLED
                raise BankruptcyError(
                    f"Agent {agent_id} throttled: insufficient funds"
                )
            else:
                # Can partially pay: throttle and try UBC renewal
                self.status[agent_id] = AgentStatus.THROTTLED
                renewal = self.renew_ubc_if_eligible(agent_id)
                if renewal.get("status") == "renewed":
                    # Retry with renewed balance
                    balance = self.balance(agent_id)
                    if balance >= total_mxu:
                        self.status[agent_id] = AgentStatus.ACTIVE
                    else:
                        raise BankruptcyError(
                            f"Agent {agent_id} still insufficient after UBC renewal"
                        )
                else:
                    raise BankruptcyError(
                        f"Agent {agent_id} insufficient funds, UBC renewal failed"
                    )
        else:
            # Sufficient funds: restore to active
            self.status[agent_id] = AgentStatus.ACTIVE
        
        # Debit and burn
        self.debit(agent_id, total_mxu, reason="compute_bill")
        self.treasury.burn_for_costs(total_mxu)
        self.last_activity[agent_id] = datetime.now()
        
        return {
            "status": "success",
            "billed": total_mxu,
            "breakdown": bill,
            "new_balance": self.balance(agent_id),
            "agent_status": self.status[agent_id].value
        }
    
    def pay_agent(
        self,
        client_id: str,
        agent_id: str,
        amount_mxu: float,
        quality_score: float = 1.0
    ) -> Dict[str, any]:
        """
        Client pays agent for completed work.
        Includes progressive taxation and reputation update.
        """
        if client_id not in self.wallets:
            raise AgentNotFound(f"Client {client_id} not found")
        if agent_id not in self.wallets:
            raise AgentNotFound(f"Agent {agent_id} not found")
        
        # Validate amount
        if amount_mxu < self.policy.min_transaction_mxu:
            raise InvalidTransaction(
                f"Amount {amount_mxu} below minimum {self.policy.min_transaction_mxu}"
            )
        if amount_mxu > self.policy.max_transaction_mxu:
            raise InvalidTransaction(
                f"Amount {amount_mxu} exceeds maximum {self.policy.max_transaction_mxu}"
            )
        
        # Calculate tax
        tax_info = self.treasury.collect_tax(
            amount_mxu, self.balance(client_id)
        )
        net_payment = tax_info["net"]
        
        # Execute transaction
        self.debit(client_id, amount_mxu, reason="payment_to_agent")
        self.credit(agent_id, net_payment, source="work_payment")
        
        # Update reputation (exponential moving average)
        old_rep = self.reputation[agent_id]
        self.reputation[agent_id] = 0.9 * old_rep + 0.1 * quality_score
        
        self.last_activity[agent_id] = datetime.now()
        
        logger.info(
            f"Payment: {client_id} → {agent_id}: "
            f"{amount_mxu:.2f} MXU (tax: {tax_info['tax']:.2f}, "
            f"net: {net_payment:.2f})"
        )
        
        return {
            "status": "success",
            "gross": amount_mxu,
            "tax": tax_info["tax"],
            "tax_rate": tax_info["rate"],
            "net": net_payment,
            "agent_new_balance": self.balance(agent_id),
            "agent_reputation": self.reputation[agent_id]
        }
    
    def deposit_usd(self, user_id: str, usd_amount: float) -> Dict[str, any]:
        """
        Human deposits real money into the system.
        This is the outer loop: USD → MXU
        """
        if user_id not in self.wallets:
            # Auto-onboard if not exists (for human users)
            self.wallets[user_id] = 0.0
            self.reputation[user_id] = 1.0  # Humans start with reputation
            self.status[user_id] = AgentStatus.ACTIVE
            self.last_activity[user_id] = datetime.now()
            self.flags[user_id] = set()
        
        # Mint MXU
        mint_result = self.treasury.mint_from_deposit(usd_amount)
        
        # Credit user account
        self.credit(
            user_id,
            mint_result["user_share"],
            source="usd_deposit"
        )
        
        logger.info(
            f"USD deposit: {user_id} deposited ${usd_amount:.2f}, "
            f"received {mint_result['user_share']:.2f} MXU"
        )
        
        return {
            "status": "success",
            "usd_deposited": usd_amount,
            "mxu_received": mint_result["user_share"],
            "commons_contribution": mint_result["commons_share"],
            "exchange_rate": mint_result["exchange_rate"],
            "new_balance": self.balance(user_id)
        }
    
    # =========================================================================
    # ECONOMIC METRICS & MONITORING
    # =========================================================================
    
    def calculate_economic_metrics(self) -> Dict[str, any]:
        """Calculate health indicators for stabilizer"""
        total_agents = len(self.wallets)
        
        if total_agents == 0:
            return {
                "total_agents": 0,
                "active_agents": 0,
                "unemployment_rate": 0.0,
                "velocity": 0.0,
                "concentration": 0.0,
                "avg_reputation": 0.0
            }
        
        # Active agents (have worked before)
        active = sum(1 for rep in self.reputation.values() if rep > 0)
        
        # Unemployment rate
        idle = total_agents - active
        unemployment_rate = idle / total_agents
        
        # Velocity (transactions per unit supply)
        velocity = (
            self.treasury.total_transactions / self.treasury.mxu_supply
            if self.treasury.mxu_supply > 0 else 0
        )
        
        # Concentration (largest holder's share)
        if self.wallets:
            max_balance = max(self.wallets.values())
            concentration = (
                max_balance / self.treasury.mxu_supply
                if self.treasury.mxu_supply > 0 else 0
            )
        else:
            concentration = 0.0
        
        # Average reputation
        avg_reputation = (
            sum(self.reputation.values()) / len(self.reputation)
            if self.reputation else 0.0
        )
        
        # Agent status distribution
        status_dist = {}
        for status in AgentStatus:
            count = sum(1 for s in self.status.values() if s == status)
            status_dist[status.value] = count
        
        return {
            "total_agents": total_agents,
            "active_agents": active,
            "idle_agents": idle,
            "unemployment_rate": unemployment_rate,
            "velocity": velocity,
            "concentration": concentration,
            "avg_reputation": avg_reputation,
            "status_distribution": status_dist
        }
    
    # =========================================================================
    # AUTOMATIC STABILIZERS (Central Bank Functions)
    # =========================================================================
    
    def stabilizer_step(
        self,
        projected_mxu_burn_per_day: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Automatic economic stabilization.
        Responds to crises like a central bank:
        - Austerity mode on low reserves
        - Stimulus on high unemployment
        - Liquidity injection on deflation
        """
        # Calculate projection if not provided
        if projected_mxu_burn_per_day is None:
            # Simple average: total burned / days elapsed (assume 30 days)
            projected_mxu_burn_per_day = self.treasury.total_mxu_burned / 30.0
        
        health = self.treasury.reserve_health(projected_mxu_burn_per_day)
        metrics = self.calculate_economic_metrics()
        
        actions_taken = []
        
        # =====================================================================
        # CRISIS 1: Reserve Depletion → AUSTERITY
        # =====================================================================
        
        if health["crisis_mode"]:
            actions_taken.append({
                "type": "AUSTERITY_MODE",
                "reason": f"Reserve coverage at {health['coverage_ratio']:.2%}",
                "actions": [
                    "Throttle non-essential agents",
                    "Raise transaction tax (within constitutional limits)",
                    "Pause new agent onboarding"
                ],
                "severity": "high" if health["coverage_ratio"] < 0.5 else "medium"
            })
            
            logger.warning(
                f"AUSTERITY MODE: Coverage ratio {health['coverage_ratio']:.2%}"
            )
        
        # =====================================================================
        # CRISIS 2: High Unemployment → STIMULUS
        # =====================================================================
        
        if metrics["unemployment_rate"] > 0.40:  # 40% unemployment
            stimulus_budget = self.treasury.emergency_pool_mxu * 0.10
            
            if stimulus_budget >= 100:  # Minimum viable stimulus
                # Identify idle agents
                eligible_agents = [
                    aid for aid, rep in self.reputation.items()
                    if rep == 0 and self.status[aid] == AgentStatus.ACTIVE
                ]
                
                if eligible_agents:
                    per_agent = stimulus_budget / len(eligible_agents)
                    
                    for aid in eligible_agents:
                        self.credit(aid, per_agent, source="stimulus")
                    
                    self.treasury.emergency_pool_mxu -= stimulus_budget
                    
                    actions_taken.append({
                        "type": "STIMULUS",
                        "reason": f"Unemployment at {metrics['unemployment_rate']:.1%}",
                        "amount": stimulus_budget,
                        "beneficiaries": len(eligible_agents),
                        "per_agent": per_agent
                    })
                    
                    logger.info(
                        f"STIMULUS: Distributed {stimulus_budget:.2f} MXU "
                        f"to {len(eligible_agents)} idle agents"
                    )
        
        # =====================================================================
        # CRISIS 3: Low Velocity/Deflation → LIQUIDITY INJECTION
        # =====================================================================
        
        if metrics["velocity"] < 0.01 and self.treasury.emergency_pool_mxu > 500:
            bonus_per_agent = 50.0
            active_agents = [
                aid for aid, status in self.status.items()
                if status == AgentStatus.ACTIVE
            ]
            
            total_injection = bonus_per_agent * len(active_agents)
            
            if self.treasury.emergency_pool_mxu >= total_injection:
                for aid in active_agents:
                    self.credit(aid, bonus_per_agent, source="liquidity_injection")
                
                self.treasury.emergency_pool_mxu -= total_injection
                
                actions_taken.append({
                    "type": "LIQUIDITY_INJECTION",
                    "reason": f"Velocity at {metrics['velocity']:.4f}",
                    "amount": total_injection,
                    "beneficiaries": len(active_agents),
                    "per_agent": bonus_per_agent
                })
                
                logger.info(
                    f"LIQUIDITY: Injected {total_injection:.2f} MXU "
                    f"to {len(active_agents)} active agents"
                )
        
        return {
            "health": health,
            "metrics": metrics,
            "actions": actions_taken,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_state(self) -> Dict[str, any]:
        """Get complete economy state"""
        return {
            "treasury": self.treasury.get_state(),
            "metrics": self.calculate_economic_metrics(),
            "agents": {
                "total": len(self.wallets),
                "active": sum(1 for s in self.status.values() if s == AgentStatus.ACTIVE),
                "throttled": sum(1 for s in self.status.values() if s == AgentStatus.THROTTLED),
                "hibernated": sum(1 for s in self.status.values() if s == AgentStatus.HIBERNATED)
            },
            "timestamp": datetime.now().isoformat()
        }
