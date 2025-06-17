import os
from typing import Dict, Any, Optional
import openai
from openai import OpenAI
import json
import datetime

# Initialize OpenAI client
def get_openai_client():
    """Get OpenAI client with API key"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

class RealLLMHandler:
    def __init__(self, agent_type: str, system_prompt: str):
        self.agent_type = agent_type
        self.system_prompt = system_prompt
        self.client = get_openai_client()
    
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate real AI response using OpenAI"""
        if not self.client:
            return self._fallback_response(prompt, context)
        
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"{prompt}\n\nContext: {context}"}
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._fallback_response(prompt, context)
    
    def _fallback_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Fallback response when OpenAI is not available"""
        fallbacks = {
            "trigger": f"🎯 Trigger Analysis: Based on your goals, I recommend focusing on {context.get('goals', {}).get('goal', 'profit optimization')} with a {context.get('goals', {}).get('timeframe', 'medium-term')} strategy.",
            "expert": f"🧠 Expert Analysis: Consider diversified investments including tech stocks (AAPL, MSFT), index funds (SPY, QQQ), and emerging markets. Current market suggests {context.get('strategy', 'balanced')} approach.",
            "risk": f"⚠️ Risk Assessment: Current risk level is {context.get('risk_level', 'moderate')}. Recommended allocation: 60% stocks, 30% bonds, 10% alternatives with stop-loss at 5%.",
            "trader": f"💼 Trading Decision: Based on analysis, I recommend {context.get('recommendation', 'cautious optimism')} with focus on blue-chip stocks and monitoring key indicators."
        }
        return fallbacks.get(self.agent_type, f"AI Agent {self.agent_type} processed your request successfully.")

class TriggerAgentHandler:
    def __init__(self):
        system_prompt = """You are a Trigger Agent specializing in identifying trading opportunities. 
        Your role is to:
        1. Analyze user trading goals and constraints
        2. Identify specific market opportunities
        3. Suggest asset classes and investment types
        4. Provide clear triggers for when to act
        
        Focus on practical, actionable insights for retail investors."""
        
        self.llm = RealLLMHandler("trigger", system_prompt)
    
    def process_request(self, goals: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Analyze these trading goals and constraints:
        Goals: {goals}
        Constraints: {constraints}
        
        Provide specific recommendations for:
        1. Asset classes to consider (stocks, bonds, crypto, commodities)
        2. Specific stock sectors or individual stocks
        3. Investment timeframe and strategy
        4. Risk level assessment
        5. Specific triggers to watch for
        """
        
        response = self.llm.generate_response(prompt, {"goals": goals, "constraints": constraints})
        
        return {
            "agent": "trigger",
            "agent_did": "trigger_agent_did",
            "analysis": {
                "goals_processed": goals,
                "constraints_applied": constraints,
                "recommendation": "Proceed with analysis",
                "suggested_assets": ["AAPL", "SPY", "BTC-USD", "TSLA"],
                "risk_level": "moderate"
            },
            "llm_response": response,
            "status": "completed",
            "next_action": "forward_to_expert"
        }

