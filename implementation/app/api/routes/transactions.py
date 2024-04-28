# routes/transactions.py

from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, status
import requests
from slowapi.errors import RateLimitExceeded

# Import the DAG instance
from app.api.config.limiter import limiter
from app.api.config.logger import logger
from app.api.config.dag import dag
from app.api.config.env import API_NAME

from app.api.models.wallet import PublicKey
from app.api.models.transaction import TransactionCreate, Transaction
from app.api.models.responses import Response, ResponseError

from app.api.methods.errors import handle_error

router = APIRouter()

"""
API Endpoints:

Transactions:
- Get unconfirmed transactions
- Post transaction
"""

# Get unconfirmed transactions
@router.get('/unconfirmed/', 
            response_model=Response[list], 
            status_code=status.HTTP_200_OK, 
            tags=["TRANSACTIONS"],
            responses={
                500: {"model": ResponseError, "description": "Internal server error."},
                429: {"model": ResponseError, "description": "Too many requests."},
                200: {"model": Response[list], "description": "Unconfirmed transactions."}
            })
def get_unconfirmed_transactions(request: Request):
    """
    Get unconfirmed transactions.
    
    Args:
    - request: Request
    
    Returns:
    - Response[list]: Unconfirmed transactions.
    """
    try:
        # Get the unconfirmed transactions
        unconfirmed_transactions = [tx.to_dict() for tx in dag.unconfirmed_transactions]
        # Return the unconfirmed transactions
        return Response(data=unconfirmed_transactions, message=f"{len(unconfirmed_transactions)} Unconfirmed transactions.")
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)

# Post transaction
@router.post('/post/', 
             response_model=Response[dict], 
             status_code=status.HTTP_200_OK, 
             tags=["TRANSACTIONS"],
             responses={
                 500: {"model": ResponseError, "description": "Internal server error."},
                 429: {"model": ResponseError, "description": "Too many requests."},
                 200: {"model": Response[dict], "description": "Transaction posted."}
             })
#@limiter.limit("5/minute")
def post_transaction(transaction: TransactionCreate,
                     request: Request):
    """
    Post a transaction.
    
    Args:
    - transaction: TransactionCreate
    - request: Request
    
    Returns:
    - Response[dict]: Transaction posted.
    """
    try:
        # Create the transaction
        transaction = Transaction(**transaction.dict(),
                                  timestamp=datetime.now())
        # Add the transaction
        transaction_added = dag.add_transaction(transaction)
        if not transaction_added:
            raise HTTPException(status_code=400, detail="Transaction could not be added.")
        # Share the transaction with neighbors
        for neighbor in dag.neighbors:
            requests.post(f"{neighbor}api/v1/{API_NAME}/nodes/transaction/", json=transaction.to_dict())
        return Response(data=transaction, message="Transaction posted.")
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)