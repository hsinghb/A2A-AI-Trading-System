"""
Script to list all registered agent DIDs (on-chain) using backend.blockchain.agent_registry.
"""

import sys
import os
from pathlib import Path

# Add the project root directory to the Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

import logging
from backend.blockchain.agent_registry import agent_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        # This assumes your agent_registry has a method called list_agents()
        agents = agent_registry.list_agents()
        logger.info("Registered agent DIDs (on-chain): %s", agents)
        print("Registered agent DIDs (on-chain):")
        for did in agents:
            print(did)
    except Exception as e:
        logger.error("Error listing on-chain agents: %s", e)
        print("Error listing on-chain agents:", e)
