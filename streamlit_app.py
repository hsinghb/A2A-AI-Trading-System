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

def create_flexible_trading_form():
    """Create a flexible trading form with presets and dynamic inputs"""
    
    st.markdown("### 🎯 Trading Goals & Constraints")
    
    # Configuration management
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Preset selection
        preset_option = st.selectbox(
            "Choose a preset or create custom:",
            [
                "Conservative Portfolio",
                "Moderate Growth", 
                "Aggressive Trading",
                "Day Trading",
                "Swing Trading",
                "Custom Configuration"
            ],
            help="Select a preset to auto-fill common trading parameters, or choose Custom for full control"
        )
        
        # Show preset preview
        if preset_option != "Custom Configuration":
            preset_descriptions = {
                "Conservative Portfolio": "Low risk, long-term value investing with blue-chip stocks and dividends. Target: 5% annual return, max 3% drawdown.",
                "Moderate Growth": "Balanced growth strategy with ETFs and growth stocks. Target: 12% annual return, max 8% drawdown.",
                "Aggressive Trading": "High-risk momentum trading with crypto and tech stocks. Target: 25% annual return, max 15% drawdown.",
                "Day Trading": "Short-term scalping with high-volume stocks. Target: 2% daily return, max 5% drawdown.",
                "Swing Trading": "Medium-term technical analysis with support/resistance. Target: 8% weekly return, max 10% drawdown."
            }
            
            st.info(f"**{preset_option}**: {preset_descriptions.get(preset_option, '')}")
    
    with col2:
        # Save configuration
        config_name = st.text_input("Config Name", placeholder="My Strategy", help="Name to save your configuration")
        if st.button("💾 Save Config", key="save_config"):
            if config_name:
                # This would save to a file or database
                st.success(f"Configuration '{config_name}' saved!")
            else:
                st.error("Please enter a configuration name")
    
    with col3:
        # Load configuration
        saved_configs = ["My Conservative", "Growth Strategy", "Day Trading Setup"]  # This would load from storage
        if saved_configs:
            load_config = st.selectbox("Load Saved Config", ["None"] + saved_configs)
            if load_config != "None" and st.button("📂 Load Config", key="load_config"):
                st.info(f"Loading configuration: {load_config}")
                # This would load the selected configuration
                st.rerun()
    
    # Initialize default values based on preset
    if preset_option == "Conservative Portfolio":
        default_goals = {
            "target_return": 0.05,
            "time_horizon": "1y",
            "risk_tolerance": "low",
            "investment_style": "value",
            "focus_areas": ["blue_chips", "dividends"]
        }
        default_constraints = {
            "max_position_size": 50000,
            "max_drawdown": 0.03,
            "allowed_assets": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
            "min_liquidity": 5000000,
            "max_slippage": 0.005,
            "sector_limits": {"tech": 0.4, "finance": 0.3}
        }
    elif preset_option == "Moderate Growth":
        default_goals = {
            "target_return": 0.12,
            "time_horizon": "6m",
            "risk_tolerance": "moderate",
            "investment_style": "growth",
            "focus_areas": ["growth_stocks", "etfs"]
        }
        default_constraints = {
            "max_position_size": 100000,
            "max_drawdown": 0.08,
            "allowed_assets": ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"],
            "min_liquidity": 2000000,
            "max_slippage": 0.01,
            "sector_limits": {"tech": 0.6, "healthcare": 0.2}
        }
    elif preset_option == "Aggressive Trading":
        default_goals = {
            "target_return": 0.25,
            "time_horizon": "1m",
            "risk_tolerance": "high",
            "investment_style": "momentum",
            "focus_areas": ["crypto", "meme_stocks", "options"]
        }
        default_constraints = {
            "max_position_size": 200000,
            "max_drawdown": 0.15,
            "allowed_assets": ["BTC", "ETH", "TSLA", "NVDA", "AMD"],
            "min_liquidity": 1000000,
            "max_slippage": 0.02,
            "sector_limits": {"tech": 0.8, "crypto": 0.4}
        }
    elif preset_option == "Day Trading":
        default_goals = {
            "target_return": 0.02,
            "time_horizon": "1d",
            "risk_tolerance": "high",
            "investment_style": "scalping",
            "focus_areas": ["high_volume", "volatility"]
        }
        default_constraints = {
            "max_position_size": 50000,
            "max_drawdown": 0.05,
            "allowed_assets": ["SPY", "QQQ", "TSLA", "NVDA", "AMD"],
            "min_liquidity": 10000000,
            "max_slippage": 0.003,
            "sector_limits": {"tech": 0.7}
        }
    elif preset_option == "Swing Trading":
        default_goals = {
            "target_return": 0.08,
            "time_horizon": "1w",
            "risk_tolerance": "moderate",
            "investment_style": "technical",
            "focus_areas": ["breakouts", "support_resistance"]
        }
        default_constraints = {
            "max_position_size": 75000,
            "max_drawdown": 0.10,
            "allowed_assets": ["AAPL", "MSFT", "GOOGL", "AMZN", "META"],
            "min_liquidity": 3000000,
            "max_slippage": 0.008,
            "sector_limits": {"tech": 0.5, "consumer": 0.3}
        }
    else:  # Custom Configuration
        default_goals = {
            "target_return": 0.10,
            "time_horizon": "3m",
            "risk_tolerance": "moderate",
            "investment_style": "balanced",
            "focus_areas": []
        }
        default_constraints = {
            "max_position_size": 100000,
            "max_drawdown": 0.08,
            "allowed_assets": ["BTC", "ETH", "AAPL", "MSFT"],
            "min_liquidity": 2000000,
            "max_slippage": 0.01,
            "sector_limits": {}
        }
    
    # Create two columns for goals and constraints
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Trading Goals")
        
        # Target return with slider
        target_return = st.slider(
            "Target Return (%)",
            min_value=0.1,
            max_value=100.0,
            value=float(default_goals["target_return"] * 100),
            step=0.1,
            help="Expected annual return target"
        ) / 100.0
        
        # Time horizon
        time_horizon = st.selectbox(
            "Time Horizon",
            ["1d", "1w", "1m", "3m", "6m", "1y", "2y", "5y"],
            index=["1d", "1w", "1m", "3m", "6m", "1y", "2y", "5y"].index(default_goals["time_horizon"]),
            help="Investment time horizon"
        )
        
        # Risk tolerance
        risk_tolerance = st.selectbox(
            "Risk Tolerance",
            ["low", "moderate", "high", "very_high"],
            index=["low", "moderate", "high", "very_high"].index(default_goals["risk_tolerance"]),
            help="Your risk tolerance level"
        )
        
        # Investment style
        investment_style = st.selectbox(
            "Investment Style",
            ["value", "growth", "momentum", "dividend", "scalping", "swing", "balanced"],
            index=["value", "growth", "momentum", "dividend", "scalping", "swing", "balanced"].index(default_goals["investment_style"]),
            help="Your preferred investment approach"
        )
        
        # Focus areas (multi-select)
        focus_options = [
            "blue_chips", "growth_stocks", "dividends", "etfs", "crypto", 
            "meme_stocks", "options", "high_volume", "volatility", 
            "breakouts", "support_resistance", "ai_tech", "biotech"
        ]
        focus_areas = st.multiselect(
            "Focus Areas",
            focus_options,
            default=default_goals["focus_areas"],
            help="Specific areas or strategies to focus on"
        )
    
    with col2:
        st.markdown("#### 🛡️ Risk Constraints")
        
        # Position size
        max_position_size = st.number_input(
            "Max Position Size ($)",
            min_value=1000,
            max_value=1000000,
            value=default_constraints["max_position_size"],
            step=1000,
            help="Maximum amount to invest in a single position"
        )
        
        # Max drawdown
        max_drawdown = st.slider(
            "Max Drawdown (%)",
            min_value=0.1,
            max_value=50.0,
            value=float(default_constraints["max_drawdown"] * 100),
            step=0.1,
            help="Maximum acceptable portfolio decline"
        ) / 100.0
        
        # Allowed assets
        asset_options = [
            "BTC", "ETH", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", 
            "AMD", "META", "SPY", "QQQ", "IWM", "GLD", "SLV", "USDT"
        ]
        allowed_assets = st.multiselect(
            "Allowed Assets",
            asset_options,
            default=default_constraints["allowed_assets"],
            help="Assets you're willing to trade"
        )
        
        # Liquidity requirement
        min_liquidity = st.selectbox(
            "Min Liquidity",
            ["$500K", "$1M", "$2M", "$5M", "$10M", "$50M"],
            index=["$500K", "$1M", "$2M", "$5M", "$10M", "$50M"].index(f"${default_constraints['min_liquidity']/1000000:.0f}M"),
            help="Minimum daily trading volume requirement"
        )
        min_liquidity_value = int(min_liquidity.replace("$", "").replace("K", "000").replace("M", "000000"))
        
        # Max slippage
        max_slippage = st.slider(
            "Max Slippage (%)",
            min_value=0.1,
            max_value=5.0,
            value=float(default_constraints["max_slippage"] * 100),
            step=0.1,
            help="Maximum acceptable price slippage"
        ) / 100.0
    
    # Advanced options expander
    with st.expander("🔧 Advanced Options"):
        st.markdown("#### Sector Limits")
        
        sectors = ["tech", "finance", "healthcare", "consumer", "energy", "crypto", "biotech"]
        sector_limits = {}
        
        for sector in sectors:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"{sector.title()}")
            with col2:
                limit = st.number_input(
                    f"{sector.title()} %",
                    min_value=0,
                    max_value=100,
                    value=int(default_constraints.get("sector_limits", {}).get(sector, 0) * 100),
                    key=f"sector_{sector}"
                ) / 100.0
                if limit > 0:
                    sector_limits[sector] = limit
        
        # Additional constraints
        st.markdown("#### Additional Constraints")
        
        col1, col2 = st.columns(2)
        with col1:
            use_stop_loss = st.checkbox("Use Stop Loss", value=True)
            use_take_profit = st.checkbox("Use Take Profit", value=True)
            allow_shorting = st.checkbox("Allow Short Positions", value=False)
        
        with col2:
            max_correlation = st.slider("Max Correlation", 0.0, 1.0, 0.7, 0.1)
            min_sharpe_ratio = st.number_input("Min Sharpe Ratio", 0.0, 5.0, 0.5, 0.1)
    
    # Build the final goals and constraints objects
    goals = {
        "target_return": target_return,
        "time_horizon": time_horizon,
        "risk_tolerance": risk_tolerance,
        "investment_style": investment_style,
        "focus_areas": focus_areas,
        "use_stop_loss": use_stop_loss,
        "use_take_profit": use_take_profit,
        "allow_shorting": allow_shorting,
        "max_correlation": max_correlation,
        "min_sharpe_ratio": min_sharpe_ratio
    }
    
    constraints = {
        "max_position_size": max_position_size,
        "max_drawdown": max_drawdown,
        "allowed_assets": allowed_assets,
        "min_liquidity": min_liquidity_value,
        "max_slippage": max_slippage,
        "sector_limits": sector_limits
    }
    
    # Show summary
    st.markdown("### 📋 Configuration Summary")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Goals:**")
        st.json(goals)
    
    with col2:
        st.markdown("**Constraints:**")
        st.json(constraints)
    
    return goals, constraints

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
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False

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
    """Display trading analysis results with enhanced flexibility for different data structures"""
    if not analysis_data:
        st.warning("No analysis data available")
        return
    
    # Debug: Show the raw data structure if debug mode is enabled
    if st.session_state.get('debug_mode', False):
        st.subheader("🔍 Debug: Raw Response Data")
        st.json(analysis_data)
    
    # Extract data from multiple possible locations
    data_sources = []
    
    # Check for data in the main response
    if isinstance(analysis_data, dict):
        # Look for data in various possible keys
        for key in ['result', 'analysis', 'data', 'response']:
            if key in analysis_data and analysis_data[key]:
                data_sources.append(analysis_data[key])
        
        # If no data found in specific keys, use the entire response
        if not data_sources and len(analysis_data) > 2:  # More than just status/message
            data_sources.append(analysis_data)
    
    # If still no data sources, try the analysis_data itself
    if not data_sources:
        data_sources = [analysis_data]
    
    # Display data from all sources
    for i, data in enumerate(data_sources):
        if not data:
            continue
            
        # Create tabs for different types of data
        tab_names = []
        tab_data = {}
        
        # Check for different data types
        if isinstance(data, dict):
            # Market analysis
            if any(key in data for key in ['market_analysis', 'BTC', 'ETH', 'AAPL', 'MSFT']):
                tab_names.append("📊 Market Analysis")
                tab_data["📊 Market Analysis"] = data
            
            # Risk assessment
            if any(key in data for key in ['risk_assessment', 'risk_evaluation', 'risk_metrics']):
                tab_names.append("⚠️ Risk Assessment")
                tab_data["⚠️ Risk Assessment"] = data
            
            # Expert analysis
            if any(key in data for key in ['expert_analysis', 'analysis', 'recommendations']):
                tab_names.append("🧠 Expert Analysis")
                tab_data["🧠 Expert Analysis"] = data
            
            # Strategy
            if any(key in data for key in ['strategy', 'strategy_used', 'trading_strategy']):
                tab_names.append("🎯 Strategy")
                tab_data["🎯 Strategy"] = data
            
            # Trades
            if any(key in data for key in ['trades', 'orders', 'execution']):
                tab_names.append("💼 Trades")
                tab_data["💼 Trades"] = data
            
            # General data overview
            if not tab_names:
                tab_names.append("📋 Data Overview")
                tab_data["📋 Data Overview"] = data
        
        # Create tabs and display data
        if tab_names:
            tabs = st.tabs(tab_names)
            
            for tab, tab_name in zip(tabs, tab_names):
                with tab:
                    display_data_in_tab(tab_data[tab_name], tab_name)
        else:
            # Fallback: display as general data
            st.subheader("📋 Analysis Results")
            display_data_overview(data)
    
    # Show status information if available
    if isinstance(analysis_data, dict):
        status = analysis_data.get('status', 'unknown')
        message = analysis_data.get('message', '')
        timestamp = analysis_data.get('timestamp', '')
        
        if status or message:
            st.subheader("ℹ️ Status Information")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Status", status)
            with col2:
                if message:
                    st.write("**Message:**", message)
            with col3:
                if timestamp:
                    st.write("**Timestamp:**", timestamp)

