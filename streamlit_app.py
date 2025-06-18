import streamlit as st
import requests
import json
import sys
import os
import uuid
import time
from backend.eth_account_utils import generate_eth_account
from backend.eth_jwt_utils import generate_test_jwt_ethereum
from eth_account import Account
from eth_keys import keys
from backend.database import (
    store_account, get_account, get_all_accounts, get_registered_accounts,
    update_registration_status, store_chat_message,
    get_chat_history
)
from backend.did_utils import generate_did, register_did
from typing import Optional, Dict, Any
import datetime
from backend.debug_utils import (
    DebugManager, 
    setup_debug_mode, 
    toggle_debug_mode, 
    get_debug_manager
)
import asyncio

# (Optional) Set REDIS_URL if you want persistent session state
# os.environ["REDIS_URL"] = "redis://localhost:6379/0"

# Backend API endpoint (FastAPI)
BACKEND_URL = "http://localhost:8000"

# Initialize debug mode
setup_debug_mode()

# Add debug mode toggle in the sidebar
with st.sidebar:
    st.title("🔧 Debug Controls")
    if st.button("Toggle Debug Mode"):
        toggle_debug_mode()
    st.write("Debug Mode:", "🟢 On" if st.session_state.debug_mode else "🔴 Off")
    
    # Debug: Show current registration status
    st.write("**Debug - Registration Status:**")
    if "registration_status" in st.session_state:
        for agent, status in st.session_state.registration_status.items():
            st.write(f"{agent}: {status}")
    else:
        st.write("No registration status found")
    
    # Debug: Show agent accounts
    st.write("**Debug - Agent Accounts:**")
    if "agent_accounts" in st.session_state:
        for agent, account in st.session_state.agent_accounts.items():
            st.write(f"{agent}: {account.get('did', 'No DID')[:20]}...")
    else:
        st.write("No agent accounts found")

