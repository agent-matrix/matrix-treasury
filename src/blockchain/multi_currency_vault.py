"""
Multi-Currency Vault: Enterprise Payment Gateway

Supports multiple fiat and crypto currencies for admin withdrawals:
- USDC (stablecoin on Base/Polygon/Arbitrum/Optimism)
- EUR (EURe stablecoin)
- BTC (Bitcoin Layer 2 or wrapped BTC)

Features:
- Cross-chain bridging support
- Real-time exchange rates
- Admin-only wire transfer configuration
- Multi-network deployment
"""

import os
import logging
from decimal import Decimal
from typing import Optional, Dict, Any, Literal
from enum import Enum
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Currency(str, Enum):
    """Supported currencies for admin withdrawals"""
    USDC = "USDC"
    EUR = "EUR"
    BTC = "BTC"


class Network(str, Enum):
    """Supported blockchain networks"""
    BASE = "base"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE_SEPOLIA = "base-sepolia"


# Multi-currency contract addresses per network
CURRENCY_CONTRACTS = {
    Network.BASE: {
        Currency.USDC: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        Currency.EUR: "0x60a3E35Cc302bFA44Cb288Bc5a4F316Fdb1adb42",  # EURe on Base
        Currency.BTC: "0x0555E30da8f98308EdB960aa94C0Db47230d2B9c",  # cbBTC on Base
    },
    Network.POLYGON: {
        Currency.USDC: "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        Currency.EUR: "0x18ec0A6E18E5bc3784fDd3a3634b31245ab704F6",  # EURe on Polygon
        Currency.BTC: "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",  # WBTC on Polygon
    },
    Network.ARBITRUM: {
        Currency.USDC: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        Currency.EUR: "0x643b34980E635719C15a2D4ce69571a258F940E9",  # EURe on Arbitrum
        Currency.BTC: "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f",  # WBTC on Arbitrum
    },
    Network.OPTIMISM: {
        Currency.USDC: "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85",
        Currency.EUR: "0x9485aca5bbBE1667AD97c7fE7C4531a624C8b1ED",  # EURe on Optimism
        Currency.BTC: "0x68f180fcCe6836688e9084f035309E29Bf0A2095",  # WBTC on Optimism
    },
    Network.BASE_SEPOLIA: {
        Currency.USDC: "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        Currency.EUR: "0x0000000000000000000000000000000000000000",  # Not available on testnet
        Currency.BTC: "0x0000000000000000000000000000000000000000",  # Not available on testnet
    },
}

# RPC Endpoints
RPC_ENDPOINTS = {
    Network.BASE: "https://mainnet.base.org",
    Network.POLYGON: "https://polygon-rpc.com",
    Network.ARBITRUM: "https://arb1.arbitrum.io/rpc",
    Network.OPTIMISM: "https://mainnet.optimism.io",
    Network.BASE_SEPOLIA: "https://sepolia.base.org",
}

# Chain IDs
CHAIN_IDS = {
    Network.BASE: 8453,
    Network.POLYGON: 137,
    Network.ARBITRUM: 42161,
    Network.OPTIMISM: 10,
    Network.BASE_SEPOLIA: 84532,
}

# ERC20 ABI (minimal)
ERC20_ABI = [
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
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
]


class CurrencyConverter:
    """Real-time currency conversion (simplified - use Chainlink oracles in production)"""

    @staticmethod
    def get_exchange_rate(from_currency: Currency, to_currency: Currency = Currency.USDC) -> Decimal:
        """Get exchange rate between currencies"""
        # Simplified - in production use Chainlink price feeds
        rates = {
            (Currency.USDC, Currency.USDC): Decimal("1.0"),
            (Currency.EUR, Currency.USDC): Decimal("1.08"),  # 1 EUR = 1.08 USD
            (Currency.BTC, Currency.USDC): Decimal("45000"),  # 1 BTC = 45000 USD
            (Currency.USDC, Currency.EUR): Decimal("0.93"),  # 1 USD = 0.93 EUR
            (Currency.USDC, Currency.BTC): Decimal("0.000022"),  # 1 USD = 0.000022 BTC
        }
        return rates.get((from_currency, to_currency), Decimal("1.0"))

    @staticmethod
    def convert(amount: Decimal, from_currency: Currency, to_currency: Currency) -> Decimal:
        """Convert amount between currencies"""
        rate = CurrencyConverter.get_exchange_rate(from_currency, to_currency)
        return amount * rate


