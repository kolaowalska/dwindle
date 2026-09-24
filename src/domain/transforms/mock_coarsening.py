from __future__ import annotations

import logging
import networkx as nx
import random

from src.domain.transforms.base import GraphTransform, TransformInfo
from src.domain.transforms.registry import register_transform
from src.domain.graph_model import Graph, RunParams

log = logging.getLogger(__name__)


@register_transform("mock_coarsening")
class MockCoarsening(GraphTransform):
    INFO = TransformInfo(name="coarsening for the layman", abbrev="coarsening")

    def run(self, graph: Graph, params: RunParams) -> Graph:
        G = graph.to_networkx(copy=True)

        reduction_ratio = params.get("reduction_ratio", 0.5)
        seed = params.get("seed", 420)
        rng = random.Random(seed)

        initial_nodes = G.number_of_nodes()
        target_nodes = int(initial_nodes * (1 - reduction_ratio))
        target_nodes = max(1, target_nodes)
        max_retries = initial_nodes * 2  # safety brake
        retries = 0

        while G.number_of_nodes() > target_nodes and retries < max_retries:
            if G.number_of_edges() == 0:
                log.warning("no edges left to contract, stopping early")
                break

            edges = list(G.edges())
            if not edges:
                break

            u, v = rng.choice(edges)

            if u == v:
                retries += 1
                continue

            nx.contracted_nodes(G, u, v, self_loops=False, copy=False)

            retries = 0

        final_nodes = G.number_of_nodes()

        return Graph.from_networkx(
            G,
            name=f"{graph.name}_coarsened",
            metadata={
                "operation": "mock_coarsening",
                "target_reduction": reduction_ratio,
                "initial_nodes": initial_nodes,
                "final_nodes": final_nodes
            }
        )
