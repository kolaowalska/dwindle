from .base import Sparsifier
from .registry import register_sparsifier
from ..graph_model import Graph, RunParams
from ..transforms.base import TransformInfo


@register_sparsifier("identity_stub")
class IdentitySparsifier(Sparsifier):
    INFO = TransformInfo(name="identity sparsifier", abbrev="id")

    def run(self, graph: Graph, params: RunParams) -> Graph:
        return Graph.from_networkx(
            graph.to_networkx(copy=True),
            name=f"{graph.name}_identity",
            metadata=graph.metadata
        )

