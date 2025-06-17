#!/usr/bin/env python3
"""
Script to compile the updated AgentRegistry contract and update ABI files
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv(project_root / ".env", override=True)

def compile_contract():
    """Compile the Solidity contract using solc"""
    print("Compiling AgentRegistry contract...")
    
    # Paths
    sol_file = project_root / "contracts" / "AgentRegistry.sol"
    output_dir = project_root / "contracts" / "build"
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Compile using solc
        cmd = [
            "solc",
            "--optimize",
            "--optimize-runs", "200",
            "--combined-json", "abi,bin",
            "--base-path", str(project_root / "contracts"),
            "--include-path", str(project_root / "contracts"),
            "--overwrite",
            str(sol_file),
            "-o", str(output_dir)
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
        
        if result.returncode != 0:
            print(f"Compilation failed: {result.stderr}")
            return False
            
        print("✅ Contract compiled successfully!")
        return True
        
    except FileNotFoundError:
        print("❌ solc compiler not found. Please install solc:")
        print("   macOS: brew install solidity")
        print("   Ubuntu: sudo apt-get install solc")
        print("   Or download from: https://docs.soliditylang.org/en/latest/installing-solidity.html")
        return False
    except Exception as e:
        print(f"❌ Compilation error: {str(e)}")
        return False

def extract_contract_data():
    """Extract ABI and bytecode from compiled output"""
    print("\nExtracting contract data...")
    
    # Read the combined JSON output
    combined_json_path = project_root / "contracts" / "build" / "combined.json"
    
    try:
        with open(combined_json_path, 'r') as f:
            combined_data = json.load(f)
        
        # Find the AgentRegistry contract
        contract_key = None
        for key in combined_data['contracts']:
            if 'AgentRegistry' in key:
                contract_key = key
                break
        
        if not contract_key:
            print("❌ AgentRegistry contract not found in compiled output")
            return None
        
        contract_data = combined_data['contracts'][contract_key]
        abi = contract_data['abi']
        bytecode = contract_data['bin']
        
        print("✅ Contract data extracted successfully!")
        return {
            'abi': abi,
            'bytecode': bytecode
        }
        
    except Exception as e:
        print(f"❌ Error extracting contract data: {str(e)}")
        return None

def update_abi_files(contract_data):
    """Update both ABI files with the new contract data"""
    print("\nUpdating ABI files...")
    
    # Paths to update
    abi_files = [
        project_root / "contracts" / "AgentRegistry.json",
        project_root / "backend" / "blockchain" / "contracts" / "AgentRegistry.json"
    ]
    
    for abi_file in abi_files:
        try:
            # Create directory if it doesn't exist
            abi_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create the JSON structure
            contract_json = {
                "contractName": "AgentRegistry",
                "abi": contract_data['abi'],
                "bytecode": contract_data['bytecode']
            }
            
            # Write to file
            with open(abi_file, 'w') as f:
                json.dump(contract_json, f, indent=4)
            
            print(f"✅ Updated: {abi_file}")
            
        except Exception as e:
            print(f"❌ Error updating {abi_file}: {str(e)}")
            return False
    
    return True

def verify_abi():
    """Verify that the ABI contains the expected functions"""
    print("\nVerifying ABI...")
    
    # Load the updated ABI
    abi_file = project_root / "contracts" / "AgentRegistry.json"
    
    try:
        with open(abi_file, 'r') as f:
            contract_json = json.load(f)
            abi = contract_json['abi']
        
        # Check for expected functions
        expected_functions = [
            'admin',
            'registerAdmin',
            'registerAgent',
            'getAgent',
            'updateReputation',
            'deactivateAgent'
        ]
        
        function_names = []
        for item in abi:
            if item['type'] == 'function':
                function_names.append(item['name'])
        
        print("Found functions:", function_names)
        
        missing_functions = []
        for func in expected_functions:
            if func not in function_names:
                missing_functions.append(func)
        
        if missing_functions:
            print(f"❌ Missing functions: {missing_functions}")
            return False
        else:
            print("✅ All expected functions found in ABI!")
            return True
            
    except Exception as e:
        print(f"❌ Error verifying ABI: {str(e)}")
        return False

def main():
    """Main function to compile and update"""
    print("🔄 Starting contract compilation and ABI update...")
    print("=" * 60)
    
    # Step 1: Compile contract
    if not compile_contract():
        return False
    
    # Step 2: Extract contract data
    contract_data = extract_contract_data()
    if not contract_data:
        return False
    
    # Step 3: Update ABI files
    if not update_abi_files(contract_data):
        return False
    
    # Step 4: Verify ABI
    if not verify_abi():
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Contract compilation and ABI update completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Deploy the updated contract:")
    print("   python scripts/deploy_registry.py")
    print("2. Test the new contract:")
    print("   python test_new_contract.py")
    print("3. Update your backend to use the new contract address")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 