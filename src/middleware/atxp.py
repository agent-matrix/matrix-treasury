"""
ATXP Payment Middleware: HTTP 402 Automatic Payment Protocol

Intercepts HTTP 402 (Payment Required) responses and automatically
pays for services using the CFO's approval system.

This enables agents to access paid APIs, tools, and services without
human intervention for procurement.

Standards:
- HTTP 402 Payment Required (RFC 7231)
- Payment headers and negotiation
"""

import logging
import requests
from typing import Dict, Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class ATXPMiddleware:
    """
    Wraps HTTP requests. Catches 402 Errors and auto-pays via CFO.

    Usage:
        middleware = ATXPMiddleware(cfo)
        response = middleware.request("agent_123", "https://api.example.com/data")
    """

    def __init__(self, cfo):
        """
        Initialize ATXP middleware.

        Args:
            cfo: MatrixCFO instance for payment approval
        """
        self.cfo = cfo

    def request(
        self,
        agent_id: str,
        url: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ) -> requests.Response:
        """
        Make an HTTP request with automatic payment handling.

        Args:
            agent_id: Agent making the request
            url: Target URL
            method: HTTP method (GET, POST, etc.)
            data: Request payload
            headers: Request headers
            timeout: Request timeout in seconds

        Returns:
            Response object (or raises exception)

        Raises:
            PaymentRequiredException: If CFO denies payment
            requests.RequestException: For other HTTP errors
        """
        headers = headers or {}

        logger.info(f"🌐 [ATXP] {agent_id} requesting: {method} {url}")

        try:
            # 1. Try Request
            response = requests.request(
                method=method,
                url=url,
                json=data,
                headers=headers,
                timeout=timeout,
            )

            # 2. Check for 402 Payment Required
            if response.status_code == 402:
                logger.info(f"🛑 [ATXP] 402 Payment Required from {url}")

                # Parse payment invoice from response
                invoice = self._parse_payment_invoice(response)

                logger.info(
                    f"   💰 Invoice: ${invoice.get('cost')} to {invoice.get('address')}"
                )

                # 3. Ask CFO for approval
                decision = self.cfo.request_funding(
                    agent_id=agent_id,
                    expense_details={
                        "item": f"API Call to {url}",
                        "cost_usd": invoice.get("cost", 0),
                        "address": invoice.get("address"),
                        "reason": f"Required for {method} {url}",
                    },
                )

                if not decision.get("approved"):
                    logger.error(f"   ❌ CFO Denied Payment: {decision.get('reason')}")
                    raise PaymentRequiredException(
                        f"CFO denied payment: {decision.get('reason')}"
                    )

                # 4. Retry with Payment Proof
                logger.info(f"   ✅ Payment approved, retrying with proof...")

                payment_headers = {
                    **headers,
                    "X-Payment-Hash": decision.get("tx_hash"),
                    "X-Payment-Amount": str(invoice.get("cost")),
                }

                response = requests.request(
                    method=method,
                    url=url,
                    json=data,
                    headers=payment_headers,
                    timeout=timeout,
                )

                if response.status_code == 200:
                    logger.info(f"   ✅ Request succeeded after payment")
                else:
                    logger.warning(
                        f"   ⚠️ Request still failed after payment: {response.status_code}"
                    )

            return response

        except requests.RequestException as e:
            logger.error(f"❌ [ATXP] Request failed: {e}")
            raise

    def _parse_payment_invoice(self, response: requests.Response) -> Dict[str, Any]:
        """
        Parse payment invoice from 402 response.

        Expected formats:
        - JSON body: {"cost": 0.05, "address": "0x...", "currency": "USDC"}
        - Headers: X-Payment-Required: 0.05, X-Payment-Address: 0x...
        """
        # Try JSON body first
        try:
            invoice = response.json()
            return {
                "cost": float(invoice.get("cost", 0)),
                "address": invoice.get("address", ""),
                "currency": invoice.get("currency", "USDC"),
            }
        except Exception:
            pass

        # Fallback to headers
        cost = response.headers.get("X-Payment-Required", "0")
        address = response.headers.get("X-Payment-Address", "")

        try:
            cost_float = float(cost)
        except ValueError:
            cost_float = 0.0

        return {
            "cost": cost_float,
            "address": address,
            "currency": response.headers.get("X-Payment-Currency", "USDC"),
        }


class PaymentRequiredException(Exception):
    """Raised when payment is required but denied."""
    pass


# Convenience functions for common patterns
def get_with_payment(agent_id: str, url: str, cfo, **kwargs) -> requests.Response:
    """Convenience wrapper for GET requests with ATXP."""
    middleware = ATXPMiddleware(cfo)
    return middleware.request(agent_id, url, method="GET", **kwargs)


def post_with_payment(
    agent_id: str, url: str, cfo, data: Optional[Dict] = None, **kwargs
) -> requests.Response:
    """Convenience wrapper for POST requests with ATXP."""
    middleware = ATXPMiddleware(cfo)
    return middleware.request(agent_id, url, method="POST", data=data, **kwargs)
