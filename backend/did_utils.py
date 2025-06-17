from eth_account import Account
from eth_keys import keys
import requests
from typing import Dict, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get backend URL from environment variable or use default
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def generate_did() -> Optional[Dict]:
    """Generate a new Ethereum account and return its DID information."""
    try:
        # Create a new Ethereum account
        account = Account.create()
        
        # Get the private key as hex string
        private_key = account.key.hex()
        
        # Get the public key
        public_key = keys.PrivateKey(bytes.fromhex(private_key)).public_key.to_hex()
        
        # Get the Ethereum address
        address = account.address
        
        # Create a DID (using the Ethereum address as the identifier)
        did = f"did:ethr:{address}"
        
        return {
            "did": did,
            "address": address,
            "public_key": public_key,
            "private_key": private_key
        }
    except Exception as e:
        print(f"Error generating DID: {e}")
        return None

def register_did(did: str, public_key: str, agent_type: str) -> bool:
    """Register a DID with the backend."""
    try:
        # Prepare the registration request
        registration_data = {
            "did": did,
            "public_key": public_key,
            "agent_type": agent_type
        }
        
        # Send registration request to backend
        response = requests.post(
            f"{BACKEND_URL}/register-did",
            json=registration_data
        )
        
        # Check if registration was successful
        if response.status_code == 200:
            return True
        else:
            print(f"Registration failed: {response.text}")
            return False
    except Exception as e:
        print(f"Error registering DID: {e}")
        return False

def verify_did(did: str, jwt: str) -> bool:
    """Verify a DID's JWT with the backend."""
    try:
        # Prepare the verification request
        verification_data = {
            "did": did,
            "jwt": jwt
        }
        
        # Send verification request to backend
        response = requests.post(
            f"{BACKEND_URL}/verify-did",
            json=verification_data
        )
        
        # Check if verification was successful
        if response.status_code == 200:
            return True
        else:
            print(f"Verification failed: {response.text}")
            return False
    except Exception as e:
        print(f"Error verifying DID: {e}")
        return False

def get_did_info(did: str) -> Optional[Dict]:
    """Get information about a registered DID from the backend."""
    try:
        # Send request to backend
        response = requests.get(f"{BACKEND_URL}/did-info/{did}")
        
        # Check if request was successful
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get DID info: {response.text}")
            return None
    except Exception as e:
        print(f"Error getting DID info: {e}")
        return None 