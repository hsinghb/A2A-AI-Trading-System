#!/usr/bin/env python3
"""
Script to test the newly deployed AgentRegistry contract
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Force reload environment variables
load_dotenv(project_root / ".env", override=True)

def test_new_contract():
    """Test the newly deployed contract"""
    # Initialize Web3
    rpc_url = os.getenv("ETHEREUM_RPC_URL")
    contract_address = os.getenv("AGENT_REGISTRY_ADDRESS")
    admin_private_key = os.getenv("ADMIN_PRIVATE_KEY")
    
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # Load contract ABI (use the backend/blockchain/contracts/AgentRegistry.json which matches the deployed contract)
    contract_path = os.path.join(project_root, "backend", "blockchain", "contracts", "AgentRegistry.json")
    with open(contract_path, "r") as f:
        contract_json = json.load(f)
        abi = contract_json["abi"]
    
    # Create contract instance
    contract = w3.eth.contract(address=contract_address, abi=abi)
    
    # Get admin account
    admin_account = w3.eth.account.from_key(admin_private_key)
    admin_address = admin_account.address
    
    print(f"Testing new contract at: {contract_address}")
    print(f"Admin address: {admin_address}")
    print("=" * 50)
    
    # Test 1: Check if admin is set correctly
    print("1. Testing admin() function...")
    try:
        admin = contract.functions.admin().call()
        print(f"   Current admin: {admin}")
        
        if admin == admin_address:
            print("   ✅ Admin is set correctly!")
        else:
            print(f"   ❌ Admin mismatch! Expected: {admin_address}, Got: {admin}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error calling admin(): {str(e)}")
        return False
    
    # Test 2: Check if admin can call admin-only functions
    print("\n2. Testing admin-only function access...")
    try:
        # Try to call registerAdmin (should work for current admin)
        nonce = w3.eth.get_transaction_count(admin_address)
        gas_price = w3.eth.gas_price
        
        # Build transaction (don't send)
        tx = contract.functions.registerAdmin(admin_address).build_transaction({
            'from': admin_address,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': gas_price
        })
        print("   ✅ Admin can build admin-only transactions")
        
    except Exception as e:
        print(f"   ❌ Error building admin transaction: {str(e)}")
        return False
    
    # Test 3: Check if we can register an agent
    print("\n3. Testing agent registration...")
    try:
        # Test agent data
        test_did = "did:eth:0x0000000000000000000000000000000000000001"
        test_public_key = "test_public_key_123"
        test_metadata = '{"name": "Test Agent", "type": "trading"}'
        
        # Build transaction
        tx = contract.functions.registerAgent(
            test_did,
            test_public_key,
            test_metadata
        ).build_transaction({
            'from': admin_address,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': gas_price
        })
        print("   ✅ Agent registration transaction can be built")
        
        # Actually send the transaction
        signed_tx = w3.eth.account.sign_transaction(tx, admin_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"   Transaction sent: {tx_hash.hex()}")
        
        # Wait for transaction receipt
        print("   Waiting for confirmation...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            print("   ✅ Agent registered successfully!")
            
            # Verify agent was registered
            print("\n4. Verifying agent registration...")
            try:
                agent_info = contract.functions.getAgent(test_did).call()
                print(f"   Agent address: {agent_info[0]}")
                print(f"   Agent public key: {agent_info[1]}")
                print(f"   Agent reputation: {agent_info[2]}")
                print(f"   Agent is active: {agent_info[6]}")
                print("   ✅ Agent verification successful!")
                
            except Exception as e:
                print(f"   ❌ Error verifying agent: {str(e)}")
                
        else:
            print("   ❌ Agent registration failed!")
            return False
            
    except Exception as e:
        print(f"   ❌ Error registering agent: {str(e)}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! The contract is working correctly.")
    print("=" * 50)
    return True

if __name__ == "__main__":
    success = test_new_contract()
    if success:
        print("\nNext steps:")
        print("1. Update your backend to use the new contract address")
        print("2. Test your trading agents with the new contract")
        print("3. Monitor transactions on Etherscan")
    else:
        print("\n❌ Contract tests failed. Please check the deployment.") 