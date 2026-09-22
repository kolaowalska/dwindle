from __future__ import annotations

import logging
import os
import networkx as nx
from dataclasses import dataclass
from typing import Any

from src.domain.graph_model import Graph

log = logging.getLogger(__name__)

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


def _apply_direction(g: nx.Graph, source: GraphSource) -> nx.Graph:
    """
    formats like graphml carry their own directedness, so `directed` only
    promotes an undirected file; it never demotes a directed one.
    """
    if source.directed and not g.is_directed():
        return g.to_directed()
    return g

class GraphGateway:
    """
    [GATEWAY] to external graph data.
    """
    def load(self, source: GraphSource) -> Graph:
        log.info(f"loading graph '{source.name}' from {source.kind}")

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
                log.debug(f"reading file {path}")

                if ext in _LOADERS:
                    return _apply_direction(_LOADERS[ext](str(path), source), source)

                create_using = nx.DiGraph if source.directed else nx.Graph
                delimiter = "," if ext == ".csv" else None
                data = (('weight', float),) if source.weighted else False

                try:
                    return nx.read_edgelist(
                        str(path),
                        nodetype=int,
                        create_using=create_using,
                        delimiter=delimiter,
                        data=data
                    )
                except (TypeError, ValueError):
                    log.info(f"non-integer node labels in {path}, reading them as strings")
                    return nx.read_edgelist(
                        str(path),
                        create_using=create_using,
                        delimiter=delimiter,
                        data=data
                    )

            return Graph.from_loader(name=source.name, loader_f=lazy_loader)

        elif source.kind == "memory":
            nx_graph = source.value if source.value is not None else (
                nx.DiGraph() if source.directed else nx.Graph()
            )
            return Graph.from_networkx(nx_graph, name=source.name)

        else:
            raise ValueError(f"unknown source kind: {source.kind}")
