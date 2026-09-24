import networkx.algorithms.community as nx_comm

from src.domain.graph_model import Graph, RunParams
from src.domain.metrics.base import Metric, MetricInfo, MetricResult
from src.domain.metrics.registry import register_metric


@register_metric("community_preservation")
class CommunityPreservation(Metric):
    INFO = MetricInfo(
        name="community preservation",
        type="absolute",
        description=(
            "modularity and number of communities detected by the louvain method."
            "use with DeltaMetric to check whether sparsification fractures communities"
        ),
    )

    def compute(self, graph: Graph, params: RunParams) -> MetricResult:
        g = graph.to_networkx(copy=False)
        g_undirected = g.to_undirected() if g.is_directed() else g

        if g_undirected.number_of_edges() == 0:
            return MetricResult(
                metric=self.INFO.name,
                summary={"modularity": 0.0, "n_communities": 0},
            )

        seed = int(params.get("seed", 2137))
        communities = nx_comm.louvain_communities(g_undirected, seed=seed)
        modularity = float(nx_comm.modularity(g_undirected, communities))

        return MetricResult(
            metric=self.INFO.name,
            summary={
                "modularity": modularity,
                "n_communities": len(communities),
            },
        )