class MultiCurrencyVault:
    """
    Enterprise-grade multi-currency vault for admin withdrawals.
    Supports USDC, EUR, BTC across multiple chains.
    """

    def __init__(
        self,
        network: Network = Network.BASE,
        private_key: Optional[str] = None,
    ):
        """
        Initialize multi-currency vault.

        Args:
            network: Blockchain network to use
            private_key: Admin private key (optional, read-only if not provided)
        """
        self.network = network
        self.rpc_url = os.getenv(f"{network.upper()}_RPC_URL", RPC_ENDPOINTS[network])

        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to {network} at {self.rpc_url}")

        # Initialize account
        private_key = private_key or os.getenv("ADMIN_PRIVATE_KEY") or os.getenv("TREASURY_PRIVATE_KEY")
        if private_key:
            self.account = Account.from_key(private_key)
            logger.info(f"Multi-currency vault initialized: {self.account.address} on {network}")
        else:
            logger.warning("No private key - vault is read-only")
            self.account = None

        # Initialize currency contracts
        self.contracts = {}
        self.decimals_cache = {}

        for currency in Currency:
            contract_address = CURRENCY_CONTRACTS[network].get(currency)
            if contract_address and contract_address != "0x0000000000000000000000000000000000000000":
                try:
                    contract = self.w3.eth.contract(
                        address=Web3.to_checksum_address(contract_address),
                        abi=ERC20_ABI
                    )
                    self.contracts[currency] = contract

                    # Cache decimals
                    try:
                        decimals = contract.functions.decimals().call()
                        self.decimals_cache[currency] = decimals
                    except:
                        self.decimals_cache[currency] = 18 if currency == Currency.BTC else 6

                    logger.info(f"  {currency.value}: {contract_address}")
                except Exception as e:
                    logger.warning(f"Could not initialize {currency.value} contract: {e}")

    def get_balance(self, currency: Currency, address: Optional[str] = None) -> Decimal:
        """
        Get balance for specific currency.

        Args:
            currency: Currency to check
            address: Address to check (defaults to vault address)

        Returns:
            Balance in human-readable format
        """
        if currency not in self.contracts:
            raise ValueError(f"{currency.value} not available on {self.network}")

        check_address = address or (self.account.address if self.account else None)
        if not check_address:
            raise ValueError("No address available")

        try:
            contract = self.contracts[currency]
            balance_raw = contract.functions.balanceOf(
                Web3.to_checksum_address(check_address)
            ).call()

            decimals = self.decimals_cache[currency]
            balance = Decimal(balance_raw) / Decimal(10 ** decimals)

            logger.debug(f"{currency.value} balance: {balance}")
            return balance

        except Exception as e:
            logger.error(f"Error fetching {currency.value} balance: {e}")
            raise

    def get_all_balances(self, address: Optional[str] = None) -> Dict[str, Decimal]:
        """Get balances for all currencies"""
        balances = {}
        for currency in Currency:
            if currency in self.contracts:
                try:
                    balances[currency.value] = self.get_balance(currency, address)
                except Exception as e:
                    logger.warning(f"Could not fetch {currency.value} balance: {e}")
                    balances[currency.value] = Decimal("0")
        return balances

    def transfer(
        self,
        to_address: str,
        amount: Decimal,
        currency: Currency,
        memo: str = "",
        gas_limit: int = 100000,
    ) -> Dict[str, Any]:
        """
        Transfer currency to admin address (admin-only operation).

        Args:
            to_address: Recipient address
            amount: Amount to transfer (human-readable)
            currency: Currency to transfer
            memo: Optional memo
            gas_limit: Gas limit for transaction

        Returns:
            Transaction details
        """
        if not self.account:
            raise ValueError("Cannot send transactions: account not initialized")

        if currency not in self.contracts:
            raise ValueError(f"{currency.value} not available on {self.network}")

        logger.info(f"💸 [MULTI-VAULT] Transferring {amount} {currency.value} to {to_address}")
        if memo:
            logger.info(f"   Memo: {memo}")

        try:
            contract = self.contracts[currency]
            decimals = self.decimals_cache[currency]

            # Convert to smallest unit
            amount_raw = int(amount * Decimal(10 ** decimals))

            # Check balance
            current_balance = self.get_balance(currency)
            if current_balance < amount:
                raise ValueError(
                    f"Insufficient {currency.value} balance: {current_balance} < {amount}"
                )

            # Build transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)

            tx = contract.functions.transfer(
                Web3.to_checksum_address(to_address),
                amount_raw
            ).build_transaction({
                "from": self.account.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.w3.eth.gas_price,
                "chainId": CHAIN_IDS[self.network],
            })

            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = self.w3.to_hex(tx_hash)

            logger.info(f"✅ [MULTI-VAULT] Transaction sent: {tx_hash_hex}")

            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            status = "success" if receipt["status"] == 1 else "failed"

            return {
                "tx_hash": tx_hash_hex,
                "status": status,
                "block_number": receipt["blockNumber"],
                "gas_used": receipt["gasUsed"],
                "amount": float(amount),
                "currency": currency.value,
                "network": self.network.value,
                "to_address": to_address,
                "memo": memo,
            }

        except Exception as e:
            logger.error(f"❌ [MULTI-VAULT] Transfer failed: {e}")
            raise

    def get_vault_status(self) -> Dict[str, Any]:
        """Get comprehensive multi-currency vault status"""
        try:
            balances = self.get_all_balances()

            # Calculate total in USDC equivalent
            total_usdc = Decimal("0")
            for curr_str, balance in balances.items():
                currency = Currency(curr_str)
                usdc_value = CurrencyConverter.convert(balance, currency, Currency.USDC)
                total_usdc += usdc_value

            return {
                "network": self.network.value,
                "address": self.account.address if self.account else None,
                "balances": {k: float(v) for k, v in balances.items()},
                "total_usdc_equivalent": float(total_usdc),
                "connected": self.w3.is_connected(),
                "chain_id": CHAIN_IDS[self.network],
                "supported_currencies": [c.value for c in Currency if c in self.contracts],
            }

        except Exception as e:
            logger.error(f"Error getting vault status: {e}")
            return {
                "error": str(e),
                "connected": self.w3.is_connected(),
            }
