# routes/nodes.py

from typing import List
from fastapi import APIRouter, HTTPException, Request, status
import requests
from slowapi.errors import RateLimitExceeded

# Import the DAG instance
from app.api.config.limiter import limiter
from app.api.config.logger import logger
from app.api.config.dag import dag
from app.api.config.env import IS_PRODUCTION, LOCALHOST_SERVER_URL, PRODUCTION_SERVER_URL, API_NAME

from app.api.models.blockchain import Block
from app.api.models.transaction import Transaction
from app.api.models.neighbor import Neighbor
from app.api.models.responses import Response, ResponseError

from app.api.methods.errors import handle_error

router = APIRouter()

"""
API Endpoints:

Nodes:
- Get neighbors
- Connect to neighbor
- Receive neighbor transaction
- Receive neighbor block
"""

# Get neighbors
@router.get('/neighbors/', 
            response_model=Response[List[str]], 
            status_code=status.HTTP_200_OK, 
            tags=["NODES"],
            responses={
                500: {"model": ResponseError, "description": "Internal server error."},
                429: {"model": ResponseError, "description": "Too many requests."},
                200: {"model": Response[List[str]], "description": "Neighbors."}
            })
#@limiter.limit("5/minute")
def get_neighbors(request: Request):
    """
    Get the neighbors of the node.
    
    Args:
    - request: Request
    
    Returns:
    - Response[dict]: Neighbors.
    """
    try:
        # Get the neighbors
        neighbors = dag.get_neighbors()
        return Response(data=neighbors, message=f"{len(neighbors)} Neighbors.")
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)

# Connect to neighbor
@router.post('/connect/', 
             response_model=Response[str], 
             status_code=status.HTTP_200_OK, 
             tags=["NODES"],
             responses={
                 500: {"model": ResponseError, "description": "Internal server error."},
                 429: {"model": ResponseError, "description": "Too many requests."},
                 200: {"model": Response[str], "description": "Connected to neighbor."}
             })
#@limiter.limit("5/minute")
def connect_to_neighbor(request: Request,
                        neighbor: Neighbor):
    """
    Connect to a neighbor.
    
    Args:
    - request: Request
    - neighbor: Neighbor
    
    Returns:
    - Response[dict]: Connected to neighbor.
    """
    try:
        address_url = neighbor.address_url

        # Verify if the neighbor is a valid URL
        if not address_url.startswith("http"):
            raise HTTPException(status_code=400, detail="Invalid neighbor URL.")

        # Get the neighbor's DAG
        neighbor_dag = requests.get(f"{address_url}api/v1/{API_NAME}/dag/").json()
        neighbor_dag_nodes = neighbor_dag["data"]["nodes"]

        # Compare which DAG is bigger
        print("Neighbor DAG nodes:", len(neighbor_dag_nodes))
        print("Current DAG nodes:", len(dag.graph.nodes))
        if len(neighbor_dag_nodes) > len(dag.graph.nodes):
            # Load the neighbor's DAG
            dag.recreate_blockchain_from_graph(neighbor_dag)

        # Get the neighbor neighbors
        neighbor_neighbors = requests.get(f"{address_url}api/v1/{API_NAME}/nodes/neighbors/").json()
        neighbor_neighbors = neighbor_neighbors["data"]

        # Merge the neighbors of the neighbor with the current node
        for neighbor_neighbor in neighbor_neighbors:
            if neighbor_neighbor not in dag.get_neighbors():
                dag.add_neighbor(neighbor_neighbor)

        if address_url not in dag.get_neighbors():
            # Send the petition to connect to the neighbor
            if int(IS_PRODUCTION): # type: ignore
                requests.post(f"{address_url}api/v1/{API_NAME}/nodes/connect/", json=Neighbor(address_url=PRODUCTION_SERVER_URL).dict()) # type: ignore
            else:
                requests.post(f"{address_url}api/v1/{API_NAME}/nodes/connect/", json=Neighbor(address_url=LOCALHOST_SERVER_URL).dict()) # type: ignore

            # Add the neighbor
            dag.add_neighbor(address_url) # type: ignore

        return Response(data=address_url, message=f"Connected to neighbor {address_url}.")
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)

# Receive neighbor transaction
@router.post('/transaction/', 
             response_model=Response[Transaction], 
             status_code=status.HTTP_200_OK, 
             tags=["NODES"],
             responses={
                 500: {"model": ResponseError, "description": "Internal server error."},
                 429: {"model": ResponseError, "description": "Too many requests."},
                 200: {"model": Response[str], "description": "Received neighbor transaction."}
             })
#@limiter.limit("5/minute")
def receive_neighbor_transaction(request: Request,
                                 transaction: Transaction):
    """
    Receive a transaction from a neighbor.
    
    Args:
    - request: Request
    - transaction: Transaction
    
    Returns:
    - Response[dict]: Received neighbor transaction.
    """
    try:
        # Add the transaction to the DAG
        dag.add_transaction(transaction)
        return Response(data=transaction, message="Received neighbor transaction.")
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)

# Receive neighbor block
@router.post('/block/', 
             response_model=Response[Block], 
             status_code=status.HTTP_200_OK, 
             tags=["NODES"],
             responses={
                 500: {"model": ResponseError, "description": "Internal server error."},
                 429: {"model": ResponseError, "description": "Too many requests."},
                 200: {"model": Response[str], "description": "Received neighbor block."}
             })
#@limiter.limit("5/minute")
def receive_neighbor_block(request: Request,
                           block: Block):
    """
    Receive a block from a neighbor.
    
    Args:
    - request: Request
    - block: Block
    
    Returns:
    - Response[dict]: Received neighbor block.
    """
    try:
        # Add the block to the DAG
        dag.add_block(block)
        return Response(data=block, message="Received neighbor block.")
    except RateLimitExceeded:
        raise HTTPException(status_code=429, detail="Too many requests.")
    except HTTPException:
        # This is to ensure HTTPException is not caught in the generic Exception
        raise
    except Exception as e:
        handle_error(e, logger)