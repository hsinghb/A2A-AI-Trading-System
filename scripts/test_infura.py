"""
Script to test Infura connection and help set up project ID
"""

import os
import sys
import logging
from web3 import Web3
from dotenv import load_dotenv, set_key
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_infura_connection(project_id=None):
    """Test connection to Infura and help set up project ID"""
    try:
        # Load current .env file
        load_dotenv()
        current_rpc = os.getenv("ETHEREUM_RPC_URL", "")
        
        # If no project ID provided, try to extract from current RPC URL
        if not project_id and "infura.io" in current_rpc:
            project_id = current_rpc.split("/")[-1]
            logger.info(f"Found existing project ID: {project_id}")
        
        # If still no project ID, ask for it
        if not project_id:
            project_id = input("Please enter your Infura project ID: ").strip()
            if not project_id:
                raise ValueError("Project ID is required")
        
        # Construct RPC URL
        rpc_url = f"https://sepolia.infura.io/v3/{project_id}"
        
        # Test connection
        logger.info(f"Testing connection to: {rpc_url}")
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not w3.is_connected():
            raise ConnectionError("Failed to connect to Infura")
        
        # Get network info
        network_version = w3.net.version
        latest_block = w3.eth.block_number
        
        logger.info("Connection successful!")
        logger.info(f"Connected to network: {network_version}")
        logger.info(f"Latest block: {latest_block}")
        
        # Update .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        
        # Read current .env content
        try:
            with open(env_path, 'r') as f:
                env_content = f.read()
        except FileNotFoundError:
            env_content = ""
        
        # Update or add ETHEREUM_RPC_URL
        if "ETHEREUM_RPC_URL=" in env_content:
            # Update existing value
            set_key(env_path, "ETHEREUM_RPC_URL", rpc_url)
        else:
            # Add new value
            with open(env_path, 'a') as f:
                f.write(f"\nETHEREUM_RPC_URL={rpc_url}\n")
        
        logger.info(f"Updated .env file with new RPC URL")
        
        # Test account connection if private key exists
        private_key = os.getenv("ADMIN_PRIVATE_KEY")
        if private_key:
            from eth_account import Account
            account = Account.from_key(private_key)
            address = account.address
            balance = w3.eth.get_balance(address)
            balance_eth = w3.from_wei(balance, 'ether')
            
            logger.info("\nAccount details:")
            logger.info(f"Address: {address}")
            logger.info(f"Balance: {balance_eth} ETH")
            
            if balance_eth < 0.01:
                logger.warning("\nLow balance! You need some test ETH for deployment.")
                logger.info("Get test ETH from: https://sepoliafaucet.com/")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing Infura connection: {str(e)}")
        return False

if __name__ == "__main__":
    # Allow project ID as command line argument
    project_id = sys.argv[1] if len(sys.argv) > 1 else None
    test_infura_connection(project_id) 