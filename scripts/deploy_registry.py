#!/usr/bin/env python3
"""
Script to deploy the AgentRegistry contract with the intended admin account.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv(project_root / ".env", override=True)

# Paths
sol_abi_path = project_root / "contracts" / "AgentRegistry.json"
env_path = project_root / ".env"

# Load contract ABI and bytecode
with open(sol_abi_path, "r") as f:
    contract_json = json.load(f)
    abi = contract_json["abi"]
    bytecode = contract_json["bytecode"]

def deploy_contract(w3, admin_account):
    print("\nDeploying AgentRegistry contract...")
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(admin_account.address)
    gas_price = w3.eth.gas_price
    tx = contract.constructor().build_transaction({
        'from': admin_account.address,
        'nonce': nonce,
        'gas': 2000000,
        'gasPrice': gas_price
    })
    signed_tx = w3.eth.account.sign_transaction(tx, admin_account.key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"  Transaction sent: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status != 1:
        raise Exception("Contract deployment failed")
    print(f"  Contract deployed at: {receipt.contractAddress}")
    return receipt.contractAddress

def main():
    # Get RPC URL and admin private key
    rpc_url = os.getenv("ETHEREUM_RPC_URL") or os.getenv("ETH_RPC_URL")
    admin_private_key = os.getenv("ADMIN_PRIVATE_KEY")
    if not rpc_url or not admin_private_key:
        print("Please set ETHEREUM_RPC_URL and ADMIN_PRIVATE_KEY in your .env file.")
        sys.exit(1)
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print(f"Failed to connect to Ethereum node at {rpc_url}")
        sys.exit(1)
    admin_account = Account.from_key(admin_private_key)
    print(f"Admin address: {admin_account.address}")
    # Deploy contract
    contract_address = deploy_contract(w3, admin_account)
    # Update .env
    existing_vars = {}
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    existing_vars[key] = value
    existing_vars["ETHEREUM_RPC_URL"] = rpc_url
    existing_vars["AGENT_REGISTRY_ADDRESS"] = contract_address
    existing_vars["ADMIN_PRIVATE_KEY"] = admin_private_key
    # Write back to .env
    with open(env_path, "w") as f:
        f.write("# Ethereum Network Configuration\n")
        f.write(f"ETHEREUM_RPC_URL={rpc_url}\n")
        f.write(f"AGENT_REGISTRY_ADDRESS={contract_address}\n\n")
        f.write("# Admin Credentials\n")
        f.write(f"ADMIN_PRIVATE_KEY={admin_private_key}\n\n")
        for key, value in existing_vars.items():
            if key not in ["ETHEREUM_RPC_URL", "AGENT_REGISTRY_ADDRESS", "ADMIN_PRIVATE_KEY"]:
                f.write(f"{key}={value}\n")
    print("\nDeployment complete!\n")
    print("Next Steps:")
    print("1. Fund the admin account with Sepolia ETH if needed.")
    print("2. Use the contract address and admin key in your backend/frontend.")
    print(f"3. Contract address: {contract_address}")
    print(f"4. Admin address: {admin_account.address}")
    print("5. Test admin functions to confirm deployment.")

if __name__ == "__main__":
    main() 