from app.api.models.blockchain import DAG

# Instantiating the blockchain
dag = DAG() # type: ignore
dag.load_graph_from_json_file(dag.json_file_path)

def get_blockchain():
    return dag

def reset_blockchain():
    global dag
    dag = DAG() # type: ignore
    dag.load_graph_from_json_file(dag.json_file_path)