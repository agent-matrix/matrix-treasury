"""
Core Configuration for Matrix Treasury
Canonical Standard: 1 MXU = 1 Wh (Watt-hour of compute-energy equivalent)
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import os
from enum import Enum

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class CostOracle:
    """
    Real-world cost inputs (updated periodically from external sources)
    These values should be updated via admin API or automated oracle
    """
    electricity_usd_per_kwh: float = float(os.getenv("ELECTRICITY_USD_PER_KWH", "0.15"))
    pue: float = float(os.getenv("PUE", "1.20"))  # Power Usage Effectiveness
    gpu_usd_per_hour: float = float(os.getenv("GPU_USD_PER_HOUR", "2.50"))
    avg_gpu_watts: float = float(os.getenv("AVG_GPU_WATTS", "450.0"))
    
    # Cloud infrastructure costs
    storage_usd_per_gb_month: float = 0.10
    bandwidth_usd_per_gb: float = 0.05
    ram_usd_per_gb_hour: float = 0.01
    cpu_usd_per_core_hour: float = 0.05
    
    def update_from_external(self, oracle_data: Dict):
        """Update costs from external oracle service"""
        if "electricity_usd_per_kwh" in oracle_data:
            self.electricity_usd_per_kwh = oracle_data["electricity_usd_per_kwh"]
        if "gpu_usd_per_hour" in oracle_data:
            self.gpu_usd_per_hour = oracle_data["gpu_usd_per_hour"]
        # Add more fields as needed

@dataclass
class SystemPolicy:
    """
    Constitutional parameters (require governance vote to change)
    These are the immutable laws of the Matrix economy
    """
    # Economic stability
    overhead_margin: float = 0.10  # 10% safety margin
    smoothing_alpha: float = 0.2   # EMA smoothing factor
    breaker_spike_mult: float = 1.5  # Circuit breaker threshold
    reserve_target_days: float = 14.0  # Target reserve coverage
    
    # Social safety net
    ubc_grant_mxu: float = 500.0  # Universal Basic Compute grant
    ubc_renew_mxu: float = 200.0  # Renewal amount
    ubc_max_renewals: int = 3     # Maximum renewals per agent
    ubc_renewal_cooldown_hours: int = 168  # 1 week
    
    # Taxation (progressive)
    tx_tax_rate_base: float = 0.01   # 1% minimum
    tx_tax_rate_max: float = 0.05    # 5% maximum
    tx_tax_wealth_threshold: float = 10000.0  # MXU
    
    # Resource accounting weights (Wh-equivalent conversions)
    # These convert state/resource usage into energy-equivalent MXU
    WH_PER_GB_SECOND_RAM: float = 0.00002
    WH_PER_MB_BANDWIDTH: float = 0.000002
    WH_PER_GB_DAY_STORAGE: float = 0.02
    WH_PER_CPU_SECOND: float = 0.005
    
    # Anti-gaming & security
    max_supply_concentration: float = 0.05  # 5% max ownership
    sybil_similarity_threshold: float = 0.85
    max_self_dealing_ratio: float = 0.10
    min_transaction_mxu: float = 0.01
    max_transaction_mxu: float = 1000000.0
    
    # Bankruptcy ladder thresholds
    throttle_threshold: float = 0.10  # 10% of bill
    hibernate_threshold: float = 0.01  # 1% of bill
    
    # Pool allocation ratios
    commons_split_ratio: float = 0.30  # 30% to commons on mint
    infrastructure_pool_ratio: float = 0.50
    ubc_pool_ratio: float = 0.40
    emergency_pool_ratio: float = 0.10

@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    database: str = os.getenv("DB_NAME", "matrix_treasury")
    user: str = os.getenv("DB_USER", "matrix")
    password: str = os.getenv("DB_PASSWORD", "changeme")
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class RedisConfig:
    """Redis configuration for caching and pub/sub"""
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    db: int = int(os.getenv("REDIS_DB", "0"))
    password: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"

@dataclass
class APIConfig:
    """API server configuration"""
    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "8000"))
    reload: bool = os.getenv("API_RELOAD", "false").lower() == "true"
    workers: int = int(os.getenv("API_WORKERS", "4"))
    log_level: str = os.getenv("LOG_LEVEL", "info")

@dataclass
class Config:
    """Main application configuration"""
    environment: Environment = Environment.DEVELOPMENT
    oracle: CostOracle = field(default_factory=CostOracle)
    policy: SystemPolicy = field(default_factory=SystemPolicy)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    api: APIConfig = field(default_factory=APIConfig)
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "changeme-in-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables"""
        env_str = os.getenv("ENVIRONMENT", "development")
        environment = Environment(env_str)
        return cls(environment=environment)

# Global config instance
config = Config.from_env()
