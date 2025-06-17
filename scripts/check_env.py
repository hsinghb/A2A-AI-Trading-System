"""
Script to verify environment setup before deployment
"""

import os
import logging
from web3 import Web3
from dotenv import load_dotenv
from eth_account import Account

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if environment is properly configured for deployment"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Check RPC URL
        rpc_url = os.getenv("ETHEREUM_RPC_URL")
        if not rpc_url:
            raise ValueError("ETHEREUM_RPC_URL not found in .env file")
        if "YOUR-PROJECT-ID" in rpc_url:
            raise ValueError("Please replace YOUR-PROJECT-ID in ETHEREUM_RPC_URL with your actual Infura project ID")
        
        # Check private key
        private_key = os.getenv("ADMIN_PRIVATE_KEY")
        if not private_key:
            raise ValueError("ADMIN_PRIVATE_KEY not found in .env file")
        
        # Initialize Web3
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            raise ConnectionError("Failed to connect to Ethereum node")
        
        # Get account details
        account = Account.from_key(private_key)
        address = account.address
        balance = w3.eth.get_balance(address)
        balance_eth = w3.from_wei(balance, 'ether')
        
        logger.info("Environment check results:")
        logger.info(f"Connected to network: {w3.net.version}")
        logger.info(f"Account address: {address}")
        logger.info(f"Account balance: {balance_eth} ETH")
        
        if balance_eth < 0.01:
            logger.warning("Low balance! You need some test ETH for deployment.")
            logger.info("Get test ETH from: https://sepoliafaucet.com/")
            return False
        
        logger.info("Environment check passed! Ready for deployment.")
        return True
        
    except Exception as e:
        logger.error(f"Environment check failed: {str(e)}")
        return False

if __name__ == "__main__":
    check_environment() 