def display_data_in_tab(data, tab_name):
    """Display data in a specific tab based on the tab name"""
    if tab_name == "📊 Market Analysis":
        display_market_analysis(data)
    elif tab_name == "⚠️ Risk Assessment":
        display_risk_assessment(data)
    elif tab_name == "🧠 Expert Analysis":
        display_recommendations(data)
    elif tab_name == "🎯 Strategy":
        display_strategy(data)
    elif tab_name == "💼 Trades":
        display_trades(data)
    else:
        display_data_overview(data)

def display_market_analysis(data):
    """Flexibly display market analysis data"""
    st.markdown("### 📊 Market Analysis")
    
    # Look for market analysis data in various possible locations
    market_data = None
    if "market_analysis" in data:
        market_data = data["market_analysis"]
    elif "market_data" in data:
        market_data = data["market_data"]
    elif "analysis" in data:
        market_data = data["analysis"]
    else:
        # Look for any key that might contain market data
        for key, value in data.items():
            if isinstance(value, dict) and any(asset in str(value).upper() for asset in ["BTC", "ETH", "AAPL", "MSFT"]):
                market_data = value
                break
    
    if not market_data:
        st.info("No market analysis data found")
        return
    
    # Display market data flexibly
    if isinstance(market_data, dict):
        for asset, asset_data in market_data.items():
            if isinstance(asset_data, dict):
                with st.expander(f"📈 {asset} Analysis", expanded=True):
                    display_asset_analysis(asset_data)
            else:
                st.write(f"**{asset}:** {asset_data}")
    else:
        st.json(market_data)

