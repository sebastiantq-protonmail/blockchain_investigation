# routes/transactions.py

from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, status
from slowapi.errors import RateLimitExceeded

# Import the DAG instance
from app.api.config.limiter import limiter
from app.api.config.logger import logger
from app.api.config.dag import dag

from app.api.models.wallet import PublicKey
from app.api.models.transaction import TransactionCreate, Transaction
from app.api.models.responses import Response, ResponseError

from app.api.methods.errors import handle_error

router = APIRouter()

"""
API Endpoints:

Wallet:
- Get wallet nonce
- Get wallet balance
"""

# Get wallet nonce
@router.post('/nonce/', 
             response_model=Response[int], 
             status_code=status.HTTP_200_OK, 
             tags=["WALLETS"],
             responses={
                 500: {"model": ResponseError, "description": "Internal server error."},
                 429: {"model": ResponseError, "description": "Too many requests."},
                 200: {"model": Response[int], "description": "Wallet nonce."}
             })
#@limiter.limit("5/minute")
def get_wallet_nonce(wallet: PublicKey,
                     request: Request):
    """
    Get the wallet nonce.
    
    Args:
    - wallet: PublicKey
    - request: Request
    
    Returns:
    - Response[int]: Wallet nonce.
    """
    try:
        # Get the wallet nonce
        nonce = dag.nonces.get(wallet.public_key, 0)
        return Response(data=nonce, message="Wallet nonce.")
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)

# Get wallet balance
@router.post('/balance/', 
             response_model=Response[float], 
             status_code=status.HTTP_200_OK, 
             tags=["WALLETS"],
             responses={
                 500: {"model": ResponseError, "description": "Internal server error."},
                 429: {"model": ResponseError, "description": "Too many requests."},
                 200: {"model": Response[float], "description": "Wallet balance."}
             })
#@limiter.limit("5/minute")
def get_wallet_balance(wallet: PublicKey,
                       request: Request):
    """
    Get the wallet balance.
    
    Args:
    - wallet: PublicKey
    - request: Request
    
    Returns:
    - Response[float]: Wallet balance.
    """
    try:
        # Get the wallet balance with the decimals defined in the DAG instance
        return Response(data=dag.get_wallet_balance(wallet.public_key), message="Wallet balance.")
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)
