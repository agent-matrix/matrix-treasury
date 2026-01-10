"""
Akash Infrastructure Manager

Manages decentralized infrastructure (DePIN) on Akash Network.
Ensures the agent pays its own hosting bills automatically.

Akash Network: Decentralized cloud compute marketplace
- No credit cards required
- Pay-as-you-go with crypto
- Censorship-resistant hosting
"""

import os
import logging
import subprocess
from decimal import Decimal
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AkashManager:
    """
    Manages Decentralized Infrastructure (DePIN).
    Ensures the agent pays its own rent automatically.
    """

    def __init__(
        self,
        vault,
        provider_address: Optional[str] = None,
        daily_cost_usd: float = 1.50,
    ):
        """
        Initialize Akash manager.

        Args:
            vault: ExternalVault for payments
            provider_address: Akash provider wallet address
            daily_cost_usd: Daily hosting cost in USD
        """
        self.vault = vault
        self.provider_address = provider_address or os.getenv(
            "AKASH_PROVIDER_ADDRESS", "akash1..."
        )
        self.daily_cost = Decimal(str(daily_cost_usd))

        logger.info(
            f"Akash Manager initialized: ${self.daily_cost}/day to {self.provider_address}"
        )

    def check_lease_status(self) -> Dict[str, Any]:
        """
        Check current Akash lease status.

        Returns:
            {
                "active": bool,
                "days_remaining": int,
                "expires_at": str (ISO timestamp),
                "cost_per_day": float,
            }

        Note: This is a simplified implementation.
        In production, use Akash CLI or SDK to query lease status.
        """
        try:
            # Mock implementation - replace with actual Akash CLI call
            # Example: subprocess.run(["akash", "query", "market", "lease", "list"])

            # For now, return mock data
            mock_days_remaining = 1  # Simulate low balance for demo

            expires_at = datetime.now() + timedelta(days=mock_days_remaining)

            return {
                "active": True,
                "days_remaining": mock_days_remaining,
                "expires_at": expires_at.isoformat(),
                "cost_per_day": float(self.daily_cost),
                "provider": self.provider_address,
            }

        except Exception as e:
            logger.error(f"Failed to check Akash lease status: {e}")
            return {
                "active": False,
                "days_remaining": 0,
                "error": str(e),
            }

    def check_and_renew(self, min_days: int = 2, renewal_days: int = 7) -> bool:
        """
        Check lease and renew if low.

        Runs daily via cron. If lease is low, pays rent automatically.

        Args:
            min_days: Trigger renewal if days_remaining < this
            renewal_days: How many days to pay for

        Returns:
            True if renewal executed, False otherwise
        """
        logger.info("⚙️ [AKASH] Checking infrastructure lease status...")

        status = self.check_lease_status()

        if not status.get("active"):
            logger.error("   ❌ Lease is not active!")
            return False

        days_remaining = status.get("days_remaining", 0)

        if days_remaining < min_days:
            logger.warning(
                f"   ⚠️ Lease expiring soon! Days remaining: {days_remaining}"
            )
            logger.info(f"   🔄 Renewing for {renewal_days} days...")

            # Calculate cost
            renewal_cost = self.daily_cost * Decimal(str(renewal_days))

            try:
                # Pay for renewal
                tx_result = self.vault.pay_external_bill(
                    to_address=self.provider_address,
                    amount_usdc=renewal_cost,
                    memo=f"Akash hosting renewal: {renewal_days} days",
                )

                logger.info(
                    f"   ✅ Renewal paid: ${renewal_cost} (tx: {tx_result.get('tx_hash')})"
                )

                # In production, also call Akash CLI to update lease
                # subprocess.run(["akash", "tx", "market", "lease", "create", ...])

                return True

            except Exception as e:
                logger.error(f"   ❌ Failed to renew lease: {e}")
                return False

        else:
            logger.info(f"   ✅ Lease healthy: {days_remaining} days remaining")
            return False

    def get_infrastructure_status(self) -> Dict[str, Any]:
        """Get comprehensive infrastructure status."""
        lease_status = self.check_lease_status()
        vault_status = self.vault.get_vault_status()

        days_remaining = lease_status.get("days_remaining", 0)
        cost_per_day = lease_status.get("cost_per_day", 0)

        # Calculate runway (how many days can we afford)
        usdc_balance = vault_status.get("usdc_balance", 0)
        runway_days = int(usdc_balance / cost_per_day) if cost_per_day > 0 else 0

        return {
            "lease": lease_status,
            "vault_balance_usdc": usdc_balance,
            "cost_per_day_usd": cost_per_day,
            "runway_days": runway_days,
            "health_status": (
                "HEALTHY" if days_remaining >= 7 and runway_days >= 30
                else "WARNING" if days_remaining >= 2 and runway_days >= 7
                else "CRITICAL"
            ),
        }

    def estimate_monthly_cost(self) -> Decimal:
        """Estimate monthly infrastructure cost."""
        return self.daily_cost * Decimal("30")

    def shutdown_if_bankrupt(self) -> bool:
        """
        Emergency shutdown if treasury is empty.

        This is the "death" scenario - system cannot afford to stay alive.

        Returns:
            True if shutdown initiated
        """
        try:
            balance = self.vault.get_real_balance()

            if balance < self.daily_cost:
                logger.critical(
                    f"🚨 [AKASH] BANKRUPTCY DETECTED: Balance ${balance} < daily cost ${self.daily_cost}"
                )
                logger.critical("   System will shut down gracefully...")

                # In production: Close lease, backup data, send alerts
                # subprocess.run(["akash", "tx", "market", "lease", "close", ...])

                return True

            return False

        except Exception as e:
            logger.error(f"Failed to check bankruptcy status: {e}")
            return False
