"""
Risk Agent module for evaluating trading risks
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from .base_agent import BaseAgent, AgentMessage
from backend.agent_registry import agent_registry, AgentRole
from backend.did_registry import did_registry
import os
from agents.trading_tools import RiskAssessmentTool
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskAgent(BaseAgent):
    """Risk agent for evaluating trading risks"""
    
    def __init__(self, did: str):
        """Initialize the risk agent with a DID"""
        super().__init__(did=did, name="RiskEvaluator")
        logger.info(f"Initialized Risk Agent with DID: {did}")
        self.max_risk_level = float(os.getenv('MAX_RISK_LEVEL', 0.7))
        self.risk_tool = RiskAssessmentTool()
    
    async def verify_agent(self, ask_id: str, did: str, token: str, public_key: str, algorithm: str = 'ES256K') -> Dict[str, Any]:
        """Verify another agent's DID/JWT."""
        try:
            logger.info(f"[RiskAgent] Verifying agent: did={did}, token={token[:10]}..., public_key={public_key[:10] if public_key else 'None'}...")
            
            # Normalize DID format for registry lookup
            normalized_did = did.replace('did:ethr:', 'did:eth:')
            
            # Get actual public key from registry if DID was provided
            if public_key.startswith('did:'):
                sender_normalized_did = public_key.replace('did:ethr:', 'did:eth:')
                actual_public_key = did_registry.get(sender_normalized_did)
                if not actual_public_key:
                    logger.error(f"[RiskAgent] No public key found for DID: {public_key}")
                    return {"verified": False, "message": "No public key found for DID"}
                public_key = actual_public_key
            
            # Verify token with public key
            try:
                verified_data = await self.verify_token(token, public_key, algorithm=algorithm)
                logger.info(f"[RiskAgent] Token verified successfully: {verified_data}")
                
                # Check if token DID matches provided DID
                token_did = verified_data.get('sub')  # JWT subject is the DID
                if token_did != did:
                    logger.error(f"[RiskAgent] Token DID mismatch: token_did={token_did}, provided_did={did}")
                    return {"verified": False, "message": "Token DID mismatch"}
                
                # Store verification state
                if self.redis_client:
                    self.redis_client.setex(f"session:{ask_id}:{normalized_did}", 3600, "1")  # 1 hour expiry
                else:
                    if ask_id not in self.verified_sessions:
                        self.verified_sessions[ask_id] = {}
                    self.verified_sessions[ask_id][normalized_did] = True
                
                return {"verified": True, "data": verified_data}
                
            except Exception as e:
                logger.error(f"[RiskAgent] Token verification failed: {str(e)}")
                return {"verified": False, "message": str(e)}
                
        except Exception as e:
            logger.error(f"[RiskAgent] Agent verification failed: {str(e)}")
            return {"verified": False, "message": str(e)}
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming messages and evaluate trading risks. Requires ask_id for session tracking."""
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
                verification_result = await self.verify_agent(ask_id, sender_did, sender_token, sender_public_key, algorithm='ES256K')
                if not verification_result.get("verified", False):
                    return {
                        'status': 'error',
                        'message': 'DID/JWT verification failed'
                    }
            
            if message.get('type') == 'risk_evaluation_request':
                try:
                    # Get actual public key from registry if DID was provided
                    if sender_public_key.startswith('did:'):
                        normalized_did = sender_public_key.replace('did:ethr:', 'did:eth:')
                        actual_public_key = did_registry.get(normalized_did)
                        if not actual_public_key:
                            return {
                                'status': 'error',
                                'message': 'No public key found for sender DID'
                            }
                        sender_public_key = actual_public_key
                    
                    # Verify token and extract data
                    verified_data = await self.verify_token(sender_token, sender_public_key, algorithm='ES256K')
                    if not verified_data:
                        return {
                            'status': 'error',
                            'message': 'Token verification failed'
                        }
                    
                    # Debug: Log what we received
                    logger.info(f"[RiskAgent] Verified data keys: {list(verified_data.keys())}")
                    logger.info(f"[RiskAgent] Trading analysis type: {type(verified_data.get('trading_analysis'))}")
                    logger.info(f"[RiskAgent] Market conditions type: {type(verified_data.get('market_conditions'))}")
                    
                    # Extract data with fallbacks
                    trading_analysis = verified_data.get('trading_analysis', {})
                    market_conditions = verified_data.get('market_conditions', {})
                    
                    # If trading_analysis is empty, try to get it from the message directly
                    if not trading_analysis and 'trading_analysis' in message:
                        trading_analysis = message['trading_analysis']
                        logger.info(f"[RiskAgent] Using trading_analysis from message")
                    
                    # If market_conditions is empty, try to get it from the message directly
                    if not market_conditions and 'market_conditions' in message:
                        market_conditions = message['market_conditions']
                        logger.info(f"[RiskAgent] Using market_conditions from message")
                    
                    # Evaluate risk
                    evaluation = await self._evaluate_risk(trading_analysis, market_conditions)
                    
                    # End session after ask is complete
                    self.end_ask(ask_id)
                    
                    # Get my credentials for the response
                    credentials = self.get_credentials()
                    
                    # Create response token
                    response_token = await self.create_token(
                        recipient_did=sender_did,  # This is the orchestrator's DID
                        message_type="risk_evaluation",
                        payload={
                            "evaluation": evaluation,
                            "ask_id": ask_id
                        }
                    )
                    
                    # Get orchestrator's public key from the registry using the orchestrator's DID
                    # The sender_did is the orchestrator's DID since it's sending the request
                    orchestrator_public_key = did_registry.get(sender_did)
                    
                    if not orchestrator_public_key:
                        logger.error(f"[RiskAgent] No public key found for orchestrator DID: {sender_did}")
                        return {
                            'status': 'error',
                            'message': 'Orchestrator public key not found'
                        }
                    
                    return {
                        'status': 'success',
                        'message': 'Risk evaluation completed',
                        'evaluation': evaluation,
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
    
    async def _evaluate_risk(self, trading_analysis: Dict[str, Any], market_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the risk of a trading request using the enhanced risk assessment tool"""
        try:
            # COMPREHENSIVE LOGGING: Log the risk agent processing
            print("=" * 80)
            print("⚠️ RISK AGENT: EVALUATING RISK")
            print("=" * 80)
            print(f"Trading Analysis: {json.dumps(trading_analysis, indent=2)}")
            print(f"Market Conditions: {json.dumps(market_conditions, indent=2)}")
            
            # Handle case where inputs might be None or empty
            if not trading_analysis:
                trading_analysis = {}
            if not market_conditions:
                market_conditions = {}
            
            logger.info(f"[RiskAgent] _evaluate_risk called with:")
            logger.info(f"[RiskAgent] trading_analysis keys: {list(trading_analysis.keys()) if isinstance(trading_analysis, dict) else 'not a dict'}")
            logger.info(f"[RiskAgent] market_conditions keys: {list(market_conditions.keys()) if isinstance(market_conditions, dict) else 'not a dict'}")
            
            # Extract assets from multiple possible locations in the trading analysis
            assets = []
            
            # Try to get assets from strategy
            strategy = trading_analysis.get('strategy', {})
            if isinstance(strategy, dict):
                strategy_assets = strategy.get('assets', [])
                if strategy_assets:
                    assets = strategy_assets
            
            # If no assets in strategy, try market analysis
            if not assets:
                market_analysis = trading_analysis.get('market_analysis', {})
                if isinstance(market_analysis, dict):
                    assets = list(market_analysis.keys())
            
            # If still no assets, try goals
            if not assets:
                goals = trading_analysis.get('goals', {})
                if isinstance(goals, dict):
                    goals_assets = goals.get('assets', [])
                    if goals_assets:
                        assets = goals_assets
            
            # Ensure assets is a list
            if not isinstance(assets, list):
                if isinstance(assets, str):
                    assets = [assets]
                else:
                    assets = []
            
            print(f"Extracted Assets: {assets}")
            
            # Create strategy with extracted assets
            strategy_for_risk = {
                "assets": assets,
                "position_size": strategy.get('position_size', 0.1) if isinstance(strategy, dict) else 0.1,
                "stop_loss": strategy.get('stop_loss', 0.05) if isinstance(strategy, dict) else 0.05,
                "take_profit": strategy.get('take_profit', 0.1) if isinstance(strategy, dict) else 0.1
            }
            
            print(f"Strategy for Risk Assessment: {json.dumps(strategy_for_risk, indent=2)}")
            print("=" * 80)
            
            logger.info(f"[RiskAgent] Extracted assets: {assets}")
            logger.info(f"[RiskAgent] Strategy for risk assessment: {strategy_for_risk}")
            
            # COMPREHENSIVE LOGGING: Log risk tool call
            print("=" * 80)
            print("⚠️ RISK AGENT: CALLING RISK TOOL")
            print("=" * 80)
            print(f"Calling risk tool with strategy: {json.dumps(strategy_for_risk, indent=2)}")
            print(f"Market conditions: {json.dumps(market_conditions, indent=2)}")
            print("=" * 80)
            
            # Call the risk assessment tool with the extracted assets
            risk_assessment_json = await self.risk_tool._arun(strategy_for_risk, market_conditions)
            
            # COMPREHENSIVE LOGGING: Log risk tool response
            print("=" * 80)
            print("⚠️ RISK AGENT: RISK TOOL RESPONSE")
            print("=" * 80)
            print(f"Risk Assessment JSON: {risk_assessment_json}")
            print("=" * 80)
            
            # Parse the risk assessment
            try:
                risk_assessment = json.loads(risk_assessment_json)
            except Exception as e:
                logger.error(f"[RiskAgent] Error parsing risk assessment JSON: {e}")
                risk_assessment = {"error": str(e)}
            
            # COMPREHENSIVE LOGGING: Log final risk assessment
            print("=" * 80)
            print("⚠️ RISK AGENT: FINAL RISK ASSESSMENT")
            print("=" * 80)
            print(f"Final Risk Assessment: {json.dumps(risk_assessment, indent=2)}")
            print("=" * 80)
            
            evaluation = {
                "risk_assessment": risk_assessment,
                "strategy_used": strategy_for_risk,
                "timestamp": datetime.utcnow().isoformat()
            }
            return evaluation
            
        except Exception as e:
            logger.error(f"[RiskAgent] Error in _evaluate_risk: {str(e)}")
            print(f"❌ RISK AGENT ERROR: {str(e)}")
            return {
                "risk_assessment": {
                    "error": str(e),
                    "fallback_analysis": "Risk assessment failed, using default values"
                },
                "strategy_used": {
                    "assets": ["BTC", "ETH"],
                    "position_size": 0.1,
                    "stop_loss": 0.05,
                    "take_profit": 0.1
                },
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _calculate_risk_metrics(self, trading_analysis: Dict[str, Any], market_conditions: Dict[str, Any]) -> Dict[str, float]:
        """Calculate various risk metrics for the trading proposal."""
        # Implement risk metrics calculation
        return {
            'volatility': 0.2,
            'market_risk': 0.3,
            'liquidity_risk': 0.1,
            'credit_risk': 0.15
        }
    
    def _calculate_risk_score(self, risk_metrics: Dict[str, float]) -> float:
        """Calculate overall risk score from individual metrics."""
        # Implement risk score calculation
        weights = {
            'volatility': 0.3,
            'market_risk': 0.3,
            'liquidity_risk': 0.2,
            'credit_risk': 0.2
        }
        
        score = sum(risk_metrics[k] * weights[k] for k in weights)
        return min(score, 1.0)  # Normalize to [0, 1]
    
    def _generate_recommendations(self, risk_metrics: Dict[str, float], risk_score: float) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []
        
        if risk_score > self.max_risk_level:
            recommendations.append("Risk level exceeds maximum threshold")
        
        if risk_metrics['volatility'] > 0.3:
            recommendations.append("High volatility detected - consider hedging")
            
        if risk_metrics['liquidity_risk'] > 0.2:
            recommendations.append("Liquidity risk high - ensure sufficient market depth")
            
        return recommendations

# Initialize risk agent with normalized DID
risk_agent = RiskAgent(did="did:eth:0x18c6bcb1A1342254F491e1f69620eb7fEC57E0a6")

# Export the class and instance
__all__ = ['RiskAgent', 'risk_agent'] 