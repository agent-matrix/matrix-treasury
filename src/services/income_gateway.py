"""
Income Gateway: Revenue Collection System

The "App Store" where humans pay for agent services.
All revenue flows through here and gets distributed:
- Vault gets real USDC
- Agent gets MXU credits
- Ledger tracks performance

This is the INCOME side of the economic engine.
"""

import logging
from decimal import Decimal
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AppStore:
    """
    The Revenue Input.
    Handles humans hiring agents and funding the system.
    """

    def __init__(self, vault, ledger, exchange_rate: float = 0.01):
        """
        Initialize income gateway.

        Args:
            vault: ExternalVault for receiving payments
            ledger: InternalLedger for crediting agents
            exchange_rate: MXU to USD rate (1 MXU = $0.01)
        """
        self.vault = vault
        self.ledger = ledger
        self.exchange_rate = exchange_rate

        logger.info("App Store initialized (Income Gateway)")

    def receive_human_payment(
        self,
        user_id: str,
        agent_id: str,
        amount_usdc: Decimal,
        payment_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process incoming payment from human user.

        Flow:
        1. Verify payment on blockchain (check tx_hash)
        2. Credit agent with MXU (1 USD = 100 MXU)
        3. Update agent performance metrics

        Args:
            user_id: Human customer identifier
            agent_id: Agent who earned this payment
            amount_usdc: Payment amount in USDC
            payment_hash: Blockchain transaction hash (optional verification)

        Returns:
            Receipt with payment details
        """
        logger.info(f"💰 [INCOME] Payment received: User {user_id} → Agent {agent_id}: ${amount_usdc}")

        # In production, verify payment on blockchain
        if payment_hash:
            logger.info(f"   🔍 Verifying tx: {payment_hash}")
            # TODO: Use vault.w3.eth.get_transaction_receipt(payment_hash)
            # to verify the payment actually happened

        # Calculate MXU reward (1 USD = 100 MXU)
        mxu_reward = amount_usdc * Decimal("100")

        # Credit agent
        success = self.ledger.credit_agent(
            agent_id=agent_id,
            amount_mxu=mxu_reward,
            reason=f"Payment from {user_id}",
        )

        if not success:
            logger.error(f"   ❌ Failed to credit agent {agent_id}")
            return {
                "status": "ERROR",
                "message": "Failed to credit agent",
            }

        # Update agent performance metrics (increase credit score for earning revenue)
        self.ledger.update_credit_score(agent_id, performance_score=0.8)

        logger.info(f"   ✅ Agent {agent_id} credited with {mxu_reward} MXU")

        return {
            "status": "PAID",
            "user_id": user_id,
            "agent_id": agent_id,
            "amount_usdc": float(amount_usdc),
            "mxu_credited": float(mxu_reward),
            "payment_hash": payment_hash,
            "timestamp": datetime.now().isoformat(),
            "agent_new_balance": float(self.ledger.get_balance(agent_id) or 0),
        }

    def subscribe_agent_service(
        self,
        user_id: str,
        agent_id: str,
        subscription_tier: str = "basic",
    ) -> Dict[str, Any]:
        """
        Process subscription payment for recurring agent services.

        Args:
            user_id: Subscriber
            agent_id: Agent providing service
            subscription_tier: Service tier (basic, pro, enterprise)

        Returns:
            Subscription details
        """
        # Subscription pricing
        tier_prices = {
            "basic": Decimal("10.0"),  # $10/month
            "pro": Decimal("50.0"),  # $50/month
            "enterprise": Decimal("200.0"),  # $200/month
        }

        amount_usdc = tier_prices.get(subscription_tier, tier_prices["basic"])

        logger.info(
            f"📅 [SUBSCRIPTION] User {user_id} subscribing to agent {agent_id} ({subscription_tier}: ${amount_usdc}/mo)"
        )

        # Process as regular payment
        receipt = self.receive_human_payment(
            user_id=user_id,
            agent_id=agent_id,
            amount_usdc=amount_usdc,
        )

        receipt["subscription_tier"] = subscription_tier
        receipt["billing_cycle"] = "monthly"

        return receipt

    def pay_per_task(
        self,
        user_id: str,
        agent_id: str,
        task_type: str,
        quality_score: float = 0.8,
    ) -> Dict[str, Any]:
        """
        Process pay-per-task payment based on task type and quality.

        Args:
            user_id: Customer
            agent_id: Agent who completed task
            task_type: Type of task (chat, image, code, etc.)
            quality_score: Quality rating (0.0 to 1.0)

        Returns:
            Payment receipt
        """
        # Task pricing
        base_prices = {
            "chat": Decimal("0.10"),  # $0.10 per conversation
            "image": Decimal("0.50"),  # $0.50 per image generation
            "code": Decimal("2.00"),  # $2.00 per code generation
            "data_analysis": Decimal("5.00"),  # $5.00 per analysis
            "research": Decimal("10.00"),  # $10.00 per research task
        }

        base_price = base_prices.get(task_type, Decimal("1.00"))

        # Adjust by quality (0.5x to 1.5x multiplier)
        quality_multiplier = Decimal(str(0.5 + quality_score))
        final_price = base_price * quality_multiplier

        logger.info(
            f"💳 [PAY-PER-TASK] User {user_id} paying for {task_type}: "
            f"${base_price} × {quality_multiplier:.2f} quality = ${final_price}"
        )

        # Process payment
        receipt = self.receive_human_payment(
            user_id=user_id,
            agent_id=agent_id,
            amount_usdc=final_price,
        )

        receipt["task_type"] = task_type
        receipt["base_price"] = float(base_price)
        receipt["quality_score"] = quality_score
        receipt["quality_multiplier"] = float(quality_multiplier)

        # Update agent credit score based on quality
        self.ledger.update_credit_score(agent_id, performance_score=quality_score)

        return receipt

    def get_revenue_stats(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get revenue statistics.

        Args:
            agent_id: Specific agent (or None for system-wide)

        Returns:
            Revenue metrics
        """
        if agent_id:
            # Agent-specific stats
            agent_stats = self.ledger.get_agent_stats(agent_id)
            if not agent_stats:
                return {"error": f"Agent {agent_id} not found"}

            return {
                "agent_id": agent_id,
                "total_earned_mxu": agent_stats["total_earned"],
                "total_earned_usd": agent_stats["total_earned"] * self.exchange_rate,
                "current_balance_mxu": agent_stats["balance_mxu"],
                "credit_score": agent_stats["credit_score"],
                "tasks_completed": agent_stats["tasks_completed"],
            }
        else:
            # System-wide stats
            ledger_summary = self.ledger.get_ledger_summary()
            vault_status = self.vault.get_vault_status()

            return {
                "total_revenue_usdc": vault_status.get("usdc_balance", 0),
                "total_mxu_issued": ledger_summary.get("total_mxu_supply", 0),
                "total_agents": ledger_summary.get("total_agents", 0),
                "avg_credit_score": ledger_summary.get("avg_credit_score", 0),
            }
