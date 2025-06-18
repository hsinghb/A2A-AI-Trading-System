import os
from pathlib import Path

# Add project root to Python path in a more reliable way
project_root = Path(__file__).parent.parent
import sys
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
# Remove problematic import
# from main import AITradingSystem
from backend.eth_jwt_utils import verify_jwt_with_ethereum_key
from backend.llm_agent_handlers import get_agent_handler
from backend.agent_orchestrator import get_orchestrator
from backend.did_registry import did_registry
import logging
from dotenv import load_dotenv
from backend.blockchain.agent_registry import agent_registry
from datetime import datetime


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Trading System Backend",
    description="Backend API for the AI Trading System",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Remove local did_registry dictionary
# did_registry: Dict[str, str] = {}

load_dotenv()

class DIDRegisterRequest(BaseModel):
    did: str
    public_key: str

class DIDRegisterResponse(BaseModel):
    message: str
    did: str

class ChatRequest(BaseModel):
    ask_id: str
    sender_did: str
    token: str  # JWT signed with Ethereum private key
    public_key: str  # Ethereum public key (hex)
    type: str
    # Additional fields based on message type
    goals: Dict[str, Any] = None
    constraints: Dict[str, Any] = None
    trading_analysis: Dict[str, Any] = None
    market_conditions: Dict[str, Any] = None
    advice_request: Dict[str, Any] = None
    advice: Dict[str, Any] = None

class ChatResponse(BaseModel):
    message: str
    response: Dict[str, Any]

class TradingProcessRequest(BaseModel):
    session_id: str
    request: Dict[str, Any]
    verification: Dict[str, Any]  # Contains did, jwt, and optionally public_key

