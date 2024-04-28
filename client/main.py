# main.py: Client-side code for the blockchain investigation project.

import json
import time

import requests
from models.transaction import ClientTransaction
from methods.wallets import generate_keypair, verify_signature

node_address = "http://localhost:8000"

# Get nonce from the server
def get_nonce(wallet_address: str):
    """
    Get the nonce from the server.
    """
    response = requests.post(f"{node_address}/api/v1/blockchain_investigation/wallets/nonce/", json={"public_key": wallet_address})
    return response.json()["data"]

# Load private and public keys from the keypair file (or generate a new keypair)
def load_keypair():
    """
    Generate and save two key pairs: one for GENESIS and one for SEBASTIAN.
    Each key pair includes a private key and a public key.
    The keys are stored in a JSON file named 'keypairs.json'.
    """
    try:
        with open("keypairs.json", "r") as f:
            keypairs = json.load(f)
    except FileNotFoundError:
        # Generate key pairs for GENESIS and SEBASTIAN
        genesis_private, genesis_public = generate_keypair()
        sebastian_private, sebastian_public = generate_keypair()

        # Save the key pairs to a JSON file
        keypairs = {
            "GENESIS": {
                "public_key": genesis_public,
                "private_key": genesis_private
            },
            "SEBASTIAN": {
                "public_key": sebastian_public,
                "private_key": sebastian_private
            }
        }
        with open("keypairs.json", "w") as f:
            json.dump(keypairs, f, indent=4)

    return keypairs


def main():
    """
    Main function.
    """
    keypairs = load_keypair()
    genesis_keypair = keypairs["GENESIS"]
    sebastian_keypair = keypairs["SEBASTIAN"]
    sender = genesis_keypair["public_key"]
    recipient = sebastian_keypair["public_key"]
    amount = 1000

    while True:
        nonce = get_nonce(sender) + 1

        transaction = ClientTransaction(sender, recipient, amount, nonce, genesis_keypair["private_key"])
        transaction.sign_transaction()
        transaction_dict = transaction.to_dict()

        #print("Sender:", sender)
        #print("Recipient:", recipient)
        #print("Amount:", amount)
        #print("Nonce:", nonce)
        #print("Signature:", transaction_dict["signature"])

        # Verify the signature
        #transaction_hash = f"{sender}{recipient}{amount}{nonce}"
        #print("Signature verification:", verify_signature(transaction_hash.encode(), transaction_dict["signature"], sender))

        # Send the transaction to the server
        send_test_transaction(transaction_dict)
        time.sleep(0.01)

# Send the transaction to the server (not implemented in this snippet)
def send_test_transaction(transaction_dict):
    """
    Send the transaction to the server.
    """
    while True:
        # Send the transaction to the server
        response = requests.post(f"{node_address}/api/v1/blockchain_investigation/transactions/post/", json=transaction_dict)
        print("Transaction sent to the server:", response.json())
        #time.sleep(1)
        break
    
if __name__ == "__main__":
    main()