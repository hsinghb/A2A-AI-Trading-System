"""
Python interface for interacting with the AgentRegistry smart contract
"""

from typing import Dict, Any, Optional, Tuple
import json
import logging
from web3 import Web3
from web3.contract import Contract
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from eth_account import Account
from eth_typing import Address
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AgentRegistryContract:
    """Interface for interacting with the AgentRegistry smart contract"""
    
    MIN_ETH_BALANCE = 0.01  # Minimum ETH balance required (in ETH)
    
    def __init__(self):
        """Initialize the contract interface"""
        # Get configuration from environment
        self.rpc_url = os.getenv("ETHEREUM_RPC_URL")
        self.contract_address = os.getenv("AGENT_REGISTRY_ADDRESS")
        self.admin_private_key = os.getenv("ADMIN_PRIVATE_KEY")
        
        # Check each required variable
        missing_vars = []
        if not self.rpc_url:
            missing_vars.append("ETHEREUM_RPC_URL")
        if not self.contract_address:
            missing_vars.append("AGENT_REGISTRY_ADDRESS")
        if not self.admin_private_key:
            missing_vars.append("ADMIN_PRIVATE_KEY")
        
        if missing_vars:
            error_msg = "Missing required environment variables:\n"
            for var in missing_vars:
                error_msg += f"- {var}\n"
            error_msg += "\nPlease ensure these variables are set in your .env file."
            raise ValueError(error_msg)
        
        # Initialize Web3
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            if not self.w3.is_connected():
                raise ConnectionError(f"Failed to connect to Ethereum node at {self.rpc_url}")
            logger.info(f"Connected to Ethereum node at {self.rpc_url}")
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Web3: {str(e)}")
        
        # Add middleware for PoA networks if needed
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        # Load contract ABI
        try:
            contract_path = os.path.join(os.path.dirname(__file__), "contracts", "AgentRegistry.json")
            with open(contract_path, "r") as f:
                contract_json = json.load(f)
                self.contract_abi = contract_json["abi"]
                logger.info(f"Loaded contract ABI with {len(self.contract_abi)} functions")
        except FileNotFoundError:
            raise FileNotFoundError(f"Contract ABI file not found at {contract_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in contract ABI file at {contract_path}")
        
        # Initialize contract
        try:
            self.contract: Contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=self.contract_abi
            )
            logger.info(f"Initialized contract at {self.contract_address}")
            # Verify contract code exists
            code = self.w3.eth.get_code(self.contract_address)
            if not code:
                raise ValueError(f"No contract code found at {self.contract_address}")
            logger.info("Contract code verified")
        except Exception as e:
            raise ValueError(f"Failed to initialize contract at {self.contract_address}: {str(e)}")
        
        # Get admin account
        try:
            self.admin_account = Account.from_key(self.admin_private_key)
            self.admin_address = self.admin_account.address
            # Check admin balance
            balance = self.w3.eth.get_balance(self.admin_address)
            balance_eth = self.w3.from_wei(balance, 'ether')
            logger.info(f"Admin balance: {balance_eth} ETH")
            if balance_eth < self.MIN_ETH_BALANCE:
                logger.warning(f"Admin account has low balance ({balance_eth} ETH). Minimum recommended: {self.MIN_ETH_BALANCE} ETH")
                logger.warning("Please get some Sepolia ETH from a faucet:")
                logger.warning("1. https://sepoliafaucet.com/")
                logger.warning("2. https://www.infura.io/faucet/sepolia")
                logger.warning("3. https://faucet.paradigm.xyz/")
        except Exception as e:
            raise ValueError(f"Invalid admin private key: {str(e)}")
        
        logger.info(f"Initialized AgentRegistry contract interface at {self.contract_address}")
        logger.info(f"Admin address: {self.admin_address}")
    
    def _extract_address_from_did(self, did: str) -> str:
        """Extract Ethereum address from a DID."""
        if not (did.startswith("did:eth:") or did.startswith("did:ethr:")):
            raise ValueError(f"Invalid DID format: {did}")
        
        # Handle both did:eth: and did:ethr: formats
        if did.startswith("did:eth:"):
            address = did.replace("did:eth:", "")
        else:  # did:ethr:
            address = did.replace("did:ethr:", "")
            
        if not self.w3.is_address(address):
            raise ValueError(f"Invalid Ethereum address in DID: {address}")
        return Web3.to_checksum_address(address)
    
    def _get_nonce(self, address: str = None) -> int:
        """Get the current nonce for an address"""
        if address is None:
            address = self.admin_address
        return self.w3.eth.get_transaction_count(address)
    
    def _get_chain_id(self) -> int:
        """Get the current chain ID"""
        try:
            return self.w3.eth.chain_id
        except Exception as e:
            logger.warning(f"Failed to get chain ID, using default for Sepolia (11155111): {str(e)}")
            return 11155111  # Sepolia testnet chain ID
    
    def _get_gas_price(self) -> int:
        """Get the current gas price with a small buffer"""
        try:
            base_gas_price = self.w3.eth.gas_price
            # Add 10% buffer to gas price
            return int(base_gas_price * 1.1)
        except Exception as e:
            logger.warning(f"Failed to get gas price, using default: {str(e)}")
            return 20000000000  # 20 gwei default
    
    def _estimate_gas(self, function, from_address: str) -> int:
        """Estimate gas for a function call"""
        try:
            # Create a transaction dict without data field
            transaction = {
                "from": from_address,
                "to": self.contract_address,
                "value": 0,
                "chainId": self._get_chain_id()
            }
            
            # Get the function data
            data = function._encode_transaction_data()
            
            # Add data to transaction
            transaction["data"] = data
            
            # Estimate gas
            gas_limit = self.w3.eth.estimate_gas(transaction)
            # Add 20% buffer
            return int(gas_limit * 1.2)
        except Exception as e:
            logger.warning(f"Failed to estimate gas, using default: {str(e)}")
            return 2000000  # Default gas limit
    
    def _build_transaction(self, function, from_address: str = None) -> Dict[str, Any]:
        """Build a transaction with current gas price and nonce"""
        if from_address is None:
            from_address = self.admin_address
            
        # Get current gas price
        gas_price = self._get_gas_price()
        
        # Get chain ID
        chain_id = self._get_chain_id()
        
        # Estimate gas
        gas_limit = self._estimate_gas(function, from_address)
        logger.info(f"Estimated gas limit: {gas_limit}")
        
        # Build base transaction
        transaction = {
            "from": from_address,
            "to": self.contract_address,
            "nonce": self._get_nonce(from_address),
            "gasPrice": gas_price,
            "gas": gas_limit,
            "chainId": chain_id,
            "value": 0
        }
        
        # Add function data
        transaction["data"] = function._encode_transaction_data()
        
        return transaction
    
    def _sign_and_send_transaction(self, transaction: Dict[str, Any], private_key: str = None) -> str:
        """Sign and send a transaction"""
        try:
            if private_key is None:
                private_key = self.admin_private_key
            
            # Ensure all required fields are present
            required_fields = ["from", "to", "nonce", "gasPrice", "gas", "chainId", "data"]
            for field in required_fields:
                if field not in transaction:
                    raise ValueError(f"Missing required transaction field: {field}")
            
            # Convert private key to bytes if it's a hex string
            if isinstance(private_key, str) and private_key.startswith("0x"):
                private_key = private_key[2:]
            
            # Sign the transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction,
                private_key
            )
            
            # Send the transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status != 1:
                raise Exception(f"Transaction failed: {receipt.transactionHash.hex()}")
            
            logger.info(f"Transaction confirmed: {receipt.transactionHash.hex()}")
            return receipt.transactionHash.hex()
            
        except Exception as e:
            logger.error(f"Transaction failed: {str(e)}")
            raise
    
    def _check_balance(self) -> bool:
        """Check if admin account has enough ETH for transactions"""
        try:
            balance = self.w3.eth.get_balance(self.admin_address)
            balance_eth = self.w3.from_wei(balance, 'ether')
            min_balance = 0.01  # Minimum 0.01 ETH required
            if balance_eth < min_balance:
                logger.error(f"Insufficient balance: {balance_eth} ETH. Minimum required: {min_balance} ETH")
                logger.error("Please get some Sepolia ETH from a faucet:")
                logger.error("1. https://sepoliafaucet.com/")
                logger.error("2. https://www.infura.io/faucet/sepolia")
                logger.error("3. https://faucet.paradigm.xyz/")
                return False
            return True
        except Exception as e:
            logger.error(f"Failed to check balance: {str(e)}")
            return False
    
    def register_agent(self, did: str, public_key: str, metadata: Dict[str, Any] = None) -> str:
        """Register a new agent in the registry"""
        try:
            # Check balance first
            balance = self.w3.eth.get_balance(self.admin_address)
            balance_eth = self.w3.from_wei(balance, 'ether')
            min_balance = 0.01  # Minimum 0.01 ETH required
            if balance_eth < min_balance:
                error_msg = f"Insufficient balance: {balance_eth} ETH. Minimum required: {min_balance} ETH\n"
                error_msg += "Please get some Sepolia ETH from a faucet:\n"
                error_msg += "1. https://sepoliafaucet.com/\n"
                error_msg += "2. https://www.infura.io/faucet/sepolia\n"
                error_msg += "3. https://faucet.paradigm.xyz/"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            if metadata is None:
                metadata = {}
            
            # Extract Ethereum address from DID
            agent_address = self._extract_address_from_did(did)
            logger.info(f"Registering agent with address: {agent_address}")
            
            # Build the function call
            function = self.contract.functions.registerAgent(
                agent_address,
                public_key,
                json.dumps(metadata)
            )
            
            # Get transaction parameters
            nonce = self.w3.eth.get_transaction_count(self.admin_address)
            gas_price = self.w3.eth.gas_price
            chain_id = self.w3.eth.chain_id
            
            logger.info(f"Transaction parameters - Nonce: {nonce}, Gas Price: {gas_price}, Chain ID: {chain_id}")
            
            # Build transaction
            transaction = {
                'from': self.admin_address,
                'nonce': nonce,
                'gasPrice': gas_price,
                'chainId': chain_id
            }
            
            # Estimate gas
            try:
                gas_estimate = function.estimate_gas(transaction)
                transaction['gas'] = int(gas_estimate * 1.2)  # Add 20% buffer
                logger.info(f"Estimated gas: {transaction['gas']}")
            except Exception as e:
                logger.warning(f"Gas estimation failed, using default: {str(e)}")
                transaction['gas'] = 2000000
            
            # Build the transaction
            built_txn = function.build_transaction(transaction)
            logger.info("Transaction built successfully")
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                built_txn,
                self.admin_private_key
            )
            logger.info("Transaction signed successfully")
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status != 1:
                raise Exception(f"Transaction failed: {receipt.transactionHash.hex()}")
            
            logger.info(f"Transaction confirmed: {receipt.transactionHash.hex()}")
            return receipt.transactionHash.hex()
            
        except Exception as e:
            logger.error(f"Error registering agent {did}: {str(e)}")
            raise
    
    def update_agent(self, did: str, public_key: str, metadata: Dict[str, Any] = None) -> str:
        """Update an existing agent's information."""
        try:
            if metadata is None:
                metadata = {}
            
            # Extract Ethereum address from DID
            agent_address = self._extract_address_from_did(did)
            logger.info(f"Updating agent {did} at address {agent_address}")
            
            # Build transaction
            transaction = self.contract.functions.updateAgent(
                did,
                public_key,
                json.dumps(metadata)
            ).build_transaction(self._build_transaction(self.contract.functions.updateAgent))
            
            tx_hash = self._sign_and_send_transaction(transaction)
            logger.info(f"Updated agent {did} with transaction {tx_hash}")
            return tx_hash
            
        except Exception as e:
            logger.error(f"Error updating agent {did}: {str(e)}")
            raise
    
    def update_reputation(self, agent_address: str, success: bool, metadata: Dict[str, Any] = None) -> str:
        """Update an agent's reputation"""
        try:
            if metadata is None:
                metadata = {}
            
            # Build the function call
            function = self.contract.functions.updateReputation(
                agent_address,
                success,
                json.dumps(metadata)
            )
            
            # Get transaction parameters
            nonce = self.w3.eth.get_transaction_count(self.admin_address)
            gas_price = self.w3.eth.gas_price
            chain_id = self.w3.eth.chain_id
            
            logger.info(f"Transaction parameters - Nonce: {nonce}, Gas Price: {gas_price}, Chain ID: {chain_id}")
            
            # Build transaction
            transaction = {
                'from': self.admin_address,
                'nonce': nonce,
                'gasPrice': gas_price,
                'chainId': chain_id
            }
            
            # Estimate gas
            try:
                gas_estimate = function.estimate_gas(transaction)
                transaction['gas'] = int(gas_estimate * 1.2)  # Add 20% buffer
                logger.info(f"Estimated gas: {transaction['gas']}")
            except Exception as e:
                logger.warning(f"Gas estimation failed, using default: {str(e)}")
                transaction['gas'] = 2000000
            
            # Build the transaction
            built_txn = function.build_transaction(transaction)
            logger.info("Transaction built successfully")
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                built_txn,
                self.admin_private_key
            )
            logger.info("Transaction signed successfully")
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status != 1:
                raise Exception(f"Transaction failed: {receipt.transactionHash.hex()}")
            
            logger.info(f"Transaction confirmed: {receipt.transactionHash.hex()}")
            return receipt.transactionHash.hex()
            
        except Exception as e:
            logger.error(f"Error updating reputation for agent {agent_address}: {str(e)}")
            raise
    
    def deactivate_agent(self, did: str) -> str:
        """Deactivate an agent"""
        try:
            # Build the function call
            function = self.contract.functions.deactivateAgent(did)
            
            # Get transaction parameters
            nonce = self.w3.eth.get_transaction_count(self.admin_address)
            gas_price = self.w3.eth.gas_price
            chain_id = self.w3.eth.chain_id
            
            logger.info(f"Transaction parameters - Nonce: {nonce}, Gas Price: {gas_price}, Chain ID: {chain_id}")
            
            # Build transaction
            transaction = {
                'from': self.admin_address,
                'nonce': nonce,
                'gasPrice': gas_price,
                'chainId': chain_id
            }
            
            # Estimate gas
            try:
                gas_estimate = function.estimate_gas(transaction)
                transaction['gas'] = int(gas_estimate * 1.2)  # Add 20% buffer
                logger.info(f"Estimated gas: {transaction['gas']}")
            except Exception as e:
                logger.warning(f"Gas estimation failed, using default: {str(e)}")
                transaction['gas'] = 2000000
            
            # Build the transaction
            built_txn = function.build_transaction(transaction)
            logger.info("Transaction built successfully")
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                built_txn,
                self.admin_private_key
            )
            logger.info("Transaction signed successfully")
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status != 1:
                raise Exception(f"Transaction failed: {receipt.transactionHash.hex()}")
            
            logger.info(f"Transaction confirmed: {receipt.transactionHash.hex()}")
            return receipt.transactionHash.hex()
            
        except Exception as e:
            logger.error(f"Error deactivating agent {did}: {str(e)}")
            raise
    
    def get_agent(self, did: str) -> Dict[str, Any]:
        """Get agent information"""
        try:
            # Extract Ethereum address from DID
            agent_address = self._extract_address_from_did(did)
            logger.info(f"Getting agent info for address: {agent_address}")
            
            (
                agent_address,
                public_key,
                reputation,
                total_interactions,
                successful_interactions,
                last_updated,
                is_active,
                metadata
            ) = self.contract.functions.getAgent(agent_address).call()
            
            return {
                "agent_address": agent_address,
                "public_key": public_key,
                "reputation": reputation,
                "total_interactions": total_interactions,
                "successful_interactions": successful_interactions,
                "last_updated": last_updated,
                "is_active": is_active,
                "metadata": json.loads(metadata) if metadata else {}
            }
            
        except Exception as e:
            logger.error(f"Error getting agent {did}: {str(e)}")
            raise
    
    def get_admin(self) -> Optional[str]:
        """Get the current admin address."""
        try:
            admin = self.contract.functions.admin().call()
            return admin if admin != "0x0000000000000000000000000000000000000000" else None
        except Exception as e:
            logger.error(f"Failed to get admin: {str(e)}")
            return None
    
    def is_admin(self, address: str) -> bool:
        """Check if an address is the current admin."""
        try:
            current_admin = self.get_admin()
            if not current_admin:
                return False
            return current_admin.lower() == address.lower()
        except Exception as e:
            logger.error(f"Failed to check admin status for {address}: {str(e)}")
            return False
    
    def register_admin(self, address: str, private_key: str) -> str:
        """Register a new admin. Only callable by current admin."""
        try:
            # Get current admin
            current_admin = self.get_admin()
            if current_admin and current_admin.lower() != address.lower():
                raise ValueError(f"Admin already exists: {current_admin}")
            
            # Build transaction
            transaction = self.contract.functions.registerAdmin(
                Web3.to_checksum_address(address)
            ).build_transaction(self._build_transaction(self.contract.functions.registerAdmin, address))
            
            # Sign and send with the provided private key
            tx_hash = self._sign_and_send_transaction(transaction, private_key)
            logger.info(f"Registered admin {address} with transaction {tx_hash}")
            return tx_hash
            
        except Exception as e:
            logger.error(f"Error registering admin {address}: {str(e)}")
            raise
    
    def list_agents(self) -> Dict[str, Any]:
        """List all registered agents. Note: This is a simplified implementation."""
        try:
            # This is a simplified implementation since the contract doesn't have a direct list function
            # In a real implementation, you would need to track agent registrations via events
            logger.warning("list_agents() is a simplified implementation - returns empty list")
            return {}
        except Exception as e:
            logger.error(f"Failed to list agents: {str(e)}")
            return {}

