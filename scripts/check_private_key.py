"""
Script to validate private key format
"""

import os
import logging
from dotenv import load_dotenv
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_private_key():
    """Validate the private key format in .env file"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get private key
        private_key = os.getenv("ADMIN_PRIVATE_KEY")
        if not private_key:
            raise ValueError("ADMIN_PRIVATE_KEY not found in .env file")
        
        # Remove '0x' prefix if present
        if private_key.startswith('0x'):
            private_key = private_key[2:]
        
        # Check length (should be 64 hex characters)
        if len(private_key) != 64:
            logger.error(f"Private key should be 64 characters long (got {len(private_key)})")
            return False
        
        # Check if it's valid hexadecimal
        if not re.match('^[0-9a-fA-F]+$', private_key):
            logger.error("Private key contains non-hexadecimal characters")
            return False
        
        logger.info("Private key format is valid!")
        logger.info("Make sure to update your .env file with this format (without 0x prefix):")
        logger.info(f"ADMIN_PRIVATE_KEY={private_key}")
        return True
        
    except Exception as e:
        logger.error(f"Error validating private key: {str(e)}")
        return False

if __name__ == "__main__":
    validate_private_key() 