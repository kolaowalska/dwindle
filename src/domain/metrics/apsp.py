from __future__ import annotations

import networkx as nx

from src.domain.graph_model import Graph, RunParams
from src.domain.metrics.base import Metric, MetricInfo, MetricResult
from src.domain.metrics.registry import register_metric


@register_metric("apsp")
class APSPMetric(Metric):
    INFO = MetricInfo(
        name="all pairs shortest paths",
        type="absolute",
        description=("summary statistics (avg, max path length, reachable pairs) "
                     "from APSP on the largest connected component")
    )

    def compute(self, graph: Graph, params: RunParams) -> MetricResult:
        g = graph.to_networkx(copy=False)
        ug = g.to_undirected() if g.is_directed() else g

        if ug.number_of_nodes() == 0:
            return MetricResult(metric=self.INFO.name, summary={"avg_path": 0.0, "max_path": 0.0, "n_pairs": 0})

        lcc = ug.subgraph(max(nx.connected_components(ug), key=len))
        weight_arg = "weight" if graph.is_weighted() else None

        lengths = dict(nx.all_pairs_dijkstra_path_length(lcc, weight=weight_arg))
        all_lengths = [d for src in lengths.values() for d in src.values() if d > 0]

        if not all_lengths:
            return MetricResult(metric=self.INFO.name, summary={"avg_path": 0.0, "max_path": 0.0, "n_pairs": 0})

        return MetricResult(
            metric=self.INFO.name,
            summary={
                "avg_path": float(sum(all_lengths) / len(all_lengths)),
                "max_path": float(max(all_lengths)),
                "n_pairs": len(all_lengths),
            }
        )
