from __future__ import annotations
import networkx as nx
import numpy as np
import math

from src.domain.transforms.base import TransformInfo
from src.domain.graph_model import Graph, RunParams
from src.domain.sparsifiers.base import Sparsifier
from src.domain.sparsifiers.registry import register_sparsifier


@register_sparsifier("k_neighbor")
class KNeighborSparsifier(Sparsifier):
    INFO = TransformInfo(name="k-neighbor sparsifier", abbrev="k-n")

    def run(self, graph: Graph, params: RunParams) -> Graph:
        rho = float(params.get("rho", 0.5))
        seed = int(params.get("seed", 420))

        if not (0.0 <= rho <= 1.0):
            raise ValueError(f"rho must be in [0, 1], got {rho}")

        rng = np.random.default_rng(seed)

        G = graph.to_networkx(copy=False)
        H = nx.DiGraph() if G.is_directed() else nx.Graph()
        H.add_nodes_from(G.nodes(data=True))

        for v in G.nodes():
            neighbors = list(G.neighbors(v))
            d_v = len(neighbors)

            # k_v = max(1, floor(d_v ^ rho))
            k_v = max(1, int(math.floor(d_v ** rho)))

            if d_v <= k_v:
                for u in neighbors:
                    data = G.get_edge_data(v, u)
                    H.add_edge(v, u, **data)
            else:
                weights = []
                for u in neighbors:
                    w = G.get_edge_data(v, u).get("weight", 1.0)
                    weights.append(w)

                weights = np.array(weights, dtype=float)
                total_w = weights.sum()

                if total_w > 0:
                    probs = weights / total_w
                else:
                    probs = None

                # randomly sampling distinct edges
                selected_indices = rng.choice(
                    len(neighbors),
                    size=k_v,
                    replace=False,
                    p=probs
                )

                for idx in selected_indices:
                    u = neighbors[idx]
                    data = G.get_edge_data(v, u)
                    H.add_edge(v, u, **data)

        return Graph.from_networkx(
            H,
            name=f"{graph.name}_k_neighbor",
            metadata={"rho": rho, "algorithm": "k_neighbor"}
        )