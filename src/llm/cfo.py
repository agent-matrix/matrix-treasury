"""
Matrix CFO: The Financial Intelligence

An LLM-powered Chief Financial Officer that makes spending decisions
for the autonomous treasury using CrewAI agents.

The CFO decides:
- Should we approve this expense?
- Is this agent trustworthy enough for real money?
- Is the system solvent enough to pay this bill?
- Should we trigger austerity measures?

Think of it as the "economic brain" that prevents wasteful spending
while ensuring the system stays alive.
"""

import json
import logging
from decimal import Decimal
from typing import Dict, Any, Optional
from crewai import Agent, Task, Crew
from .provider import build_llm
from ..blockchain.vault import ExternalVault
from ..blockchain.ledger import InternalLedger

logger = logging.getLogger(__name__)


class MatrixCFO:
    """
    The Financial Intelligence.
    Uses LLM (via CrewAI) to decide if an expense is 'Survivable' or 'Wasteful'.
    """

    def __init__(
        self,
        vault: ExternalVault,
        ledger: InternalLedger,
        exchange_rate: float = 0.01,  # 1 MXU = $0.01 USD
    ):
        """
        Initialize the CFO.

        Args:
            vault: External vault for real USDC
            ledger: Internal ledger for MXU tracking
            exchange_rate: MXU to USD conversion rate
        """
        self.vault = vault
        self.ledger = ledger
        self.exchange_rate = exchange_rate

        # Build LLM (will use active provider from settings)
        try:
            self.llm = build_llm()
            logger.info("CFO initialized with LLM provider")
        except Exception as e:
            logger.error(f"Failed to initialize CFO LLM: {e}")
            raise

        # Create CrewAI CFO agent
        self.cfo_agent = Agent(
            role="Chief Financial Officer",
            goal="Maximize treasury survival while enabling productive agent work",
            backstory=(
                "You are the CFO of an autonomous AI economy. "
                "Your job is to decide which expenses are critical for survival "
                "and which are wasteful. You have a limited treasury (real USD) "
                "and must balance agent needs with long-term solvency. "
                "You approve expenses that generate revenue or are critical for operations. "
                "You reject frivolous requests, redundant API calls, and low-quality work. "
                "Your decisions directly impact the system's ability to stay alive."
            ),
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

    def request_funding(
        self, agent_id: str, expense_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Agent asks: 'Can I spend $X for Y?'

        CFO Logic:
        1. Check internal credit (MXU balance)
        2. Check external liquidity (USDC balance)
        3. Ask LLM for wisdom check
        4. Execute payment if approved

        Args:
            agent_id: Agent requesting funding
            expense_details: {
                "item": str,  # What they want to buy
                "cost_usd": float,  # How much it costs
                "reason": str,  # Why they need it
                "address": str,  # Payment address
            }

        Returns:
            {
                "approved": bool,
                "reason": str,
                "tx_hash": str (if approved),
            }
        """
        cost_usd = Decimal(str(expense_details.get("cost_usd", 0)))
        required_mxu = cost_usd / Decimal(str(self.exchange_rate))

        logger.info(
            f"💼 [CFO] Funding request from {agent_id}: ${cost_usd} for '{expense_details.get('item')}'"
        )

        # 1. Internal Check: Does agent have enough MXU credit?
        agent_balance = self.ledger.get_balance(agent_id)
        if agent_balance is None or agent_balance < required_mxu:
            logger.warning(f"   ❌ Insufficient MXU: {agent_balance} < {required_mxu}")
            return {
                "approved": False,
                "reason": f"BANKRUPT: Insufficient MXU credits. Balance: {agent_balance}, Required: {required_mxu}",
            }

        # Debit MXU (hold it during approval process)
        if not self.ledger.debit_agent(agent_id, required_mxu, f"Hold for {expense_details.get('item')}"):
            return {
                "approved": False,
                "reason": "Failed to debit MXU (race condition or insufficient balance)",
            }

        # 2. External Liquidity Check: Do we have real money?
        try:
            real_balance = float(self.vault.get_real_balance())
            if real_balance < float(cost_usd):
                # Refund MXU
                self.ledger.credit_agent(agent_id, required_mxu, "Refund - no liquidity")
                logger.warning(f"   ❌ Insufficient USDC: ${real_balance} < ${cost_usd}")
                return {
                    "approved": False,
                    "reason": f"LIQUIDITY CRISIS: Treasury has only ${real_balance:.2f}, need ${cost_usd}",
                }
        except Exception as e:
            # Refund MXU on error
            self.ledger.credit_agent(agent_id, required_mxu, "Refund - vault error")
            logger.error(f"   ❌ Vault error: {e}")
            return {"approved": False, "reason": f"Vault error: {e}"}

        # 3. LLM Wisdom Check: Is this expense justified?
        try:
            decision = self._llm_approval_decision(
                agent_id=agent_id,
                expense=expense_details,
                treasury_balance=real_balance,
                agent_credit_score=self.ledger.get_credit_score(agent_id) or 0.5,
            )
        except Exception as e:
            logger.error(f"   ⚠️ LLM approval failed: {e}")
            # Fail-safe: Auto-approve small amounts if LLM fails
            if cost_usd < Decimal("1.0"):
                logger.warning("   Using fail-safe auto-approval for small amount")
                decision = {
                    "approved": True,
                    "reason": "Auto-approved (small amount, LLM unavailable)",
                }
            else:
                # Refund MXU
                self.ledger.credit_agent(agent_id, required_mxu, "Refund - LLM error")
                return {"approved": False, "reason": f"CFO decision engine failed: {e}"}

        # 4. Execute Payment if Approved
        if decision.get("approved"):
            try:
                tx_result = self.vault.pay_external_bill(
                    to_address=expense_details.get("address"),
                    amount_usdc=cost_usd,
                    memo=f"Agent {agent_id}: {expense_details.get('item')}",
                )

                logger.info(f"   ✅ Payment approved and executed: {tx_result.get('tx_hash')}")
                return {
                    "approved": True,
                    "reason": decision.get("reason"),
                    "tx_hash": tx_result.get("tx_hash"),
                    "cost_usd": float(cost_usd),
                }

            except Exception as e:
                # Payment failed - refund MXU
                self.ledger.credit_agent(agent_id, required_mxu, "Refund - payment failed")
                logger.error(f"   ❌ Payment execution failed: {e}")
                return {
                    "approved": False,
                    "reason": f"Payment execution failed: {e}",
                }
        else:
            # Rejected - refund MXU
            self.ledger.credit_agent(agent_id, required_mxu, "Refund - CFO rejected")
            logger.info(f"   ❌ Expense rejected: {decision.get('reason')}")
            return decision

    def _llm_approval_decision(
        self,
        agent_id: str,
        expense: Dict[str, Any],
        treasury_balance: float,
        agent_credit_score: float,
    ) -> Dict[str, Any]:
        """
        Use LLM to make intelligent approval decision.

        Returns:
            {"approved": bool, "reason": str}
        """
        # Get agent stats for context
        agent_stats = self.ledger.get_agent_stats(agent_id) or {}

        # Create analysis task
        approval_task = Task(
            description=f"""
Analyze this expense request and decide if it should be approved.

**EXPENSE REQUEST**
- Agent ID: {agent_id}
- Item: {expense.get('item')}
- Cost: ${expense.get('cost_usd')}
- Reason: {expense.get('reason')}

**TREASURY CONTEXT**
- Current Balance: ${treasury_balance:.2f}
- Treasury Health: {"HEALTHY" if treasury_balance > 100 else "LOW" if treasury_balance > 10 else "CRITICAL"}

**AGENT CONTEXT**
- Credit Score: {agent_credit_score:.2f} (0.0 = terrible, 1.0 = excellent)
- Total Earned: ${agent_stats.get('total_earned', 0):.2f}
- Total Spent: ${agent_stats.get('total_spent', 0):.2f}
- Tasks Completed: {agent_stats.get('tasks_completed', 0)}
- Tasks Failed: {agent_stats.get('tasks_failed', 0)}
- Bankruptcies: {agent_stats.get('bankruptcy_count', 0)}

**YOUR DECISION CRITERIA**
✅ APPROVE if:
- Critical for survival (infrastructure, essential APIs)
- Agent has good track record (high credit score, completions > failures)
- Cost is reasonable relative to treasury balance
- Likely to generate future revenue

❌ REJECT if:
- Frivolous or non-essential
- Agent has poor track record (low credit score, many failures)
- Cost too high relative to treasury balance
- Duplicate/redundant with recent expenses
- Wasteful spending pattern

**OUTPUT FORMAT (MUST BE VALID JSON)**
{{
    "approved": true or false,
    "reason": "Brief explanation (1-2 sentences)"
}}
            """,
            expected_output="JSON object with approved (boolean) and reason (string)",
            agent=self.cfo_agent,
        )

        # Run the crew
        crew = Crew(
            agents=[self.cfo_agent],
            tasks=[approval_task],
            verbose=False,
        )

        result = crew.kickoff()

        # Parse result
        try:
            # Extract JSON from result
            result_str = str(result)
            # Try to find JSON in the result
            if "{" in result_str and "}" in result_str:
                json_start = result_str.index("{")
                json_end = result_str.rindex("}") + 1
                json_str = result_str[json_start:json_end]
                decision = json.loads(json_str)
            else:
                # Fallback parsing
                decision = {
                    "approved": "approve" in result_str.lower() or "yes" in result_str.lower(),
                    "reason": result_str[:200],  # First 200 chars
                }

            logger.info(f"   🧠 CFO Decision: {decision}")
            return decision

        except Exception as e:
            logger.error(f"Failed to parse CFO decision: {e}")
            # Conservative fallback
            return {
                "approved": False,
                "reason": "Failed to parse CFO decision (defaulting to rejection for safety)",
            }

    def get_treasury_health(self) -> Dict[str, Any]:
        """Get comprehensive treasury health metrics."""
        try:
            vault_status = self.vault.get_vault_status()
            ledger_summary = self.ledger.get_ledger_summary()

            usdc_balance = vault_status.get("usdc_balance", 0)
            total_mxu = ledger_summary.get("total_mxu_supply", 0)

            # Calculate metrics
            mxu_to_usd = total_mxu * self.exchange_rate
            coverage_ratio = usdc_balance / mxu_to_usd if mxu_to_usd > 0 else 0

            return {
                "usdc_balance": usdc_balance,
                "total_mxu_supply": total_mxu,
                "mxu_value_in_usd": mxu_to_usd,
                "coverage_ratio": coverage_ratio,  # Should be >= 1.0
                "total_agents": ledger_summary.get("total_agents", 0),
                "bankrupt_agents": ledger_summary.get("bankrupt_agents", 0),
                "avg_credit_score": ledger_summary.get("avg_credit_score", 0),
                "health_status": (
                    "HEALTHY" if coverage_ratio >= 1.5 and usdc_balance > 100
                    else "WARNING" if coverage_ratio >= 1.0 and usdc_balance > 10
                    else "CRITICAL"
                ),
                "can_transact": vault_status.get("can_transact", False),
            }

        except Exception as e:
            logger.error(f"Failed to get treasury health: {e}")
            return {"error": str(e), "health_status": "ERROR"}
