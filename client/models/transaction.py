# models/transaction.py

import oqs # type: ignore

from hashlib import sha256
from methods.wallets import sign_transaction

class ClientTransaction:
    def __init__(self, sender, recipient, amount, nonce, private_key):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.nonce = nonce
        self.private_key = private_key
        self.signature = None

    def sign_transaction(self):
        """
        Sign the transaction with the private key.
        """
        transaction_hash = f"{self.sender}{self.recipient}{self.amount}{self.nonce}"
        self.signature = sign_transaction(transaction_hash, self.private_key)

    def to_dict(self):
        """
        Convert the transaction to a dictionary, ready to be sent to the server.
        """
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "nonce": self.nonce,
            "signature": self.signature
        }
