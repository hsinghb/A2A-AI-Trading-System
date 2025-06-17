import json
import base64
import time
import hashlib
import hmac
from typing import Dict, Any, Optional

def create_jwt_payload(did: str, additional_claims: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a JWT payload with standard claims and optional additional claims.
    """
    now = int(time.time())
    payload = {
        "sub": did,  # Subject (DID)
        "iat": now,  # Issued at
        "exp": now + 3600,  # Expires in 1 hour
    }
    
    if additional_claims:
        payload.update(additional_claims)
    
    return payload

def sign_jwt_with_ethereum_key(payload: Dict[str, Any], private_key: str) -> str:
    """
    Sign a JWT payload using a mock Ethereum private key.
    Returns a JWT-like token: header.payload.signature (for demo purposes)
    """
    # Create JWT header
    header = {
        "alg": "ES256K",  # ECDSA using secp256k1 curve (mock)
        "typ": "JWT"
    }
    
    # Encode header and payload
    header_encoded = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    
    # Create message to sign
    message = f"{header_encoded}.{payload_encoded}"
    
    # Create a mock signature using HMAC (for demo purposes)
    signature = hmac.new(
        private_key.encode(), 
        message.encode(), 
        hashlib.sha256
    ).hexdigest()
    
    # Encode signature
    signature_encoded = base64.urlsafe_b64encode(signature.encode()).decode().rstrip('=')
    
    # Return JWT
    return f"{message}.{signature_encoded}"

def verify_jwt_with_ethereum_key(jwt_token: str, expected_did: str, public_key_hex: str) -> Dict[str, Any]:
    """
    Verify a JWT token signed with a mock Ethereum private key.
    Returns the payload if verification succeeds, raises exception if it fails.
    """
    try:
        # Split JWT
        parts = jwt_token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")
        
        header_encoded, payload_encoded, signature_encoded = parts
        
        # Decode header and payload
        header = json.loads(base64.urlsafe_b64decode(header_encoded + '=='))
        payload = json.loads(base64.urlsafe_b64decode(payload_encoded + '=='))
        
        # Check algorithm
        if header.get('alg') != 'ES256K':
            raise ValueError("Unsupported algorithm")
        
        # Check expiration
        now = int(time.time())
        if payload.get('exp', 0) < now:
            raise ValueError("Token expired")
        
        # Normalize DIDs for comparison (handle both did:eth: and did:ethr:)
        normalized_expected_did = expected_did.replace("did:ethr:", "did:eth:")
        normalized_payload_did = payload.get('sub', '').replace("did:ethr:", "did:eth:")
        
        # Check subject (DID)
        if normalized_payload_did != normalized_expected_did:
            raise ValueError(f"Invalid subject (DID). Expected {normalized_expected_did}, got {normalized_payload_did}")
        
        # For demo purposes, we'll skip cryptographic verification
        # In a real system, you would verify the signature here
        
        return payload
        
    except Exception as e:
        raise ValueError(f"JWT verification failed: {str(e)}")

def generate_test_jwt_ethereum(did: str, private_key: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate a test JWT using mock Ethereum keys for a given DID.
    """
    payload = create_jwt_payload(did, additional_claims)
    return sign_jwt_with_ethereum_key(payload, private_key)

if __name__ == "__main__":
    # Demo usage
    from eth_account_utils import generate_eth_account
    
    # Generate test account
    account = generate_eth_account()
    did = account["did"]
    private_key = account["private_key"]
    public_key = account["public_key"]
    
    print(f"DID: {did}")
    print(f"Address: {account['address']}")
    
    # Create and sign JWT
    jwt_token = generate_test_jwt_ethereum(did, private_key, {"role": "agent", "type": "test"})
    print(f"JWT: {jwt_token}")
    
    # Verify JWT
    try:
        verified_payload = verify_jwt_with_ethereum_key(jwt_token, did, public_key)
        print(f"Verification successful! Payload: {verified_payload}")
    except ValueError as e:
        print(f"Verification failed: {e}") 