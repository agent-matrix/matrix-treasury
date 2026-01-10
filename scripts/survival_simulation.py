#!/usr/bin/env python3
"""
30-Day Survival Simulation
Stress tests the economy under various conditions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import datetime
from src.core.economy import AutoselfEconomy, AgentStatus

def run_simulation(days=30):
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║        Matrix Treasury v4.0 - 30-Day Survival Simulation            ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    
    economy = AutoselfEconomy()
    
    # Phase 1: Genesis
    print("📍 PHASE 1: GENESIS")
    print("─" * 70)
    
    humans = [f"human_{i}" for i in range(10)]
    for human in humans:
        result = economy.deposit_usd(human, 1000.0)
        print(f"  💰 {human}: $1000 → {result['mxu_received']:.2f} MXU")
    
    print(f"\n  Total Supply: {economy.treasury.mxu_supply:.2f} MXU")
    print(f"  Reserve: ${economy.treasury.reserve_usd:.2f} USD")
    
    # Phase 2: Agent Onboarding
    print("\n📍 PHASE 2: AGENT ONBOARDING")
    print("─" * 70)
    
    agents = []
    for i in range(50):
        agent_id = f"agent_{i}"
        result = economy.onboard_agent(agent_id)
        agents.append(agent_id)
        if i < 3:
            print(f"  🤖 {agent_id}: UBC {result['ubc_granted']:.2f} MXU")
    print(f"  ... {len(agents)} total agents onboarded")
    
    # Phase 3: Simulation
    print("\n📍 PHASE 3: 30-DAY ECONOMIC SIMULATION")
    print("─" * 70)
    
    events_log = []
    
    for day in range(1, days + 1):
        print(f"\n🗓️  DAY {day}")
        
        # Variable demand simulation
        if day == 10:
            num_jobs = 5
            print("  ⚠️  RECESSION: Demand dropped 75%")
            events_log.append(f"Day {day}: Recession")
        elif day == 15:
            print("  ⚡ COST SHOCK: GPU prices doubled")
            economy.oracle.gpu_usd_per_hour *= 2.0
            events_log.append(f"Day {day}: Cost Shock")
        elif day == 20:
            num_jobs = 60
            print("  📈 BOOM: Demand surge 300%")
            events_log.append(f"Day {day}: Economic Boom")
        else:
            num_jobs = random.randint(15, 25)
        
        # Execute daily jobs
        for _ in range(num_jobs):
            client = random.choice(humans)
            worker = random.choice(agents)
            
            if economy.balance(client) < 50:
                continue
            
            try:
                # Simulate work
                metering = {
                    "metering_source": "GUARDIAN",
                    "timestamp": datetime.now().isoformat(),
                    "gpu_seconds": random.uniform(10, 120),
                    "avg_watts": 450.0,
                    "ram_gb_seconds": random.uniform(1, 20) * 3600
                }
                
                economy.charge_for_work(worker, metering)
                
                # Payment
                budget = random.uniform(50, 200)
                quality = random.uniform(0.7, 1.0)
                economy.pay_agent(client, worker, budget, quality)
                
            except Exception as e:
                if "BANKRUPTCY" in str(e) or "INSUFFICIENT" in str(e):
                    renewal = economy.renew_ubc_if_eligible(worker)
                    if renewal.get("status") == "renewed":
                        print(f"    🆘 {worker} received UBC renewal")
        
        # Random capital injection
        if random.random() < 0.2:
            human = random.choice(humans)
            amount = random.uniform(100, 500)
            economy.deposit_usd(human, amount)
            print(f"    💵 {human} deposited ${amount:.2f}")
        
        # Run stabilizer
        if day % 5 == 0:
            projected_burn = economy.treasury.total_mxu_burned / day
            result = economy.stabilizer_step(projected_burn)
            
            if result["actions"]:
                print(f"    🏦 STABILIZER:")
                for action in result["actions"]:
                    print(f"       → {action['type']}: {action.get('reason', '')}")
        
        # Daily metrics
        metrics = economy.calculate_economic_metrics()
        health = economy.treasury.reserve_health(
            economy.treasury.total_mxu_burned / day
        )
        
        print(f"    📊 Active: {metrics['active_agents']}/{len(agents)} | "
              f"Unemployed: {metrics['unemployment_rate']:.1%} | "
              f"Coverage: {health['coverage_ratio']:.2f}x")
    
    # Final Report
    print("\n" + "═" * 70)
    print("📊 FINAL REPORT")
    print("═" * 70)
    
    final_metrics = economy.calculate_economic_metrics()
    final_health = economy.treasury.reserve_health(
        economy.treasury.total_mxu_burned / days
    )
    
    survivors = sum(
        1 for status in economy.status.values()
        if status in [AgentStatus.ACTIVE, AgentStatus.THROTTLED]
    )
    
    print(f"\n🤖 Agent Survival: {survivors}/{len(agents)} ({survivors/len(agents)*100:.1f}%)")
    print(f"💰 Final Reserve: ${economy.treasury.reserve_usd:,.2f} USD")
    print(f"🪙 Final Supply: {economy.treasury.mxu_supply:,.2f} MXU")
    print(f"📈 Coverage Ratio: {final_health['coverage_ratio']:.2f}x")
    print(f"🔥 Total Burned: {economy.treasury.total_mxu_burned:,.2f} MXU")
    print(f"💸 Total Minted: {economy.treasury.total_mxu_minted:,.2f} MXU")
    print(f"🔄 Total Transactions: {economy.treasury.total_transactions:,}")
    
    status = "✅ SYSTEM STABLE" if not final_health["crisis_mode"] else "⚠️  CRISIS MODE"
    print(f"\n🎯 Status: {status}")
    
    if events_log:
        print(f"\n📅 Major Events:")
        for event in events_log:
            print(f"  • {event}")
    
    print("\n" + "═" * 70)
    print("Simulation Complete!")
    print("═" * 70)

if __name__ == "__main__":
    run_simulation()
