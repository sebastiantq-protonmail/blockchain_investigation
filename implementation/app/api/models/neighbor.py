# models/neighbor.py

from datetime import datetime
from pydantic import BaseModel, Field

class Neighbor(BaseModel):
    """
    Public Key Model
    
    Args:
    - address_url: str
    """
    address_url: str = Field(default=..., description="The address URL of the neighbor")

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
                "address_url": "http://.../"
            }
        }
