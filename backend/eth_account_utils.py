import secrets
import hashlib
from eth_account import Account
from eth_keys import keys

def generate_eth_account():
    """
    Generates a real Ethereum account.
    Returns address, private key, public key, and did:ethr DID.
    """
    # Create account and get the private key as bytes
    acct = Account.create()
    private_key_bytes = acct.key  # This is already in bytes format
    private_key_hex = private_key_bytes.hex()
    address = acct.address

    # Create private key object and get public key
    private_key_obj = keys.PrivateKey(private_key_bytes)
    public_key_bytes = private_key_obj.public_key.to_bytes()
    public_key_hex = public_key_bytes.hex()
    
    did = f"did:ethr:{address}"
    return {
        "address": address,
        "private_key": "0x" + private_key_hex,  # Add 0x prefix for consistency
        "public_key": public_key_hex,
        "did": did
    }

if __name__ == "__main__":
    info = generate_eth_account()
    print("Ethereum Address:", info["address"])
    print("Private Key:", info["private_key"])
    print("Public Key:", info["public_key"])
    print("DID URI:", info["did"]) 