"""
Script to register existing agents in the blockchain registry
"""

import json
import logging
import sys
import os
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
from backend.blockchain.agent_registry import agent_registry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_agents():
    """Register existing agents in the blockchain registry"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Load existing agent DIDs from the JSON registry
        with open("data/did_registry.json", "r") as f:
            json_registry = json.load(f)
        
        logger.info("Found existing agents in JSON registry:")
        for did, data in json_registry.items():
            logger.info(f"  - {did}")
        
        # Register each agent in the blockchain registry
        for did, public_key in json_registry.items():
            try:
                # Prepare metadata
                metadata = {
                    "source": "migration",
                    "original_registry": "json",
                    "registration_date": "2024-12-20",
                    "agent_type": "trading_agent"
                }
                
                # Register agent
                logger.info(f"\nRegistering agent {did}...")
                tx_hash = agent_registry.register_agent(
                    did=did,
                    public_key=public_key,
                    metadata=metadata
                )
                
                logger.info(f"✅ Successfully registered {did}")
                logger.info(f"Transaction hash: {tx_hash}")
                
                # Wait for transaction confirmation
                logger.info("Waiting for transaction confirmation...")
                w3 = Web3(Web3.HTTPProvider(os.getenv("ETHEREUM_RPC_URL")))
                tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                logger.info(f"Transaction confirmed in block {tx_receipt.blockNumber}")
                
            except Exception as e:
                logger.error(f"Error registering agent {did}: {str(e)}")
                continue
        
        logger.info("\nAgent registration completed!")
        logger.info("You can now update the backend to use the blockchain registry")
        
    except Exception as e:
        logger.error(f"Error in registration process: {str(e)}")
        raise

if __name__ == "__main__":
    register_agents() 