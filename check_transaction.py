#!/usr/bin/env python3
"""
Script to check transaction status and debug failed transactions
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Force reload environment variables
load_dotenv(project_root / ".env", override=True)

def check_transaction(tx_hash):
    """Check transaction status and details"""
    # Initialize Web3
    rpc_url = os.getenv("ETHEREUM_RPC_URL")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    print(f"Checking transaction: {tx_hash}")
    print("=" * 50)
    
    try:
        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        print(f"Transaction Status: {'Success' if receipt.status == 1 else 'Failed'}")
        print(f"Block Number: {receipt.blockNumber}")
        print(f"Gas Used: {receipt.gasUsed}")
        print(f"Gas Price: {w3.from_wei(receipt.effectiveGasPrice, 'gwei')} gwei")
        
        # Get transaction details
        tx = w3.eth.get_transaction(tx_hash)
        print(f"From: {tx['from']}")
        print(f"To: {tx['to']}")
        print(f"Value: {w3.from_wei(tx['value'], 'ether')} ETH")
        print(f"Data: {tx['input'][:100]}...")
        
        if receipt.status == 0:
            print("\nTransaction Failed!")
            print("Possible reasons:")
            print("1. Contract reverted the transaction")
            print("2. Out of gas")
            print("3. Invalid function call")
            
            # Try to get revert reason
            try:
                # Replay the transaction to get revert reason
                tx = w3.eth.get_transaction(tx_hash)
                result = w3.eth.call(
                    {
                        'from': tx['from'],
                        'to': tx['to'],
                        'value': tx['value'],
                        'data': tx['input'],
                        'gas': tx['gas'],
                        'gasPrice': tx['gasPrice'],
                        'nonce': tx['nonce']
                    },
                    tx['blockNumber'] - 1
                )
                print(f"Call result: {result.hex()}")
            except Exception as e:
                print(f"Revert reason: {str(e)}")
        
    except Exception as e:
        print(f"Error checking transaction: {str(e)}")

def check_contract_status():
    """Check the contract status and admin"""
    try:
        from backend.blockchain.agent_registry import AgentRegistryContract
        
        agent_registry = AgentRegistryContract()
        
        print("\nContract Status:")
        print("=" * 50)
        print(f"Contract Address: {agent_registry.contract_address}")
        print(f"Admin Address: {agent_registry.admin_address}")
        
        # Check if admin exists
        try:
            admin = agent_registry.get_admin()
            print(f"Current Admin: {admin}")
        except Exception as e:
            print(f"Error getting admin: {str(e)}")
        
        # Check contract code
        code = agent_registry.w3.eth.get_code(agent_registry.contract_address)
        print(f"Contract Code: {'Present' if code else 'Not Found'}")
        
    except Exception as e:
        print(f"Error checking contract: {str(e)}")

if __name__ == "__main__":
    # Check the latest failed transaction
    tx_hash = "cc22bf3c80070fe30317b069978863e11e31a1a18b4f0c00f355c51b34a71b42"
    check_transaction(tx_hash)
    
    # Check contract status
    check_contract_status()
    
    print("\nEtherscan Links:")
    print("=" * 50)
    print(f"Transaction: https://sepolia.etherscan.io/tx/{tx_hash}")
    contract_address = os.getenv("AGENT_REGISTRY_ADDRESS")
    print(f"Contract: https://sepolia.etherscan.io/address/{contract_address}") 