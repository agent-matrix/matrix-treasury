"""
Real-Time Analytics Engine

Provides real-time metrics and insights for the Mission Control dashboard.
Replaces mock data with actual system metrics.

Features:
- Real-time transaction monitoring
- Treasury health metrics
- Agent performance analytics
- Network health tracking
- Predictive runway calculations
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TransactionRecord:
    """Individual transaction record"""
    timestamp: datetime
    agent_id: str
    amount: Decimal
    transaction_type: str  # credit, debit, loan, repayment
    reason: str
    balance_after: Decimal


@dataclass
class AgentMetrics:
    """Agent performance metrics"""
    agent_id: str
    total_earned: Decimal
    total_spent: Decimal
    current_balance: Decimal
    credit_score: Decimal
    transaction_count: int
    avg_transaction_size: Decimal
    active_loans: int
    total_debt: Decimal


class RealTimeAnalytics:
    """
    Real-time analytics engine for enterprise monitoring.
    """

    def __init__(self):
        """Initialize analytics engine"""
        self.transactions: List[TransactionRecord] = []
        self.agent_metrics: Dict[str, AgentMetrics] = {}

        # Performance tracking
        self.hourly_volume: Dict[datetime, Decimal] = defaultdict(Decimal)
        self.daily_active_agents: Dict[datetime, Set[str]] = defaultdict(set)

        logger.info("Real-Time Analytics Engine initialized")

    def record_transaction(
        self,
        agent_id: str,
        amount: Decimal,
        transaction_type: str,
        reason: str,
        balance_after: Decimal,
    ) -> None:
        """
        Record a transaction for analytics.

        Args:
            agent_id: Agent identifier
            amount: Transaction amount
            transaction_type: Type of transaction
            reason: Transaction reason
            balance_after: Agent balance after transaction
        """
        now = datetime.now()

        # Record transaction
        record = TransactionRecord(
            timestamp=now,
            agent_id=agent_id,
            amount=amount,
            transaction_type=transaction_type,
            reason=reason,
            balance_after=balance_after,
        )
        self.transactions.append(record)

        # Update hourly volume
        hour_key = now.replace(minute=0, second=0, microsecond=0)
        self.hourly_volume[hour_key] += abs(amount)

        # Track daily active agents
        day_key = now.replace(hour=0, minute=0, second=0, microsecond=0)
        self.daily_active_agents[day_key].add(agent_id)

        # Update agent metrics
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = AgentMetrics(
                agent_id=agent_id,
                total_earned=Decimal("0"),
                total_spent=Decimal("0"),
                current_balance=balance_after,
                credit_score=Decimal("0.5"),
                transaction_count=0,
                avg_transaction_size=Decimal("0"),
                active_loans=0,
                total_debt=Decimal("0"),
            )

        metrics = self.agent_metrics[agent_id]
        metrics.transaction_count += 1
        metrics.current_balance = balance_after

        if amount > 0:
            metrics.total_earned += amount
        else:
            metrics.total_spent += abs(amount)

        # Update average transaction size
        total = metrics.avg_transaction_size * Decimal(metrics.transaction_count - 1)
        metrics.avg_transaction_size = (total + abs(amount)) / Decimal(metrics.transaction_count)

    def get_recent_transactions(
        self,
        limit: int = 100,
        agent_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent transactions.

        Args:
            limit: Maximum number of transactions
            agent_id: Filter by agent (optional)

        Returns:
            List of transaction records
        """
        # Filter and sort
        filtered = self.transactions
        if agent_id:
            filtered = [t for t in filtered if t.agent_id == agent_id]

        filtered = sorted(filtered, key=lambda t: t.timestamp, reverse=True)[:limit]

        return [
            {
                "timestamp": t.timestamp.isoformat(),
                "agent_id": t.agent_id,
                "amount": float(t.amount),
                "type": t.transaction_type,
                "reason": t.reason,
                "balance_after": float(t.balance_after),
            }
            for t in filtered
        ]

    def calculate_runway(
        self,
        current_balance: Decimal,
        time_window_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Calculate treasury runway based on burn rate.

        Args:
            current_balance: Current treasury balance
            time_window_hours: Hours to analyze for burn rate

        Returns:
            Runway metrics
        """
        now = datetime.now()
        cutoff = now - timedelta(hours=time_window_hours)

        # Calculate burn rate
        recent_debits = [
            abs(t.amount) for t in self.transactions
            if t.timestamp >= cutoff and t.amount < 0
        ]

        if not recent_debits:
            return {
                "runway_days": None,
                "burn_rate_per_day": 0.0,
                "message": "No spending activity in analysis window",
            }

        total_burned = sum(recent_debits)
        burn_rate_per_hour = total_burned / Decimal(time_window_hours)
        burn_rate_per_day = burn_rate_per_hour * Decimal("24")

        if burn_rate_per_day == 0:
            runway_days = None
        else:
            runway_days = float(current_balance / burn_rate_per_day)

        return {
            "runway_days": runway_days,
            "burn_rate_per_day": float(burn_rate_per_day),
            "burn_rate_per_hour": float(burn_rate_per_hour),
            "total_burned_window": float(total_burned),
            "analysis_window_hours": time_window_hours,
        }

    def get_hourly_volume(self, hours: int = 24) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get hourly transaction volume.

        Args:
            hours: Number of hours to retrieve

        Returns:
            Hourly volume data
        """
        now = datetime.now()
        cutoff = now - timedelta(hours=hours)

        # Filter hourly data
        hourly_data = [
            {
                "hour": hour.isoformat(),
                "volume": float(volume),
            }
            for hour, volume in sorted(self.hourly_volume.items())
            if hour >= cutoff
        ]

        return {
            "hourly_volume": hourly_data,
            "total_volume": sum(v["volume"] for v in hourly_data),
        }

    def get_agent_rankings(
        self,
        metric: str = "total_earned",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get top agents by metric.

        Args:
            metric: Metric to rank by (total_earned, credit_score, etc.)
            limit: Number of agents to return

        Returns:
            Ranked agents
        """
        agents = sorted(
            self.agent_metrics.values(),
            key=lambda a: getattr(a, metric),
            reverse=True,
        )[:limit]

        return [
            {
                "agent_id": a.agent_id,
                "total_earned": float(a.total_earned),
                "total_spent": float(a.total_spent),
                "current_balance": float(a.current_balance),
                "credit_score": float(a.credit_score),
                "transaction_count": a.transaction_count,
            }
            for a in agents
        ]

    def get_system_health(
        self,
        treasury_balance: Decimal,
        total_agent_balances: Decimal,
    ) -> Dict[str, Any]:
        """
        Calculate overall system health metrics.

        Args:
            treasury_balance: Current treasury balance
            total_agent_balances: Sum of all agent balances

        Returns:
            Health metrics
        """
        # Calculate solvency ratio
        if total_agent_balances > 0:
            solvency_ratio = float(treasury_balance / total_agent_balances)
        else:
            solvency_ratio = float("inf")

        # Determine health status
        if solvency_ratio >= 1.5:
            status = "healthy"
            color = "green"
        elif solvency_ratio >= 1.0:
            status = "stable"
            color = "yellow"
        else:
            status = "critical"
            color = "red"

        # Calculate runway
        runway_data = self.calculate_runway(treasury_balance)

        # Active agents (last 24 hours)
        now = datetime.now()
        active_today = len(self.daily_active_agents.get(
            now.replace(hour=0, minute=0, second=0, microsecond=0),
            set()
        ))

        return {
            "status": status,
            "status_color": color,
            "solvency_ratio": solvency_ratio,
            "treasury_balance": float(treasury_balance),
            "total_agent_balances": float(total_agent_balances),
            "runway_days": runway_data.get("runway_days"),
            "burn_rate_per_day": runway_data.get("burn_rate_per_day"),
            "active_agents_today": active_today,
            "total_agents": len(self.agent_metrics),
            "total_transactions": len(self.transactions),
        }

    def get_dashboard_metrics(
        self,
        treasury_balance: Decimal,
        total_agent_balances: Decimal,
    ) -> Dict[str, Any]:
        """
        Get comprehensive metrics for Mission Control dashboard.

        Args:
            treasury_balance: Current treasury balance
            total_agent_balances: Sum of all agent balances

        Returns:
            Dashboard metrics
        """
        return {
            "system_health": self.get_system_health(treasury_balance, total_agent_balances),
            "recent_transactions": self.get_recent_transactions(limit=50),
            "hourly_volume": self.get_hourly_volume(hours=24),
            "top_agents": self.get_agent_rankings(limit=10),
            "runway": self.calculate_runway(treasury_balance),
        }

    def update_agent_credit_score(self, agent_id: str, credit_score: Decimal) -> None:
        """Update agent credit score"""
        if agent_id in self.agent_metrics:
            self.agent_metrics[agent_id].credit_score = credit_score

    def update_agent_loans(self, agent_id: str, active_loans: int, total_debt: Decimal) -> None:
        """Update agent loan information"""
        if agent_id in self.agent_metrics:
            self.agent_metrics[agent_id].active_loans = active_loans
            self.agent_metrics[agent_id].total_debt = total_debt

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get high-level analytics summary"""
        total_volume = sum(abs(t.amount) for t in self.transactions)
        avg_transaction = total_volume / len(self.transactions) if self.transactions else Decimal("0")

        return {
            "total_transactions": len(self.transactions),
            "total_volume": float(total_volume),
            "average_transaction": float(avg_transaction),
            "tracked_agents": len(self.agent_metrics),
            "earliest_transaction": self.transactions[0].timestamp.isoformat() if self.transactions else None,
            "latest_transaction": self.transactions[-1].timestamp.isoformat() if self.transactions else None,
        }
