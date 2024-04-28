# routes/blockchain.py

from typing import List
from networkx.readwrite import json_graph
from fastapi import APIRouter, HTTPException, Request, status
from slowapi.errors import RateLimitExceeded

# Import the DAG instance
from app.api.config.limiter import limiter
from app.api.config.logger import logger
from app.api.config.dag import dag

from app.api.models.blockchain import Block
from app.api.models.responses import Response, ResponseError

from app.api.methods.errors import handle_error

router = APIRouter()

"""
API Endpoints:

Blockchain:
- Get unconfirmed blocks
- Get block by hash
- Get DAG

Nodes (TODO):
- Get neighbors
- Post neighbor
- Connect to neighbor
"""

# Get unconfirmed blocks
@router.get('/unconfirmed_blocks/', 
            response_model=Response[list], 
            status_code=status.HTTP_200_OK, 
            tags=["BLOCKCHAIN"],
            responses={
                500: {"model": ResponseError, "description": "Internal server error."},
                429: {"model": ResponseError, "description": "Too many requests."},
                200: {"model": Response[list], "description": "Unconfirmed blocks."}
            })
#@limiter.limit("5/minute")
def get_unconfirmed_blocks(request: Request):
    """
    Get the blocks (DAG nodes) with less than umbral confirmations (node fathers).
    
    Args:
    - request: Request
    
    Returns:
    - Response[dict]: Unconfirmed blocks.
    """
    try:
        # Get the unconfirmed blocks
        unconfirmed_blocks = dag.get_unconfirmed_blocks()
        return Response(data=unconfirmed_blocks, message=f"{len(unconfirmed_blocks)} Unconfirmed blocks.")
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)

# Get block by hash
@router.get('/block/{block_hash}/', 
            response_model=Response[dict], 
            status_code=status.HTTP_200_OK, 
            tags=["BLOCKCHAIN"],
            responses={
                500: {"model": ResponseError, "description": "Internal server error."},
                429: {"model": ResponseError, "description": "Too many requests."},
                200: {"model": Response[dict], "description": "Block."}
            })
#@limiter.limit("5/minute")
def get_block_by_hash(request: Request, block_hash: str):
    """
    Get a block by its hash.
    
    Args:
    - request: Request
    - block_hash: str
    
    Returns:
    - Response[dict]: Block.
    """
    try:
        # Get the block by hash
        block = dag.get_block_by_hash(block_hash)
        if block is None:
            raise HTTPException(status_code=404, detail="Block not found.")
        return Response(data=block, message="Block.")
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)

# Get DAG
@router.get('/dag/', 
            response_model=Response[dict], 
            status_code=status.HTTP_200_OK, 
            tags=["BLOCKCHAIN"],
            responses={
                500: {"model": ResponseError, "description": "Internal server error."},
                429: {"model": ResponseError, "description": "Too many requests."},
                200: {"model": Response[dict], "description": "DAG."}
            })
#@limiter.limit("5/minute")
def get_dag(request: Request):
    """
    Get the DAG.
    
    Args:
    - request: Request
    
    Returns:
    - Response[dict]: DAG.
    """
    try:
        # Get the DAG
        graph_data = json_graph.node_link_data(dag.graph)
        return Response(data=graph_data, message="DAG.")
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)