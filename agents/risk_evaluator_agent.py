from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import numpy as np
from .base_agent import BaseAgent, AgentMessage
import logging
import json

logger = logging.getLogger(__name__)

class RiskEvaluatorAgent(BaseAgent):
    """Risk evaluation agent that assesses trading risks and constraints"""
    
    def __init__(self, did: str):
        """Initialize the risk evaluator agent"""
        super().__init__(did=did, name="RiskEvaluator")
        logger.info(f"Initialized risk evaluator agent with DID: {did}")
        self.max_risk_level = float(os.getenv('MAX_RISK_LEVEL', 0.7))
        
    async def handle_message(self, message: AgentMessage) -> Dict[str, Any]:
        """Handle incoming messages"""
        try:
            logger.info(f"[Risk] Received message: {json.dumps(message.to_dict(), indent=2)}")
            
            # Verify sender
            if not await self.verify_agent(message.sender_did, message.token):
                logger.error(f"[Risk] Sender verification failed for {message.sender_did}")
                return {
                    "status": "error",
                    "message": "Sender verification failed"
                }
            
            # Process based on message type
            if message.message_type == "risk_evaluation_request":
                return await self.process_trading_request(message.content)
            else:
                logger.error(f"[Risk] Unknown message type: {message.message_type}")
                return {
                    "status": "error",
                    "message": f"Unknown message type: {message.message_type}"
                }
                
        except Exception as e:
            logger.error(f"[Risk] Error handling message: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def process_trading_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a trading request and provide risk evaluation"""
        try:
            logger.info(f"[Risk] Processing risk evaluation request: {json.dumps(request, indent=2)}")
            
            # Extract analysis and constraints
            trading_analysis = request.get("trading_analysis", {})
            constraints = request.get("constraints", {})
            
            # Perform risk evaluation
            evaluation = await self._evaluate_risk(trading_analysis, constraints)
            
            # Create response
            response = {
                "status": "success",
                "evaluation": evaluation,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"[Risk] Risk evaluation complete: {json.dumps(response, indent=2)}")
            return response
            
        except Exception as e:
            logger.error(f"[Risk] Error processing risk evaluation: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _evaluate_risk(self, trading_analysis: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate trading risks and constraints"""
        try:
            # Extract relevant information
            market_conditions = trading_analysis.get("market_conditions", {})
            risk_factors = trading_analysis.get("risk_factors", [])
            
            # TODO: Implement actual risk evaluation logic
            # For now, return a mock evaluation
            evaluation = {
                "risk_level": "MODERATE",
                "risk_score": 0.65,
                "constraints_met": True,
                "risk_factors": {
                    "market_volatility": {
                        "level": "MEDIUM",
                        "impact": "MODERATE",
                        "mitigation": "Use limit orders and position sizing"
                    },
                    "liquidity": {
                        "level": "LOW",
                        "impact": "HIGH",
                        "mitigation": "Consider smaller position sizes"
                    },
                    "price_impact": {
                        "level": "MEDIUM",
                        "impact": "MODERATE",
                        "mitigation": "Split orders over time"
                    }
                },
                "recommendations": [
                    "Use limit orders to manage price impact",
                    "Implement position sizing based on risk tolerance",
                    "Monitor market conditions for volatility changes"
                ]
            }
            
            logger.info(f"[Risk] Risk evaluation: {json.dumps(evaluation, indent=2)}")
            return evaluation
            
        except Exception as e:
            logger.error(f"[Risk] Error evaluating risk: {str(e)}", exc_info=True)
            raise

    async def verify_agent(self, ask_id: str, did: str, token: str, public_key: str, algorithm: str = 'ES256K') -> Dict[str, Any]:
        """Verify another agent's DID/JWT."""
        try:
            logger.info(f"[RiskAgent] Verifying agent: did={did}, token={token[:10]}..., public_key={public_key[:10] if public_key else 'None'}...")
            
            # Verify token with provided public key
            try:
                verified_data = await self.verify_token(token, public_key, algorithm=algorithm)
                logger.info(f"[RiskAgent] Token verified successfully: {json.dumps(verified_data, indent=2)}")
                
                # Check if token DID matches provided DID
                token_did = verified_data.get('did')
                if token_did != did:
                    logger.error(f"[RiskAgent] Token DID mismatch: token_did={token_did}, provided_did={did}")
                    return {"verified": False, "message": "Token DID mismatch"}
                
                # Store verification state
                if self.redis_client:
                    self.redis_client.setex(f"session:{ask_id}:{did}", 3600, "1")  # 1 hour expiry
                else:
                    if ask_id not in self.verified_sessions:
                        self.verified_sessions[ask_id] = {}
                    self.verified_sessions[ask_id][did] = True
                
                return {"verified": True, "data": verified_data}
                
            except Exception as e:
                logger.error(f"[RiskAgent] Token verification failed: {str(e)}")
                return {"verified": False, "message": str(e)}
                
        except Exception as e:
            logger.error(f"[RiskAgent] Agent verification failed: {str(e)}")
            return {"verified": False, "message": str(e)}

    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming messages and evaluate trading risks. Requires ask_id for session tracking."""
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
                verified_data = await self.verify_token(sender_token, sender_public_key, algorithm='ES256K')
                if not self._verify_credentials(verified_data.get('credentials')):
                    return {
                        'status': 'error',
                        'message': 'Invalid credentials'
                    }
                risk_evaluation = await self._evaluate_risk(
                    verified_data.get('trading_analysis', {}),
                    verified_data.get('market_conditions', {})
                )
                # End session after ask is complete
                self.end_ask(ask_id)
                # Always include this agent's public key in the response
                my_normalized_did = self.did.replace('did:ethr:', 'did:eth:')
                my_public_key = did_registry.get(my_normalized_did)
                return {
                    'status': 'success',
                    'message': 'Risk evaluation completed',
                    'evaluation': risk_evaluation,
                    'credentials': self.get_credentials(),
                    'public_key': my_public_key
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
    
    def _verify_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Verify the credentials of the expert trader agent."""
        # Implement credential verification logic
        return True  # Placeholder
    
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