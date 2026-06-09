from __future__ import annotations

import os
import networkx as nx
from networkx import DiGraph, Graph
from dataclasses import dataclass
from typing import Any, Hashable

from src.domain.graph_model import Graph

_LOADERS = {
    ".graphml": lambda path, source: nx.read_graphml(path),
    ".gexf": lambda path, source: nx.read_gexf(path),
    ".gml": lambda path, source: nx.read_gml(path, label="id"),
    ".adjlist": lambda path, source: nx.read_adjlist(path, create_using=nx.DiGraph if source.directed else nx.Graph),
}


@dataclass
class GraphSource:
    kind: str
    name: str
    value: Any = None
    directed: bool = False
    weighted: bool = False

class GraphGateway:
    """
    [GATEWAY] to external graph data.
    """
    def load(self, source: GraphSource) -> Graph:
        print(f"\n[GATEWAY] loading graph '{source.name}' from {source.kind}...")

        if source.kind == "file":
            path = source.value

            if path is None:
                raise ValueError(f"error: source path is None for graph '{source.name}'")

            if not isinstance(path, (str, os.PathLike)):
                raise TypeError(f"error: expected path string, got {type(path)}")

            if not os.path.exists(path):
                raise FileNotFoundError(f"file not found: {path}")

            ext = os.path.splitext(str(path))[1].lower()

            def lazy_loader():
                print(f"\n[LAZY LOAD] reading file {path}")

                if ext in _LOADERS:
                    return _LOADERS[ext](str(path), source)

                create_using = nx.DiGraph if source.directed else nx.Graph

                if source.weighted:
                    return nx.read_edgelist(
                        str(path),
                        nodetype=int,
                        create_using=create_using,
                        data=(('weight', float),)
                    )
                return nx.read_edgelist(
                    str(path),
                    nodetype=int,
                    create_using=create_using,
                    data=False
                )

            return Graph.from_loader(name=source.name, loader_f=lazy_loader)

        elif source.kind == "memory":
            nx_graph = source.value if source.value is not None else (
                nx.DiGraph() if source.directed else nx.Graph()
            )
            return Graph.from_networkx(nx_graph, name=source.name)

        else:
            raise ValueError(f"unknown source kind: {source.kind}")
