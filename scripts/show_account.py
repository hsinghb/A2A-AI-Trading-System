"""
Script to show account details and how the address is derived
"""

import os
import logging
from web3 import Web3
from dotenv import load_dotenv
from eth_account import Account

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_account_details():
    """Show account details and explain how the address is derived"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get private key
        private_key = os.getenv("ADMIN_PRIVATE_KEY")
        if not private_key:
            raise ValueError("ADMIN_PRIVATE_KEY not found in .env file")
        
        # Create account from private key
        account = Account.from_key(private_key)
        address = account.address
        
        logger.info("Account Details:")
        logger.info("----------------")
        logger.info(f"Private Key: {private_key[:6]}...{private_key[-4:]} (truncated for security)")
        logger.info(f"Address: {address}")
        
        logger.info("\nHow this address was generated:")
        logger.info("1. The private key is a 64-character hexadecimal number")
        logger.info("2. This private key is used to derive your public key")
        logger.info("3. The last 20 bytes of the Keccak-256 hash of your public key becomes your address")
        logger.info("4. The address is prefixed with '0x' to indicate it's a hexadecimal number")
        
        logger.info("\nTo get test ETH:")
        logger.info(f"1. Go to https://sepoliafaucet.com/")
        logger.info(f"2. Enter this address: {address}")
        logger.info("3. Complete the verification process")
        logger.info("4. Wait a few minutes for the ETH to arrive")
        
        # Check current balance
        rpc_url = os.getenv("ETHEREUM_RPC_URL")
        if rpc_url:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if w3.is_connected():
                balance = w3.eth.get_balance(address)
                balance_eth = w3.from_wei(balance, 'ether')
                logger.info(f"\nCurrent balance: {balance_eth} ETH")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    show_account_details() 