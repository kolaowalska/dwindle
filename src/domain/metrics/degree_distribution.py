from __future__ import annotations
import collections
import math
import networkx as nx

from src.domain.graph_model import Graph, RunParams
from src.domain.metrics.base import Metric, MetricInfo, MetricResult
from src.domain.metrics.registry import register_metric


@register_metric("degree_distribution")
class DegreeDistribution(Metric):
    INFO = MetricInfo(
        name="degree distribution",
        type="absolute",
        description="probability distribution of vertex degrees"
    )

    def compute(self, graph: Graph, params: RunParams) -> MetricResult:
        G = graph.to_networkx(copy=False)
        n = G.number_of_nodes()

        if n == 0:
            return MetricResult(
                metric=self.INFO.name,
                summary={"entropy": 0.0, "max_degree": 0, "min_degree": 0, "unique_degrees": 0},
                artifacts={"distribution": {}},
            )

        degrees = [d for _, d in G.degree()]
        counts = collections.Counter(degrees)
        distribution = {k: count / n for k, count in counts.items()}
        entropy = -sum(p * math.log(p) for p in distribution.values() if p > 0)

        return MetricResult(
            metric=self.INFO.name,
            summary={
                "entropy": float(entropy),
                "max_degree": max(degrees),
                "min_degree": min(degrees),
                "unique_degrees": len(distribution),
            },
            artifacts={"distribution": distribution}
        )
