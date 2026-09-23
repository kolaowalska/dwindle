from __future__ import annotations

import numpy as np
import networkx as nx

from src.domain.graph_model import Graph, RunParams
from src.domain.metrics.base import RelativeMetric, MetricInfo, MetricResult
from src.domain.metrics.registry import register_metric

def _laplacian_spectrum(graph: nx.Graph, k: int) -> np.ndarray:
    """
    returns k smallest, non-trivial laplacian eigenvalues in ascending order.
    """
    n = graph.number_of_nodes()
    if n == 0:
        return np.zeros(k)

    L = nx.laplacian_matrix(graph).astype(float)
    k_used = min(k + 1, n - 1)

    try:
        import scipy.sparse.linalg as sla
        eigenvalues = sla.eigsh(L, k=k_used, which="SM", return_eigenvectors=False)
        eigenvalues = np.sort(np.abs(eigenvalues))
    except Exception:
        eigenvalues = np.sort(np.abs(np.linalg.eigvalsh(L.toarray())))

    # dropping the zero eigenvalue, taking the k smallest remaining
    nontrivial = eigenvalues[eigenvalues > 1e-10]
    if len(nontrivial) >= k:
        return nontrivial[:k]
    return np.pad(nontrivial, (0, k - len(nontrivial)))

@register_metric("spectral_similarity")
class SpectralSimilarity(RelativeMetric):
    INFO = MetricInfo(
        name="spectral similarity",
        type="relative",
        description=(
            "TODO"
        ),
    )

    def compute(self, g: Graph, h: Graph, params: RunParams) -> MetricResult:
        k = int(params.get("k", 10))

        g_undirected = g.to_networkx(copy=False)
        h_undirected = h.to_networkx(copy=False)

        if g_undirected.is_directed():
            g_undirected = g_undirected.to_undirected()
        if h_undirected.is_directed():
            h_undirected = h_undirected.to_undirected()

        if g_undirected.number_of_nodes() == 0 or h_undirected.number_of_nodes() == 0:
            return MetricResult(
                metric=self.INFO.name,
                summary={
                    "relative_l2_error": 0.0,
                    "fiedler_G": 0.0,
                    "fiedler_H": 0.0,
                    "fiedler_ratio": 0.0,
                    "k": 0,
                },
            )

        lcc_g = g_undirected.subgraph(max(nx.connected_components(g_undirected), key=len))
        lcc_h = h_undirected.subgraph(max(nx.connected_components(h_undirected), key=len))

        spectrum_g = _laplacian_spectrum(lcc_g, k)
        spectrum_h = _laplacian_spectrum(lcc_h, k)

        min_k = min(len(spectrum_g), len(spectrum_h))
        spectrum_g, spectrum_h = spectrum_g[:min_k], spectrum_h[:min_k]

        norm_g = np.linalg.norm(spectrum_g)
        err = (
            float(np.linalg.norm(spectrum_g - spectrum_h) / norm_g)
                  if norm_g > 1e-10 else 0.0
        )

        fiedler_g = float(spectrum_g[0]) if len(spectrum_g) > 0 else 0.0
        fiedler_h = float(spectrum_h[0]) if len(spectrum_h) > 0 else 0.0
        fiedler_ratio = (fiedler_h / fiedler_g) if fiedler_g > 1e-10 else 0.0

        return MetricResult(
            metric=self.INFO.name,
            summary={
                "relative_l2_error": err,
                "fiedler_G": fiedler_g,
                "fiedler_H": fiedler_h,
                "fiedler_ratio": fiedler_ratio,
                "k": min_k,
            },
        )