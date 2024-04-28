# models/transaction.py

from datetime import datetime
from pydantic import BaseModel, Field

from app.api.config.env import GENESIS_PUBLIC_KEY, SEBASTIAN_PUBLIC_KEY

class PublicKey(BaseModel):
    """
    Public Key Model
    
    Args:
    - public_key: str
    """
    public_key: str = Field(default=..., description="The public key of the wallet")

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
                "public_key": GENESIS_PUBLIC_KEY
            }
        }