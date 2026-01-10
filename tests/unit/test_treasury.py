"""
Unit tests for Treasury
"""

import pytest
from src.core.treasury import MatrixTreasury
from src.core.config import CostOracle, SystemPolicy
from src.core.exceptions import InsufficientReserves

class TestTreasury:
    
    def test_initialization(self):
        """Test treasury initialization"""
        oracle = CostOracle()
        policy = SystemPolicy()
        treasury = MatrixTreasury(oracle, policy)
        
        assert treasury.reserve_usd == 0.0
        assert treasury.mxu_supply == 0.0
        assert treasury.crisis_mode == False
    
    def test_pricing(self):
        """Test USD/MXU pricing calculation"""
        treasury = MatrixTreasury(CostOracle(), SystemPolicy())
        
        price = treasury.usd_per_mxu()
        assert price > 0
        
        rate = treasury.mxu_per_usd()
        assert rate > 0
        assert abs(price * rate - 1.0) < 0.0001
    
    def test_minting(self):
        """Test MXU minting from USD deposit"""
        treasury = MatrixTreasury(CostOracle(), SystemPolicy())
        
        initial_reserve = treasury.reserve_usd
        initial_supply = treasury.mxu_supply
        
        result = treasury.mint_from_deposit(1000.0)
        
        assert treasury.reserve_usd == initial_reserve + 1000.0
        assert treasury.mxu_supply > initial_supply
        assert result["user_share"] > 0
        assert result["commons_share"] > 0
    
    def test_burning(self):
        """Test MXU burning"""
        treasury = MatrixTreasury(CostOracle(), SystemPolicy())
        
        # Mint first
        treasury.mint_from_deposit(1000.0)
        
        initial_reserve = treasury.reserve_usd
        initial_supply = treasury.mxu_supply
        
        # Burn
        burn_amount = 100.0
        usd_cost = treasury.burn_for_costs(burn_amount)
        
        assert treasury.reserve_usd < initial_reserve
        assert treasury.mxu_supply == initial_supply - burn_amount
        assert usd_cost > 0
    
    def test_insolvency_protection(self):
        """Test that burning fails when reserves insufficient"""
        treasury = MatrixTreasury(CostOracle(), SystemPolicy())
        
        # Try to burn without reserves
        with pytest.raises(InsufficientReserves):
            treasury.burn_for_costs(1000.0)
    
    def test_progressive_taxation(self):
        """Test progressive tax calculation"""
        treasury = MatrixTreasury(CostOracle(), SystemPolicy())
        
        # Poor agent
        rate_poor = treasury.calculate_tx_tax_rate(100.0)
        
        # Rich agent
        rate_rich = treasury.calculate_tx_tax_rate(100000.0)
        
        assert rate_rich > rate_poor
        assert rate_poor >= treasury.policy.tx_tax_rate_base
        assert rate_rich <= treasury.policy.tx_tax_rate_max
    
    def test_reserve_health(self):
        """Test reserve health calculation"""
        treasury = MatrixTreasury(CostOracle(), SystemPolicy())
        
        # Mint reserves
        treasury.mint_from_deposit(10000.0)
        
        # Check health with projected burn
        health = treasury.reserve_health(100.0)  # 100 MXU/day
        
        assert "coverage_ratio" in health
        assert "coverage_days" in health
        assert "crisis_mode" in health
        
        # Should be healthy
        assert health["coverage_ratio"] > 1.0
        assert not health["crisis_mode"]
