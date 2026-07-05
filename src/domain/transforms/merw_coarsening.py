from __future__ import annotations

import numpy as np
import scipy.sparse.linalg as sla
import networkx as nx

from src.domain.graph_model import Graph, RunParams
from src.domain.transforms.base import GraphTransform
from src.domain.transforms.registry import register_transform


def _dominant_eigenvector(A, n: int) -> np.ndarray:
    """
    returns the dominant eigenvector of an adjacency matrix.
    """
    if n < 500:
        dense = A.toarray()
        eigenvalues, eigenvectors = np.linalg.eigh(dense)
        v = np.abs(eigenvectors[:, -1])
    else:
        try:
            _, eigenvectors = sla.eigsh(A, k=1, which="LM", tol=1e-10, maxiter=n * 10)
            v = np.abs(eigenvectors[:, 0])
        except Exception:
            dense = A.toarray()
            _, eigenvectors = np.linalg.eigh(dense)
            v = np.abs(eigenvectors[:, -1])

    norm = np.linalg.norm(v)
    return v / norm if norm > 0 else v

def _stationary_distribution(psi: np.ndarray) -> np.ndarray:
    """
    returns the stationary distribution proportional to psi^2.
    """
    p = psi ** 2
    total = p.sum()
    return p / total if total > 0 else p

def _impact_score(g: nx.Graph, baseline_distribution: np.ndarray, nodes: list) -> dict:
    """
    leave-one-out impact score.
    for each node v, removes the node and measures L1 distance from baseline distribution.
    """

    node_index = {n: i for i, n in enumerate(nodes)}
    scores = {}

    for v in nodes:
        gv = g.copy()
        gv.remove_node(v)

        remaining = [n for n in nodes if n != v]

        if len(remaining) == 0:
            scores[v] = 0.0
            continue

        Av = nx.to_scipy_sparse_array(gv, nodelist=remaining, dtype=float, format="csr")
        psi_v = _dominant_eigenvector(Av, len(remaining))
        Pv = _stationary_distribution(psi_v)

        pad = np.zeros(len(nodes))
        for i, n in enumerate(remaining):
            pad[node_index[n]] = Pv[i]

        scores[v] = float(np.sum(np.abs(baseline_distribution - pad)))

    return scores

@register_transform("merw_coarsening")
class MERWCoarsening(GraphTransform):
    def run(self, graph: Graph, params: RunParams) -> Graph:
        rho = float(params.get("rho", 1.0))

        if not (0.0 < rho <= 1.0):
            raise ValueError(f"rho must be in (0, 1.0], got {rho} instead")

        g = graph.to_networkx(copy=True)
        g_undirected = g.to_undirected() if g.is_directed() else g

        if not nx.is_connected(g_undirected):
            raise ValueError("merw coarsening expects a connected graph")

        nodes = list(g_undirected.nodes())
        edges = g_undirected.number_of_edges()
        targets = int(np.floor(rho * edges))

        # phase 1: global baseline
        A = nx.to_scipy_sparse_array(g_undirected, nodelist=nodes, dtype=float, format="csr")
        psi = _dominant_eigenvector(A, len(nodes))
        baseline_distribution = _stationary_distribution(psi)

        # phase 2: impact scoring
        scores = _impact_score(g_undirected, baseline_distribution, nodes)

        # phase 3: bottom-up pruning
        nodes_sorted = sorted(scores, key=lambda v: scores[v])
        h = g_undirected.copy()
        pruned = 0
        for v in nodes_sorted:
            if h.number_of_edges() <= targets:
                break

            h_temp = h.copy()
            h_temp.remove_node(v)

            if not nx.is_connected(h_temp):
                continue

            h = h_temp
            pruned += 1

            if h.number_of_edges() <= h.number_of_nodes() - 1:
                break

        # re-attaching original edge attributes
        result = g.__class__()
        result.add_nodes_from((n, g.nodes[n]) for n in h.nodes() if n in g.nodes())
        if g.is_directed():
            for u, v in h.edges():
                if g.has_edge(u, v):
                    result.add_edge(u, v, **g[u][v])
                elif g.has_edge(v, u):
                    result.add_edge(v, u, **g[v][u])
        else:
            for u, v in h.edges():
                result.add_edge(u, v, **g[u].get(v, {}))

        return graph.from_networkx(
            result,
            name=f"{graph.name}_merw",
            source=graph.source,
            metadata={"rho": rho},
        )