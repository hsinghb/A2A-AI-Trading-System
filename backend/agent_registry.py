"""
Agent Registry module for managing agent registration and trust relationships
"""

from typing import Dict, Set, Optional
import logging
import json
from pathlib import Path
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure the data directory exists
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
REGISTRY_PATH = DATA_DIR / "agent_registry.json"

class AgentRole(Enum):
    ORCHESTRATOR = "orchestrator"
    EXPERT = "expert"
    RISK = "risk"
    HUMAN = "human"

class AgentRegistry:
    """Registry for managing agent registration and trust relationships"""
    
    def __init__(self):
        self._registry: Dict[str, Dict] = {}  # DID -> Agent info
        self._trust_relationships: Dict[str, Set[str]] = {}  # DID -> Set of trusted DIDs
        self._load_registry()
        logger.info("Initialized Agent Registry")
    
    def _load_registry(self):
        """Load the registry from file"""
        try:
            if REGISTRY_PATH.exists():
                with open(REGISTRY_PATH, 'r') as f:
                    data = json.load(f)
                    self._registry = data.get('agents', {})
                    self._trust_relationships = {
                        did: set(trusted) 
                        for did, trusted in data.get('trust', {}).items()
                    }
                logger.info(f"Loaded {len(self._registry)} agents from registry")
            else:
                logger.warning(f"Registry file {REGISTRY_PATH} does not exist; starting with empty registry")
        except Exception as e:
            logger.error(f"Error loading registry: {e}")
            self._registry = {}
            self._trust_relationships = {}
    
    def _save_registry(self):
        """Save the registry to file"""
        try:
            data = {
                'agents': self._registry,
                'trust': {
                    did: list(trusted) 
                    for did, trusted in self._trust_relationships.items()
                }
            }
            with open(REGISTRY_PATH, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self._registry)} agents to registry")
        except Exception as e:
            logger.error(f"Error saving registry: {e}")
    
    def register_agent(self, did: str, role: AgentRole, public_key: str) -> bool:
        """Register a new agent with its role and public key"""
        try:
            if did in self._registry:
                logger.warning(f"Agent {did} already registered")
                return False
                
            self._registry[did] = {
                'role': role.value,
                'public_key': public_key,
                'capabilities': self._get_default_capabilities(role)
            }
            self._trust_relationships[did] = set()
            self._save_registry()
            logger.info(f"Registered agent {did} with role {role.value}")
            return True
        except Exception as e:
            logger.error(f"Error registering agent {did}: {e}")
            return False
    
    def _get_default_capabilities(self, role: AgentRole) -> Dict:
        """Get default capabilities for an agent role"""
        if role == AgentRole.ORCHESTRATOR:
            return {
                'can_verify': True,
                'can_create_tokens': True,
                'can_communicate_with': ['expert', 'risk', 'human']
            }
        elif role == AgentRole.EXPERT:
            return {
                'can_verify': True,
                'can_create_tokens': False,
                'can_communicate_with': ['orchestrator', 'risk']
            }
        elif role == AgentRole.RISK:
            return {
                'can_verify': True,
                'can_create_tokens': False,
                'can_communicate_with': ['orchestrator', 'expert']
            }
        elif role == AgentRole.HUMAN:
            return {
                'can_verify': False,
                'can_create_tokens': False,
                'can_communicate_with': ['orchestrator']
            }
        return {}
    
    def add_trust_relationship(self, from_did: str, to_did: str) -> bool:
        """Add a trust relationship between agents"""
        try:
            if from_did not in self._registry or to_did not in self._registry:
                logger.warning(f"One or both agents not registered: {from_did}, {to_did}")
                return False
                
            if from_did not in self._trust_relationships:
                self._trust_relationships[from_did] = set()
                
            self._trust_relationships[from_did].add(to_did)
            self._save_registry()
            logger.info(f"Added trust relationship: {from_did} -> {to_did}")
            return True
        except Exception as e:
            logger.error(f"Error adding trust relationship: {e}")
            return False
    
    def can_communicate(self, from_did: str, to_did: str) -> bool:
        """Check if two agents can communicate"""
        try:
            if from_did not in self._registry or to_did not in self._registry:
                return False
                
            from_role = self._registry[from_did]['role']
            to_role = self._registry[to_did]['role']
            
            # Check if roles are allowed to communicate
            from_capabilities = self._registry[from_did]['capabilities']
            if to_role not in from_capabilities['can_communicate_with']:
                return False
                
            # Check trust relationship
            return to_did in self._trust_relationships.get(from_did, set())
        except Exception as e:
            logger.error(f"Error checking communication permission: {e}")
            return False
    
    def get_agent_info(self, did: str) -> Optional[Dict]:
        """Get agent information"""
        return self._registry.get(did)
    
    def get_trusted_agents(self, did: str) -> Set[str]:
        """Get all agents trusted by a given agent"""
        return self._trust_relationships.get(did, set())
    
    def list_all_agents(self) -> Dict[str, Dict]:
        """Get all registered agents"""
        return dict(self._registry)

# Create a singleton instance
agent_registry = AgentRegistry()

# Export the class and instance
__all__ = ['AgentRegistry', 'agent_registry', 'AgentRole'] 