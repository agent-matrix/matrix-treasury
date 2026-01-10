"""
Stress tests using Locust
"""

from locust import HttpUser, task, between
import random

class TreasuryUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize user"""
        self.agent_id = f"agent_{random.randint(1000, 9999)}"
        
        # Onboard
        response = self.client.post(
            "/api/v1/agents/onboard",
            json={"agent_id": self.agent_id}
        )
        
        if response.status_code == 200:
            self.onboarded = True
        else:
            self.onboarded = False
    
    @task(3)
    def get_metrics(self):
        """Get metrics"""
        self.client.get("/api/v1/metrics")
    
    @task(2)
    def get_agent_details(self):
        """Get agent details"""
        if self.onboarded:
            self.client.get(f"/api/v1/agents/{self.agent_id}")
    
    @task(1)
    def estimate_cost(self):
        """Estimate cost"""
        self.client.post(
            "/api/v1/estimate-cost",
            json={
                "gpu_hours": random.uniform(0.1, 2.0),
                "ram_gb_hours": random.uniform(1.0, 16.0),
                "storage_gb_days": random.uniform(0.1, 10.0)
            }
        )