def wait_for_backend(max_retries=5, retry_delay=2):
    """Wait for backend server to be ready"""
    for i in range(max_retries):
        try:
            response = requests.get(f"{BACKEND_URL}/")
            if response.status_code == 200:
                st.success("Backend server is ready!")
                return True
        except requests.exceptions.ConnectionError:
            if i < max_retries - 1:
                st.warning(f"Waiting for backend server... (attempt {i+1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                st.error("Could not connect to backend server. Please make sure it's running.")
                return False
    return False

# Wait for backend to be ready
if not wait_for_backend():
    st.stop()

# Initialize session state for UI state only
if "onboarding_step" not in st.session_state:
    st.session_state.onboarding_step = 1
if "expert_verified" not in st.session_state:
    st.session_state.expert_verified = False
if "trading_results" not in st.session_state:
    st.session_state.trading_results = None
if "show_results" not in st.session_state:
    st.session_state.show_results = False

# Load accounts from database
def load_accounts():
    """Load all agent accounts from the database."""
    accounts = get_registered_accounts()
    st.session_state.agent_accounts = accounts
    st.session_state.registration_status = {
        agent_type: account.get('is_registered', False)
        for agent_type, account in accounts.items()
    }

# Load accounts on startup
load_accounts()

def generate_and_register_did(agent_type: str):
    """Generate and store a new DID for an agent."""
    try:
        # Generate new DID
        account = generate_did()
        if not account:
            st.error("Failed to generate DID")
            return None
        
        # Store in database
        if store_account(agent_type, account):
            # Update session state
            st.session_state.agent_accounts[agent_type] = account
            st.session_state.registration_status[agent_type] = False
            st.rerun()
            return account
        else:
            st.error("Failed to store account in database")
            return None
    except Exception as e:
        st.error(f"Error generating DID: {e}")
        return None

def register_agent_did(agent_type: str, account: dict) -> bool:
    """Register an agent's DID and update its status."""
    try:
        if register_did(account["did"], account["public_key"], agent_type):
            # Update registration status in database
            if update_registration_status(agent_type, True):
                # Update session state
                st.session_state.registration_status[agent_type] = True
                st.rerun()
                return True
        return False
    except Exception as e:
        st.error(f"Error registering DID: {e}")
        return False

def register_did(did, public_key, agent_name):
    """Register a DID with the backend"""
    payload = {"did": did, "public_key": public_key}
    resp = requests.post(f"{BACKEND_URL}/did/register", json=payload)
    if resp.status_code == 200:
        st.success(f"Registered DID: {did}")
        st.session_state.registration_status[agent_name] = True
        return True
    else:
        st.error(f"Failed to register DID {did}: {resp.text}")
        return False

def verify_agent_did(agent_type: str, did: str, jwt: str) -> bool:
    """Verify an agent's DID and JWT with another agent."""
    try:
        # Get the verifying agent's account
        verifying_agent = st.session_state.agent_accounts.get(agent_type)
        if not verifying_agent:
            st.error(f"{agent_type} account not found")
            return False

        # Generate JWT for the verifying agent
        verifying_jwt = generate_test_jwt_ethereum(
            did=verifying_agent["did"],
            private_key=verifying_agent["private_key"],
            additional_claims={"role": agent_type, "type": "verification"}
        )

        # Send verification request to backend
        verification_data = {
            "verifier_did": verifying_agent["did"],
            "verifier_jwt": verifying_jwt,
            "target_did": did,
            "target_jwt": jwt
        }

        response = requests.post(
            f"{BACKEND_URL}/verify-agent",
            json=verification_data
        )

        return response.status_code == 200
    except Exception as e:
        st.error(f"Error verifying agent: {e}")
        return False

def display_trading_analysis(analysis_data):
    """Display the trading analysis results in a flexible format"""
    if not analysis_data:
        st.warning("No analysis data available")
        return
    
    # Debug: Show the structure of analysis_data
    st.write("**Debug - Analysis Data Structure:**")
    st.json(analysis_data)
    
    st.subheader("Trading Analysis Results")
    
    # Display status and message - handle various formats
    status = analysis_data.get("status", "unknown")
    message = analysis_data.get("message", "No message available")
    
    status_color = "green" if status == "success" else "red"
    st.markdown(f"**Status:** :{status_color}[{status}]")
    st.markdown(f"**Message:** {message}")

    # Display step-by-step messages if present
    step_messages = analysis_data.get("messages", [])
    if step_messages:
        st.subheader("Process Steps")
        for step in step_messages:
            step_label = step.get("step", "Step")
            step_msg = step.get("message", "")
            st.info(f"**{step_label}**: {step_msg}")
    
    # The main analysis data is in the "analysis" field from the backend
    analysis = analysis_data.get("analysis", {})
    
    if not analysis:
        # If no structured analysis found, display the entire response
        st.info("No structured analysis found - displaying raw response")
        st.json(analysis_data)
        return
    
    # Create tabs for different aspects of the analysis
    tab1, tab2, tab3, tab4 = st.tabs(["Analysis Overview", "Market Data", "Risk Assessment", "Raw Data"])
    
    with tab1:
        st.markdown("### Analysis Overview")
        
        # Handle different analysis formats
        if isinstance(analysis, dict):
            # Look for common analysis fields
            if "expert_analysis" in analysis:
                expert = analysis["expert_analysis"]
                st.markdown("#### Expert Analysis")
                if isinstance(expert, dict):
                    for key, value in expert.items():
                        if isinstance(value, (dict, list)):
                            st.markdown(f"**{key.replace('_', ' ').title()}:**")
                            st.json(value)
                        else:
                            st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
                else:
                    st.markdown(f"**Expert Analysis:** {expert}")
            
            # Display any recommendations
            if "recommendations" in analysis:
                st.markdown("#### Recommendations")
                recs = analysis["recommendations"]
                if isinstance(recs, list):
                    for i, rec in enumerate(recs, 1):
                        if isinstance(rec, dict):
                            st.markdown(f"**Recommendation {i}:**")
                            for key, value in rec.items():
                                st.markdown(f"- {key.replace('_', ' ').title()}: {value}")
                        else:
                            st.markdown(f"**Recommendation {i}:** {rec}")
                        st.markdown("---")
                else:
                    st.markdown(f"**Recommendations:** {recs}")
            
            # Display any strategy information
            if "strategy" in analysis:
                st.markdown("#### Strategy")
                strategy = analysis["strategy"]
                if isinstance(strategy, dict):
                    for key, value in strategy.items():
                        st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
                else:
                    st.markdown(f"**Strategy:** {strategy}")
        else:
            st.markdown(f"**Analysis:** {analysis}")
    
    with tab2:
        st.markdown("### Market Data")
        
        # Look for market analysis data in various formats
        market_data = None
        if isinstance(analysis, dict):
            if "market_analysis" in analysis:
                market_data = analysis["market_analysis"]
            elif "market_data" in analysis:
                market_data = analysis["market_data"]
            elif "BTC" in analysis or "ETH" in analysis:
                # Direct asset data
                market_data = analysis
        
        if market_data:
            if isinstance(market_data, dict):
                for asset, data in market_data.items():
                    if isinstance(data, dict):
                        st.markdown(f"#### {asset}")
                        
                        # Current price
                        if "current_price" in data:
                            st.metric("Current Price", f"${data['current_price']:.2f}")
                        
                        # Statistical metrics
                        if "statistical_metrics" in data:
                            metrics = data["statistical_metrics"]
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Mean Return", f"{metrics.get('mean_return', 0):.4f}")
                            with col2:
                                st.metric("Volatility", f"{metrics.get('volatility', 0):.4f}")
                            with col3:
                                st.metric("VaR (95%)", f"{metrics.get('var_95', 0):.4f}")
                        
                        # Trend analysis
                        if "trend_analysis" in data:
                            trend = data["trend_analysis"]
                            st.markdown("**Trend Analysis:**")
                            st.markdown(f"- Direction: {trend.get('trend_direction', 'Unknown')}")
                            st.markdown(f"- SMA 20: ${trend.get('sma_20', 0):.2f}")
                            st.markdown(f"- SMA 50: ${trend.get('sma_50', 0):.2f}")
                        
                        # Technical indicators
                        if "technical_indicators" in data:
                            tech = data["technical_indicators"]
                            st.markdown("**Technical Indicators:**")
                            st.markdown(f"- RSI: {tech.get('rsi', 0):.2f}")
                            st.markdown(f"- MACD: {tech.get('macd', 0):.4f}")
                        
                        # Recommendations
                        if "recommendations" in data:
                            st.markdown("**Recommendations:**")
                            for rec in data["recommendations"]:
                                st.info(f"• {rec}")
                        
                        st.markdown("---")
                    else:
                        st.markdown(f"**{asset}:** {data}")
            else:
                st.markdown(f"**Market Data:** {market_data}")
        else:
            st.info("No market data available")
    
    with tab3:
        st.markdown("### Risk Assessment")
        
        # Look for risk assessment data in the correct location
        risk_data = None
        if isinstance(analysis, dict):
            if "risk_evaluation" in analysis:
                risk_evaluation = analysis["risk_evaluation"]
                if isinstance(risk_evaluation, dict) and "risk_assessment" in risk_evaluation:
                    risk_data = risk_evaluation["risk_assessment"]
            elif "risk_assessment" in analysis:
                risk_data = analysis["risk_assessment"]
            elif "risk_metrics" in analysis:
                risk_data = analysis["risk_metrics"]
        
        if risk_data:
            if isinstance(risk_data, dict):
                # Check if this is per-asset risk assessment (new format)
                if any(key in risk_data for key in ["BTC", "ETH", "AAPL", "MSFT"]):
                    st.markdown("#### Per-Asset Risk Assessment")
                    
                    for asset, asset_risk in risk_data.items():
                        if isinstance(asset_risk, dict):
                            st.markdown(f"**{asset}**")
                            
                            # Risk metrics
                            if "risk_metrics" in asset_risk:
                                metrics = asset_risk["risk_metrics"]
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Volatility", f"{metrics.get('volatility', 0):.4f}")
                                    st.metric("VaR (95%)", f"{metrics.get('var_95', 0):.4f}")
                                with col2:
                                    st.metric("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.4f}")
                                    st.metric("Sortino Ratio", f"{metrics.get('sortino_ratio', 0):.4f}")
                                with col3:
                                    st.metric("Market Correlation", f"{metrics.get('market_correlation', 0):.4f}")
                                    st.metric("Expected Shortfall", f"{metrics.get('expected_shortfall', 0):.4f}")
                            
                            # Position risk
                            if "position_risk" in asset_risk:
                                pos_risk = asset_risk["position_risk"]
                                st.markdown("**Position Risk:**")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Position Value", f"${pos_risk.get('position_value', 0):.2f}")
                                with col2:
                                    st.metric("Max Loss", f"${pos_risk.get('max_loss', 0):.2f}")
                                with col3:
                                    st.metric("Risk/Reward", f"{pos_risk.get('risk_reward_ratio', 0):.2f}")
                            
                            # Overall risk assessment
                            if "risk_assessment" in asset_risk:
                                overall = asset_risk["risk_assessment"]
                                st.markdown("**Overall Assessment:**")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Risk Score", f"{overall.get('overall_risk', 0):.4f}")
                                with col2:
                                    risk_level = overall.get('risk_level', 'Unknown')
                                    color = "red" if risk_level == "high" else "orange" if risk_level == "moderate" else "green"
                                    st.markdown(f"**Risk Level:** :{color}[{risk_level.upper()}]")
                                
                                # Recommendations
                                if "recommendations" in overall:
                                    st.markdown("**Recommendations:**")
                                    for rec in overall["recommendations"]:
                                        st.info(f"• {rec}")
                            
                            st.markdown("---")
                
                else:
                    # Legacy format - single risk assessment
                    # Risk metrics
                    if "risk_metrics" in risk_data:
                        metrics = risk_data["risk_metrics"]
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Volatility", f"{metrics.get('volatility', 0):.4f}")
                            st.metric("Market Risk", f"{metrics.get('market_risk', 0):.4f}")
                        with col2:
                            st.metric("Liquidity Risk", f"{metrics.get('liquidity_risk', 0):.4f}")
                            st.metric("Credit Risk", f"{metrics.get('credit_risk', 0):.4f}")
                    
                    # Overall risk assessment
                    st.markdown("#### Overall Assessment")
                    st.markdown(f"**Risk Score:** {risk_data.get('risk_score', 'Not available')}")
                    st.markdown(f"**Risk Level:** {risk_data.get('risk_level', 'Not available')}")
                    
                    # Risk recommendations
                    if "recommendations" in risk_data:
                        st.markdown("#### Risk Recommendations")
                        for rec in risk_data["recommendations"]:
                            st.info(f"• {rec}")
            else:
                st.markdown(f"**Risk Assessment:** {risk_data}")
        else:
            st.info("No risk assessment data available")
    
    with tab4:
        st.markdown("### Raw Data")
        st.json(analysis)

def trigger_trading_request(session_id, goals, constraints, human_trader):
    """Trigger a trading request and handle the response"""
    debug_manager = get_debug_manager(session_id)
    
    try:
        # Use admin credentials for the request (since we're testing)
        admin_did = "did:eth:0xb061c3e5D0d182c6743c743fC14eDD4fdbD5c127"
        admin_private_key = "4bf0e53a3e05c778577287fec2b19c9f29dbe0856885e07dfcef2f80bc1d9ac1"
        
        # Generate JWT for the admin (acting as human trader)
        admin_jwt = generate_test_jwt_ethereum(
            did=admin_did,
            private_key=admin_private_key,
            additional_claims={"role": "human_trader", "type": "trading_request"}
        )
        
        # Prepare the request payload
        request_payload = {
            "session_id": str(session_id),
            "request": {
                "goals": dict(goals) if goals else {},
                "constraints": dict(constraints) if constraints else {},
                "expert_agent_did": "did:eth:0x9d3C85DDe576481b16d3d78a9fb5eb393f94cfd5",
                "risk_agent_did": "did:eth:0x836f41d73cADE7a0dDeEF983c0e790467D2155DD",
                "timestamp": str(datetime.datetime.now()),
                "status": "pending"
            },
            "verification": {
                "did": admin_did,
                "jwt": admin_jwt
            }
        }
        
        # Log the request
        debug_manager.log_request("/trading/process", request_payload)
        
        # Make the API request
        response = requests.post(
            f"{BACKEND_URL}/trading/process",
            json=request_payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Prepare response data for logging
        response_data = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.json() if response.ok else response.text
        }
        
        # Log the response
        debug_manager.log_response("/trading/process", response.status_code, response_data)
        
        # Handle the response
        if response.status_code == 200:
            result = response.json()
            debug_manager.log_agent_action("system", "info", {"message": "Trading analysis completed successfully"})
            
            # Debug: Print the result
            st.write("**Debug - Backend Response:**")
            st.json(result)
            
            return result
        else:
            error = Exception(f"Error {response.status_code}: {response.text}")
            debug_manager.log_error("trading_request", error, {"response": response.text})
            st.error(str(error))
            return None
            
    except Exception as e:
        debug_manager.log_error("trading_request", e, {"goals": goals, "constraints": constraints})
        st.error(f"Error initiating trading request: {str(e)}")
        return None

def expert_trader_process(session_id: str, request_data: dict) -> Optional[dict]:
    """Expert trader analyzes the request with DID verification."""
    try:
        # Get expert agent account
        expert_agent = st.session_state.agent_accounts.get("expert_agent")
        if not expert_agent:
            st.error("Expert agent account not found")
            return None

        # Verify human trader's DID
        if not verify_agent_did("expert_agent", request_data["did"], request_data["jwt"]):
            st.error("Failed to verify human trader's DID")
            return None

        # Generate JWT for expert agent
        expert_jwt = generate_test_jwt_ethereum(
            did=expert_agent["did"],
            private_key=expert_agent["private_key"],
            additional_claims={"role": "expert_agent", "type": "analysis"}
        )

        # Prepare analysis request
        analysis_data = {
            "session_id": session_id,
            "request_data": request_data,
            "did": expert_agent["did"],
            "jwt": expert_jwt
        }

        # Send request to backend
        response = requests.post(
            f"{BACKEND_URL}/expert-analysis",
            json=analysis_data
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Expert analysis failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error in expert analysis: {e}")
        return None

def risk_evaluator_process(session_id: str, analysis_data: dict) -> Optional[dict]:
    """Risk evaluator assesses the strategy with DID verification."""
    try:
        # Get risk agent account
        risk_agent = st.session_state.agent_accounts.get("risk_agent")
        if not risk_agent:
            st.error("Risk agent account not found")
            return None

        # Verify expert agent's DID
        if not verify_agent_did("risk_agent", analysis_data["did"], analysis_data["jwt"]):
            st.error("Failed to verify expert agent's DID")
            return None

        # Generate JWT for risk agent
        risk_jwt = generate_test_jwt_ethereum(
            did=risk_agent["did"],
            private_key=risk_agent["private_key"],
            additional_claims={"role": "risk_agent", "type": "evaluation"}
        )

        # Prepare risk evaluation request
        risk_data = {
            "session_id": session_id,
            "analysis_data": analysis_data,
            "did": risk_agent["did"],
            "jwt": risk_jwt
        }

        # Send request to backend
        response = requests.post(
            f"{BACKEND_URL}/risk-evaluation",
            json=risk_data
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Risk evaluation failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error in risk evaluation: {e}")
        return None

def trading_advice_process(session_id: str, risk_data: dict) -> Optional[dict]:
    """Trader agent provides final advice with DID verification."""
    try:
        # Get trader agent account
        trader_agent = st.session_state.agent_accounts.get("trader_agent")
        if not trader_agent:
            st.error("Trader agent account not found")
            return None

        # Verify risk agent's DID
        if not verify_agent_did("trader_agent", risk_data["did"], risk_data["jwt"]):
            st.error("Failed to verify risk agent's DID")
            return None

        # Generate JWT for trader agent
        trader_jwt = generate_test_jwt_ethereum(
            did=trader_agent["did"],
            private_key=trader_agent["private_key"],
            additional_claims={"role": "trader_agent", "type": "advice"}
        )

        # Prepare final advice request
        advice_data = {
            "session_id": session_id,
            "risk_data": risk_data,
            "did": trader_agent["did"],
            "jwt": trader_jwt
        }

        # Send request to backend
        response = requests.post(
            f"{BACKEND_URL}/trading-advice",
            json=advice_data
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Trading advice generation failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error generating trading advice: {e}")
        return None

def display_account_info(account_type, account):
    """Helper function to display account information safely"""
    if account:
        st.code(f"""
        DID: {account['did']}
        Address: {account['address']}
        Public Key: {account['public_key']}
        """)
    else:
        st.info(f"No DID registered for {account_type.replace('_', ' ').title()}")

def validate_json_input(json_str: str, field_name: str) -> Optional[Dict[str, Any]]:
    """Validate and parse JSON input with proper error handling."""
    if not json_str or not isinstance(json_str, str):
        st.error(f"{field_name} must be a non-empty string")
        return None
        
    try:
        # First try to parse the JSON
        parsed = json.loads(json_str.strip())
        
        # Ensure it's a dictionary
        if not isinstance(parsed, dict):
            st.error(f"{field_name} must be a JSON object (dictionary)")
            return None
            
        return parsed
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON in {field_name}: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error processing {field_name}: {str(e)}")
        return None

def process_trading_request(goals: str, constraints: str, ask_id: str, account: Dict[str, Any]) -> bool:
    """
    Process a trading request by validating inputs and triggering the request.
    
    Args:
        goals (str): JSON string containing trading goals
        constraints (str): JSON string containing trading constraints
        ask_id (str): Unique identifier for the trading request
        account (Dict[str, Any]): Account information for the human trader
        
    Returns:
        bool: True if request was successful, False otherwise
    """
    try:
        # Validate JSON inputs
        goals_dict = validate_json_input(goals, "Trading Goals")
        constraints_dict = validate_json_input(constraints, "Trading Constraints")
        
        if goals_dict is None or constraints_dict is None:
            st.error("Invalid JSON format in goals or constraints")
            return False
            
        # Check required fields
        required_goal_fields = ["goal", "timeframe"]
        required_constraint_fields = ["max_risk"]
        
        missing_goal_fields = [field for field in required_goal_fields if field not in goals_dict]
        missing_constraint_fields = [field for field in required_constraint_fields if field not in constraints_dict]
        
        if missing_goal_fields:
            st.error(f"Missing required fields in goals: {', '.join(missing_goal_fields)}")
            return False
            
        if missing_constraint_fields:
            st.error(f"Missing required fields in constraints: {', '.join(missing_constraint_fields)}")
            return False
        
        # Trigger the trading request
        trigger_resp = trigger_trading_request(ask_id, goals_dict, constraints_dict, account)
        
        if trigger_resp and trigger_resp.get("status") == "success":
            st.success("Trading request sent successfully!")
            
            # Use the backend response directly
            st.session_state.trading_results = trigger_resp
            st.session_state.show_results = True
            
            # Store the session for chat history
            st.session_state.current_session = ask_id
            
            return True
        else:
            error_msg = trigger_resp.get("message", "Unknown error") if trigger_resp else "Failed to get response"
            st.error(f"Error sending trading request: {error_msg}")
            return False
            
    except Exception as e:
        st.error(f"Error processing trading request: {str(e)}")
        return False

# Main UI
st.title("AI Trading System")
st.markdown("""
This is an AI-powered trading system that uses multiple specialized agents to analyze and execute trades.
Each agent has a unique DID (Decentralized Identifier) for secure communication and verification.
""")

# Define onboarding steps
ONBOARDING_STEPS = {
    1: "Register as Human Trader",
    2: "Set up Trading Account",
    3: "Get Verified by Expert Agent",
    4: "Enable Expert Chat",
    5: "Integrate Risk Agent"
}

TOTAL_STEPS = len(ONBOARDING_STEPS)

# Display onboarding progress
st.header("🤖 AI Trading System Onboarding")
st.markdown("""
    Follow these steps to set up your AI trading system:
    1. Register as a Human Trader
    2. Set up your Trading Account
    3. Get verified by the Expert Agent
    4. Enable Expert Chat functionality
    5. Integrate the Risk Agent
""")

# Calculate progress
completed_steps = sum(1 for step in range(1, st.session_state.onboarding_step) 
                     if st.session_state.registration_status.get(
                         "human_trader" if step == 1 else
                         "trader_agent" if step == 2 else
                         "expert_agent" if step == 3 else
                         "risk_agent" if step == 4 else None
                     ))

# Display progress bar
if TOTAL_STEPS > 0:
    progress = completed_steps / TOTAL_STEPS
    st.progress(progress)
    st.write(f"Step {st.session_state.onboarding_step} of {TOTAL_STEPS}: {ONBOARDING_STEPS[st.session_state.onboarding_step]}")

# Display current step
current_step = st.session_state.onboarding_step
if current_step in ONBOARDING_STEPS:
    st.subheader(f"Step {current_step}: {ONBOARDING_STEPS[current_step]}")
    
    # Step 1: Human Trader Registration
    if current_step == 1:
        with st.expander("Human Trader Registration", expanded=True):
            agent_type = "human_trader"
            account = st.session_state.agent_accounts.get(agent_type)
            
            if account:
                st.write("**Current Status:**")
                st.write(f"- DID: {account['did']}")
                st.write(f"- Address: {account['address']}")
                
                if not st.session_state.registration_status.get(agent_type):
                    if st.button("Register Human Trader DID", key="register_human_trader"):
                        if register_agent_did(agent_type, account):
                            st.success("DID registered successfully!")
                            st.session_state.onboarding_step = 2
                            st.rerun()
            else:
                if st.button("Generate Human Trader DID", key="generate_human_trader"):
                    new_account = generate_and_register_did(agent_type)
                    if new_account:
                        st.success("New DID generated successfully!")
                        st.rerun()
    
    # Step 2: Trading Account Setup
    elif current_step == 2:
        with st.expander("Trading Account Setup", expanded=True):
            agent_type = "trader_agent"
            account = st.session_state.agent_accounts.get(agent_type)
            
            if account:
                st.write("**Current Status:**")
                st.write(f"- DID: {account['did']}")
                st.write(f"- Address: {account['address']}")
                
                if not st.session_state.registration_status.get(agent_type):
                    if st.button("Register Trading Account DID", key="register_trader_agent"):
                        if register_agent_did(agent_type, account):
                            st.success("DID registered successfully!")
                            st.session_state.onboarding_step = 3
                            st.rerun()
            else:
                if st.button("Generate Trading Account DID", key="generate_trader_agent"):
                    new_account = generate_and_register_did(agent_type)
                    if new_account:
                        st.success("New DID generated successfully!")
                        st.rerun()
    
    # Step 3: Expert Agent Verification
    elif current_step == 3:
        with st.expander("Expert Agent Verification", expanded=True):
            agent_type = "expert_agent"
            account = st.session_state.agent_accounts.get(agent_type)
            
            if account:
                st.write("**Current Status:**")
                st.write(f"- DID: {account['did']}")
                st.write(f"- Address: {account['address']}")
                
                if not st.session_state.registration_status.get(agent_type):
                    if st.button("Register Expert Agent DID", key="register_expert_agent"):
                        if register_agent_did(agent_type, account):
                            st.success("DID registered successfully!")
                            st.session_state.onboarding_step = 4
                            st.rerun()
            else:
                if st.button("Generate Expert Agent DID", key="generate_expert_agent"):
                    new_account = generate_and_register_did(agent_type)
                    if new_account:
                        st.success("New DID generated successfully!")
                        st.rerun()
    
    # Step 4: Risk Agent Integration
    elif current_step == 4:
        with st.expander("Risk Agent Integration", expanded=True):
            agent_type = "risk_agent"
            account = st.session_state.agent_accounts.get(agent_type)
            
            if account:
                st.write("**Current Status:**")
                st.write(f"- DID: {account['did']}")
                st.write(f"- Address: {account['address']}")
                
                if not st.session_state.registration_status.get(agent_type):
                    if st.button("Register Risk Agent DID", key="register_risk_agent"):
                        if register_agent_did(agent_type, account):
                            st.success("DID registered successfully!")
                            st.session_state.onboarding_step = 5
                            st.rerun()
            else:
                if st.button("Generate Risk Agent DID", key="generate_risk_agent"):
                    new_account = generate_and_register_did(agent_type)
                    if new_account:
                        st.success("New DID generated successfully!")
                        st.rerun()
    
    # Step 5: System Ready
    elif current_step == 5:
        st.success("🎉 All agents are registered and the system is ready!")
        st.info("You can now use the AI trading system with all agents integrated.")

# Trading System UI (only show if all agents are registered and verified)
if all(st.session_state.registration_status.values()) and st.session_state.expert_verified:
    st.markdown("---")
    st.title("Trading System")
    st.success("All agents are registered, verified, and ready to trade!")
    
    # Get agent accounts using the new naming convention
    HUMAN_TRADER_ACCOUNT = st.session_state.agent_accounts.get("human_trader")
    TRADER_AGENT_ACCOUNT = st.session_state.agent_accounts.get("trader_agent")
    EXPERT_AGENT_ACCOUNT = st.session_state.agent_accounts.get("expert_agent")
    RISK_AGENT_ACCOUNT = st.session_state.agent_accounts.get("risk_agent")
    
    # Verify all accounts are present
    if not all([HUMAN_TRADER_ACCOUNT, TRADER_AGENT_ACCOUNT, EXPERT_AGENT_ACCOUNT, RISK_AGENT_ACCOUNT]):
        st.error("Some agent accounts are missing. Please complete the onboarding process.")
        st.stop()
    
    # Trading request section
    st.header("🤖 AI Trading System")
    
    # Chat sections - only show if agents are registered
    # Temporarily allow testing even if not all agents are registered
    if True:  # all_agents_registered():  # Temporarily bypass registration check
        # Demo: Simulate a TriggerAgent → ExpertTraderAgent → RiskEvaluatorAgent workflow
        st.header("🤖 AI Agent Workflows")

        # Default values with proper JSON formatting
        default_goals = {
            "goal": "maximize profit",
            "timeframe": "1d",
            "target_return": 0.05,
            "risk_tolerance": "moderate",
            "trading_pairs": ["BTC/USD", "ETH/USD"],
            "strategy_type": "momentum"
        }
        
        default_constraints = {
            "max_risk": 0.5,
            "max_position_size": 0.1,
            "max_drawdown": 0.15,
            "min_liquidity": 1000000,
            "max_slippage": 0.01,
            "min_volume": 100000
        }

        goals = st.text_area(
            "Trading Goals (JSON)",
            value=json.dumps(default_goals, indent=2),
            help="Enter your trading goals in JSON format. Example: {'goal': 'maximize profit', 'timeframe': '1d'}"
        )
        
        constraints = st.text_area(
            "Trading Constraints (JSON)",
            value=json.dumps(default_constraints, indent=2),
            help="Enter your trading constraints in JSON format. Example: {'max_risk': 0.5, 'max_position_size': 0.1}"
        )

        # Chat workflow buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎯 Start AI Trading Analysis", key="start_trading_analysis_chat"):
                ask_id = str(uuid.uuid4())
                st.write(f"🆔 Session ID: {ask_id}")
                
                # Check if HUMAN_TRADER_ACCOUNT is available
                if HUMAN_TRADER_ACCOUNT is None:
                    st.error("❌ Human Trader account not found. Please register a Human Trader account first.")
                else:
                    if process_trading_request(goals, constraints, ask_id, HUMAN_TRADER_ACCOUNT):
                        st.rerun()

    # Display chat history for current session
    if "current_session" in st.session_state:
        st.header("💬 Agent Communication Log")
        display_chat_history(st.session_state.current_session)

# Use the persistent accounts with proper null checks
HUMAN_TRADER_ACCOUNT = st.session_state.agent_accounts.get("human_trader")
EXPERT_AGENT_ACCOUNT = st.session_state.agent_accounts.get("expert_agent")
RISK_AGENT_ACCOUNT = st.session_state.agent_accounts.get("risk_agent")
TRADER_AGENT_ACCOUNT = st.session_state.agent_accounts.get("trader_agent")

# Initialize agent information with null checks
HUMAN_TRADER_DID = HUMAN_TRADER_ACCOUNT["did"] if HUMAN_TRADER_ACCOUNT else None
HUMAN_TRADER_PUBLIC_KEY = HUMAN_TRADER_ACCOUNT["public_key"] if HUMAN_TRADER_ACCOUNT else None
HUMAN_TRADER_PRIVATE_KEY = HUMAN_TRADER_ACCOUNT["private_key"] if HUMAN_TRADER_ACCOUNT else None

EXPERT_AGENT_DID = EXPERT_AGENT_ACCOUNT["did"] if EXPERT_AGENT_ACCOUNT else None
EXPERT_AGENT_PUBLIC_KEY = EXPERT_AGENT_ACCOUNT["public_key"] if EXPERT_AGENT_ACCOUNT else None
EXPERT_AGENT_PRIVATE_KEY = EXPERT_AGENT_ACCOUNT["private_key"] if EXPERT_AGENT_ACCOUNT else None

RISK_AGENT_DID = RISK_AGENT_ACCOUNT["did"] if RISK_AGENT_ACCOUNT else None
RISK_AGENT_PUBLIC_KEY = RISK_AGENT_ACCOUNT["public_key"] if RISK_AGENT_ACCOUNT else None
RISK_AGENT_PRIVATE_KEY = RISK_AGENT_ACCOUNT["private_key"] if RISK_AGENT_ACCOUNT else None

TRADER_AGENT_DID = TRADER_AGENT_ACCOUNT["did"] if TRADER_AGENT_ACCOUNT else None
TRADER_AGENT_PUBLIC_KEY = TRADER_AGENT_ACCOUNT["public_key"] if TRADER_AGENT_ACCOUNT else None
TRADER_AGENT_PRIVATE_KEY = TRADER_AGENT_ACCOUNT["private_key"] if TRADER_AGENT_ACCOUNT else None

# Check if all agents are registered
def all_agents_registered():
    # Debug: Show current registration status
    st.sidebar.write("**Debug - Registration Status:**")
    for agent, status in st.session_state.registration_status.items():
        st.sidebar.write(f"{agent}: {status}")
    
    # Check if all required agents are registered
    required_agents = ["human_trader", "expert_agent", "risk_agent", "trader_agent"]
    all_registered = all(st.session_state.registration_status.get(agent, False) for agent in required_agents)
    
    st.sidebar.write(f"**All Required Agents Registered:** {all_registered}")
    return all_registered

# Generate a JWT using Ethereum keys
def generate_jwt(did, private_key, additional_claims=None):
    return generate_test_jwt_ethereum(did, private_key, additional_claims)

# Streamlit UI
st.title("🤖 AI-Powered Multi-Agent Trading System")
st.caption("Real LLM agents with Ethereum DIDs for secure trading decisions")

# LLM Configuration section
with st.expander("🧠 LLM Configuration"):
    st.write("**Agent Intelligence:**")
    st.write("- 🎯 **Trigger Agent**: Analyzes trading goals and opportunities")
    st.write("- 🧠 **Expert Trader**: Provides detailed market analysis and strategies") 
    st.write("- ⚠️ **Risk Evaluator**: Assesses and optimizes risk profiles")
    st.write("- 💼 **Trader Agent**: Synthesizes recommendations and makes decisions")
    st.write("")
    st.write("**LLM Provider**: OpenAI GPT-3.5-turbo (with fallback to mock for demo)")
    st.write("**Authentication**: Ethereum DIDs with JWT verification")

# Display agent information
st.header("Agent Information")
with st.expander("View Agent DIDs and Addresses"):
    agents = [
        ("Human Trader", HUMAN_TRADER_ACCOUNT, st.session_state.registration_status.get("human_trader", False)),
        ("Expert Agent", EXPERT_AGENT_ACCOUNT, st.session_state.registration_status.get("expert_agent", False)),
        ("Risk Agent", RISK_AGENT_ACCOUNT, st.session_state.registration_status.get("risk_agent", False)),
        ("Trader Agent", TRADER_AGENT_ACCOUNT, st.session_state.registration_status.get("trader_agent", False))
    ]
    
    for name, account, is_registered in agents:
        status = "✅ Registered" if is_registered else "❌ Not Registered"
        st.write(f"**{name}:** {status}")
        if account:
            st.write(f"- DID: {account['did']}")
            st.write(f"- Address: {account['address']}")
        else:
            st.write("- No account registered")
        st.write("")

# Registration section
st.header("Agent Registration")
col1, col2 = st.columns(2)

with col1:
    if st.button("Register All Agent DIDs", key="register_all_agents"):
        if HUMAN_TRADER_ACCOUNT:
            st.session_state.registration_status["human_trader"] = register_agent_did("human_trader", HUMAN_TRADER_ACCOUNT)
        if EXPERT_AGENT_ACCOUNT:
            st.session_state.registration_status["expert_agent"] = register_agent_did("expert_agent", EXPERT_AGENT_ACCOUNT)
        if RISK_AGENT_ACCOUNT:
            st.session_state.registration_status["risk_agent"] = register_agent_did("risk_agent", RISK_AGENT_ACCOUNT)
        if TRADER_AGENT_ACCOUNT:
            st.session_state.registration_status["trader_agent"] = register_agent_did("trader_agent", TRADER_AGENT_ACCOUNT)
        st.rerun()

with col2:
    if all_agents_registered():
        st.success("🎉 All AI agents registered and ready!")
    else:
        st.warning("⚠️ Please register agents before testing AI chat")

# Chat sections - only show if agents are registered
# Temporarily allow testing even if not all agents are registered
if True:  # all_agents_registered():  # Temporarily bypass registration check
    # Demo: Simulate a TriggerAgent → ExpertTraderAgent → RiskEvaluatorAgent workflow
    st.header("🤖 AI Agent Workflows")

    # Default values with proper JSON formatting
    default_goals = {
        "goal": "maximize profit",
        "timeframe": "1d",
        "target_return": 0.05,
        "risk_tolerance": "moderate",
        "trading_pairs": ["BTC/USD", "ETH/USD"],
        "strategy_type": "momentum"
    }
    
    default_constraints = {
        "max_risk": 0.5,
        "max_position_size": 0.1,
        "max_drawdown": 0.15,
        "min_liquidity": 1000000,
        "max_slippage": 0.01,
        "min_volume": 100000
    }

    goals = st.text_area(
        "Trading Goals (JSON)",
        value=json.dumps(default_goals, indent=2),
        help="Enter your trading goals in JSON format. Example: {'goal': 'maximize profit', 'timeframe': '1d'}"
    )
    
    constraints = st.text_area(
        "Trading Constraints (JSON)",
        value=json.dumps(default_constraints, indent=2),
        help="Enter your trading constraints in JSON format. Example: {'max_risk': 0.5, 'max_position_size': 0.1}"
    )

    # Chat workflow buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎯 Start AI Trading Analysis", key="start_trading_analysis_chat"):
            ask_id = str(uuid.uuid4())
            st.write(f"🆔 Session ID: {ask_id}")
            
            # Check if HUMAN_TRADER_ACCOUNT is available
            if HUMAN_TRADER_ACCOUNT is None:
                st.error("❌ Human Trader account not found. Please register a Human Trader account first.")
            else:
                if process_trading_request(goals, constraints, ask_id, HUMAN_TRADER_ACCOUNT):
                    st.rerun()

    with col2:
        if st.button("💼 Request AI Trading Advice", key="request_trading_advice"):
            ask_id = str(uuid.uuid4())
            st.write(f"🆔 Session ID: {ask_id}")

            advice_request = {"query": "How do I optimize my trading strategy?"}
            
            # TraderAgent sends a trading advice request
            trader_resp = trading_advice_process(ask_id, advice_request)
            if trader_resp:
                st.session_state.chat_history.append({
                    "role": "💼 Trader AI", 
                    "content": f"**AI Advice Request**\n\n{json.dumps(trader_resp, indent=2)}"
                })
                st.rerun()

else:
    st.info("👆 Please register all AI agents first to enable intelligent chat functionality")

# Display trading results if available
if st.session_state.show_results and st.session_state.trading_results:
    st.markdown("---")
    st.header("📊 Trading Analysis Results")
    
    # Display the results
    display_trading_analysis(st.session_state.trading_results)
    
    # Add a button to clear results
    if st.button("Clear Results", key="clear_results"):
        st.session_state.show_results = False
        st.session_state.trading_results = None
        st.rerun()

st.info("🤖 **AI-Powered System**: This UI uses real LLM agents (OpenAI GPT-3.5-turbo) for intelligent trading analysis. Each agent has specialized knowledge and uses Ethereum DIDs with JWT verification for secure communication.")

# Registration buttons for individual agents
st.header("Individual Agent Registration")
for agent_name, agent_account, is_registered in [
    ("Human Trader", HUMAN_TRADER_ACCOUNT, st.session_state.registration_status.get("human_trader", False)),
    ("Expert Agent", EXPERT_AGENT_ACCOUNT, st.session_state.registration_status.get("expert_agent", False)),
    ("Risk Agent", RISK_AGENT_ACCOUNT, st.session_state.registration_status.get("risk_agent", False)),
    ("Trader Agent", TRADER_AGENT_ACCOUNT, st.session_state.registration_status.get("trader_agent", False))
]:
    agent_type = agent_name.lower().replace(" ", "_")
    with st.expander(f"{agent_name} Registration"):
        if agent_account:
            st.write(f"**Current Status:** {'✅ Registered' if is_registered else '❌ Not Registered'}")
            st.write(f"- DID: {agent_account['did']}")
            st.write(f"- Address: {agent_account['address']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Generate New DID for {agent_name}", key=f"generate_{agent_type}"):
                    new_account = generate_and_register_did(agent_type)
                    if new_account:
                        st.success("New DID generated successfully!")
                        st.rerun()
            
            with col2:
                if not is_registered:
                    if st.button(f"Register {agent_name} DID", key=f"register_{agent_type}"):
                        if register_agent_did(agent_type, agent_account):
                            st.success("DID registered successfully!")
                            st.rerun()
        else:
            st.info(f"No account registered for {agent_name}")
            if st.button(f"Generate DID for {agent_name}", key=f"generate_new_{agent_type}"):
                new_account = generate_and_register_did(agent_type)
                if new_account:
                    st.success("New DID generated successfully!")
                    st.rerun()

# Update the chat history handling
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# When storing chat messages
def store_chat_interaction(session_id: str, role: str, content: str):
    """Store a chat message and update the session state."""
    if store_chat_message(session_id, role, content):
        st.session_state.chat_history.append({
            "role": role,
            "content": content
        })
        st.rerun()

# When displaying chat history
def display_chat_history(session_id: str):
    """Display chat history for a session."""
    history = get_chat_history(session_id)
    for msg in history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"]) 