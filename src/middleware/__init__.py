"""
Middleware Layer: Payment Automation

Components:
- ATXP: HTTP 402 automatic payment handling
"""

from .atxp import ATXPMiddleware, PaymentRequiredException, get_with_payment, post_with_payment

__all__ = ["ATXPMiddleware", "PaymentRequiredException", "get_with_payment", "post_with_payment"]
