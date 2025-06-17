"""
Script to check address on both mainnet and testnet
"""

import os
import logging
from web3 import Web3
from dotenv import load_dotenv
from eth_account import Account

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_networks():
    """Check address on both mainnet and testnet"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get account
        private_key = os.getenv("ADMIN_PRIVATE_KEY")
        if not private_key:
            raise ValueError("ADMIN_PRIVATE_KEY not found in .env file")
        
        account = Account.from_key(private_key)
        address = account.address
        
        logger.info(f"Your address: {address}")
        logger.info("\nChecking different networks:")
        
        # Mainnet (using Infura)
        mainnet_url = "https://mainnet.infura.io/v3/3924afa57c00454c80d1d403b1d8e272"
        w3_mainnet = Web3(Web3.HTTPProvider(mainnet_url))
        
        if w3_mainnet.is_connected():
            balance_mainnet = w3_mainnet.eth.get_balance(address)
            balance_mainnet_eth = w3_mainnet.from_wei(balance_mainnet, 'ether')
            logger.info("\nMainnet (Real ETH):")
            logger.info(f"Network: Ethereum Mainnet")
            logger.info(f"Balance: {balance_mainnet_eth} ETH")
            logger.info("This is where your real ETH would be if you sent it")
        
        # Sepolia Testnet
        sepolia_url = os.getenv("ETHEREUM_RPC_URL")
        if sepolia_url:
            w3_sepolia = Web3(Web3.HTTPProvider(sepolia_url))
            if w3_sepolia.is_connected():
                balance_sepolia = w3_sepolia.eth.get_balance(address)
                balance_sepolia_eth = w3_sepolia.from_wei(balance_sepolia, 'ether')
                logger.info("\nSepolia Testnet (Test ETH):")
                logger.info(f"Network: Sepolia Testnet")
                logger.info(f"Balance: {balance_sepolia_eth} ETH")
                logger.info("This is where you need test ETH for development")
        
        logger.info("\nImportant Notes:")
        logger.info("1. Mainnet and Testnet are separate networks")
        logger.info("2. Real ETH on mainnet cannot be used on testnet")
        logger.info("3. You need to get test ETH specifically for Sepolia testnet")
        logger.info("4. To get test ETH, use: https://sepoliafaucet.com/")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    check_networks() 