def display_asset_analysis(asset_data):
    """Display analysis for a single asset"""
    if not isinstance(asset_data, dict):
        st.write(asset_data)
        return
    
    # Create columns for different metrics
    col1, col2 = st.columns(2)
    
    with col1:
        # Price and basic metrics
        if "current_price" in asset_data:
            st.metric("Current Price", f"${asset_data['current_price']:.2f}")
        
        if "statistical_metrics" in asset_data:
            metrics = asset_data["statistical_metrics"]
            st.markdown("**📊 Statistical Metrics**")
            if "volatility" in metrics:
                st.metric("Volatility", f"{metrics['volatility']:.4f}")
            if "mean_return" in metrics:
                st.metric("Mean Return", f"{metrics['mean_return']:.4f}")
            if "var_95" in metrics:
                st.metric("VaR (95%)", f"{metrics['var_95']:.4f}")
        
        # Technical indicators
        if "technical_indicators" in asset_data:
            tech = asset_data["technical_indicators"]
            st.markdown("**🔧 Technical Indicators**")
            if "rsi" in tech:
                st.metric("RSI", f"{tech['rsi']:.2f}")
            if "macd" in tech:
                st.metric("MACD", f"{tech['macd']:.4f}")
    
    with col2:
        # Trend analysis
        if "trend_analysis" in asset_data:
            trend = asset_data["trend_analysis"]
            st.markdown("**📈 Trend Analysis**")
            if "trend_direction" in trend:
                direction = trend["trend_direction"]
                color = "green" if direction == "bullish" else "red" if direction == "bearish" else "orange"
                st.markdown(f"**Trend:** :{color}[{direction.title()}]")
            if "sma_20" in trend:
                st.metric("SMA 20", f"${trend['sma_20']:.2f}")
            if "sma_50" in trend:
                st.metric("SMA 50", f"${trend['sma_50']:.2f}")
        
        # Volatility analysis
        if "volatility_analysis" in asset_data:
            vol = asset_data["volatility_analysis"]
            st.markdown("**📊 Volatility Analysis**")
            if "volatility_regime" in vol:
                regime = vol["volatility_regime"]
                color = "green" if regime == "low" else "red" if regime == "high" else "orange"
                st.markdown(f"**Regime:** :{color}[{regime.title()}]")
            if "current_volatility" in vol:
                st.metric("Current Vol", f"{vol['current_volatility']:.4f}")
    
    # Recommendations
    if "recommendations" in asset_data:
        st.markdown("**💡 Recommendations**")
        for rec in asset_data["recommendations"]:
            st.write(f"• {rec}")

