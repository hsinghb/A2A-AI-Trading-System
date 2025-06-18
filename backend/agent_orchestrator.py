"""
Enhanced Agent Orchestrator module for coordinating trading agents with blockchain-based DID verification.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import logging
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import uuid
from eth_account import Account

from .blockchain.agent_registry import agent_registry
from .eth_jwt_utils import generate_test_jwt_ethereum, verify_jwt_with_ethereum_key
from .did_registry import did_registry
from agents.expert_trader_agent import ExpertTraderAgent
from agents.risk_agent import RiskAgent

load_dotenv()

class OrchestratorState(BaseModel):
    """State management for the orchestrator."""
    session_id: str
    human_trader_did: str
    request: Dict[str, Any]
    analysis_results: Optional[Dict[str, Any]] = None
    status: str = "pending"
    timestamp: str = datetime.now().isoformat()
    agent_status: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

class TradingAgentOrchestrator:
    """Enhanced orchestrator for coordinating trading agents with blockchain verification."""
    
    def __init__(self):
        """Initialize the orchestrator with admin credentials."""
        self.logger = logging.getLogger(__name__)
        
        # Load admin credentials
        self.admin_did = os.getenv("ADMIN_DID")
        self.admin_private_key = os.getenv("ADMIN_PRIVATE_KEY")
        
        if not self.admin_did or not self.admin_private_key:
            raise ValueError("Admin DID and private key are required for orchestrator initialization")
        
        # Verify admin status with fallback
        if self.admin_did.startswith("did:eth:"):
            admin_address = self.admin_did.replace("did:eth:", "")
        else:  # did:ethr:
            admin_address = self.admin_did.replace("did:ethr:", "")
        
        # Try to verify admin status, but don't fail if it doesn't work
        try:
            is_admin = agent_registry.is_admin(admin_address)
            if not is_admin:
                self.logger.warning(f"Address {admin_address} is not recognized as admin in contract")
                self.logger.warning("Continuing with local admin privileges - some blockchain features may be limited")
        except Exception as e:
            self.logger.warning(f"Could not verify admin status: {str(e)}")
            self.logger.warning("Continuing with local admin privileges - some blockchain features may be limited")
        
        # Initialize agents list with caching
        self.agents: Dict[str, Any] = {}
        self.agent_info_cache: Dict[str, Dict[str, Any]] = {}
        
        # Active sessions
        self.sessions: Dict[str, OrchestratorState] = {}
        
        # Pre-initialize known agents
        self._initialize_known_agents()
        
        self.logger.info("Successfully created new orchestrator instance")

    def _initialize_known_agents(self):
        """Pre-initialize known agents from the DID registry."""
        try:
            # Get expert agent info - using a DID that exists in the registry
            expert_did = "did:eth:0x9d3C85DDe576481b16d3d78a9fb5eb393f94cfd5"
            expert_public_key = did_registry.get(expert_did)
            if expert_public_key:
                self.agent_info_cache[expert_did] = {
                    "agent_address": expert_did.replace("did:eth:", ""),
                    "public_key": expert_public_key,
                    "reputation": 100,
                    "total_interactions": 0,
                    "successful_interactions": 0,
                    "last_updated": 0,
                    "is_active": True,
                    "metadata": {"type": "expert_trader"}
                }
                self.agents[expert_did] = ExpertTraderAgent(did=expert_did)
                self.logger.info(f"Pre-initialized expert agent: {expert_did}")
            
            # Get risk agent info - using a DID that exists in the registry
            risk_did = "did:eth:0x836f41d73cADE7a0dDeEF983c0e790467D2155DD"
            risk_public_key = did_registry.get(risk_did)
            if risk_public_key:
                self.agent_info_cache[risk_did] = {
                    "agent_address": risk_did.replace("did:eth:", ""),
                    "public_key": risk_public_key,
                    "reputation": 100,
                    "total_interactions": 0,
                    "successful_interactions": 0,
                    "last_updated": 0,
                    "is_active": True,
                    "metadata": {"type": "risk_evaluator"}
                }
                self.agents[risk_did] = RiskAgent(did=risk_did)
                self.logger.info(f"Pre-initialized risk agent: {risk_did}")
                
        except Exception as e:
            self.logger.warning(f"Error pre-initializing agents: {str(e)}")

    def get_admin_public_key(self) -> str:
        """Get the admin's public key from the private key."""
        try:
            account = Account.from_key(self.admin_private_key)
            return account.address
        except Exception as e:
            self.logger.error(f"Error getting admin public key: {str(e)}")
            # Fallback: return the address from DID
            return self.admin_did.replace("did:eth:", "").replace("did:ethr:", "")

    def get_agent_info(self, did: str) -> Dict[str, Any]:
        """Get agent information from cache or blockchain registry."""
        try:
            # Check cache first
            if did in self.agent_info_cache:
                return self.agent_info_cache[did]
            
            # Try blockchain registry
            try:
                agent_info = agent_registry.get_agent(did)
                self.agent_info_cache[did] = agent_info
                return agent_info
            except Exception as e:
                self.logger.warning(f"Failed to get agent info from blockchain for {did}: {str(e)}")
                
                # Fallback to DID registry
                public_key = did_registry.get(did)
                if public_key:
                    agent_info = {
                        "agent_address": did.replace("did:eth:", "").replace("did:ethr:", ""),
                        "public_key": public_key,
                        "reputation": 100,
                        "total_interactions": 0,
                        "successful_interactions": 0,
                        "last_updated": 0,
                        "is_active": True,
                        "metadata": {"type": "unknown", "source": "did_registry"}
                    }
                    self.agent_info_cache[did] = agent_info
                    return agent_info
                
                raise ValueError(f"Agent {did} not found in any registry")
                
        except Exception as e:
            self.logger.error(f"Failed to get agent info for {did}: {str(e)}")
            raise

    def initialize_agent(self, did: str, agent_type: str) -> None:
        """Initialize an agent instance based on its type."""
        try:
            # Check if already initialized
            if did in self.agents:
                self.logger.info(f"Agent {did} already initialized")
                return
            
            # Get agent info
            agent_info = self.get_agent_info(did)
            if not agent_info.get("is_active", True):
                raise ValueError(f"Agent {did} is not active")
            
            # Initialize based on type
            if agent_type == "expert":
                self.agents[did] = ExpertTraderAgent(did=did)
            elif agent_type == "risk":
                self.agents[did] = RiskAgent(did=did)
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")
            
            self.logger.info(f"Initialized {agent_type} agent with DID: {did}")
        except Exception as e:
            self.logger.error(f"Failed to initialize agent {did}: {str(e)}")
            raise

    async def create_token(self, recipient_did: str, message_type: str, payload: Dict[str, Any]) -> str:
        """Create a JWT token for agent communication."""
        try:
            token_payload = {
                "sub": self.admin_did,
                "aud": recipient_did,
                "iat": datetime.now().timestamp(),
                "exp": datetime.now().timestamp() + 3600,  # 1 hour expiry
                "type": message_type,
                "role": "orchestrator"
            }
            token_payload.update(payload)
            
            return generate_test_jwt_ethereum(
                did=self.admin_did,
                private_key=self.admin_private_key,
                additional_claims=token_payload
            )
        except Exception as e:
            self.logger.error(f"Error creating token: {str(e)}")
            raise

    async def verify_agent(self, did: str, token: str) -> Dict[str, Any]:
        """Verify an agent's identity using their DID and JWT."""
        try:
            agent_info = self.get_agent_info(did)
            if not agent_info.get("is_active", True):
                return {"verified": False, "message": f"Agent {did} is not active"}
            
            try:
                verified_data = verify_jwt_with_ethereum_key(
                    token,
                    did,
                    agent_info["public_key"]
                )
                return {"verified": True, "data": verified_data}
            except Exception as e:
                return {"verified": False, "message": str(e)}
        except Exception as e:
            return {"verified": False, "message": str(e)}

    async def process_trading_request(self, request: Dict[str, Any], verification: Dict[str, str]) -> Dict[str, Any]:
        """Process a trading request through the expert and risk agents."""
        try:
            session_id = str(uuid.uuid4())
            human_trader_did = verification.get('did')
            human_token = verification.get('jwt')
            
            # COMPREHENSIVE LOGGING: Log the orchestrator processing
            print("=" * 80)
            print("🎯 ORCHESTRATOR: PROCESSING TRADING REQUEST")
            print("=" * 80)
            print(f"Session ID: {session_id}")
            print(f"Human Trader DID: {human_trader_did}")
            print(f"Request: {json.dumps(request, indent=2)}")
            
            # Extract and log user assets
            goals = request.get("goals", {})
            constraints = request.get("constraints", {})
            user_assets = goals.get("assets", [])
            allowed_assets = constraints.get("allowed_assets", [])
            
            print(f"User Assets from Goals: {user_assets}")
            print(f"Allowed Assets from Constraints: {allowed_assets}")
            print("=" * 80)
            
            if not human_trader_did or not human_token:
                return {"status": "error", "message": "Missing trader DID or token"}
            
            # Verify human trader
            verification_result = await self.verify_agent(human_trader_did, human_token)
            if not verification_result.get("verified", False):
                return {"status": "error", "message": verification_result.get("message", "Trader verification failed")}
            
            # Initialize session state
            self.sessions[session_id] = OrchestratorState(
                session_id=session_id,
                human_trader_did=human_trader_did,
                request=request
            )
            
            # Get or initialize expert agent
            expert_did = request.get("expert_agent_did")
            if not expert_did:
                return {"status": "error", "message": "Expert agent DID not specified"}
            
            self.initialize_agent(expert_did, "expert")
            
            # Create token for expert agent
            expert_token = await self.create_token(
                recipient_did=expert_did,
                message_type="trading_request",
                payload={
                    "goals": request.get("goals", {}),
                    "constraints": request.get("constraints", {}),
                    "timestamp": datetime.now().isoformat(),
                    "ask_id": session_id
                }
            )
            
            # COMPREHENSIVE LOGGING: Log expert agent request
            print("=" * 80)
            print("🧠 ORCHESTRATOR: SENDING TO EXPERT AGENT")
            print("=" * 80)
            expert_request = {
                "type": "trading_request",
                "goals": request.get("goals", {}),
                "constraints": request.get("constraints", {}),
                "timestamp": datetime.now().isoformat(),
                "ask_id": session_id,
                "sender_did": self.admin_did,
                "token": expert_token,
                "public_key": self.admin_did
            }
            print(f"Expert Request: {json.dumps(expert_request, indent=2)}")
            print("=" * 80)
            
            # Process with expert agent
            expert_response = await self.agents[expert_did].process_message(expert_request)
            
            # COMPREHENSIVE LOGGING: Log expert agent response
            print("=" * 80)
            print("🧠 ORCHESTRATOR: EXPERT AGENT RESPONSE")
            print("=" * 80)
            print(f"Status: {expert_response.get('status')}")
            print(f"Message: {expert_response.get('message', 'No message')}")
            print(f"Analysis: {json.dumps(expert_response.get('analysis', {}), indent=2)}")
            print("=" * 80)
            
            if expert_response.get("status") != "success":
                return {"status": "error", "message": expert_response.get("message")}
            
            # Get or initialize risk agent
            risk_did = request.get("risk_agent_did")
            if not risk_did:
                return {"status": "error", "message": "Risk agent DID not specified"}
            
            self.initialize_agent(risk_did, "risk")
            
            # Create token for risk agent
            risk_token = await self.create_token(
                recipient_did=risk_did,
                message_type="risk_evaluation_request",
                payload={
                    "trading_analysis": expert_response.get("analysis", {}),
                    "market_conditions": expert_response.get("analysis", {}),  # Use analysis as market_conditions for now
                    "timestamp": datetime.now().isoformat(),
                    "ask_id": session_id
                }
            )
            
            # COMPREHENSIVE LOGGING: Log risk agent request
            print("=" * 80)
            print("⚠️ ORCHESTRATOR: SENDING TO RISK AGENT")
            print("=" * 80)
            risk_request = {
                "type": "risk_evaluation_request",
                "trading_analysis": expert_response.get("analysis", {}),
                "market_conditions": expert_response.get("analysis", {}),
                "timestamp": datetime.now().isoformat(),
                "ask_id": session_id,
                "sender_did": self.admin_did,
                "token": risk_token,
                "public_key": self.admin_did
            }
            print(f"Risk Request: {json.dumps(risk_request, indent=2)}")
            print("=" * 80)
            
            # Process with risk agent
            risk_response = await self.agents[risk_did].process_message(risk_request)
            
            # COMPREHENSIVE LOGGING: Log risk agent response
            print("=" * 80)
            print("⚠️ ORCHESTRATOR: RISK AGENT RESPONSE")
            print("=" * 80)
            print(f"Status: {risk_response.get('status')}")
            print(f"Message: {risk_response.get('message', 'No message')}")
            print(f"Evaluation: {json.dumps(risk_response.get('evaluation', {}), indent=2)}")
            print("=" * 80)
            
            # Check if risk response has evaluation data, even if status is not success
            risk_evaluation = {}
            if risk_response.get("status") == "success":
                risk_evaluation = risk_response.get("evaluation", {})
            elif risk_response.get("evaluation"):
                # If we have evaluation data even with error status, use it
                risk_evaluation = risk_response.get("evaluation", {})
                self.logger.warning(f"Risk agent returned error status but provided evaluation data: {risk_response.get('message', 'Unknown error')}")
            else:
                # Only return error if we have no evaluation data at all
                return {"status": "error", "message": risk_response.get("message", "Risk evaluation failed")}
            
            # Update session state
            self.sessions[session_id].analysis_results = {
                "expert_analysis": expert_response.get("analysis", {}),
                "risk_evaluation": risk_evaluation,
                "timestamp": datetime.now().isoformat()
            }
            self.sessions[session_id].status = "completed"
            
            # COMPREHENSIVE LOGGING: Log final result
            print("=" * 80)
            print("✅ ORCHESTRATOR: FINAL RESULT")
            print("=" * 80)
            final_result = {
                "status": "success",
                "session_id": session_id,
                "result": self.sessions[session_id].analysis_results,
                "timestamp": datetime.now().isoformat()
            }
            print(f"Final Result: {json.dumps(final_result, indent=2)}")
            print("=" * 80)
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"Error processing trading request: {str(e)}")
            # Always include any partial analysis results if available
            partial_results = {}
            if session_id in self.sessions and self.sessions[session_id].analysis_results:
                partial_results = self.sessions[session_id].analysis_results
            
            return {
                "status": "error",
                "message": str(e),
                "result": partial_results,
                "timestamp": datetime.now().isoformat()
            }

    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get the status of a trading session."""
        if session_id not in self.sessions:
            return {"status": "error", "message": "Session not found"}
        
        session = self.sessions[session_id]
        return {
            "status": "success",
            "session": session.dict()
        }

# Global orchestrator instance
_orchestrator = None

def get_orchestrator() -> TradingAgentOrchestrator:
    """Get or create the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TradingAgentOrchestrator()
    return _orchestrator 