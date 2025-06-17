#!/usr/bin/env python3
"""
Script to register trading agents in the blockchain registry.
This script registers both expert and risk agents with their DIDs and public keys.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from eth_account import Account
from web3 import Web3

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.blockchain.agent_registry import agent_registry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_eth_account() -> tuple[str, str, str]:
    """Generate a new Ethereum account and return its address, private key, and DID."""
    account = Account.create()
    address = account.address
    private_key = account.key.hex()
    did = f"did:eth:{address}"
    return address, private_key, did

def register_agent(agent_type: str) -> tuple[str, str, str]:
    """Register a new agent of the specified type."""
    try:
        # Generate new Ethereum account for the agent
        address, private_key, did = generate_eth_account()
        
        # Get the public key (in this case, it's the same as the address)
        public_key = address
        
        # Register the agent in the blockchain registry
        metadata = {
            "type": agent_type,
            "name": f"{agent_type.capitalize()} Trading Agent",
            "version": "1.0.0",
            "capabilities": ["trading_analysis"] if agent_type == "expert" else ["risk_evaluation"]
        }
        
        # Register agent using the blockchain registry
        tx_hash = agent_registry.register_agent(did, public_key, metadata)
        logger.info(f"Registered {agent_type} agent with DID: {did}")
        logger.info(f"Transaction hash: {tx_hash}")
        
        return did, private_key, public_key
        
    except Exception as e:
        logger.error(f"Failed to register {agent_type} agent: {str(e)}")
        raise

def main():
    """Main function to register expert and risk agents."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Verify admin credentials are set
        admin_did = os.getenv("ADMIN_DID")
        admin_private_key = os.getenv("ADMIN_PRIVATE_KEY")
        
        if not admin_did or not admin_private_key:
            raise ValueError("Admin DID and private key must be set in environment variables")
        
        # Verify admin is registered
        admin_info = agent_registry.get_agent(admin_did)
        if not admin_info["is_active"]:
            raise ValueError("Admin account is not registered or not active in the blockchain registry")
        
        # Register expert agent
        expert_did, expert_private_key, expert_public_key = register_agent("expert")
        
        # Register risk agent
        risk_did, risk_private_key, risk_public_key = register_agent("risk")
        
        # Print registration summary
        print("\nAgent Registration Summary:")
        print("==========================")
        print(f"\nExpert Agent:")
        print(f"DID: {expert_did}")
        print(f"Private Key: {expert_private_key}")
        print(f"Public Key: {expert_public_key}")
        
        print(f"\nRisk Agent:")
        print(f"DID: {risk_did}")
        print(f"Private Key: {risk_private_key}")
        print(f"Public Key: {risk_public_key}")
        
        # Save agent credentials to .env file
        env_path = project_root / ".env"
        
        # Read existing .env content
        existing_vars = {}
        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        key, value = line.strip().split("=", 1)
                        existing_vars[key] = value
        
        # Update agent credentials
        existing_vars["EXPERT_AGENT_DID"] = expert_did
        existing_vars["EXPERT_AGENT_PRIVATE_KEY"] = expert_private_key
        existing_vars["RISK_AGENT_DID"] = risk_did
        existing_vars["RISK_AGENT_PRIVATE_KEY"] = risk_private_key
        
        # Write back to .env file
        with open(env_path, "w") as f:
            # Write sections
            f.write("# Ethereum Network Configuration\n")
            for key in ["ETH_RPC_URL", "AGENT_REGISTRY_ADDRESS"]:
                if key in existing_vars:
                    f.write(f"{key}={existing_vars[key]}\n")
            f.write("\n")
            
            f.write("# Admin Credentials\n")
            for key in ["ADMIN_DID", "ADMIN_PRIVATE_KEY"]:
                if key in existing_vars:
                    f.write(f"{key}={existing_vars[key]}\n")
            f.write("\n")
            
            f.write("# Trading Agent Credentials\n")
            for key in ["EXPERT_AGENT_DID", "EXPERT_AGENT_PRIVATE_KEY", 
                       "RISK_AGENT_DID", "RISK_AGENT_PRIVATE_KEY"]:
                if key in existing_vars:
                    f.write(f"{key}={existing_vars[key]}\n")
            f.write("\n")
            
            # Write other variables
            for key, value in existing_vars.items():
                if key not in ["ETH_RPC_URL", "AGENT_REGISTRY_ADDRESS",
                             "ADMIN_DID", "ADMIN_PRIVATE_KEY",
                             "EXPERT_AGENT_DID", "EXPERT_AGENT_PRIVATE_KEY",
                             "RISK_AGENT_DID", "RISK_AGENT_PRIVATE_KEY"]:
                    f.write(f"{key}={value}\n")
        
        logger.info("Agent credentials have been saved to .env file")
        
        # Verify agent registration
        expert_info = agent_registry.get_agent(expert_did)
        risk_info = agent_registry.get_agent(risk_did)
        
        print("\nVerification Results:")
        print("====================")
        print(f"\nExpert Agent Status: {'Active' if expert_info['is_active'] else 'Inactive'}")
        print(f"Risk Agent Status: {'Active' if risk_info['is_active'] else 'Inactive'}")
        
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 