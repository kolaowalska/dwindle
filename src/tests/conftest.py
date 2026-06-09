from __future__ import annotations

import networkx as nx
import pytest

from src.domain.graph_model import Graph, RunParams
from src.application.experiment_service import ExperimentService
from src.infrastructure.persistence.stubs import InMemoryGraphRepository, InMemoryExperimentRepository


@pytest.fixture
def path10():
    return Graph.from_networkx(nx.path_graph(10), name="path10")

@pytest.fixture
def triangle():
    g = nx.Graph()
    g.add_edges_from([(0, 1), (1, 2), (0, 2)])
    return Graph.from_networkx(g, name="triangle")

@pytest.fixture
def complete5():
    return Graph.from_networkx(nx.complete_graph(5), name="complete5")

@pytest.fixture
def disconnected():
    g = nx.Graph()
    g.add_edges_from([(0, 1), (2, 3)])
    return Graph.from_networkx(g, name="disconnected")

@pytest.fixture
def weighted():
    g = nx.Graph()
    g.add_edge(0, 1, weight=2.0)
    g.add_edge(1, 2, weight=0.5)
    g.add_edge(2, 3, weight=1.0)
    return Graph.from_networkx(g, name="weighted")

@pytest.fixture
def directed():
    return Graph.from_networkx(nx.DiGraph([(0, 1), (1, 2), (2, 0)]), name="directed")

@pytest.fixture
def empty():
    return Graph.from_networkx(nx.Graph(), name="empty")

@pytest.fixture
def service():
    return ExperimentService(InMemoryGraphRepository(), InMemoryExperimentRepository())

@pytest.fixture
def no_params():
    return RunParams({})
