#!/usr/bin/env python3
"""
Test script for enhanced trading tools
"""

import asyncio
import json
from agents.trading_tools import (
    MarketAnalysisTool,
    RiskAssessmentTool,
    PortfolioAnalysisTool
)

async def test_market_analysis():
    """Test the enhanced market analysis tool"""
    print("🔍 Testing Market Analysis Tool...")
    
    tool = MarketAnalysisTool()
    assets = ["AAPL", "MSFT", "GOOGL"]
    
    try:
        result = await tool._arun(assets, "1d")
        analysis = json.loads(result)
        
        print(f"✅ Market analysis completed for {len(assets)} assets")
        
        for asset, data in analysis.items():
            if "error" not in data:
                print(f"\n📊 {asset} Analysis:")
                print(f"  Current Price: ${data['current_price']:.2f}")
                print(f"  Volatility: {data['statistical_metrics']['volatility']:.4f}")
                print(f"  VaR (95%): {data['statistical_metrics']['var_95']:.4f}")
                print(f"  Trend: {data['trend_analysis']['trend_direction']}")
                print(f"  RSI: {data['technical_indicators']['rsi']:.2f}" if data['technical_indicators']['rsi'] else "  RSI: N/A")
                print(f"  Recommendations: {len(data['recommendations'])} items")
            else:
                print(f"❌ Error analyzing {asset}: {data['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Market analysis test failed: {e}")
        return False

async def test_risk_assessment():
    """Test the enhanced risk assessment tool"""
    print("\n⚠️  Testing Risk Assessment Tool...")
    
    tool = RiskAssessmentTool()
    strategy = {
        "assets": ["AAPL", "MSFT"],
        "position_size": 0.1,
        "stop_loss": 0.05,
        "take_profit": 0.15
    }
    market_conditions = {"volatility": "moderate", "trend": "bullish"}
    
    try:
        result = await tool._arun(strategy, market_conditions)
        assessment = json.loads(result)
        
        print(f"✅ Risk assessment completed for {len(strategy['assets'])} assets")
        
        for asset, data in assessment.items():
            if "error" not in data:
                print(f"\n📈 {asset} Risk Assessment:")
                print(f"  Overall Risk: {data['risk_assessment']['overall_risk']:.3f}")
                print(f"  Risk Level: {data['risk_assessment']['risk_level']}")
                print(f"  Sharpe Ratio: {data['risk_metrics']['sharpe_ratio']:.3f}")
                print(f"  VaR (95%): {data['risk_metrics']['var_95']:.4f}")
                print(f"  Risk-Reward Ratio: {data['position_risk']['risk_reward_ratio']:.2f}")
                print(f"  Recommendations: {len(data['risk_assessment']['recommendations'])} items")
            else:
                print(f"❌ Error assessing risk for {asset}: {data['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Risk assessment test failed: {e}")
        return False

async def test_portfolio_analysis():
    """Test the enhanced portfolio analysis tool"""
    print("\n💼 Testing Portfolio Analysis Tool...")
    
    tool = PortfolioAnalysisTool()
    portfolio_id = "test_portfolio"
    
    try:
        result = await tool._arun(portfolio_id)
        analysis = json.loads(result)
        
        if "error" not in analysis:
            print(f"✅ Portfolio analysis completed")
            print(f"\n📊 Portfolio Performance:")
            print(f"  Total Value: ${analysis['performance']['total_value']:,.2f}")
            print(f"  Volatility: {analysis['performance']['volatility']:.4f}")
            print(f"  Sharpe Ratio: {analysis['performance']['sharpe_ratio']:.3f}")
            print(f"  VaR (95%): {analysis['performance']['var_95']:.4f}")
            print(f"  Max Drawdown: {analysis['performance']['max_drawdown']:.4f}")
            print(f"  Diversification Score: {analysis['diversification_score']:.3f}")
            print(f"  Recommendations: {len(analysis['recommendations'])} items")
            
            print(f"\n📋 Holdings:")
            for holding in analysis['holdings']:
                print(f"  {holding['asset']}: {holding['allocation']:.1%} (${holding['value']:,.2f})")
        else:
            print(f"❌ Portfolio analysis error: {analysis['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Portfolio analysis test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Enhanced Trading Tools Test Suite")
    print("=" * 50)
    
    results = []
    
    # Test market analysis
    results.append(await test_market_analysis())
    
    # Test risk assessment
    results.append(await test_risk_assessment())
    
    # Test portfolio analysis
    results.append(await test_portfolio_analysis())
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"  Tests Passed: {passed}/{total}")
    print(f"  Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced trading tools are working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    asyncio.run(main()) 