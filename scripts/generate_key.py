"""
Script to generate a valid Ethereum private key and address
"""

import secrets
import logging
from eth_account import Account
from web3 import Web3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_key():
    """Generate a new Ethereum private key and address"""
    try:
        # Generate a random 32-byte (64 hex characters) private key
        private_key = secrets.token_hex(32)
        
        # Create an account from the private key
        account = Account.from_key(private_key)
        address = account.address
        
        logger.info("Generated new Ethereum key pair:")
        logger.info(f"Private Key: {private_key}")
        logger.info(f"Address: {address}")
        
        # Create .env file content
        env_content = f"""# Ethereum RPC URL (e.g., Infura, Alchemy, or local node)
ETHEREUM_RPC_URL=https://sepolia.infura.io/v3/YOUR-PROJECT-ID

# Admin private key (64 hex characters, no 0x prefix)
ADMIN_PRIVATE_KEY={private_key}

# Contract address (will be filled after deployment)
AGENT_REGISTRY_ADDRESS=

# Network ID (11155111 for Sepolia)
NETWORK_ID=11155111
"""
        
        logger.info("\nCopy this content to your .env file:")
        logger.info("----------------------------------------")
        print(env_content)
        logger.info("----------------------------------------")
        
        logger.info("\nImportant:")
        logger.info("1. Save this private key securely - it cannot be recovered if lost!")
        logger.info("2. This is a test key - never use it for real funds")
        logger.info("3. Get some test ETH from a Sepolia faucet for this address")
        logger.info("4. Replace YOUR-PROJECT-ID with your actual Infura project ID")
        
        return private_key, address
        
    except Exception as e:
        logger.error(f"Error generating key: {str(e)}")
        raise

if __name__ == "__main__":
    generate_key() 