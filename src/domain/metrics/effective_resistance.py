from __future__ import annotations

import networkx as nx
import numpy as np

from src.domain.graph_model import Graph, RunParams
from src.domain.metrics.base import Metric, MetricInfo, MetricResult
from src.domain.metrics.registry import register_metric


@register_metric("effective_resistance")
class EffectiveResistance(Metric):
    INFO = MetricInfo(
        name="effective resistance",
        type="absolute",
        description="total effective resistance (kirchhoff index); lower = better connected."
    )

    def compute(self, graph: Graph, params: RunParams) -> MetricResult:
        g = graph.to_networkx(copy=False)
        ug = g.to_undirected() if g.is_directed() else g

        if ug.number_of_nodes() == 0:
            return MetricResult(
                metric=self.INFO.name,
                summary={"kirchhoff_index": 0.0, "component_nodes": 0},
            )

        lcc = ug.subgraph(max(nx.connected_components(ug), key=len))
        n = lcc.number_of_nodes()

        L = nx.laplacian_matrix(lcc).toarray().astype(float)

        try:
            L_pinv = np.linalg.pinv(L)
            kirchhoff = float(n * np.trace(L_pinv))
        except Exception:
            kirchhoff = -1.0

        return MetricResult(
            metric=self.INFO.name,
            summary={"kirchhoff_index": kirchhoff, "component_nodes": n},
        )