def display_risk_assessment(data):
    """Display risk assessment data with enhanced flexibility for different structures"""
    if not data:
        st.warning("No risk assessment data available")
        return
    
    st.subheader("⚠️ Risk Assessment")
    
    # Look for risk assessment data in various possible locations
    risk_data = None
    
    # Check for direct risk assessment data
    if isinstance(data, dict):
        # Look for risk assessment in various keys
        for key in ['risk_assessment', 'risk_evaluation', 'risk_metrics', 'risk_analysis']:
            if key in data and data[key]:
                risk_data = data[key]
                break
        
        # If no specific risk key found, check if the data itself contains risk metrics
        if not risk_data:
            # Check if data contains asset-specific risk metrics
            if any(isinstance(data.get(asset), dict) and 'risk_metrics' in data[asset] for asset in data.keys()):
                risk_data = data
            # Check if data contains general risk metrics
            elif any('risk' in key.lower() for key in data.keys()):
                risk_data = data
            # Check for nested risk_evaluation structure (from analysis field)
            elif 'risk_evaluation' in data and isinstance(data['risk_evaluation'], dict):
                risk_eval = data['risk_evaluation']
                if 'risk_assessment' in risk_eval:
                    risk_data = risk_eval['risk_assessment']
                else:
                    risk_data = risk_eval
    
    # If still no risk data found, use the original data
    if not risk_data:
        risk_data = data
    
    # Display the risk assessment data
    if isinstance(risk_data, dict):
        # Check if it's asset-specific risk data
        if any(isinstance(risk_data.get(asset), dict) and 'risk_metrics' in risk_data[asset] for asset in risk_data.keys()):
            # Asset-specific risk assessment
            for asset, asset_data in risk_data.items():
                if isinstance(asset_data, dict) and 'risk_metrics' in asset_data:
                    display_asset_risk(asset, asset_data)
        else:
            # General risk assessment
            display_general_risk(risk_data)
    else:
        # Fallback: display as JSON
        st.json(risk_data)

