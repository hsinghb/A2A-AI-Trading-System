#!/usr/bin/env python3
"""
Script to set up the admin account for the trading system.
This script generates a new Ethereum account for the admin, registers it in the blockchain,
and saves the credentials to .env file.
"""

import os
import sys
import logging
from pathlib import Path
from eth_account import Account
from web3 import Web3
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.blockchain.agent_registry import AgentRegistryContract

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_admin_account() -> tuple[str, str, str]:
    """Generate a new Ethereum account for the admin."""
    account = Account.create()
    address = account.address
    private_key = account.key.hex()
    did = f"did:eth:{address}"
    return address, private_key, did

def register_admin(address: str, private_key: str) -> bool:
    """Register the admin account in the blockchain registry."""
    try:
        # Create a new agent registry instance
        agent_registry = AgentRegistryContract()
        
        # First register as an agent
        did = f"did:eth:{address}"
        metadata = {
            "type": "admin",
            "name": "System Administrator",
            "version": "1.0.0",
            "capabilities": ["admin_management"]
        }
        
        # Register as agent first
        tx_hash = agent_registry.register_agent(did, address, metadata)
        logger.info(f"Registered admin as agent with transaction: {tx_hash}")
        
        # Verify agent registration
        agent_info = agent_registry.get_agent(did)
        if not agent_info["is_active"]:
            raise Exception("Failed to verify agent registration")
        
        # Then set as admin
        tx_hash = agent_registry.register_admin(address, private_key)
        logger.info(f"Set admin status with transaction: {tx_hash}")
        
        # Verify admin status
        is_admin = agent_registry.is_admin(address)
        if not is_admin:
            raise Exception("Failed to verify admin status after registration")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to register admin: {str(e)}")
        return False

def main():
    """Main function to set up admin account."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get project root directory
        project_root = Path(__file__).parent.parent
        
        # Check if admin already exists in .env
        existing_admin_address = os.getenv("ADMIN_ADDRESS")
        existing_admin_key = os.getenv("ADMIN_PRIVATE_KEY")
        
        if existing_admin_address and existing_admin_key:
            logger.info("Found existing admin credentials in .env")
            address = existing_admin_address
            did = f"did:eth:{address}"
            
            # Create a new agent registry instance
            agent_registry = AgentRegistryContract()
            
            # Verify if existing admin is registered
            try:
                agent_info = agent_registry.get_agent(did)
                if agent_info["is_active"] and agent_registry.is_admin(address):
                    logger.info("Existing admin is already registered in the blockchain")
                    return
            except Exception as e:
                logger.warning(f"Existing admin not registered: {str(e)}")
            
            # Try to register existing admin
            if register_admin(address, existing_admin_key):
                logger.info("Successfully registered existing admin")
                return
            else:
                logger.warning("Failed to register existing admin, generating new account")
        
        # Generate new admin account
        address, private_key, did = generate_admin_account()
        
        # Print admin credentials
        print("\nAdmin Account Setup:")
        print("===================")
        print(f"Address: {address}")
        print(f"DID: {did}")
        print(f"Private Key: {private_key}")
        
        # Register admin in blockchain
        print("\nRegistering admin in blockchain...")
        if not register_admin(address, private_key):
            print("\nError: Failed to register admin in blockchain.")
            print("This could be because:")
            print("1. The blockchain network is not accessible")
            print("2. The account doesn't have enough ETH for gas")
            print("3. The contract is not properly deployed")
            sys.exit(1)
        
        # Save to .env file
        env_path = project_root / ".env"
        
        # Check if .env exists and read existing content
        existing_vars = {}
        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        key, value = line.strip().split("=", 1)
                        existing_vars[key] = value
        
        # Update admin credentials
        existing_vars["ADMIN_ADDRESS"] = address
        existing_vars["ADMIN_PRIVATE_KEY"] = private_key
        existing_vars["ADMIN_DID"] = did
        
        # Write back to .env file
        with open(env_path, "w") as f:
            # Write sections
            f.write("# Ethereum Network Configuration\n")
            for key in ["ETHEREUM_RPC_URL", "AGENT_REGISTRY_ADDRESS"]:
                if key in existing_vars:
                    f.write(f"{key}={existing_vars[key]}\n")
            f.write("\n")
            
            f.write("# Admin Credentials\n")
            f.write(f"ADMIN_ADDRESS={address}\n")
            f.write(f"ADMIN_PRIVATE_KEY={private_key}\n")
            f.write(f"ADMIN_DID={did}\n")
            f.write("\n")
            
            # Write other variables
            for key, value in existing_vars.items():
                if key not in ["ETHEREUM_RPC_URL", "AGENT_REGISTRY_ADDRESS",
                             "ADMIN_ADDRESS", "ADMIN_PRIVATE_KEY", "ADMIN_DID"]:
                    f.write(f"{key}={value}\n")
        
        logger.info(f"Admin credentials have been saved to {env_path}")
        
        print("\nAdmin Setup Complete!")
        print("\nNext Steps:")
        print("1. Ensure the admin account has enough ETH for gas fees")
        print("2. Run 'python scripts/register_agents.py' to register trading agents")
        
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 