# Export for use in other modules
__all__ = ['AgentRegistryContract']

# Create a singleton instance for use in other modules
try:
    agent_registry = AgentRegistryContract()
    logger.info("Created AgentRegistry instance")
except Exception as e:
    logger.error(f"Failed to create AgentRegistry instance: {str(e)}")
    logger.info("Creating mock AgentRegistry instance for development")
    
    # Create a mock instance for development
    class MockAgentRegistryContract:
        def __init__(self):
            self.logger = logging.getLogger(__name__)
            self.logger.warning("Using MockAgentRegistryContract - blockchain features disabled")
        
        def register_agent(self, did: str, public_key: str, metadata: Dict[str, Any] = None) -> str:
            self.logger.info(f"Mock: Registered agent {did}")
            return "mock_tx_hash_123"
        
        def get_agent(self, did: str) -> Dict[str, Any]:
            self.logger.info(f"Mock: Getting agent {did}")
            # Handle both did:eth: and did:ethr: formats
            if did.startswith("did:eth:"):
                agent_address = did.replace("did:eth:", "")
            else:  # did:ethr:
                agent_address = did.replace("did:ethr:", "")
                
            return {
                "agent_address": agent_address,
                "public_key": "mock_public_key",
                "reputation": 100,
                "total_interactions": 0,
                "successful_interactions": 0,
                "last_updated": 0,
                "is_active": True,
                "metadata": {}
            }
        
        def update_reputation(self, agent_address: str, success: bool, metadata: Dict[str, Any] = None) -> str:
            self.logger.info(f"Mock: Updated reputation for {agent_address}")
            return "mock_tx_hash_456"
        
        def deactivate_agent(self, did: str) -> str:
            self.logger.info(f"Mock: Deactivated agent {did}")
            return "mock_tx_hash_789"
        
        def get_admin(self) -> Optional[str]:
            return "0xb061c3e5D0d182c6743c743fC14eDD4fdbD5c127"
        
        def register_admin(self, address: str, private_key: str) -> str:
            self.logger.info(f"Mock: Registered admin {address}")
            return "mock_tx_hash_admin"
        
        def is_admin(self, address: str) -> bool:
            return address.lower() == "0xb061c3e5D0d182c6743c743fC14eDD4fdbD5c127".lower()
        
        def update_agent(self, did: str, public_key: str, metadata: Dict[str, Any] = None) -> str:
            self.logger.info(f"Mock: Updated agent {did}")
            return "mock_tx_hash_update"
        
        def list_agents(self) -> Dict[str, Any]:
            self.logger.info("Mock: Listing agents")
            return {}
    
    agent_registry = MockAgentRegistryContract()
