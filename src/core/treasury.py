"""
Matrix Treasury - The Central Bank
Implements the complete economic engine with reserve management,
pricing, minting, burning, and taxation.
"""

import math
from typing import Dict, Optional, Tuple
from datetime import datetime
import logging

from src.core.config import CostOracle, SystemPolicy
from src.core.exceptions import InsufficientReserves

logger = logging.getLogger(__name__)

class MatrixTreasury:
    """
    The Central Bank of the Matrix Economy
    
    Core Principles:
    - 1 MXU = 1 Wh of compute-energy equivalent
    - All minting backed by USD reserves
    - All burning represents real cost consumption
    - Automatic stabilizers maintain solvency
    """
    
    def __init__(self, oracle: CostOracle, policy: SystemPolicy):
        self.oracle = oracle
        self.policy = policy
        
        # Core economic state
        self.reserve_usd: float = 0.0
        self.mxu_supply: float = 0.0
        
        # Public pools (funded by taxes and commons allocation)
        self.infrastructure_pool_mxu: float = 0.0
        self.ubc_pool_mxu: float = 0.0
        self.emergency_pool_mxu: float = 0.0
        
        # Price smoothing state
        self._ema_usd_per_mxu: Optional[float] = None
        self._last_raw_price: Optional[float] = None
        self._last_price_update: datetime = datetime.now()
        
        # Metrics & monitoring
        self.total_transactions: int = 0
        self.total_mxu_burned: float = 0.0
        self.total_mxu_minted: float = 0.0
        self.crisis_mode: bool = False
        
        logger.info("Treasury initialized with MXU standard: 1 MXU = 1 Wh")
    
    # =========================================================================
    # PRICING ENGINE
    # =========================================================================
    
    def _raw_usd_per_mxu(self) -> float:
        """
        Calculate raw cost per MXU from current oracle data.
        
        Formula:
        USD/MXU = (Energy_Cost + Capacity_Cost) * (1 + Margin)
        
        Where:
        - Energy_Cost = (USD/kWh / 1000) * PUE  [per Wh]
        - Capacity_Cost = GPU_USD/hour / Wh_per_GPU_hour
        """
        # Energy cost per Wh (with PUE overhead)
        usd_per_wh_energy = (
            self.oracle.electricity_usd_per_kwh / 1000.0
        ) * self.oracle.pue
        
        # Capacity cost per Wh (GPU rental amortized)
        wh_per_gpu_hour = self.oracle.avg_gpu_watts * 1.0  # 1 hour
        usd_per_wh_capacity = (
            self.oracle.gpu_usd_per_hour / wh_per_gpu_hour
        )
        
        # Combined cost with safety margin
        base_cost = usd_per_wh_energy + usd_per_wh_capacity
        return base_cost * (1.0 + self.policy.overhead_margin)
    
    def usd_per_mxu(self) -> float:
        """
        Get smoothed USD/MXU exchange rate with circuit breaker.
        
        Uses exponential moving average for stability,
        with immediate updates on spike detection.
        """
        raw = self._raw_usd_per_mxu()
        
        # Initialize on first call
        if self._ema_usd_per_mxu is None:
            self._ema_usd_per_mxu = raw
            self._last_raw_price = raw
            self._last_price_update = datetime.now()
            return raw
        
        # Circuit breaker: immediate update if spike detected
        if raw > self._last_raw_price * self.policy.breaker_spike_mult:
            logger.warning(
                f"Circuit breaker triggered: "
                f"Price spike from {self._last_raw_price:.6f} to {raw:.6f}"
            )
            self._ema_usd_per_mxu = raw
        else:
            # Exponential moving average smoothing
            alpha = self.policy.smoothing_alpha
            self._ema_usd_per_mxu = (
                alpha * raw + (1 - alpha) * self._ema_usd_per_mxu
            )
        
        self._last_raw_price = raw
        self._last_price_update = datetime.now()
        
        return self._ema_usd_per_mxu
    
    def mxu_per_usd(self) -> float:
        """Exchange rate: USD → MXU"""
        price = self.usd_per_mxu()
        return 1.0 / price if price > 0 else 0.0
    
    # =========================================================================
    # MINTING & BURNING (Reserve-Backed Operations)
    # =========================================================================
    
    def mint_from_deposit(self, usd_amount: float) -> Dict[str, float]:
        """
        Mint new MXU backed by USD deposit.
        
        Allocation:
        - 70% to depositor
        - 30% to public pools (infrastructure, UBC, emergency)
        
        Args:
            usd_amount: USD amount deposited
            
        Returns:
            Dictionary with minting details
        """
        if usd_amount <= 0:
            return {
                "minted": 0.0,
                "user_share": 0.0,
                "commons_share": 0.0,
                "exchange_rate": self.mxu_per_usd()
            }
        
        # Update reserves
        self.reserve_usd += usd_amount
        
        # Calculate minted amount at current rate
        total_minted = usd_amount * self.mxu_per_usd()
        
        # Split allocation
        user_share = total_minted * (1.0 - self.policy.commons_split_ratio)
        commons_share = total_minted * self.policy.commons_split_ratio
        
        # Distribute commons to pools
        self.infrastructure_pool_mxu += commons_share * self.policy.infrastructure_pool_ratio
        self.ubc_pool_mxu += commons_share * self.policy.ubc_pool_ratio
        self.emergency_pool_mxu += commons_share * self.policy.emergency_pool_ratio
        
        # Update supply
        self.mxu_supply += total_minted
        self.total_mxu_minted += total_minted
        
        logger.info(
            f"Minted {total_minted:.2f} MXU from ${usd_amount:.2f} USD deposit. "
            f"User: {user_share:.2f}, Commons: {commons_share:.2f}"
        )
        
        return {
            "minted": total_minted,
            "user_share": user_share,
            "commons_share": commons_share,
            "exchange_rate": self.mxu_per_usd(),
            "pools": {
                "infrastructure": commons_share * self.policy.infrastructure_pool_ratio,
                "ubc": commons_share * self.policy.ubc_pool_ratio,
                "emergency": commons_share * self.policy.emergency_pool_ratio
            }
        }
    
    def burn_for_costs(self, mxu_amount: float) -> float:
        """
        Burn MXU to pay real infrastructure costs.
        This is the survival constraint: reserves must cover all burns.
        
        Args:
            mxu_amount: Amount of MXU to burn
            
        Returns:
            USD equivalent cost
            
        Raises:
            InsufficientReserves: If reserves cannot cover cost
        """
        mxu_amount = max(0.0, mxu_amount)
        usd_equiv = mxu_amount * self.usd_per_mxu()
        
        # CRITICAL: Solvency check
        if self.reserve_usd < usd_equiv:
            self.crisis_mode = True
            raise InsufficientReserves(
                f"Cannot burn {mxu_amount:.2f} MXU (${usd_equiv:.2f} USD). "
                f"Only ${self.reserve_usd:.2f} USD in reserves."
            )
        
        # Execute burn
        self.reserve_usd -= usd_equiv
        self.mxu_supply -= mxu_amount
        self.total_mxu_burned += mxu_amount
        
        logger.debug(
            f"Burned {mxu_amount:.4f} MXU (${usd_equiv:.4f} USD). "
            f"Reserve: ${self.reserve_usd:.2f}"
        )
        
        return usd_equiv
    
    # =========================================================================
    # TAXATION (Progressive)
    # =========================================================================
    
    def calculate_tx_tax_rate(self, sender_balance_mxu: float) -> float:
        """
        Calculate progressive transaction tax rate based on wealth.
        
        Wealthier agents contribute more to public goods.
        """
        wealth_factor = sender_balance_mxu / self.policy.tx_tax_wealth_threshold
        rate = self.policy.tx_tax_rate_base + (wealth_factor * 0.01)
        
        # Clamp to constitutional limits
        return max(
            self.policy.tx_tax_rate_base,
            min(self.policy.tx_tax_rate_max, rate)
        )
    
    def collect_tax(
        self,
        amount_mxu: float,
        sender_balance_mxu: float
    ) -> Dict[str, float]:
        """
        Collect transaction tax and allocate to public pools.
        
        Returns:
            Dictionary with tax details
        """
        rate = self.calculate_tx_tax_rate(sender_balance_mxu)
        tax = amount_mxu * rate
        net = amount_mxu - tax
        
        # Allocate tax revenue to pools
        self.infrastructure_pool_mxu += tax * self.policy.infrastructure_pool_ratio
        self.ubc_pool_mxu += tax * self.policy.ubc_pool_ratio
        self.emergency_pool_mxu += tax * self.policy.emergency_pool_ratio
        
        self.total_transactions += 1
        
        logger.debug(f"Collected {tax:.4f} MXU tax at {rate:.2%} rate")
        
        return {
            "tax": tax,
            "rate": rate,
            "net": net,
            "gross": amount_mxu
        }
    
    # =========================================================================
    # HEALTH MONITORING
    # =========================================================================
    
    def reserve_health(
        self,
        projected_mxu_burn_per_day: float
    ) -> Dict[str, any]:
        """
        Calculate reserve health metrics.
        
        Key metric: coverage_ratio = reserves / target_reserves
        - > 1.0: Healthy
        - < 1.0: Crisis mode
        """
        daily_cost_usd = projected_mxu_burn_per_day * self.usd_per_mxu()
        target_usd = daily_cost_usd * self.policy.reserve_target_days
        
        coverage_ratio = (
            self.reserve_usd / target_usd if target_usd > 0 else math.inf
        )
        
        coverage_days = (
            self.reserve_usd / daily_cost_usd
            if daily_cost_usd > 0 else math.inf
        )
        
        # Update crisis status
        previous_crisis = self.crisis_mode
        self.crisis_mode = coverage_ratio < 1.0
        
        if self.crisis_mode and not previous_crisis:
            logger.warning(
                f"CRISIS MODE ACTIVATED: Reserve coverage at {coverage_ratio:.2%}"
            )
        elif not self.crisis_mode and previous_crisis:
            logger.info(
                f"Crisis resolved: Reserve coverage at {coverage_ratio:.2%}"
            )
        
        return {
            "reserve_usd": self.reserve_usd,
            "daily_cost_usd": daily_cost_usd,
            "target_usd": target_usd,
            "coverage_ratio": coverage_ratio,
            "coverage_days": coverage_days,
            "crisis_mode": self.crisis_mode,
            "mxu_supply": self.mxu_supply,
            "exchange_rate": self.usd_per_mxu()
        }
    
    def get_state(self) -> Dict[str, any]:
        """Get complete treasury state for monitoring/debugging"""
        return {
            "reserve_usd": self.reserve_usd,
            "mxu_supply": self.mxu_supply,
            "pools": {
                "infrastructure": self.infrastructure_pool_mxu,
                "ubc": self.ubc_pool_mxu,
                "emergency": self.emergency_pool_mxu
            },
            "pricing": {
                "usd_per_mxu": self.usd_per_mxu(),
                "mxu_per_usd": self.mxu_per_usd(),
                "raw_price": self._raw_usd_per_mxu()
            },
            "metrics": {
                "total_transactions": self.total_transactions,
                "total_mxu_burned": self.total_mxu_burned,
                "total_mxu_minted": self.total_mxu_minted,
                "crisis_mode": self.crisis_mode
            },
            "timestamp": datetime.now().isoformat()
        }
