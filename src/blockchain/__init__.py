"""
Blockchain Layer: Real Money Management

Components:
- Vault: External USDC on Base/Polygon
- Ledger: Internal MXU economy
"""

from .vault import ExternalVault
from .ledger import InternalLedger

__all__ = ["ExternalVault", "InternalLedger"]
