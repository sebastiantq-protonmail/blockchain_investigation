# models/blockchain.py

import json
import os
import sys

import requests
from pympler import asizeof # type: ignore
import networkx as nx # type: ignore

from random import choice
from datetime import datetime
from hashlib import sha256
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.api.methods.wallets import verify_signature

from app.api.models.transaction import Transaction

from app.api.config.env import API_NAME, GENESIS_PUBLIC_KEY, SEBASTIAN_PUBLIC_KEY, LOCALHOST_SERVER_URL, PRODUCTION_SERVER_URL, IS_PRODUCTION

class Block(BaseModel):
    """
    Block Model

    Args:
    - index: int
    - transactions: List[Transaction]
    - nonce: int
    - children_hashes: List[str]
    - timestamp: datetime
    """
    index: int = Field(default=..., description="The index of the block")
    transactions: List[Transaction] = Field(default=..., description="The list of transactions in the block")
    nonce: int = Field(default=0, description="The nonce of the block")
    children_hashes: List[str] = Field(default=[], description="The list of children hashes of the block")
    timestamp: datetime = Field(default=datetime.now(), description="The timestamp of the block")

    @property
    def hash(self) -> str:
        block_content = json.dumps({
            "index": self.index,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce,
            "children_hashes": self.children_hashes,
            "timestamp": self.timestamp.isoformat()
        }, sort_keys=True).encode('utf-8')
        return sha256(block_content).hexdigest()
    
    def to_dict(self):
        return {
            "index": self.index,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce,
            "children_hashes": self.children_hashes,
            "timestamp": self.timestamp.isoformat()
        }

    class Config:
        """
        Pydantic Config

        Args:
        - arbitrary_types_allowed: bool
        """
        arbitrary_types_allowed = True
        schema_extra = {
            "example": {
                "index": 0,
                "transactions": [
                    {
                        "sender": "public_key",
                        "recipient": "public_key",
                        "amount": 10,
                        "nonce": 0,
                        "signature": "signature"
                    }
                ],
                "nonce": 0,
                "children_hashes": [],
                "hash": "hash"
            }
        }

