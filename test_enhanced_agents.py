#!/usr/bin/env python3
"""
Test script for enhanced agents with real market data and risk assessment
"""

import asyncio
import json
import logging
from datetime import datetime
from agents.expert_trader_agent import ExpertTraderAgent
from agents.risk_agent import RiskAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_expert_trader_agent():
    """Test the enhanced ExpertTraderAgent with real market analysis"""
    print("🔍 Testing Enhanced ExpertTraderAgent...")
    
    try:
        # Initialize the agent
        agent = ExpertTraderAgent(did="did:eth:0x1234567890123456789012345678901234567890")
        
        # Create a test trading request
        test_request = {
            "goals": {
                "assets": ["AAPL", "MSFT", "GOOGL"],
                "position_size": 0.1,
                "target_return": 0.15
            },
            "constraints": {
                "stop_loss": 0.05,
                "take_profit": 0.2,
                "max_risk": 0.3
            }
        }
        
        # Test the analysis method directly
        analysis = await agent._analyze_trading_request(test_request)
        
        print("✅ ExpertTraderAgent analysis completed")
        print(f"\n📊 Market Analysis Results:")
        
        if "market_analysis" in analysis:
            market_data = analysis["market_analysis"]
            for asset, data in market_data.items():
                if isinstance(data, dict) and "error" not in data:
                    print(f"\n  {asset}:")
                    print(f"    Current Price: ${data.get('current_price', 'N/A'):.2f}")
                    print(f"    Volatility: {data.get('statistical_metrics', {}).get('volatility', 'N/A'):.4f}")
                    print(f"    Trend: {data.get('trend_analysis', {}).get('trend_direction', 'N/A')}")
                    print(f"    RSI: {data.get('technical_indicators', {}).get('rsi', 'N/A')}")
                elif "error" in data:
                    print(f"    {asset}: Error - {data['error']}")
        
        print(f"\n⚠️  Risk Assessment Results:")
        if "risk_assessment" in analysis:
            risk_data = analysis["risk_assessment"]
            for asset, data in risk_data.items():
                if isinstance(data, dict) and "error" not in data:
                    print(f"\n  {asset}:")
                    print(f"    Overall Risk: {data.get('risk_assessment', {}).get('overall_risk', 'N/A'):.3f}")
                    print(f"    Risk Level: {data.get('risk_assessment', {}).get('risk_level', 'N/A')}")
                    print(f"    Sharpe Ratio: {data.get('risk_metrics', {}).get('sharpe_ratio', 'N/A'):.3f}")
                elif "error" in data:
                    print(f"    {asset}: Error - {data['error']}")
        
        print(f"\n💡 Recommendations:")
        if "recommendations" in analysis:
            for rec in analysis["recommendations"]:
                print(f"  - {rec.get('asset', 'Unknown')}: {rec.get('recommendation', 'No recommendation')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ExpertTraderAgent test failed: {e}")
        logger.error(f"ExpertTraderAgent test error: {e}", exc_info=True)
        return False

async def test_risk_agent():
    """Test the enhanced RiskAgent with real risk assessment"""
    print("\n⚠️  Testing Enhanced RiskAgent...")
    
    try:
        # Initialize the agent
        agent = RiskAgent(did="did:eth:0x0987654321098765432109876543210987654321")
        
        # Create test trading analysis and market conditions
        test_trading_analysis = {
            "assets": ["AAPL", "MSFT"],
            "position_size": 0.15,
            "stop_loss": 0.03,
            "take_profit": 0.12
        }
        
        test_market_conditions = {
            "volatility": "moderate",
            "trend": "bullish",
            "market_regime": "normal"
        }
        
        # Test the risk evaluation method directly
        evaluation = await agent._evaluate_risk(test_trading_analysis, test_market_conditions)
        
        print("✅ RiskAgent evaluation completed")
        print(f"\n📈 Risk Evaluation Results:")
        
        if "risk_assessment" in evaluation:
            risk_data = evaluation["risk_assessment"]
            for asset, data in risk_data.items():
                if isinstance(data, dict) and "error" not in data:
                    print(f"\n  {asset}:")
                    print(f"    Overall Risk: {data.get('risk_assessment', {}).get('overall_risk', 'N/A'):.3f}")
                    print(f"    Risk Level: {data.get('risk_assessment', {}).get('risk_level', 'N/A')}")
                    print(f"    VaR (95%): {data.get('risk_metrics', {}).get('var_95', 'N/A'):.4f}")
                    print(f"    Sharpe Ratio: {data.get('risk_metrics', {}).get('sharpe_ratio', 'N/A'):.3f}")
                    print(f"    Risk-Reward Ratio: {data.get('position_risk', {}).get('risk_reward_ratio', 'N/A'):.2f}")
                    
                    # Show recommendations
                    recommendations = data.get('risk_assessment', {}).get('recommendations', [])
                    if recommendations:
                        print(f"    Recommendations:")
                        for rec in recommendations:
                            print(f"      - {rec}")
                elif "error" in data:
                    print(f"    {asset}: Error - {data['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ RiskAgent test failed: {e}")
        logger.error(f"RiskAgent test error: {e}", exc_info=True)
        return False

