"""
Enhanced DID Registry module for managing agent DIDs, public keys, and reputation
"""

from typing import Dict, Optional, Tuple, List
import logging
import json
from pathlib import Path
from datetime import datetime
import re
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure the data directory exists
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
REGISTRY_PATH = DATA_DIR / "did_registry.json"
REPUTATION_PATH = DATA_DIR / "reputation.json"

class DIDMethod(Enum):
    """Supported DID methods"""
    ETH = "eth"
    ETHR = "ethr"
    # Add more methods as needed

@dataclass
class AgentReputation:
    """Reputation data for an agent"""
    score: float = 0.0  # Reputation score (0-100)
    total_interactions: int = 0  # Total number of interactions
    successful_interactions: int = 0  # Number of successful interactions
    last_updated: str = ""  # ISO format timestamp
    metadata: Dict = None  # Additional metadata

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not self.last_updated:
            self.last_updated = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'AgentReputation':
        return cls(**data)

class DIDRegistry:
    """Enhanced registry for managing agent DIDs, public keys, and reputation"""
    
    # DID validation patterns
    DID_PATTERNS = {
        DIDMethod.ETH: r'^did:eth:0x[a-fA-F0-9]{40}$',
        DIDMethod.ETHR: r'^did:ethr:0x[a-fA-F0-9]{40}$'
    }
    
    def __init__(self):
        self._registry: Dict[str, str] = {}  # DID -> public key
        self._reputation: Dict[str, AgentReputation] = {}  # DID -> reputation
        self._load_registry()
        self._load_reputation()
        logger.info("Initialized Enhanced DID Registry")
    
    def _load_registry(self):
        """Load the registry from file"""
        try:
            if REGISTRY_PATH.exists():
                with open(REGISTRY_PATH, 'r') as f:
                    self._registry = json.load(f)
                logger.info(f"Loaded {len(self._registry)} DIDs from registry")
            else:
                logger.warning(f"Registry file {REGISTRY_PATH} does not exist; starting with empty registry")
        except Exception as e:
            logger.error(f"Error loading registry: {e}")
            self._registry = {}
    
    def _load_reputation(self):
        """Load reputation data from file"""
        try:
            if REPUTATION_PATH.exists():
                with open(REPUTATION_PATH, 'r') as f:
                    data = json.load(f)
                    self._reputation = {
                        did: AgentReputation.from_dict(rep_data)
                        for did, rep_data in data.items()
                    }
                logger.info(f"Loaded reputation data for {len(self._reputation)} agents")
            else:
                logger.warning(f"Reputation file {REPUTATION_PATH} does not exist; starting with empty reputation data")
        except Exception as e:
            logger.error(f"Error loading reputation data: {e}")
            self._reputation = {}
    
    def _save_registry(self):
        """Save the registry to file"""
        try:
            with open(REGISTRY_PATH, 'w') as f:
                json.dump(self._registry, f, indent=2)
            logger.info(f"Saved {len(self._registry)} DIDs to registry")
        except Exception as e:
            logger.error(f"Error saving registry: {e}")
    
    def _save_reputation(self):
        """Save reputation data to file"""
        try:
            with open(REPUTATION_PATH, 'w') as f:
                json.dump(
                    {did: rep.to_dict() for did, rep in self._reputation.items()},
                    f, indent=2
                )
            logger.info(f"Saved reputation data for {len(self._reputation)} agents")
        except Exception as e:
            logger.error(f"Error saving reputation data: {e}")
    
    def validate_did(self, did: str) -> Tuple[bool, Optional[DIDMethod]]:
        """Validate DID format and return the method if valid"""
        for method, pattern in self.DID_PATTERNS.items():
            if re.match(pattern, did):
                return True, method
        return False, None
    
    def normalize_did(self, did: str) -> str:
        """Normalize DID to did:eth: format"""
        return did.replace("did:ethr:", "did:eth:")
    
    def register(self, did: str, public_key: str) -> bool:
        """Register a new DID with its public key"""
        try:
            # Validate DID format
            is_valid, method = self.validate_did(did)
            if not is_valid:
                logger.error(f"Invalid DID format: {did}")
                return False
            
            # Normalize DID
            normalized_did = self.normalize_did(did)
            
            # Check if already registered
            if normalized_did in self._registry:
                logger.warning(f"DID {did} already registered")
                return False
            
            # Register DID and initialize reputation
            self._registry[normalized_did] = public_key
            self._reputation[normalized_did] = AgentReputation()
            
            # Save changes
            self._save_registry()
            self._save_reputation()
            
            logger.info(f"Registered DID: {did} (normalized: {normalized_did})")
            return True
            
        except Exception as e:
            logger.error(f"Error registering DID {did}: {str(e)}")
            return False
    
    def get(self, did: str) -> Optional[str]:
        """Get the public key for a DID"""
        try:
            # Validate DID format
            is_valid, _ = self.validate_did(did)
            if not is_valid:
                logger.error(f"Invalid DID format: {did}")
                return None
            
            # Normalize and retrieve
            normalized_did = self.normalize_did(did)
            public_key = self._registry.get(normalized_did)
            
            if public_key is None:
                logger.warning(f"DID {did} not found in registry")
            
            return public_key
            
        except Exception as e:
            logger.error(f"Error retrieving DID {did}: {str(e)}")
            return None
    
    def get_private_key(self, did: str) -> Optional[str]:
        """Get or generate a private key for a DID (for demo purposes)"""
        try:
            # Validate DID format
            is_valid, _ = self.validate_did(did)
            if not is_valid:
                logger.error(f"Invalid DID format: {did}")
                return None
            
            # Normalize DID
            normalized_did = self.normalize_did(did)
            
            # For demo purposes, generate a deterministic private key based on the DID
            # In production, this should be stored securely
            import hashlib
            hash_obj = hashlib.sha256(normalized_did.encode())
            private_key = "0x" + hash_obj.hexdigest()[:64]  # 32 bytes = 64 hex chars
            
            logger.info(f"Generated private key for DID: {did}")
            return private_key
            
        except Exception as e:
            logger.error(f"Error generating private key for DID {did}: {str(e)}")
            return None
    
    def get_reputation(self, did: str) -> Optional[AgentReputation]:
        """Get reputation data for a DID"""
        try:
            normalized_did = self.normalize_did(did)
            return self._reputation.get(normalized_did)
        except Exception as e:
            logger.error(f"Error retrieving reputation for DID {did}: {str(e)}")
            return None
    
    def update_reputation(self, did: str, success: bool, metadata: Dict = None) -> bool:
        """Update reputation for a DID based on interaction outcome"""
        try:
            normalized_did = self.normalize_did(did)
            if normalized_did not in self._reputation:
                logger.warning(f"No reputation data found for DID {did}")
                return False
            
            rep = self._reputation[normalized_did]
            rep.total_interactions += 1
            if success:
                rep.successful_interactions += 1
            
            # Update score (simple success rate for now)
            rep.score = (rep.successful_interactions / rep.total_interactions) * 100
            
            # Update metadata
            if metadata:
                rep.metadata.update(metadata)
            
            rep.last_updated = datetime.utcnow().isoformat()
            
            self._save_reputation()
            logger.info(f"Updated reputation for DID {did}: score={rep.score:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating reputation for DID {did}: {str(e)}")
            return False
    
    def remove(self, did: str) -> bool:
        """Remove a DID from the registry"""
        try:
            normalized_did = self.normalize_did(did)
            
            if normalized_did not in self._registry:
                logger.warning(f"DID {did} not found in registry")
                return False
            
            # Remove from both registry and reputation
            del self._registry[normalized_did]
            if normalized_did in self._reputation:
                del self._reputation[normalized_did]
            
            self._save_registry()
            self._save_reputation()
            
            logger.info(f"Removed DID: {did}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing DID {did}: {str(e)}")
            return False
    
    def list_all(self) -> Dict[str, Dict]:
        """Get all registered DIDs with their public keys and reputation"""
        return {
            did: {
                "public_key": self._registry[did],
                "reputation": self._reputation.get(did, AgentReputation()).to_dict()
            }
            for did in self._registry
        }

# Create a singleton instance
did_registry = DIDRegistry()

# Export the class and types for type hints and direct usage
__all__ = ['DIDRegistry', 'DIDMethod', 'AgentReputation', 'did_registry'] 