class DAG(BaseModel):
    """
    Directed Acyclic Graph (DAG) Model

    Args:
    - graph: nx.DiGraph
    - balances: Dict[str, float]
    - nonces: Dict[str, int]
    - unconfirmed_transactions: List[Transaction]
    - json_file_path: str
    - block_mb_size_limit: int
    - minimal_degree: int
    - decimal_places: int
    """
    # State
    graph: nx.DiGraph = Field(default_factory=nx.DiGraph, description="The Directed Acyclic Graph (DAG)")
    balances: Dict[str, int] = Field(default={
        GENESIS_PUBLIC_KEY: 100000 # That's 1000.00 in the decimal_places
    }, description="The balances of the wallets")
    nonces: Dict[str, int] = Field(default_factory=dict, description="The nonces of the wallets")

    # Temporary state
    unconfirmed_transactions: List[Transaction] = Field(default_factory=list, description="The list of unconfirmed transactions")

    # Configurations
    json_file_path: str = Field(default='app/api/shared/blockchain.json', description="The path to the JSON file")
    block_mb_size_limit: int = Field(1, description="The size limit of a block in MB")
    minimal_degree: int = Field(3, description="The minimal degree of a block")
    decimal_places: int = Field(2, description="The number of decimal places for the balances")

    # Neighbors
    neighbors: List[str] = Field(default=[PRODUCTION_SERVER_URL if int(IS_PRODUCTION) else LOCALHOST_SERVER_URL], description="The list of neighbors URLs") # type: ignore

    def create_block(self) -> Optional[Block]:
        """
        Create a new block from unconfirmed transactions if the limit is reached.
        """
        actual_block_size = asizeof.asizeof(self.unconfirmed_transactions)
        # Convertir bytes a megabytes
        #tamanio_total_mb = actual_block_size / (1024 * 1024)
        #print(f'Tamaño total en megabytes: {tamanio_total_mb:.20f} MB')
        if actual_block_size < self.block_mb_size_limit * 1024 * 1024:
            return None

        # Select children blocks - simplest case, select randomly from blocks without children
        children_hashes = [node for node, degree in self.graph.out_degree() if degree < self.minimal_degree]

        # Create the new block
        new_block = Block(
            index=len(self.graph),
            transactions=self.unconfirmed_transactions,
            nonce=0, # This could be adjusted based on specific use-case
            children_hashes=children_hashes,
            timestamp=datetime.now()
        )

        # Add the block to the graph
        if self.add_block(new_block):
            # Remove confirmed transactions
            # TODO: This could be optimized by using a set instead of a list
            self.unconfirmed_transactions = [tx for tx in self.unconfirmed_transactions if tx not in new_block.transactions]
            return new_block
        return None

    def add_block(self, block: Block):
        """
        Add a new block to the DAG, ensuring no cycles are created.
        """
        # Check if block already exists in the graph
        if block.hash in self.graph:
            # Handle the existing block case (e.g., skip, update, or re-validate)
            print(f"Block with hash {block.hash} already exists.")
            return False  # or handle differently based on your application needs

        self.graph.add_node(block.hash, block=block)
        for child_hash in block.children_hashes:
            if child_hash not in self.graph:
                return False
            self.graph.add_edge(child_hash, block.hash)
            # Validate the child Block
            child_block = self.graph.nodes[child_hash]['block']
            if not self.validate_block(child_block):
                return False
            # If the child is valid and has been confirmed at least minimal_degree times, process its transactions
            if self.graph.in_degree(child_hash) == self.minimal_degree:
                #print("Children hashes:", child_block.children_hashes)
                self.process_transactions(child_block.transactions)
                #print(f"Block confirmed: {child_hash}")
                # Save the block to JSON file
                self.save_graph_to_json_file(self.json_file_path)

                # Share the block with neighbors
                for neighbor in self.neighbors:
                    requests.post(f"{neighbor}api/v1/{API_NAME}/nodes/block/", json=child_block.to_dict())
        if not nx.is_directed_acyclic_graph(self.graph):
            self.graph.remove_node(block.hash)
            return False
        return True
    
    def validate_block(self, block: Block) -> bool:
        """
        Validate a block by checking its hash and the transactions it contains.
        """
        for tx in block.transactions:
            # Verify the transaction signature
            if not verify_signature(f"{tx.sender}{tx.recipient}{tx.amount}{tx.nonce}".encode(), tx.signature, tx.sender):
                return False
        # Verify the block hash
        return block.hash == block.hash

    def add_transaction(self, transaction: Transaction) -> bool:
        """
        Add a new transaction to the unconfirmed transactions list.
        """
        # Check if the nonce is correct (if is the next one in the sequence)
        if transaction.sender in self.nonces and transaction.nonce != self.nonces[transaction.sender] + 1:
            return False
        # Check if the sender has enough balance
        if transaction.sender not in self.balances:
            return False
        if self.balances[transaction.sender] < transaction.amount:
            return False
        
        self.unconfirmed_transactions.append(transaction)
        
        # Update the nonces
        self.nonces[transaction.sender] = self.nonces.get(transaction.sender, 0) + 1

        created_block = self.create_block()
        if created_block:
            print(f"Block created: {created_block.hash}")

        return True

    def process_transactions(self, transactions: List[Transaction]) -> bool:
        """
        Process a list of transactions, updating the balances accordingly.
        """
        temp_balances = self.balances.copy()
        for tx in transactions:
            if temp_balances.get(tx.sender, 0) < tx.amount:
                return False  # Insufficient funds
            temp_balances[tx.sender] -= tx.amount
            temp_balances[tx.recipient] = temp_balances.get(tx.recipient, 0) + tx.amount
        self.balances = temp_balances
        return True
    
    # Blockchain route methods
    def get_unconfirmed_blocks(self) -> List[Block]:
        """
        Get blocks (nodes) with less than umbral confirmations (node fathers).
        """
        return [self.graph.nodes[node] for node in self.graph.nodes if self.graph.in_degree(node) < 2]
    
    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        """
        Get a block by its hash.
        """
        return self.graph.nodes.get(block_hash, None)
    
    def get_wallet_balance(self, public_key: str) -> Optional[int]:
        """
        Get the balance of a wallet.
        """
        return self.balances.get(public_key, 0) / (10 ** self.decimal_places)

    def save_graph_to_json_file(self, file_path) -> None:
        """
        Save the blockchain to a JSON file.
        """
        # Get the data from the graph
        data = nx.node_link_data(self.graph)
        # Convert all Block objects to dictionaries
        for node in data['nodes']:
            if 'block' in node:
                node['block'] = node['block'].to_dict()
        # Write the data to the file
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

    def load_graph_from_json_file(self, file_path) -> None:
        """
        Load the blockchain from a JSON file and reevaluate all transactions.
        """
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                data = json.load(file)
            graph = nx.node_link_graph(data)
            
            # Initialize the blockchain state
            self.graph = nx.DiGraph()
            self.balances = {
                GENESIS_PUBLIC_KEY: 100000 # type: ignore
            } # Reset the balances
            self.nonces = {}
            
            self.recreate_blockchain_from_graph(graph)
        else:
            # If the file does not exist, initialize a new blockchain
            self.graph = nx.DiGraph()
            print("No existing blockchain found. A new blockchain has been initialized.")

    def recreate_blockchain_from_graph(self, graph: nx.DiGraph) -> None:
        # Order the nodes in topological order
        try:
            nodes_in_order = list(nx.topological_sort(graph))
        except nx.NetworkXUnfeasible:
            print("Cyclic dependencies detected in the blockchain graph.")
            return
        
        # Process the blocks in order
        for node in nodes_in_order:
            block_data = graph.nodes[node]['block']
            block = Block(**block_data)
            print(f"Processing block {block.index} with hash {block.hash}")
            self.process_block(block)
            self.graph.add_node(block.hash, block=block)
            for child_hash in block.children_hashes:
                if child_hash in self.graph:
                    self.graph.add_edge(block.hash, child_hash)
                    
        print("Blockchain successfully reconstructed from the file.")

    def process_block(self, block: Block) -> None:
        """
        Process a single block, verifying transactions and updating state.
        """
        for tx in block.transactions:
            # Verify the transaction
            if self.validate_transaction(tx):
                self.apply_transaction(tx)
            else:
                #print(f"Transaction in block {block.index} is invalid: {tx}")
                return

    def validate_transaction(self, tx: Transaction) -> bool:
        """
        Validate a transaction's signature and check balances and nonces.
        """
        # Verify the signature
        if not verify_signature(f"{tx.sender}{tx.recipient}{tx.amount}{tx.nonce}".encode(), tx.signature, tx.sender):
            #print("\nInvalid signature")
            return False
        # Verify the nonce
        if tx.sender in self.nonces and tx.nonce != self.nonces[tx.sender] + 1:
            #print("\nInvalid nonce")
            #print(f"Expected nonce: {self.nonces[tx.sender] + 1}, got: {tx.nonce}")
            return False
        # Verify the balance
        if self.balances.get(tx.sender, 0) < tx.amount:
            #print("\nInsufficient funds")
            return False
        return True

    def apply_transaction(self, tx: Transaction) -> None:
        """
        Apply a transaction to the blockchain state.
        """
        self.balances[tx.sender] -= tx.amount
        self.balances[tx.recipient] = self.balances.get(tx.recipient, 0) + tx.amount
        self.nonces[tx.sender] = tx.nonce

    def get_neighbors(self) -> List[str]:
        """
        Get the neighbors of the node.
        """
        return self.neighbors
    
    def add_neighbor(self, neighbor_url: str) -> None:
        """
        Add a new neighbor to the node.
        """
        if neighbor_url not in self.neighbors:
            self.neighbors.append(neighbor_url)

    class Config:
        """
        Pydantic Config

        Args:
        - arbitrary_types_allowed: bool
        """
        arbitrary_types_allowed = True
        schema_extra = {
            "example": {
                "graph": {},
                "unconfirmed_transactions": [
                    {
                        "sender": GENESIS_PUBLIC_KEY,
                        "recipient": SEBASTIAN_PUBLIC_KEY,
                        "amount": 10,
                        "nonce": 0,
                        "signature": "signature"
                    }
                ],
                "block_transactions_limit": 10,
                "balances": {
                    GENESIS_PUBLIC_KEY: 100
                }
            }
        }