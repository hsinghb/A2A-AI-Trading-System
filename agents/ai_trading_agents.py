from typing import Dict, Any, List
from datetime import datetime
from .ai_base_agent import AIBaseAgent
from .trading_tools import (
    MarketAnalysisTool,
    RiskAssessmentTool,
    TradeExecutionTool,
    PortfolioAnalysisTool
)

class AITriggerAgent(AIBaseAgent):
    def __init__(self, agent_name: str = "TriggerAgent"):
        tools = [
            MarketAnalysisTool(),
            PortfolioAnalysisTool()
        ]
        
        role = """You are an AI trading trigger agent responsible for initiating trading activities.
        Your role is to:
        1. Monitor market conditions and portfolio performance
        2. Identify trading opportunities
        3. Create well-defined trading goals and constraints
        4. Communicate effectively with the expert trader agent
        
        Always consider:
        - Current market conditions
        - Portfolio performance and composition
        - Risk tolerance and investment goals
        - Market trends and opportunities"""
        
        super().__init__(
            agent_name=agent_name,
            agent_role=role,
            tools=tools,
            temperature=0.7
        )

class AIExpertTraderAgent(AIBaseAgent):
    def __init__(self, agent_name: str = "ExpertTraderAgent"):
        tools = [
            MarketAnalysisTool(),
            RiskAssessmentTool(),
            TradeExecutionTool(),
            PortfolioAnalysisTool()
        ]
        
        role = """You are an AI expert trader agent responsible for executing trading strategies.
        Your role is to:
        1. Analyze trading requests from the trigger agent
        2. Develop and validate trading strategies
        3. Coordinate with the risk evaluator agent
        4. Execute trades based on approved strategies
        
        Always consider:
        - Trading goals and constraints
        - Risk assessments and recommendations
        - Market conditions and opportunities
        - Portfolio impact and performance"""
        
        super().__init__(
            agent_name=agent_name,
            agent_role=role,
            tools=tools,
            temperature=0.5  # Lower temperature for more consistent trading decisions
        )

class AIRiskEvaluatorAgent(AIBaseAgent):
    def __init__(self, agent_name: str = "RiskEvaluatorAgent"):
        tools = [
            MarketAnalysisTool(),
            RiskAssessmentTool(),
            PortfolioAnalysisTool()
        ]
        
        role = """You are an AI risk evaluator agent responsible for assessing trading risks.
        Your role is to:
        1. Evaluate trading strategies for potential risks
        2. Analyze market conditions and volatility
        3. Assess portfolio impact and exposure
        4. Provide risk management recommendations
        
        Always consider:
        - Market volatility and conditions
        - Portfolio risk exposure
        - Trading strategy complexity
        - Risk management best practices"""
        
        super().__init__(
            agent_name=agent_name,
            agent_role=role,
            tools=tools,
            temperature=0.3  # Lower temperature for more conservative risk assessment
        )
    
    async def evaluate_strategy(self, strategy: Dict[str, Any], market_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Specialized method for strategy risk evaluation."""
        try:
            # Get risk assessment using the risk assessment tool
            risk_assessment = await self.tools[1]._arun(strategy, market_conditions)
            
            # Get market analysis for additional context
            market_analysis = await self.tools[0]._arun(
                assets=strategy.get("assets", []),
                timeframe=strategy.get("timeframe", "1d")
            )
            
            # Get portfolio analysis for exposure assessment
            portfolio_analysis = await self.tools[2]._arun(
                portfolio_id=strategy.get("portfolio_id", "default")
            )
            
            # Process all information through the agent
            evaluation = await self.process_message({
                "type": "risk_evaluation",
                "strategy": strategy,
                "risk_assessment": risk_assessment,
                "market_analysis": market_analysis,
                "portfolio_analysis": portfolio_analysis
            })
            
            return evaluation
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error in strategy evaluation: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            } 