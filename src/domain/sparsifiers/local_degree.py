from __future__ import annotations
import networkx as nx
import math

from src.domain.transforms.base import TransformInfo
from src.domain.graph_model import Graph, RunParams
from src.domain.sparsifiers.base import Sparsifier
from src.domain.sparsifiers.registry import register_sparsifier


@register_sparsifier("local_degree")
class LocalDegreeSparsifier(Sparsifier):
    INFO = TransformInfo(name="local degree sparsifier", abbrev="ld")

    def run(self, graph: Graph, params: RunParams) -> Graph:
        rho = float(params.get("rho", 0.5))

        if not (0.0 <= rho <= 1.0):
            raise ValueError(f"rho must be in [0, 1], got {rho}")

        G = graph.to_networkx(copy=False)
        H = nx.DiGraph() if G.is_directed() else nx.Graph()
        H.add_nodes_from(G.nodes(data=True))

        if G.is_directed():
            D = dict(G.out_degree())
        else:
            D = dict(G.degree())

        for v in G.nodes():
            neighbors = list(G.neighbors(v))
            d_v = len(neighbors)
            k_v = math.floor(d_v ** rho)

            if k_v > 0: # sorting neighbors by their degree descending
                neighbors_sorted = sorted(
                    neighbors,
                    key=lambda u: D.get(u, 0),
                    reverse=True
                )

                selected = neighbors_sorted[:k_v]

                for u in selected:
                    data = G.get_edge_data(v, u)
                    H.add_edge(v, u, **data)

        return Graph.from_networkx(
            H,
            name=f"{graph.name}_local_degree",
            metadata={"rho": rho}
        )
