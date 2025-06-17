"""
Script to help request test ETH from multiple faucets
"""

import os
import logging
import webbrowser
from web3 import Web3
from dotenv import load_dotenv
from eth_account import Account

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def request_test_eth():
    """Help request test ETH from multiple faucets"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get account address
        private_key = os.getenv("ADMIN_PRIVATE_KEY")
        if not private_key:
            raise ValueError("ADMIN_PRIVATE_KEY not found in .env file")
        
        account = Account.from_key(private_key)
        address = account.address
        
        logger.info(f"Your address: {address}")
        logger.info("\nRequesting test ETH from multiple faucets...")
        
        # List of faucets with their URLs
        faucets = [
            {
                "name": "Alchemy Sepolia Faucet",
                "url": f"https://sepoliafaucet.com/?address={address}",
                "description": "Most reliable, requires Alchemy account"
            },
            {
                "name": "Sepolia Official Faucet",
                "url": f"https://faucet.sepolia.dev/?address={address}",
                "description": "Official faucet, requires GitHub account"
            },
            {
                "name": "Community Faucet",
                "url": f"https://sepolia-faucet.pk910.de/?address={address}",
                "description": "Community faucet, requires solving captcha"
            }
        ]
        
        # Print faucet information
        logger.info("\nAvailable faucets:")
        for i, faucet in enumerate(faucets, 1):
            logger.info(f"\n{i}. {faucet['name']}")
            logger.info(f"   Description: {faucet['description']}")
            logger.info(f"   URL: {faucet['url']}")
        
        # Ask which faucet to use
        choice = input("\nEnter the number of the faucet you want to use (1-3): ")
        try:
            choice = int(choice)
            if 1 <= choice <= len(faucets):
                selected_faucet = faucets[choice - 1]
                logger.info(f"\nOpening {selected_faucet['name']}...")
                webbrowser.open(selected_faucet['url'])
                
                logger.info("\nAfter requesting ETH:")
                logger.info("1. Wait a few minutes for the transaction to be confirmed")
                logger.info("2. Run: python scripts/monitor_balance.py")
                logger.info("3. Once you see a balance > 0.01 ETH, run: python scripts/deploy_registry.py")
            else:
                logger.error("Invalid choice. Please enter a number between 1 and 3.")
        except ValueError:
            logger.error("Please enter a valid number.")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    request_test_eth() 