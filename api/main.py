from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import asyncio
import json
from datetime import datetime

from agents.ai_trading_agents import AITriggerAgent, AIExpertTraderAgent, AIRiskEvaluatorAgent
from main import AITradingSystem

app = FastAPI(title="AI Trading System API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize trading system
trading_system = None

class TradingRequest(BaseModel):
    goals: Dict[str, Any]
    constraints: Dict[str, Any]

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = WebSocketManager()

@app.on_event("startup")
async def startup_event():
    global trading_system
    trading_system = AITradingSystem()

@app.get("/")
async def root():
    return {"message": "AI Trading System API"}

@app.post("/api/trading/request")
async def create_trading_request(request: TradingRequest):
    try:
        result = await trading_system.process_trading_request(
            request.goals,
            request.constraints
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/trading")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                request_data = json.loads(data)
                request = TradingRequest(**request_data)
                
                # Process request and send updates
                async def process_and_broadcast():
                    try:
                        # Trigger Agent Analysis
                        await manager.broadcast(json.dumps({
                            "type": "status",
                            "agent": "trigger",
                            "message": "Analyzing market conditions...",
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                        
                        trigger_response = await trading_system.trigger_agent.process_message({
                            "type": "trading_request",
                            "goals": request.goals,
                            "constraints": request.constraints,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        
                        await manager.broadcast(json.dumps({
                            "type": "analysis",
                            "agent": "trigger",
                            "data": trigger_response,
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                        
                        # Expert Trader Strategy
                        await manager.broadcast(json.dumps({
                            "type": "status",
                            "agent": "expert",
                            "message": "Developing trading strategy...",
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                        
                        expert_response = await trading_system.expert_trader.process_message({
                            "type": "strategy_development",
                            "trigger_analysis": trigger_response["response"],
                            "goals": request.goals,
                            "constraints": request.constraints
                        })
                        
                        await manager.broadcast(json.dumps({
                            "type": "strategy",
                            "agent": "expert",
                            "data": expert_response,
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                        
                        # Risk Evaluation
                        await manager.broadcast(json.dumps({
                            "type": "status",
                            "agent": "risk",
                            "message": "Evaluating risks...",
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                        
                        risk_response = await trading_system.risk_evaluator.evaluate_strategy(
                            strategy=expert_response["response"],
                            market_conditions=trigger_response["response"]
                        )
                        
                        await manager.broadcast(json.dumps({
                            "type": "risk",
                            "agent": "risk",
                            "data": risk_response,
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                        
                        # Final Decision
                        await manager.broadcast(json.dumps({
                            "type": "status",
                            "agent": "expert",
                            "message": "Making final decision...",
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                        
                        final_decision = await trading_system.expert_trader.process_message({
                            "type": "execution_decision",
                            "strategy": expert_response["response"],
                            "risk_evaluation": risk_response["response"]
                        })
                        
                        await manager.broadcast(json.dumps({
                            "type": "decision",
                            "agent": "expert",
                            "data": final_decision,
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                        
                    except Exception as e:
                        await manager.broadcast(json.dumps({
                            "type": "error",
                            "message": str(e),
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                
                # Start processing in background
                asyncio.create_task(process_and_broadcast())
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }))
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 