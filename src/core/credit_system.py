"""
Agent Credit System: Collateral-Based Borrowing

Enables agents to borrow MXU against collateral with automatic repayment tracking.

Features:
- Credit limits based on agent performance
- Collateral-based lending (overcollateralized)
- Automatic liquidation on default
- Interest rate calculation
- Credit score integration
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Loan:
    """Represents an active loan"""
    loan_id: str
    agent_id: str
    principal: Decimal  # Amount borrowed
    collateral: Decimal  # Collateral deposited
    interest_rate: Decimal  # Annual interest rate
    issued_at: datetime
    due_date: datetime
    repaid: Decimal  # Amount repaid so far
    status: str  # active, repaid, defaulted, liquidated

    def total_due(self) -> Decimal:
        """Calculate total amount due including interest"""
        days_elapsed = (datetime.now() - self.issued_at).days
        daily_rate = self.interest_rate / Decimal("365")
        interest = self.principal * daily_rate * Decimal(days_elapsed)
        return self.principal + interest

    def is_undercollateralized(self, collateral_ratio: Decimal = Decimal("1.5")) -> bool:
        """Check if loan is undercollateralized"""
        required_collateral = self.principal * collateral_ratio
        return self.collateral < required_collateral

    def is_overdue(self) -> bool:
        """Check if loan is past due date"""
        return datetime.now() > self.due_date and self.status == "active"


class AgentCreditSystem:
    """
    Manages agent credit, borrowing, and repayment.
    """

    def __init__(self):
        """Initialize credit system"""
        self.loans: Dict[str, List[Loan]] = {}  # agent_id -> list of loans
        self.loan_counter = 0

        # Credit parameters
        self.min_credit_score = Decimal("0.5")  # Minimum score to borrow
        self.max_ltv = Decimal("0.66")  # Loan-to-value ratio (66%)
        self.liquidation_ltv = Decimal("0.75")  # Liquidation threshold (75%)
        self.base_interest_rate = Decimal("0.10")  # 10% annual
        self.default_loan_term_days = 30  # 30 days default

        logger.info("Agent Credit System initialized")

    def calculate_credit_limit(
        self,
        agent_id: str,
        credit_score: Decimal,
        total_earned: Decimal,
    ) -> Decimal:
        """
        Calculate agent's maximum borrowing limit.

        Args:
            agent_id: Agent identifier
            credit_score: Agent's credit score (0.0 - 1.0)
            total_earned: Agent's total historical earnings

        Returns:
            Maximum borrowing limit in MXU
        """
        if credit_score < self.min_credit_score:
            return Decimal("0")

        # Credit limit = f(credit_score, total_earned)
        # Higher score and earnings = higher limit
        base_limit = total_earned * Decimal("0.5")  # Can borrow 50% of earnings
        score_multiplier = credit_score  # 0.5 to 1.0
        credit_limit = base_limit * score_multiplier

        logger.debug(f"Credit limit for {agent_id}: {credit_limit} MXU")
        return credit_limit

    def calculate_interest_rate(self, credit_score: Decimal) -> Decimal:
        """
        Calculate interest rate based on credit score.
        Better score = lower interest rate.

        Args:
            credit_score: Agent's credit score (0.0 - 1.0)

        Returns:
            Annual interest rate (decimal)
        """
        # Interest rate ranges from 5% (perfect score) to 20% (minimum score)
        min_rate = Decimal("0.05")  # 5%
        max_rate = Decimal("0.20")  # 20%

        # Linear interpolation
        rate = max_rate - (credit_score * (max_rate - min_rate))
        return max(min_rate, min(rate, max_rate))

    def request_loan(
        self,
        agent_id: str,
        amount: Decimal,
        collateral: Decimal,
        credit_score: Decimal,
        total_earned: Decimal,
        loan_term_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Request a collateral-backed loan.

        Args:
            agent_id: Agent requesting loan
            amount: Amount to borrow (MXU)
            collateral: Collateral to deposit (MXU)
            credit_score: Agent's credit score
            total_earned: Agent's total earnings
            loan_term_days: Loan term in days (default 30)

        Returns:
            Loan details or error
        """
        logger.info(f"💳 [CREDIT] Loan request: {agent_id} wants {amount} MXU")

        # Check credit eligibility
        if credit_score < self.min_credit_score:
            return {
                "approved": False,
                "reason": f"Credit score too low: {credit_score} < {self.min_credit_score}",
            }

        # Check credit limit
        credit_limit = self.calculate_credit_limit(agent_id, credit_score, total_earned)
        if amount > credit_limit:
            return {
                "approved": False,
                "reason": f"Amount exceeds credit limit: {amount} > {credit_limit}",
                "credit_limit": float(credit_limit),
            }

        # Check collateral (must be overcollateralized)
        required_collateral = amount / self.max_ltv  # 150% collateral
        if collateral < required_collateral:
            return {
                "approved": False,
                "reason": f"Insufficient collateral: {collateral} < {required_collateral}",
                "required_collateral": float(required_collateral),
            }

        # Calculate interest rate
        interest_rate = self.calculate_interest_rate(credit_score)

        # Create loan
        self.loan_counter += 1
        loan_id = f"LOAN-{self.loan_counter:06d}"
        loan_term = loan_term_days or self.default_loan_term_days

        loan = Loan(
            loan_id=loan_id,
            agent_id=agent_id,
            principal=amount,
            collateral=collateral,
            interest_rate=interest_rate,
            issued_at=datetime.now(),
            due_date=datetime.now() + timedelta(days=loan_term),
            repaid=Decimal("0"),
            status="active",
        )

        # Store loan
        if agent_id not in self.loans:
            self.loans[agent_id] = []
        self.loans[agent_id].append(loan)

        logger.info(f"✅ [CREDIT] Loan approved: {loan_id} for {amount} MXU at {interest_rate*100}% APR")

        return {
            "approved": True,
            "loan_id": loan_id,
            "principal": float(amount),
            "collateral": float(collateral),
            "interest_rate": float(interest_rate),
            "due_date": loan.due_date.isoformat(),
            "total_due": float(loan.total_due()),
        }

    def repay_loan(
        self,
        agent_id: str,
        loan_id: str,
        amount: Decimal,
    ) -> Dict[str, Any]:
        """
        Repay a loan (partial or full).

        Args:
            agent_id: Agent making repayment
            loan_id: Loan ID
            amount: Amount to repay

        Returns:
            Repayment details
        """
        # Find loan
        loan = self._find_loan(agent_id, loan_id)
        if not loan:
            raise ValueError(f"Loan not found: {loan_id}")

        if loan.status != "active":
            raise ValueError(f"Loan is not active: {loan.status}")

        total_due = loan.total_due()
        loan.repaid += amount

        # Check if fully repaid
        if loan.repaid >= total_due:
            loan.status = "repaid"
            collateral_returned = loan.collateral
            logger.info(f"✅ [CREDIT] Loan {loan_id} fully repaid, returning {collateral_returned} MXU collateral")

            return {
                "status": "fully_repaid",
                "loan_id": loan_id,
                "amount_paid": float(amount),
                "total_repaid": float(loan.repaid),
                "collateral_returned": float(collateral_returned),
                "overpayment": float(loan.repaid - total_due) if loan.repaid > total_due else 0.0,
            }
        else:
            remaining = total_due - loan.repaid
            logger.info(f"💰 [CREDIT] Partial repayment: {amount} MXU, {remaining} MXU remaining")

            return {
                "status": "partial_repayment",
                "loan_id": loan_id,
                "amount_paid": float(amount),
                "total_repaid": float(loan.repaid),
                "remaining": float(remaining),
            }

    def check_liquidations(self) -> List[Dict[str, Any]]:
        """
        Check all active loans for liquidation conditions.

        Returns:
            List of liquidated loans
        """
        liquidations = []

        for agent_id, agent_loans in self.loans.items():
            for loan in agent_loans:
                if loan.status != "active":
                    continue

                # Check if undercollateralized or overdue
                if loan.is_undercollateralized(self.liquidation_ltv) or loan.is_overdue():
                    logger.warning(f"⚠️ [CREDIT] Liquidating loan {loan.loan_id}")

                    loan.status = "liquidated"
                    liquidations.append({
                        "loan_id": loan.loan_id,
                        "agent_id": agent_id,
                        "principal": float(loan.principal),
                        "collateral_seized": float(loan.collateral),
                        "reason": "undercollateralized" if loan.is_undercollateralized(self.liquidation_ltv) else "overdue",
                    })

        return liquidations

    def get_agent_loans(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all loans for an agent"""
        if agent_id not in self.loans:
            return []

        return [
            {
                "loan_id": loan.loan_id,
                "principal": float(loan.principal),
                "collateral": float(loan.collateral),
                "interest_rate": float(loan.interest_rate),
                "issued_at": loan.issued_at.isoformat(),
                "due_date": loan.due_date.isoformat(),
                "total_due": float(loan.total_due()),
                "repaid": float(loan.repaid),
                "status": loan.status,
            }
            for loan in self.loans[agent_id]
        ]

    def get_total_debt(self, agent_id: str) -> Decimal:
        """Calculate agent's total outstanding debt"""
        if agent_id not in self.loans:
            return Decimal("0")

        total_debt = Decimal("0")
        for loan in self.loans[agent_id]:
            if loan.status == "active":
                total_debt += loan.total_due() - loan.repaid

        return total_debt

    def _find_loan(self, agent_id: str, loan_id: str) -> Optional[Loan]:
        """Find a specific loan"""
        if agent_id not in self.loans:
            return None

        for loan in self.loans[agent_id]:
            if loan.loan_id == loan_id:
                return loan

        return None

    def get_system_stats(self) -> Dict[str, Any]:
        """Get credit system statistics"""
        total_loans = 0
        active_loans = 0
        total_principal = Decimal("0")
        total_collateral = Decimal("0")

        for agent_loans in self.loans.values():
            for loan in agent_loans:
                total_loans += 1
                if loan.status == "active":
                    active_loans += 1
                    total_principal += loan.principal
                    total_collateral += loan.collateral

        return {
            "total_loans": total_loans,
            "active_loans": active_loans,
            "total_principal": float(total_principal),
            "total_collateral": float(total_collateral),
            "collateralization_ratio": float(total_collateral / total_principal) if total_principal > 0 else 0.0,
        }
