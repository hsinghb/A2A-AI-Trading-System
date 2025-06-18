"""
Expert Trader Agent module for analyzing trading requests
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from .base_agent import BaseAgent, AgentMessage
from backend.agent_registry import agent_registry, AgentRole
from backend.did_registry import did_registry
from agents.trading_tools import MarketAnalysisTool, RiskAssessmentTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExpertTraderAgent(BaseAgent):
    """Expert trader agent for analyzing trading requests"""
    
    def __init__(self, did: str):
        """Initialize the expert trader agent with a DID"""
        super().__init__(did=did, name="ExpertTrader")
        logger.info(f"Initialized Expert Trader Agent with DID: {did}")
        self.market_tool = MarketAnalysisTool()
        self.risk_tool = RiskAssessmentTool()
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming messages and analyze trading requests. Requires ask_id for session tracking."""
        try:
            ask_id = message.get('ask_id')
            sender_did = message.get('sender_did')
            sender_token = message.get('token')
            sender_public_key = message.get('public_key')
            
            if not ask_id or not sender_did or not sender_token or not sender_public_key:
                return {
                    'status': 'error',
                    'message': 'Missing ask_id, sender_did, token, or public_key'
                }
            
            # Verify sender for this ask/session
            if not self.is_verified(ask_id, sender_did):
                verification_result = await self.verify_agent(ask_id, sender_did, sender_token, sender_public_key)
                if not verification_result.get("verified", False):
                    return {
                        'status': 'error',
                        'message': verification_result.get("message", "DID/JWT verification failed")
                    }
            
            if message.get('type') == 'trading_request':
                try:
                    # Get the verified public key for this session
                    verified_public_key = self.get_verified_public_key(ask_id, sender_did)
                    if not verified_public_key:
                        return {
                            'status': 'error',
                            'message': 'No verified public key found for sender'
                        }
                    
                    # Verify token and extract trading request
                    verified_data = await self.verify_token(sender_token, verified_public_key)
                    if not verified_data:
                        return {
                            'status': 'error',
                            'message': 'Token verification failed'
                        }
                    
                    # Process the trading request
                    analysis = await self._analyze_trading_request(verified_data)
                    
                    # Create response token
                    response_token = await self.create_token(
                        recipient_did=sender_did,  # This is the orchestrator's DID
                        message_type="trading_analysis",
                        payload={
                            "analysis": analysis,
                            "ask_id": ask_id
                        }
                    )
                    
                    # End session after ask is complete
                    self.end_ask(ask_id)
                    
                    # Get my credentials for the response
                    credentials = self.get_credentials()
                    
                    # Get orchestrator's public key from the registry using the orchestrator's DID
                    # The sender_did is the orchestrator's DID since it's sending the request
                    orchestrator_public_key = did_registry.get(sender_did)
                    
                    if not orchestrator_public_key:
                        logger.error(f"[ExpertAgent] No public key found for orchestrator DID: {sender_did}")
                        return {
                            'status': 'error',
                            'message': 'Orchestrator public key not found'
                        }
                    
                    return {
                        'status': 'success',
                        'message': 'Trading analysis completed',
                        'analysis': analysis,
                        'credentials': credentials,
                        'token': response_token,
                        'public_key': orchestrator_public_key  # Include orchestrator's public key
                    }
                    
                except ValueError as e:
                    return {
                        'status': 'error',
                        'message': str(e)
                    }
            
            return {
                'status': 'error',
                'message': 'Invalid message type'
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def _analyze_trading_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a trading request and provide recommendations"""
        try:
            import json
            logger.info(f"[ExpertTraderAgent] Received request: {json.dumps(request, indent=2)}")
            
            # COMPREHENSIVE LOGGING: Log the expert agent processing
            print("=" * 80)
            print("🧠 EXPERT AGENT: ANALYZING TRADING REQUEST")
            print("=" * 80)
            print(f"Request: {json.dumps(request, indent=2)}")
            
            # Extract request details
            goals = request.get('goals', {})
            constraints = request.get('constraints', {})
            
            # Extract assets from multiple possible locations
            assets = []
            if isinstance(goals, dict):
                assets = goals.get('assets', [])
            if not assets and isinstance(constraints, dict):
                assets = constraints.get('allowed_assets', [])
            
            # Ensure assets is a list
            if not isinstance(assets, list):
                if isinstance(assets, str):
                    assets = [assets]
                else:
                    assets = []
            
            position_size = goals.get('position_size', 0.1) if isinstance(goals, dict) else 0.1
            stop_loss = constraints.get('stop_loss', 0.05) if isinstance(constraints, dict) else 0.05
            take_profit = constraints.get('take_profit', 0.1) if isinstance(constraints, dict) else 0.1
            
            print(f"Extracted Goals: {goals}")
            print(f"Extracted Constraints: {constraints}")
            print(f"Extracted Assets: {assets}")
            print(f"Position Size: {position_size}")
            print(f"Stop Loss: {stop_loss}")
            print(f"Take Profit: {take_profit}")
            print("=" * 80)
            
            logger.info(f"[ExpertTraderAgent] Extracted assets: {assets}")
            
            # Create strategy with user assets
            strategy = {
                "assets": assets,
                "position_size": position_size,
                "stop_loss": stop_loss,
                "take_profit": take_profit
            }
            
            # COMPREHENSIVE LOGGING: Log strategy creation
            print("=" * 80)
            print("🧠 EXPERT AGENT: CREATED STRATEGY")
            print("=" * 80)
            print(f"Strategy: {json.dumps(strategy, indent=2)}")
            print("=" * 80)
            
            # Get market analysis using user assets
            market_analysis = await self._get_market_analysis(strategy)
            
            # COMPREHENSIVE LOGGING: Log market analysis
            print("=" * 80)
            print("🧠 EXPERT AGENT: MARKET ANALYSIS RESULT")
            print("=" * 80)
            print(f"Market Analysis: {json.dumps(market_analysis, indent=2)}")
            print("=" * 80)
            
            # Create comprehensive analysis
            analysis = {
                "market_analysis": market_analysis,
                "strategy": strategy,
                "recommendations": self._generate_recommendations(strategy, market_analysis),
                "timestamp": datetime.now().isoformat()
            }
            
            # COMPREHENSIVE LOGGING: Log final analysis
            print("=" * 80)
            print("🧠 EXPERT AGENT: FINAL ANALYSIS")
            print("=" * 80)
            print(f"Final Analysis: {json.dumps(analysis, indent=2)}")
            print("=" * 80)
            
            return analysis
            
        except Exception as e:
            logger.error(f"[ExpertTraderAgent] Error in _analyze_trading_request: {str(e)}")
            print(f"❌ EXPERT AGENT ERROR: {str(e)}")
            raise

    async def _get_market_analysis(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Get market analysis using the market analysis tool"""
        try:
            assets = strategy.get('assets', [])
            if not assets:
                logger.warning("[ExpertTraderAgent] No assets provided for market analysis")
                return {}
            
            # Perform real market analysis
            market_analysis_json = await self.market_tool._arun(assets, "1d")
            market_analysis = None
            try:
                import json
                market_analysis = json.loads(market_analysis_json)
            except Exception as e:
                logger.error(f"[ExpertTraderAgent] Error parsing market analysis JSON: {e}")
                market_analysis = {"error": str(e)}
            
            return market_analysis
            
        except Exception as e:
            logger.error(f"[ExpertTraderAgent] Error in _get_market_analysis: {str(e)}")
            return {"error": str(e)}

    def _generate_recommendations(self, strategy: Dict[str, Any], market_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on strategy and market analysis"""
        try:
            recommendations = []
            
            for asset, analysis in (market_analysis or {}).items():
                if isinstance(analysis, dict) and analysis.get("recommendations"):
                    for rec in analysis["recommendations"]:
                        recommendations.append({
                            "asset": asset,
                            "recommendation": rec
                        })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"[ExpertTraderAgent] Error in _generate_recommendations: {str(e)}")
            return []

# Initialize expert agent with normalized DID
expert_agent = ExpertTraderAgent(did="did:eth:0x3990762F90777172Af4A203225EAb3e8813b8030")

# Export the class and instance
__all__ = ['ExpertTraderAgent', 'expert_agent'] 