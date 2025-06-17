import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from agents.ai_trading_agents import AITriggerAgent, AIExpertTraderAgent, AIRiskEvaluatorAgent
from fastapi import FastAPI

load_dotenv()

app = FastAPI()

class AITradingSystem:
    def __init__(self):
        # Initialize AI agents
        self.trigger_agent = AITriggerAgent()
        self.expert_trader = AIExpertTraderAgent()
        self.risk_evaluator = AIRiskEvaluatorAgent()
    
    async def process_trading_request(self, goals: dict, constraints: dict) -> dict:
        """Process a trading request through the AI agent system."""
        try:
            # 1. Trigger Agent analyzes the request and market conditions
            trigger_response = await self.trigger_agent.process_message({
                "type": "trading_request",
                "goals": goals,
                "constraints": constraints,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            if trigger_response["status"] == "error":
                return trigger_response
            
            # 2. Expert Trader develops and validates the strategy
            expert_response = await self.expert_trader.process_message({
                "type": "strategy_development",
                "trigger_analysis": trigger_response["response"],
                "goals": goals,
                "constraints": constraints
            })
            
            if expert_response["status"] == "error":
                return expert_response
            
            # 3. Risk Evaluator assesses the strategy
            risk_response = await self.risk_evaluator.evaluate_strategy(
                strategy=expert_response["response"],
                market_conditions=trigger_response["response"]
            )
            
            if risk_response["status"] == "error":
                return risk_response
            
            # 4. Expert Trader makes final decision and executes if approved
            final_decision = await self.expert_trader.process_message({
                "type": "execution_decision",
                "strategy": expert_response["response"],
                "risk_evaluation": risk_response["response"]
            })
            
            return final_decision
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error in trading system: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

async def main():
    # Example usage
    trading_system = AITradingSystem()
    
    # Example trading request
    goals = {
        "target_return": 0.1,
        "time_horizon": "1d",
        "risk_tolerance": "moderate",
        "assets": ["BTC", "ETH"],
        "strategy_type": "momentum"
    }
    
    constraints = {
        "max_position_size": 100000,
        "max_drawdown": 0.05,
        "allowed_assets": ["BTC", "ETH"],
        "min_liquidity": 1000000,
        "max_slippage": 0.01
    }
    
    try:
        print("Processing trading request...")
        result = await trading_system.process_trading_request(goals, constraints)
        print("\nTrading System Response:")
        print("Status:", result["status"])
        print("Message:", result["message"])
        print("Response:", result.get("response", {}))
        print("Timestamp:", result["timestamp"])
    except Exception as e:
        print(f"Error processing trading request: {e}")

if __name__ == "__main__":
    asyncio.run(main())

# Add your routes here 