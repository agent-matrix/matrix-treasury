"""
Unit tests for Economy
"""

import pytest
from src.core.economy import AutoselfEconomy, AgentStatus
from src.core.exceptions import InsufficientFunds, AgentNotFound

class TestEconomy:
    
    def test_agent_onboarding(self):
        """Test agent onboarding with UBC"""
        economy = AutoselfEconomy()
        
        # Seed UBC pool
        economy.treasury.mint_from_deposit(1000.0)
        
        result = economy.onboard_agent("agent_1")
        
        assert result["status"] == "success"
        assert result["ubc_granted"] > 0
        assert economy.balance("agent_1") > 0
    
    def test_ubc_renewal(self):
        """Test UBC renewal eligibility"""
        economy = AutoselfEconomy()
        economy.treasury.mint_from_deposit(1000.0)
        
        # Onboard and give reputation
        economy.onboard_agent("agent_1")
        economy.reputation["agent_1"] = 0.8
        
        # Drain balance
        balance = economy.balance("agent_1")
        economy.wallets["agent_1"] = 10.0  # Below threshold
        
        result = economy.renew_ubc_if_eligible("agent_1")
        
        assert result["eligible"] == True
        if result.get("status") == "renewed":
            assert economy.balance("agent_1") > 10.0
    
    def test_charge_for_work(self):
        """Test billing agent for work"""
        economy = AutoselfEconomy()
        economy.treasury.mint_from_deposit(1000.0)
        economy.onboard_agent("agent_1")

        # Give agent sufficient funds for the work (this is a large compute job)
        economy.deposit_usd("agent_1", 500.0)  # Add more funds for expensive work

        initial_balance = economy.balance("agent_1")

        metering = {
            "metering_source": "GUARDIAN",
            "timestamp": "2024-01-01T00:00:00",
            "gpu_seconds": 3600.0,
            "avg_watts": 450.0,
            "ram_gb_seconds": 3600.0 * 16
        }

        result = economy.charge_for_work("agent_1", metering)

        assert result["status"] == "success"
        assert economy.balance("agent_1") < initial_balance
    
    def test_payment_flow(self):
        """Test payment between agents"""
        economy = AutoselfEconomy()
        economy.treasury.mint_from_deposit(2000.0)
        
        # Onboard two agents
        economy.onboard_agent("client_1")
        economy.onboard_agent("agent_1")
        
        # Give client more funds
        economy.deposit_usd("client_1", 1000.0)
        
        client_initial = economy.balance("client_1")
        agent_initial = economy.balance("agent_1")
        
        # Execute payment
        result = economy.pay_agent("client_1", "agent_1", 100.0, quality_score=0.9)
        
        assert result["status"] == "success"
        assert economy.balance("client_1") < client_initial
        assert economy.balance("agent_1") > agent_initial
        assert result["tax"] > 0
    
    def test_bankruptcy_ladder(self):
        """Test bankruptcy ladder activation"""
        economy = AutoselfEconomy()
        economy.onboard_agent("agent_1")
        
        # Drain balance
        economy.wallets["agent_1"] = 0.1
        
        metering = {
            "metering_source": "GUARDIAN",
            "timestamp": "2024-01-01T00:00:00",
            "gpu_seconds": 3600.0,
            "avg_watts": 450.0
        }
        
        with pytest.raises(Exception):  # Should trigger bankruptcy
            economy.charge_for_work("agent_1", metering)
        
        # Check status changed
        assert economy.status["agent_1"] in [AgentStatus.THROTTLED, AgentStatus.HIBERNATED]
