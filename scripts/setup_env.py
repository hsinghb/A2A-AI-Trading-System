#!/usr/bin/env python3
"""
Script to set up the initial environment variables for the trading system.
This script creates a .env file with the necessary configuration.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def setup_environment():
    """Set up the initial environment variables."""
    try:
        # Get project root directory
        env_path = project_root / ".env"
        
        # Check if .env already exists
        if env_path.exists():
            print("Found existing .env file. Please backup and remove it before running this script.")
            return
        
        # Get user input for configuration
        print("\nSetting up environment variables...")
        print("================================")
        
        # Get RPC URL
        rpc_url = input("\nEnter Ethereum RPC URL (default: http://localhost:8545): ").strip()
        if not rpc_url:
            rpc_url = "http://localhost:8545"
        
        # Get contract address
        contract_address = input("\nEnter AgentRegistry contract address: ").strip()
        if not contract_address:
            print("Error: Contract address is required")
            return
        
        # Create .env file
        with open(env_path, "w") as f:
            f.write("# Ethereum Network Configuration\n")
            f.write(f"ETH_RPC_URL={rpc_url}\n")
            f.write(f"AGENT_REGISTRY_ADDRESS={contract_address}\n\n")
            
            f.write("# Admin Credentials\n")
            f.write("# These will be set by setup_admin.py\n")
            f.write("ADMIN_DID=\n")
            f.write("ADMIN_PRIVATE_KEY=\n\n")
            
            f.write("# Trading Agent Credentials\n")
            f.write("# These will be set by register_agents.py\n")
            f.write("EXPERT_AGENT_DID=\n")
            f.write("EXPERT_AGENT_PRIVATE_KEY=\n")
            f.write("RISK_AGENT_DID=\n")
            f.write("RISK_AGENT_PRIVATE_KEY=\n")
        
        print(f"\nEnvironment variables have been saved to {env_path}")
        print("\nNext Steps:")
        print("1. Verify the RPC URL and contract address in the .env file")
        print("2. Run 'python scripts/setup_admin.py' to set up the admin account")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    setup_environment() 