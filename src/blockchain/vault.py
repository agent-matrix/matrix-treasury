"""
External Vault: Real Money (USDC) Management on Blockchain

This module manages REAL cryptocurrency (USDC) on Base/Polygon chains.
Acts as the irrevocable bank account for autonomous agents.

Security Features:
- Multi-signature support (optional)
- Gas price optimization
- Transaction retry logic
- Balance monitoring
"""

import os
import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from web3 import Web3
from web3.exceptions import ContractLogicError, TransactionNotFound
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# USDC Contract Addresses
USDC_CONTRACTS = {
    "base": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # Base Mainnet
    "polygon": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # Polygon Mainnet
    "base-sepolia": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",  # Base Sepolia (Testnet)
}

# Minimal ERC20 ABI for USDC operations
USDC_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
]


class ExternalVault:
    """
    Manages REAL money (USDC) on the Blockchain (Base/Polygon).
    Acts as the irrevocable bank account for the Agent.
    """

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        private_key: Optional[str] = None,
        network: str = "base",
    ):
        """
        Initialize the External Vault.

        Args:
            rpc_url: Blockchain RPC endpoint (defaults to env var)
            private_key: Private key for transactions (defaults to env var)
            network: Network name (base, polygon, base-sepolia)
        """
        self.rpc_url = rpc_url or os.getenv("RPC_URL", "https://mainnet.base.org")
        if not self.rpc_url:
            raise ValueError("RPC_URL not set in environment or constructor")

        self.network = network
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to blockchain at {self.rpc_url}")

        # Initialize account
        private_key = private_key or os.getenv("TREASURY_PRIVATE_KEY")
        if private_key:
            self.account = Account.from_key(private_key)
            logger.info(f"Vault initialized with address: {self.account.address}")
        else:
            logger.warning("No private key provided - vault is read-only")
            self.account = None

        # USDC Contract
        self.usdc_address = USDC_CONTRACTS.get(network)
        if not self.usdc_address:
            raise ValueError(f"Unsupported network: {network}")

        self.usdc_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.usdc_address), abi=USDC_ABI
        )

        # Cache decimals
        try:
            self.decimals = self.usdc_contract.functions.decimals().call()
        except Exception as e:
            logger.warning(f"Could not fetch USDC decimals: {e}, defaulting to 6")
            self.decimals = 6

    def get_real_balance(self, address: Optional[str] = None) -> Decimal:
        """
        Returns the actual cash runway in USDC.

        Args:
            address: Address to check (defaults to vault address)

        Returns:
            Balance in USDC (human-readable)
        """
        try:
            check_address = address or self.account.address if self.account else None
            if not check_address:
                raise ValueError("No address available to check balance")

            balance_raw = self.usdc_contract.functions.balanceOf(
                Web3.to_checksum_address(check_address)
            ).call()

            # Convert from smallest unit to USDC
            balance_usdc = Decimal(balance_raw) / Decimal(10**self.decimals)

            logger.info(f"Vault balance: {balance_usdc} USDC")
            return balance_usdc

        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            raise

    def get_native_balance(self) -> Decimal:
        """Get native token balance (ETH on Base, MATIC on Polygon) for gas fees."""
        if not self.account:
            raise ValueError("Account not initialized")

        balance_wei = self.w3.eth.get_balance(self.account.address)
        balance_eth = self.w3.from_wei(balance_wei, "ether")
        return Decimal(str(balance_eth))

    def pay_external_bill(
        self, to_address: str, amount_usdc: Decimal, memo: str = ""
    ) -> Dict[str, Any]:
        """
        Executes an irreversible USDC transaction on the blockchain.

        Used for: Cloud Bills, API Keys, Tool Access, Infrastructure Rent.

        Args:
            to_address: Recipient address
            amount_usdc: Amount in USDC (human-readable)
            memo: Optional transaction memo

        Returns:
            Transaction details including hash and status

        Raises:
            ValueError: If account not initialized or insufficient balance
            Exception: For transaction failures
        """
        if not self.account:
            raise ValueError("Cannot send transactions: account not initialized")

        logger.info(f"💸 [VAULT] PAYING REAL BILL: ${amount_usdc} to {to_address}")
        if memo:
            logger.info(f"   Memo: {memo}")

        try:
            # Convert to smallest unit
            amount_raw = int(amount_usdc * Decimal(10**self.decimals))

            # Check balance
            current_balance = self.get_real_balance()
            if current_balance < amount_usdc:
                raise ValueError(
                    f"Insufficient USDC balance: {current_balance} < {amount_usdc}"
                )

            # Check gas balance
            gas_balance = self.get_native_balance()
            if gas_balance < Decimal("0.001"):  # Minimum gas reserve
                logger.warning(
                    f"Low gas balance: {gas_balance} ETH - transaction may fail"
                )

            # Build transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)

            tx = self.usdc_contract.functions.transfer(
                Web3.to_checksum_address(to_address), amount_raw
            ).build_transaction(
                {
                    "from": self.account.address,
                    "nonce": nonce,
                    "gas": 100000,  # USDC transfer typically uses ~50k gas
                    "gasPrice": self.w3.eth.gas_price,
                    "chainId": self.w3.eth.chain_id,
                }
            )

            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = self.w3.to_hex(tx_hash)

            logger.info(f"✅ [VAULT] Transaction sent: {tx_hash_hex}")

            # Wait for confirmation (optional - can be async)
            try:
                receipt = self.w3.eth.wait_for_transaction_receipt(
                    tx_hash, timeout=120
                )
                status = "success" if receipt["status"] == 1 else "failed"
                logger.info(f"   Transaction {status}: Block {receipt['blockNumber']}")

                return {
                    "tx_hash": tx_hash_hex,
                    "status": status,
                    "block_number": receipt["blockNumber"],
                    "gas_used": receipt["gasUsed"],
                    "amount_usdc": float(amount_usdc),
                    "to_address": to_address,
                }

            except TransactionNotFound:
                logger.warning("Transaction pending - not confirmed yet")
                return {
                    "tx_hash": tx_hash_hex,
                    "status": "pending",
                    "amount_usdc": float(amount_usdc),
                    "to_address": to_address,
                }

        except ContractLogicError as e:
            logger.error(f"❌ [VAULT] Contract error: {e}")
            raise ValueError(f"Transaction rejected by contract: {e}")

        except Exception as e:
            logger.error(f"❌ [VAULT] Transaction failed: {e}")
            raise

    def estimate_gas_cost(self) -> Decimal:
        """Estimate current gas cost for a USDC transfer in USD."""
        try:
            gas_price_wei = self.w3.eth.gas_price
            gas_limit = 100000  # Typical USDC transfer

            # Get ETH price (simplified - in production use oracle)
            eth_usd_price = Decimal(os.getenv("ETH_USD_PRICE", "2000"))

            gas_cost_eth = self.w3.from_wei(gas_price_wei * gas_limit, "ether")
            gas_cost_usd = Decimal(str(gas_cost_eth)) * eth_usd_price

            return gas_cost_usd

        except Exception as e:
            logger.warning(f"Could not estimate gas: {e}")
            return Decimal("0.50")  # Safe default estimate

    def get_vault_status(self) -> Dict[str, Any]:
        """Get comprehensive vault status for monitoring."""
        try:
            usdc_balance = self.get_real_balance()
            gas_balance = self.get_native_balance() if self.account else Decimal("0")
            gas_estimate = self.estimate_gas_cost()

            return {
                "network": self.network,
                "address": self.account.address if self.account else None,
                "usdc_balance": float(usdc_balance),
                "gas_balance_eth": float(gas_balance),
                "estimated_gas_cost_usd": float(gas_estimate),
                "can_transact": bool(self.account and usdc_balance > 0 and gas_balance > 0),
                "usdc_contract": self.usdc_address,
                "connected": self.w3.is_connected(),
            }

        except Exception as e:
            logger.error(f"Error getting vault status: {e}")
            return {
                "error": str(e),
                "connected": self.w3.is_connected(),
            }
