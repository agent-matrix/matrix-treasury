"""
Integration tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient

class TestAPIEndpoints:
    
    def test_health_check(self, client):
        """Test health endpoint"""
        response = client.get("/api/v1/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_agent_onboarding_flow(self, client):
        """Test complete agent onboarding flow"""
        # Onboard agent
        response = client.post(
            "/api/v1/agents/onboard",
            json={"agent_id": "test_agent_1", "agent_type": "agent"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # Get agent details
        response = client.get("/api/v1/agents/test_agent_1")
        assert response.status_code == 200
        agent = response.json()
        assert agent["id"] == "test_agent_1"
    
    def test_deposit_and_transaction_flow(self, client):
        """Test deposit and transaction flow"""
        # Deposit USD
        response = client.post(
            "/api/v1/deposits",
            json={"user_id": "user_1", "amount_usd": 1000.0}
        )
        assert response.status_code == 200
        deposit = response.json()
        assert deposit["mxu_received"] > 0
        
        # Onboard agent
        client.post(
            "/api/v1/agents/onboard",
            json={"agent_id": "agent_1"}
        )
        
        # Execute transaction
        response = client.post(
            "/api/v1/transactions",
            json={
                "from_id": "user_1",
                "to_id": "agent_1",
                "amount_mxu": 100.0,
                "quality_score": 0.95
            }
        )
        assert response.status_code == 200
        tx = response.json()
        assert tx["status"] == "success"
        assert tx["tax"] > 0
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200
        metrics = response.json()
        assert "supply" in metrics
        assert "reserves" in metrics
        assert "price_usd" in metrics
