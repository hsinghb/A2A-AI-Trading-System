#!/usr/bin/env python3
"""
Script to deploy the AgentRegistry contract and set up environment variables.
"""

import os
import sys
import json
import logging
from pathlib import Path
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def deploy_contract(w3: Web3, account: Account, contract_abi: list, contract_bytecode: str) -> str:
    """Deploy the AgentRegistry contract."""
    try:
        # Create contract instance
        contract = w3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)
        
        # Get deployment account
        address = account.address
        private_key = account.key.hex()
        
        # Get nonce and gas price
        nonce = w3.eth.get_transaction_count(address)
        gas_price = w3.eth.gas_price
        
        # Build transaction
        tx = contract.constructor().build_transaction({
            'from': address,
            'nonce': nonce,
            'gas': 2000000,  # Gas limit
            'gasPrice': gas_price
        })
        
        # Sign and send transaction
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status != 1:
            raise Exception("Contract deployment failed")
        
        return receipt.contractAddress
        
    except Exception as e:
        logger.error(f"Failed to deploy contract: {str(e)}")
        raise

def main():
    """Main function to deploy contract and set up environment."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get RPC URL
        rpc_url = os.getenv("ETH_RPC_URL", "http://localhost:8545")
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not w3.is_connected():
            raise Exception(f"Failed to connect to Ethereum node at {rpc_url}")
        
        # Load contract ABI and bytecode
        contract_path = project_root / "backend" / "blockchain" / "contracts" / "AgentRegistry.json"
        with open(contract_path, "r") as f:
            contract_data = json.load(f)
            contract_abi = contract_data["abi"]
            contract_bytecode = contract_data["bytecode"]
        
        # Generate deployment account
        account = Account.create()
        address = account.address
        private_key = account.key.hex()
        
        # Deploy contract
        print("\nDeploying AgentRegistry contract...")
        contract_address = deploy_contract(w3, account, contract_abi, contract_bytecode)
        print(f"Contract deployed at: {contract_address}")
        
        # Save environment variables
        env_path = project_root / ".env"
        
        # Check if .env exists and read existing content
        existing_vars = {}
        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        key, value = line.strip().split("=", 1)
                        existing_vars[key] = value
        
        # Update environment variables
        existing_vars["ETH_RPC_URL"] = rpc_url
        existing_vars["AGENT_REGISTRY_ADDRESS"] = contract_address
        existing_vars["ADMIN_DID"] = f"did:eth:{address}"
        existing_vars["ADMIN_PRIVATE_KEY"] = private_key
        
        # Write back to .env file
        with open(env_path, "w") as f:
            f.write("# Ethereum Network Configuration\n")
            f.write(f"ETH_RPC_URL={rpc_url}\n")
            f.write(f"AGENT_REGISTRY_ADDRESS={contract_address}\n\n")
            
            f.write("# Admin Credentials\n")
            f.write(f"ADMIN_DID=did:eth:{address}\n")
            f.write(f"ADMIN_PRIVATE_KEY={private_key}\n\n")
            
            # Write other existing variables
            for key, value in existing_vars.items():
                if key not in ["ETH_RPC_URL", "AGENT_REGISTRY_ADDRESS", "ADMIN_DID", "ADMIN_PRIVATE_KEY"]:
                    f.write(f"{key}={value}\n")
        
        print("\nEnvironment setup complete!")
        print("\nNext Steps:")
        print("1. Fund the admin account with some ETH for gas fees")
        print("2. Run 'python scripts/register_agents.py' to register trading agents")
        
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 