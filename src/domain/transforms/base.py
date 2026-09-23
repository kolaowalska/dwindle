from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.domain.graph_model import Graph, RunParams, OperationDescriptor

log = logging.getLogger(__name__)


@dataclass
class TransformInfo:
    """
    metadata for a GraphTransform plugin
    """
    name: str
    abbrev: str
    version: str = "1.0.0"
    supports_directed: bool = True
    supports_weighted: bool = True
    deterministic: bool = False

    def descriptor(self) -> OperationDescriptor:
        return OperationDescriptor(kind="transform", name=self.name, version=self.version)


class GraphTransform(ABC):
    INFO: TransformInfo

    def execute(self, graph: Graph, params: RunParams) -> Graph:
        self._check_supported(graph)

        if graph.node_count == 0:
            log.warning(f"[{self.__class__.__name__}] no nodes found")

        log.info(f"[{self.__class__.__name__}] starting transformation on '{graph.name}'")
        start_time = time.perf_counter()

        result_graph = self.run(graph, params)
        duration = time.perf_counter() - start_time

        result_graph.metadata['algorithm'] = self.__class__.__name__
        result_graph.metadata['execution_time'] = duration
        result_graph.metadata['parent_graph'] = graph.name

        log.info(f"[{self.__class__.__name__}] finished in {duration:.5f}s")
        return result_graph

    def _check_supported(self, graph: Graph) -> None:
        info = getattr(self, "INFO", None)
        if info is None:
            raise AttributeError(
                f"{self.__class__.__name__} must declare INFO = TransformInfo(...)"
            )

        if graph.is_directed() and not info.supports_directed:
            raise ValueError(f"'{info.name}' does not support directed graphs")
        if graph.is_weighted() and not info.supports_weighted:
            raise ValueError(f"'{info.name}' does not support weighted graphs")

    @abstractmethod
    def run(self, graph: Graph, params: RunParams) -> Graph:
        pass
