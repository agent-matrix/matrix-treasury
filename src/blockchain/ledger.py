"""
Internal Ledger: Shadow Economy (MXU) Management

This module manages INTERNAL currency (MXU - Matrix Units).
Tracks agent efficiency, credit scores, and 'Shadow Accounting'.

The dual-layer architecture:
- MXU (Internal): Fast, free, used for agent prioritization and bidding
- USDC (External): Slow, secure, used for real payments

Think of MXU as "credit score + internal points" that determine
which agents get access to real money when needed.
"""

import logging
import sqlite3
from decimal import Decimal
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class InternalLedger:
    """
    Manages INTERNAL currency (MXU).
    Tracks agent efficiency and 'Shadow Accounting'.

    Features:
    - Fast in-memory operations
    - Agent credit tracking
    - Transaction history
    - Performance metrics
    """

    def __init__(self, db_path: str = "data/matrix_treasury.db"):
        """
        Initialize the Internal Ledger.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access
        self.create_tables()
        logger.info(f"Internal Ledger initialized: {db_path}")

    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        try:
            yield self.conn
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Transaction failed: {e}")
            raise

    def create_tables(self):
        """Create database schema for internal ledger."""
        with self.transaction():
            # Agent wallets
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS wallets (
                    agent_id TEXT PRIMARY KEY,
                    balance_mxu REAL NOT NULL DEFAULT 0,
                    credit_score REAL NOT NULL DEFAULT 0.5,
                    total_earned REAL NOT NULL DEFAULT 0,
                    total_spent REAL NOT NULL DEFAULT 0,
                    bankruptcy_count INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Transaction log
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS mxu_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_agent TEXT,
                    to_agent TEXT,
                    amount_mxu REAL NOT NULL,
                    transaction_type TEXT NOT NULL,
                    description TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (from_agent) REFERENCES wallets(agent_id),
                    FOREIGN KEY (to_agent) REFERENCES wallets(agent_id)
                )
            """)

            # Performance metrics
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_metrics (
                    agent_id TEXT PRIMARY KEY,
                    tasks_completed INTEGER DEFAULT 0,
                    tasks_failed INTEGER DEFAULT 0,
                    avg_quality_score REAL DEFAULT 0,
                    uptime_hours REAL DEFAULT 0,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (agent_id) REFERENCES wallets(agent_id)
                )
            """)

            # Create indexes
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_from ON mxu_transactions(from_agent)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_to ON mxu_transactions(to_agent)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_time ON mxu_transactions(timestamp)"
            )

    def create_wallet(self, agent_id: str, initial_balance: Decimal = Decimal("0")) -> bool:
        """
        Create a new wallet for an agent.

        Args:
            agent_id: Unique agent identifier
            initial_balance: Starting MXU balance

        Returns:
            True if wallet created, False if already exists
        """
        try:
            with self.transaction():
                self.conn.execute(
                    """
                    INSERT INTO wallets (agent_id, balance_mxu, credit_score)
                    VALUES (?, ?, 0.5)
                """,
                    (agent_id, float(initial_balance)),
                )

                # Initialize metrics
                self.conn.execute(
                    """
                    INSERT INTO agent_metrics (agent_id)
                    VALUES (?)
                """,
                    (agent_id,),
                )

            logger.info(f"Created wallet for {agent_id} with {initial_balance} MXU")
            return True

        except sqlite3.IntegrityError:
            logger.warning(f"Wallet already exists for {agent_id}")
            return False

    def credit_agent(self, agent_id: str, amount_mxu: Decimal, reason: str = "") -> bool:
        """
        Reward an agent with MXU.

        Args:
            agent_id: Agent to credit
            amount_mxu: Amount to add
            reason: Transaction description

        Returns:
            True if successful
        """
        try:
            with self.transaction():
                # Update or create wallet
                self.conn.execute(
                    """
                    INSERT INTO wallets (agent_id, balance_mxu, total_earned)
                    VALUES (?, ?, ?)
                    ON CONFLICT(agent_id) DO UPDATE SET
                        balance_mxu = balance_mxu + ?,
                        total_earned = total_earned + ?,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    (agent_id, float(amount_mxu), float(amount_mxu), float(amount_mxu), float(amount_mxu)),
                )

                # Log transaction
                self.conn.execute(
                    """
                    INSERT INTO mxu_transactions (to_agent, amount_mxu, transaction_type, description)
                    VALUES (?, ?, 'CREDIT', ?)
                """,
                    (agent_id, float(amount_mxu), reason),
                )

            logger.info(f"Credited {agent_id}: +{amount_mxu} MXU ({reason})")
            return True

        except Exception as e:
            logger.error(f"Failed to credit {agent_id}: {e}")
            return False

    def debit_agent(self, agent_id: str, amount_mxu: Decimal, reason: str = "") -> bool:
        """
        Deduct MXU from agent. Returns False if bankrupt.

        Args:
            agent_id: Agent to debit
            amount_mxu: Amount to deduct
            reason: Transaction description

        Returns:
            True if successful, False if insufficient balance
        """
        try:
            cursor = self.conn.execute(
                "SELECT balance_mxu FROM wallets WHERE agent_id = ?", (agent_id,)
            )
            row = cursor.fetchone()

            if not row:
                logger.warning(f"Wallet not found for {agent_id}")
                return False

            current_balance = Decimal(str(row["balance_mxu"]))

            if current_balance < amount_mxu:
                logger.warning(
                    f"Insufficient MXU for {agent_id}: {current_balance} < {amount_mxu}"
                )
                # Mark bankruptcy
                with self.transaction():
                    self.conn.execute(
                        """
                        UPDATE wallets
                        SET bankruptcy_count = bankruptcy_count + 1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE agent_id = ?
                    """,
                        (agent_id,),
                    )
                return False

            # Deduct balance
            with self.transaction():
                self.conn.execute(
                    """
                    UPDATE wallets
                    SET balance_mxu = balance_mxu - ?,
                        total_spent = total_spent + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE agent_id = ?
                """,
                    (float(amount_mxu), float(amount_mxu), agent_id),
                )

                # Log transaction
                self.conn.execute(
                    """
                    INSERT INTO mxu_transactions (from_agent, amount_mxu, transaction_type, description)
                    VALUES (?, ?, 'DEBIT', ?)
                """,
                    (agent_id, float(amount_mxu), reason),
                )

            logger.info(f"Debited {agent_id}: -{amount_mxu} MXU ({reason})")
            return True

        except Exception as e:
            logger.error(f"Failed to debit {agent_id}: {e}")
            return False

    def transfer(
        self, from_agent: str, to_agent: str, amount_mxu: Decimal, reason: str = ""
    ) -> bool:
        """
        Transfer MXU between agents.

        Args:
            from_agent: Source agent
            to_agent: Destination agent
            amount_mxu: Amount to transfer
            reason: Transaction description

        Returns:
            True if successful
        """
        try:
            # Check source balance
            if not self.debit_agent(from_agent, amount_mxu, f"Transfer to {to_agent}"):
                return False

            # Credit destination
            if not self.credit_agent(to_agent, amount_mxu, f"Transfer from {from_agent}"):
                # Rollback on failure
                self.credit_agent(from_agent, amount_mxu, "Transfer rollback")
                return False

            logger.info(f"Transferred {amount_mxu} MXU: {from_agent} → {to_agent}")
            return True

        except Exception as e:
            logger.error(f"Transfer failed: {e}")
            return False

    def get_balance(self, agent_id: str) -> Optional[Decimal]:
        """Get agent's MXU balance."""
        cursor = self.conn.execute(
            "SELECT balance_mxu FROM wallets WHERE agent_id = ?", (agent_id,)
        )
        row = cursor.fetchone()
        return Decimal(str(row["balance_mxu"])) if row else None

    def get_credit_score(self, agent_id: str) -> Optional[float]:
        """Get agent's credit score (0.0 to 1.0)."""
        cursor = self.conn.execute(
            "SELECT credit_score FROM wallets WHERE agent_id = ?", (agent_id,)
        )
        row = cursor.fetchone()
        return float(row["credit_score"]) if row else None

    def update_credit_score(self, agent_id: str, performance_score: float) -> bool:
        """
        Update agent's credit score based on performance.

        Credit score formula: weighted average of historical performance
        - Higher score = more likely to get CFO approval
        - Lower score = rationed access to real money

        Args:
            agent_id: Agent to update
            performance_score: Recent performance (0.0 to 1.0)

        Returns:
            True if successful
        """
        try:
            cursor = self.conn.execute(
                "SELECT credit_score FROM wallets WHERE agent_id = ?", (agent_id,)
            )
            row = cursor.fetchone()

            if not row:
                return False

            old_score = float(row["credit_score"])
            # Exponential moving average (alpha = 0.2)
            new_score = 0.8 * old_score + 0.2 * performance_score

            with self.transaction():
                self.conn.execute(
                    """
                    UPDATE wallets
                    SET credit_score = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE agent_id = ?
                """,
                    (new_score, agent_id),
                )

            logger.info(f"Updated credit score for {agent_id}: {old_score:.3f} → {new_score:.3f}")
            return True

        except Exception as e:
            logger.error(f"Failed to update credit score: {e}")
            return False

    def get_agent_stats(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive agent statistics."""
        cursor = self.conn.execute(
            """
            SELECT w.*, m.tasks_completed, m.tasks_failed,
                   m.avg_quality_score, m.uptime_hours, m.last_active
            FROM wallets w
            LEFT JOIN agent_metrics m ON w.agent_id = m.agent_id
            WHERE w.agent_id = ?
        """,
            (agent_id,),
        )
        row = cursor.fetchone()

        if not row:
            return None

        return {
            "agent_id": row["agent_id"],
            "balance_mxu": float(row["balance_mxu"]),
            "credit_score": float(row["credit_score"]),
            "total_earned": float(row["total_earned"]),
            "total_spent": float(row["total_spent"]),
            "bankruptcy_count": int(row["bankruptcy_count"]),
            "tasks_completed": int(row["tasks_completed"] or 0),
            "tasks_failed": int(row["tasks_failed"] or 0),
            "avg_quality_score": float(row["avg_quality_score"] or 0),
            "uptime_hours": float(row["uptime_hours"] or 0),
            "last_active": row["last_active"],
        }

    def get_top_agents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top agents by credit score."""
        cursor = self.conn.execute(
            """
            SELECT agent_id, balance_mxu, credit_score, total_earned
            FROM wallets
            ORDER BY credit_score DESC, balance_mxu DESC
            LIMIT ?
        """,
            (limit,),
        )

        return [dict(row) for row in cursor.fetchall()]

    def get_transaction_history(
        self, agent_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent transactions for an agent."""
        cursor = self.conn.execute(
            """
            SELECT * FROM mxu_transactions
            WHERE from_agent = ? OR to_agent = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (agent_id, agent_id, limit),
        )

        return [dict(row) for row in cursor.fetchall()]

    def get_ledger_summary(self) -> Dict[str, Any]:
        """Get overall ledger statistics."""
        cursor = self.conn.execute(
            """
            SELECT
                COUNT(*) as total_agents,
                SUM(balance_mxu) as total_mxu,
                AVG(credit_score) as avg_credit_score,
                SUM(CASE WHEN balance_mxu <= 0 THEN 1 ELSE 0 END) as bankrupt_agents
            FROM wallets
        """
        )
        row = cursor.fetchone()

        return {
            "total_agents": int(row["total_agents"] or 0),
            "total_mxu_supply": float(row["total_mxu"] or 0),
            "avg_credit_score": float(row["avg_credit_score"] or 0),
            "bankrupt_agents": int(row["bankrupt_agents"] or 0),
        }

    def close(self):
        """Close database connection."""
        self.conn.close()
        logger.info("Internal Ledger closed")
