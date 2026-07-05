from __future__ import annotations

import networkx as nx

from src.domain.graph_model import Graph, RunParams
from src.domain.metrics.base import Metric, MetricInfo, MetricResult
from src.domain.metrics.registry import register_metric


@register_metric("avg_stretch")
class AvgStretch(Metric):
    INFO = MetricInfo(
        name="average stretch",
        type="absolute",
        description="average node eccentricity on the largest connected component (min = radius, max = diameter)"
    )

    def compute(self, graph: Graph, params: RunParams) -> MetricResult:
        G = graph.to_networkx(copy=False)
        ug = G.to_undirected() if G.is_directed() else G

        if ug.number_of_nodes() == 0:
            return MetricResult(metric=self.INFO.name, summary={"avg": 0.0, "min": 0.0})

        lcc = ug.subgraph(max(nx.connected_components(ug), key=len))
        ecc = nx.eccentricity(lcc)
        values = list(ecc.values())

        return MetricResult(
            metric=self.INFO.name,
            summary={
                "avg": float(sum(values) / len(values)),
                "min": float(min(values)),
            }
        )
