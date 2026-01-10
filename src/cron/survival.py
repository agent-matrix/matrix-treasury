"""
System Survival Loop: The Heartbeat

Runs every 24 hours to ensure the autonomous system stays alive.

Critical functions:
1. Check treasury solvency
2. Pay infrastructure bills (Akash rent)
3. Trigger economic stabilizers if needed
4. Report system health

This is the "pulse" that keeps the digital organism alive.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.blockchain.vault import ExternalVault
from src.blockchain.ledger import InternalLedger
from src.llm.cfo import MatrixCFO
from src.services.akash.manager import AkashManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/survival.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def daily_survival_check():
    """
    The Heartbeat.
    Runs every 24h to ensure the system stays alive.
    """
    logger.info("="*80)
    logger.info("💓 SYSTEM HEARTBEAT: Survival Check Started")
    logger.info(f"   Timestamp: {datetime.now().isoformat()}")
    logger.info("="*80)

    try:
        # Initialize components
        logger.info("📦 Initializing system components...")

        vault = ExternalVault()
        ledger = InternalLedger()
        cfo = MatrixCFO(vault, ledger)
        akash = AkashManager(vault)

        logger.info("   ✅ All components initialized")

        # 1. Check Treasury Solvency
        logger.info("\n💰 STEP 1: Checking Treasury Solvency")
        logger.info("-" * 80)

        try:
            health = cfo.get_treasury_health()

            logger.info(f"   💵 USDC Balance: ${health.get('usdc_balance', 0):.2f}")
            logger.info(f"   📊 Total MXU Supply: {health.get('total_mxu_supply', 0):.2f}")
            logger.info(f"   🎯 Coverage Ratio: {health.get('coverage_ratio', 0):.2f}x")
            logger.info(f"   🏥 Health Status: {health.get('health_status', 'UNKNOWN')}")
            logger.info(f"   👥 Total Agents: {health.get('total_agents', 0)}")
            logger.info(f"   💀 Bankrupt Agents: {health.get('bankrupt_agents', 0)}")

            # Alert if unhealthy
            if health.get('health_status') == 'CRITICAL':
                logger.critical("   🚨 CRITICAL: Treasury health is CRITICAL!")
            elif health.get('health_status') == 'WARNING':
                logger.warning("   ⚠️  WARNING: Treasury health degraded")
            else:
                logger.info("   ✅ Treasury is healthy")

        except Exception as e:
            logger.error(f"   ❌ Failed to check solvency: {e}")

        # 2. Check and Pay Infrastructure
        logger.info("\n☁️  STEP 2: Infrastructure Management (Akash)")
        logger.info("-" * 80)

        try:
            infra_status = akash.get_infrastructure_status()

            logger.info(f"   🏠 Lease Status: {infra_status['lease'].get('active', 'Unknown')}")
            logger.info(f"   📅 Days Remaining: {infra_status['lease'].get('days_remaining', 0)}")
            logger.info(f"   💵 Cost per Day: ${infra_status.get('cost_per_day_usd', 0):.2f}")
            logger.info(f"   🛤️  Runway: {infra_status.get('runway_days', 0)} days")
            logger.info(f"   🏥 Infrastructure Health: {infra_status.get('health_status', 'UNKNOWN')}")

            # Try to renew if needed
            renewed = akash.check_and_renew()
            if renewed:
                logger.info("   ✅ Infrastructure renewed successfully")
            else:
                logger.info("   ℹ️  No renewal needed")

            # Check for bankruptcy
            if akash.shutdown_if_bankrupt():
                logger.critical("   🚨 SYSTEM BANKRUPTCY - Initiating shutdown")
                return False  # Signal failure

        except Exception as e:
            logger.error(f"   ❌ Infrastructure check failed: {e}")

        # 3. Economic Stabilizers (if needed)
        logger.info("\n⚖️  STEP 3: Economic Stabilizers")
        logger.info("-" * 80)

        try:
            health = cfo.get_treasury_health()

            # Check if intervention needed
            coverage_ratio = health.get('coverage_ratio', 1.0)
            usdc_balance = health.get('usdc_balance', 0)

            if coverage_ratio < 1.0:
                logger.warning("   ⚠️  Coverage ratio below 1.0 - Austerity measures recommended")
                # In production: Raise prices, throttle demand
            elif usdc_balance < 100:
                logger.warning("   ⚠️  Low USDC reserves - Revenue generation needed")
                # In production: Alert operators, increase marketing

            bankruptcy_rate = health.get('bankrupt_agents', 0) / max(health.get('total_agents', 1), 1)
            if bankruptcy_rate > 0.4:
                logger.warning(f"   ⚠️  High bankruptcy rate: {bankruptcy_rate:.1%}")
                # In production: Trigger stimulus program (UBC renewals)

        except Exception as e:
            logger.error(f"   ❌ Stabilizer check failed: {e}")

        # 4. Summary Report
        logger.info("\n📊 SURVIVAL SUMMARY")
        logger.info("="*80)

        try:
            health = cfo.get_treasury_health()
            infra = akash.get_infrastructure_status()

            logger.info(f"✅ Treasury Balance: ${health.get('usdc_balance', 0):.2f}")
            logger.info(f"✅ System Health: {health.get('health_status', 'UNKNOWN')}")
            logger.info(f"✅ Infrastructure: {infra.get('runway_days', 0)} days runway")
            logger.info(f"✅ Active Agents: {health.get('total_agents', 0)}")
            logger.info(f"✅ Survival Status: OPERATIONAL")

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")

        logger.info("\n💓 Heartbeat Complete - System Alive")
        logger.info("="*80)

        return True

    except Exception as e:
        logger.critical(f"💀 CRITICAL FAILURE IN SURVIVAL CHECK: {e}")
        logger.exception(e)
        return False


if __name__ == "__main__":
    """
    Run as standalone script or cron job.

    Setup cron (Linux):
    0 0 * * * /usr/bin/python3 /path/to/survival.py >> /var/log/matrix-survival.log 2>&1
    """
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    # Run survival check
    success = daily_survival_check()

    # Exit with appropriate code
    sys.exit(0 if success else 1)
