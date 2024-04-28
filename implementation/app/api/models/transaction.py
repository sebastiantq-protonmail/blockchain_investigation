# models/transaction.py

from datetime import datetime
from pydantic import BaseModel, Field

from app.api.config.env import GENESIS_PUBLIC_KEY, SEBASTIAN_PUBLIC_KEY

class TransactionCreate(BaseModel):
    """
    TransactionCreate Model
    
    Args:
    - sender: str
    - recipient: str
    - amount: int
    - nonce: int
    - signature: str
    """
    sender: str = Field(default=..., description="The public key of the sender")
    recipient: str = Field(default=..., description="The public key of the recipient")
    amount: int = Field(default=..., description="The amount of the transaction")
    nonce: int = Field(default=..., description="The nonce of the transaction")
    signature: str = Field(default=..., description="The signature of the transaction")

    class Config:
        """
        Pydantic Config
        
        Args:
        - arbitrary_types_allowed: bool
        - json_encoders: dict
        """
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        schema_extra = {
            "example": {
                "sender": GENESIS_PUBLIC_KEY,
                "recipient": SEBASTIAN_PUBLIC_KEY,
                "amount": 10,
                "nonce": 0,
                "signature": "signature"
            }
        }

class Transaction(TransactionCreate):
    """
    Transaction Model

    Args:
    - timestamp: datetime
    """
    timestamp: datetime = Field(default=datetime.now(), description="The timestamp of the transaction")

    def to_dict(self):
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "nonce": self.nonce,
            "signature": self.signature,
            "timestamp": self.timestamp.isoformat()
        }

    class Config:
        """
        Pydantic Config
        
        Args:
        - arbitrary_types_allowed: bool
        - json_encoders: dict
        """
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        schema_extra = {
            "example": {
                "sender": GENESIS_PUBLIC_KEY,
                "recipient": SEBASTIAN_PUBLIC_KEY,
                "amount": 10,
                "nonce": 0,
                "signature": "signature",
                "timestamp": "datetime.now().isoformat()"
            }
        }