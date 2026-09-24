from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Dict, Iterable, Tuple, NewType, Callable
import uuid
import networkx as nx
import numpy as np
import scipy.sparse.linalg as sla

log = logging.getLogger(__name__)

GraphID = NewType('GraphID', str)
RunID = NewType('RunID', str)
ArtifactHandle = NewType('ArtifactHandle', str)

def new_graph_id() -> GraphID:
    return GraphID(str(uuid.uuid4()))

def new_run_id() -> RunID:
    return RunID(str(uuid.uuid4()))

@dataclass(frozen=True)
class RunParams:
    """immutable collection of parameters used by any runnable operation"""
    values: Mapping[str, Any] = field(default_factory=dict)

    def get(self, key:str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def with_overrides(self, **overrides: Any) -> "RunParams":
        merged = dict(self.values)
        merged.update(overrides)
        return RunParams(merged)

@dataclass(frozen=True)
class OperationDescriptor:
    """which algorithm produced the output"""
    kind: str
    name: str
    version: str = "1.0.0"
    params: Mapping[str, Any] = field(default_factory=dict)

# DOMAIN MODEL

class Graph:
    __slots__ = (
        "_loader",
        "_nx",
        "_spectral_cache",
        "directed",
        "id",
        "metadata",
        "name",
        "source",
        "weighted"
    )

    def __init__(
        self,
        nx_graph: Optional[nx.Graph | nx.DiGraph],
        id: GraphID,
        name: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        loader: Optional[Callable[[], nx.Graph]] = None
    ):
        self._nx = nx_graph
        self._loader = loader
        self.id: GraphID = id or new_graph_id()
        self.name: str = name or f"graph-{self.id}"
        self.source: Optional[str] = source
        self.metadata: Dict[str, Any] = dict(metadata or {})
        self._spectral_cache: Optional[Dict[str, Any]] = None

        if self._nx is not None:
            self.directed = self._nx.is_directed()
            self.weighted = nx.is_weighted(self._nx)
        else:
            self.directed = None
            self.weighted = None

    def to_networkx(self, copy: bool = True) -> nx.Graph | nx.DiGraph:
        """
        [LAZY LOAD] triggers loading from db if _nx is None
        -> copy=True returns a clone. slow (O(V + E)), consumes double RAM, but safe for mutation
        -> copy=False returns a reference to the internal object. fast (O(1)), zero extra ram. use to read properties
        """
        if self._nx is None and self._loader is not None:
            log.info(f"lazy loading graph data for '{self.name}'")
            self._nx = self._loader()

            if self._nx is not None:
                self.directed = self._nx.is_directed()
                self.weighted = nx.is_weighted(self._nx)

        if self._nx is None:
            return nx.Graph()

        return self._nx.copy() if copy else self._nx

    @property
    def node_count(self) -> int:
        return self.to_networkx(copy=False).number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self.to_networkx(copy=False).number_of_edges()

    def is_directed(self) -> bool:
        return self.to_networkx(copy=False).is_directed()

    def is_weighted(self) -> bool:
        if self.weighted is not None:
            return self.weighted
        return nx.is_weighted(self.to_networkx(copy=False))

    def copy(self, with_edge_attrs: bool = True) -> "Graph":
        G = self.to_networkx(copy=False)
        nx_copy = G.__class__()
        nx_copy.add_nodes_from(G.nodes(data=True))
        nx_copy.add_edges_from(
            G.edges(data=True) if with_edge_attrs else G.edges()
        )
        return Graph(
            nx_copy,
            id=new_graph_id(),
            name=self.name + "_copy",
            source=self.source,
            metadata=self.metadata.copy(),
        )

    def nodes(self) -> Iterable[Any]:
        return self.to_networkx(copy=False).nodes()

    def edges(self, data: bool = False) -> Iterable[Tuple[Any, Any] | Tuple[Any, Any, Mapping[str, Any]]]:
        return self.to_networkx(copy=False).edges(data)

    def degree(self, v: Any) -> float:
        return self.to_networkx(copy=False).degree[v]

    def edge_weight(self, u: Any, v: Any, default: float = 1.0, weight_attr: str = "weight") -> float:
        G = self.to_networkx(copy=False)
        data = G.get_edge_data(u, v, default=None)

        if data is None:
            raise KeyError(f"edge ({u}, {v}) not found :(")

        if isinstance(data, dict):
            return float(data.get(weight_attr, default))

        return float(min(d.get(weight_attr, default) for d in data.values()))

    @property
    def spectral_properties(self) -> Dict[str, Any]:
        if self._spectral_cache is not None:
            return self._spectral_cache

        G = self.to_networkx(copy=False)
        A = nx.to_scipy_sparse_array(G, dtype=float, format="csr")

        try:
            eigenvalues, eigenvectors = sla.eigsh(A, k=1, which="LA")
            lambda_value = float(eigenvalues[0])
            v = np.abs(eigenvectors[:, 0])
            v = v / np.linalg.norm(v)
        except Exception as e:
            log.warning(f"sparse eigenvector computation failed ({e}), falling back to dense")
            eigenvalues, eigenvectors = np.linalg.eigh(nx.to_numpy_array(G))
            lambda_value = float(eigenvalues[-1])
            v = np.abs(eigenvectors[:, -1])
            v = v / np.linalg.norm(v)

        self._spectral_cache = {
            "lambda": lambda_value,
            "eigenvector": v,
            "entropy_rate": float(np.log(lambda_value)) if lambda_value > 0 else float("-inf")
        }

        return self._spectral_cache


    # FACTORIES
    @staticmethod
    def from_networkx(g: nx.Graph | nx.DiGraph, *, name: Optional[str] = None, source: Optional[str] = None,
                      metadata: Optional[Mapping[str, Any]] = None) -> "Graph":
        final_name = name or str(uuid.uuid4())
        return Graph(
            nx_graph=g,
            id=new_graph_id(),
            name=final_name,
            source=source,
            metadata=metadata or {}
        )

    @staticmethod
    def from_loader(name: str, loader_f: Callable[[], nx.Graph], metadata: Optional[dict] = None) -> "Graph":
        """factory for [LAZY LOAD] (virtual proxy)"""
        return Graph(
            nx_graph=None,
            id=new_graph_id(),
            name=name,
            source="lazy_loader",
            metadata=metadata or {},
            loader=loader_f
        )


