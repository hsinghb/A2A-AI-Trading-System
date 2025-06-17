from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import jwt
from datetime import datetime
import os
from dotenv import load_dotenv
import redis
import logging
import json
from backend.did_registry import did_registry
from backend.eth_jwt_utils import verify_jwt_with_ethereum_key, sign_jwt_with_ethereum_key, create_jwt_payload

load_dotenv()

logger = logging.getLogger(__name__)

class AgentMessage:
    """Structured message format for agent communication"""
    def __init__(
        self,
        message_type: str,
        content: Dict[str, Any],
        sender_did: str,
        recipient_did: str,
        token: str,
        timestamp: Optional[str] = None
    ):
        self.type = message_type
        self.content = content
        self.sender_did = sender_did
        self.recipient_did = recipient_did
        self.token = token
        self.timestamp = timestamp or datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "content": self.content,
            "sender_did": self.sender_did,
            "recipient_did": self.recipient_did,
            "token": self.token,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        return cls(
            message_type=data["type"],
            content=data["content"],
            sender_did=data["sender_did"],
            recipient_did=data["recipient_did"],
            token=data["token"],
            timestamp=data.get("timestamp")
        )

class BaseAgent(ABC):
    def __init__(self, did: str, name: str):
        self.did = did
        self.name = name
        self.jwt_secret = os.getenv('JWT_SECRET')
        # Session-based verification state: {ask_id: {did: {verified: bool, public_key: str}}}
        self.verified_sessions: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.redis_url = os.getenv('REDIS_URL')
        self.redis_client = None
        if self.redis_url:
            self.redis_client = redis.Redis.from_url(self.redis_url)
        logger.info(f"Initialized {name} with DID: {did}")
    
    async def verify_agent(self, ask_id: str, did: str, token: str, public_key: str, algorithm: str = 'ES256K') -> Dict[str, Any]:
        """Verify another agent's DID/JWT using the provided public key."""
        try:
            logger.info(f"[{self.name}] Verifying agent: did={did}, token={token[:10]}..., public_key={public_key[:10] if public_key else 'None'}...")
            
            # Normalize DID format for registry lookup
            normalized_did = did.replace('did:ethr:', 'did:eth:')
            
            # Get actual public key from registry if DID was provided
            if public_key.startswith('did:'):
                sender_normalized_did = public_key.replace('did:ethr:', 'did:eth:')
                actual_public_key = did_registry.get(sender_normalized_did)
                if not actual_public_key:
                    logger.error(f"[{self.name}] No public key found for DID: {public_key}")
                    return {"verified": False, "message": "No public key found for DID"}
                public_key = actual_public_key
            
            # Verify token with public key
            try:
                verified_data = await self.verify_token(token, public_key, algorithm=algorithm)
                logger.info(f"[{self.name}] Token verified successfully: {verified_data}")
                
                # Check if token DID matches provided DID
                token_did = verified_data.get('sub')  # JWT subject is the DID
                if token_did != did:
                    logger.error(f"[{self.name}] Token DID mismatch: token_did={token_did}, provided_did={did}")
                    return {"verified": False, "message": "Token DID mismatch"}
                
                # Store verification state with public key
                verification_state = {
                    "verified": True,
                    "public_key": public_key,
                    "verified_at": datetime.utcnow().isoformat()
                }
                
                if self.redis_client:
                    self.redis_client.setex(
                        f"session:{ask_id}:{normalized_did}",
                        3600,  # 1 hour expiry
                        json.dumps(verification_state)
                    )
                else:
                    if ask_id not in self.verified_sessions:
                        self.verified_sessions[ask_id] = {}
                    self.verified_sessions[ask_id][normalized_did] = verification_state
                
                return {"verified": True, "data": verified_data}
                
            except Exception as e:
                logger.error(f"[{self.name}] Token verification failed: {str(e)}")
                return {"verified": False, "message": str(e)}
                
        except Exception as e:
            logger.error(f"[{self.name}] Agent verification failed: {str(e)}")
            return {"verified": False, "message": str(e)}
    
    def is_verified(self, ask_id: str, did: str) -> bool:
        """Check if a DID is verified for a given ask/session."""
        normalized_did = did.replace('did:ethr:', 'did:eth:')
        if self.redis_client:
            state = self.redis_client.get(f"session:{ask_id}:{normalized_did}")
            if state:
                verification_state = json.loads(state)
                return verification_state.get("verified", False)
            return False
        return self.verified_sessions.get(ask_id, {}).get(normalized_did, {}).get("verified", False)
    
    def get_verified_public_key(self, ask_id: str, did: str) -> Optional[str]:
        """Get the public key used for verification of a DID in a session."""
        normalized_did = did.replace('did:ethr:', 'did:eth:')
        if self.redis_client:
            state = self.redis_client.get(f"session:{ask_id}:{normalized_did}")
            if state:
                try:
                    verification_state = json.loads(state)
                    if isinstance(verification_state, dict):
                        return verification_state.get("public_key")
                    else:
                        # If it's just a boolean, we don't have the public key stored
                        return None
                except (json.JSONDecodeError, TypeError):
                    return None
            return None
        
        # For in-memory storage
        session_data = self.verified_sessions.get(ask_id, {}).get(normalized_did)
        if isinstance(session_data, dict):
            return session_data.get("public_key")
        else:
            # If it's just a boolean, we don't have the public key stored
            return None
    
    def end_ask(self, ask_id: str):
        """Clear verification state for a completed ask/session."""
        if self.redis_client:
            # Remove all DIDs for this ask_id
            keys = self.redis_client.keys(f"session:{ask_id}:*")
            if keys:
                self.redis_client.delete(*keys)
        else:
            if ask_id in self.verified_sessions:
                del self.verified_sessions[ask_id]
    
    async def verify_token(self, token: str, public_key: Optional[str] = None, algorithm: str = 'ES256K') -> Dict[str, Any]:
        """Verify a JWT token using the provided public key."""
        try:
            logger.info(f"[{self.name}] Verifying token with algorithm={algorithm}, public_key={public_key[:10] if public_key else 'None'}...")
            
            if not public_key:
                raise ValueError("No verification key provided")
            
            # Use Ethereum JWT verification for ES256K algorithm
            if algorithm == 'ES256K':
                # For Ethereum JWT verification, we need the expected DID
                # Extract DID from the token or use a default
                try:
                    # Try to decode the token to get the subject (DID)
                    import base64
                    import json
                    parts = token.split('.')
                    if len(parts) >= 2:
                        payload_encoded = parts[1]
                        # Add padding if needed
                        payload_encoded += '=' * (4 - len(payload_encoded) % 4)
                        payload = json.loads(base64.urlsafe_b64decode(payload_encoded))
                        expected_did = payload.get('sub', '')
                    else:
                        expected_did = self.did  # Fallback to own DID
                    
                    # Use Ethereum JWT verification
                    verified_data = verify_jwt_with_ethereum_key(token, expected_did, public_key)
                    logger.info(f"[{self.name}] Ethereum JWT token verified successfully")
                    return verified_data
                    
                except Exception as e:
                    logger.error(f"[{self.name}] Ethereum JWT verification failed: {str(e)}")
                    raise ValueError(f"Ethereum JWT verification failed: {str(e)}")
            else:
                # Fallback to standard JWT for other algorithms
                try:
                    decoded = jwt.decode(token, public_key, algorithms=[algorithm])
                    logger.info(f"[{self.name}] Standard JWT token verified successfully")
                    return decoded
                except jwt.InvalidSignatureError as e:
                    logger.error(f"[{self.name}] Invalid signature: {str(e)}")
                    raise ValueError(f"Invalid signature: {str(e)}")
                except jwt.ExpiredSignatureError as e:
                    logger.error(f"[{self.name}] Token expired: {str(e)}")
                    raise ValueError(f"Token expired: {str(e)}")
                except jwt.InvalidTokenError as e:
                    logger.error(f"[{self.name}] Invalid token: {str(e)}")
                    raise ValueError(f"Invalid token: {str(e)}")
                
        except Exception as e:
            logger.error(f"[{self.name}] Error verifying token: {str(e)}")
            raise ValueError(f"Error verifying token: {str(e)}")
    
    async def create_token(self, recipient_did: str, message_type: str, payload: Optional[Dict[str, Any]] = None) -> str:
        """Create a JWT token for agent-to-agent communication."""
        try:
            # Get private key from registry
            normalized_did = self.did.replace('did:ethr:', 'did:eth:')
            private_key = did_registry.get_private_key(normalized_did)
            if not private_key:
                raise ValueError(f"No private key found for DID: {self.did}")
            
            # Create base payload
            base_payload = {
                "sub": self.did,
                "aud": recipient_did,
                "iat": int(datetime.utcnow().timestamp()),
                "exp": int(datetime.utcnow().timestamp()) + 3600,  # 1 hour expiration
                "role": "agent",
                "type": message_type
            }
            
            # Merge with additional payload if provided
            if payload:
                base_payload.update(payload)
            
            # Use custom Ethereum JWT signing instead of standard JWT
            token = sign_jwt_with_ethereum_key(base_payload, private_key)
            return token
            
        except Exception as e:
            logger.error(f"[{self.name}] Error creating token: {str(e)}")
            raise
    
    def get_credentials(self) -> Dict[str, Any]:
        """Get agent's verifiable credentials."""
        normalized_did = self.did.replace('did:ethr:', 'did:eth:')
        public_key = did_registry.get(normalized_did)
        return {
            'did': self.did,
            'name': self.name,
            'type': self.__class__.__name__,
            'public_key': public_key,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    @abstractmethod
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming messages. To be implemented by specific agents."""
        pass

    async def send_message(self, recipient_did: str, message: AgentMessage) -> Dict[str, Any]:
        """Send a message to another agent"""
        try:
            # Create token for this message
            token = await self.create_token(recipient_did, message.type)
            message.token = token

            # Get recipient agent from registry
            recipient = did_registry.get_agent(recipient_did)
            if not recipient:
                raise ValueError(f"Recipient agent not found: {recipient_did}")

            # Send message to recipient
            response = await recipient.handle_message(message)
            return response

        except Exception as e:
            logger.error(f"[{self.name}] Error sending message: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def handle_message(self, message: AgentMessage) -> Dict[str, Any]:
        """Handle incoming messages - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement handle_message")

    async def process_trading_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process trading requests - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement process_trading_request") 