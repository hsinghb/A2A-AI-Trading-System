#!/usr/bin/env python3
"""
Test script to check backend response format
"""

import sys
import os
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_backend_response():
    """Test the backend trading endpoint and see the response format"""
    
    # Backend URL
    backend_url = "http://localhost:8000/trading/process"
    
    # Get admin credentials
    admin_private_key = os.getenv("ADMIN_PRIVATE_KEY")
    admin_did = os.getenv("ADMIN_DID")
    
    if not admin_private_key or not admin_did:
        print("❌ Admin credentials not found in environment")
        return
    
    # Generate JWT
    from backend.eth_jwt_utils import generate_test_jwt_ethereum
    
    jwt = generate_test_jwt_ethereum(
        did=admin_did,
        private_key=admin_private_key,
        additional_claims={"role": "admin"}
    )
    
    # Test request data
    test_request = {
        "session_id": "test_session_123",
        "request": {
            "goals": {
                "target_return": 0.1,
                "time_horizon": "1d",
                "risk_tolerance": "moderate",
                "assets": ["AAPL", "MSFT"]
            },
            "constraints": {
                "max_position_size": 100000,
                "max_drawdown": 0.05,
                "allowed_assets": ["AAPL", "MSFT"],
                "min_liquidity": 1000000,
                "max_slippage": 0.01
            },
            "portfolio": {
                "total_value": 100000,
                "positions": {
                    "AAPL": {"allocation": 0.5, "value": 50000},
                    "MSFT": {"allocation": 0.5, "value": 50000}
                }
            }
        },
        "verification": {
            "did": admin_did,
            "jwt": jwt
        }
    }
    
    try:
        print("🚀 Testing backend response format...")
        print(f"Request URL: {backend_url}")
        print(f"Admin DID: {admin_did}")
        
        # Make the request
        response = requests.post(backend_url, json=test_request, timeout=30)
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Success! Response structure:")
            print(json.dumps(data, indent=2))
            
            # Check the structure
            if "analysis" in data:
                analysis = data["analysis"]
                print(f"\n📋 Analysis field type: {type(analysis)}")
                print(f"📋 Analysis keys: {list(analysis.keys()) if isinstance(analysis, dict) else 'Not a dict'}")
                
                # Check for market data
                if isinstance(analysis, dict):
                    if "AAPL" in analysis or "MSFT" in analysis:
                        print("✅ Found direct asset data in analysis")
                    elif "market_analysis" in analysis:
                        print("✅ Found market_analysis field")
                    elif "market_data" in analysis:
                        print("✅ Found market_data field")
                    else:
                        print("❌ No market data found in expected locations")
            else:
                print("❌ No 'analysis' field found in response")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing backend: {str(e)}")

if __name__ == "__main__":
    test_backend_response() 