import jwt
import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# (You can later load your private key from a file or env var.)
# For demo purposes, a dummy private key (in PEM format) is used.
# In production, use a secure key (e.g. generated via openssl).
_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj
MzEfYyjiWA4R4/M2bS1GB4t7NXp98C3SC6dVMvDuictGeurT8jNbvJZHtCSuYEvu
NMoSfm76oqFvAp8Gy0iz5sxjZmSnXyCdPEovGhLa0VzMaQ8s+CLOyS56YyCFGeJZ
vRrZvB9IhxrJ3VxJxw+QxKJxJw==
-----END PRIVATE KEY-----"""

def generate_test_jwt(did: str, private_key: str = _PRIVATE_KEY, algorithm: str = "RS256") -> str:
    """
    Generate a test JWT for a given DID (using a dummy private key).
    The payload includes a 'sub' claim equal to the DID and an 'iat' (issued at) claim.
    (For production, use a secure private key.)
    """
    payload = {"sub": did, "iat": jwt.utils.timegm(jwt.utils.datetime_to_timestamp(datetime.datetime.utcnow()))}
    return jwt.encode(payload, private_key, algorithm=algorithm)

def verify_jwt(token: str, public_key: str) -> Dict[str, Any]:
    """Verify a JWT token using the provided public key.
    
    Args:
        token (str): The JWT token to verify
        public_key (str): The public key to use for verification
        
    Returns:
        Dict[str, Any]: The decoded token payload if verification succeeds
        
    Raises:
        jwt.InvalidTokenError: If the token is invalid or verification fails
        Exception: For other errors during verification
    """
    try:
        # Verify and decode the token
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=["ES256"],  # Using ECDSA with SHA-256
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "require": ["exp", "iat", "sub"]  # Required claims
            }
        )
        
        return decoded
        
    except jwt.ExpiredSignatureError:
        logger.error("JWT token has expired")
        raise
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid JWT token: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error verifying JWT token: {str(e)}")
        raise

if __name__ == "__main__":
    # Example usage (for testing)
    did = "did:example:123456789abcdefghi"
    token = generate_test_jwt(did)
    print("Generated JWT (for testing):", token) 