"""
Custom exceptions for Matrix Treasury
"""

class MatrixTreasuryError(Exception):
    """Base exception for all treasury errors"""
    pass

class InsufficientReserves(MatrixTreasuryError):
    """Raised when system cannot cover costs from reserves"""
    pass

class InsufficientFunds(MatrixTreasuryError):
    """Raised when agent/user has insufficient balance"""
    pass

class ConstitutionalViolation(MatrixTreasuryError):
    """Raised when economic laws are violated"""
    pass

class AgentNotFound(MatrixTreasuryError):
    """Raised when agent ID doesn't exist"""
    pass

class InvalidTransaction(MatrixTreasuryError):
    """Raised when transaction is invalid"""
    pass

class MeteringError(MatrixTreasuryError):
    """Raised when metering data is invalid"""
    pass

class BankruptcyError(MatrixTreasuryError):
    """Raised when agent enters bankruptcy"""
    pass

class AuthorizationError(MatrixTreasuryError):
    """Raised when authorization fails"""
    pass
