"""
Script to update .env file with the deployed contract address
"""

import os
import logging
from dotenv import load_dotenv, set_key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_contract_address():
    """Update .env file with the deployed contract address"""
    try:
        # Load current .env
        load_dotenv()
        
        # Get contract address from deployed_address.txt
        with open("contracts/deployed_address.txt", "r") as f:
            contract_address = f.read().strip()
        
        # Update .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        set_key(env_path, "AGENT_REGISTRY_ADDRESS", contract_address)
        
        logger.info("Updated .env file with contract address:")
        logger.info(f"AGENT_REGISTRY_ADDRESS={contract_address}")
        
        # Verify the update
        load_dotenv(override=True)  # Reload with override
        if os.getenv("AGENT_REGISTRY_ADDRESS") == contract_address:
            logger.info("✅ Verification successful!")
        else:
            logger.error("❌ Verification failed!")
        
    except Exception as e:
        logger.error(f"Error updating .env file: {str(e)}")
        raise

if __name__ == "__main__":
    update_contract_address() 