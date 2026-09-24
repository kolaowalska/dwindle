import networkx as nx
import matplotlib.pyplot as plt
import os


def save_comparison_plot(original_nx, modified_nx, title: str, filename: str):
    plt.figure(figsize=(10, 5))

    # plotting original
    plt.subplot(1, 2, 1)
    plt.title(f"original\n(|V|={len(original_nx)}, |E|={len(original_nx.edges)})")
    pos = nx.spring_layout(original_nx, seed=420, k=1.5)
    nx.draw(original_nx, pos, node_size=20, node_color='deeppink', edge_color='lightpink', alpha=0.5)

    # plotting modified
    plt.subplot(1, 2, 2)
    plt.title(f"modified\n(|V|={len(modified_nx)}, |E|={len(modified_nx.edges)})")
    if set(modified_nx.nodes()).issubset(set(original_nx.nodes())):
        nx.draw(modified_nx, pos, node_size=20, node_color='deeppink', edge_color='lightpink', alpha=0.5)
    else:
        nx.draw(modified_nx, node_size=20, node_color='deeppink')

    plt.suptitle(title)

    os.makedirs("results", exist_ok=True)
    out_path = f"results/{filename}"
    plt.savefig(out_path)
    plt.close()
    print(f"[visualizer] comparison saved to {out_path}")