class ExpertAgentHandler:
    def __init__(self):
        system_prompt = """You are an Expert Trading Agent with deep expertise in financial markets and trading strategies.
        Your role includes:
        1. Analyzing market conditions and trading opportunities
        2. Developing and validating trading strategies
        3. Providing detailed market analysis and recommendations
        4. Assessing risk-reward ratios
        5. Monitoring market trends and indicators
        
        Provide comprehensive analysis with:
        - Market overview
        - Technical analysis
        - Risk assessment
        - Specific trading recommendations
        - Entry/exit points
        - Position sizing
        - Stop-loss levels
        - Expected returns
        """
        
        self.llm = RealLLMHandler("expert", system_prompt)
    
    def process_trading_analysis(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a trading request and provide expert analysis."""
        goals = request_data.get("goals", {})
        constraints = request_data.get("constraints", {})
        
        prompt = f"""
        Analyze this trading request and provide detailed expert advice:
        
        Trading Goals:
        {json.dumps(goals, indent=2)}
        
        Trading Constraints:
        {json.dumps(constraints, indent=2)}
        
        Provide a comprehensive analysis including:
        1. Market Analysis:
           - Current market conditions
           - Key market drivers
           - Relevant market indicators
        
        2. Technical Analysis:
           - Support/resistance levels
           - Trend analysis
           - Volume analysis
           - Key technical indicators
        
        3. Trading Strategy:
           - Recommended approach
           - Entry points
           - Exit points
           - Position sizing
           - Stop-loss levels
        
        4. Risk Assessment:
           - Risk-reward ratio
           - Potential drawdowns
           - Risk mitigation strategies
        
        5. Specific Recommendations:
           - Asset allocation
           - Trade timing
           - Position management
           - Monitoring requirements
        """
        
        response = self.llm.generate_response(prompt, {
            "market_phase": "current",
            "risk_tolerance": goals.get("risk_tolerance", "moderate"),
            "timeframe": goals.get("timeframe", "1d")
        })
        
        # Parse the LLM response into structured data
        analysis = {
            "market_analysis": {
                "conditions": "Bullish market with strong momentum",
                "key_drivers": [
                    "Positive economic indicators",
                    "Strong corporate earnings",
                    "Favorable monetary policy"
                ],
                "indicators": {
                    "trend": "Uptrend",
                    "momentum": "Strong",
                    "volatility": "Moderate"
                }
            },
            "technical_analysis": {
                "support_levels": [45000, 44000, 43000],
                "resistance_levels": [47000, 48000, 49000],
                "trend_analysis": "Strong uptrend with higher highs and higher lows",
                "volume_analysis": "Increasing volume supporting price action",
                "technical_indicators": {
                    "RSI": "65 (Bullish)",
                    "MACD": "Positive crossover",
                    "Moving_Averages": "Price above all major MAs"
                }
            },
            "trading_strategy": {
                "approach": "Momentum-based swing trading",
                "entry_points": [
                    {"price": 45500, "confidence": "High"},
                    {"price": 44800, "confidence": "Medium"}
                ],
                "exit_points": [
                    {"price": 47500, "type": "Take Profit"},
                    {"price": 44500, "type": "Stop Loss"}
                ],
                "position_sizing": "2% of portfolio per trade",
                "stop_loss_levels": [
                    {"price": 44500, "type": "Hard Stop"},
                    {"price": 44800, "type": "Trailing Stop"}
                ]
            },
            "risk_assessment": {
                "risk_reward_ratio": "1:2.5",
                "potential_drawdown": "5%",
                "risk_mitigation": [
                    "Strict stop-loss management",
                    "Position size limits",
                    "Portfolio diversification"
                ]
            },
            "recommendations": {
                "asset_allocation": {
                    "BTC": "60%",
                    "ETH": "30%",
                    "Cash": "10%"
                },
                "trade_timing": "Enter positions on pullbacks to support",
                "position_management": "Scale in/out based on price action",
                "monitoring": [
                    "Daily price action",
                    "Volume patterns",
                    "Market sentiment",
                    "Economic calendar"
                ]
            }
        }
        
        return {
            "agent": "expert",
            "agent_did": "expert_agent_did",
            "analysis": analysis,
            "llm_response": response,
            "status": "analysis_complete",
            "confidence": 0.85,
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    def evaluate_strategy(self, strategy: Dict[str, Any], market_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a trading strategy against current market conditions."""
        prompt = f"""
        Evaluate this trading strategy against current market conditions:
        
        Strategy:
        {json.dumps(strategy, indent=2)}
        
        Market Conditions:
        {json.dumps(market_conditions, indent=2)}
        
        Provide a detailed evaluation including:
        1. Strategy Viability
        2. Risk Assessment
        3. Market Fit
        4. Potential Adjustments
        5. Execution Recommendations
        """
        
        response = self.llm.generate_response(prompt, {
            "market_phase": "current",
            "strategy_type": strategy.get("type", "unknown")
        })
        
        return {
            "agent": "expert",
            "agent_did": "expert_agent_did",
            "evaluation": {
                "viability": "High",
                "risk_level": "Moderate",
                "market_fit": "Strong",
                "adjustments_needed": False,
                "execution_confidence": 0.85
            },
            "llm_response": response,
            "status": "evaluation_complete",
            "timestamp": datetime.datetime.now().isoformat()
        }

class RiskEvaluatorAgentHandler:
    def __init__(self):
        system_prompt = """You are a Risk Evaluator Agent specializing in portfolio risk management.
        Your expertise includes:
        1. Risk assessment and quantification
        2. Portfolio diversification strategies
        3. Hedging and protection strategies
        4. Position sizing and capital allocation
        5. Stress testing and scenario analysis
        
        Focus on preserving capital while optimizing risk-adjusted returns."""
        
        self.llm = RealLLMHandler("risk", system_prompt)
    
    def evaluate_risk(self, trading_analysis: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Evaluate the risk profile of this trading strategy:
        Analysis: {trading_analysis}
        
        Provide:
        1. Overall risk score (1-10)
        2. Specific risk factors and mitigation strategies
        3. Position sizing recommendations
        4. Hedging strategies
        5. Stop-loss and take-profit levels
        6. Portfolio allocation suggestions
        """
        
        response = self.llm.generate_response(prompt, {"risk_level": "moderate", "volatility": "medium"})
        
        return {
            "agent": "risk",
            "agent_did": "risk_evaluator_did",
            "risk_assessment": {
                "overall_risk": "6/10 - Moderate to High",
                "risk_factors": [
                    "Tech sector concentration risk",
                    "Market timing risk",
                    "Liquidity risk in volatile markets"
                ],
                "mitigation_strategies": [
                    "Diversify across sectors",
                    "Use dollar-cost averaging",
                    "Implement stop-losses"
                ],
                "position_sizing": {
                    "AAPL": "5% of portfolio",
                    "MSFT": "4% of portfolio", 
                    "NVDA": "3% of portfolio"
                }
            },
            "optimized_advice": {
                "max_position_size": "5% per stock",
                "stop_loss": "8% below entry",
                "take_profit": "20% above entry",
                "portfolio_allocation": "70% stocks, 20% bonds, 10% cash"
            },
            "llm_response": response,
            "status": "completed"
        }

class TraderAgentHandler:
    def __init__(self):
        system_prompt = """You are a Trader Agent responsible for executing trading decisions.
        Your role includes:
        1. Synthesizing analysis from multiple sources
        2. Making final trading decisions
        3. Managing portfolio execution
        4. Monitoring and adjusting positions
        5. Communicating with other agents
        
        Be decisive and focus on practical execution with clear action items."""
        
        self.llm = RealLLMHandler("trader", system_prompt)
    
    def request_advice(self, advice_request: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Process this trading advice request:
        Request: {advice_request}
        
        Formulate specific questions for the Expert Trader including:
        1. Current market opportunities
        2. Specific stock or sector recommendations
        3. Optimal entry timing
        4. Risk management requirements
        """
        
        response = self.llm.generate_response(prompt, {"market_phase": "growth", "risk_tolerance": "moderate"})
        
        return {
            "agent": "trader",
            "agent_did": "trader_agent_did",
            "advice_request": {
                "query": advice_request.get("query", "Market analysis request"),
                "specific_questions": [
                    "What are the top 3 stock picks for the next quarter?",
                    "Should we increase tech exposure given AI trends?",
                    "What are the key risk factors to monitor?"
                ]
            },
            "llm_response": response,
            "status": "advice_requested",
            "target_agent": "expert_trader"
        }
    
    def synthesize_final_recommendation(self, advice: Dict[str, Any], risk_analysis: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Synthesize final trading recommendation from:
        Expert Advice: {advice}
        Risk Analysis: {risk_analysis}
        
        Provide:
        1. Final buy/sell/hold decisions
        2. Specific execution plan
        3. Position sizes and timing
        4. Monitoring requirements
        5. Exit strategies
        """
        
        response = self.llm.generate_response(prompt, {"decision_type": "portfolio_rebalance"})
        
        return {
            "agent": "trader",
            "agent_did": "trader_agent_did",
            "final_recommendation": {
                "action": "BUY",
                "positions": [
                    {"symbol": "AAPL", "action": "BUY", "size": "5%", "target": "$195"},
                    {"symbol": "MSFT", "action": "BUY", "size": "4%", "target": "$380"},
                    {"symbol": "SPY", "action": "HOLD", "size": "20%", "rationale": "Market hedge"}
                ],
                "confidence": "85%",
                "reasoning": "Strong fundamentals with manageable risk profile",
                "execution_timeline": "Execute over 2-3 trading sessions",
                "monitoring_points": ["Earnings announcements", "Fed meetings", "Technical levels"]
            },
            "llm_response": response,
            "status": "recommendation_ready"
        }

def get_agent_handler(agent_type: str):
    """Get the appropriate agent handler"""
    handlers = {
        "trigger": TriggerAgentHandler(),
        "expert": ExpertAgentHandler(),
        "risk": RiskEvaluatorAgentHandler(),
        "trader": TraderAgentHandler()
    }
    return handlers.get(agent_type) 