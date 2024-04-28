import requests
import networkx as nx
import matplotlib.pyplot as plt

def fetch_dag():
    response = requests.get('http://localhost:8000/api/v1/blockchain_investigation/dag/')
    data = response.json()
    return data['data']

def plot_dag(dag_data):
    G = nx.DiGraph()
    for node in dag_data['nodes']:
        G.add_node(node['id'], label=node['block']['index'])
    for link in dag_data['links']:
        G.add_edge(link['source'], link['target'])

    pos = nx.spring_layout(G)  # Layout for visualizing the DAG
    nx.draw(G, pos, with_labels=True, labels=nx.get_node_attributes(G, 'label'))
    plt.show()

dag_data = fetch_dag()
plot_dag(dag_data)
