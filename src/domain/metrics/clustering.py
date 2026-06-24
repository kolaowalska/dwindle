from __future__ import annotations

import networkx as nx

from src.domain.graph_model import Graph, RunParams
from src.domain.metrics.base import Metric, MetricInfo, MetricResult
from src.domain.metrics.registry import register_metric


@register_metric("clustering")
class Clustering(Metric):
    INFO = MetricInfo(
        name="clustering",
        type="absolute",
        description=(
            "average clustering coefficient and transitivity; measures local triangle density"
        ),
    )

    def compute(self, graph: Graph, params: RunParams) -> MetricResult:
        g = graph.to_networkx(copy=False)
        weight_arg = "weight" if graph.is_weighted() else None
        g_undirected = g.to_undirected() if g.is_directed() else g

        if g_undirected.number_of_nodes() == 0:
            return MetricResult(
                metric=self.INFO.name,
                summary={"avg_clustering": 0.0, "transitivity": 0.0, "weighted": bool(weight_arg)},
            )

        avg_clustering = float(nx.average_clustering(g_undirected, weight=weight_arg))
        transitivity = float(nx.transitivity(g_undirected))

        return MetricResult(
            metric=self.INFO.name,
            summary={
                "avg_clustering": avg_clustering,
                "transitivity": transitivity,
                "weighted": bool(weight_arg),
            }
        )