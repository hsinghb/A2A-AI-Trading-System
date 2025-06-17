"""
Script to test Ethereum node connection
"""

import logging
from web3 import Web3
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Test connection to Ethereum node"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get RPC URL
        rpc_url = os.getenv("ETHEREUM_RPC_URL")
        if not rpc_url:
            raise ValueError("ETHEREUM_RPC_URL not found in .env file")
        
        logger.info(f"Attempting to connect to: {rpc_url}")
        
        # Initialize Web3
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Test connection
        if w3.is_connected():
            logger.info("Successfully connected to Ethereum node!")
            logger.info(f"Connected to network: {w3.net.version}")
            logger.info(f"Current block number: {w3.eth.block_number}")
            
            # Get admin account if private key is available
            admin_private_key = os.getenv("ADMIN_PRIVATE_KEY")
            if admin_private_key:
                from eth_account import Account
                admin_account = Account.from_key(admin_private_key)
                admin_address = admin_account.address
                balance = w3.eth.get_balance(admin_address)
                logger.info(f"Admin address: {admin_address}")
                logger.info(f"Admin balance: {w3.from_wei(balance, 'ether')} ETH")
            else:
                logger.warning("ADMIN_PRIVATE_KEY not found in .env file")
        else:
            raise ConnectionError("Failed to connect to Ethereum node")
            
    except Exception as e:
        logger.error(f"Error testing connection: {str(e)}")
        raise

if __name__ == "__main__":
    test_connection() 