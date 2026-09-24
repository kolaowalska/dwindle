from __future__ import annotations

import numpy as np
import networkx as nx

from src.domain.transforms.base import TransformInfo
from src.domain.graph_model import Graph, RunParams
from src.domain.sparsifiers.base import Sparsifier
from src.domain.sparsifiers.registry import register_sparsifier


@register_sparsifier("pagerank")
class PageRankPruning(Sparsifier):
    INFO = TransformInfo(name="pagerank pruning", abbrev="pr")

    def run(self, graph: Graph, params: RunParams) -> Graph:
        rho = float(params.get("rho", 0.5))
        alpha = float(params.get("alpha", 0.85)) # standard damping factor

        g = graph.to_networkx(copy=True)
        ug = g.to_undirected() if g.is_directed() else g

        if not nx.is_connected(ug):
            raise ValueError("pagerank pruning expects a connected graph")

        target_edges = int(np.floor(rho * ug.number_of_edges()))

        # trw stationary distribution
        scores = nx.pagerank(ug, alpha=alpha)

        # bottom-up pruning logic
        sorted_nodes = sorted(scores, key=lambda x: scores[x])
        H = ug.copy()

        for v in sorted_nodes:
            if H.number_of_edges() <= target_edges:
                break
            H_temp = H.copy()
            H_temp.remove_node(v)
            if not nx.is_connected(H_temp):
                continue
            H = H_temp
            if H.number_of_edges() <= H.number_of_nodes() - 1:
                break

        result = g.__class__()
        result.add_nodes_from((n, g.nodes[n]) for n in H.nodes() if n in g.nodes())
        if g.is_directed():
            for u, v in H.edges():
                if g.has_edge(u, v): result.add_edge(u, v, **g[u][v])
                elif g.has_edge(v, u): result.add_edge(v, u, **g[v][u])
        else:
            for u, v in H.edges():
                result.add_edge(u, v, **g[u].get(v, {}))

        return Graph.from_networkx(
            result,
            name=f"{graph.name}_pr",
            metadata={"rho": rho, "alpha": alpha},
        )
