"""
Simple Bearer token guard for Matrix Treasury API.
Aligned with Agent-Matrix ecosystem auth standards.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.config import config

_bearer = HTTPBearer(auto_error=False)


def require_api_token(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    """
    Simple Bearer token gate for mutation/admin endpoints.
    - In development: if no token is configured, allow (non-destructive).
    - In staging/production: token must be configured and must match.
    """
    expected = config.security.api_token
    env = config.environment.value

    if env in ("production", "staging"):
        if not expected:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Treasury is misconfigured: missing MATRIX_TREASURY_TOKEN (or API_TOKEN/ADMIN_TOKEN)",
            )

    # If no token configured (dev), allow through.
    if not expected:
        return

    provided = (creds.credentials if creds else "").strip()
    if not provided or provided != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: valid operator token required",
        )
