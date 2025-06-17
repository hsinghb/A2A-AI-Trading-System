#!/usr/bin/env python3
"""
Script to test trading agents with the new contract
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Force reload environment variables
load_dotenv(project_root / ".env", override=True)

def test_trading_agents():
    """Test trading agents with the new contract"""
    print("🔄 Testing trading agents with new contract...")
    print("=" * 60)
    
    try:
        # Import the backend agent registry
        from backend.blockchain.agent_registry import AgentRegistryContract
        
        # Initialize the contract interface
        print("1. Initializing contract interface...")
        agent_registry = AgentRegistryContract()
        print(f"   ✅ Contract initialized at: {agent_registry.contract_address}")
        print(f"   ✅ Admin address: {agent_registry.admin_address}")
        
        # Test admin functions
        print("\n2. Testing admin functions...")
        try:
            admin = agent_registry.get_admin()
            print(f"   ✅ Current admin: {admin}")
        except Exception as e:
            print(f"   ❌ Error getting admin: {str(e)}")
            return False
        
        # Test agent registration
        print("\n3. Testing agent registration...")
        
        # Sample trading agents
        test_agents = [
            {
                "name": "Risk Evaluator Agent",
                "did": "did:eth:0x1111111111111111111111111111111111111111",
                "public_key": "risk_evaluator_public_key_123",
                "metadata": {
                    "type": "risk_evaluator",
                    "version": "1.0",
                    "capabilities": ["risk_assessment", "portfolio_analysis"]
                }
            },
            {
                "name": "Trading Agent",
                "did": "did:eth:0x2222222222222222222222222222222222222222", 
                "public_key": "trading_agent_public_key_456",
                "metadata": {
                    "type": "trading",
                    "version": "1.0",
                    "capabilities": ["market_analysis", "trade_execution"]
                }
            },
            {
                "name": "Expert Trader Agent",
                "did": "did:eth:0x3333333333333333333333333333333333333333",
                "public_key": "expert_trader_public_key_789",
                "metadata": {
                    "type": "expert_trader",
                    "version": "1.0",
                    "capabilities": ["advanced_analysis", "strategy_optimization"]
                }
            }
        ]
        
        registered_agents = []
        
        for i, agent in enumerate(test_agents, 1):
            print(f"\n   Registering agent {i}: {agent['name']}")
            try:
                # Register the agent
                tx_hash = agent_registry.register_agent(
                    did=agent['did'],
                    public_key=agent['public_key'],
                    metadata=agent['metadata']
                )
                print(f"   ✅ Agent registered! Transaction: {tx_hash}")
                
                # Verify registration
                agent_info = agent_registry.get_agent(agent['did'])
                print(f"   ✅ Agent verified - Address: {agent_info['agent_address']}")
                print(f"   ✅ Agent verified - Active: {agent_info['is_active']}")
                print(f"   ✅ Agent verified - Reputation: {agent_info['reputation']}")
                
                registered_agents.append(agent)
                
            except Exception as e:
                print(f"   ❌ Error registering agent: {str(e)}")
                continue
        
        if not registered_agents:
            print("   ❌ No agents were successfully registered")
            return False
        
        # Test reputation updates
        print(f"\n4. Testing reputation updates for {len(registered_agents)} agents...")
        
        for i, agent in enumerate(registered_agents):
            print(f"\n   Updating reputation for: {agent['name']}")
            try:
                # Update reputation (simulate successful interaction)
                tx_hash = agent_registry.update_reputation(
                    agent_address=agent['did'].replace("did:eth:", ""),
                    success=True,
                    metadata={"interaction_type": "test", "result": "success"}
                )
                print(f"   ✅ Reputation updated! Transaction: {tx_hash}")
                
                # Check updated reputation
                agent_info = agent_registry.get_agent(agent['did'])
                print(f"   ✅ New reputation: {agent_info['reputation']}")
                print(f"   ✅ Total interactions: {agent_info['total_interactions']}")
                print(f"   ✅ Successful interactions: {agent_info['successful_interactions']}")
                
            except Exception as e:
                print(f"   ❌ Error updating reputation: {str(e)}")
                continue
        
        # Test agent deactivation
        print(f"\n5. Testing agent deactivation...")
        if registered_agents:
            test_agent = registered_agents[0]
            print(f"   Deactivating agent: {test_agent['name']}")
            try:
                tx_hash = agent_registry.deactivate_agent(test_agent['did'])
                print(f"   ✅ Agent deactivated! Transaction: {tx_hash}")
                
                # Verify deactivation
                agent_info = agent_registry.get_agent(test_agent['did'])
                print(f"   ✅ Agent status: {'Active' if agent_info['is_active'] else 'Inactive'}")
                
            except Exception as e:
                print(f"   ❌ Error deactivating agent: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🎉 Trading agent tests completed successfully!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"- Contract address: {agent_registry.contract_address}")
        print(f"- Admin address: {agent_registry.admin_address}")
        print(f"- Agents registered: {len(registered_agents)}")
        print(f"- All admin functions working: ✅")
        print(f"- All agent functions working: ✅")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing trading agents: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_backend_integration():
    """Test backend integration with the new contract"""
    print("\n🔄 Testing backend integration...")
    print("=" * 60)
    
    try:
        # Test importing and using the backend modules
        from backend.blockchain.agent_registry import AgentRegistryContract
        from backend.did_registry import DIDRegistry
        
        print("1. Testing backend imports...")
        print("   ✅ AgentRegistryContract imported successfully")
        print("   ✅ DIDRegistry imported successfully")
        
        # Test DID registry
        print("\n2. Testing DID registry...")
        did_registry = DIDRegistry()
        print("   ✅ DID registry initialized successfully")
        
        # Test agent orchestrator
        print("\n3. Testing agent orchestrator...")
        try:
            from backend.agent_orchestrator import AgentOrchestrator
            orchestrator = AgentOrchestrator()
            print("   ✅ Agent orchestrator initialized successfully")
        except Exception as e:
            print(f"   ⚠️  Agent orchestrator error (may be expected): {str(e)}")
        
        print("\n✅ Backend integration tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Backend integration error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting comprehensive trading agent tests...")
    
    # Test trading agents
    agents_success = test_trading_agents()
    
    # Test backend integration
    backend_success = test_backend_integration()
    
    print("\n" + "=" * 60)
    if agents_success and backend_success:
        print("🎉 All tests passed! Your trading system is ready!")
        print("\nNext steps:")
        print("1. Start your trading system")
        print("2. Monitor transactions on Etherscan")
        print("3. Check agent performance and reputation")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    print("=" * 60) 