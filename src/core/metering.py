"""
Resource Metering System
Converts raw usage metrics into MXU (Wh-equivalent) billing.

Only the scheduler/guardian can issue billable metering events.
"""

from typing import Dict, Optional
from datetime import datetime
import logging

from src.core.config import CostOracle, SystemPolicy
from src.core.exceptions import MeteringError

logger = logging.getLogger(__name__)

class ResourceMetering:
    """
    Converts computational resource usage into MXU billing.
    
    Four-part tariff:
    1. Energy: Measured GPU/CPU work
    2. Capacity: Reservation/availability rent
    3. State: RAM, storage, bandwidth costs
    4. Governance: Security/infrastructure overhead
    """
    
    @staticmethod
    def validate_metering(metering: Dict[str, float]) -> None:
        """Validate metering data"""
        required_fields = ["metering_source", "timestamp"]
        
        for field in required_fields:
            if field not in metering:
                raise MeteringError(f"Missing required field: {field}")
        
        # Only guardian can issue billable metering
        if metering.get("metering_source") != "GUARDIAN":
            raise MeteringError(
                "Only GUARDIAN can issue billable metering events"
            )
        
        # Validate numeric fields
        numeric_fields = [
            "gpu_seconds", "cpu_seconds", "ram_gb_seconds",
            "bandwidth_mb", "storage_gb_days"
        ]
        
        for field in numeric_fields:
            if field in metering:
                value = metering[field]
                if not isinstance(value, (int, float)) or value < 0:
                    raise MeteringError(
                        f"Invalid {field}: must be non-negative number"
                    )
    
    @staticmethod
    def bill_from_metering(
        metering: Dict[str, float],
        oracle: CostOracle,
        policy: SystemPolicy
    ) -> Dict[str, any]:
        """
        Convert metering data to MXU billing.
        
        All resource categories are converted to Wh-equivalent
        via policy weights, maintaining the MXU = Wh standard.
        
        Args:
            metering: Resource usage data
            oracle: Cost oracle for pricing
            policy: System policy for conversion weights
            
        Returns:
            Detailed billing breakdown
        """
        # Validate first
        ResourceMetering.validate_metering(metering)
        
        # =====================================================================
        # 1. ENERGY: Measured GPU/CPU work
        # =====================================================================
        
        gpu_seconds = metering.get("gpu_seconds", 0.0)
        avg_watts = metering.get("avg_watts", oracle.avg_gpu_watts)
        wh_gpu_energy = (gpu_seconds * avg_watts) / 3600.0
        
        cpu_seconds = metering.get("cpu_seconds", 0.0)
        cpu_cores = metering.get("cpu_cores", 1.0)
        # Estimate: 1 CPU core ≈ 15W average
        wh_cpu_energy = (cpu_seconds * cpu_cores * 15.0) / 3600.0
        
        wh_energy_total = wh_gpu_energy + wh_cpu_energy
        
        # =====================================================================
        # 2. CAPACITY: Reservation/availability rent
        # =====================================================================
        
        # Capacity rent matches energy cost in active state
        # In production, this could be time-based regardless of utilization
        wh_capacity = wh_energy_total
        
        # =====================================================================
        # 3. STATE: Memory, storage, bandwidth
        # =====================================================================
        
        ram_gb_seconds = metering.get("ram_gb_seconds", 0.0)
        wh_ram = ram_gb_seconds * policy.WH_PER_GB_SECOND_RAM
        
        bandwidth_mb = metering.get("bandwidth_mb", 0.0)
        wh_bandwidth = bandwidth_mb * policy.WH_PER_MB_BANDWIDTH
        
        storage_gb_days = metering.get("storage_gb_days", 0.0)
        wh_storage = storage_gb_days * policy.WH_PER_GB_DAY_STORAGE
        
        wh_state_total = wh_ram + wh_bandwidth + wh_storage
        
        # =====================================================================
        # 4. GOVERNANCE: Infrastructure overhead (small, steady)
        # =====================================================================
        
        # 2% overhead for security, routing, monitoring
        wh_governance = (wh_energy_total + wh_capacity + wh_state_total) * 0.02
        
        # =====================================================================
        # TOTAL BILL
        # =====================================================================
        
        total_mxu = (
            wh_energy_total +
            wh_capacity +
            wh_state_total +
            wh_governance
        )
        
        # Calculate percentages
        if total_mxu > 0:
            energy_pct = (wh_energy_total / total_mxu) * 100
            capacity_pct = (wh_capacity / total_mxu) * 100
            state_pct = (wh_state_total / total_mxu) * 100
            governance_pct = (wh_governance / total_mxu) * 100
        else:
            energy_pct = capacity_pct = state_pct = governance_pct = 0.0
        
        logger.debug(
            f"Billed {total_mxu:.4f} MXU: "
            f"Energy={energy_pct:.1f}%, "
            f"Capacity={capacity_pct:.1f}%, "
            f"State={state_pct:.1f}%, "
            f"Gov={governance_pct:.1f}%"
        )
        
        return {
            "total_mxu": total_mxu,
            "components": {
                "energy_mxu": wh_energy_total,
                "capacity_mxu": wh_capacity,
                "state_mxu": wh_state_total,
                "governance_mxu": wh_governance
            },
            "breakdown": {
                "gpu_wh": wh_gpu_energy,
                "cpu_wh": wh_cpu_energy,
                "ram_wh": wh_ram,
                "bandwidth_wh": wh_bandwidth,
                "storage_wh": wh_storage
            },
            "percentages": {
                "energy": energy_pct,
                "capacity": capacity_pct,
                "state": state_pct,
                "governance": governance_pct
            },
            "metering_metadata": {
                "source": metering.get("metering_source"),
                "timestamp": metering.get("timestamp"),
                "agent_id": metering.get("agent_id")
            }
        }
    
    @staticmethod
    def estimate_cost(
        gpu_hours: float = 0.0,
        ram_gb_hours: float = 0.0,
        storage_gb_days: float = 0.0,
        oracle: Optional[CostOracle] = None,
        policy: Optional[SystemPolicy] = None
    ) -> Dict[str, float]:
        """
        Quick cost estimation for planning purposes.
        Does NOT require guardian signature.
        """
        from src.core.config import CostOracle, SystemPolicy
        
        if oracle is None:
            oracle = CostOracle()
        if policy is None:
            policy = SystemPolicy()
        
        # Convert to metering format
        metering = {
            "metering_source": "ESTIMATION",  # Not billable
            "timestamp": datetime.now().isoformat(),
            "gpu_seconds": gpu_hours * 3600,
            "ram_gb_seconds": ram_gb_hours * 3600,
            "storage_gb_days": storage_gb_days
        }
        
        # Calculate without validation
        gpu_seconds = metering["gpu_seconds"]
        wh_energy = (gpu_seconds * oracle.avg_gpu_watts) / 3600.0
        wh_capacity = wh_energy
        wh_ram = metering["ram_gb_seconds"] * policy.WH_PER_GB_SECOND_RAM
        wh_storage = storage_gb_days * policy.WH_PER_GB_DAY_STORAGE
        
        total_mxu = wh_energy + wh_capacity + wh_ram + wh_storage
        
        return {
            "estimated_mxu": total_mxu,
            "estimated_usd": total_mxu * (oracle.electricity_usd_per_kwh / 1000.0 * oracle.pue),
            "warning": "This is an estimate only. Actual billing requires guardian metering."
        }
