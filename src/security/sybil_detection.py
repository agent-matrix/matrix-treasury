"""
Sybil Detection System: ML-Based Agent Fraud Detection

Detects suspicious agent behavior patterns that may indicate:
- Multiple fake identities (Sybil attacks)
- Credit score manipulation
- Transaction pattern anomalies
- Coordinated fraud

Features:
- Pattern-based detection (simple ML)
- Behavioral fingerprinting
- Transaction timing analysis
- Credit score anomaly detection
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class AgentBehaviorProfile:
    """Behavioral fingerprint of an agent"""
    agent_id: str
    first_seen: datetime
    transaction_count: int
    avg_transaction_amount: Decimal
    transaction_times: List[datetime]  # For timing analysis
    credit_score_history: List[Tuple[datetime, Decimal]]
    bankruptcy_count: int
    total_earned: Decimal
    total_spent: Decimal
    ip_addresses: Set[str]  # Simulated - in production track actual IPs
    device_fingerprints: Set[str]  # Simulated - in production track actual devices

    def transaction_velocity(self) -> float:
        """Calculate transactions per hour"""
        if not self.transaction_times or len(self.transaction_times) < 2:
            return 0.0

        time_span = (self.transaction_times[-1] - self.transaction_times[0]).total_seconds() / 3600
        if time_span == 0:
            return float(self.transaction_count)

        return self.transaction_count / time_span

    def credit_score_volatility(self) -> Decimal:
        """Calculate credit score volatility (standard deviation)"""
        if len(self.credit_score_history) < 2:
            return Decimal("0")

        scores = [score for _, score in self.credit_score_history]
        mean = sum(scores) / len(scores)
        variance = sum((score - mean) ** 2 for score in scores) / len(scores)
        return variance ** Decimal("0.5")


class SybilDetector:
    """
    ML-based sybil and fraud detection system.
    """

    def __init__(self):
        """Initialize detection system"""
        self.profiles: Dict[str, AgentBehaviorProfile] = {}
        self.flagged_agents: Set[str] = set()
        self.agent_groups: Dict[str, Set[str]] = defaultdict(set)  # Detected clusters

        # Detection thresholds
        self.max_transaction_velocity = 100.0  # Trans/hour
        self.max_credit_score_volatility = Decimal("0.3")  # Volatility threshold
        self.min_account_age_minutes = 5  # Minimum age before transacting
        self.similarity_threshold = 0.8  # Behavioral similarity threshold

        logger.info("Sybil Detection System initialized")

    def track_agent(
        self,
        agent_id: str,
        transaction_amount: Optional[Decimal] = None,
        credit_score: Optional[Decimal] = None,
        ip_address: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
    ) -> None:
        """
        Track agent activity for behavioral analysis.

        Args:
            agent_id: Agent identifier
            transaction_amount: Amount of transaction (if any)
            credit_score: Current credit score (if updated)
            ip_address: IP address (simulated)
            device_fingerprint: Device fingerprint (simulated)
        """
        now = datetime.now()

        # Create profile if new agent
        if agent_id not in self.profiles:
            self.profiles[agent_id] = AgentBehaviorProfile(
                agent_id=agent_id,
                first_seen=now,
                transaction_count=0,
                avg_transaction_amount=Decimal("0"),
                transaction_times=[],
                credit_score_history=[],
                bankruptcy_count=0,
                total_earned=Decimal("0"),
                total_spent=Decimal("0"),
                ip_addresses=set(),
                device_fingerprints=set(),
            )

        profile = self.profiles[agent_id]

        # Update transaction data
        if transaction_amount is not None:
            profile.transaction_count += 1
            profile.transaction_times.append(now)

            # Update average
            total = profile.avg_transaction_amount * Decimal(profile.transaction_count - 1)
            profile.avg_transaction_amount = (total + transaction_amount) / Decimal(profile.transaction_count)

            if transaction_amount > 0:
                profile.total_earned += transaction_amount
            else:
                profile.total_spent += abs(transaction_amount)

        # Update credit score history
        if credit_score is not None:
            profile.credit_score_history.append((now, credit_score))

        # Track IP and device (simulated)
        if ip_address:
            profile.ip_addresses.add(ip_address)

        if device_fingerprint:
            profile.device_fingerprints.add(device_fingerprint)

    def detect_sybil_attack(self, agent_id: str) -> Dict[str, any]:
        """
        Analyze agent for sybil attack indicators.

        Args:
            agent_id: Agent to analyze

        Returns:
            Detection results with risk score and flags
        """
        if agent_id not in self.profiles:
            return {
                "agent_id": agent_id,
                "is_suspicious": False,
                "risk_score": 0.0,
                "flags": [],
            }

        profile = self.profiles[agent_id]
        flags = []
        risk_score = 0.0

        # Flag 1: High transaction velocity (bot-like behavior)
        velocity = profile.transaction_velocity()
        if velocity > self.max_transaction_velocity:
            flags.append(f"High transaction velocity: {velocity:.1f} tx/hour")
            risk_score += 0.3

        # Flag 2: New account with immediate high-value transactions
        account_age = (datetime.now() - profile.first_seen).total_seconds() / 60
        if account_age < self.min_account_age_minutes and profile.transaction_count > 0:
            flags.append(f"New account ({account_age:.1f} min) with immediate activity")
            risk_score += 0.2

        # Flag 3: Credit score manipulation (high volatility)
        volatility = profile.credit_score_volatility()
        if volatility > self.max_credit_score_volatility:
            flags.append(f"Credit score manipulation: volatility {volatility:.2f}")
            risk_score += 0.25

        # Flag 4: Shared IP with multiple agents (sybil cluster)
        if profile.ip_addresses:
            shared_ip_count = self._count_shared_ips(agent_id)
            if shared_ip_count > 5:
                flags.append(f"Shared IP with {shared_ip_count} other agents")
                risk_score += 0.3

        # Flag 5: Multiple bankruptcies (abuse pattern)
        if profile.bankruptcy_count > 2:
            flags.append(f"Multiple bankruptcies: {profile.bankruptcy_count}")
            risk_score += 0.2

        # Flag 6: Spending >> Earning (potential drain attack)
        if profile.total_spent > profile.total_earned * Decimal("2"):
            flags.append(f"Spending ({profile.total_spent}) >> Earning ({profile.total_earned})")
            risk_score += 0.25

        # Normalize risk score
        risk_score = min(risk_score, 1.0)

        is_suspicious = risk_score >= 0.5

        if is_suspicious and agent_id not in self.flagged_agents:
            self.flagged_agents.add(agent_id)
            logger.warning(f"🚨 [SYBIL] Agent {agent_id} flagged as suspicious (risk: {risk_score:.2f})")

        return {
            "agent_id": agent_id,
            "is_suspicious": is_suspicious,
            "risk_score": risk_score,
            "flags": flags,
            "profile": {
                "account_age_hours": (datetime.now() - profile.first_seen).total_seconds() / 3600,
                "transaction_count": profile.transaction_count,
                "transaction_velocity": velocity,
                "credit_score_volatility": float(volatility),
                "bankruptcy_count": profile.bankruptcy_count,
            },
        }

    def detect_sybil_cluster(self) -> List[Set[str]]:
        """
        Detect clusters of related agents (sybil networks).

        Uses behavioral similarity and shared resources.

        Returns:
            List of agent clusters
        """
        clusters = []

        # Build similarity graph
        similarity_graph = defaultdict(set)

        agent_ids = list(self.profiles.keys())
        for i, agent1 in enumerate(agent_ids):
            for agent2 in agent_ids[i+1:]:
                similarity = self._calculate_similarity(agent1, agent2)

                if similarity >= self.similarity_threshold:
                    similarity_graph[agent1].add(agent2)
                    similarity_graph[agent2].add(agent1)

        # Find connected components (clusters)
        visited = set()

        for agent_id in agent_ids:
            if agent_id in visited:
                continue

            # BFS to find cluster
            cluster = set()
            queue = [agent_id]

            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue

                visited.add(current)
                cluster.add(current)

                # Add neighbors
                for neighbor in similarity_graph[current]:
                    if neighbor not in visited:
                        queue.append(neighbor)

            # Only report clusters of size > 1
            if len(cluster) > 1:
                clusters.append(cluster)
                logger.warning(f"🚨 [SYBIL] Detected cluster of {len(cluster)} related agents")

        return clusters

    def _count_shared_ips(self, agent_id: str) -> int:
        """Count how many other agents share IPs with this agent"""
        if agent_id not in self.profiles:
            return 0

        agent_ips = self.profiles[agent_id].ip_addresses
        if not agent_ips:
            return 0

        shared_count = 0
        for other_id, other_profile in self.profiles.items():
            if other_id == agent_id:
                continue

            # Check for IP overlap
            if agent_ips & other_profile.ip_addresses:
                shared_count += 1

        return shared_count

    def _calculate_similarity(self, agent1: str, agent2: str) -> float:
        """
        Calculate behavioral similarity between two agents.

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if agent1 not in self.profiles or agent2 not in self.profiles:
            return 0.0

        profile1 = self.profiles[agent1]
        profile2 = self.profiles[agent2]

        similarity_score = 0.0

        # Shared IPs (strong signal)
        if profile1.ip_addresses & profile2.ip_addresses:
            similarity_score += 0.4

        # Shared device fingerprints (strong signal)
        if profile1.device_fingerprints & profile2.device_fingerprints:
            similarity_score += 0.3

        # Similar transaction patterns
        if profile1.transaction_count > 0 and profile2.transaction_count > 0:
            amt_diff = abs(profile1.avg_transaction_amount - profile2.avg_transaction_amount)
            max_amt = max(profile1.avg_transaction_amount, profile2.avg_transaction_amount)
            if max_amt > 0:
                amt_similarity = 1.0 - float(amt_diff / max_amt)
                similarity_score += 0.15 * amt_similarity

        # Created within same timeframe (weak signal)
        time_diff = abs((profile1.first_seen - profile2.first_seen).total_seconds())
        if time_diff < 300:  # Within 5 minutes
            similarity_score += 0.15

        return min(similarity_score, 1.0)

    def get_flagged_agents(self) -> List[Dict[str, any]]:
        """Get all flagged agents with their risk assessments"""
        flagged = []

        for agent_id in self.flagged_agents:
            result = self.detect_sybil_attack(agent_id)
            flagged.append(result)

        return flagged

    def reset_flag(self, agent_id: str) -> None:
        """Remove sybil flag from agent (after manual review)"""
        if agent_id in self.flagged_agents:
            self.flagged_agents.remove(agent_id)
            logger.info(f"✅ [SYBIL] Flag removed from {agent_id}")

    def get_detection_stats(self) -> Dict[str, any]:
        """Get detection system statistics"""
        total_agents = len(self.profiles)
        flagged_count = len(self.flagged_agents)
        clusters = self.detect_sybil_cluster()

        return {
            "total_agents_tracked": total_agents,
            "flagged_agents": flagged_count,
            "flagged_percentage": (flagged_count / total_agents * 100) if total_agents > 0 else 0.0,
            "detected_clusters": len(clusters),
            "largest_cluster_size": max([len(c) for c in clusters]) if clusters else 0,
        }
