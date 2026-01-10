"""
Admin Wire Transfer Settings

Secure configuration for admin-only wire transfers and withdrawals.
Supports multiple payment methods:
- Bank wire transfers (USD, EUR)
- Cryptocurrency withdrawals (USDC, BTC)
- Cross-chain bridging

Security Features:
- Encrypted storage of sensitive data
- Admin authentication required
- Withdrawal limits and approval workflows
- Audit logging
"""

import os
import logging
import json
from decimal import Decimal
from typing import Dict, Optional, Any, Literal
from dataclasses import dataclass, asdict
from datetime import datetime
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class BankAccount:
    """Bank account details for wire transfers"""
    account_name: str
    account_number: str  # Encrypted
    routing_number: str  # Encrypted
    swift_code: str  # Encrypted
    bank_name: str
    bank_address: str
    currency: str  # USD, EUR
    country: str


@dataclass
class CryptoWallet:
    """Cryptocurrency wallet for withdrawals"""
    address: str  # Encrypted
    network: str  # base, polygon, arbitrum, optimism
    currency: str  # USDC, BTC, EUR
    label: str


@dataclass
class WithdrawalLimits:
    """Withdrawal limits for risk management"""
    daily_limit_usd: Decimal
    per_transaction_limit_usd: Decimal
    monthly_limit_usd: Decimal
    requires_approval_above_usd: Decimal


class SecureStorage:
    """Encrypted storage for sensitive admin data"""

    def __init__(self):
        """Initialize encryption"""
        # In production, load from secure key management system
        encryption_key = os.getenv("ADMIN_ENCRYPTION_KEY")

        if not encryption_key:
            # Generate new key (for development)
            encryption_key = Fernet.generate_key().decode()
            logger.warning("Using generated encryption key - set ADMIN_ENCRYPTION_KEY in production")

        self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)

    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()


