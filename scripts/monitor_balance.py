"""
Script to monitor account balance while waiting for test ETH
"""

import os
import time
import logging
from web3 import Web3
from dotenv import load_dotenv
from eth_account import Account

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monitor_balance():
    """Monitor account balance until it's sufficient for deployment"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get RPC URL and private key
        rpc_url = os.getenv("ETHEREUM_RPC_URL")
        private_key = os.getenv("ADMIN_PRIVATE_KEY")
        
        if not all([rpc_url, private_key]):
            raise ValueError("Missing required environment variables")
        
        # Initialize Web3
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            raise ConnectionError("Failed to connect to Ethereum node")
        
        # Get account
        account = Account.from_key(private_key)
        address = account.address
        
        logger.info(f"Monitoring balance for address: {address}")
        logger.info("Waiting for test ETH... (Press Ctrl+C to stop)")
        
        last_balance = None
        while True:
            try:
                # Get current balance
                balance = w3.eth.get_balance(address)
                balance_eth = w3.from_wei(balance, 'ether')
                
                # Only log if balance changed
                if balance_eth != last_balance:
                    logger.info(f"Current balance: {balance_eth} ETH")
                    last_balance = balance_eth
                    
                    # Check if we have enough for deployment
                    if balance_eth >= 0.01:
                        logger.info("\n✅ Sufficient balance for deployment!")
                        logger.info("You can now run: python scripts/deploy_registry.py")
                        break
                
                # Wait 10 seconds before next check
                time.sleep(10)
                
            except KeyboardInterrupt:
                logger.info("\nMonitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error checking balance: {str(e)}")
                time.sleep(10)  # Wait before retrying
        
    except Exception as e:
        logger.error(f"Error in monitoring: {str(e)}")
        raise

if __name__ == "__main__":
    monitor_balance() 