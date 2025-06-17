"""
Script to compile the AgentRegistry smart contract
"""

import json
import logging
import os
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compile_contract():
    """Compile the AgentRegistry contract using solc"""
    try:
        contract_path = Path("contracts/AgentRegistry.sol")
        if not contract_path.exists():
            raise FileNotFoundError(f"Contract file not found at {contract_path}")
        
        # Create output directory if it doesn't exist
        os.makedirs("contracts/build", exist_ok=True)
        
        # Compile contract
        logger.info("Compiling contract...")
        compile_cmd = [
            "solc",
            "--optimize",
            "--combined-json", "abi,bin",
            "--overwrite",
            str(contract_path)
        ]
        
        logger.debug(f"Running command: {' '.join(compile_cmd)}")
        result = subprocess.run(compile_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Compilation failed with error: {result.stderr}")
            raise Exception(f"Compilation failed: {result.stderr}")
        
        # Print raw compilation output
        logger.debug("Raw compilation output:")
        logger.debug(result.stdout)
        
        try:
            # Try to parse the output as JSON
            compiled = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse compilation output as JSON: {e}")
            logger.error(f"Raw output: {result.stdout}")
            raise
        
        # Debug: Print the full compilation output structure
        logger.debug("Full compilation output structure:")
        logger.debug(json.dumps(compiled, indent=2))
        
        # Debug: Print available contract keys
        logger.debug("Available contract keys:")
        if "contracts" not in compiled:
            logger.error("No 'contracts' key in compilation output")
            logger.error(f"Available keys: {list(compiled.keys())}")
            raise Exception("Invalid compilation output format")
        
        # Find the contract data
        contract_data = None
        for contract_key, contract_info in compiled["contracts"].items():
            logger.debug(f"Processing contract key: {contract_key}")
            logger.debug(f"Contract info type: {type(contract_info)}")
            logger.debug(f"Contract info: {contract_info}")
            
            if isinstance(contract_info, dict):
                for name, data in contract_info.items():
                    logger.debug(f"Processing contract name: {name}")
                    logger.debug(f"Contract data type: {type(data)}")
                    logger.debug(f"Contract data: {data}")
                    
                    # If data is a string, try to parse it as JSON
                    if isinstance(data, str):
                        try:
                            data = json.loads(data)
                        except json.JSONDecodeError:
                            logger.debug(f"Data is not JSON: {data}")
                            continue
                    
                    # If data is a dictionary, check for ABI and bytecode
                    if isinstance(data, dict):
                        if "abi" in data and "bin" in data:
                            contract_data = data
                            logger.info(f"Found valid contract data in {name}")
                            break
                    # If data is a list, it might be the ABI directly
                    elif isinstance(data, list) and len(data) > 0:
                        # Look for the bytecode in the contract info
                        if "bin" in contract_info:
                            contract_data = {
                                "abi": data,
                                "bin": contract_info["bin"]
                            }
                            logger.info(f"Found ABI list and bytecode in {name}")
                            break
            
            if contract_data:
                break
        
        if not contract_data:
            # Try one more time with a different approach
            for contract_key, contract_info in compiled["contracts"].items():
                if isinstance(contract_info, dict):
                    # Try to find ABI and bin in the contract info directly
                    if "abi" in contract_info and "bin" in contract_info:
                        contract_data = {
                            "abi": contract_info["abi"],
                            "bin": contract_info["bin"]
                        }
                        logger.info(f"Found contract data directly in {contract_key}")
                        break
        
        if not contract_data:
            raise Exception("Could not find any contract with ABI and bytecode")
        
        # Extract ABI and bytecode
        if isinstance(contract_data, dict):
            abi = contract_data["abi"]
            bytecode = contract_data["bin"]
        else:
            raise Exception(f"Unexpected contract data type: {type(contract_data)}")
        
        # Ensure ABI is a list
        if isinstance(abi, str):
            try:
                abi = json.loads(abi)
            except json.JSONDecodeError:
                raise Exception("ABI is not valid JSON")
        
        if not isinstance(abi, list):
            raise Exception(f"Unexpected ABI type: {type(abi)}")
        
        # Save ABI and bytecode
        contract_json = {
            "abi": abi,
            "bytecode": f"0x{bytecode}" if not bytecode.startswith("0x") else bytecode
        }
        
        with open("contracts/AgentRegistry.json", "w") as f:
            json.dump(contract_json, f, indent=2)
        
        logger.info("Contract compiled successfully!")
        logger.info("ABI and bytecode saved to contracts/AgentRegistry.json")
        
    except Exception as e:
        logger.error(f"Error compiling contract: {str(e)}")
        # Print more detailed error information
        logger.error(f"Error details: {type(e).__name__}: {str(e)}")
        raise

if __name__ == "__main__":
    # Enable debug logging for more detailed output
    logging.getLogger().setLevel(logging.DEBUG)
    compile_contract() 