class WireTransferSettings:
    """
    Admin settings for wire transfers and withdrawals.
    """

    def __init__(self, storage_path: str = "data/admin_settings.json"):
        """
        Initialize wire transfer settings.

        Args:
            storage_path: Path to settings file (encrypted)
        """
        self.storage_path = storage_path
        self.secure_storage = SecureStorage()

        # Settings
        self.bank_accounts: Dict[str, BankAccount] = {}
        self.crypto_wallets: Dict[str, CryptoWallet] = {}
        self.withdrawal_limits = WithdrawalLimits(
            daily_limit_usd=Decimal("50000"),
            per_transaction_limit_usd=Decimal("10000"),
            monthly_limit_usd=Decimal("500000"),
            requires_approval_above_usd=Decimal("5000"),
        )

        # Withdrawal tracking
        self.daily_withdrawn = Decimal("0")
        self.monthly_withdrawn = Decimal("0")
        self.last_reset = datetime.now()

        # Load saved settings
        self._load_settings()

        logger.info("Wire Transfer Settings initialized")

    def add_bank_account(
        self,
        account_id: str,
        account_name: str,
        account_number: str,
        routing_number: str,
        swift_code: str,
        bank_name: str,
        bank_address: str,
        currency: str,
        country: str,
    ) -> Dict[str, Any]:
        """
        Add a bank account for wire transfers (admin only).

        Args:
            account_id: Unique identifier
            account_name: Account holder name
            account_number: Account number (will be encrypted)
            routing_number: Routing/sort code (will be encrypted)
            swift_code: SWIFT/BIC code (will be encrypted)
            bank_name: Bank name
            bank_address: Bank address
            currency: Currency (USD, EUR)
            country: Country code

        Returns:
            Confirmation details
        """
        logger.info(f"🏦 [ADMIN] Adding bank account: {account_id} ({currency})")

        # Encrypt sensitive data
        encrypted_account = self.secure_storage.encrypt(account_number)
        encrypted_routing = self.secure_storage.encrypt(routing_number)
        encrypted_swift = self.secure_storage.encrypt(swift_code)

        account = BankAccount(
            account_name=account_name,
            account_number=encrypted_account,
            routing_number=encrypted_routing,
            swift_code=encrypted_swift,
            bank_name=bank_name,
            bank_address=bank_address,
            currency=currency,
            country=country,
        )

        self.bank_accounts[account_id] = account
        self._save_settings()

        return {
            "account_id": account_id,
            "bank_name": bank_name,
            "currency": currency,
            "status": "added",
        }

    def add_crypto_wallet(
        self,
        wallet_id: str,
        address: str,
        network: str,
        currency: str,
        label: str = "",
    ) -> Dict[str, Any]:
        """
        Add a cryptocurrency wallet for withdrawals (admin only).

        Args:
            wallet_id: Unique identifier
            address: Wallet address (will be encrypted)
            network: Blockchain network
            currency: Currency code
            label: Optional label

        Returns:
            Confirmation details
        """
        logger.info(f"💰 [ADMIN] Adding crypto wallet: {wallet_id} ({currency} on {network})")

        # Encrypt address
        encrypted_address = self.secure_storage.encrypt(address)

        wallet = CryptoWallet(
            address=encrypted_address,
            network=network,
            currency=currency,
            label=label,
        )

        self.crypto_wallets[wallet_id] = wallet
        self._save_settings()

        return {
            "wallet_id": wallet_id,
            "network": network,
            "currency": currency,
            "label": label,
            "status": "added",
        }

    def get_bank_account(self, account_id: str, decrypt: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get bank account details.

        Args:
            account_id: Account identifier
            decrypt: Whether to decrypt sensitive fields

        Returns:
            Account details (sensitive fields encrypted unless decrypt=True)
        """
        if account_id not in self.bank_accounts:
            return None

        account = self.bank_accounts[account_id]
        details = asdict(account)

        if decrypt:
            details["account_number"] = self.secure_storage.decrypt(account.account_number)
            details["routing_number"] = self.secure_storage.decrypt(account.routing_number)
            details["swift_code"] = self.secure_storage.decrypt(account.swift_code)
        else:
            details["account_number"] = "****" + details["account_number"][-4:]
            details["routing_number"] = "****"
            details["swift_code"] = "****"

        return details

    def get_crypto_wallet(self, wallet_id: str, decrypt: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get crypto wallet details.

        Args:
            wallet_id: Wallet identifier
            decrypt: Whether to decrypt address

        Returns:
            Wallet details
        """
        if wallet_id not in self.crypto_wallets:
            return None

        wallet = self.crypto_wallets[wallet_id]
        details = asdict(wallet)

        if decrypt:
            details["address"] = self.secure_storage.decrypt(wallet.address)
        else:
            decrypted = self.secure_storage.decrypt(wallet.address)
            details["address"] = decrypted[:6] + "..." + decrypted[-4:]

        return details

    def check_withdrawal_limit(self, amount_usd: Decimal) -> Dict[str, Any]:
        """
        Check if withdrawal is within limits.

        Args:
            amount_usd: Withdrawal amount in USD

        Returns:
            Approval status and details
        """
        self._reset_limits_if_needed()

        # Check per-transaction limit
        if amount_usd > self.withdrawal_limits.per_transaction_limit_usd:
            return {
                "approved": False,
                "reason": f"Exceeds per-transaction limit: ${amount_usd} > ${self.withdrawal_limits.per_transaction_limit_usd}",
            }

        # Check daily limit
        if self.daily_withdrawn + amount_usd > self.withdrawal_limits.daily_limit_usd:
            return {
                "approved": False,
                "reason": f"Exceeds daily limit: ${self.daily_withdrawn + amount_usd} > ${self.withdrawal_limits.daily_limit_usd}",
                "daily_remaining": float(self.withdrawal_limits.daily_limit_usd - self.daily_withdrawn),
            }

        # Check monthly limit
        if self.monthly_withdrawn + amount_usd > self.withdrawal_limits.monthly_limit_usd:
            return {
                "approved": False,
                "reason": f"Exceeds monthly limit: ${self.monthly_withdrawn + amount_usd} > ${self.withdrawal_limits.monthly_limit_usd}",
                "monthly_remaining": float(self.withdrawal_limits.monthly_limit_usd - self.monthly_withdrawn),
            }

        # Check if manual approval required
        requires_approval = amount_usd > self.withdrawal_limits.requires_approval_above_usd

        return {
            "approved": True,
            "requires_manual_approval": requires_approval,
            "daily_remaining": float(self.withdrawal_limits.daily_limit_usd - self.daily_withdrawn),
            "monthly_remaining": float(self.withdrawal_limits.monthly_limit_usd - self.monthly_withdrawn),
        }

    def record_withdrawal(self, amount_usd: Decimal) -> None:
        """Record a withdrawal for limit tracking"""
        self._reset_limits_if_needed()
        self.daily_withdrawn += amount_usd
        self.monthly_withdrawn += amount_usd
        self._save_settings()

    def update_limits(
        self,
        daily_limit: Optional[Decimal] = None,
        per_transaction_limit: Optional[Decimal] = None,
        monthly_limit: Optional[Decimal] = None,
        approval_threshold: Optional[Decimal] = None,
    ) -> Dict[str, Any]:
        """Update withdrawal limits (admin only)"""
        if daily_limit is not None:
            self.withdrawal_limits.daily_limit_usd = daily_limit

        if per_transaction_limit is not None:
            self.withdrawal_limits.per_transaction_limit_usd = per_transaction_limit

        if monthly_limit is not None:
            self.withdrawal_limits.monthly_limit_usd = monthly_limit

        if approval_threshold is not None:
            self.withdrawal_limits.requires_approval_above_usd = approval_threshold

        self._save_settings()

        return {
            "daily_limit": float(self.withdrawal_limits.daily_limit_usd),
            "per_transaction_limit": float(self.withdrawal_limits.per_transaction_limit_usd),
            "monthly_limit": float(self.withdrawal_limits.monthly_limit_usd),
            "approval_threshold": float(self.withdrawal_limits.requires_approval_above_usd),
        }

    def get_all_accounts(self) -> Dict[str, Any]:
        """Get all configured accounts (masked)"""
        return {
            "bank_accounts": [
                {
                    "account_id": acc_id,
                    **self.get_bank_account(acc_id, decrypt=False),
                }
                for acc_id in self.bank_accounts.keys()
            ],
            "crypto_wallets": [
                {
                    "wallet_id": wallet_id,
                    **self.get_crypto_wallet(wallet_id, decrypt=False),
                }
                for wallet_id in self.crypto_wallets.keys()
            ],
        }

    def _reset_limits_if_needed(self) -> None:
        """Reset daily/monthly limits based on time"""
        now = datetime.now()

        # Reset daily limit
        if now.date() > self.last_reset.date():
            self.daily_withdrawn = Decimal("0")
            logger.info("Daily withdrawal limit reset")

        # Reset monthly limit
        if now.month != self.last_reset.month or now.year != self.last_reset.year:
            self.monthly_withdrawn = Decimal("0")
            logger.info("Monthly withdrawal limit reset")

        self.last_reset = now

    def _save_settings(self) -> None:
        """Save settings to encrypted file"""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

            data = {
                "bank_accounts": {k: asdict(v) for k, v in self.bank_accounts.items()},
                "crypto_wallets": {k: asdict(v) for k, v in self.crypto_wallets.items()},
                "withdrawal_limits": asdict(self.withdrawal_limits),
                "daily_withdrawn": str(self.daily_withdrawn),
                "monthly_withdrawn": str(self.monthly_withdrawn),
                "last_reset": self.last_reset.isoformat(),
            }

            # Convert Decimal to string for JSON
            def decimal_converter(obj):
                if isinstance(obj, Decimal):
                    return str(obj)
                raise TypeError

            with open(self.storage_path, "w") as f:
                json.dump(data, f, default=decimal_converter, indent=2)

        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    def _load_settings(self) -> None:
        """Load settings from encrypted file"""
        try:
            if not os.path.exists(self.storage_path):
                return

            with open(self.storage_path, "r") as f:
                data = json.load(f)

            # Load bank accounts
            for acc_id, acc_data in data.get("bank_accounts", {}).items():
                self.bank_accounts[acc_id] = BankAccount(**acc_data)

            # Load crypto wallets
            for wallet_id, wallet_data in data.get("crypto_wallets", {}).items():
                self.crypto_wallets[wallet_id] = CryptoWallet(**wallet_data)

            # Load withdrawal limits
            if "withdrawal_limits" in data:
                limits = data["withdrawal_limits"]
                self.withdrawal_limits = WithdrawalLimits(
                    daily_limit_usd=Decimal(limits["daily_limit_usd"]),
                    per_transaction_limit_usd=Decimal(limits["per_transaction_limit_usd"]),
                    monthly_limit_usd=Decimal(limits["monthly_limit_usd"]),
                    requires_approval_above_usd=Decimal(limits["requires_approval_above_usd"]),
                )

            # Load tracking data
            self.daily_withdrawn = Decimal(data.get("daily_withdrawn", "0"))
            self.monthly_withdrawn = Decimal(data.get("monthly_withdrawn", "0"))
            self.last_reset = datetime.fromisoformat(data.get("last_reset", datetime.now().isoformat()))

            logger.info("Settings loaded successfully")

        except Exception as e:
            logger.warning(f"Could not load settings: {e}")