class AgentRegistrationRequest(BaseModel):
    did: str
    public_key: str
    metadata: dict = {}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "message": "AI Trading System Backend is running"}

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify backend functionality"""
    return {
        "status": "success",
        "message": "Backend is working correctly",
        "timestamp": datetime.now().isoformat(),
        "test_data": {
            "sample_market_data": {
                "BTC": {
                    "current_price": 45000.0,
                    "trend": "bullish",
                    "volatility": 0.025
                },
                "ETH": {
                    "current_price": 3000.0,
                    "trend": "neutral",
                    "volatility": 0.030
                }
            }
        }
    }

@app.post("/trading/process")
async def process_trading(request: TradingProcessRequest):
    """Process a trading request with DID verification and agent orchestration"""
    try:
        logger.info(f"Received trading request for session {request.session_id}")
        logger.debug(f"Request data: {request.dict()}")
        now_ts = datetime.utcnow().isoformat()
        
        # Verify the JWT first
        try:
            verify_jwt_with_ethereum_key(
                request.verification["jwt"],
                request.verification["did"],
                did_registry.get(request.verification["did"])
            )
            logger.info(f"JWT verification successful for DID: {request.verification['did']}")
        except Exception as e:
            logger.error(f"JWT verification failed: {str(e)}")
            return {
                "status": "error",
                "session_id": request.session_id,
                "analysis": {},
                "timestamp": now_ts,
                "message": f"JWT verification failed: {str(e)}"
            }
        
        # Get the orchestrator
        try:
            orchestrator = get_orchestrator()
            logger.info("Successfully initialized orchestrator")
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {str(e)}")
            return {
                "status": "error",
                "session_id": request.session_id,
                "analysis": {},
                "timestamp": now_ts,
                "message": f"Failed to initialize orchestrator: {str(e)}"
            }
        
        # Process the request through the agent orchestration system
        try:
            logger.info("Processing request through orchestrator")
            result = await orchestrator.process_trading_request(
                request=request.request,
                verification=request.verification
            )
            logger.info(f"Orchestrator response: {result}")
            
            if result.get("status") == "error":
                logger.error(f"Orchestrator returned error: {result.get('error', 'Unknown error')}")
                return {
                    "status": "error",
                    "session_id": request.session_id,
                    "analysis": {},
                    "timestamp": now_ts,
                    "message": f"Orchestrator error: {result.get('error', 'Unknown error')}"
                }
            
            return {
                "status": "success",
                "session_id": request.session_id,
                "analysis": result.get("result", {}),
                "timestamp": result.get("timestamp", now_ts),
                "message": "Trading analysis completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error during orchestration: {str(e)}")
            return {
                "status": "error",
                "session_id": request.session_id,
                "analysis": {},
                "timestamp": now_ts,
                "message": f"Error during orchestration: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"Unexpected error in process_trading: {str(e)}")
        now_ts = datetime.utcnow().isoformat()
        return {
            "status": "error",
            "session_id": getattr(request, 'session_id', None),
            "analysis": {},
            "timestamp": now_ts,
            "message": f"Unexpected error: {str(e)}"
        }

@app.post("/did/register", response_model=DIDRegisterResponse)
async def register_did(request: DIDRegisterRequest):
    # Use the imported did_registry singleton
    if did_registry.get(request.did):
        raise HTTPException(status_code=400, detail="DID already registered")
    
    # Register using the singleton instance
    if not did_registry.register(request.did, request.public_key):
        raise HTTPException(status_code=500, detail="Failed to register DID")
    
    return DIDRegisterResponse(
        message="DID registered successfully",
        did=request.did
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Check if DID is registered
    if request.sender_did not in did_registry:
        raise HTTPException(status_code=401, detail="DID not registered")
    
    # Get the registered public key for this DID
    registered_public_key = did_registry[request.sender_did]
    
    # Verify JWT using Ethereum key
    try:
        payload = verify_jwt_with_ethereum_key(
            request.token, 
            request.sender_did, 
            registered_public_key
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"JWT verification failed: {str(e)}")
    
    # Determine agent type from DID or message type
    agent_type = determine_agent_type(request.sender_did, request.type)
    
    # Get appropriate LLM handler
    handler = get_agent_handler(agent_type)
    if not handler:
        raise HTTPException(status_code=400, detail=f"Unknown agent type: {agent_type}")
    
    # Process the message using LLM
    try:
        if request.type == "trading_request" and agent_type == "trigger":
            response = handler.process_request(request.goals or {}, request.constraints or {})
        elif request.type == "trading_request" and agent_type == "expert":
            response = handler.process_trading_analysis(request.trading_analysis or {})
        elif request.type == "risk_evaluation_request" and agent_type == "risk":
            response = handler.evaluate_risk(request.trading_analysis or {})
        elif request.type == "advice_request" and agent_type == "trader":
            response = handler.request_advice(request.advice_request or {})
        elif request.type == "advice_response" and agent_type == "expert":
            response = handler.process_trading_analysis(request.advice or {})
        elif request.type == "optimize_advice" and agent_type == "risk":
            response = handler.evaluate_risk(request.advice or {})
        elif request.type == "receive_advice" and agent_type == "trader":
            response = handler.synthesize_final_recommendation(
                request.advice or {}, 
                {"risk_analysis": "Previous risk evaluation"}
            )
        else:
            # Fallback for unknown message types
            response = {
                "agent": agent_type,
                "message": f"Processed {request.type} message",
                "status": "processed",
                "llm_response": f"AI agent {agent_type} processed your request successfully."
            }
    except Exception as e:
        response = {
            "agent": agent_type,
            "error": str(e),
            "status": "error",
            "fallback_response": f"Agent {agent_type} encountered an issue but is still operational."
        }
    
    return ChatResponse(
        message="LLM-powered agent response generated",
        response=response
    )

def determine_agent_type(sender_did: str, message_type: str) -> str:
    """Determine agent type based on DID or message type"""
    # Simple mapping - in a real system, you might store this in the DID registry
    if "trigger" in sender_did.lower():
        return "trigger"
    elif "expert" in sender_did.lower():
        return "expert"
    elif "risk" in sender_did.lower():
        return "risk"
    elif "trader" in sender_did.lower():
        return "trader"
    
    # Fallback based on message type
    if message_type in ["trading_request"]:
        return "trigger"
    elif message_type in ["advice_request", "receive_advice"]:
        return "trader"
    elif message_type in ["advice_response"]:
        return "expert"
    elif message_type in ["risk_evaluation_request", "optimize_advice"]:
        return "risk"
    
    return "trader"  # Default fallback 

@app.post("/agent/register")
def register_agent(req: AgentRegistrationRequest):
    try:
        tx_hash = agent_registry.register_agent(
            did=req.did,
            public_key=req.public_key,
            metadata=req.metadata
        )
        return {"status": "success", "tx_hash": tx_hash}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/agent/reregister")
def reregister_agent(req: AgentRegistrationRequest):
    try:
        tx_hash = agent_registry.update_agent(
            did=req.did,
            public_key=req.public_key,
            metadata=req.metadata
        )
        return {"status": "success", "tx_hash": tx_hash}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 