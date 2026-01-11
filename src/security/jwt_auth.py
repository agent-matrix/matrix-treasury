"""JWT-based admin authentication for Mission Control.

This module provides:
- Password hashing/verification with bcrypt
- JWT access token creation
- FastAPI dependency to protect admin-only endpoints
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import jwt
from sqlalchemy.orm import Session

from src.db.connection import get_db
from src.db.models import AdminUser

# JWT Configuration
JWT_SECRET = "matrix-treasury-secret-change-in-production"  # Override with env var
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer security
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt

    Note: Bcrypt has a 72-byte limit, so we truncate to 72 characters
    which is safe for ASCII and conservative for multi-byte UTF-8.
    """
    # Truncate to 72 characters to stay well within bcrypt's 72-byte limit
    truncated_password = password[:72]
    return pwd_context.hash(truncated_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plain text password against a hash

    Note: Bcrypt has a 72-byte limit, so we truncate to match hash_password behavior.
    """
    # Truncate to 72 characters to match hash_password behavior
    truncated_password = plain_password[:72]
    return pwd_context.verify(truncated_password, password_hash)


def create_access_token(*, sub: str, expires_hours: Optional[int] = None) -> str:
    """Create a JWT access token

    Args:
        sub: Subject (username)
        expires_hours: Token expiration in hours (default: JWT_EXPIRATION_HOURS)

    Returns:
        Encoded JWT token string
    """
    expire = datetime.now(timezone.utc) + timedelta(
        hours=expires_hours or JWT_EXPIRATION_HOURS
    )
    payload = {
        "sub": sub,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _get_user_from_token(db: Session, token: str) -> AdminUser:
    """Internal helper to decode token and fetch user"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject"
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

    user = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    return user


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> AdminUser:
    """FastAPI dependency to get current authenticated admin

    Usage:
        @router.get("/protected")
        async def protected_route(admin: AdminUser = Depends(get_current_admin)):
            return {"username": admin.username}
    """
    return _get_user_from_token(db, credentials.credentials)
