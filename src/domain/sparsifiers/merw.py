from __future__ import annotations

import logging
import numpy as np
import scipy.sparse.linalg as sla
import networkx as nx

from src.domain.transforms.base import TransformInfo
from src.domain.graph_model import Graph, RunParams
from src.domain.sparsifiers.base import Sparsifier
from src.domain.sparsifiers.registry import register_sparsifier

log = logging.getLogger(__name__)


def _dominant_eigenvector(A, n: int) -> np.ndarray:
    """
    returns the dominant eigenvector of an adjacency matrix.
    """
    if n < 500:
        _, eigenvectors = np.linalg.eigh(A.toarray())
        v = np.abs(eigenvectors[:, -1])
    else:
        try:
            _, eigenvectors = sla.eigsh(A, k=1, which="LA", tol=1e-10, maxiter=n * 10)
            v = np.abs(eigenvectors[:, 0])
        except Exception:
            _, eigenvectors = np.linalg.eigh(A.toarray())
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

def _score_edges(g: nx.Graph, baseline_distribution: np.ndarray, nodes: list) -> dict[tuple, float]:
    """
    leave-one-out impact score.
    for each edge, the function temporarily removes the edge, recomputes the MERW
    stationary distribution, and measures the L1 shift from baseline.
    """
    scores = {}

    for u, v in g.edges():
        g_temp = g.copy()
        g_temp.remove_edge(u, v)

        if not nx.is_connected(g_temp):
            scores[(u, v)] = float("inf")
            continue

        A_temp = nx.to_scipy_sparse_array(g_temp, nodelist=nodes, dtype=float, format="csr")
        psi_temp = _dominant_eigenvector(A_temp, len(nodes))
        P_temp = _stationary_distribution(psi_temp)

        scores[(u, v)] = float(np.sum(np.abs(baseline_distribution - P_temp)))

    return scores


@register_sparsifier("merw")
class MERWSparsifier(Sparsifier):
    INFO = TransformInfo(name="MERW sparsifier", abbrev="merw")
    """
    TODO
    """
    def run(self, graph: Graph, params: RunParams) -> Graph:
        rho = float(params.get("rho", 0.5))
        rescore_interval = int(params.get("rescore_interval", 0))

        if not (0.0 < rho <= 1.0):
            raise ValueError(f"rho must be in (0, 1], got {rho}")

        g = graph.to_networkx(copy=True)
        ug = g.to_undirected() if g.is_directed() else g

        if not nx.is_connected(ug):
            raise ValueError(f"merw sparsifier expects a connected graph")

        nodes = list(ug.nodes())
        target_edges = int(np.floor(rho * ug.number_of_edges()))

        # phase 1
        A = nx.to_scipy_sparse_array(ug, nodelist=nodes, dtype=float, format="csr")
        psi = _dominant_eigenvector(A, len(nodes))
        baseline_distribution = _stationary_distribution(psi)

        # phase 2
        scores = _score_edges(ug, baseline_distribution, nodes)

        # phase 3
        h = ug.copy()
        pruned = 0

        while h.number_of_edges() > target_edges:
            candidates = {
                e: s for e, s in scores.items()
                if h.has_edge(*e) and s < float("inf")
            }
            if not candidates:
                log.warning("no more prunable edges, stopping early")
                break

            u, v = min(candidates, key=lambda e: candidates[e])

            # re-checking connectivity live; this edge may have become a bridge
            h_temp = h.copy()
            h_temp.remove_edge(u, v)

            if not nx.is_connected(h_temp):
                scores[(u, v)] = float("inf") # marking as untouchable going forward
                continue

            h.remove_edge(u, v)
            del scores[(u, v)]
            pruned += 1

            if rescore_interval > 0 and pruned % rescore_interval == 0:
                A_h = nx.to_scipy_sparse_array(h, nodelist=list(h.nodes()), dtype=float, format="csr")
                psi_h = _dominant_eigenvector(A_h, h.number_of_nodes())
                baseline_distribution_h = _stationary_distribution(psi_h)
                scores = _score_edges(h, baseline_distribution_h, list(h.nodes()))

        result = g.__class__()
        result.add_nodes_from(
            (n, g.nodes[n]) for n in h.nodes() if n in g.nodes()
        )

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
            metadata={"rho": rho, "rescore_interval": rescore_interval},
        )