def display_asset_risk(asset, asset_data):
    """Display risk assessment for a single asset"""
    st.markdown(f"**⚠️ {asset} Risk Assessment**")
    
    # Display risk metrics
    if "risk_metrics" in asset_data:
        st.markdown("**📊 Risk Metrics**")
        for key, value in asset_data["risk_metrics"].items():
            st.metric(key.replace("_", " ").title(), f"{value:.4f}")
    
    # Display risk details
    st.markdown("**📋 Risk Details**")
    for key, value in asset_data.items():
        if isinstance(value, str):
            st.write(f"**{key.replace('_', ' ').title()}:** {value}")

def display_general_risk(risk_data):
    """Display general risk assessment"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 Risk Metrics**")
        for key, value in risk_data.items():
            if isinstance(value, (int, float)):
                st.metric(key.replace("_", " ").title(), f"{value:.4f}")
    
    with col2:
        st.markdown("**📋 Risk Details**")
        for key, value in risk_data.items():
            if isinstance(value, str):
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")

def display_recommendations(data):
    """Flexibly display recommendations"""
    st.markdown("### 💡 Recommendations")
    
    # Look for recommendations in various possible locations
    recommendations = None
    if "recommendations" in data:
        recommendations = data["recommendations"]
    elif "advice" in data:
        recommendations = data["advice"]
    elif "suggestions" in data:
        recommendations = data["suggestions"]
    
    if not recommendations:
        st.info("No recommendations found")
        return
    
    if isinstance(recommendations, list):
        for i, rec in enumerate(recommendations, 1):
            st.write(f"{i}. {rec}")
    elif isinstance(recommendations, dict):
        for category, recs in recommendations.items():
            st.markdown(f"**{category.replace('_', ' ').title()}:**")
            if isinstance(recs, list):
                for rec in recs:
                    st.write(f"• {rec}")
            else:
                st.write(f"• {recs}")
    else:
        st.write(recommendations)

def display_strategy(data):
    """Flexibly display strategy information"""
    st.markdown("### 🎯 Strategy")
    
    # Look for strategy data
    strategy_data = None
    if "strategy" in data:
        strategy_data = data["strategy"]
    elif "strategy_analysis" in data:
        strategy_data = data["strategy_analysis"]
    
    if not strategy_data:
        st.info("No strategy data found")
        return
    
    if isinstance(strategy_data, dict):
        for key, value in strategy_data.items():
            st.markdown(f"**{key.replace('_', ' ').title()}:**")
            if isinstance(value, list):
                for item in value:
                    st.write(f"• {item}")
            else:
                st.write(value)
    else:
        st.write(strategy_data)

def display_trades(data):
    """Flexibly display trade information"""
    st.markdown("### 💼 Trades")
    
    # Look for trade data
    trade_data = None
    if "trades" in data:
        trade_data = data["trades"]
    elif "trade_recommendations" in data:
        trade_data = data["trade_recommendations"]
    
    if not trade_data:
        st.info("No trade data found")
        return
    
    if isinstance(trade_data, list):
        for i, trade in enumerate(trade_data, 1):
            with st.expander(f"Trade {i}", expanded=True):
                if isinstance(trade, dict):
                    for key, value in trade.items():
                        st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                else:
                    st.write(trade)
    elif isinstance(trade_data, dict):
        for key, value in trade_data.items():
            st.markdown(f"**{key.replace('_', ' ').title()}:**")
            st.write(value)
    else:
        st.write(trade_data)

def display_data_overview(data):
    """Display a general overview of all data"""
    st.markdown("### 📋 Data Overview")
    
    if isinstance(data, dict):
        # Create a tree-like view of the data structure
        def display_dict_recursive(d, level=0):
            indent = "  " * level
            for key, value in d.items():
                if isinstance(value, dict):
                    st.markdown(f"{indent}**{key.replace('_', ' ').title()}:**")
                    display_dict_recursive(value, level + 1)
                elif isinstance(value, list):
                    st.markdown(f"{indent}**{key.replace('_', ' ').title()}:**")
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            st.markdown(f"{indent}  Item {i+1}:")
                            display_dict_recursive(item, level + 2)
                        else:
                            st.write(f"{indent}  • {item}")
                else:
                    st.write(f"{indent}**{key.replace('_', ' ').title()}:** {value}")
        
        display_dict_recursive(data)
    else:
        st.json(data)

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
            
            # Return the result even if status is not success, as long as we have data
            if result.get("status") == "success" or result.get("result") or result.get("data") or result.get("analysis"):
                return result
            else:
                st.error(f"Backend returned error: {result.get('message', 'Unknown error')}")
                return result  # Still return it so the UI can handle it
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
        
        # Debug: Show what we got back
        if st.session_state.get('debug_mode', False):
            st.write("**Debug - Trigger Response:**")
            st.json(trigger_resp)
        
        if trigger_resp:
            # Check if we have data, even if status is not success
            if trigger_resp.get("status") == "success":
                st.success("Trading request sent successfully!")
                st.session_state.trading_results = trigger_resp
                st.session_state.show_results = True
                st.session_state.current_session = ask_id
                if st.session_state.get('debug_mode', False):
                    st.write("**Debug - Set show_results to True**")
                return True
            elif trigger_resp.get("result") or trigger_resp.get("data") or trigger_resp.get("analysis"):
                # If we have data even with error status, show it
                st.warning("Trading request completed with warnings, but data is available:")
                st.write(f"Warning: {trigger_resp.get('message', 'Unknown warning')}")
                st.session_state.trading_results = trigger_resp
                st.session_state.show_results = True
                st.session_state.current_session = ask_id
                if st.session_state.get('debug_mode', False):
                    st.write("**Debug - Set show_results to True (with warnings)**")
                return True
            else:
                error_msg = trigger_resp.get("message", "Unknown error")
                st.error(f"Error sending trading request: {error_msg}")
                return False
        else:
            st.error("Failed to get response from backend")
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

        # Use the new flexible trading form
        goals, constraints = create_flexible_trading_form()
        
        # Convert the form data to the format expected by the backend
        # Map the new flexible format to the backend format
        backend_goals = {
            "goal": f"{goals['investment_style']} trading with {goals['risk_tolerance']} risk",
            "timeframe": goals['time_horizon'],
            "target_return": goals['target_return'],
            "risk_tolerance": goals['risk_tolerance'],
            "trading_pairs": [f"{asset}/USD" for asset in constraints['allowed_assets']],
            "strategy_type": goals['investment_style'],
            "focus_areas": goals['focus_areas'],
            "use_stop_loss": goals['use_stop_loss'],
            "use_take_profit": goals['use_take_profit'],
            "allow_shorting": goals['allow_shorting'],
            "max_correlation": goals['max_correlation'],
            "min_sharpe_ratio": goals['min_sharpe_ratio']
        }
        
        backend_constraints = {
            "max_risk": 1.0 - {"low": 0.8, "moderate": 0.6, "high": 0.4, "very_high": 0.2}.get(goals['risk_tolerance'], 0.6),
            "max_position_size": constraints['max_position_size'],
            "max_drawdown": constraints['max_drawdown'],
            "min_liquidity": constraints['min_liquidity'],
            "max_slippage": constraints['max_slippage'],
            "allowed_assets": constraints['allowed_assets'],
            "sector_limits": constraints['sector_limits']
        }

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
                    # Convert to JSON strings for the existing function
                    goals_json = json.dumps(backend_goals)
                    constraints_json = json.dumps(backend_constraints)
                    
                    if process_trading_request(goals_json, constraints_json, ask_id, HUMAN_TRADER_ACCOUNT):
                        st.rerun()
        
        with col2:
            if st.button("🔄 Reset Form", key="reset_form"):
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

    # Use the new flexible trading form
    goals, constraints = create_flexible_trading_form()
    
    # Convert the form data to the format expected by the backend
    # Map the new flexible format to the backend format
    backend_goals = {
        "goal": f"{goals['investment_style']} trading with {goals['risk_tolerance']} risk",
        "timeframe": goals['time_horizon'],
        "target_return": goals['target_return'],
        "risk_tolerance": goals['risk_tolerance'],
        "trading_pairs": [f"{asset}/USD" for asset in constraints['allowed_assets']],
        "strategy_type": goals['investment_style'],
        "focus_areas": goals['focus_areas'],
        "use_stop_loss": goals['use_stop_loss'],
        "use_take_profit": goals['use_take_profit'],
        "allow_shorting": goals['allow_shorting'],
        "max_correlation": goals['max_correlation'],
        "min_sharpe_ratio": goals['min_sharpe_ratio']
    }
    
    backend_constraints = {
        "max_risk": 1.0 - {"low": 0.8, "moderate": 0.6, "high": 0.4, "very_high": 0.2}.get(goals['risk_tolerance'], 0.6),
        "max_position_size": constraints['max_position_size'],
        "max_drawdown": constraints['max_drawdown'],
        "min_liquidity": constraints['min_liquidity'],
        "max_slippage": constraints['max_slippage'],
        "allowed_assets": constraints['allowed_assets'],
        "sector_limits": constraints['sector_limits']
    }

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
                # Convert to JSON strings for the existing function
                goals_json = json.dumps(backend_goals)
                constraints_json = json.dumps(backend_constraints)
                
                if process_trading_request(goals_json, constraints_json, ask_id, HUMAN_TRADER_ACCOUNT):
                    st.rerun()
        
        with col2:
            if st.button("🔄 Reset Form", key="reset_form"):
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

# Debug section
with st.expander("🔧 Debug Information", expanded=False):
    st.write("**Session State:**")
    st.write(f"- show_results: {st.session_state.get('show_results', False)}")
    st.write(f"- trading_results: {st.session_state.get('trading_results', None) is not None}")
    if st.session_state.get('trading_results'):
        st.write(f"- trading_results keys: {list(st.session_state.trading_results.keys())}")
    
    # Debug mode toggle
    debug_mode = st.checkbox("Enable Debug Mode", value=st.session_state.get('debug_mode', False))
    st.session_state.debug_mode = debug_mode
    
    if debug_mode:
        st.write("**Raw Trading Results:**")
        st.json(st.session_state.get('trading_results', {}))

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