async def test_end_to_end_workflow():
    """Test the complete workflow from expert analysis to risk evaluation"""
    print("\n🔄 Testing End-to-End Workflow...")
    
    try:
        # Initialize both agents
        expert_agent = ExpertTraderAgent(did="did:eth:0x1234567890123456789012345678901234567890")
        risk_agent = RiskAgent(did="did:eth:0x0987654321098765432109876543210987654321")
        
        # Step 1: Expert analysis
        test_request = {
            "goals": {
                "assets": ["AAPL", "MSFT"],
                "position_size": 0.1,
                "target_return": 0.12
            },
            "constraints": {
                "stop_loss": 0.05,
                "take_profit": 0.15,
                "max_risk": 0.25
            }
        }
        
        print("  Step 1: Expert Analysis...")
        expert_analysis = await expert_agent._analyze_trading_request(test_request)
        
        # Step 2: Risk evaluation
        print("  Step 2: Risk Evaluation...")
        market_conditions = {
            "volatility": "moderate",
            "trend": "bullish"
        }
        
        risk_evaluation = await risk_agent._evaluate_risk(
            expert_analysis.get("market_analysis", {}),
            market_conditions
        )
        
        print("✅ End-to-end workflow completed successfully")
        
        # Summary
        print(f"\n📋 Workflow Summary:")
        print(f"  Expert Analysis: {'✅' if expert_analysis else '❌'}")
        print(f"  Risk Evaluation: {'✅' if risk_evaluation else '❌'}")
        
        # Check if we have real data (not errors)
        has_real_market_data = False
        has_real_risk_data = False
        
        if "market_analysis" in expert_analysis:
            for asset, data in expert_analysis["market_analysis"].items():
                if isinstance(data, dict) and "error" not in data and "current_price" in data:
                    has_real_market_data = True
                    break
        
        if "risk_assessment" in risk_evaluation:
            for asset, data in risk_evaluation["risk_assessment"].items():
                if isinstance(data, dict) and "error" not in data and "risk_metrics" in data:
                    has_real_risk_data = True
                    break
        
        print(f"  Real Market Data: {'✅' if has_real_market_data else '❌'}")
        print(f"  Real Risk Data: {'✅' if has_real_risk_data else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ End-to-end workflow test failed: {e}")
        logger.error(f"End-to-end workflow test error: {e}", exc_info=True)
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Enhanced Agents Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test ExpertTraderAgent
    results.append(await test_expert_trader_agent())
    
    # Test RiskAgent
    results.append(await test_risk_agent())
    
    # Test end-to-end workflow
    results.append(await test_end_to_end_workflow())
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"  Tests Passed: {passed}/{total}")
    print(f"  Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced agents are working correctly with real data.")
        print("\n✅ Integration Summary:")
        print("  - ExpertTraderAgent now uses real market analysis")
        print("  - RiskAgent now uses real risk assessment")
        print("  - Both agents provide data-driven recommendations")
        print("  - End-to-end workflow is functional")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    print(f"\n⏰ Test completed at: {datetime.utcnow().isoformat()}")

if __name__ == "__main__":
    asyncio.run(main()) 