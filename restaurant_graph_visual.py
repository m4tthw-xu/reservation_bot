import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# Load the CSV file into a pandas DataFrame
file_path = 'adjacency_matrix.csv'
adj_matrix_df = pd.read_csv(file_path, index_col=0)

# Create a graph from the adjacency matrix
G = nx.Graph()

# Add nodes
for restaurant in adj_matrix_df.index:
    G.add_node(restaurant)

# Add edges with weights above the threshold
threshold = 0.5
for i, row in adj_matrix_df.iterrows():
    for j, value in row.items():
        if value > threshold:
            G.add_edge(i, j, weight=value)


def visualize_subset(restaurants, n=5, threshold=0.5):
    # Create a subgraph
    subG = nx.Graph()

    # Add the specified nodes and their neighbors
    for restaurant in restaurants:
        if restaurant in G:
            subG.add_node(restaurant)
            neighbors = list(G.neighbors(restaurant))
            # Sort neighbors by edge weight in descending order
            neighbors = sorted(neighbors, key=lambda neighbor: G[restaurant][neighbor]['weight'], reverse=True)
            # Add top n neighbors based on the threshold
            for neighbor in neighbors[:n]:
                weight = G[restaurant][neighbor]['weight']
                if weight > threshold:
                    subG.add_node(neighbor)
                    subG.add_edge(restaurant, neighbor, weight=weight)

    # Draw the subgraph
    plt.figure(figsize=(12, 8))  # Increase figure size
    pos = nx.spring_layout(subG, k=0.9)  # positions for all nodes, adjust k for spacing

    # Draw nodes
    nx.draw_networkx_nodes(subG, pos, node_size=700, node_color='lightblue', edgecolors='black')

    # Draw edges
    edges = subG.edges(data=True)
    nx.draw_networkx_edges(subG, pos, edgelist=edges, width=2, alpha=0.7, edge_color='gray')

    # Draw edge labels
    edge_labels = {(u, v): f'{d["weight"]:.2f}' for u, v, d in edges}
    nx.draw_networkx_edge_labels(subG, pos, edge_labels=edge_labels, font_size=10)

    # Draw labels
    nx.draw_networkx_labels(subG, pos, font_size=12, font_family='sans-serif')

    plt.title(f'Restaurant Similarity Subgraph (Top {n} Neighbors, Threshold > {threshold})')
    plt.axis('off')  # Turn off the axis
    plt.show()

def get_n_neighbors(restaurants, n):
    result = {}
    # Add the specified nodes and their neighbors
    for restaurant in restaurants:
        if restaurant in G:
            neighbors = list(G.neighbors(restaurant))
            # Sort neighbors by edge weight in descending order
            neighbors = sorted(neighbors, key=lambda neighbor: G[restaurant][neighbor]['weight'], reverse=True)
            result[restaurant] = neighbors[:n]

    return result


# Example usage
# restaurants_to_visualize = ["LENOIR", "Odd Duck"]
# visualize_subset(restaurants_to_visualize, n=5, threshold=0.5)
#
# print(get_n_neighbors(restaurants_to_visualize, 3))